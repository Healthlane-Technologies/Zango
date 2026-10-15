"""Write side of the catalogue: import, lint, publish and export template packs.

A pack is a directory (or a zip of one)::

    template.json      manifest: identity, version, catalogue, file names
    schema.json        JSON Schema the requirement YAML must satisfy
    ui.json            builder sections for the console
    rules.json         cross-reference rules
    INTERVIEW.md       how the analyst runs the conversation
    SCHEMA.md          the prose vocabulary the analyst reads
    starter.yaml       the draft a new requirement starts from
    example.yaml       a fully answered example
    skill/...          the build skill (SKILL.md + references); packs on the
                       generic spec have none (see generic.py)

File names other than the manifest are whatever template.json says, so older
packs keep importing. Importing is idempotent: a pack whose content matches an
existing version is a no-op.
"""

from __future__ import annotations

import io
import json
import posixpath
import re
import zipfile

from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import (
    MAX_VERSION_BYTES,
    MAX_VERSION_FILES,
    SEMVER_RE,
    SLUG_RE,
    AppTemplate,
    AppTemplateFile,
    AppTemplateVersion,
    SpecFormat,
    TemplateStatus,
    VersionStatus,
)
from .catalogue import bump_revision
from .paths import content_sha, normalise_pack_path, sha256_file


MANIFEST = "template.json"
RULE_KINDS = ("unique", "ref", "required_when", "max_items", "exactly_one")
RULE_LEVELS = ("error", "warning")


class PackError(ValidationError):
    """A pack that cannot be imported, with a message fit for a user."""


class LintFailed(ValidationError):
    """Publishing was refused; ``issues`` lists why."""

    def __init__(self, issues):
        self.issues = issues
        errors = [i for i in issues if i["level"] == "error"]
        super().__init__(f"{len(errors)} problem(s) must be fixed before publishing.")


@dataclass
class Pack:
    manifest: dict
    documents: dict  # file name -> text (manifest-referenced files)
    skill_files: dict = field(default_factory=dict)  # path in skill dir -> text
    references: list = field(default_factory=list)  # [{id, title, summary, tags, yaml}]


# ---------------------------------------------------------------- reading --


def _read_source(source) -> dict:
    """All text files of a pack directory or zip, keyed by relative path."""
    files = {}
    if isinstance(source, (bytes, bytearray)) or (
        isinstance(source, (str, Path)) and str(source).endswith(".zip")
    ):
        data = (
            source
            if isinstance(source, (bytes, bytearray))
            else Path(source).read_bytes()
        )
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            # Tolerate a single top-level folder inside the zip.
            prefix = ""
            tops = {n.split("/", 1)[0] for n in names}
            if len(tops) == 1 and all("/" in n for n in names):
                prefix = tops.pop() + "/"
            for name in names:
                rel = name[len(prefix) :]
                if _skipped(rel):
                    continue
                files[rel] = _text_or_bytes(zf.read(name))
        return files

    root = Path(source)
    if not root.is_dir():
        raise PackError(f"{source} is not a directory or a .zip file.")
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_file() and not _skipped(rel):
            files[rel] = _text_or_bytes(path.read_bytes())
    return files


def _skipped(rel: str) -> bool:
    """Files a pack never carries: OS litter, hidden files, Python caches."""
    parts = rel.split("/")
    return (
        rel.startswith("__MACOSX/")
        or any(p.startswith(".") or p == "__pycache__" for p in parts)
        or rel.endswith((".pyc", ".pyo"))
    )


