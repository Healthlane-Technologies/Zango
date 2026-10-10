"""App Studio builds: the platform runs the skill's scripts, the agent writes code.

Every subprocess is mocked: these tests pin the order of the steps, their
argv, what reaches each subprocess's environment, and how outcomes are read —
not the skill's scripts themselves.
"""

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from zango.apps.agent_mode import studio_build
from zango.apps.agent_mode.postrun import StepResult
from zango.apps.agent_mode.studio_build import (
    PLAYWRIGHT_REASON,
    StudioBuild,
    StudioError,
    is_studio,
)


SPEC = """\
spec_version: 1
app:
  code: demo_app
  name: Demo
roles:
  - { name: Manager }
modules:
  - code: orders
    url: orders
"""

RESOLVED = {"app": {"code": "demo_app"}, "roles": {"Manager": {"slug": "manager"}},
            "modules": [{"code": "orders", "url": "orders"}]}


def make_skill(root: Path) -> Path:
    skill = root / "skill"
    for rel in (
        "scripts/spec_check.py",
        "scripts/zango_platform.py",
        "scripts/selftest_runtime.py",
        "scripts/lucide_icons.py",
        "scripts/prune_first_migration.py",
        "assets/backend/zas_core/__init__.py",
        "assets/backend/zas_core/expr.py",
        "assets/frontend/zas/index.ts",
        "assets/frontend/patches/@zango-core+crud+2.0.0.patch",
        "assets/templates/frontend/index.css",
    ):
        (skill / rel).parent.mkdir(parents=True, exist_ok=True)
        (skill / rel).write_text("# stub\n")
    return skill


class FakeRun:
    """Stands in for subprocess.run; records argv/env and plays scripted outcomes."""

    def __init__(self, workspace: Path, outcomes=None):
        self.ws = workspace
        self.calls = []
        self.outcomes = outcomes or {}

    def key(self, argv):
        joined = " ".join(argv)
        for name in ("spec_check.py", "selftest_runtime.py", "lucide_icons.py", "prune_first_migration.py"):
            if name in joined:
                return name + (" --audit-holes" if "--audit-holes" in argv else "")
        if "zango_platform.py" in joined:
            return "platform:" + argv[argv.index(next(a for a in argv if a.endswith("zango_platform.py"))) + 1]
        if "-m" in argv:
            return argv[argv.index("-m") + 1]
        if "-c" in argv:
            return "probe"
        return " ".join(argv[:3])

    def __call__(self, argv, **kw):
        key = self.key(argv)
        self.calls.append((key, list(argv), kw.get("env") or {}, kw.get("cwd")))
        outcome = self.outcomes.get(key)
        if callable(outcome):
            outcome = outcome(argv)
        rc = 0 if outcome is None else outcome
        if key == "spec_check.py":
            zas = self.ws / ".zas"
            zas.mkdir(exist_ok=True)
            (zas / "spec.resolved.json").write_text(json.dumps(RESOLVED))
            (zas / "spec.ui.json").write_text("{}")
            if rc == 1:
                (zas / "issues.md").write_text(
                    "# Spec issues\n\n- **error** `roles.Boss`: unknown role Fix: declare it\n"
                    "- **warn** `x`: fine\n"
                )
        if key == "lucide_icons.py":
            (self.ws / ".zas" / "menu_icons.json").write_text("{}")
        return subprocess.CompletedProcess(argv, rc, stdout=f"{key} out\n", stderr="")


class StudioTestBase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="studio-"))
        self.skill = make_skill(self.root)
        self.ws = self.root / "proj" / "workspaces" / "demo_app"
        (self.ws / "backend").mkdir(parents=True)
        (self.ws / "migrations").mkdir()
        (self.ws / "settings.json").write_text(
            json.dumps({"app_name": "demo_app", "modules": [{"name": "app", "path": "backend.app"}]})
        )
        self.run_dir = self.root / "run"
        (self.run_dir / "spec").mkdir(parents=True)
        self.spec = self.run_dir / "spec" / "app_spec.yaml"
        self.spec.write_text(SPEC)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def build(self, **kw):
        defaults = dict(
            skill_dir=str(self.skill),
            workspace=str(self.ws),
            spec_path=str(self.spec),
            run_dir=str(self.run_dir),
            base_dir=str(self.root / "proj"),
            app_name="demo_app",
            app_domain="demo.local",
        )
        defaults.update(kw)
        return StudioBuild(**defaults)


