import asyncio
import io
import json
import zipfile

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, lint

from .test_spec_tools import _NoQueries
from .tests import AppTemplatesTestBase


def make_pdf(text="Eligibility: HER2-positive patients only.") -> bytes:
    import fitz

    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def make_docx(
    paragraphs=("Program SOP", "Distributors see only their own orders."),
) -> bytes:
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    body += "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Role</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Manager</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
    xml = f'<?xml version="1.0"?><w:document xmlns:w="{w}"><w:body>{body}</w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


def make_xlsx() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["SKU", "Free after"])
    ws.append(["enhertu_100mg", 3])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class DocumentTests(AppTemplatesTestBase):
    def test_every_supported_type_is_extracted(self):
        from zango.apps.agent_mode.documents import extract

        pdf = extract("sop.pdf", make_pdf())
        self.assertEqual((pdf.pages, pdf.content_type), (1, "application/pdf"))
        self.assertIn("HER2-positive", pdf.text)
        docx = extract("SOP v2.docx", make_docx())
        self.assertIn("Distributors see only their own orders.", docx.text)
        self.assertIn("| Role | Manager |", docx.text)
        xlsx = extract("orders.xlsx", make_xlsx())
        self.assertEqual(xlsx.sheets, ["Orders"])
        self.assertIn("| enhertu_100mg | 3 |", xlsx.text)
        self.assertIn("| a | b |", extract("x.csv", b"a,b\n").text)
        self.assertEqual(extract("notes.md", "# Héllo".encode()).text, "# Héllo")

    def test_bad_uploads_are_refused(self):
        from zango.apps.agent_mode import documents
        from zango.apps.agent_mode.documents import DocumentError, extract, extract_all

        for name, data in (
            ("x.exe", b"MZ"),
            ("fake.pdf", b"not a pdf"),
            ("broken.docx", b"PK nope"),
            ("e.txt", b""),
        ):
            with self.assertRaises(DocumentError, msg=name):
                extract(name, data)
        with self.assertRaises(DocumentError):
            extract_all([("a.txt", b"x")] * 11)
        with (
            mock.patch.object(documents, "MAX_UNZIPPED_BYTES", 10),
            self.assertRaises(DocumentError),
        ):
            extract("bomb.docx", make_docx())

    def test_names_are_made_safe(self):
        from zango.apps.agent_mode.documents import extract

        self.assertEqual(extract("../../etc/pass wd.txt", b"x").name, "pass wd.txt")

    def test_docs_dir_has_originals_extracts_and_an_index(self):
        from zango.apps.agent_mode.documents import extract, write_docs_dir

        rows = []
        for i, (name, data) in enumerate(
            (("sop.pdf", make_pdf()), ("plan.docx", make_docx())), 1
        ):
            e = extract(name, data)
            rows.append(SimpleNamespace(pk=i, **e.model_fields()))
        req = mock.Mock(object_uuid="r1")
        req.documents.all.return_value.order_by.return_value = rows
        with self.settings(BASE_DIR=self.tmp.name):
            root = write_docs_dir("onc_pap", req)
        self.assertTrue((root / "01-sop.pdf").is_file())
        self.assertTrue(
            (root / "02-plan.docx.txt").read_text().startswith("Program SOP")
        )
        index = (root / "INDEX.md").read_text()
        self.assertIn("sop.pdf", index)
        self.assertIn("1 pages", index)

    def test_drafting_is_chosen_for_documents_or_a_detailed_brief(self):
        from zango.apps.agent_mode.documents import wants_draft

        self.assertTrue(wants_draft("", 1))
        self.assertTrue(wants_draft("x" * 700, 0))
        self.assertFalse(wants_draft("A PAP for oncology.", 0))


class ReferenceTests(AppTemplatesTestBase):
    def test_psp_ships_a_valid_reference(self):
        version, _ = import_pack(PACKS_DIR / "psp", publish_now=True)
        self.assertEqual([r["id"] for r in version.references], ["enhertu_pap"])
        self.assertTrue(version.drafting_md.startswith("# Drafting"))
        catalogue.clear_caches()
        view = catalogue.get_template("psp")
        ref = view.references[0]
        self.assertTrue(Path(ref["path"]).is_file())
        self.assertTrue(Path(view.file_path("drafting")).is_file())

    def test_an_invalid_reference_does_not_lint(self):
        root = self.pack()
        (root / "references").mkdir()
        (root / "references" / "bad.yaml").write_text("roles: not-a-list\n")
        (root / "references.json").write_text(
            json.dumps([{"id": "bad", "file": "references/bad.yaml"}])
        )
        manifest = json.loads((root / "template.json").read_text())
        manifest["references"] = "references.json"
        (root / "template.json").write_text(json.dumps(manifest))
        version, _ = import_pack(root)
        self.assertTrue(any(i["file"] == "references/bad.yaml" for i in lint(version)))


class DraftModeTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "psp", publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("psp")

    def requirement(self, mode="draft", reference=""):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        r = AgentRequirement(initial_prompt="go")
        seed_template_requirement(r, self.template)
        r.mode, r.reference_id = mode, reference
        r.save = lambda *a, **k: None
        return r

    class Ctx:
        app_name = "onc_pap"
        workspace_path = "/w"
        packages = []
        modules = []
        roles = []

    def test_the_draft_prompt_replaces_the_interview(self):
        from zango.apps.agent_mode.requirements import compose_analyst_prompt

        text = compose_analyst_prompt(
            self.requirement(reference="enhertu_pap"),
            self.Ctx(),
            "see docs",
            docs_dir="/d",
        )
        self.assertIn("Draft this journey in one pass", text)
        self.assertIn(self.template.file_path("drafting"), text)
        self.assertIn("/d/INDEX.md", text)
        self.assertIn("`enhertu_pap`", text)
        self.assertIn("The user chose `enhertu_pap`", text)
        self.assertIn("do not ask questions", text)
        self.assertNotIn("ask your opening questions", text)

        interview = compose_analyst_prompt(
            self.requirement(mode="interview"), self.Ctx(), "a PAP"
        )
        self.assertNotIn("Draft this journey", interview)

    def test_draft_turns_get_room_and_the_docs(self):
        from zango.apps.agent_mode.requirements import build_analyst_options
        from zango.apps.agent_mode.spec_tools import SpecWorkbench, build_spec_server

        bench = SpecWorkbench(
            self.template.starter_yaml, self.template, emit=lambda e: None
        )
        req = mock.Mock(session_id="", mode="draft")
        with mock.patch("zango.apps.agent_mode.options.build_env", return_value={}):
            opts = build_analyst_options(
                ctx=mock.Mock(workspace_path="/tmp"),
                creds=object(),
                requirement=req,
                spec_server=build_spec_server(bench),
                docs_dir="/docs",
            )
        self.assertIn("/docs", opts.add_dirs)
        self.assertGreaterEqual(opts.max_turns, 150)
        self.assertIn("mcp__spec__spec_flag", opts.allowed_tools)

    def test_flags_and_decisions_tools(self):
        from zango.apps.agent_mode.spec_tools import (
            SpecWorkbench,
            ToolRefused,
            make_handler,
            tool_specs,
        )

        emitted = []
        bench = SpecWorkbench(
            self.template.starter_yaml, self.template, emit=emitted.append
        )
        handlers = {n: make_handler(bench, fn) for n, _, _, fn in tool_specs(bench)}
        with _NoQueries():
            asyncio.run(
                handlers["spec_flag"](
                    {
                        "path": "/name",
                        "kind": "inferred",
                        "note": "from the RFP title",
                        "source": {
                            "document": "rfp.pdf",
                            "locator": "p. 1",
                            "quote": "Onc PAP",
                        },
                    }
                )
            )
            bad = asyncio.run(
                handlers["spec_flag"](
                    {"path": "/nope/x", "kind": "inferred", "note": "?"}
                )
            )
            asyncio.run(
                handlers["spec_open_decisions"](
                    {
                        "items": [
                            {
                                "question": "Who approves enrolment?",
                                "options": ["Manager", "Executive"],
                                "path": "/programs",
                            }
                        ]
                    }
                )
            )
        self.assertTrue(bad["is_error"])
        self.assertEqual(emitted[-1]["flags"][0]["source"]["locator"], "p. 1")
        self.assertEqual(emitted[-1]["flags"][0]["source"]["document"], "rfp.pdf")
        self.assertEqual(emitted[-1]["open_decisions"][0]["recommended"], "Manager")
        with self.assertRaises(ToolRefused):
            bench.set_open_decisions([{"question": f"q{i}"} for i in range(9)])
        with self.assertRaises(ToolRefused):
            bench.mark_ready("done")  # decisions still open
        bench.unflag("/name")
        self.assertEqual(bench.flags, [])

    def test_review_items_are_saved_without_touching_the_yaml(self):
        from zango.apps.agent_mode.tasks import _record_spec_edit

        r = self.requirement()
        saved = {}
        r.save = lambda update_fields=None, **k: saved.setdefault(
            "fields", update_fields
        )
        before = r.spec_markdown
        _record_spec_edit(
            r,
            {
                "flags": [{"path": "/name", "kind": "default", "note": "n"}],
                "open_decisions": [],
            },
        )
        self.assertEqual(r.spec_markdown, before)
        self.assertEqual(r.spec_flags[0]["path"], "/name")
        self.assertIn("spec_flags", saved["fields"])
        self.assertNotIn("spec_markdown", saved["fields"])

    def test_manual_edits_and_confirm_clear_flags(self):
        from zango.apps.agent_mode.template_spec import confirm_flags, save_manual

        r = self.requirement()
        r.spec_flags = [
            {"path": "/name", "kind": "default", "note": "x"},
            {"path": "/journey", "kind": "default", "note": "y"},
        ]
        code, payload = save_manual(
            r, r.spec_markdown.replace("name: ", "name: Onc ", 1), r.draft_revision
        )
        self.assertEqual(code, 200, payload)
        self.assertEqual([f["path"] for f in payload["flags"]], ["/journey"])
        self.assertEqual(payload["flags"][0]["section"], "program")
        code, payload = confirm_flags(r, ["/journey"])
        self.assertEqual((code, payload["flags"]), (200, []))

    def test_open_decisions_block_approval_and_answers_compose_one_message(self):
        from zango.apps.agent_mode.template_spec import (
            approval_problem,
            decisions_message,
        )

        r = self.requirement()
        r.spec_is_draft = False
        r.open_decisions = [{"id": "d1", "question": "Who approves?"}]
        self.assertEqual(approval_problem(r)[0], 409)
        body, ids = decisions_message(
            "",
            [
                {
                    "id": "d1",
                    "question": "Who approves?",
                    "path": "/programs",
                    "answer": "Manager",
                }
            ],
        )
        self.assertIn("Who approves? (/programs): Manager", body)
        self.assertEqual(ids, ["d1"])