def _text_or_bytes(data: bytes):
    """A file's text, or its bytes when it is not UTF-8 (an image, say)."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data


def read_pack(source) -> Pack:
    raw_files = _read_source(source)
    if MANIFEST not in raw_files:
        raise PackError(f"The pack has no {MANIFEST}.")
    # Only the build skill may carry binary files; everything the manifest
    # names is read as text.
    files = _TextOnly(raw_files)
    try:
        manifest = json.loads(files[MANIFEST])
    except ValueError as exc:
        raise PackError(f"{MANIFEST} is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PackError(f"{MANIFEST} must be a JSON object.")
    if (
        not manifest.get("slug")
        and isinstance(source, (str, Path))
        and Path(source).is_dir()
    ):
        manifest["slug"] = Path(source).name

    documents = {}
    for key in (
        "interview",
        "schema",
        "starter",
        "example",
        "json_schema",
        "ui_schema",
        "rules",
    ):
        name = str(manifest.get(key) or "").strip()
        if name:
            if name not in files:
                raise PackError(
                    f"{MANIFEST} names {key} = {name!r}, which is not in the pack."
                )
            documents[key] = files[name]

    for key in ("drafting",):
        name = str(manifest.get(key) or "").strip()
        if name:
            if name not in files:
                raise PackError(
                    f"{MANIFEST} names {key} = {name!r}, which is not in the pack."
                )
            documents[key] = files[name]

    references = []
    index_name = str(manifest.get("references") or "").strip()
    if index_name:
        if index_name not in files:
            raise PackError(
                f"{MANIFEST} names references = {index_name!r}, which is not in the pack."
            )
        try:
            entries = json.loads(files[index_name])
        except ValueError as exc:
            raise PackError(f"{index_name} is not valid JSON: {exc}") from exc
        base = posixpath.dirname(index_name)
        for entry in entries if isinstance(entries, list) else []:
            rid = str((entry or {}).get("id") or "").strip()
            rel = (
                posixpath.join(base, str(entry.get("file") or f"{rid}.yaml"))
                if base
                else str(entry.get("file") or f"{rid}.yaml")
            )
            if not re.match(r"^[a-z][a-z0-9_-]{1,63}$", rid) or rel not in files:
                raise PackError(
                    f"Reference {rid!r} in {index_name} is missing or misnamed."
                )
            references.append(
                {
                    "id": rid,
                    "title": str(entry.get("title") or rid),
                    "summary": str(entry.get("summary") or ""),
                    "tags": [str(t) for t in entry.get("tags") or []][:12],
                    "yaml": files[rel],
                }
            )

    for key in ("adapter", "html"):
        name = str((manifest.get("builder") or {}).get(key) or "").strip()
        if name:
            if name not in files:
                raise PackError(
                    f"{MANIFEST} names builder {key} = {name!r}, which is not in the pack."
                )
            documents[f"builder_{key}"] = files[name]

    skill_files = {}
    skill_dir = str(manifest.get("skill_dir") or "").strip().strip("/")
    if skill_dir:
        prefix = skill_dir + "/"
        for rel, value in raw_files.items():
            if rel.startswith(prefix):
                skill_files[normalise_pack_path(rel[len(prefix) :])] = value
    if len(skill_files) > MAX_VERSION_FILES:
        raise PackError(f"The build skill has more than {MAX_VERSION_FILES} files.")
    total = sum(
        len(t if isinstance(t, (bytes, bytearray)) else t.encode("utf-8"))
        for t in list(documents.values()) + list(skill_files.values())
    )
    if total > MAX_VERSION_BYTES:
        raise PackError(f"The pack is larger than {MAX_VERSION_BYTES} bytes.")
    return Pack(
        manifest=manifest,
        documents=documents,
        skill_files=skill_files,
        references=references,
    )


class _TextOnly(dict):
    """The pack's files, refusing a binary one wherever text is expected."""

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if isinstance(value, (bytes, bytearray)):
            raise PackError(f"{key} is not a UTF-8 text file.")
        return value


def _json_doc(pack: Pack, key: str, default):
    text = pack.documents.get(key)
    if not text:
        return default
    try:
        return json.loads(text)
    except ValueError as exc:
        raise PackError(f"{pack.manifest.get(key)} is not valid JSON: {exc}") from exc


def _catalogue(manifest: dict) -> dict:
    cat = dict(manifest.get("catalogue") or {})
    # The analyst-facing descriptors live at the manifest's top level in older
    # packs; the catalogue is where the database keeps them.
    for key in ("aka", "fits_when", "gives_you"):
        if key in manifest and key not in cat:
            cat[key] = manifest[key]
    return cat


