"""A template's workspace: the app skeleton a new app starts from, as a zip.

The zip is in Zango's app-template layout — ``settings.json`` (app_name,
modules, routes), ``manifest.json`` (packages), the app's code, frontend and
migrations — optionally wrapped in one top-level folder. It lives in the
database on the template version, so an app created from a template gets the
exact engine that version was published with.

Parts of the workspace belong to the template rather than the app — for PSP,
``backend/template/`` is the engine and ``backend/custom/`` is the app's own
configuration. Those *engine paths* are restored from the zip before every
build, so an edit to the engine can never survive into a build; everything
else is the app's to change.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import posixpath
import shutil
import uuid
import zipfile

from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import ValidationError


MAX_ZIP_BYTES = 64 * 1024 * 1024
MAX_UNZIPPED_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 5000
MARKER = ".zango-template.json"

# What zip_directory() leaves out of a template repo by default: VCS data,
# installed dependencies and caches, and Zango packages (installed from
# manifest.json when the app is created, never copied).
DEFAULT_EXCLUDES = (
    ".git/",
    "node_modules/",
    "__pycache__/",
    ".DS_Store",
    "packages/",
    ".venv/",
)


class WorkspaceError(ValidationError):
    """A workspace zip that cannot be used, with a message fit for a user."""


@dataclass
class ZipInfo:
    prefix: str  # single top-level folder to strip ("" if none)
    entries: int
    unzipped_bytes: int
    app_name: str
    zango_version: str
    run_migrations: bool
    files: list = field(default_factory=list)  # relative paths, prefix stripped


def _safe_rel(name: str) -> str:
    raw = name.replace("\\", "/")
    if raw.startswith("/") or "\x00" in raw:
        raise WorkspaceError(f"Unsafe path in the zip: {name!r}")
    norm = posixpath.normpath(raw)
    if norm.startswith("../") or norm == ".." or "/../" in f"/{norm}/":
        raise WorkspaceError(f"Unsafe path in the zip: {name!r}")
    return norm


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    return (info.external_attr >> 16) & 0o170000 == 0o120000


def inspect_zip(data: bytes) -> ZipInfo:
    """Check a workspace zip is safe and usable; describe it."""
    if not data:
        raise WorkspaceError("The workspace zip is empty.")
    if len(data) > MAX_ZIP_BYTES:
        raise WorkspaceError(
            f"The workspace zip is larger than {MAX_ZIP_BYTES // (1024 * 1024)} MB."
        )
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise WorkspaceError("That is not a zip file.") from exc
    with zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > MAX_ENTRIES:
            raise WorkspaceError(f"The workspace has more than {MAX_ENTRIES} files.")
        total = 0
        names = []
        for info in infos:
            if _is_symlink(info):
                raise WorkspaceError(f"Symbolic links are not allowed: {info.filename}")
            names.append(_safe_rel(info.filename))
            total += info.file_size
        if total > MAX_UNZIPPED_BYTES:
            raise WorkspaceError(
                f"The workspace unzips to more than {MAX_UNZIPPED_BYTES // (1024 * 1024)} MB."
            )
        names = [n for n in names if not n.startswith("__MACOSX/")]
        tops = {n.split("/", 1)[0] for n in names}
        prefix = ""
        if len(tops) == 1 and all("/" in n for n in names):
            prefix = tops.pop() + "/"
        files = [n[len(prefix) :] for n in names]
        if "settings.json" not in files:
            raise WorkspaceError("The workspace has no settings.json at its root.")
        if "manifest.json" not in files:
            raise WorkspaceError("The workspace has no manifest.json at its root.")
        try:
            settings = json.loads(zf.read(prefix + "settings.json"))
        except ValueError as exc:
            raise WorkspaceError("settings.json is not valid JSON.") from exc
    return ZipInfo(
        prefix=prefix,
        entries=len(files),
        unzipped_bytes=total,
        app_name=str(settings.get("app_name") or ""),
        zango_version=str(settings.get("zango_version") or ""),
        run_migrations="migrations/generate.txt" in files,
        files=files,
    )


def check_zango_version(info: ZipInfo) -> None:
    """Refuse a workspace built for another Zango than the one running."""
    if not info.zango_version:
        return
    from packaging.specifiers import InvalidSpecifier, SpecifierSet
    from packaging.version import Version

    import zango

    try:
        # Platforms run pre-releases (1.2.0b9); a plain `>=` must still admit them.
        if not SpecifierSet(info.zango_version).contains(
            Version(zango.__version__), prereleases=True
        ):
            raise WorkspaceError(
                f"The workspace needs Zango {info.zango_version}; this platform runs {zango.__version__}."
            )
    except InvalidSpecifier as exc:
        raise WorkspaceError(
            f"settings.json has an invalid zango_version: {info.zango_version!r}"
        ) from exc


def attach_workspace(version, data: bytes, engine_paths=None) -> ZipInfo:
    """Put a workspace zip on a draft version."""
    from ..models import ImmutableVersionError

    if not version.is_draft:
        raise ImmutableVersionError(
            f"{version} is {version.status}; attach the workspace to a new draft."
        )
    info = inspect_zip(data)
    version.workspace_zip = bytes(data)
    version.workspace_sha = hashlib.sha256(data).hexdigest()
    version.workspace_size = len(data)
    if engine_paths is not None:
        version.workspace_engine_paths = normalise_engine_paths(engine_paths)
    version.save()
    return info


def normalise_engine_paths(paths) -> list:
    out = []
    for p in paths or ():
        p = str(p).strip().replace("\\", "/").lstrip("/")
        if not p or p.startswith("..") or "/../" in f"/{p}":
            raise WorkspaceError(f"Invalid engine path: {p!r}")
        out.append(p)
    return out


def _is_engine(rel: str, engine_paths) -> bool:
    for p in engine_paths:
        if p.endswith("/"):
            if rel.startswith(p):
                return True
        elif rel == p or rel.startswith(p + "/"):
            return True
    return False


def _zip(version):
    return zipfile.ZipFile(io.BytesIO(bytes(version.workspace_zip)))


def extract_workspace(version, dest: Path, app_name: str) -> ZipInfo:
    """Unzip ``version``'s workspace into ``dest`` for an app called ``app_name``."""
    if not version.has_workspace:
        raise WorkspaceError(f"{version} has no workspace.")
    info = inspect_zip(bytes(version.workspace_zip))
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    with _zip(version) as zf:
        for member in zf.infolist():
            if member.is_dir() or member.filename.startswith("__MACOSX/"):
                continue
            rel = _safe_rel(member.filename)[len(info.prefix) :]
            target = (dest / rel).resolve()
            if not str(target).startswith(str(root) + os.sep):
                raise WorkspaceError(f"Unsafe path in the zip: {member.filename!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    set_app_name(dest, app_name)
    write_marker(dest, version)
    return info


def set_app_name(workspace: Path, app_name: str) -> None:
    """Point the workspace's settings.json at this app."""
    path = Path(workspace) / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    settings["app_name"] = app_name
    path.write_text(json.dumps(settings, indent=4) + "\n", encoding="utf-8")


def write_marker(workspace: Path, version) -> None:
    marker = {
        "template": version.template.slug,
        "version": version.version,
        "version_uuid": str(version.object_uuid),
        "workspace_sha": version.workspace_sha,
        "engine_paths": list(version.workspace_engine_paths or []),
    }
    (Path(workspace) / MARKER).write_text(
        json.dumps(marker, indent=2) + "\n", encoding="utf-8"
    )


def engine_drift(version, workspace: Path) -> list:
    """Engine files in ``workspace`` that differ from, or are missing against, the zip."""
    engine_paths = list(version.workspace_engine_paths or [])
    if not version.has_workspace or not engine_paths:
        return []
    info = inspect_zip(bytes(version.workspace_zip))
    drift = []
    with _zip(version) as zf:
        for member in zf.infolist():
            if member.is_dir() or member.filename.startswith("__MACOSX/"):
                continue
            rel = _safe_rel(member.filename)[len(info.prefix) :]
            if not _is_engine(rel, engine_paths):
                continue
            path = Path(workspace) / rel
            if not path.is_file():
                drift.append((rel, "missing"))
            elif path.read_bytes() != zf.read(member):
                drift.append((rel, "changed"))
    return drift


def restore_engine(version, workspace: Path) -> list:
    """Put drifted engine files back from the zip; return what was restored."""
    drift = engine_drift(version, workspace)
    if not drift:
        return []
    info = inspect_zip(bytes(version.workspace_zip))
    wanted = {rel for rel, _ in drift}
    with _zip(version) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            rel = _safe_rel(member.filename)[len(info.prefix) :]
            if rel in wanted:
                target = Path(workspace) / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))
    return drift


