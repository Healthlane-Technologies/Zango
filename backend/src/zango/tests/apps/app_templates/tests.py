import json
import os
import tempfile

from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import override_settings

from zango.apps.shared.app_templates.models import (
    AppTemplate,
    AppTemplateFile,
    AppTemplateVersion,
    ImmutableVersionError,
    VersionStatus,
)
from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.materialise import materialise
from zango.apps.shared.app_templates.services.packs import (
    LintFailed,
    PackError,
    export_pack,
    import_pack,
    lint,
    publish,
)
from zango.apps.shared.app_templates.services.paths import normalise_pack_path
from zango.test.cases import ZangoTestCase


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["journey"],
    "properties": {
        "journey": {"type": "string", "title": "Code"},
        "roles": {
            "type": "array",
            "items": {"type": "object", "properties": {"name": {"type": "string"}}},
        },
    },
}


def write_pack(
    root: Path,
    *,
    slug="demo",
    version="1.0.0",
    starter="journey: demo\n",
    skill_name="zango-demo-builder",
):
    root.mkdir(parents=True, exist_ok=True)
    (root / "template.json").write_text(
        json.dumps(
            {
                "slug": slug,
                "name": "Demo Program",
                "version": version,
                "category": "Testing",
                "one_liner": "A tiny template for tests.",
                "aka": ["demo"],
                "fits_when": ["you are testing"],
                "gives_you": ["nothing real"],
                "catalogue": {"description": "Only for tests."},
                "spec_format": "yaml",
                "spec_root": "journey",
                "build_skill_name": skill_name,
                "interview": "INTERVIEW.md",
                "schema": "SCHEMA.md",
                "starter": "starter.yaml",
                "example": "example.yaml",
                "json_schema": "schema.json",
                "ui_schema": "ui.json",
                "rules": "rules.json",
                "skill_dir": "skill",
            }
        )
    )
    (root / "INTERVIEW.md").write_text("# Interview\nAsk about roles.\n")
    (root / "SCHEMA.md").write_text("# Vocabulary\n")
    (root / "starter.yaml").write_text(starter)
    (root / "example.yaml").write_text("journey: demo\nroles:\n  - name: Manager\n")
    (root / "schema.json").write_text(json.dumps(SCHEMA))
    (root / "ui.json").write_text(
        json.dumps(
            {"sections": [{"id": "roles", "title": "Roles", "pointer": "/roles"}]}
        )
    )
    (root / "rules.json").write_text(
        json.dumps(
            [
                {
                    "id": "unique-role",
                    "kind": "unique",
                    "level": "error",
                    "path": "/roles/*",
                    "key": "name",
                    "message": "Two roles share a name.",
                }
            ]
        )
    )
    (root / "skill" / "references").mkdir(parents=True, exist_ok=True)
    (root / "skill" / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: test\n---\n# Build it\n"
    )
    (root / "skill" / "references" / "roles.md").write_text(
        "Roles become user roles.\n"
    )
    return root


