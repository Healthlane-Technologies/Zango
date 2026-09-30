import io
import json
import zipfile

from pathlib import Path
from unittest import mock

from zango.apps.shared.app_templates.models import ImmutableVersionError
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, publish
from zango.apps.shared.app_templates.services.workspace import (
    MARKER,
    WorkspaceError,
    attach_workspace,
    engine_drift,
    extract_workspace,
    inspect_zip,
    new_draft_from,
    restore_engine,
    zip_directory,
)

from .tests import AppTemplatesTestBase


def make_zip(files: dict, prefix="psp-template/") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, text in files.items():
            zf.writestr(prefix + name, text)
    return buf.getvalue()


WORKSPACE = {
    "settings.json": json.dumps(
        {"app_name": "enhertupap", "zango_version": ">=0.0.1", "modules": []}
    ),
    "manifest.json": json.dumps({"packages": [{"name": "crud", "version": "1.0.17"}]}),
    "backend/template/engine.py": "ENGINE = 1\n",
    "backend/template/programs/models.py": "class Program: ...\n",
    "backend/custom/patient/patient_config.py": "PATIENT = 'example'\n",
    "packages/crud/big.js": "x" * 10,
}


class WorkspaceZipTests(AppTemplatesTestBase):
    def draft(self):
        version, _ = import_pack(self.pack())
        return version

    def test_inspect_strips_the_top_folder_and_reads_settings(self):
        info = inspect_zip(make_zip(WORKSPACE))
        self.assertEqual(info.prefix, "psp-template/")
        self.assertIn("backend/template/engine.py", info.files)
        self.assertEqual(info.app_name, "enhertupap")
        self.assertFalse(info.run_migrations)

    def test_unsafe_or_incomplete_zips_are_refused(self):
        for files in (
            {"../evil.py": "x", "settings.json": "{}", "manifest.json": "{}"},
            {"manifest.json": "{}"},
            {"settings.json": "{}"},
        ):
            with self.assertRaises(WorkspaceError):
                inspect_zip(make_zip(files, prefix=""))
        with self.assertRaises(WorkspaceError):
            inspect_zip(b"not a zip")

    def test_attach_only_to_drafts(self):
        version = self.draft()
        attach_workspace(version, make_zip(WORKSPACE), ["backend/template/"])
        self.assertTrue(version.has_workspace)
        self.assertEqual(version.workspace_engine_paths, ["backend/template/"])
        published = publish(version)
        with self.assertRaises(ImmutableVersionError):
            attach_workspace(published, make_zip(WORKSPACE))

    def test_extract_sets_the_app_name_and_writes_a_marker(self):
        version = self.draft()
        attach_workspace(version, make_zip(WORKSPACE), ["backend/template/"])
        dest = Path(self.tmp.name) / "ws"
        extract_workspace(version, dest, "onc_pap")
        self.assertEqual(
            json.loads((dest / "settings.json").read_text())["app_name"], "onc_pap"
        )
        self.assertTrue((dest / "backend/template/engine.py").is_file())
        marker = json.loads((dest / MARKER).read_text())
        self.assertEqual(marker["template"], "demo")
        self.assertEqual(marker["workspace_sha"], version.workspace_sha)

    def test_engine_drift_is_restored_and_custom_is_left_alone(self):
        version = self.draft()
        attach_workspace(version, make_zip(WORKSPACE), ["backend/template/"])
        dest = Path(self.tmp.name) / "ws"
        extract_workspace(version, dest, "onc_pap")
        (dest / "backend/template/engine.py").write_text("ENGINE = 'hacked'\n")
        (dest / "backend/template/programs/models.py").unlink()
        (dest / "backend/custom/patient/patient_config.py").write_text(
            "PATIENT = 'this client'\n"
        )
        self.assertEqual(
            sorted(engine_drift(version, dest)),
            [
                ("backend/template/engine.py", "changed"),
                ("backend/template/programs/models.py", "missing"),
            ],
        )
        restored = restore_engine(version, dest)
        self.assertEqual(len(restored), 2)
        self.assertEqual(
            (dest / "backend/template/engine.py").read_text(), "ENGINE = 1\n"
        )
        self.assertEqual(
            (dest / "backend/custom/patient/patient_config.py").read_text(),
            "PATIENT = 'this client'\n",
        )
        self.assertEqual(engine_drift(version, dest), [])

    def test_zip_directory_leaves_out_packages_and_vcs(self):
        src = Path(self.tmp.name) / "checkout"
        for name, text in {
            **WORKSPACE,
            ".git/HEAD": "ref",
            "frontend/node_modules/x/index.js": "x",
        }.items():
            (src / name).parent.mkdir(parents=True, exist_ok=True)
            (src / name).write_text(text)
        files = inspect_zip(zip_directory(src)).files
        self.assertIn("backend/template/engine.py", files)
        self.assertFalse(
            [
                f
                for f in files
                if f.startswith(("packages/", ".git/")) or "node_modules" in f
            ]
        )

    def test_new_packs_keep_the_attached_workspace(self):
        v1, _ = import_pack(self.pack(), publish_now=True)
        with_ws = new_draft_from(v1, "1.0.1")
        attach_workspace(with_ws, make_zip(WORKSPACE), ["backend/template/"])
        publish(with_ws)
        # Re-importing the same pack (as migrate does) is a no-op, not a clash.
        _, created = import_pack(self.pack())
        self.assertFalse(created)
        # A newer pack inherits the workspace.
        v2, created = import_pack(
            self.pack(version="1.1.0", starter="journey: v2\n"), publish_now=True
        )
        self.assertTrue(created)
        self.assertEqual(v2.workspace_sha, with_ws.workspace_sha)
        self.assertEqual(bytes(v2.workspace_zip), bytes(with_ws.workspace_zip))


class TemplateBuildTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        draft, _ = import_pack(self.pack())
        attach_workspace(draft, make_zip(WORKSPACE), ["backend/template/"])
        self.version = publish(draft)
        catalogue.clear_caches()

    def run_for(self, spec):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        requirement = AgentRequirement(initial_prompt="go")
        seed_template_requirement(requirement, catalogue.get_template("demo"), spec)
        return mock.Mock(requirement=requirement)

    def test_prepare_restores_the_engine_and_writes_the_spec(self):
        from zango.apps.agent_mode.template_build import prepare

        workspace = Path(self.tmp.name) / "ws"
        extract_workspace(self.version, workspace, "onc_pap")
        (workspace / "backend/template/engine.py").write_text("tampered\n")
        run_dir = Path(self.tmp.name) / "run"
        build = prepare(self.run_for("journey: demo\n"), str(workspace), str(run_dir))
        self.assertEqual(build.restored, [("backend/template/engine.py", "changed")])
        self.assertEqual(Path(build.spec_path), run_dir / "spec" / "journey.yaml")
        self.assertEqual(Path(build.spec_path).read_text(), "journey: demo\n")
        self.assertEqual(build.skill, "zango-tpl-demo:zango-demo-builder")

    def test_non_template_runs_are_left_alone(self):
        from zango.apps.agent_mode.template_build import prepare

        self.assertIsNone(prepare(mock.Mock(requirement=None), "/w", "/r"))

    def test_the_build_prompt_dispatches_the_template_skill(self):
        from zango.apps.agent_mode.prompt import compose_prompt, template_build_request

        ask = template_build_request(
            catalogue.get_template("demo"),
            "/runs/x/spec/journey.yaml",
            ["backend/template/"],
        )
        self.assertIn("/runs/x/spec/journey.yaml", ask)
        self.assertIn("zango-tpl-demo:zango-demo-builder", ask)
        self.assertIn("`backend/template/`", ask)

        class Ctx:
            app_name = "onc_pap"
            workspace_path = "/w"
            schema_name = "onc_pap"
            primary_domain = "onc.local"
            packages = []
            modules = []
            roles = []

        text = compose_prompt(ask, Ctx(), skill="zango-tpl-demo:zango-demo-builder")
        self.assertTrue(text.startswith("/zango-tpl-demo:zango-demo-builder"))

    def test_build_options_load_the_template_plugin(self):
        from zango.apps.agent_mode.options import build_agent_options
        from zango.apps.agent_mode.template_build import TemplateBuild

        build = TemplateBuild(
            template=catalogue.get_template("demo"), spec_path="/r/spec/journey.yaml"
        )

        class Ctx:
            workspace_path = "/w"
            primary_domain = "onc.local"
            app_name = "onc_pap"

        run = mock.Mock(
            permission_mode="", model="", effort="", max_turns=None, max_budget_usd=None
        )
        with (
            mock.patch("zango.apps.agent_mode.options.build_env", return_value={}),
            mock.patch("zango.apps.agent_mode.guards.make_pre_tool_use_guard") as guard,
        ):
            opts = build_agent_options(
                run=run,
                ctx=Ctx(),
                creds=object(),
                settings_path="/s.json",
                template_build=build,
            )
        self.assertIn({"type": "local", "path": build.plugin_dir}, opts.plugins)
        self.assertIn("zango-tpl-demo:zango-demo-builder", opts.skills)
        self.assertIn(build.plugin_dir, guard.call_args.kwargs["read_roots"])
        self.assertIn("/r/spec", guard.call_args.kwargs["read_roots"])


class ScaffoldWorkspaceTests(AppTemplatesTestBase):
    def test_launch_hands_the_template_workspace_to_app_creation(self):
        from zango.apps.agent_mode.scaffold import launch_app
        from zango.apps.shared.agent_mode.models import AgentAppScaffold

        draft, _ = import_pack(self.pack())
        attach_workspace(draft, make_zip(WORKSPACE), ["backend/template/"])
        version = publish(draft)
        scaffold = AgentAppScaffold.objects.create(
            prompt="a PAP", template_version=version
        )
        seen = {}

        def fake_create(**kwargs):
            ws = Path(kwargs["app_template_dir"])
            seen["app_name"] = json.loads((ws / "settings.json").read_text())[
                "app_name"
            ]
            seen["engine"] = (ws / "backend/template/engine.py").is_file()
            seen["name"] = kwargs["name"]
            return mock.Mock(uuid="00000000-0000-0000-0000-000000000001"), "task-1"

        identity = mock.Mock(
            name="identity", label="Onc PAP", description="d", source="agent"
        )
        identity.name = "onc_pap"
        with (
            mock.patch(
                "zango.apps.agent_mode.config.load_config",
                return_value=mock.Mock(enabled=True),
            ),
            mock.patch(
                "zango.apps.agent_mode.credentials.resolve_credentials",
                return_value=None,
            ),
            mock.patch(
                "zango.apps.agent_mode.naming.suggest_identity", return_value=identity
            ),
            mock.patch(
                "zango.apps.agent_mode.naming.unique_name", return_value="onc_pap"
            ),
            mock.patch(
                "zango.apps.shared.tenancy.models.TenantModel.create",
                side_effect=fake_create,
            ),
        ):
            launch_app(scaffold)
        self.assertEqual(
            seen, {"app_name": "onc_pap", "engine": True, "name": "onc_pap"}
        )
