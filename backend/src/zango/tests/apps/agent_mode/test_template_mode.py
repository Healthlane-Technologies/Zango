"""Template mode (AGENT_MODE_TEMPLATE_MODE_PLAN.html): the pieces that need no database.

- prototype_kit: the kit capture turned into prototype parts, and the YAML that goes with them;
- the analyst's first turn on a template opened as it is (T2);
- a build reads the approved version, never the live requirement (T3, G1);
- the change map against a baseline (T4).
"""

import json
import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace

from zango.apps.agent_mode import prototype_kit as pk
from zango.apps.agent_mode.approval_bundle import (
    change_map,
    prototype_index_md,
    write_change_map,
)
from zango.apps.agent_mode.prototype import (
    assemble,
    design_tokens,
    parts_hash,
    static_problems,
)


# A capture as kit_capture_worker returns it, for a two-role app: a list that opens a 360 with two
# tabs, and a sidebar per role.
CAPTURE = {
    "ok": True,
    "app": {"name": "Demo", "radius": "rounded", "density": "comfortable"},
    "vars": {"--page": "#F8F9FB", "--bd": "#E2E4E9", "--brand": "#7C3AED"},
    "pages": [
        {"code": "items", "title": "Items", "type": "crud", "detail_view": None},
        {"code": "item_360", "title": "Item", "type": "detail", "detail_view": "item_360"},
        {"code": "admin_only", "title": "Admin", "type": "crud", "detail_view": None},
    ],
    "roles": [
        {
            "name": "Program Manager",
            "landing": "items",
            "pages": [
                {"page": "items", "record": None, "views": {"": 0}},
                {"page": "item_360", "record": "7", "views": {"": 1, "a": 1, "b": 2}},
                {"page": "admin_only", "error": "did not open"},
            ],
        },
        {
            "name": "Agent",
            "landing": "items",
            "pages": [{"page": "items", "record": None, "views": {"": 0}}],
        },
    ],
    "views": [
        {
            "html": '<div class="z-top"></div><div class="z-content"><table><tbody>'
            '<tr data-a="3" data-kk="0"><td>One</td></tr><tr data-a="4" data-kk="0"><td>Two</td></tr>'
            '</tbody></table><button data-a="5" data-kk="1"><svg xmlns="x" data-lucide="plus" '
            'class="lucide lucide-plus big"><path d="M1"></path></svg>New</button>'
            '<button data-a="6" data-kk="2">Sort</button></div>',
            "acts": {"0": {"g": ["item_360", "7", None]}, "1": {"o": [["modal", 0]]}},
            "overlays": [
                {"kind": "modal", "html": '<div class="mo"><button data-a="9" data-kk="1.0">x</button></div>'}
            ],
        },
        {"html": '<h1>Item 7</h1><button data-kk="0">A</button>', "acts": {"0": {"g": ["item_360", "7", "a"]}}, "overlays": []},
        {"html": "<h1>Item 7</h1><p>tab b</p>", "acts": {}, "overlays": []},
    ],
    "sides": {
        "Program Manager": {
            "html": '<aside class="z-side"><nav><button class="z-ni on" data-a="1" data-kk="s0">Items</button></nav></aside>',
            "acts": {"s0": {"g": ["items", None, None]}},
            "overlays": [],
        },
        "Agent": {"html": '<aside class="z-side"><nav></nav></aside>', "acts": {}, "overlays": []},
    },
}

KIT_HTML = (
    '<html><head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">'
    "<style>:root{--page:#F8F9FB;--bd:#E2E4E9}\nbody{font-family:'Inter',sans-serif}\n"
    "/* the generated app */\n:root{--brand:#4F46E5}\n.z-pill{height:34px}\n.zapp{height:100%}</style>"
    "<script>/* lucide 0.469.0, inlined from https://unpkg.com/lucide@0.469.0/dist/umd/lucide.min.js */</script>"
    "</head><body></body></html>"
)

SPEC = """\
spec_version: 1
app:
  code: demo   # the app
  name: Demo
roles:
  - name: Program Manager
  - name: Agent
pages:
  - { code: items, type: crud, entity: item }
  - { code: item_360, type: detail, detail_view: item_360 }
"""


