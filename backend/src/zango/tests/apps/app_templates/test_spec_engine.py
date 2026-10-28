import copy
import json
import unittest

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services.spec import (
    document,
    rules,
    validate,
    yamlio,
)


PSP = PACKS_DIR / "psp"


class _View:
    """Just enough of a TemplateView for the validator."""

    is_yaml = True

    def __init__(self):
        self.json_schema = json.loads((PSP / "schema.json").read_text())
        self.rules = json.loads((PSP / "rules.json").read_text())
        self.ui_schema = json.loads((PSP / "ui.json").read_text())


def example():
    return yamlio.load((PSP / "example.yaml").read_text())


class DocumentTests(unittest.TestCase):
    def test_pointer_escaping_round_trips(self):
        self.assertEqual(document.to_pointer(["a/b", "c~d", 0]), "/a~1b/c~0d/0")
        self.assertEqual(document.parse("/a~1b/c~0d/0"), ["a/b", "c~d", "0"])
        self.assertEqual(document.parse(""), [])

    def test_selectors_find_items_by_code_and_by_single_key(self):
        doc = example()
        self.assertEqual(document.resolve(doc, "/masters/@city"), ["masters", 0])
        state = document.get(doc, "/masters/@city/fields/@state")
        self.assertIsInstance(state, dict)
        self.assertEqual(
            document.resolve(doc, "/masters/@city/fields/@state"),
            ["masters", 0, "fields", 0],
        )
        with self.assertRaises(document.PathError):
            document.get(doc, "/masters/@nowhere")

    def test_edits_return_new_documents_and_changed_paths(self):
        doc = example()
        before = copy.deepcopy(doc)
        new, changed = document.set_at(doc, "/roles/Manager/sees_only", "own")
        self.assertEqual(doc, before, "the input must not be mutated")
        self.assertEqual(new["roles"]["Manager"]["sees_only"], "own")
        self.assertEqual(changed, ["/roles/Manager/sees_only"])

        new, changed = document.add_at(
            new, "/masters", {"code": "clinic", "name": "Clinic"}, index=0
        )
        self.assertEqual(new["masters"][0]["code"], "clinic")
        self.assertEqual(changed, ["/masters/0"])
        self.assertEqual(document.resolve(new, "/masters/@city"), ["masters", 1])

        new, changed = document.remove_at(new, "/masters/@clinic")
        self.assertEqual(changed, ["/masters/0"])
        self.assertEqual(new["masters"], before["masters"])

        new, changed = document.add_at(new, "/roles/Auditor", {})
        self.assertIn("Auditor", new["roles"])
        with self.assertRaises(document.PathError):
            document.add_at(new, "/roles/Auditor", {})

    def test_diff_reports_the_deepest_changes(self):
        doc = example()
        new, _ = document.set_at(doc, "/roles/Distributor/scope_field", "hospital")
        new, _ = document.add_at(new, "/roles/Auditor", {})
        self.assertEqual(
            sorted(document.diff(doc, new)),
            ["/roles/Auditor", "/roles/Distributor/scope_field"],
        )
        self.assertEqual(document.diff(doc, doc), [])

    def test_section_for_prefers_the_most_specific_section(self):
        sections = _View().ui_schema["sections"]
        self.assertEqual(document.section_for("/roles/Manager", sections), "roles")
        self.assertEqual(
            document.section_for("/patient/states/0", sections), "patient_lifecycle"
        )
        self.assertEqual(
            document.section_for("/patient/attributes/1", sections), "patient"
        )
        self.assertEqual(
            document.section_for("/programs/0/orders/1/code", sections), "orders"
        )
        self.assertEqual(
            document.section_for("/programs/0/schemes/0", sections), "schemes"
        )
        self.assertEqual(document.section_for("/programs/0/code", sections), "programs")
        self.assertEqual(document.section_for("/journey", sections), "program")


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.rules = _View().rules

    def test_the_example_breaks_no_rule(self):
        self.assertEqual(rules.evaluate(example(), self.rules), [])

    def test_an_undeclared_role_on_a_step_is_caught(self):
        doc = example()
        doc["patient"]["steps"][0]["by"] = ["Executive", "Ghost"]
        issues = rules.evaluate(doc, self.rules)
        hit = [i for i in issues if i["rule"] == "step_role_known"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["path"], "/patient/steps/0/by")
        self.assertIn("Ghost", hit[0]["message"])

    def test_duplicate_master_codes_are_caught(self):
        doc = example()
        doc["masters"].append(copy.deepcopy(doc["masters"][0]))
        self.assertTrue(
            any(
                i["rule"] == "master_code_unique"
                for i in rules.evaluate(doc, self.rules)
            )
        )

    def test_scope_field_required_for_own_records(self):
        doc = example()
        del doc["roles"]["Distributor"]["scope_field"]
        hit = [
            i
            for i in rules.evaluate(doc, self.rules)
            if i["rule"] == "scope_field_for_own"
        ]
        self.assertEqual(hit[0]["path"], "/roles/Distributor/sees_only")

    def test_steps_must_use_declared_states_per_lifecycle(self):
        doc = example()
        doc["patient"]["steps"][0]["to"] = "limbo"
        hit = [
            i
            for i in rules.evaluate(doc, self.rules)
            if i["rule"] == "patient_step_states"
        ]
        self.assertEqual(hit[0]["path"], "/patient/steps/0/to")


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.view = _View()

    def test_starter_and_example_have_no_errors(self):
        for name in ("starter.yaml", "example.yaml"):
            _, issues = validate.validate_text((PSP / name).read_text(), self.view)
            self.assertFalse(
                validate.has_errors(issues),
                (name, [i for i in issues if i["level"] == "error"][:3]),
            )
        _, strict = validate.validate_text(
            (PSP / "example.yaml").read_text(), self.view, strict=True
        )
        self.assertFalse(validate.has_errors(strict))

    def test_a_wrong_type_is_a_structural_error_with_its_section(self):
        doc = example()
        doc["roles"] = ["Manager"]
        issues = validate.validate_doc(doc, self.view)
        broken = validate.structural_errors(issues)
        self.assertTrue(broken)
        self.assertEqual(broken[0]["path"], "/roles")
        self.assertEqual(broken[0]["section"], "roles")

    def test_missing_required_is_a_warning_until_finalize(self):
        doc = example()
        del doc["patient"]
        loose = [
            i
            for i in validate.validate_doc(doc, self.view)
            if i["code"] == "schema:required"
        ]
        self.assertEqual([i["level"] for i in loose], ["warning"])
        self.assertFalse(validate.structural_errors(loose))
        strict = [
            i
            for i in validate.validate_doc(doc, self.view, strict=True)
            if i["code"] == "schema:required"
        ]
        self.assertEqual([i["level"] for i in strict], ["error"])

    def test_rule_breaches_do_not_block_an_edit_but_do_block_approval(self):
        doc = example()
        doc["patient"]["steps"][0]["by"] = "Ghost"
        issues = validate.validate_doc(doc, self.view)
        self.assertTrue(validate.has_errors(issues))
        self.assertFalse(
            [i for i in validate.structural_errors(issues) if i.get("rule")]
        )

    def test_unreadable_yaml_reports_a_line(self):
        doc, issues = validate.validate_text(
            "journey: x\nroles: [unclosed\n", self.view
        )
        self.assertIsNone(doc)
        self.assertEqual(issues[0]["code"], "yaml")
        self.assertIsNotNone(issues[0]["line"])

    def test_yaml_pyyaml_cannot_read_is_an_error(self):
        # YAML 1.2 (ruamel) reads a `?` inside a flow mapping; PyYAML, which the build uses, does not.
        text = "actions:\n  - {name: submit, confirm: Submit this?, on_done: Notify}\n"
        doc, issues = validate.validate_text(text, self.view)
        self.assertEqual(doc["actions"][0]["confirm"], "Submit this?")
        self.assertEqual(issues[0]["code"], "yaml_compat")
        self.assertEqual(issues[0]["line"], 2)


class PyYAMLCompatTests(unittest.TestCase):
    def test_dump_rt_quotes_flow_scalars_pyyaml_cannot_read(self):
        import yaml

        text = (
            "# kept\n"
            "actions:\n"
            "  - {name: submit, confirm: Submit this?, roles: [A, B], note: 'x: y'}\n"
            "  - name: close\n"
            "    confirm: Close this?\n"
        )
        out = yamlio.dump_rt(yamlio.load_rt(text))
        self.assertIsNone(yamlio.pyyaml_problem(out))
        self.assertEqual(yaml.safe_load(out), yamlio.load(text))
        self.assertIn('confirm: "Submit this?"', out)
        self.assertIn("confirm: Close this?", out)  # block style is fine unquoted
        self.assertIn("# kept", out)
