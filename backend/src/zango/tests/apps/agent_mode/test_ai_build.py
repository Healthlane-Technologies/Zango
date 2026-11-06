"""AI helpers in the build (AI agents plan, P2): the checker resolves `ai` and makes prompt / tool holes,
the audit checks prompts and uses_ai calls, the platform's AI step is idempotent, and the build creates
the app's AI account as a keyless placeholder."""

import copy
import json
import sys
import tempfile
import unittest

from pathlib import Path

import yaml

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir
from zango.test.cases import ZangoAppBaseTestCase


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
if str(SKILL / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL / "scripts"))

import spec_check  # noqa: E402
import zango_platform  # noqa: E402

EXAMPLE = yaml.safe_load((PACKS_DIR / "zango_app" / "example.yaml").read_text())


def checked(raw):
    S = spec_check.Spec(copy.deepcopy(raw), "x.yaml")
    S.build()
    S.lint()
    S.prototype_screens()
    S.page_holes()
    S.derive()
    S.resolve_ai()
    S.ai_holes()
    S.number_holes({})
    return S


def agent(M, code):
    return next(a for a in M["ai"]["agents"] if a["code"] == code)


class CheckerTests(unittest.TestCase):
    def test_ai_resolves_for_the_runtime_and_the_platform(self):
        S = checked(EXAMPLE)
        self.assertEqual(S.L.errors(), [])
        M = S.M
        self.assertEqual(M["ai"]["provider"], {"kind": "anthropic", "name": "app-llm", "model": "claude-sonnet-4-5",
                                               "monthly_budget_usd": 50})
        reader = agent(M, "invoice_reader")
        self.assertEqual(reader["zango_name"], "invoice-reader")
        self.assertEqual(reader["run"], "inline")
        self.assertEqual(reader["roles"], ["Vendor User"])  # who can add invoices
        self.assertEqual(reader["output"]["format"], "JSON")
        self.assertEqual(reader["output"]["json_schema"]["required"], ["invoice_no", "invoice_date", "amount"])
        self.assertEqual(reader["prompts"]["user"]["file"], "backend/procurement/ai/invoice_reader.user.md")
        screening = agent(M, "vendor_screening")
        self.assertEqual(screening["output"]["json_schema"]["properties"]["risk_rating"]["enum"], ["low", "medium", "high", None])
        self.assertEqual({t["where"] for t in screening["triggers"] if t["event"] == "button"}, {"record", "row"})
        chat = agent(M, "vendor_assistant")
        self.assertNotIn("user", chat["prompts"])  # a chat's question is the user message
        self.assertEqual(chat["prompts"]["system"]["variables"], ["today", "role", "record", "related"])
        self.assertEqual(chat["tools"], ["zas_search_records"])
        self.assertEqual(chat["tool_entities"], ["invoice"])
        self.assertEqual(chat["memory"], 10)
        self.assertEqual([r["via"] for r in chat["context"]["related"]], ["vendor", "vendor"])
        summary = agent(M, "spend_summary")
        self.assertEqual(summary["prompts"]["user"]["variables"], ["records"])
        self.assertIn("Finance", summary["roles"])  # named on the trigger

    def test_holes_for_prompts_tools_and_uses_ai(self):
        raw = copy.deepcopy(EXAMPLE)
        a = next(x for x in raw["ai"]["agents"] if x["code"] == "vendor_screening")
        a["tools"] = [{"code": "gst_lookup", "text": "Look up a GSTIN on the GST portal", "safety": "external"}]
        a["triggers"].append({"event": "task"})
        raw["app"]["custom_requirements"] = [{"area": "scheduled", "title": "Nightly rescreen", "text": "Rescreen approved vendors",
                                              "uses_ai": ["vendor_screening"], "acceptance": ["x"]}]
        S = checked(raw)
        self.assertEqual(S.L.errors(), [])
        kinds = [h["kind"] for h in S.holes]
        self.assertEqual(kinds.count("ai_prompt"), 4)
        tool = next(h for h in S.holes if h["kind"] == "ai_tool")
        self.assertEqual(tool["target"], "backend/vendors/tools.py::gst_lookup")
        self.assertIn("ToolSafety.EXTERNAL", tool["signature"])
        req = next(h for h in S.holes if h["where"] == "app.custom_requirements[0]")
        self.assertEqual(req["uses_ai"], ["vendor_screening"])
        self.assertIn('run_from_code("vendor_screening"', req["text"])
        self.assertIn("{{input}}", next(h for h in S.holes if h["where"] == "ai.agents.vendor_screening")["text"])

    def test_audit_checks_prompt_files_variables_and_calls(self):
        raw = copy.deepcopy(EXAMPLE)
        raw["app"]["custom_requirements"] = [{"area": "scheduled", "title": "Re-read", "text": "Re-read invoices",
                                              "uses_ai": ["invoice_reader"], "acceptance": ["x"]}]
        next(x for x in raw["ai"]["agents"] if x["code"] == "invoice_reader")["triggers"].append({"event": "task"})
        S = checked(raw)
        for h in S.holes:
            h["status"] = "done" if h["kind"] in ("ai_prompt", "requirement") else "blocked"
        with tempfile.TemporaryDirectory() as ws:
            def write(rel, text):
                p = Path(ws) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            prompts = {h["function"]: h for h in S.holes if h["kind"] == "ai_prompt"}
            for code, h in prompts.items():
                for p in h["prompts"]:
                    body = " ".join("{{" + v + "}}" for v in p["variables"]) or "Be brief."
                    write(p["file"], (f"<!-- zas:hole {h['id']} -->\n" if p["file"].endswith(".system.md") else "") + body)
            write("backend/procurement/tasks.py", "def app__req__1():\n    pass\n")
            out = self.audit(ws, S.holes)
            self.assertIn('run_from_code("invoice_reader", …) not found', out)
            write("backend/procurement/tasks.py", "def app__req__1():\n    run_from_code('invoice_reader', obj=None)\n")
            write("backend/procurement/ai/spend_summary.user.md", "Summarise {{records}} for {{vendor}}")
            out = self.audit(ws, S.holes)
            self.assertNotIn("not found", out)
            self.assertIn("uses vendor; it may use records", out)
            write("backend/procurement/ai/spend_summary.user.md", "Summarise the purchase orders.")
            self.assertIn("never uses {{records}}", self.audit(ws, S.holes))

    def audit(self, ws, holes):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            spec_check.audit_holes(ws, holes)
        return buf.getvalue()