class DetectionTests(StudioTestBase):
    def test_only_a_skill_with_the_spec_checker_is_a_studio_build(self):
        self.assertTrue(is_studio(SimpleNamespace(skill_dir=str(self.skill))))
        (self.skill / "scripts" / "spec_check.py").unlink()
        self.assertFalse(is_studio(SimpleNamespace(skill_dir=str(self.skill))))
        self.assertFalse(is_studio(SimpleNamespace(skill_dir="")))
        self.assertFalse(is_studio(None))


class PrepareTests(StudioTestBase):
    def test_spec_check_runtime_selftest_in_order_with_a_clean_environment(self):
        fake = FakeRun(self.ws)
        build = self.build()
        events = []
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "sk-secret", "PLATFORM_USER_PASSWORD": "leak"}
        ):
            build.prepare(emit=lambda kind, msg, **k: events.append((kind, msg)))

        self.assertEqual(
            [s.step for s in build.steps],
            ["studio:spec_check", "studio:runtime", "studio:selftest", "studio:frontend"],
        )
        key, argv, env, cwd = fake.calls[0]
        self.assertEqual(key, "spec_check.py")
        self.assertEqual(argv[0], sys.executable)
        # The checker reads a re-emitted copy of the approved spec, never the original.
        self.assertTrue(argv[2].endswith("app_spec.build.yaml"))
        self.assertEqual(argv[3:5], ["--workspace", str(self.ws)])
        self.assertEqual(cwd, str(self.skill / "scripts"))
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("PLATFORM_USER_PASSWORD", env)
        self.assertEqual(env["ZAS_CONFIG"], str(self.run_dir / "zango-config.json"))
        config = json.loads((self.run_dir / "zango-config.json").read_text())
        self.assertEqual(config["setup_mode"], "venv")
        self.assertEqual(config["project_dir"], str(self.root / "proj"))

        core = self.ws / "backend" / "zas_core"
        self.assertTrue((core / "expr.py").is_file())
        self.assertEqual(json.loads((core / "spec.json").read_text()), RESOLVED)
        settings = json.loads((self.ws / "settings.json").read_text())
        self.assertEqual([m["name"] for m in settings["modules"]], ["app", "zas_core"])

        # Again (an update build): still one zas_core module.
        with mock.patch.object(studio_build.subprocess, "run", FakeRun(self.ws)):
            self.build().prepare()
        settings = json.loads((self.ws / "settings.json").read_text())
        self.assertEqual([m["name"] for m in settings["modules"]], ["app", "zas_core"])

    def test_spec_errors_stop_the_build_before_the_agent(self):
        fake = FakeRun(self.ws, {"spec_check.py": 1})
        build = self.build()
        with mock.patch.object(studio_build.subprocess, "run", fake):
            with self.assertRaises(StudioError) as caught:
                build.prepare()
        self.assertEqual(caught.exception.error_type, "SpecCheckFailed")
        self.assertIn("unknown role", str(caught.exception))
        self.assertNotIn("fine", str(caught.exception))
        self.assertEqual([c[0] for c in fake.calls], ["spec_check.py"])  # nothing after it
        self.assertFalse((self.ws / "backend" / "zas_core").exists())

    def test_a_failing_runtime_selftest_stops_the_build(self):
        fake = FakeRun(self.ws, {"selftest_runtime.py": 1})
        with mock.patch.object(studio_build.subprocess, "run", fake):
            with self.assertRaises(StudioError) as caught:
                self.build().prepare()
        self.assertEqual(caught.exception.error_type, "RuntimeSelfTestFailed")

    def test_the_frontend_is_skipped_without_node(self):
        build = self.build(frontend_allowed=False)
        with mock.patch.object(studio_build.subprocess, "run", FakeRun(self.ws)):
            build.prepare()
        self.assertFalse(build.frontend_ready)
        self.assertIn("AGENT_MODE_ALLOW_FRONTEND_BUILD", build.frontend_reason)
        self.assertTrue(build.steps[-1].skipped_reason)

    def test_the_frontend_is_prepared_with_pinned_packages_and_the_patch(self):
        def scaffold(argv):
            fe = self.ws / "frontend"
            (fe / "src").mkdir(parents=True)
            (fe / "package.json").write_text(json.dumps({"name": "x", "scripts": {"dev": "vite"}}))
            return 0

        fake = FakeRun(self.ws, {"npx --yes @zango-core/create-zango-app": scaffold})
        build = self.build(frontend_allowed=True)
        with mock.patch.object(studio_build.subprocess, "run", fake):
            build.prepare()
        self.assertTrue(build.frontend_ready, build.frontend_reason)
        npm = [c[1] for c in fake.calls if c[1][0] in ("npm", "npx")]
        self.assertEqual(npm[0][:3], ["npx", "--yes", "@zango-core/create-zango-app"])
        self.assertIn("@zango-core/crud@2.0.0", npm[1])
        self.assertIn("lucide-react@1.31.0", npm[1])
        self.assertIn("--save-exact", npm[1])
        self.assertIn("patch-package", npm[2])
        self.assertEqual(npm[3], ["npx", "--no", "patch-package"])
        fe = self.ws / "frontend"
        self.assertEqual(json.loads((fe / "package.json").read_text())["scripts"]["postinstall"], "patch-package")
        self.assertTrue((fe / "patches" / "@zango-core+crud+2.0.0.patch").is_file())
        self.assertTrue((fe / "src" / "zas" / "index.ts").is_file())
        self.assertTrue((fe / "src" / "custom" / "spec.ui.json").is_file())
        self.assertTrue((fe / "src" / "index.css").is_file())
        env_line = (fe / ".env").read_text().strip()
        self.assertEqual(env_line, "VITE_PROXY_ROUTES=/api,/zango,/appbuilder,/crud,/workflow,/orders,")
        self.assertEqual(fake.calls[-1][0], "lucide_icons.py")


