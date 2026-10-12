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
            StudioBuild, "has_playwright", return_value=True
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
        self.assertFalse(outcome.waiting)

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
            StudioBuild, "has_playwright", return_value=True
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
        build = self.build(frontend_ready=outcome.pop("frontend_ready", True))
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


class FrontendPrepTests(StudioTestBase):
    """The scaffold's own install may fail on a peer conflict; anything else stops the build."""

    def scaffold_files(self, rc):
        def scaffold(argv):
            fe = self.ws / "frontend"
            (fe / "src").mkdir(parents=True, exist_ok=True)
            (fe / "package.json").write_text(json.dumps({"name": "x", "scripts": {}}))
            return rc

        return scaffold

    def test_a_failed_scaffold_install_is_recovered_by_the_pinned_install(self):
        fake = FakeRun(self.ws, {"npx --yes @zango-core/create-zango-app": self.scaffold_files(1)})
        build = self.build(frontend_allowed=True)
        with mock.patch.object(studio_build.subprocess, "run", fake):
            build.prepare()
        self.assertTrue(build.frontend_ready, build.frontend_reason)
        scaffold = next(c for c in fake.calls if c[0] == "npx --yes @zango-core/create-zango-app")
        self.assertEqual(scaffold[2].get("npm_config_legacy_peer_deps"), "true")
        self.assertTrue(any("@zango-core/crud@2.0.0" in c[1] for c in fake.calls))

    def test_a_scaffold_that_wrote_nothing_stops_the_build(self):
        fake = FakeRun(self.ws, {"npx --yes @zango-core/create-zango-app": 1})
        with mock.patch.object(studio_build.subprocess, "run", fake):
            with self.assertRaises(StudioError) as caught:
                self.build(frontend_allowed=True).prepare()
        self.assertEqual(caught.exception.error_type, "FrontendPrepFailed")
        self.assertIn("/app", str(caught.exception))

    def test_a_failed_pinned_install_stops_the_build_with_npms_reason(self):
        def pin(argv):
            return 1

        fake = FakeRun(self.ws, {
            "npx --yes @zango-core/create-zango-app": self.scaffold_files(0),
            "npm install --save-exact": pin,
        })
        original = FakeRun.__call__

        def call(self_, argv, **kw):
            result = original(self_, argv, **kw)
            if argv[:3] == ["npm", "install", "--save-exact"]:
                result.stderr = "npm error code ERESOLVE\nnpm error /x/_logs/1-eresolve-report.txt"
            return result

        with mock.patch.object(FakeRun, "__call__", call), mock.patch.object(
            studio_build.subprocess, "run", fake
        ):
            with self.assertRaises(StudioError) as caught:
                self.build(frontend_allowed=True).prepare()
        self.assertEqual(caught.exception.error_type, "FrontendPrepFailed")
        self.assertIn("peer dependencies", str(caught.exception))
        self.assertIn("eresolve-report.txt", str(caught.exception))


