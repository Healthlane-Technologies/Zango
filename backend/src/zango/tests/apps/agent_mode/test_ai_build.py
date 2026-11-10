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
        self.assertEqual(M["ai"]["provider"], {"kind": "anthropic", "name": "app-llm", "model": "claude-sonnet-5-5",
                                               "monthly_budget_usd": 50})
        reader = agent(M, "invoice_reader")
        self.assertEqual(reader["zango_name"], "invoice-reader")
        self.assertEqual(reader["run"], "async")  # every run is a background task, form fill too
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

    def test_an_inline_helper_is_refused(self):
        raw = copy.deepcopy(EXAMPLE)
        next(x for x in raw["ai"]["agents"] if x["code"] == "invoice_reader")["run"] = "inline"
        errs = checked(raw).L.errors()
        self.assertTrue(any("ai.agents" in str(e) and "background" in str(e) for e in errs), errs)

    def test_a_requirement_fired_by_a_save_queues_the_helper_with_run_later(self):
        raw = copy.deepcopy(EXAMPLE)
        next(x for x in raw["ai"]["agents"] if x["code"] == "invoice_reader")["triggers"].append({"event": "task"})
        inv = next(e for m in raw["modules"] for e in m["entities"] if e["code"] == "invoice")
        inv.setdefault("custom_requirements", []).append(
            {"area": "backend", "title": "Read on upload", "text": "Read the invoice when it is added",
             "trigger": {"event": "create"}, "uses_ai": ["invoice_reader"], "acceptance": ["x"]})
        S = checked(raw)
        self.assertEqual(S.L.errors(), [])
        h = next(h for h in S.holes if h.get("uses_ai") and h["where"].startswith("entities.invoice"))
        self.assertEqual(h["ai_call"], "run_later")
        self.assertIn('run_later("invoice_reader"', h["text"])
        self.assertIn(f'then="{h["function"]}__after_ai"', h["text"])
        for x in S.holes:
            x["status"] = "done" if x is h else "blocked"
        with tempfile.TemporaryDirectory() as ws:
            f = Path(ws) / h["target"].split("::", 1)[0]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"def {h['function']}(request, obj):\n    run_from_code('invoice_reader', obj=obj)\n")
            self.assertIn('run_later("invoice_reader", …) not found', self.audit(ws, S.holes))
            f.write_text(f"def {h['function']}(request, obj):\n    run_later('invoice_reader', obj=obj, then='x')\n")
            self.assertNotIn("not found", self.audit(ws, S.holes))

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
        self.providers = [{"id": 7, "name": "app-llm", "default_model": "claude-sonnet-5-5", "is_validated": False}]
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
        self.assertEqual((create["provider_id"], create["model"], create["output_schema"]), (7, "claude-sonnet-5-5", "JSON"))
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
        # the shared test schema is not migrated for the AI app: make its tables
        from django.apps import apps
        from django.db import connection
        from django_tenants.utils import tenant_context

        with tenant_context(cls.tenant):
            with connection.cursor() as cur:
                cur.execute("select to_regclass('ai_appllmprovider') is not null")
                made = cur.fetchone()[0]  # by an earlier test class
            if not made:
                with connection.schema_editor() as ed:
                    for m in apps.get_app_config("ai").get_models():
                        ed.create_model(m)

    def setUp(self):
        from django_tenants.utils import tenant_context

        from zango.apps.ai.models import AppLLMAgent, AppLLMProvider
        from zango.apps.shared.platform_settings.models import PlatformAIAccount

        PlatformAIAccount.objects.all().delete()
        with tenant_context(self.tenant):
            AppLLMAgent.objects.all().delete()
            AppLLMProvider.objects.all().delete()

    def _platform(self, **kw):
        from zango.apps.shared.platform_settings.models import PlatformAIAccount

        acc = PlatformAIAccount(
            name=kw.pop("name", "company-openai"),
            provider_slug=kw.pop("provider_slug", "openai"),
            default_model="gpt-4o",
            model_list=[{"id": "gpt-4o", "name": "GPT-4o"}, {"id": "gpt-4o-mini", "name": "GPT-4o mini"}],
            is_default=True,
            is_enabled=True,
            is_validated=True,
            **kw,
        )
        acc.set_config({"api_key": "sk-platform-test"})  # pragma: allowlist secret
        acc.save()
        return acc

    def test_without_a_platform_default_the_build_makes_a_keyless_placeholder_once(self):
        from django_tenants.utils import tenant_context

        from zango.ai.exceptions import ProviderNotConnected
        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.ai.models import AppLLMProvider

        ai = checked(EXAMPLE).M["ai"]
        out = ensure_ai_account(self.tenant.name, ai)
        self.assertEqual(out, {"status": "created", "name": "app-llm", "connected": False, "via": ""})
        with tenant_context(self.tenant):
            p = AppLLMProvider.objects.get(name="app-llm")
            self.assertEqual((p.provider_slug, p.default_model, p.is_enabled, p.is_placeholder), ("anthropic", "claude-sonnet-5-5", True, True))
            self.assertEqual(p._decrypt_config(), {})
            self.assertFalse(p.is_connected)
            self.assertTrue(p.enabled_models.filter(model_id="claude-sonnet-5-5").exists())
            with self.assertRaises(ProviderNotConnected):
                p.get_client()
        self.assertEqual(ensure_ai_account(self.tenant.name, ai)["status"], "exists")
        self.assertEqual(ensure_ai_account(self.tenant.name, {"agents": []})["status"], "none")

    def test_with_a_platform_default_the_build_links_to_it(self):
        from django_tenants.utils import tenant_context

        from zango.ai.exceptions import ProviderNotConnected
        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.ai.models import AppLLMProvider

        acc = self._platform(app_monthly_budget_usd=25)
        out = ensure_ai_account(self.tenant.name, checked(EXAMPLE).M["ai"])
        self.assertEqual(out, {"status": "created", "name": "app-llm", "connected": True, "via": "company-openai"})
        with tenant_context(self.tenant):
            p = AppLLMProvider.objects.get(name="app-llm")
            # the spec asks for a Claude model the account doesn't offer: its default wins
            self.assertEqual((p.source, p.provider_slug, p.default_model, p.is_placeholder), ("platform", "openai", "gpt-4o", False))
            self.assertEqual(p.platform_account_uuid, acc.uuid)
            self.assertEqual(p._decrypt_config(), {"api_key": "sk-platform-test"})  # pragma: allowlist secret
            self.assertEqual(sorted(p.enabled_models.values_list("model_id", flat=True)), ["gpt-4o", "gpt-4o-mini"])
            self.assertEqual(p.monthly_budget_usd, 25)
            self.assertTrue(p.is_connected)
            self.assertEqual(p.get_provider_class().slug, "openai")

            acc.is_enabled = False
            acc.save()
            p.refresh_from_db()
            self.assertFalse(p.is_connected)
            self.assertIn("switched off", p.connection_problem())
            with self.assertRaises(ProviderNotConnected):
                p.get_client()

    def test_a_placeholder_is_linked_once_a_platform_default_exists_and_agents_follow(self):
        from django_tenants.utils import tenant_context

        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.ai.models import AppLLMAgent, AppLLMProvider

        ai = checked(EXAMPLE).M["ai"]
        ensure_ai_account(self.tenant.name, ai)
        with tenant_context(self.tenant):
            p = AppLLMProvider.objects.get(name="app-llm")
            AppLLMAgent.objects.create(name="vendor-screening", provider=p, model="claude-sonnet-5-5")
        self._platform()
        out = ensure_ai_account(self.tenant.name, ai)
        self.assertEqual((out["status"], out["connected"], out["via"]), ("linked", True, "company-openai"))
        with tenant_context(self.tenant):
            self.assertEqual(AppLLMAgent.objects.get(name="vendor-screening").model, "gpt-4o")
        self.assertEqual(ensure_ai_account(self.tenant.name, ai)["status"], "exists")

    def test_connect_own_key_replaces_the_link(self):
        from django_tenants.utils import tenant_context

        from zango.ai.accounts import connect_own
        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.ai.models import AppLLMProvider

        self._platform()
        ensure_ai_account(self.tenant.name, checked(EXAMPLE).M["ai"])
        with tenant_context(self.tenant):
            p = AppLLMProvider.objects.get(name="app-llm")
            out = connect_own(p, "anthropic", {"api_key": "sk-ant-own"}, "claude-sonnet-5-5", [{"id": "claude-sonnet-5-5", "name": "Sonnet"}])  # pragma: allowlist secret
            p.refresh_from_db()
            self.assertEqual(out["default_model"], "claude-sonnet-5-5")
            self.assertEqual((p.source, p.platform_account_uuid, p.provider_slug), ("own", None, "anthropic"))
            self.assertEqual(p._decrypt_config(), {"api_key": "sk-ant-own"})  # pragma: allowlist secret
            self.assertTrue(p.is_connected)

    def test_apps_linked_to_lists_the_app(self):
        from zango.ai.accounts import apps_linked_to
        from zango.apps.agent_mode.ai_account import ensure_ai_account

        acc = self._platform()
        ensure_ai_account(self.tenant.name, checked(EXAMPLE).M["ai"])
        self.assertEqual([a["name"] for a in apps_linked_to(acc.uuid)], [self.tenant.name])