class KitPartsTests(unittest.TestCase):
    """The kit page itself is the prototype: its markup, styles and scripts, the YAML it draws, a bridge."""

    def setUp(self):
        self.parts = pk.imported_parts(CAPTURE, KIT_HTML, SPEC)
        self.manifest = json.loads(self.parts["manifest.json"])

    def test_one_screen_per_page_a_role_opens_with_maps(self):
        screens = {s["id"]: s for s in self.manifest["screens"]}
        self.assertEqual(sorted(screens), ["item_360", "items"])  # admin_only opened for nobody
        self.assertEqual(screens["items"]["maps"], "/pages/@items")
        self.assertEqual(screens["items"]["roles"], ["program_manager", "agent"])
        self.assertEqual(screens["item_360"]["sample"], "7")
        self.assertEqual(self.manifest["source"], "imported")
        self.assertTrue(self.manifest["kit"])
        self.assertEqual(self.manifest["roles"], {"program_manager": "Program Manager", "agent": "Agent"})
        self.assertEqual(self.manifest["home"], {"program_manager": "items", "agent": "items"})
        self.assertTrue(self.manifest["fonts"][0].startswith("https://fonts.googleapis.com/"))

    def test_parts_assemble_with_no_static_problems(self):
        self.assertEqual(static_problems(self.parts), [])
        self.assertTrue(pk.is_from_kit(self.parts))
        self.assertTrue(pk.is_kit_page(self.parts))
        html = assemble(self.parts)
        self.assertIn("window.ZAS_KIT_SPEC", html)
        self.assertIn("ZAS.ready", html)
        self.assertIn("ZAS.boot()", html)

    def test_the_page_draws_the_yaml_it_is_given(self):
        changed = pk.with_spec(self.parts, SPEC + "# a new column\n")
        self.assertIn("a new column", changed[pk.SPEC_PART])
        self.assertNotIn("a new column", self.parts[pk.SPEC_PART])
        self.assertEqual(pk.with_spec({"a.js": "x"}, SPEC), {"a.js": "x"})  # not a kit page: as it is

    def test_the_bridge_maps_role_codes_to_the_specs_role_names(self):
        bridge = self.parts[pk.BRIDGE_PART]
        self.assertIn('"program_manager": "Program Manager"', bridge)
        self.assertIn("ZAS_GOTO", bridge)

    def test_the_theme_and_canonical_tokens(self):
        tokens = self.parts["tokens.css"]
        self.assertIn("--brand: #7C3AED;", tokens)
        # the greys the kit draws the app with, not the Studio page's own variables
        self.assertIn("--border: #EAECF0;", tokens)
        design = design_tokens(self.parts)
        self.assertEqual(design["tokens"]["brand"], "#7C3AED")
        self.assertEqual(design["tokens"]["border"], "#EAECF0")

    def test_open_spec_adds_design_and_screen_map_and_keeps_comments(self):
        text = pk.open_spec(SPEC, self.parts)
        self.assertIn("# the app", text)
        import yaml

        doc = yaml.safe_load(text)
        self.assertEqual(doc["app"]["design"]["tokens"]["brand"], "#7C3AED")
        self.assertEqual(
            doc["prototype"]["screens"],
            [{"id": "items", "maps": "/pages/@items"}, {"id": "item_360", "maps": "/pages/@item_360"}],
        )
        # what the spec already says wins, and running it twice adds nothing
        self.assertEqual(pk.open_spec(text, self.parts), text)


class ChromeLandmarkTests(unittest.TestCase):
    def test_runtime_chrome_is_not_a_label(self):
        from zango.apps.agent_mode.prototype_coverage import landmarks_module

        lm = landmarks_module()
        dom = (
            '<h1>Vouchers</h1><p data-zas-chrome>14 records</p><table><tr><th>Code</th></tr></table>'
            '<div class="z-pg" data-zas-chrome><button>Previous</button><button>Next</button></div>'
            '<div role="tablist"><button role="tab">Vouchers</button></div>'
            '<nav><div class="z-ng nav-group">Master Data</div><button>Pharmacies</button></nav>'
        )
        marks = lm.landmarks(dom)
        self.assertNotIn("Previous", marks["button"])
        self.assertIsNone(lm.subtitle(dom))
        self.assertEqual(marks["tab"], ["Vouchers"])
        self.assertEqual(marks["menu"], [("Master Data", "Pharmacies")])


class _Template(SimpleNamespace):
    def file_path(self, key):
        return f"/tpl/{key}.md"