class FakePlatform:
    """The App Panel AI API as zango_platform.cmd_ai uses it, in memory."""

    def __init__(self, ws, uuid="u"):
        self.ws, self.uuid, self.calls = ws, uuid, []
        self.providers = [{"id": 7, "name": "app-llm", "default_model": "claude-sonnet-4-5", "is_validated": False}]
        self.prompts, self.agents, self.tools = {}, {}, ["zas_search_records", "zas_read_record"]

    def get(self, path, **params):
        if path.endswith("/providers/"):
            return {"providers": {"records": self.providers}}
        if path.endswith("/tools/"):
            return {"tools": {"records": [{"name": n} for n in self.tools]}}
        if path.endswith("/prompts/"):
            return {"prompts": {"records": list(self.prompts.values())}}
        if path.endswith("/agents/"):
            return {"agents": {"records": list(self.agents.values())}}
        raise AssertionError(path)

    def send_json(self, method, path, body=None):
        self.calls.append((method, path.split("/ai", 1)[1], body))
        tail = path.split("/ai", 1)[1]
        if tail == "/tools/sync/":
            return {"stats": {"created": 0, "updated": 0, "deactivated": 0}}
        if tail == "/prompts/" and method == "POST":
            pid = len(self.prompts) + 1
            self.prompts[body["name"]] = {"id": pid, "name": body["name"], "active_version": {"content": body["content"]}}
            return {"prompt_id": pid}
        if tail == "/agents/" and method == "POST":
            aid = len(self.agents) + 1
            self.agents[body["name"]] = {"id": aid, "name": body["name"], **body}
            return {"agent_id": aid}
        if tail.endswith("/versions/"):
            return {"version": {"id": 99}}
        return {}


class PlatformStepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)
        (self.ws / ".zas").mkdir()
        self.M = json.loads(json.dumps(checked(EXAMPLE).M, default=str))
        for a in self.M["ai"]["agents"]:
            for p in a["prompts"].values():
                f = self.ws / p["file"]
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("<!-- zas:hole H-01 -->\nYou help with " + a["name"] + ". " + " ".join("{{" + v + "}}" for v in p["variables"]))

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_run_creates_then_a_rerun_changes_nothing(self):
        P, log = FakePlatform(str(self.ws)), []
        zango_platform.cmd_ai(P, self.M, log.append)
        made = [c for c in P.calls if c[0] in ("POST", "PUT") and c[1] != "/tools/sync/"]
        self.assertEqual(sum(1 for c in made if c[1] == "/prompts/"), 7)  # 4 system + 3 user (the chat has none)
        create = next(c[2] for c in made if c[1] == "/agents/" and c[2]["name"] == "vendor-screening")
        self.assertEqual((create["provider_id"], create["model"], create["output_schema"]), (7, "claude-sonnet-4-5", "JSON"))
        self.assertNotIn("<!--", P.prompts["vendor-screening-system"]["active_version"]["content"])
        state = json.loads((self.ws / ".zas" / "ai_state.json").read_text())
        self.assertEqual(sorted(state["agents"]), ["invoice_reader", "spend_summary", "vendor_assistant", "vendor_screening"])

        P.calls.clear()
        zango_platform.cmd_ai(P, self.M, log.append)
        self.assertEqual([c for c in P.calls if c[1] != "/tools/sync/"], [])

    def test_a_changed_prompt_gets_a_live_version_and_user_settings_stay(self):
        P = FakePlatform(str(self.ws))
        zango_platform.cmd_ai(P, self.M, lambda m: None)
        P.agents["vendor-screening"]["model"] = "claude-opus-4-1"  # the user's change in the console
        (self.ws / "backend/vendors/ai/vendor_screening.system.md").write_text("Be stricter. {{today}}")
        agent(self.M, "vendor_screening")["tools"] = ["zas_read_record"]
        P.calls.clear()
        zango_platform.cmd_ai(P, self.M, lambda m: None)
        paths = [(c[0], c[1]) for c in P.calls if c[1] != "/tools/sync/"]
        self.assertIn(("POST", "/prompts/1/versions/"), [(m, p.replace(str(P.prompts["vendor-screening-system"]["id"]), "1", 1)) for m, p in paths])
        put = next(c[2] for c in P.calls if c[0] == "PUT")
        self.assertEqual(put["tools"], ["zas_read_record"])
        self.assertNotIn("model", put)
        self.assertNotIn("provider_id", put)

    def test_missing_prompts_and_tools_stop_the_step(self):
        (self.ws / "backend/vendors/ai/vendor_screening.user.md").write_text("<!-- zas:hole H-01 -->\n")
        with self.assertRaisesRegex(zango_platform.PlatformError, "vendor_screening.user.md"):
            zango_platform.cmd_ai(FakePlatform(str(self.ws)), self.M, lambda m: None)
        (self.ws / "backend/vendors/ai/vendor_screening.user.md").write_text("{{record}}")
        P = FakePlatform(str(self.ws))
        P.tools = []
        with self.assertRaisesRegex(zango_platform.PlatformError, "zas_search_records"):
            zango_platform.cmd_ai(P, self.M, lambda m: None)


class AiAccountTests(ZangoAppBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the shared test schema is not migrated for the AI app: make the two tables the step writes
        from django.db import connection
        from django_tenants.utils import tenant_context

        from zango.apps.ai.models import AppLLMProvider
        from zango.apps.ai.models.provider import AppLLMProviderModel

        with tenant_context(cls.tenant):
            have = connection.introspection.table_names()
            with connection.schema_editor() as ed:
                for m in (AppLLMProvider, AppLLMProviderModel):
                    if m._meta.db_table not in have:
                        ed.create_model(m)

    def test_the_build_creates_a_keyless_placeholder_once(self):
        from django_tenants.utils import tenant_context

        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.ai.models import AppLLMProvider

        ai = checked(EXAMPLE).M["ai"]
        out = ensure_ai_account(self.tenant.name, ai)
        self.assertEqual(out, {"status": "created", "name": "app-llm", "connected": False})
        with tenant_context(self.tenant):
            p = AppLLMProvider.objects.get(name="app-llm")
            self.assertEqual((p.provider_slug, p.default_model, p.is_enabled, p.is_validated), ("anthropic", "claude-sonnet-4-5", True, False))
            self.assertEqual(p._decrypt_config(), {})
            self.assertTrue(p.enabled_models.filter(model_id="claude-sonnet-4-5").exists())
        self.assertEqual(ensure_ai_account(self.tenant.name, ai)["status"], "exists")
        self.assertEqual(ensure_ai_account(self.tenant.name, {"agents": []})["status"], "none")