class AppShellTests(StudioTestBase):
    def shell(self, *, route=True, module=True, html=True, build="zango-app.123.min.js", deploy=True):
        ws = self.ws
        settings = json.loads((ws / "settings.json").read_text())
        settings["modules"] = [{"name": "app", "path": "backend.app"}] if module else []
        settings["app_routes"] = [{"module": "core", "re_path": "^core/", "url": "urls"}]
        if route:
            settings["app_routes"].append({"module": "app", "re_path": "^", "url": "urls"})
        (ws / "settings.json").write_text(json.dumps(settings))
        app = ws / "backend" / "app"
        (app / "templates").mkdir(parents=True, exist_ok=True)
        (app / "urls.py").write_text("urlpatterns = []\n")
        (app / "views.py").write_text("\n")
        (ws / "frontend" / "src").mkdir(parents=True, exist_ok=True)
        (ws / "frontend" / "src" / "App.tsx").write_text("export {}\n")
        (app / "templates" / "app.html").unlink(missing_ok=True)
        shutil.rmtree(ws / "static", ignore_errors=True)
        if html:
            (app / "templates" / "app.html").write_text(
                f"<script type=\"module\" src=\"{{% zstatic 'js/{build}' %}}\"></script>"
            )
        if deploy:
            (ws / "static" / "js").mkdir(parents=True, exist_ok=True)
            (ws / "static" / "js" / build).write_text("// build\n")
        return self.build(frontend_ready=True)

    def ids(self, layer):
        return [f["id"] for f in layer.failures]

    def test_a_complete_shell_passes(self):
        layer = self.shell().check_app_shell()
        self.assertEqual(layer.status, "pass", layer.failures)

    def test_what_is_missing_is_named(self):
        self.assertIn("app_shell.route", self.ids(self.shell(route=False).check_app_shell()))
        self.assertIn("app_shell.module", self.ids(self.shell(module=False).check_app_shell()))
        self.assertIn("app_shell.file:templates/app.html", self.ids(self.shell(html=False).check_app_shell()))
        self.assertIn("app_shell.build_file", self.ids(self.shell(deploy=False).check_app_shell()))
        self.assertIn("app_shell.build_ref", self.ids(self.shell(build="{{BUILD_FILE}}").check_app_shell()))

    def test_a_build_older_than_the_sources_is_stale(self):
        build = self.shell()
        old = self.ws / "static" / "js" / "zango-app.123.min.js"
        os.utime(old, (1_000_000, 1_000_000))
        self.assertIn("app_shell.stale", self.ids(build.check_app_shell()))

    def test_it_runs_first_and_is_skipped_without_a_frontend(self):
        build = self.build(frontend_ready=False, frontend_reason="Node tooling is not enabled")
        with mock.patch.object(studio_build.subprocess, "run", FakeRun(self.ws)), mock.patch.object(
            StudioBuild, "app_reachable", return_value=(False, "no")
        ), mock.patch.object(StudioBuild, "has_playwright", return_value=False):
            layers = build.verify()
        self.assertEqual(list(layers)[0], "app_shell")
        self.assertEqual(layers["app_shell"].status, "skip")
        self.assertIn("Node tooling", layers["app_shell"].reason)

    def test_a_missing_shell_goes_back_to_the_agent(self):
        build = self.shell(route=False)
        layers = {"app_shell": build.check_app_shell()}
        digest = build.digest(True, layers)
        self.assertIn("app_shell.route", digest)


class NoFrontendOutcomeTests(FinishStudioTests):
    def test_a_build_without_a_frontend_is_partial_and_says_so(self):
        run, status, extra = self.finish({
            "ok": True, "bring_up_ok": True, "rounds": 0, "report": {}, "frontend_ready": False,
            "layers": {"app_shell": {"status": "skip", "reason": "no frontend"}},
        })
        self.assertEqual(status, "partial")
        self.assertEqual(extra["error_type"], "StudioNoFrontend")
        self.assertIn("/app is not served", extra["error_message"])
        self.assertEqual(run.studio_report["not_verified"], ["app_shell"])