class AnalystPreambleTests(unittest.TestCase):
    def _prompt(self, mode):
        from zango.apps.agent_mode.requirements import compose_analyst_prompt

        template = _Template(
            name="Voucher & Coupon Management",
            slug="voucher-coupon",
            version="0.1.1",
            spec_root="app_spec",
            starter_yaml="spec_version: 1",
            is_yaml=True,
        )
        requirement = SimpleNamespace(
            session_id="",
            template_slug="voucher-coupon",
            template=template,
            mode=mode,
            spec_markdown="spec_version: 1",
        )
        ctx = SimpleNamespace(
            packages=[], modules=[], roles=[], app_name="vouchers", workspace_path="/ws"
        )
        return compose_analyst_prompt(
            requirement, ctx, "Add a Finance approval above ₹5,000"
        )

    def test_a_template_opened_as_it_is_edits_instead_of_interviewing(self):
        prompt = self._prompt("template")
        self.assertIn("opened on a template, as it is", prompt)
        self.assertIn("Edit, don't interview", prompt)
        self.assertIn("The design is completely open", prompt)
        self.assertIn("Never approximate an instruction", prompt)
        self.assertIn("Add a Finance approval above ₹5,000", prompt)
        self.assertIn("Make the change now", prompt)
        self.assertNotIn("ask your opening questions", prompt)
        self.assertNotIn("follow that interview", prompt)

    def test_other_template_requirements_keep_the_interview(self):
        prompt = self._prompt("interview")
        self.assertIn("follow that interview", prompt)
        self.assertNotIn("opened on a template, as it is", prompt)


class PinnedBuildTests(unittest.TestCase):
    """G1: a build reads the version approved at Commit, not the requirement as it is now."""

    def _run(self, version, live_parts):
        requirement = SimpleNamespace(
            spec_markdown="live: edited after commit",
            preview_mode="open",
            prototype_parts=live_parts,
            prototype_hash=parts_hash(live_parts),
        )
        return SimpleNamespace(requirement=requirement, requirement_version=version)

    def test_a_pinned_run_reads_the_version(self):
        from zango.apps.agent_mode.template_build import approved

        agreed = {"manifest.json": '{"screens":[{"id":"a"}]}', "screens/a.js": "x"}
        version = SimpleNamespace(
            version=3,
            spec_markdown="agreed: true",
            preview_mode="open",
            prototype_parts=agreed,
            prototype_hash=parts_hash(agreed),
            baseline="template:abc",
        )
        pinned = approved(self._run(version, {"screens/a.js": "edited later"}))
        self.assertEqual(pinned.spec, "agreed: true")
        self.assertEqual(pinned.prototype, agreed)
        self.assertTrue(pinned.is_open)
        self.assertEqual(pinned.baseline, "template:abc")

    def test_a_tampered_version_is_refused(self):
        from zango.apps.agent_mode.template_build import PinMismatch, approved

        version = SimpleNamespace(
            version=3,
            spec_markdown="s",
            preview_mode="open",
            prototype_parts={"screens/a.js": "changed"},
            prototype_hash="0" * 32,
            baseline="",
        )
        with self.assertRaises(PinMismatch):
            approved(self._run(version, {}))

    def test_a_run_from_before_pinning_reads_the_requirement(self):
        from zango.apps.agent_mode.template_build import approved

        pinned = approved(self._run(None, {"screens/a.js": "x"}))
        self.assertEqual(pinned.spec, "live: edited after commit")
        self.assertIsNone(pinned.version)


def _proto(screens: dict, tokens=":root{--brand:#123}", app=".a{}", shell="shell") -> dict:
    manifest = {"screens": [{"id": i, "title": i} for i in screens], "roles": {"r": "R"}}
    parts = {
        "manifest.json": json.dumps(manifest),
        "tokens.css": tokens,
        "app.css": app,
        "shell.js": shell,
    }
    parts.update({f"screens/{i}.js": body for i, body in screens.items()})
    return parts


SCREEN = "".join(f"<div class='row'><b>Field {n}</b><span>value {n}</span></div>" for n in range(30))


