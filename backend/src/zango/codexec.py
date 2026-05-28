"""User-facing helpers for Code Execution snippets.

Usage from a snippet:

    from zango import codexec

    text = codexec.read_text("seed.csv")
    codexec.write_json("result.json", {"ok": True})

All operations are scoped to the *current execution* — set by the executor
just before `exec()`-ing the user code. Calling these helpers outside that
context raises `CodexecOutsideRunError`.

The bytes live in Django's `default_storage` (S3 / local / whatever the
project configures). The file mapping rows live on `CodeExecFile`. This
module is the only API user code should touch for file I/O.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, List, Optional, Union

from django.core.files.base import ContentFile


__all__ = [
    "read",
    "read_text",
    "read_json",
    "open",
    "local_path",
    "list_inputs",
    "write",
    "write_text",
    "write_json",
    "open_output",
    "list_outputs",
    "FileRef",
    "bind_execution",
    "CodexecOutsideRunError",
    "CodexecFileNotFound",
]


# ---------------------------------------------------------------------------
# Per-run context (thread-local — celery workers run one task per thread)
# ---------------------------------------------------------------------------

_local = threading.local()


class CodexecOutsideRunError(RuntimeError):
    """Raised when helpers are called outside a Code Execution run context."""


class CodexecFileNotFound(FileNotFoundError):
    """Raised when an input file name does not exist for the current run."""


def _current_execution_id() -> str:
    eid = getattr(_local, "execution_id", None)
    if not eid:
        raise CodexecOutsideRunError(
            "codexec helpers can only be used inside a Code Execution run."
        )
    return eid


@contextmanager
def bind_execution(execution_id: str) -> Iterator[None]:
    """Set the active execution id for the duration of a block.

    Used by the celery executor; not intended to be called from user code.
    """
    prev = getattr(_local, "execution_id", None)
    _local.execution_id = str(execution_id)
    try:
        yield
    finally:
        _local.execution_id = prev


# ---------------------------------------------------------------------------
# Name sanitization — never trust what user code writes
# ---------------------------------------------------------------------------


def _sanitize_name(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    if "\x00" in name:
        raise ValueError("name must not contain NUL bytes")
    base = os.path.basename(name.replace("\\", "/"))
    base = base.lstrip(".")
    if not base or base in (".", ".."):
        raise ValueError("invalid file name")
    return base[:255]


def _get_input(name: str):
    from zango.apps.code_execution.models import CodeExecFile, FileKind  # lazy

    name = _sanitize_name(name)
    try:
        return CodeExecFile.objects.get(
            execution_id=_current_execution_id(),
            kind=FileKind.INPUT,
            name=name,
        )
    except CodeExecFile.DoesNotExist:
        raise CodexecFileNotFound(
            f"No input file named {name!r} attached to this run."
        ) from None


# ---------------------------------------------------------------------------
# FileRef — what the user code sees
# ---------------------------------------------------------------------------


class FileRef:
    """Thin wrapper around a `CodeExecFile` row exposed to user code."""

    __slots__ = ("_obj",)

    def __init__(self, obj):
        self._obj = obj

    @property
    def name(self) -> str:
        return self._obj.name

    @property
    def size(self) -> int:
        return self._obj.size_bytes

    @property
    def content_type(self) -> str:
        return self._obj.content_type

    @property
    def sha256(self) -> str:
        return self._obj.sha256

    @property
    def kind(self) -> str:
        return self._obj.kind

    def read(self) -> bytes:
        with self._obj.file.open("rb") as f:
            return f.read()

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.read().decode(encoding)

    def open(self, mode: str = "rb"):
        return self._obj.file.open(mode)

    def __repr__(self) -> str:
        return f"<FileRef name={self.name!r} kind={self.kind} size={self.size}>"


# ---------------------------------------------------------------------------
# Read API
# ---------------------------------------------------------------------------


def read(name: str) -> bytes:
    """Return the raw bytes of an input file."""
    obj = _get_input(name)
    with obj.file.open("rb") as f:
        return f.read()


def read_text(name: str, encoding: str = "utf-8") -> str:
    """Return the decoded text of an input file."""
    return read(name).decode(encoding)


def read_json(name: str) -> Any:
    """Return the parsed JSON contents of an input file."""
    return json.loads(read_text(name))


def open(name: str, mode: str = "rb"):  # noqa: A001 - shadow builtin intentional
    """Open an input file for reading. Pass mode='r' for text."""
    if "w" in mode or "a" in mode or "+" in mode or "x" in mode:
        raise ValueError(
            "codexec.open is read-only; use codexec.open_output(name) to write."
        )
    return _get_input(name).file.open(mode)


def local_path(name: str) -> Path:
    """Materialize an input file to a local tmp path and return it.

    Useful when a library needs a real filesystem path (pandas, openpyxl, PIL).
    """
    obj = _get_input(name)
    cache_dir = Path(f"/tmp/codexec/{_current_execution_id()}/in")
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / obj.name
    needs_refresh = not target.exists() or target.stat().st_size != obj.size_bytes
    if needs_refresh:
        with obj.file.open("rb") as src, target.open("wb") as dst:
            chunker = src.chunks() if hasattr(src, "chunks") else None
            if chunker is not None:
                for chunk in chunker:
                    dst.write(chunk)
            else:
                while True:
                    chunk = src.read(65536)
                    if not chunk:
                        break
                    dst.write(chunk)
    return target


def list_inputs() -> List[FileRef]:
    """Return every input file attached to the current run."""
    from zango.apps.code_execution.models import CodeExecFile, FileKind

    qs = CodeExecFile.objects.filter(
        execution_id=_current_execution_id(), kind=FileKind.INPUT
    ).order_by("name")
    return [FileRef(o) for o in qs]


# ---------------------------------------------------------------------------
# Write API
# ---------------------------------------------------------------------------


def _store_output(name: str, data: Union[bytes, bytearray, str]) -> FileRef:
    from zango.apps.code_execution.models import CodeExecFile, FileKind

    name = _sanitize_name(name)
    exec_id = _current_execution_id()

    if isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, (bytes, bytearray)):
        payload = bytes(data)
    else:
        raise TypeError("data must be bytes, bytearray, or str")

    sha = hashlib.sha256(payload).hexdigest()
    size = len(payload)

    obj, created = CodeExecFile.objects.get_or_create(
        execution_id=exec_id,
        kind=FileKind.OUTPUT,
        name=name,
        defaults={"sha256": sha, "size_bytes": size},
    )

    if not created and obj.file:
        try:
            obj.file.delete(save=False)
        except Exception:
            pass
        obj.sha256 = sha
        obj.size_bytes = size

    obj.file.save(name, ContentFile(payload), save=True)
    return FileRef(obj)


def write(
    name: str,
    data: Union[bytes, bytearray, str],
    content_type: Optional[str] = None,
) -> FileRef:
    """Write an output file. Returns a `FileRef` to the persisted row."""
    ref = _store_output(name, data)
    if content_type:
        ref._obj.content_type = content_type
        ref._obj.save(update_fields=["content_type"])
    return ref


def write_text(name: str, text: str, encoding: str = "utf-8") -> FileRef:
    """Write a text output file (default UTF-8)."""
    return write(name, text.encode(encoding), content_type="text/plain")


def write_json(name: str, obj: Any, indent: int = 2) -> FileRef:
    """Write a JSON output file."""
    payload = json.dumps(obj, indent=indent, default=str, ensure_ascii=False).encode(
        "utf-8"
    )
    return write(name, payload, content_type="application/json")


class _OutputWriter:
    """Buffered writer returned by `open_output()`.

    Buffers in memory and uploads on close. Fine for files up to the per-output
    cap (~25 MB); large streaming outputs aren't a v1 goal.
    """

    def __init__(self, name: str, mode: str):
        if "r" in mode:
            raise ValueError("open_output is for writing; use codexec.open for reads.")
        self.name = name
        self.mode = mode
        self._buf = bytearray()
        self._closed = False
        # Capture execution id at creation so closing outside the run still works.
        self._exec_id = _current_execution_id()

    def write(self, data: Union[bytes, bytearray, str]) -> int:
        if self._closed:
            raise ValueError("write on closed writer")
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._buf.extend(data)
        return len(data)

    def writelines(self, lines) -> None:
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        with bind_execution(self._exec_id):
            _store_output(self.name, bytes(self._buf))
        self._buf = bytearray()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def open_output(name: str, mode: str = "wb"):
    """Open a streaming output writer. Row is finalized on close."""
    return _OutputWriter(name, mode)


def list_outputs() -> List[FileRef]:
    """Return every output file written so far by the current run."""
    from zango.apps.code_execution.models import CodeExecFile, FileKind

    qs = CodeExecFile.objects.filter(
        execution_id=_current_execution_id(), kind=FileKind.OUTPUT
    ).order_by("name")
    return [FileRef(o) for o in qs]