class WaitingTests(VerifyTests):
    """A build pauses for what only the user can fix, and continues from its checkpoint."""

    def fake(self):
        return FakeRun(self.ws, {
            "zas_test.api": results_writer(self.ws, "api", lambda a: [{"id": "access.order.Manager", "status": "pass"}]),
            "zas_test.ui": results_writer(self.ws, "ui", lambda a: [{"id": "ui.menu.Manager", "status": "pass"}]),
            "zas_test.design": results_writer(self.ws, "design", lambda a: [{"id": "design.lint", "status": "pass"}]),
            "zas_test.scenarios": results_writer(self.ws, "scenarios", lambda a: []),
        })

    def run_finish(self, build, fake, *, reachable=True, playwright=True, **kw):
        why = "the app's domain does not answer from the platform (http://demo.local:8000/: URLError)."
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub([])
        ), mock.patch.object(
            StudioBuild, "app_reachable", return_value=(reachable, "" if reachable else why)
        ), mock.patch.object(StudioBuild, "has_playwright", return_value=playwright):
            return build.finish(CREDS, resume_agent=None, rounds=2, **kw)

    def ready_build(self):
        (self.ws / ".zas" / "menu_icons.json").write_text("{}")
        (self.ws / "frontend").mkdir(exist_ok=True)  # an earlier build's frontend: the UI layer runs
        return self.build(first_build=False, frontend_ready=False)

    def test_an_unreachable_domain_pauses_after_everything_independent_ran(self):
        fake = self.fake()
        build = self.ready_build()
        outcome = self.run_finish(build, fake, reachable=False)

        self.assertTrue(outcome.waiting)
        action = outcome.pending_actions[0]
        self.assertEqual(action["kind"], "hosts_entry")
        self.assertEqual(action["command"], 'echo "127.0.0.1 demo.local" | sudo tee -a /etc/hosts')
        self.assertIn("demo.local", action["title"])
        self.assertEqual(action["blocks"], ["platform:appbuilder", "api", "ui", "design", "scenarios"])
        self.assertNotIn("reason", action)

        ran = [c[0] for c in fake.calls]
        self.assertIn("platform:check", ran)          # the bring-up before appbuilder ran
        self.assertNotIn("platform:appbuilder", ran)  # held
        self.assertIn("spec_check.py --audit-holes", ran)
        self.assertEqual(ran.count("zas_test.design"), 1)  # the lint only
        for name in ("zas_test.api", "zas_test.ui", "zas_test.scenarios", "zas_test.report"):
            self.assertNotIn(name, ran)
        self.assertEqual(set(outcome.layers), {"app_shell", "audit_holes", "design_lint"})
        held = next(s for s in build.steps if s.step == "studio:platform:appbuilder")
        self.assertIn("held until you complete", held.skipped_reason)

        cp = outcome.checkpoint
        self.assertEqual(cp["held_steps"], ["appbuilder"])
        self.assertEqual(cp["held_layers"], ["api", "ui", "design", "scenarios"])
        self.assertEqual(cp["build"]["workspace"], str(self.ws))
        json.dumps(cp)  # it is stored on the run

    def test_a_remote_platform_gets_a_dns_instruction_and_no_command(self):
        build = self.build(first_build=False, platform_url="https://console.example.com")
        with mock.patch.object(StudioBuild, "app_reachable", return_value=(False, "no")), mock.patch.object(
            StudioBuild, "has_playwright", return_value=True
        ):
            (action,) = build.environment_actions()
        self.assertEqual(action["command"], "")
        self.assertIn("DNS record", action["detail"])

    def test_missing_playwright_pauses_only_the_browser_checks(self):
        fake = self.fake()
        outcome = self.run_finish(self.ready_build(), fake, playwright=False)
        self.assertTrue(outcome.waiting)
        (action,) = outcome.pending_actions
        self.assertEqual(action["kind"], "install_playwright")
        self.assertIn("-m pip install playwright", action["command"])
        self.assertEqual(action["blocks"], ["ui", "design"])
        ran = [c[0] for c in fake.calls]
        self.assertIn("platform:appbuilder", ran)
        self.assertIn("zas_test.api", ran)
        self.assertNotIn("zas_test.ui", ran)
        self.assertEqual(outcome.checkpoint["held_layers"], ["ui", "design"])
        self.assertEqual(outcome.checkpoint["held_steps"], [])

    def test_continuing_runs_only_what_was_held_then_finishes(self):
        first = self.run_finish(self.ready_build(), self.fake(), reachable=False)
        checkpoint = json.loads(json.dumps(first.checkpoint))

        fake = self.fake()
        build = StudioBuild.from_checkpoint(checkpoint)
        self.assertEqual(build.workspace, str(self.ws))
        outcome = self.run_finish(build, fake, checkpoint=checkpoint)

        self.assertFalse(outcome.waiting)
        self.assertTrue(outcome.ok, {n: l.to_dict() for n, l in outcome.layers.items()})
        ran = [c[0] for c in fake.calls]
        self.assertEqual(
            [r for r in ran if r != "probe"],
            ["platform:appbuilder", "zas_test.api", "zas_test.ui", "zas_test.design", "zas_test.scenarios",
             "zas_test.report"],
        )
        self.assertEqual(
            set(outcome.layers),
            {"app_shell", "audit_holes", "design_lint", "api", "ui", "design", "scenarios"},
        )
        self.assertEqual(outcome.layers["audit_holes"].status, "pass")  # carried over, not re-run

    def test_skipping_finishes_with_those_checks_not_verified(self):
        first = self.run_finish(self.ready_build(), self.fake(), reachable=False)
        fake = self.fake()
        build = StudioBuild.from_checkpoint(first.checkpoint)
        outcome = self.run_finish(build, fake, reachable=False, checkpoint=first.checkpoint, skip=True)

        self.assertFalse(outcome.waiting)
        self.assertTrue(outcome.ok)
        self.assertEqual([c[0] for c in fake.calls if c[0] != "probe"], ["zas_test.report"])
        for name in ("api", "ui", "design", "scenarios"):
            self.assertEqual(outcome.layers[name].status, "skip")
            self.assertIn("skipped by the user: Point demo.local", outcome.layers[name].reason)
        step = next(s for s in build.steps if s.step == "studio:platform:appbuilder")
        self.assertIn("skipped by the user", step.skipped_reason)

    def test_a_failed_bring_up_does_not_wait_for_the_user(self):
        fake = self.fake()
        build = self.ready_build()
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub([], fail="studio:ws_migrate")
        ), mock.patch.object(StudioBuild, "app_reachable", return_value=(False, "no answer")), mock.patch.object(
            StudioBuild, "has_playwright", return_value=True
        ):
            outcome = build.finish(CREDS, resume_agent=None, rounds=2)
        self.assertFalse(outcome.waiting)
        self.assertFalse(outcome.bring_up_ok)
        self.assertEqual(outcome.layers["api"].status, "skip")

    def test_still_failing_names_what_is_not_done_yet(self):
        pending = [{"id": "hosts_entry", "kind": "hosts_entry", "title": "Point demo.local at this server"}]
        build = self.build()
        with mock.patch.object(StudioBuild, "app_reachable", return_value=(False, "demo.local: URLError")), \
                mock.patch.object(StudioBuild, "has_playwright", return_value=True):
            (missing,) = build.still_failing(pending)
        self.assertEqual(missing["still_failing_reason"], "demo.local: URLError")
        with mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")), \
                mock.patch.object(StudioBuild, "has_playwright", return_value=True):
            self.assertEqual(self.build().still_failing(pending), [])