class ChangeMapTests(unittest.TestCase):
    def setUp(self):
        self.base = _proto({"dash": SCREEN, "list": SCREEN + "<table></table>", "form": SCREEN})

    def test_identical_is_unchanged(self):
        changes, patches = change_map(self.base, self.base, "template t@1")
        self.assertEqual(set(changes["screens"].values()), {"unchanged"})
        self.assertEqual(changes["baseline"], "template t@1")
        self.assertEqual(patches, {})

    def test_a_theme_only_change_restyles_every_screen(self):
        now = dict(self.base, **{"tokens.css": ":root{--brand:#0A7}"})
        changes, patches = change_map(now, self.base)
        self.assertEqual(set(changes["screens"].values()), {"restyled"})
        self.assertEqual(changes["global"]["tokens.css"], "changed")
        self.assertEqual(changes["global"]["app.css"], "unchanged")
        self.assertEqual(patches, {})

    def test_a_one_screen_edit_tags_exactly_that_screen_with_its_patch(self):
        now = dict(self.base)
        now["screens/list.js"] = self.base["screens/list.js"].replace("Field 3<", "Amount<")
        changes, patches = change_map(now, self.base)
        self.assertEqual(
            changes["screens"], {"dash": "unchanged", "list": "edited", "form": "unchanged"}
        )
        self.assertEqual(list(patches), ["list"])
        self.assertIn("+<b>Amount</b>", patches["list"])

    def test_mostly_new_markup_is_rewritten_and_new_screens_are_new(self):
        now = _proto(
            {"dash": "<main>" + "<p>KPI</p>" * 40 + "</main>", "list": self.base["screens/list.js"],
             "form": SCREEN, "finance": SCREEN},
        )
        changes, _ = change_map(now, self.base)
        self.assertEqual(changes["screens"]["dash"], "rewritten")
        self.assertEqual(changes["screens"]["finance"], "new")
        self.assertEqual(changes["screens"]["list"], "unchanged")

    def test_a_removed_screen_is_listed(self):
        now = _proto({"dash": SCREEN, "list": self.base["screens/list.js"]})
        changes, _ = change_map(now, self.base)
        self.assertEqual(changes["removed"], ["form"])

    def test_no_baseline_makes_every_screen_new(self):
        changes, _ = change_map(self.base, {}, "")
        self.assertEqual(set(changes["screens"].values()), {"new"})
        self.assertEqual(changes["baseline"], "none")

    def test_bundle_files_and_the_index_column(self):
        now = dict(self.base)
        now["screens/form.js"] = SCREEN.replace("value 1<", "value one<")
        with tempfile.TemporaryDirectory() as tmp:
            changes = write_change_map(tmp, now, ("template t@1", self.base))
            self.assertTrue((Path(tmp) / "changes.json").is_file())
            self.assertTrue((Path(tmp) / "screens" / "form" / "diff.patch").is_file())
            self.assertFalse((Path(tmp) / "screens" / "dash" / "diff.patch").exists())
        capture = {
            "screens": [
                {"id": "dash", "title": "dash", "roles": [{"role": "r", "files": ["x"]}]},
                {"id": "form", "title": "form", "roles": [{"role": "r", "files": ["x"]}]},
            ]
        }
        md = prototype_index_md(capture, {}, None, changes=changes)
        self.assertIn("**Change map**", md)
        self.assertIn("| Change |", md)
        self.assertIn("| `form` | form | r |  | screens/form/ |  | edited (`diff.patch`) |", md)
        self.assertIn("| `dash` | dash | r |  | screens/dash/ |  | unchanged |", md)
        # without a baseline the table is as before
        self.assertNotIn("Change", prototype_index_md(capture, {}, None))


class SpecScreensTests(unittest.TestCase):
    """A page the spec gains after the template was drawn gets a manifest screen (and a parent list)."""

    SPEC = (
        "pages:\n"
        "  - { code: campaigns, type: crud, entity: campaign }\n"
        "  - { code: voucher_360, type: detail, detail_view: voucher_360 }\n"
        "  - { code: vouchers, type: crud, entity: voucher }\n"
        "roles:\n"
        "  - { name: Program Manager, menu: [{ page: campaigns }, { page: vouchers }] }\n"
        "detail_views:\n"
        "  - { code: voucher_360, hero: voucher, roles: [Program Manager] }\n"
    )

    def _parts(self):
        manifest = {
            "source": "imported",
            "screens": [{"id": "campaigns", "title": "Campaigns", "roles": ["program_manager"], "maps": "/pages/@campaigns"}],
        }
        return {"manifest.json": json.dumps(manifest), pk.SPEC_PART: ""}

    def test_new_pages_get_screens_and_a_record_one_gets_parent_and_sample(self):
        out = pk.with_spec({**self._parts(), "body.html": "<x>", "imported/script-zz-bridge.js": "ZAS.ready"}, self.SPEC)
        screens = {s["id"]: s for s in json.loads(out["manifest.json"])["screens"]}
        self.assertEqual(set(screens), {"campaigns", "voucher_360", "vouchers"})
        v = screens["voucher_360"]
        self.assertEqual((v["record"], v["sample"], v["parent"], v["maps"]), ("voucher_360", "1", "vouchers", "/pages/@voucher_360"))
        self.assertEqual(v["roles"], ["program_manager"])
        self.assertEqual(screens["campaigns"]["title"], "Campaigns")  # a drawn screen is left as it was

    def test_running_it_again_changes_nothing(self):
        once = pk.spec_screens(self._parts(), self.SPEC)
        self.assertIs(pk.spec_screens(once, self.SPEC), once)