def manage_stub(order, makes_initial=False, fail=None):
    def run_step(step, args, base_dir, timeout=300):
        order.append(step)
        if makes_initial and args[0] == "ws_makemigration":
            Path(makes_initial).write_text("operations = []\n")
        return StepResult(step=step, command=["manage.py", *args], returncode=1 if step == fail else 0)

    return run_step


CREDS = {"PLATFORM_USERNAME": "agent-build-x@agent-mode.invalid", "PLATFORM_USER_PASSWORD": "Secr3t!pass"}


class BringUpTests(StudioTestBase):
    def bring_up(self, build, fake, order, **manage):
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub(order, **manage)
        ), mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")):
            events = []
            ok = build.bring_up(CREDS, emit=lambda kind, msg, **k: events.append((msg, k.get("data"))))
        return ok, events

    def test_order_and_prune_on_the_first_build_only(self):
        (self.ws / ".zas").mkdir()
        (self.ws / ".zas" / "menu_icons.json").write_text("{}")
        initial = self.ws / "migrations" / "0001_initial.py"
        fake = FakeRun(self.ws)
        order = []
        build = self.build(first_build=True)
        ok, events = self.bring_up(build, fake, order, makes_initial=str(initial))
        self.assertTrue(ok)
        self.assertEqual(
            [s.step for s in build.steps],
            [
                "studio:platform:roles",
                "studio:ws_makemigration",
                "studio:prune_first_migration",
                "studio:ws_migrate",
                "studio:platform:sync",
                "studio:platform:schedule",
                "studio:platform:users",
                "studio:platform:check",
                "studio:sync_static",
                "studio:collectstatic",
                "studio:platform:appbuilder",
            ],
        )
        prune = next(c for c in fake.calls if c[0] == "prune_first_migration.py")
        self.assertEqual(prune[1][-1], str(initial))

        # Credentials: only in the platform script's environment, nowhere else.
        for key, argv, env, _ in fake.calls:
            if key.startswith("platform:"):
                self.assertEqual(env["PLATFORM_USER_PASSWORD"], CREDS["PLATFORM_USER_PASSWORD"])
                self.assertIn("--platform", argv)
            else:
                self.assertNotIn("PLATFORM_USER_PASSWORD", env)
            self.assertNotIn(CREDS["PLATFORM_USER_PASSWORD"], " ".join(argv))
        dumped = json.dumps([s.to_dict() for s in build.steps]) + json.dumps(events, default=str)
        self.assertNotIn(CREDS["PLATFORM_USER_PASSWORD"], dumped)

        later = self.build(first_build=False)
        order = []
        self.bring_up(later, FakeRun(self.ws), order)
        prune = next(s for s in later.steps if s.step == "studio:prune_first_migration")
        self.assertTrue(prune.skipped_reason)

    def test_a_failed_migration_skips_everything_after_it(self):
        build = self.build(first_build=False)
        ok, _ = self.bring_up(build, FakeRun(self.ws), [], fail="studio:ws_migrate")
        self.assertFalse(ok)
        after = [s for s in build.steps if s.step in ("studio:platform:sync", "studio:platform:appbuilder")]
        self.assertTrue(all(s.skipped_reason for s in after))

    def test_appbuilder_is_skipped_without_menu_icons(self):
        build = self.build(first_build=False, frontend_reason="no node")
        ok, _ = self.bring_up(build, FakeRun(self.ws), [])
        self.assertTrue(ok)  # skipped, not failed
        step = build.steps[-1]
        self.assertEqual(step.step, "studio:platform:appbuilder")
        self.assertIn("menu icons", step.skipped_reason)