class AppTemplatesTestBase(ZangoTestCase):
    @classmethod
    def get_test_module_path(cls):
        return os.path.join("apps/app_templates")

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = "testserver"
        tenant.tenant_type = "public"
        return tenant

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.testserver.com"

    @classmethod
    def get_test_schema_name(cls):
        return "public"

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(
            AGENT_MODE_TEMPLATES_DIR=os.path.join(self.tmp.name, "materialised")
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        catalogue.clear_caches()
        self.addCleanup(catalogue.clear_caches)
        # Keep these tests independent of whatever packs ship with Zango.
        AppTemplate.objects.exclude(
            slug__in=[p.name for p in PACKS_DIR.iterdir()]
        ).delete()

    def pack(self, name="demo", **kw):
        return write_pack(Path(self.tmp.name) / name, **kw)


class ImportAndPublishTests(AppTemplatesTestBase):
    def test_import_creates_a_draft_with_skill_files(self):
        version, created = import_pack(self.pack())
        self.assertTrue(created)
        self.assertEqual(version.status, VersionStatus.DRAFT)
        self.assertEqual(version.template.name, "Demo Program")
        self.assertEqual(version.catalogue["fits_when"], ["you are testing"])
        self.assertEqual(
            sorted(version.files.values_list("path", flat=True)),
            ["SKILL.md", "references/roles.md"],
        )
        self.assertIsNone(version.template.current_version)

    def test_publish_makes_it_current_and_is_idempotent_on_reimport(self):
        version, _ = import_pack(self.pack(), publish_now=True)
        self.assertEqual(version.status, VersionStatus.PUBLISHED)
        self.assertEqual(len(version.content_sha), 64)
        self.assertEqual(version.template.current_version_id, version.pk)

        again, created = import_pack(self.pack())
        self.assertFalse(created)
        self.assertEqual(again.pk, version.pk)

    def test_same_version_with_different_content_is_refused(self):
        import_pack(self.pack(), publish_now=True)
        with self.assertRaises(PackError):
            import_pack(self.pack(starter="journey: changed\n"))

    def test_a_new_version_becomes_current_and_the_old_one_stays_resolvable(self):
        v1, _ = import_pack(self.pack(), publish_now=True)
        v2, _ = import_pack(
            self.pack(version="1.1.0", starter="journey: v2\n"), publish_now=True
        )
        catalogue.clear_caches()
        self.assertEqual(catalogue.get_template("demo").version, "1.1.0")
        pinned = catalogue.get_template("demo", version_uuid=v1.object_uuid)
        self.assertEqual(pinned.version, "1.0.0")
        self.assertIn("journey: demo", pinned.starter_yaml)

    def test_export_round_trips(self):
        version, _ = import_pack(self.pack(), publish_now=True)
        blob = export_pack(version)
        again, created = import_pack(blob)
        self.assertFalse(created)
        self.assertEqual(again.pk, version.pk)


class ImmutabilityTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(self.pack(), publish_now=True)

    def test_published_content_cannot_change(self):
        self.version.starter_yaml = "journey: tampered\n"
        with self.assertRaises(ImmutableVersionError):
            self.version.save()

    def test_published_version_can_be_deprecated_but_not_deleted(self):
        self.version.status = VersionStatus.DEPRECATED
        self.version.save()
        with self.assertRaises(ImmutableVersionError):
            self.version.delete()

    def test_published_files_cannot_change(self):
        row = self.version.files.get(path="SKILL.md")
        row.content = "tampered"
        with self.assertRaises(ImmutableVersionError):
            row.save()

    def test_only_one_draft_per_template(self):
        AppTemplateVersion.objects.create(
            template=self.version.template, version="2.0.0"
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AppTemplateVersion.objects.create(
                template=self.version.template, version="2.1.0"
            )


class LintTests(AppTemplatesTestBase):
    def test_clean_pack_has_no_errors(self):
        version, _ = import_pack(self.pack())
        self.assertEqual([i for i in lint(version) if i["level"] == "error"], [])

    def test_starter_that_breaks_the_schema_blocks_publishing(self):
        version, _ = import_pack(self.pack(starter="roles: not-a-list\n"))
        issues = lint(version)
        files = {i["file"] for i in issues if i["level"] == "error"}
        self.assertIn("starter.yaml", files)
        with self.assertRaises(LintFailed):
            publish(version)
        version.refresh_from_db()
        self.assertEqual(version.status, VersionStatus.DRAFT)

    def test_skill_name_must_match_the_manifest(self):
        root = self.pack()
        (root / "skill" / "SKILL.md").write_text("---\nname: something-else\n---\n")
        version, _ = import_pack(root)
        self.assertTrue(
            any(
                i["file"] == "skill/SKILL.md" and i["level"] == "error"
                for i in lint(version)
            )
        )

    def test_ui_pointer_must_resolve(self):
        root = self.pack()
        (root / "ui.json").write_text(
            json.dumps({"sections": [{"id": "x", "pointer": "/nope"}]})
        )
        version, _ = import_pack(root)
        self.assertTrue(any(i["file"] == "ui.json" for i in lint(version)))


class MaterialiseTests(AppTemplatesTestBase):
    def test_layout_and_idempotence(self):
        version, _ = import_pack(self.pack(), publish_now=True)
        path = materialise(version)
        self.assertTrue((path / ".claude-plugin" / "plugin.json").is_file())
        self.assertEqual(
            json.loads((path / ".claude-plugin" / "plugin.json").read_text())["name"],
            "zango-tpl-demo",
        )
        self.assertTrue((path / "skills" / "zango-demo-builder" / "SKILL.md").is_file())
        self.assertTrue(
            (
                path / "skills" / "zango-demo-builder" / "references" / "roles.md"
            ).is_file()
        )
        self.assertTrue((path / "requirements" / "INTERVIEW.md").is_file())
        self.assertEqual(
            json.loads((path / "requirements" / "schema.json").read_text()), SCHEMA
        )
        mtime = (path / "requirements" / "INTERVIEW.md").stat().st_mtime
        self.assertEqual(materialise(version), path)
        self.assertEqual(
            (path / "requirements" / "INTERVIEW.md").stat().st_mtime, mtime
        )

    def test_unsafe_paths_are_refused(self):
        for bad in (
            "../etc/passwd",
            "/abs",
            "a/../../b",
            ".hidden",
            "a/.git/config",
            "",
        ):
            with self.assertRaises(ValidationError, msg=bad):
                normalise_pack_path(bad)
        self.assertEqual(normalise_pack_path("references\\a.md"), "references/a.md")

    def test_file_rows_refuse_traversal(self):
        version, _ = import_pack(self.pack())
        with self.assertRaises(ValidationError):
            AppTemplateFile(version=version, path="../escape.md", content="x").save()


class CatalogueTests(AppTemplatesTestBase):
    def test_view_has_the_old_interface(self):
        import_pack(self.pack(), publish_now=True)
        view = catalogue.get_template("  DEMO ")
        self.assertIsNotNone(view)
        self.assertTrue(view.is_yaml)
        self.assertEqual(view.spec_root, "journey")
        self.assertTrue(Path(view.file_path("interview")).is_file())
        self.assertTrue(Path(view.file_path("schema")).is_file())
        self.assertEqual(view.sections, (("roles", "Roles"),))
        self.assertEqual(view.qualified_skill, "zango-tpl-demo:zango-demo-builder")
        self.assertEqual(catalogue.spec_format_for("demo"), "yaml")
        self.assertEqual(catalogue.spec_format_for("nope"), "markdown")
        self.assertIsNone(catalogue.get_template(None))

    def test_drafts_and_archived_templates_are_not_offered(self):
        import_pack(self.pack())
        self.assertNotIn("demo", catalogue.load_templates())
        version, _ = import_pack(self.pack(), publish_now=True)
        catalogue.clear_caches()
        self.assertIn("demo", catalogue.load_templates())
        template = version.template
        template.status = "archived"
        template.save()
        catalogue.bump_revision()
        self.assertNotIn("demo", catalogue.load_templates())

    def test_digest_points_the_analyst_at_the_materialised_pack(self):
        import_pack(self.pack(), publish_now=True)
        digest = catalogue.catalogue_digest()
        view = catalogue.get_template("demo")
        self.assertIn("Demo Program  (slug: demo)", digest)
        self.assertIn("Offer it when:", digest)
        self.assertIn(f"pack: {view.path}/", digest)


class BundledPackTests(AppTemplatesTestBase):
    def test_bundled_packs_are_seeded_and_publishable(self):
        packs = (
            [p for p in PACKS_DIR.iterdir() if (p / "template.json").is_file()]
            if PACKS_DIR.is_dir()
            else []
        )
        if not packs:
            self.skipTest("no bundled packs")
        for pack in packs:
            version, _ = import_pack(pack, publish_now=True)
            self.assertEqual(version.status, VersionStatus.PUBLISHED)
            errors = [i for i in lint(version) if i["level"] == "error"]
            self.assertEqual(errors, [], pack.name)


class YamlTests(AppTemplatesTestBase):
    def test_specs_are_read_as_yaml_1_2(self):
        # YAML 1.1 (PyYAML) turns a bare `on:` key into True; PSP uses it.
        from zango.apps.shared.app_templates.services.spec import yamlio

        self.assertEqual(
            yamlio.load("notify_client:\n  on: [approved]\n"),
            {"notify_client": {"on": ["approved"]}},
        )
        with self.assertRaises(yamlio.SpecYAMLError) as ctx:
            yamlio.load("a: [unclosed\n")
        self.assertIsNotNone(ctx.exception.line)