def _ui_schema(pack: Pack) -> dict:
    ui = _json_doc(pack, "ui_schema", {}) or {}
    if not ui.get("sections") and pack.manifest.get("sections"):
        ui = {
            **ui,
            "sections": [
                {"id": s.get("id"), "title": s.get("title", ""), "order": i}
                for i, s in enumerate(pack.manifest["sections"])
                if isinstance(s, dict) and s.get("id")
            ],
        }
    return ui


def _version_fields(pack: Pack) -> dict:
    m = pack.manifest
    spec_format = str(m.get("spec_format") or "yaml").strip().lower()
    if spec_format not in SpecFormat.values:
        raise PackError(f"spec_format must be one of {', '.join(SpecFormat.values)}.")
    return {
        "catalogue": _catalogue(m),
        "spec_format": spec_format,
        "spec_root": str(m.get("spec_root") or ""),
        "spec_dialect": str(m.get("spec_dialect") or "").strip()[:32],
        "json_schema": _json_doc(pack, "json_schema", {}),
        "ui_schema": _ui_schema(pack),
        "interview_md": pack.documents.get("interview", ""),
        "schema_md": pack.documents.get("schema", ""),
        "starter_yaml": pack.documents.get("starter", ""),
        "example_yaml": pack.documents.get("example", ""),
        "rules": _json_doc(pack, "rules", []),
        "build_skill_name": str(m.get("build_skill_name") or ""),
        "workspace_engine_paths": _engine_paths(m),
        "builder_html": pack.documents.get("builder_html", ""),
        "builder_adapter": pack.documents.get("builder_adapter", ""),
        "references": pack.references,
        "drafting_md": pack.documents.get("drafting", ""),
    }


def _engine_paths(manifest: dict) -> list:
    from .workspace import WorkspaceError, normalise_engine_paths

    try:
        return normalise_engine_paths(
            (manifest.get("workspace") or {}).get("engine_paths") or []
        )
    except WorkspaceError as exc:
        raise PackError(exc.message) from exc


# ---------------------------------------------------------------- linting --


def frontmatter_name(markdown: str) -> str:
    """The ``name:`` from a SKILL.md's YAML frontmatter, or ""."""
    lines = (markdown or "").lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        if key.strip() == "name":
            return value.strip().strip("'\"")
    return ""


def _issue(level, file, message, pointer=""):
    return {"level": level, "file": file, "pointer": pointer, "message": message}


def _resolve_schema_pointer(schema: dict, pointer: str) -> bool:
    """Whether ``pointer`` (into the *document*) names something the schema describes."""
    node = schema
    defs = schema.get("$defs", {})
    for raw in [p for p in pointer.split("/")[1:]]:
        part = raw.replace("~1", "/").replace("~0", "~")
        for _ in range(10):
            ref = node.get("$ref") if isinstance(node, dict) else None
            if not ref:
                break
            node = defs.get(ref.split("/")[-1], {})
        if not isinstance(node, dict):
            return False
        if node.get("type") == "array" or "items" in node:
            node = node.get("items", {})
            if part.lstrip("-").isdigit() or part.startswith("@") or part == "*":
                continue
        props = node.get("properties", {})
        if part in props:
            node = props[part]
        elif isinstance(node.get("additionalProperties"), dict):
            node = node["additionalProperties"]
        else:
            return False
    return True


