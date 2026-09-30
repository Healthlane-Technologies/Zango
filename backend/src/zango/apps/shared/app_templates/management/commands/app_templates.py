"""``manage.py app_templates import|export|list`` — manage template packs."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Import, export or list app templates."

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="action", required=True)

        imp = sub.add_parser("import", help="Import a pack directory or .zip.")
        imp.add_argument("source")
        imp.add_argument(
            "--publish", action="store_true", help="Publish after importing."
        )
        imp.add_argument("--version", help="Override the manifest's version.")

        exp = sub.add_parser("export", help="Export a version as a pack .zip.")
        exp.add_argument("slug")
        exp.add_argument("out", help="Path of the .zip to write.")
        exp.add_argument("--version", help="Version to export (default: current).")

        sub.add_parser("list", help="List templates and their versions.")

    def handle(self, *args, **opts):
        from zango.apps.shared.app_templates.models import AppTemplate
        from zango.apps.shared.app_templates.services.catalogue import clear_caches
        from zango.apps.shared.app_templates.services.packs import (
            LintFailed,
            PackError,
            export_pack,
            import_pack,
        )

        action = opts["action"]
        if action == "import":
            try:
                version, created = import_pack(
                    opts["source"],
                    publish_now=opts["publish"],
                    version=opts.get("version"),
                    by="cli",
                )
            except LintFailed as exc:
                for issue in exc.issues:
                    self.stderr.write(
                        f"  {issue['level']}: {issue['file']} {issue['pointer']} {issue['message']}"
                    )
                raise CommandError(str(exc.message)) from exc
            except PackError as exc:
                raise CommandError(exc.message) from exc
            clear_caches()
            verb = "Imported" if created else "Unchanged"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb}: {version.template.slug} {version.version} ({version.status})"
                )
            )
            return

        if action == "export":
            template = AppTemplate.objects.filter(slug=opts["slug"]).first()
            if template is None:
                raise CommandError(f"No template {opts['slug']!r}.")
            version = (
                template.versions.filter(version=opts["version"]).first()
                if opts.get("version")
                else template.current_version
            )
            if version is None:
                raise CommandError("No such version.")
            Path(opts["out"]).write_bytes(export_pack(version))
            self.stdout.write(self.style.SUCCESS(f"Wrote {opts['out']}"))
            return

        for template in AppTemplate.objects.all():
            current = template.current_version_id
            self.stdout.write(f"{template.slug}  {template.name}  [{template.status}]")
            for version in template.versions.all():
                mark = "*" if version.pk == current else " "
                self.stdout.write(f"  {mark} {version.version}  {version.status}")