def results_writer(ws: Path, layer: str, records):
    def write(argv):
        path = ws / ".zas" / "test_results.json"
        data = json.loads(path.read_text()) if path.is_file() else {"results": []}
        data["results"] = [r for r in data["results"] if r.get("layer") != layer] + [
            {"layer": layer, **r} for r in records(argv)
        ]
        path.write_text(json.dumps(data))
        return 1 if any(r["status"] == "fail" for r in records(argv)) else 0

    return write


class VerifyTests(StudioTestBase):
    def setUp(self):
        super().setUp()
        zas = self.ws / ".zas"
        zas.mkdir()
        (zas / "test_users.json").write_text(json.dumps({"users": [
            {"email": "test.manager@demo-app.test", "password": "Pw1!xxxx", "roles": ["Manager"]}
        ]}))

    def patches(self, fake, playwright=False):
        return [
            mock.patch.object(studio_build.subprocess, "run", fake),
            mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")),
            mock.patch.object(StudioBuild, "has_playwright", return_value=playwright),
        ]

    def test_browser_layers_are_skipped_not_passed_without_playwright(self):
        fake = FakeRun(self.ws, {
            "zas_test.api": results_writer(self.ws, "api", lambda a: [{"id": "access.order.Manager", "status": "pass"}]),
            "zas_test.design": results_writer(self.ws, "design", lambda a: [{"id": "design.lint", "status": "pass"}]),
            "zas_test.scenarios": results_writer(self.ws, "scenarios", lambda a: []),
        })
        build = self.build(frontend_ready=True)
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            StudioBuild, "app_reachable", return_value=(True, "")
        ), mock.patch.object(StudioBuild, "has_playwright", return_value=False):
            layers = build.verify()
        self.assertEqual(layers["ui"].status, "skip")
        self.assertEqual(layers["ui"].reason, PLAYWRIGHT_REASON)
        self.assertEqual(layers["design"].status, "skip")
        self.assertEqual(layers["api"].status, "pass")
        self.assertEqual(layers["design_lint"].status, "pass")
        ran = [c[0] for c in fake.calls]
        self.assertNotIn("zas_test.ui", ran)
        lint = next(c for c in fake.calls if c[0] == "zas_test.design")
        self.assertEqual(lint[1][-2:], ["--only", "lint"])

    def test_unreachable_app_skips_the_layers_that_sign_in(self):
        build = self.build()
        with mock.patch.object(studio_build.subprocess, "run", FakeRun(self.ws)), mock.patch.object(
            StudioBuild, "app_reachable", return_value=(False, "demo.local does not answer")
        ), mock.patch.object(StudioBuild, "has_playwright", return_value=True):
            layers = build.verify()
        for name in ("api", "ui", "design", "scenarios"):
            self.assertEqual(layers[name].status, "skip", name)
            self.assertIn("does not answer", layers[name].reason)
        self.assertEqual(layers["audit_holes"].status, "pass")

    def test_a_failing_group_goes_back_to_the_agent_and_only_it_is_rerun(self):
        state = {"round": 0}

        def api_records(argv):
            if state["round"] == 0:
                return [
                    {"id": "transition.order.approve", "title": "Manager approves", "role": "Manager",
                     "spec_path": "modules.orders.order.workflow", "status": "fail", "detail": "HTTP 403"},
                    {"id": "access.order.Manager", "status": "pass"},
                ]
            return [{"id": "transition.order.approve", "status": "pass"}]

        fake = FakeRun(self.ws, {
            "zas_test.api": results_writer(self.ws, "api", api_records),
            "zas_test.design": results_writer(self.ws, "design", lambda a: [{"id": "design.lint", "status": "pass"}]),
            "zas_test.scenarios": results_writer(self.ws, "scenarios", lambda a: []),
        })
        digests = []

        def resume(digest):
            digests.append(digest)
            state["round"] = 1
            return True

        build = self.build(first_build=False)
        (self.ws / ".zas" / "menu_icons.json").write_text("{}")
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub([])
        ), mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")), mock.patch.object(
            StudioBuild, "has_playwright", return_value=False
        ):
            outcome = build.finish(CREDS, resume_agent=resume, rounds=2)

        self.assertTrue(outcome.ok, {n: l.to_dict() for n, l in outcome.layers.items()})
        self.assertEqual(outcome.rounds, 1)
        self.assertEqual(len(digests), 1)
        self.assertIn("transition.order.approve", digests[0])
        self.assertIn("HTTP 403", digests[0])
        api_runs = [c[1] for c in fake.calls if c[0] == "zas_test.api"]
        self.assertEqual(len(api_runs), 2)
        self.assertNotIn("--only", api_runs[0])
        self.assertEqual(api_runs[1][-2:], ["--only", "transitions"])
        self.assertEqual([c[0] for c in fake.calls].count("zas_test.scenarios"), 1)  # not re-run
        self.assertIn("ui", outcome.skipped)

    def test_fix_rounds_stop_when_the_agent_cannot_continue(self):
        fake = FakeRun(self.ws, {
            "spec_check.py --audit-holes": 1,
            "zas_test.design": results_writer(self.ws, "design", lambda a: []),
            "zas_test.api": results_writer(self.ws, "api", lambda a: []),
            "zas_test.scenarios": results_writer(self.ws, "scenarios", lambda a: []),
        })
        calls = []
        build = self.build(first_build=False)
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub([])
        ), mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")), mock.patch.object(
            StudioBuild, "has_playwright", return_value=False
        ):
            outcome = build.finish(CREDS, resume_agent=lambda d: calls.append(d) or False, rounds=2)
        self.assertFalse(outcome.ok)
        self.assertEqual(len(calls), 1)
        self.assertEqual(outcome.failing, ["audit_holes"])

    def test_test_users_are_read_into_the_runs_format(self):
        users = self.build().test_users()
        self.assertEqual(users, [{"email": "test.manager@demo-app.test", "role": "Manager",
                                  "status": "created", "password": "Pw1!xxxx"}])