def lint(version: AppTemplateVersion, files=None) -> list:
    """Everything wrong with a version, as [{level, file, pointer, message}]."""
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError

    issues = []
    template = version.template
    cat = version.catalogue or {}

    if not template.name:
        issues.append(_issue("error", MANIFEST, "The template needs a name."))
    if not template.one_liner:
        issues.append(
            _issue("error", MANIFEST, "The template needs a one-line description.")
        )
    if not cat.get("description"):
        issues.append(_issue("warning", MANIFEST, "The catalogue has no description."))
    if not re.match(SEMVER_RE, version.version or ""):
        issues.append(
            _issue("error", MANIFEST, f"{version.version!r} is not a semver version.")
        )

    from .generic import GENERIC_DIALECT, GENERIC_SLUG, borrows, effective, fallback_for

    generic = fallback_for(version)
    if borrows(version) and generic is None:
        issues.append(
            _issue(
                "warning",
                MANIFEST,
                f"The generic template {GENERIC_SLUG!r} is not published; "
                "whatever this template leaves out has nothing to fall back to.",
            )
        )
    schema = effective(version, "json_schema", generic) or {}
    validator = None
    if version.spec_format == SpecFormat.YAML and not schema:
        issues.append(
            _issue("error", "schema.json", "A YAML template needs a JSON Schema.")
        )
    if schema:
        try:
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
        except SchemaError as exc:
            issues.append(
                _issue("error", "schema.json", f"Invalid JSON Schema: {exc.message}")
            )

    if not effective(version, "interview_md", generic):
        issues.append(_issue("error", "INTERVIEW.md", "The template has no interview."))

    if version.spec_format == SpecFormat.YAML:
        from .spec import yamlio

        for name, text in (
            ("starter.yaml", version.starter_yaml),
            ("example.yaml", version.example_yaml),
        ):
            if not text:
                level = "error" if name == "starter.yaml" else "warning"
                issues.append(_issue(level, name, f"{name} is missing."))
                continue
            try:
                doc = yamlio.load(text)
            except yamlio.SpecYAMLError as exc:
                issues.append(_issue("error", name, f"Not valid YAML: {exc}"))
                continue
            if validator is not None:
                for err in sorted(
                    validator.iter_errors(doc), key=lambda e: list(e.absolute_path)
                ):
                    pointer = "/" + "/".join(str(p) for p in err.absolute_path)
                    issues.append(_issue("error", name, err.message, pointer))

    if validator is not None:
        from .spec import yamlio

        seen_refs = set()
        for ref in version.references or []:
            name = f"references/{ref.get('id')}.yaml"
            if ref.get("id") in seen_refs:
                issues.append(_issue("error", name, "Two references share this id."))
            seen_refs.add(ref.get("id"))
            try:
                doc = yamlio.load(ref.get("yaml") or "")
            except yamlio.SpecYAMLError as exc:
                issues.append(_issue("error", name, f"Not valid YAML: {exc}"))
                continue
            for err in validator.iter_errors(doc):
                pointer = "/" + "/".join(str(p) for p in err.absolute_path)
                issues.append(_issue("error", name, err.message, pointer))

    for section in version.sections:
        pointer = section.get("pointer")
        if pointer and schema and not _resolve_schema_pointer(schema, pointer):
            issues.append(
                _issue(
                    "error",
                    "ui.json",
                    f"Section {section['id']!r} points at {pointer}, "
                    "which the schema does not describe.",
                    pointer,
                )
            )

    if not isinstance(version.rules, list):
        issues.append(_issue("error", "rules.json", "rules.json must be a list."))
    else:
        seen = set()
        for i, rule in enumerate(version.rules):
            where = f"/{i}"
            if not isinstance(rule, dict):
                issues.append(
                    _issue("error", "rules.json", "Each rule must be an object.", where)
                )
                continue
            if not rule.get("id") or rule["id"] in seen:
                issues.append(
                    _issue("error", "rules.json", "Each rule needs a unique id.", where)
                )
            seen.add(rule.get("id"))
            if rule.get("kind") not in RULE_KINDS:
                issues.append(
                    _issue(
                        "error",
                        "rules.json",
                        f"Unknown rule kind {rule.get('kind')!r}.",
                        where,
                    )
                )
            if rule.get("level", "error") not in RULE_LEVELS:
                issues.append(
                    _issue(
                        "error",
                        "rules.json",
                        f"Unknown level {rule.get('level')!r}.",
                        where,
                    )
                )
            if not rule.get("message"):
                issues.append(
                    _issue("error", "rules.json", "Each rule needs a message.", where)
                )

    if version.has_workspace:
        from .workspace import WorkspaceError, check_zango_version, inspect_zip

        try:
            check_zango_version(inspect_zip(bytes(version.workspace_zip)))
        except WorkspaceError as exc:
            issues.append(_issue("error", "workspace.zip", exc.message))

    if version.builder_html and not version.builder_adapter:
        issues.append(
            _issue(
                "error",
                "builder",
                "The builder page needs an adapter (builder.adapter in template.json).",
            )
        )
    if version.builder_html and "</body>" not in version.builder_html.lower():
        issues.append(
            _issue(
                "error",
                "builder",
                "The builder page has no </body> to inject the adapter before.",
            )
        )

    if files is None:
        files = {row.path: row.value for row in version.files.all()}
    if version.build_skill_name:
        skill_md = files.get("SKILL.md")
        if skill_md is None:
            issues.append(
                _issue("error", "skill/SKILL.md", "The build skill has no SKILL.md.")
            )
        else:
            name = frontmatter_name(skill_md)
            if name != version.build_skill_name:
                issues.append(
                    _issue(
                        "error",
                        "skill/SKILL.md",
                        f"SKILL.md frontmatter name is {name!r}; the manifest says "
                        f"{version.build_skill_name!r}.",
                    )
                )
    elif files:
        issues.append(
            _issue(
                "error",
                MANIFEST,
                "Skill files are present but build_skill_name is not set.",
            )
        )
    elif version.spec_dialect != GENERIC_DIALECT:
        # (A template on the generic spec is built with Agent Mode's App Studio skill.)
        issues.append(_issue("warning", MANIFEST, "The template has no build skill."))
    return issues