def zip_directory(source: Path, excludes=DEFAULT_EXCLUDES) -> bytes:
    """A workspace zip from a template checkout, leaving out ``excludes``."""
    source = Path(source)
    if not (source / "settings.json").is_file():
        raise WorkspaceError(
            f"{source} has no settings.json; is it a Zango app template?"
        )

    def excluded(rel: str) -> bool:
        for pattern in excludes:
            if pattern.endswith("/"):
                if rel.startswith(pattern) or f"/{pattern}" in f"/{rel}":
                    return True
            elif rel == pattern or rel.endswith("/" + pattern):
                return True
        return False

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(source).as_posix()
            if excluded(rel):
                continue
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return buf.getvalue()


def new_draft_from(version, new_version: str):
    """A draft copying ``version`` (content, skill files, workspace) as ``new_version``."""
    from ..models import AppTemplateFile, AppTemplateVersion

    draft = AppTemplateVersion(template=version.template, version=new_version)
    for name in version.CONTENT_FIELDS:
        if name != "version":
            setattr(draft, name, getattr(version, name))
    draft.workspace_zip = version.workspace_zip
    draft.workspace_size = version.workspace_size
    draft.save()
    for row in version.files.all():
        AppTemplateFile(
            version=draft, path=row.path, content=row.content, encoding=row.encoding
        ).save()
    return draft


def bump_patch(version: str) -> str:
    base, _, _ = version.partition("-")
    major, minor, patch = (int(x) for x in base.split("."))
    return f"{major}.{minor}.{patch + 1}"


def temp_dir() -> Path:
    """A scratch directory every worker can reach (workspaces live under BASE_DIR too)."""
    from django.conf import settings

    path = Path(settings.BASE_DIR) / ".agent_mode" / "tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path