class WaitingRunTests(StudioTestBase):
    """How a paused build is recorded, continued, served and left alone by the sweep."""

    def waiting_outcome(self):
        from zango.apps.agent_mode.studio_build import LayerResult, StudioOutcome

        action = {"id": "hosts_entry", "kind": "hosts_entry", "title": "Point demo.local at this server",
                  "detail": "…", "command": "echo …", "blocks": ["platform:appbuilder", "api"]}
        return StudioOutcome(
            ok=False, bring_up_ok=True, rounds=0, report={},
            layers={"audit_holes": LayerResult(name="audit_holes", counts={"pass": 1})},
            pending_actions=[action],
            checkpoint={"build": {}, "layers": {}, "rounds": 0, "held_steps": ["appbuilder"],
                        "held_layers": ["api"], "actions": [action]},
        )

    def finish(self, outcome, **kw):
        from zango.apps.agent_mode import tasks
        from zango.apps.agent_mode.snapshot import workspace_manifest

        run = SimpleNamespace(pk=1, save=lambda update_fields=None: None)
        build = self.build(frontend_ready=True)
        build.steps = [StepResult(step="studio:platform:appbuilder", returncode=0)]
        build.finish = mock.Mock(return_value=outcome)
        recorder = mock.Mock()

        @contextlib.contextmanager
        def account(tenant):
            yield dict(CREDS)

        with mock.patch.object(tasks, "_abort_requested", return_value=False):
            status, extra = tasks._finish_studio(
                run=run, tenant=None, studio=build, state={}, recorder=recorder,
                emit=lambda *a, **k: None, drive=None, new_stream=lambda d: None,
                baseline_manifest=kw.pop("baseline", workspace_manifest(str(self.ws))),
                service_account=account, rounds=2, **kw,
            )
        return run, build, recorder, status, extra

    def test_a_waiting_outcome_parks_the_run_with_its_checkpoint(self):
        from zango.apps.agent_mode import tasks

        run, build, recorder, status, extra = self.finish(self.waiting_outcome())
        self.assertEqual(status, "waiting")
        self.assertEqual(extra["pending_actions"][0]["kind"], "hosts_entry")
        self.assertEqual(extra["studio_checkpoint"]["held_layers"], ["api"])
        baseline = extra["studio_checkpoint"]["baseline"]
        self.assertTrue(Path(baseline).is_file())
        self.assertEqual(tasks._load_baseline(baseline), json.loads(Path(baseline).read_text()))
        self.assertEqual(run.studio_report["layers"]["audit_holes"]["status"], "pass")
        waiting = [c for c in recorder.emit.call_args_list if "Waiting for you" in str(c)]
        self.assertEqual(len(waiting), 1)
        self.assertNotIn("Secr3t", str(recorder.emit.call_args_list))

        parked = mock.Mock()
        tasks._conclude(parked, status, extra, mock.Mock(seq=3))
        parked.pause.assert_called_once_with(extra["pending_actions"], extra["studio_checkpoint"])
        parked.finalize.assert_not_called()

    def test_a_continuation_passes_the_checkpoint_and_keeps_the_earlier_steps(self):
        from zango.apps.agent_mode.studio_build import LayerResult, StudioOutcome

        done = StudioOutcome(ok=True, bring_up_ok=True, rounds=0, report={"verdict": "Ready"},
                             layers={"api": LayerResult(name="api", counts={"pass": 2})})
        checkpoint = self.waiting_outcome().checkpoint
        earlier = [{"step": "studio:ws_migrate", "returncode": 0}]
        run, build, _, status, extra = self.finish(
            done, checkpoint=checkpoint, skip=False, prior_steps=earlier, baseline=None
        )
        self.assertEqual((status, extra), ("success", {}))
        self.assertEqual(build.finish.call_args.kwargs["checkpoint"], checkpoint)
        self.assertFalse(build.finish.call_args.kwargs["skip"])
        self.assertEqual([s["step"] for s in run.post_steps],
                         ["studio:ws_migrate", "studio:platform:appbuilder"])

    def test_the_continue_task_re_enters_from_the_checkpoint(self):
        from zango.apps.agent_mode import tasks

        checkpoint = {"build": self.build(frontend_ready=True).build_state(), "layers": {}, "rounds": 0,
                      "held_steps": [], "held_layers": ["api"], "actions": []}
        run = mock.MagicMock()
        run.id, run.pk = 1, 1
        run.studio_checkpoint, run.post_steps = checkpoint, [{"step": "studio:ws_migrate"}]
        run.session_id, run.total_cost_usd, run.tool_use_counts = "sess-1", None, {}
        run.requirement = None
        ctx = SimpleNamespace(workspace_path=str(self.ws))
        with mock.patch("zango.apps.agent_mode.recorder.EventRecorder") as recorder_cls, \
                mock.patch("zango.apps.agent_mode.models.AgentRunEvent.objects") as events, \
                mock.patch("zango.apps.agent_mode.settings_writer.write_run_settings", return_value="/s.json"), \
                mock.patch("zango.apps.agent_mode.config.load_config", return_value=SimpleNamespace()), \
                mock.patch.object(tasks, "_apply_state"), \
                mock.patch.object(tasks, "_finish_studio", return_value=("success", {})) as finish:
            events.filter.return_value.order_by.return_value.values_list.return_value.first.return_value = 41
            recorder_cls.return_value.seq = 50
            result = tasks._continue(run, SimpleNamespace(name="demo_app"), object(), "/ws",
                                     lambda tenant: ctx, skip=True)
        self.assertEqual(recorder_cls.call_args.kwargs["start_seq"], 41)  # events carry on
        kwargs = finish.call_args.kwargs
        self.assertEqual(kwargs["checkpoint"], checkpoint)
        self.assertTrue(kwargs["skip"])
        self.assertEqual(kwargs["prior_steps"], [{"step": "studio:ws_migrate"}])
        self.assertEqual(kwargs["studio"].workspace, str(self.ws))
        self.assertEqual(kwargs["state"]["session_id"], "sess-1")
        run.finalize.assert_called_once_with("success")
        self.assertEqual(result["events"], 50)

    def test_waiting_holds_the_slot_and_the_sweep_leaves_it_alone(self):
        from zango.apps.agent_mode.models import ACTIVE_STATUSES, TERMINAL_STATUSES, AgentRun, RunStatus

        self.assertNotIn(RunStatus.WAITING, TERMINAL_STATUSES)
        self.assertNotIn(RunStatus.WAITING, ACTIVE_STATUSES)  # what the sweep reaps
        run = AgentRun(status=RunStatus.RUNNING, is_active=True)
        saved = {}
        run.save = lambda update_fields=None: saved.update(fields=update_fields)
        run.pause([{"kind": "hosts_entry"}], {"rounds": 0})
        self.assertEqual(run.status, "waiting")
        self.assertFalse(run.is_terminal)
        self.assertTrue(run.is_active)
        self.assertIn("studio_checkpoint", saved["fields"])
        run.finalize(RunStatus.SUCCESS)
        self.assertIsNone(run.pending_actions)
        self.assertIsNone(run.studio_checkpoint)

    # -- API ---------------------------------------------------------------

    def api_run(self, **kw):
        defaults = dict(pk=1, object_uuid="11111111-1111-1111-1111-111111111111", status="waiting",
                        workspace_path=str(self.ws), studio_report=None, is_terminal=False,
                        studio_checkpoint={"build": self.build().build_state()},
                        pending_actions=[{"id": "hosts_entry", "kind": "hosts_entry",
                                          "title": "Point demo.local at this server"}])
        defaults.update(kw)
        return SimpleNamespace(**defaults)

    def call_continue(self, run, body, *, missing=(), claimed=1):
        from zango.api.platform.agent_mode.v1 import views

        manager = mock.Mock()
        manager.get.return_value = run
        manager.filter.return_value.update.return_value = claimed
        with mock.patch.object(views, "_bind_tenant", return_value=SimpleNamespace(name="demo_app")), \
                mock.patch.object(views.AgentRun, "objects", manager), \
                mock.patch.object(views.transaction, "on_commit", lambda fn: fn()), \
                mock.patch.object(views, "_in_tenant", lambda tenant: contextlib.nullcontext()), \
                mock.patch.object(StudioBuild, "still_failing", return_value=list(missing)), \
                mock.patch("zango.apps.agent_mode.tasks.agent_run_continue.apply_async") as dispatch:
            dispatch.return_value = SimpleNamespace(id="task-9")
            response = views.AgentRunContinueView().post(
                SimpleNamespace(data=body), "app-uuid", run.object_uuid
            )
        return response.status_code, json.loads(response.content)["response"], dispatch, manager

    def test_continue_is_refused_while_the_fix_is_not_detected(self):
        still = [{"id": "hosts_entry", "kind": "hosts_entry", "title": "Point demo.local at this server",
                  "still_failing_reason": "demo.local: URLError"}]
        code, body, dispatch, manager = self.call_continue(self.api_run(), {"skip": False}, missing=still)
        self.assertEqual(code, 409)
        self.assertEqual(body["pending_actions"][0]["still_failing_reason"], "demo.local: URLError")
        dispatch.assert_not_called()
        manager.filter.assert_not_called()  # the run stays waiting

    def test_continue_dispatches_once_the_fix_is_in_and_skip_does_not_check(self):
        code, body, dispatch, manager = self.call_continue(self.api_run(), {"skip": False})
        self.assertEqual((code, body["status"]), (200, "syncing"))
        self.assertEqual(dispatch.call_args.kwargs["kwargs"], {"skip": False})
        self.assertEqual(manager.filter.return_value.update.call_args_list[0].kwargs["status"], "syncing")

        with mock.patch.object(StudioBuild, "environment_actions") as checks:
            code, body, dispatch, _ = self.call_continue(self.api_run(), {"skip": True})
        self.assertEqual(code, 200)
        self.assertEqual(dispatch.call_args.kwargs["kwargs"], {"skip": True})
        checks.assert_not_called()

    def test_continue_on_a_run_that_is_not_waiting_is_a_conflict(self):
        for run in (self.api_run(status="success"), self.api_run(status="syncing")):
            code, body, dispatch, _ = self.call_continue(run, {"skip": False})
            self.assertEqual(code, 409)
            dispatch.assert_not_called()
        code, _, dispatch, _ = self.call_continue(self.api_run(), {"skip": False}, claimed=0)
        self.assertEqual(code, 409)  # someone else just continued it
        dispatch.assert_not_called()

    def call_report(self, run):
        from zango.api.platform.agent_mode.v1 import views

        manager = mock.Mock()
        manager.get.return_value = run
        with mock.patch.object(views, "_bind_tenant"), mock.patch.object(views.AgentRun, "objects", manager):
            return views.AgentRunReportView().get(SimpleNamespace(), "app-uuid", run.object_uuid)

    def test_the_html_report_is_served_sandboxed_and_only_from_the_workspace(self):
        zas = self.ws / ".zas"
        zas.mkdir()
        (zas / "build_report.html").write_text("<h1>Build report</h1>")
        run = self.api_run(studio_report={"report": {"html_path": str(zas / "build_report.html")}})
        response = self.call_report(run)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Build report", response.content)
        self.assertEqual(response["Content-Security-Policy"], "sandbox allow-scripts")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertTrue(response["Content-Type"].startswith("text/html"))

        outside = self.root / "elsewhere.html"
        outside.write_text("<h1>secrets</h1>")
        for path in (str(outside), str(zas / ".." / ".." / "elsewhere.html"), str(zas / "missing.html"), ""):
            run = self.api_run(studio_report={"report": {"html_path": path}})
            self.assertEqual(self.call_report(run).status_code, 404, path)
        self.assertEqual(self.call_report(self.api_run(studio_report=None)).status_code, 404)

    def test_the_run_payload_exposes_actions_checks_and_the_report(self):
        from zango.api.platform.agent_mode.v1.serializers import (
            AgentRunDetailSerializer,
            AgentRunListSerializer,
        )

        report = {
            "ok": False, "bring_up_ok": True, "frontend": True, "rounds": 1, "not_verified": ["ui"],
            "layers": {"api": {"status": "pass"}, "ui": {"status": "skip", "reason": "x"},
                       "scenarios": {"status": "fail", "failures": [{"id": "scenarios.H-01"}]}},
            "skipped": [{"layer": "ui", "reason": "x"}],
            "report": {"verdict": "Not ready", "summary_md": "# r", "html_path": "/w/.zas/build_report.html"},
        }
        detail = AgentRunDetailSerializer()
        data = detail.get_report(SimpleNamespace(studio_report=report))
        self.assertEqual(data["verdict"], "Not ready")
        self.assertEqual(data["not_verified"], ["ui"])
        self.assertEqual(data["layers"]["scenarios"]["failures"][0]["id"], "scenarios.H-01")
        self.assertIsNone(data["html_url"])  # the detail view fills it in
        self.assertNotIn("password", json.dumps(data))
        waiting = SimpleNamespace(status="waiting", pending_actions=[{"kind": "hosts_entry"}])
        self.assertEqual(detail.get_pending_actions(waiting), [{"kind": "hosts_entry"}])
        self.assertEqual(detail.get_pending_actions(SimpleNamespace(status="success", pending_actions=None)), [])
        self.assertEqual(
            AgentRunListSerializer().get_checks(SimpleNamespace(studio_report=report)),
            {"total": 3, "passed": 1, "failed": 1, "not_verified": 1},
        )
        self.assertIsNone(AgentRunListSerializer().get_checks(SimpleNamespace(studio_report=None)))
        self.assertEqual(AgentRunListSerializer().get_pending_actions(waiting), [{"kind": "hosts_entry"}])
        self.assertEqual(
            AgentRunListSerializer().get_pending_actions(SimpleNamespace(status="failed", pending_actions=[{}])), []
        )
        self.assertIn("checks", AgentRunListSerializer.Meta.fields)
        self.assertIn("pending_actions", AgentRunListSerializer.Meta.fields)
