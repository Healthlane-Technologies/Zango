"""The `ai` section of the Zango app spec: AI helpers that the build turns into Zango AI agents."""

import yaml

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack
from zango.apps.shared.app_templates.services.spec import yamlio
from zango.apps.shared.app_templates.services.spec.validate import validate_doc

from .tests import AppTemplatesTestBase


PACK = PACKS_DIR / "zango_app"


class AiSpecTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        import_pack(PACK, publish_now=True)
        catalogue.clear_caches()
        self.view = catalogue.get_template("zango-app")

    def doc(self):
        return yamlio.to_plain(yamlio.load(self.view.example_yaml))

    def agent(self, doc, code):
        return next(a for a in doc["ai"]["agents"] if a["code"] == code)

    def errors(self, doc):
        return [i["message"] for i in validate_doc(doc, self.view, strict=True) if i["level"] == "error"]

    def test_the_example_declares_valid_helpers(self):
        doc = self.doc()
        self.assertEqual(
            [a["code"] for a in doc["ai"]["agents"]],
            ["invoice_reader", "vendor_screening", "vendor_assistant"],
        )
        self.assertEqual(self.errors(doc), [])

    def test_shape_mistakes_are_structural(self):
        doc = self.doc()
        self.agent(doc, "vendor_screening")["review"] = "maybe"
        self.agent(doc, "invoice_reader")["triggers"].append({"event": "webhook"})
        doc["ai"]["provider"]["api_key"] = "placeholder"  # keys never go in the spec  # pragma: allowlist secret
        messages = self.errors(doc)
        self.assertTrue(any("maybe" in m for m in messages), messages)
        self.assertTrue(any("webhook" in m for m in messages), messages)
        self.assertTrue(any("api_key" in m for m in messages), messages)

    def test_references_are_checked(self):
        doc = self.doc()
        screening = self.agent(doc, "vendor_screening")
        screening["access"]["roles"].append("Auditor")
        screening["triggers"].append({"event": "button", "roles": ["Finance"]})  # no label
        screening["triggers"].append({"event": "transition", "transition": "archive"})
        screening["context"]["fields"].append("bank_account")
        doc["modules"][1]["entities"][0]["custom_requirements"] = [
            {"text": "Nightly rescreen", "uses_ai": ["vendor_rescreen"], "acceptance": ["x"]}
        ]
        messages = "\n".join(self.errors(doc))
        self.assertIn('"Auditor" is not a declared role', messages)
        self.assertIn("needs a label", messages)
        self.assertIn("'archive' is not a transition of vendor", messages)
        self.assertIn("'bank_account' is not a field of vendor", messages)
        self.assertIn('"vendor_rescreen"', messages)

    def test_outputs_must_fit_and_never_retrigger_themselves(self):
        doc = self.doc()
        screening = self.agent(doc, "vendor_screening")
        screening["output"]["fields"][0]["type"] = "boolean"  # into a choice field
        screening["triggers"].append({"event": "update", "fields": ["risk_rating"]})
        messages = "\n".join(self.errors(doc))
        self.assertIn("a boolean answer does not fit 'risk_rating'", messages)
        self.assertIn("would run itself again", messages)

    def test_task_helpers_need_a_caller_and_memory_needs_chat(self):
        doc = self.doc()
        reader = self.agent(doc, "invoice_reader")
        reader["triggers"].append({"event": "task"})
        reader["memory"] = {"window": 5}
        messages = "\n".join(self.errors(doc))
        self.assertIn("nothing calls this helper", messages)
        self.assertIn("memory is only for chat helpers", messages)

        doc["app"]["custom_requirements"] = [
            {"area": "scheduled", "text": "Re-read invoices nightly", "uses_ai": ["invoice_reader"],
             "trigger": {"event": "schedule", "cron": "0 2 * * *"}, "acceptance": ["x"]}
        ]
        reader.pop("memory")
        self.assertNotIn("nothing calls this helper", "\n".join(self.errors(doc)))

    def test_mark_ready_needs_acceptance_and_a_sample(self):
        from zango.apps.agent_mode.spec_tools import SpecWorkbench, ToolRefused

        doc = self.doc()
        assistant = self.agent(doc, "vendor_assistant")
        assistant.pop("acceptance")
        assistant.pop("preview")
        bench = SpecWorkbench(yaml.safe_dump(doc, sort_keys=False), self.view, emit=lambda e: None)
        with self.assertRaises(ToolRefused) as refused:
            bench.mark_ready("done")
        message = str(refused.exception)
        self.assertIn("/ai/agents/@vendor_assistant", message)
        self.assertIn("preview.sample", message)
