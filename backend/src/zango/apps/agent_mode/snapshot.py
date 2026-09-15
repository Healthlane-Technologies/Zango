"""Pre-run workspace snapshot, change detection and rollback.

Agent Mode writes directly into the live workspace with no diff gate, so the
tarball taken here is the only undo. It is a safety net, not a checkpoint
system: over a size ceiling the snapshot is skipped with a loud warning and
the run proceeds, because the alternative — refusing to run on a large
workspace — is worse.

The manifest doubles as change detection: diffing before/after is how the
post-run pipeline decides which steps to run. Deliberately git-independent,
since a workspace may or may not be a repo.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
import tempfile
import time

from dataclasses import dataclass, field


SNAPSHOT_EXCLUDES = frozenset(
    {
        "__pycache__",
        ".git",
        "node_modules",
        ".venv",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".DS_Store",
    }
)

# Content-hash only below this; larger files fall back to (size, mtime).
# Keeps the pre-run cost well under a second on a normal workspace.
HASH_MAX_BYTES = 2 * 1024 * 1024
MAX_LISTED_CHANGES = 500


@dataclass
class SnapshotInfo:
    path: str = ""
    size_bytes: int = 0
    manifest: dict = field(default_factory=dict)
    skipped_reason: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.path) and not self.skipped_reason


@dataclass
class FileChanges:
    added: list = field(default_factory=list)
    modified: list = field(default_factory=list)
    deleted: list = field(default_factory=list)
    truncated: bool = False

    @property
    def any(self) -> bool:
        return bool(self.added or self.modified or self.deleted)

    def all_paths(self) -> list:
        return sorted({*self.added, *self.modified, *self.deleted})

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "modified": self.modified,
            "deleted": self.deleted,
            "truncated": self.truncated,
        }


def _iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SNAPSHOT_EXCLUDES]
        for name in filenames:
            if name in SNAPSHOT_EXCLUDES:
                continue
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            yield full, os.path.relpath(full, root)


def _digest(path: str) -> str:
    h = hashlib.sha1()  # noqa: S324 - change detection, not security
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def workspace_manifest(root: str) -> dict:
    """relpath -> [size, mtime_ns, short_sha1]. Never raises."""
    manifest = {}
    for full, rel in _iter_files(root):
        try:
            st = os.stat(full)
            digest = _digest(full) if st.st_size <= HASH_MAX_BYTES else ""
            manifest[rel] = [st.st_size, st.st_mtime_ns, digest]
        except OSError:
            continue
    return manifest


def directory_size(root: str) -> int:
    total = 0
    for full, _ in _iter_files(root):
        try:
            total += os.path.getsize(full)
        except OSError:
            continue
    return total


def create_snapshot(root: str, dest_dir: str, max_bytes: int) -> SnapshotInfo:
    """Tar the workspace. Returns a SnapshotInfo; never raises."""
    manifest = workspace_manifest(root)
    try:
        size = directory_size(root)
        if size > max_bytes:
            return SnapshotInfo(
                manifest=manifest,
                skipped_reason=(
                    f"workspace is {size / 1e6:.0f} MB, over the "
                    f"{max_bytes / 1e6:.0f} MB snapshot ceiling"
                ),
            )
        os.makedirs(dest_dir, exist_ok=True)
        path = os.path.join(dest_dir, "pre.tar.gz")
        with tarfile.open(path, "w:gz") as tar:
            for full, rel in _iter_files(root):
                try:
                    tar.add(full, arcname=rel)
                except OSError:
                    continue
        return SnapshotInfo(
            path=path, size_bytes=os.path.getsize(path), manifest=manifest
        )
    except Exception as exc:  # noqa: BLE001 - a snapshot failure must not block
        return SnapshotInfo(
            manifest=manifest, skipped_reason=f"{type(exc).__name__}: {exc}"
        )


def diff_manifest(before: dict, after: dict) -> FileChanges:
    before = before or {}
    after = after or {}
    added = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    modified = sorted(
        rel for rel in (set(before) & set(after)) if before[rel] != after[rel]
    )
    truncated = any(len(x) > MAX_LISTED_CHANGES for x in (added, modified, deleted))
    return FileChanges(
        added=added[:MAX_LISTED_CHANGES],
        modified=modified[:MAX_LISTED_CHANGES],
        deleted=deleted[:MAX_LISTED_CHANGES],
        truncated=truncated,
    )


def _is_within(base: str, target: str) -> bool:
    base = os.path.realpath(base)
    target = os.path.realpath(target)
    return target == base or os.path.commonpath([base, target]) == base


def restore_snapshot(tar_path: str, root: str) -> dict:
    """Restore the workspace from a snapshot.

    Extracts to a temporary directory first and validates every member stays
    inside it, so a tampered archive cannot write outside the workspace. Only
    once extraction succeeds is the live tree swapped, and the displaced tree
    is kept alongside rather than deleted.
    """
    if not tar_path or not os.path.isfile(tar_path):
        raise FileNotFoundError(f"snapshot not found: {tar_path}")

    staging = tempfile.mkdtemp(prefix="agent-mode-restore-")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                target = os.path.join(staging, member.name)
                if not _is_within(staging, target):
                    raise ValueError(f"unsafe path in archive: {member.name}")
                if member.issym() or member.islnk():
                    raise ValueError(f"links are not allowed: {member.name}")
            tar.extractall(staging)  # noqa: S202 - members validated above

        displaced = f"{root.rstrip(os.sep)}.replaced-{int(time.time())}"
        if os.path.isdir(root):
            os.rename(root, displaced)
        else:
            displaced = ""
        shutil.move(staging, root)
        staging = ""
        return {"restored_to": root, "previous_tree": displaced}
    finally:
        if staging and os.path.isdir(staging):
            shutil.rmtree(staging, ignore_errors=True)


def prune_snapshots(runs_dir: str, keep: int = 5) -> int:
    """Keep the newest `keep` run directories under runs_dir."""
    removed = 0
    try:
        entries = [
            os.path.join(runs_dir, d)
            for d in os.listdir(runs_dir)
            if os.path.isdir(os.path.join(runs_dir, d))
        ]
    except OSError:
        return 0
    entries.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    for stale in entries[keep:]:
        shutil.rmtree(stale, ignore_errors=True)
        removed += 1
    return removed