# -------------------------------------------------------------- publishing --


@transaction.atomic
def publish(
    version: AppTemplateVersion, changelog: str = "", by: str = ""
) -> AppTemplateVersion:
    """Freeze a draft and make it the template's current version."""
    version = (
        AppTemplateVersion.objects.select_for_update()
        .select_related("template")
        .get(pk=version.pk)
    )
    if not version.is_draft:
        raise PackError(f"{version} is already {version.status}.")
    issues = lint(version)
    if any(i["level"] == "error" for i in issues):
        raise LintFailed(issues)

    version.content_sha = content_sha(version)
    version.status = VersionStatus.PUBLISHED
    version.changelog = changelog or version.changelog
    version.published_at = timezone.now()
    version.published_by = by or ""
    version.save()

    template = version.template
    template.current_version = version
    template.status = TemplateStatus.PUBLISHED
    template.save(update_fields=["current_version", "status", "modified_at"])
    transaction.on_commit(bump_revision)
    return version


# ---------------------------------------------------------------- importing --


def _pack_sha(
    template: AppTemplate, version: str, fields: dict, skill_files: dict
) -> str:
    probe = AppTemplateVersion(template=template, version=version, **fields)
    return content_sha(
        probe,
        [(p, sha256_file(t)) for p, t in skill_files.items()],
        include_workspace=False,
    )