class SubscriptionTests(AiAccountTests):
    """AGENT_MODE_AUTH=subscription: the local Claude login, like Build with AI (DEBUG only)."""

    SUB = {"DEBUG": True, "AGENT_MODE_AUTH": "subscription", "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-test"}  # pragma: allowlist secret

    def test_hidden_and_not_connected_when_the_switch_is_off(self):
        from django.test import override_settings

        from zango.ai.providers.registry import get_available_providers

        with override_settings(DEBUG=True, AGENT_MODE_AUTH="api_key"):
            self.assertNotIn("claude_subscription", [p["slug"] for p in get_available_providers()])
        with override_settings(**self.SUB):
            self.assertIn("claude_subscription", [p["slug"] for p in get_available_providers()])
        with override_settings(**{**self.SUB, "DEBUG": False}):
            self.assertNotIn("claude_subscription", [p["slug"] for p in get_available_providers()])

    def test_the_build_uses_the_subscription_before_the_platform_default(self):
        from django.test import override_settings
        from django_tenants.utils import tenant_context

        from zango.ai.exceptions import ProviderNotConnected
        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.ai.models import AppLLMProvider

        self._platform()
        ai = checked(EXAMPLE).M["ai"]
        with override_settings(**self.SUB):
            out = ensure_ai_account(self.tenant.name, ai)
            self.assertEqual((out["status"], out["connected"]), ("created", True))
            with tenant_context(self.tenant):
                p = AppLLMProvider.objects.get(name="app-llm")
                self.assertEqual((p.provider_slug, p.source, p.default_model), ("claude_subscription", "own", "claude-sonnet-5-5"))
                self.assertTrue(p.is_connected)
            self.assertEqual(ensure_ai_account(self.tenant.name, ai)["status"], "exists")
        # switch off: the account says why and refuses to call
        with override_settings(DEBUG=True, AGENT_MODE_AUTH="api_key"), tenant_context(self.tenant):
            p = AppLLMProvider.objects.get(name="app-llm")
            self.assertFalse(p.is_connected)
            self.assertIn("switched off", p.connection_problem())
            with self.assertRaises(ProviderNotConnected):
                p.get_client()

    def test_complete_asks_for_the_schema_and_unfences_the_answer(self):
        from unittest import mock

        from django.test import override_settings

        from zango.ai.providers.base import LLMMessage
        from zango.ai.providers.claude_subscription import ClaudeSubscriptionProvider

        seen = {}

        def fake_run(self, prompt, model, system, timeout, tools=None, attachments=None):
            seen.update(prompt=prompt, model=model, system=system)
            return '```json\n{"risk": "high"}\n```', {"input_tokens": 12, "output_tokens": 5}, []

        with override_settings(**self.SUB), mock.patch.object(ClaudeSubscriptionProvider, "_run", fake_run):
            prov = ClaudeSubscriptionProvider({})
            r = prov.complete([LLMMessage(role="user", content="Vendor: Acme")], "claude-sonnet-5-5",
                              system="Rate the risk.", response_format={"type": "object"})
        self.assertEqual(r.content, '{"risk": "high"}')
        self.assertEqual((r.usage.input_tokens, r.usage.output_tokens), (12, 5))
        self.assertEqual(prov.compute_cost(r.usage, "claude-sonnet-5-5"), 0.0)
        self.assertIn('{"type": "object"}', seen["system"])
        self.assertEqual(seen["prompt"], "Vendor: Acme")

    # -- tools: the CLI is shown them but Zango runs them (see the provider docstring) --

    def _tools(self):
        from zango.ai.providers.base import LLMToolDef

        schema = {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}
        return [LLMToolDef("zas_search_records", "Search records.", schema), LLMToolDef("other", "Other.", schema)]

    def _fake_query(self, blocks, seen, raises=True):
        """A stand-in for the SDK's `query`: one AssistantMessage per block, then the turn limit."""
        from claude_agent_sdk import AssistantMessage, ResultError, ResultMessage, TextBlock, ToolUseBlock

        async def query(prompt, options):
            seen["options"] = options
            seen["prompt"] = prompt
            for b in blocks:
                content = [TextBlock(b)] if isinstance(b, str) else [ToolUseBlock(*b)]
                yield AssistantMessage(content=content, model="m")
            yield ResultMessage(subtype="error_max_turns" if raises else "success", duration_ms=1, duration_api_ms=1,
                                is_error=raises, num_turns=2, session_id="s", usage={"input_tokens": 7, "output_tokens": 3})
            if raises:
                raise ResultError("Reached maximum number of turns (1)", data={"subtype": "error_max_turns"})

        return query

    def _complete(self, blocks, tools, seen, **kw):
        from unittest import mock

        from django.test import override_settings

        from zango.ai.providers.base import LLMMessage
        from zango.ai.providers.claude_subscription import ClaudeSubscriptionProvider

        with override_settings(**self.SUB), mock.patch("claude_agent_sdk.query", self._fake_query(blocks, seen, **kw)):
            return ClaudeSubscriptionProvider({}).complete(
                [LLMMessage(role="user", content="Find Acme")], "claude-sonnet-5-5", tools=tools, system="Help.")

    def test_a_tool_turn_comes_back_as_tool_use_with_every_call(self):
        seen = {}
        r = self._complete(
            ["Looking.", ("tu_1", "mcp__zango__zas_search_records", {"q": "Acme"}), ("tu_2", "mcp__zango__other", {"q": "x"})],
            self._tools(), seen)
        self.assertEqual(r.stop_reason, "tool_use")
        self.assertEqual([(c.id, c.name, c.input) for c in r.tool_calls],
                         [("tu_1", "zas_search_records", {"q": "Acme"}), ("tu_2", "other", {"q": "x"})])
        self.assertEqual(r.content, "Looking.")
        self.assertEqual((r.usage.input_tokens, r.usage.output_tokens), (7, 3))

    def test_the_cli_is_offered_only_the_agents_tools_and_runs_none(self):
        seen = {}
        self._complete([("tu_1", "mcp__zango__other", {"q": "x"})], self._tools(), seen)
        o = seen["options"]
        self.assertEqual(o.tools, [])  # no files, shell or web
        self.assertEqual(o.max_turns, 1)
        self.assertIsNone(o.can_use_tool)
        self.assertEqual(sorted(o.allowed_tools), ["mcp__zango__other", "mcp__zango__zas_search_records"])
        self.assertEqual(list(o.mcp_servers), ["zango"])

    def test_an_agent_without_tools_is_one_plain_turn(self):
        seen = {}
        r = self._complete(["Hello."], None, seen, raises=False)
        self.assertEqual((r.stop_reason, r.content, r.tool_calls), ("end_turn", "Hello.", []))
        self.assertFalse(seen["options"].mcp_servers)
        self.assertFalse(seen["options"].allowed_tools)

    def test_a_cli_failure_without_tool_calls_is_still_an_error(self):
        from zango.ai.exceptions import LLMAPIError

        with self.assertRaises(LLMAPIError):
            self._complete([], self._tools(), {})

    def test_the_next_prompt_shows_the_earlier_call_and_its_result(self):
        from zango.ai.providers.base import LLMMessage
        from zango.ai.providers.claude_subscription import _prompt

        prompt = _prompt([
            LLMMessage(role="user", content="Find Acme"),
            LLMMessage(role="assistant", content=[
                {"type": "text", "text": "Looking."},
                {"type": "tool_use", "id": "tu_1", "name": "zas_search_records", "input": {"q": "Acme"}}]),
            LLMMessage(role="user", content=[
                {"type": "tool_result", "tool_use_id": "tu_1", "content": '{"count": 1}', "is_error": False}]),
        ])
        self.assertIn('called tool zas_search_records with {"q": "Acme"}', prompt)
        self.assertIn('result of tool zas_search_records]\n{"count": 1}', prompt)

    def test_a_pdf_goes_to_the_cli_as_a_block_beside_the_prompt(self):
        from unittest import mock

        from zango.ai.providers.base import LLMFile, LLMMessage
        from zango.ai.providers.claude_subscription import ClaudeSubscriptionProvider

        doc = LLMFile.from_bytes(b"%PDF-1.4 resume", media_type="application/pdf").to_anthropic_block()
        seen = {}

        def fake_run(self, prompt, model, system, timeout, tools=None, attachments=None):
            seen.update(prompt=prompt, attachments=attachments)
            return "Dev Malhotra", {}, []

        msg = LLMMessage(role="user", content=[doc, {"type": "text", "text": "Who is this?"}])
        with mock.patch.object(ClaudeSubscriptionProvider, "_run", fake_run):
            ClaudeSubscriptionProvider({}).complete([msg], "claude-sonnet-5-5")
        self.assertEqual(seen["attachments"], [doc])
        self.assertEqual(seen["prompt"], "Who is this?")  # no base64 in the text

    def test_a_file_it_cannot_send_is_named_in_the_prompt(self):
        from zango.ai.providers.base import LLMMessage
        from zango.ai.providers.claude_subscription import _attachments, _prompt

        msg = LLMMessage(role="user", content=[
            {"type": "document", "source": {"type": "file", "file_id": "f_1"}}, {"type": "text", "text": "Read it"}])
        self.assertEqual(_attachments([msg]), [])
        self.assertIn("[attached document not sent in local testing]", _prompt([msg]))

    def test_agent_client_runs_the_tool_through_the_executor_then_answers(self):
        from unittest import mock

        from zango.ai.agent_client import AgentClient
        from zango.ai.providers.claude_subscription import ClaudeSubscriptionProvider
        from zango.tests.apps.ai.test_agent_client import _EXEC, _PC, _TOOL_CALL_MODEL, _TOOL_MODEL
        from zango.tests.apps.ai.test_agent_client import _make_agent, _make_tool_result

        prompts = []

        def fake_run(self, prompt, model, system, timeout, tools=None, attachments=None):
            prompts.append((prompt, [t.name for t in tools or []]))
            if len(prompts) == 1:
                return "", {}, [("tu_1", "zas_search_records", {"q": "Acme"})]
            return "Found it.", {}, []

        provider = ClaudeSubscriptionProvider({})

        def complete(**kw):
            return provider.complete(kw["messages"], kw["model"], tools=kw.get("tools"), system=kw.get("system"))

        agent = _make_agent(tools=["zas_search_records"], provider_slug="claude_subscription")
        with mock.patch.object(ClaudeSubscriptionProvider, "_run", fake_run), mock.patch(_PC) as pc_cls, \
                mock.patch(_EXEC) as exec_cls, mock.patch(_TOOL_MODEL), mock.patch(_TOOL_CALL_MODEL):
            pc_cls.return_value.complete.side_effect = complete
            pc_cls.return_value._get_client.return_value = mock.MagicMock()
            exec_cls.return_value.execute.return_value = _make_tool_result(output={"count": 1})
            out = AgentClient(agent).run(input="Find Acme")
        self.assertEqual(out.content, "Found it.")
        exec_cls.return_value.execute.assert_called_once_with("zas_search_records", {"q": "Acme"})
        self.assertEqual(len(prompts), 2)
        self.assertIn("result of tool zas_search_records", prompts[1][0])
        self.assertIn('{"count": 1}', prompts[1][0])