class GuardTests(unittest.TestCase):
    def test_only_the_offline_type_check_is_added(self):
        from zango.apps.agent_mode.guards import check_bash

        for cmd in ("npx --no tsc --noEmit", "npx --no-install tsc --noEmit", "cd frontend && npx --no tsc --noEmit"):
            self.assertTrue(check_bash(cmd, app_name="X", allow_frontend=True)[0], cmd)
        for cmd in ("npx tsc --noEmit", "npx --no tsc", "npx --no tsc --noEmit && npx tsc", "npx --no patch-package"):
            self.assertFalse(check_bash(cmd, app_name="X", allow_frontend=True)[0], cmd)
        self.assertFalse(check_bash("npx --no tsc --noEmit", app_name="X", allow_frontend=False)[0])


class PromptTests(StudioTestBase):
    def test_the_studio_prompt_points_at_server_mode_and_says_what_was_skipped(self):
        from zango.apps.agent_mode.prompt import compose_studio_prompt

        tb = SimpleNamespace(
            skill="zango-tpl-zango-app:zango-app-studio",
            skill_dir=str(self.skill),
            spec_path=str(self.spec),
            template=SimpleNamespace(name="Ordering Portal", version="1.0.0"),
        )
        ctx = SimpleNamespace(app_name="demo_app", workspace_path=str(self.ws), primary_domain="demo.local")
        skipped = self.build(frontend_reason="node is not installed")
        text = compose_studio_prompt(ctx, tb, skipped)
        self.assertTrue(text.startswith("/zango-tpl-zango-app:zango-app-studio"))
        self.assertIn(f"{self.skill}/references/server-mode.md", text)
        self.assertIn("SKIPPED (node is not installed)", text)
        self.assertNotIn("npx --no tsc", text)
        ready = self.build(frontend_ready=True, update=True)
        text = compose_studio_prompt(ctx, tb, ready)
        self.assertIn("npx --no tsc --noEmit", text)
        self.assertIn("UPDATE build", text)