@transaction.atomic
def import_pack(
    source, *, publish_now: bool = False, version: str | None = None, by: str = ""
):
    """Import a pack; returns (AppTemplateVersion, created).

    * content identical to an existing version → that version, created=False;
    * the template has a draft → the draft is overwritten with the pack;
    * otherwise → a new draft, published straight away if ``publish_now``.
    """
    pack = read_pack(source)
    m = pack.manifest
    slug = str(m.get("slug") or "").strip().lower()
    if not re.match(SLUG_RE, slug):
        raise PackError(f"Invalid template slug {slug!r}.")
    version_str = str(version or m.get("version") or "").strip()
    if not re.match(SEMVER_RE, version_str):
        raise PackError(f"The pack needs a semver version (got {version_str!r}).")

    template, _ = AppTemplate.objects.select_for_update().get_or_create(
        slug=slug, defaults={"name": str(m.get("name") or slug)}
    )
    for attr, key in (
        ("name", "name"),
        ("category", "category"),
        ("icon", "icon"),
        ("one_liner", "one_liner"),
        ("is_beta", "is_beta"),
    ):
        if key in m:
            setattr(template, attr, m[key])
    template.save()

    fields = _version_fields(pack)
    sha = _pack_sha(template, version_str, fields, pack.skill_files)
    # The same pack, whether or not a workspace was attached to it since.
    for existing in template.versions.exclude(status=VersionStatus.DRAFT):
        if content_sha(existing, include_workspace=False) == sha:
            return existing, False

    clash = (
        template.versions.filter(version=version_str)
        .exclude(status=VersionStatus.DRAFT)
        .first()
    )
    if clash:
        raise PackError(
            f"{slug} {version_str} is already {clash.status} with different content; "
            "bump the version in template.json."
        )

    draft = template.versions.filter(status=VersionStatus.DRAFT).first()
    if draft is None:
        draft = AppTemplateVersion(template=template)
    draft.version = version_str
    for key, value in fields.items():
        setattr(draft, key, value)
    # Packs don't carry the workspace (it may be private code, attached per
    # platform); a newer pack keeps the one the current version has.
    source = template.current_version
    if not draft.has_workspace and source is not None and source.has_workspace:
        draft.workspace_zip = source.workspace_zip
        draft.workspace_sha = source.workspace_sha
        draft.workspace_size = source.workspace_size
    # Likewise the builder page: packs ship the adapter, the page is attached.
    if not draft.builder_html and source is not None and source.builder_html:
        draft.builder_html = source.builder_html
    draft.save()

    draft.files.all().delete()
    for path, value in pack.skill_files.items():
        AppTemplateFile.for_value(draft, path, value).save()

    if publish_now:
        draft = publish(
            draft,
            changelog=str(m.get("changelog") or f"Imported {version_str}."),
            by=by,
        )
    return draft, True


# ---------------------------------------------------------------- exporting --


def export_pack(version: AppTemplateVersion) -> bytes:
    """A zip of ``version`` in pack layout, importable with import_pack()."""
    template = version.template
    cat = dict(version.catalogue or {})
    manifest = {
        "slug": template.slug,
        "name": template.name,
        "version": version.version,
        "category": template.category,
        "icon": template.icon,
        "is_beta": template.is_beta,
        "one_liner": template.one_liner,
        "aka": cat.pop("aka", []),
        "fits_when": cat.pop("fits_when", []),
        "gives_you": cat.pop("gives_you", []),
        "catalogue": cat,
        "spec_format": version.spec_format,
        "spec_root": version.spec_root,
        "spec_dialect": version.spec_dialect,
        "build_skill_name": version.build_skill_name,
        "sections": [
            {"id": s["id"], "title": s.get("title", "")} for s in version.sections
        ],
        "interview": "INTERVIEW.md",
        "schema": "SCHEMA.md",
        "starter": "starter.yaml",
        "example": "example.yaml",
        "json_schema": "schema.json",
        "ui_schema": "ui.json",
        "rules": "rules.json",
        "skill_dir": "skill",
        "changelog": version.changelog,
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        prefix = f"{template.slug}/"
        zf.writestr(
            prefix + MANIFEST, json.dumps(manifest, indent=2, ensure_ascii=False)
        )
        for name, text in (
            ("INTERVIEW.md", version.interview_md),
            ("SCHEMA.md", version.schema_md),
            ("starter.yaml", version.starter_yaml),
            ("example.yaml", version.example_yaml),
            ("schema.json", json.dumps(version.json_schema or {}, indent=2)),
            ("ui.json", json.dumps(version.ui_schema or {}, indent=2)),
            ("rules.json", json.dumps(version.rules or [], indent=2)),
        ):
            zf.writestr(prefix + name, text or "")
        for row in version.files.all():
            zf.writestr(f"{prefix}skill/{row.path}", row.value)
    return buf.getvalue()