class PlatformAiAccountApiTests(AiAccountTests):
    """/api/v1/platform/ai-accounts/: super admins only; keys checked live and never returned."""

    def _call(self, view, method, path, data=None, superadmin=True, **kw):
        import json

        from rest_framework.test import APIRequestFactory, force_authenticate

        from zango.apps.shared.platformauth.models import PlatformUserModel
        from zango.cli.start_project import create_platform_user

        email = "ai_admin@example.com" if superadmin else "ai_member@example.com"
        pu = PlatformUserModel.objects.filter(email=email).first()
        if pu is None:
            create_platform_user(email, "Testpassword@123")  # pragma: allowlist secret
            pu = PlatformUserModel.objects.get(email=email)
        pu.is_superadmin = superadmin
        pu.save()
        f = APIRequestFactory()
        req = getattr(f, method)(path, data or {}, format="json", HTTP_HOST="test.testserver.com")
        force_authenticate(req, user=pu.user)
        resp = view.as_view()(req, **kw)
        if hasattr(resp, "render"):
            resp.render()
        return resp.status_code, json.loads(resp.content)

    def test_create_checks_the_key_and_never_returns_it(self):
        from unittest import mock

        from zango.api.platform.ai_accounts.v1 import views as V
        from zango.apps.shared.platform_settings.models import PlatformAIAccount

        models = [{"id": "claude-sonnet-5-5", "name": "Sonnet"}, {"id": "claude-haiku-4-5", "name": "Haiku"}]
        body = {"name": "company-claude", "provider_slug": "anthropic", "config": {"api_key": "sk-ant-api03-abcdefghijklmnop"},  # pragma: allowlist secret
                "default_model": "claude-sonnet-5-5", "model_ids": ["claude-sonnet-5-5"]}
        with mock.patch.object(V, "check_credentials", return_value=(False, "Invalid API key.", [])):
            status, out = self._call(V.PlatformAIAccountsView, "post", "/x/", body)
        self.assertEqual((status, out["response"]["message"]), (400, "Invalid API key."))
        self.assertFalse(PlatformAIAccount.objects.exists())

        with mock.patch.object(V, "check_credentials", return_value=(True, "", models)):
            status, out = self._call(V.PlatformAIAccountsView, "post", "/x/", body)
        self.assertEqual(status, 201, out)
        acc = out["response"]["account"]
        self.assertTrue(acc["is_default"])  # the first account becomes the default
        self.assertEqual(acc["status"], "connected")
        self.assertEqual([m["id"] for m in acc["models"]], ["claude-sonnet-5-5"])
        self.assertNotIn("abcdefghijklmnop", json_dump(out))
        self.assertEqual(PlatformAIAccount.objects.get().get_config()["api_key"], "sk-ant-api03-abcdefghijklmnop")  # pragma: allowlist secret

        status, out = self._call(V.PlatformAIAccountsView, "get", "/x/")
        self.assertEqual(status, 200)
        self.assertNotIn("abcdefghijklmnop", json_dump(out))
        self.assertIn("anthropic", [s["slug"] for s in out["response"]["services"]])

    def test_members_who_are_not_super_admins_are_refused(self):
        from zango.api.platform.ai_accounts.v1 import views as V

        status, _ = self._call(V.PlatformAIAccountsView, "get", "/x/", superadmin=False)
        self.assertEqual(status, 403)

    def test_an_account_apps_use_cannot_be_deleted_and_only_one_is_default(self):
        from zango.api.platform.ai_accounts.v1 import views as V
        from zango.apps.agent_mode.ai_account import ensure_ai_account
        from zango.apps.shared.platform_settings.models import PlatformAIAccount

        first = self._platform()
        ensure_ai_account(self.tenant.name, checked(EXAMPLE).M["ai"])
        status, out = self._call(V.PlatformAIAccountDetailView, "delete", "/x/", account_uuid=first.uuid)
        self.assertEqual((status, out["response"]["error_code"]), (409, "ACCOUNT_IN_USE"))
        self.assertEqual(out["response"]["apps"][0]["name"], self.tenant.name)

        second = self._platform(name="company-azure", provider_slug="azure_openai")
        first.refresh_from_db()
        self.assertEqual(list(PlatformAIAccount.objects.filter(is_default=True)), [second])
        status, out = self._call(V.PlatformAIAccountDetailView, "put", "/x/", {"is_default": True}, account_uuid=first.uuid)
        self.assertEqual(status, 200, out)
        self.assertEqual(list(PlatformAIAccount.objects.filter(is_default=True).values_list("name", flat=True)), ["company-openai"])


def json_dump(x):
    import json

    return json.dumps(x)
