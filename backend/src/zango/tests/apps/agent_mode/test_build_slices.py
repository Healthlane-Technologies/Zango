"""Build in slices, and keep failures that are not the app's away from the agent.

The build agent checks each slice (one record with its pages) with studio_verify while it still
has it in mind; the test layers run only that slice's spec paths. A failure the agent traces to
the platform is reported, not patched around, and a failure a fix round did not move is not sent
again.
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import studio_build
from zango.apps.agent_mode.guards import make_pre_tool_use_guard, runtime_tamper
from zango.apps.agent_mode.studio_build import LayerResult, StudioBuild, _signature
from zango.apps.agent_mode.studio_tools import ToolCall, _paths, handle_call, verify_slice
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

from .test_studio_build import CREDS, FakeRun, StudioTestBase, manage_stub, results_writer


SCRIPTS = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import zas_test  # noqa: E402


class ScopeTests(unittest.TestCase):
    def test_a_prefix_matches_on_a_segment_boundary(self):
        p = ["entities.case"]
        self.assertTrue(zas_test.in_scope("entities.case", p))
        self.assertTrue(zas_test.in_scope("entities.case.form.create", p))
        self.assertTrue(zas_test.in_scope("entities.case.validation.rules[2]", p))
        self.assertFalse(zas_test.in_scope("entities.case_document.form", p))
        self.assertFalse(zas_test.in_scope("pages.my_cases", p))

    def test_no_scope_or_no_path_always_runs(self):
        self.assertTrue(zas_test.in_scope("pages.x", []))
        self.assertTrue(zas_test.in_scope("", ["entities.case"]))

    def test_a_scoped_run_replaces_only_its_own_results(self):
        ws = tempfile.mkdtemp(prefix="scope-")
        try:
            zas_test.save_results(ws, "api", [
                {"layer": "api", "id": "a", "spec_path": "entities.case.form", "status": "fail"},
                {"layer": "api", "id": "b", "spec_path": "entities.area.form", "status": "pass"},
            ])
            with mock.patch.dict(os.environ, {zas_test.SCOPE_ENV: "entities.case"}):
                zas_test.save_results(ws, "api", [
                    {"layer": "api", "id": "a", "spec_path": "entities.case.form", "status": "pass"},
                    {"layer": "api", "id": "stray", "spec_path": "entities.area.x", "status": "pass"},
                ])
            got = {r["id"]: r["status"] for r in zas_test.load_results(ws)["results"]}
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        self.assertEqual(got, {"a": "pass", "b": "pass"})


class RuntimeGuardTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")
        os.makedirs(os.path.join(self.root, "backend", "cases"))
        self.forms = os.path.join(self.root, "backend", "cases", "forms.py")
        with open(self.forms, "w") as fh:
            fh.write("from ..zas_core import mixins as _zm\nfrom ..zas_core.mixins import ZasFormMixin\n")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_writing_under_zas_core_is_refused(self):
        why = runtime_tamper(self.root, "backend/zas_core/mixins.py", {"content": "x = 1"})
        self.assertIn("report_platform_issue", why)

    def test_patching_an_imported_runtime_name_is_refused(self):
        edit = {"old_string": "x", "new_string": "        _zm._FormRecord = _CaseFormRecord\n"}
        self.assertTrue(runtime_tamper(self.root, self.forms, edit))
        edit = {"old_string": "x", "new_string": "ZasFormMixin.clean = lambda self: None\n"}
        self.assertTrue(runtime_tamper(self.root, self.forms, edit))

    def test_ordinary_app_code_passes(self):
        edit = {"old_string": "x", "new_string": "class CaseForm(ZasFormMixin):\n    zas_entity = 'case'\n"}
        self.assertEqual(runtime_tamper(self.root, self.forms, edit), "")
        self.assertEqual(runtime_tamper(self.root, self.forms, {"new_string": "rec = _zm.load(x)\n"}), "")

    def test_the_hook_denies_it(self):
        guard = make_pre_tool_use_guard(self.root)
        res = asyncio.run(guard({"tool_name": "Write", "tool_input": {
            "file_path": "backend/zas_core/expr.py", "content": "pass"}}, "t", None))
        self.assertEqual(res["hookSpecificOutput"]["permissionDecision"], "deny")


class FakeStudio:
    def __init__(self, layers, ok=True):
        self.layers, self.ok, self.calls, self.issues = layers, ok, [], []
        self.live_creds = None

    def bring_up(self, creds, emit=None):
        self.calls.append(("bring_up", creds))
        return self.ok

    def verify(self, emit=None, only=None, bring_up_ok=True, scope=()):
        self.calls.append(("verify", dict(only), tuple(scope)))
        return self.layers

    def platform_issue_ids(self):
        return [i["check_id"] for i in self.issues]

    def add_platform_issue(self, issue):
        self.issues.append(issue)

    def digest(self, ok, layers):
        return StudioBuild.digest(self, ok, layers)


class ToolTests(unittest.TestCase):
    def failing(self, fid="create.case"):
        return {"api": LayerResult(name="api", status="fail", counts={"pass": 3, "fail": 1},
                                   failures=[{"id": fid, "title": "create case", "detail": "HTTP 400"}])}

    def test_paths_keep_spec_paths_only(self):
        self.assertEqual(_paths({"paths": ["entities.case", "/pages/my_cases", "rm -rf", "entities.case"]}),
                         ["entities.case", "pages.my_cases"])

    def test_a_slice_runs_its_layers_on_its_paths_and_briefs_the_failures(self):
        studio = FakeStudio(self.failing())
        text = verify_slice(studio, CREDS, ["entities.case"])
        self.assertEqual(studio.calls[0], ("bring_up", CREDS))
        self.assertEqual(studio.calls[1][2], ("entities.case",))
        self.assertIn("design", studio.calls[1][1])
        self.assertIn("This slice's checks found problems", text)
        self.assertIn("create.case", text)
        self.assertIn("report_platform_issue", text)

    def test_a_reported_platform_failure_leaves_the_brief(self):
        studio = FakeStudio(self.failing())
        call = ToolCall("report_platform_issue", {"check_id": "create.case", "what": "rule bug",
                                                  "where": "zas_core/expr.py:526"})
        handle_call(call, studio=studio, tenant=None, service_account=None)
        self.assertTrue(call.done.is_set())
        self.assertIn("Recorded", call.result)
        text = verify_slice(studio, CREDS, ["entities.case"])
        self.assertIn("The slice works", text)

    def test_a_fix_round_reuses_the_open_account(self):
        studio = FakeStudio({})
        studio.live_creds = {"PLATFORM_USERNAME": "held"}

        def no_second_account(*a, **k):
            raise AssertionError("opened the service account again")

        call = ToolCall("studio_verify", {"paths": ["entities.case"]})
        handle_call(call, studio=studio, tenant=None, service_account=no_second_account)
        self.assertEqual(studio.calls[0], ("bring_up", {"PLATFORM_USERNAME": "held"}))
        self.assertIn("The slice works", call.result)

    def test_a_crash_still_answers_the_agent(self):
        class Broken(FakeStudio):
            def bring_up(self, creds, emit=None):
                raise RuntimeError("boom")

        call = ToolCall("studio_verify", {"paths": ["entities.case"]})
        handle_call(call, studio=Broken({}), tenant=None,
                    service_account=lambda *a, **k: __import__("contextlib").nullcontext(CREDS))
        self.assertIn("could not run", call.result)


class RepeatTests(StudioTestBase):
    def test_signature_ignores_record_numbers(self):
        a = {"id": "x", "detail": 'Cannot query "ZC-2026-0008": Must be "Case" instance.'}
        b = {"id": "x", "detail": 'Cannot query "ZC-2026-0052": Must be "Case" instance.'}
        self.assertEqual(_signature(a), _signature(b))

    def run_rounds(self, build, api_records, rounds=2):
        fake = FakeRun(self.ws, {
            "zas_test.api": results_writer(self.ws, "api", api_records),
            "zas_test.design": results_writer(self.ws, "design", lambda a: [{"id": "design.lint", "status": "pass"}]),
            "zas_test.scenarios": results_writer(self.ws, "scenarios", lambda a: []),
        })
        digests = []
        (self.ws / ".zas" / "menu_icons.json").write_text("{}")
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub([])
        ), mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")), mock.patch.object(
            StudioBuild, "has_playwright", return_value=True
        ):
            outcome = build.finish(CREDS, resume_agent=lambda d: digests.append(d) or True, rounds=rounds)
        return outcome, digests

    def setUp(self):
        super().setUp()
        zas = self.ws / ".zas"
        zas.mkdir()
        (zas / "spec.resolved.json").write_text(json.dumps({"app": {}, "roles": {}, "modules": []}))
        (zas / "test_users.json").write_text("{}")

    def test_a_failure_a_round_did_not_move_is_not_sent_again(self):
        same = lambda a: [{"id": "row_action.case.delete_draft", "title": "Delete draft", "spec_path": "entities.case",  # noqa: E731
                           "status": "fail", "detail": 'HTTP 500: Cannot query "ZC-2026-0008"'}]
        outcome, digests = self.run_rounds(self.build(first_build=False), same, rounds=3)
        self.assertEqual(len(digests), 1)
        self.assertIn("delete_draft", digests[0])
        self.assertFalse(outcome.ok)  # still in the verdict

    def test_a_reported_platform_failure_gets_no_round(self):
        build = self.build(first_build=False)
        build.add_platform_issue({"check_id": "create.case", "what": "zas_core rule bug"})
        fails = lambda a: [{"id": "create.case", "title": "create", "spec_path": "entities.case",  # noqa: E731
                            "status": "fail", "detail": "HTTP 400"}]
        outcome, digests = self.run_rounds(build, fails)
        self.assertEqual(digests, [])
        self.assertFalse(outcome.ok)
        self.assertEqual(build.platform_issue_ids(), ["create.case"])
