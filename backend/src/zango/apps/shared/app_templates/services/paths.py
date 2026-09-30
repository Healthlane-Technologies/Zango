"""Path and hashing helpers shared by the models and the pack services."""

from __future__ import annotations

import hashlib
import json
import posixpath

from django.core.exceptions import ValidationError


def normalise_pack_path(path: str) -> str:
    """A safe, relative, forward-slash path inside a pack, or ValidationError.

    Pack files end up on disk and are read by an agent, so a path that climbs
    out of the pack (``..``), is absolute, or hides in a dotfile is refused
    rather than cleaned up.
    """
    raw = str(path or "").strip().replace("\\", "/")
    if not raw or raw.startswith("/") or "\x00" in raw:
        raise ValidationError(f"Invalid file path: {path!r}")
    norm = posixpath.normpath(raw)
    parts = norm.split("/")
    if norm in (".", "") or any(p in ("", ".", "..") for p in parts):
        raise ValidationError(f"Invalid file path: {path!r}")
    if any(p.startswith(".") for p in parts):
        raise ValidationError(f"Hidden files are not allowed: {path!r}")
    if len(norm) > 255:
        raise ValidationError(f"File path is too long: {path!r}")
    return norm


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def content_sha(version, files=None, *, include_workspace: bool = True) -> str:
    """Hash of everything that makes up a version: its content and its files.

    ``files`` is an iterable of (path, sha256); defaults to the version's rows.
    ``include_workspace=False`` leaves out the attached workspace zip, to tell
    whether two versions came from the same *pack*.
    """
    payload = {f: getattr(version, f) for f in version.CONTENT_FIELDS}
    if not include_workspace:
        # Attached per platform, not part of the pack.
        payload.pop("workspace_sha", None)
        payload.pop("builder_html", None)
    if files is None:
        files = version.files.values_list("path", "sha256")
    payload["files"] = sorted([list(pair) for pair in files])
    payload["slug"] = version.template.slug
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