class ReportSerializerTests(unittest.TestCase):
    def test_report_is_none_until_a_studio_build_records_one(self):
        from zango.api.platform.agent_mode.v1.serializers import AgentRunDetailSerializer

        s = AgentRunDetailSerializer()
        self.assertIsNone(s.get_report(SimpleNamespace(studio_report=None)))
        data = s.get_report(SimpleNamespace(studio_report={
            "ok": False, "rounds": 1, "layers": {"api": {"status": "fail"}},
            "skipped": [{"layer": "ui", "reason": PLAYWRIGHT_REASON}],
            "report": {"summary_md": "# Build report", "html_path": "/w/.zas/build_report.html"},
        }))
        self.assertEqual(data["summary_md"], "# Build report")
        self.assertEqual(data["html_path"], "/w/.zas/build_report.html")
        self.assertEqual(data["rounds"], 1)
        self.assertFalse(data["ok"])


from zango.tests.apps.app_templates.tests import AppTemplatesTestBase  # noqa: E402


class ServiceAccountTests(AppTemplatesTestBase):
    def test_minted_for_the_app_and_disabled_afterwards_even_on_failure(self):
        from django.contrib.auth.models import User

        from zango.apps.shared.platformauth.models import PlatformUserModel

        tenant = SimpleNamespace(uuid="00000000-0000-0000-0000-000000000000")
        with studio_build.service_account(tenant) as creds:
            user = PlatformUserModel.objects.get(email=creds["PLATFORM_USERNAME"])
            self.assertFalse(user.is_superadmin)
            self.assertTrue(user.is_active)
            self.assertTrue(user.check_password(creds["PLATFORM_USER_PASSWORD"]))
            self.assertTrue(PlatformUserModel.validate_password(creds["PLATFORM_USER_PASSWORD"]))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.apps.exists())
        self.assertFalse(User.objects.get(pk=user.user_id).is_active)

        with self.assertRaises(RuntimeError):
            with studio_build.service_account(tenant) as creds:
                raise RuntimeError("bring-up blew up")
        self.assertFalse(PlatformUserModel.objects.get(email=creds["PLATFORM_USERNAME"]).is_active)


class FinishStudioTests(StudioTestBase):
    def finish(self, outcome):
        from zango.apps.agent_mode import tasks
        from zango.apps.agent_mode.snapshot import workspace_manifest
        from zango.apps.agent_mode.studio_build import LayerResult, StudioOutcome

        saved = []
        run = SimpleNamespace(pk=1, save=lambda update_fields=None: saved.append(update_fields))
        build = self.build()
        build.steps = [StepResult(step="studio:ws_migrate", returncode=0)]
        layers = {n: LayerResult(name=n, **kw) for n, kw in outcome.pop("layers").items()}
        build.finish = mock.Mock(return_value=StudioOutcome(layers=layers, **outcome))
        recorder = mock.Mock()

        @contextlib.contextmanager
        def account(tenant):
            yield dict(CREDS)

        with mock.patch.object(tasks, "_abort_requested", return_value=False):
            status, extra = tasks._finish_studio(
                run=run, tenant=None, studio=build, state={}, recorder=recorder,
                emit=lambda *a, **k: None, drive=None, new_stream=lambda d: None,
                baseline_manifest=workspace_manifest(str(self.ws)), service_account=account, rounds=2,
            )
        build.finish.assert_called_once()
        self.assertEqual(build.finish.call_args.args[0], CREDS)
        return run, status, extra

    def test_success_records_the_report_and_skips(self):
        run, status, extra = self.finish({
            "ok": True, "bring_up_ok": True, "rounds": 0,
            "report": {"summary_md": "# ok", "html_path": "/x.html"},
            "layers": {"api": {"counts": {"pass": 3}}, "ui": {"status": "skip", "reason": PLAYWRIGHT_REASON}},
        })
        self.assertEqual((status, extra), ("success", {}))
        self.assertEqual(run.studio_report["skipped"], [{"layer": "ui", "reason": PLAYWRIGHT_REASON}])
        self.assertEqual(run.post_steps[0]["step"], "studio:ws_migrate")

    def test_failing_checks_make_the_run_partial(self):
        run, status, extra = self.finish({
            "ok": False, "bring_up_ok": True, "rounds": 2, "report": {},
            "layers": {"api": {"status": "fail", "failures": [{"id": "tag.x"}]}},
        })
        self.assertEqual(status, "partial")
        self.assertEqual(extra["error_type"], "StudioChecksFailed")
        self.assertIn("api (1)", extra["error_message"])
        self.assertIn("2 fix round", extra["error_message"])
