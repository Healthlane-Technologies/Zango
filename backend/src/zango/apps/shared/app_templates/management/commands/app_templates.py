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

        zipw = sub.add_parser(
            "zip-workspace",
            help="Zip a template app checkout (leaves out .git, node_modules, packages/…).",
        )
        zipw.add_argument("source", help="The checkout directory (has settings.json).")
        zipw.add_argument("out", help="Path of the .zip to write.")
        zipw.add_argument(
            "--exclude",
            action="append",
            default=[],
            help="Extra path to leave out (dir/ or file).",
        )

        att = sub.add_parser(
            "attach-workspace",
            help="Attach a workspace zip to a template as its next version.",
        )
        att.add_argument("slug")
        att.add_argument(
            "source", help="A workspace .zip, or a checkout directory to zip."
        )
        att.add_argument(
            "--version", help="Version for the new draft (default: next patch)."
        )
        att.add_argument(
            "--engine-path",
            action="append",
            dest="engine_paths",
            help="Engine path (repeatable).",
        )
        att.add_argument("--changelog", default="")
        att.add_argument("--publish", action="store_true")

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

        if action == "zip-workspace":
            from zango.apps.shared.app_templates.services.workspace import (
                DEFAULT_EXCLUDES,
                WorkspaceError,
                inspect_zip,
                zip_directory,
            )

            try:
                data = zip_directory(
                    Path(opts["source"]), (*DEFAULT_EXCLUDES, *opts["exclude"])
                )
                info = inspect_zip(data)
            except WorkspaceError as exc:
                raise CommandError(exc.message) from exc
            Path(opts["out"]).write_bytes(data)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Wrote {opts['out']}: {info.entries} files, {len(data) / 1e6:.1f} MB zipped, "
                    f"{info.unzipped_bytes / 1e6:.1f} MB unzipped."
                )
            )
            return

        if action == "attach-workspace":
            return self._attach(opts)

        for template in AppTemplate.objects.all():
            current = template.current_version_id
            self.stdout.write(f"{template.slug}  {template.name}  [{template.status}]")
            for version in template.versions.all():
                mark = "*" if version.pk == current else " "
                self.stdout.write(f"  {mark} {version.version}  {version.status}")

    def _attach(self, opts):
        from django.db import transaction

        from zango.apps.shared.app_templates.models import AppTemplate, VersionStatus
        from zango.apps.shared.app_templates.services.catalogue import clear_caches
        from zango.apps.shared.app_templates.services.packs import LintFailed, publish
        from zango.apps.shared.app_templates.services.workspace import (
            WorkspaceError,
            attach_workspace,
            bump_patch,
            new_draft_from,
            zip_directory,
        )

        template = AppTemplate.objects.filter(slug=opts["slug"]).first()
        if template is None:
            raise CommandError(f"No template {opts['slug']!r}. Import its pack first.")
        source = Path(opts["source"])
        try:
            data = zip_directory(source) if source.is_dir() else source.read_bytes()
            with transaction.atomic():
                draft = template.versions.filter(status=VersionStatus.DRAFT).first()
                if draft is None:
                    base = template.current_version
                    if base is None:
                        raise CommandError(
                            f"{template.slug} has no published version to build on."
                        )
                    draft = new_draft_from(
                        base, opts.get("version") or bump_patch(base.version)
                    )
                elif opts.get("version"):
                    draft.version = opts["version"]
                info = attach_workspace(draft, data, opts.get("engine_paths"))
                self.stdout.write(
                    f"Attached a workspace to {template.slug} {draft.version} (draft): "
                    f"{info.entries} files, {len(data) / 1e6:.1f} MB."
                )
                if opts["publish"]:
                    publish(
                        draft,
                        changelog=opts["changelog"] or "Workspace attached.",
                        by="cli",
                    )
        except LintFailed as exc:
            for issue in exc.issues:
                self.stderr.write(
                    f"  {issue['level']}: {issue['file']} {issue['pointer']} {issue['message']}"
                )
            raise CommandError(str(exc.message)) from exc
        except WorkspaceError as exc:
            raise CommandError(exc.message) from exc
        clear_caches()
        state = "published" if opts["publish"] else "draft"
        self.stdout.write(
            self.style.SUCCESS(f"{template.slug} {draft.version} is {state}.")
        )
