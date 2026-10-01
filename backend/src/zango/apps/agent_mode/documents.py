"""Documents a user hands the analyst: SOPs, RFPs, protocols, process maps.

They are checked and their text extracted on upload, stored with the
requirement, and written to a per-requirement directory the analyst can read
(``docs_dir``). PDFs are kept as-is as well — Claude Code reads them natively,
tables and all — and every document gets a plain-text extract the analyst can
grep and quote from, listed in an ``INDEX.md``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import zipfile

from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree


MAX_FILES = 10
MAX_TOTAL_BYTES = 25 * 1024 * 1024
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_UNZIPPED_BYTES = 100 * 1024 * 1024  # DOCX/XLSX are zips: bomb guard
MAX_TEXT_CHARS = 400_000
MAX_SHEET_ROWS = 500

KINDS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class DocumentError(ValueError):
    """A document that cannot be accepted; the message is shown to the user."""


@dataclass
class Extracted:
    name: str
    content_type: str
    size: int
    sha256: str
    text: str
    pages: int = 0
    sheets: list = field(default_factory=list)
    data: bytes = field(default=b"", repr=False)

    def model_fields(self) -> dict:
        """Keyword arguments for a document row (scaffold or requirement)."""
        return {
            "name": self.name,
            "content_type": self.content_type,
            "size": self.size,
            "sha256": self.sha256,
            "data": self.data,
            "extracted_text": self.text,
            "pages": self.pages,
            "sheets": self.sheets,
        }


def _safe_name(name: str) -> str:
    base = os.path.basename(str(name or "").replace("\\", "/")).strip() or "document"
    base = re.sub(r"[^A-Za-z0-9._ -]+", "_", base)[:120]
    return base.lstrip(".") or "document"


def _check_zip(data: bytes, required: str) -> zipfile.ZipFile:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise DocumentError("The file is damaged or not what its name says.") from exc
    if sum(i.file_size for i in zf.infolist()) > MAX_UNZIPPED_BYTES:
        raise DocumentError("The file expands to more than 100 MB.")
    if required not in zf.namelist():
        raise DocumentError("The file is damaged or not what its name says.")
    return zf


def _pdf(data: bytes) -> tuple[str, int]:
    if not data.startswith(b"%PDF"):
        raise DocumentError("The file is not a PDF.")
    import fitz  # PyMuPDF

    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            parts = [
                f"--- page {i} ---\n{page.get_text()}" for i, page in enumerate(doc, 1)
            ]
            return "\n".join(parts), doc.page_count
    except Exception as exc:  # noqa: BLE001
        raise DocumentError("The PDF could not be read.") from exc


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _docx(data: bytes) -> str:
    zf = _check_zip(data, "word/document.xml")
    root = ElementTree.fromstring(zf.read("word/document.xml"))
    body = root.find(f"{_W}body")
    lines = []
    for block in body if body is not None else []:
        if block.tag == f"{_W}p":
            text = "".join(t.text or "" for t in block.iter(f"{_W}t")).strip()
            if text:
                lines.append(text)
        elif block.tag == f"{_W}tbl":
            for row in block.iter(f"{_W}tr"):
                cells = [
                    " ".join(t.text or "" for t in cell.iter(f"{_W}t")).strip()
                    for cell in row.iter(f"{_W}tc")
                ]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
    return "\n".join(lines)


def _xlsx(data: bytes) -> tuple[str, list]:
    _check_zip(data, "xl/workbook.xml")
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        raise DocumentError("The spreadsheet could not be read.") from exc
    parts, sheets = [], []
    for ws in wb.worksheets:
        sheets.append(ws.title)
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= MAX_SHEET_ROWS:
                rows.append(f"| … {ws.max_row - MAX_SHEET_ROWS} more rows |")
                break
            if any(v not in (None, "") for v in row):
                rows.append(
                    "| " + " | ".join("" if v is None else str(v) for v in row) + " |"
                )
        parts.append(f"--- sheet {ws.title} ---\n" + "\n".join(rows))
    wb.close()
    return "\n\n".join(parts), sheets


def _text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise DocumentError("The text file's encoding could not be read.")


def extract(name: str, data: bytes) -> Extracted:
    """Check one upload and extract its text."""
    name = _safe_name(name)
    ext = os.path.splitext(name)[1].lower()
    if ext not in KINDS:
        raise DocumentError(
            f"{name}: only PDF, Word (.docx), Excel (.xlsx), CSV, text and Markdown files can be read."
        )
    if not data:
        raise DocumentError(f"{name} is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise DocumentError(f"{name} is larger than 25 MB.")
    pages, sheets = 0, []
    try:
        if ext == ".pdf":
            text, pages = _pdf(data)
        elif ext == ".docx":
            text = _docx(data)
        elif ext == ".xlsx":
            text, sheets = _xlsx(data)
        elif ext == ".csv":
            rows = list(csv.reader(io.StringIO(_text(data))))
            text = "\n".join(
                "| " + " | ".join(r) + " |" for r in rows[: MAX_SHEET_ROWS * 4]
            )
        else:
            text = _text(data)
    except DocumentError as exc:
        raise DocumentError(f"{name}: {exc}") from exc
    except ElementTree.ParseError as exc:
        raise DocumentError(f"{name}: the file is damaged.") from exc
    return Extracted(
        name=name,
        content_type=KINDS[ext],
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        text=text[:MAX_TEXT_CHARS],
        pages=pages,
        sheets=sheets,
        data=data,
    )


def extract_all(files) -> list[Extracted]:
    """``files`` is [(name, bytes)]; checks the batch limits too."""
    files = list(files)
    if len(files) > MAX_FILES:
        raise DocumentError(f"Upload at most {MAX_FILES} documents.")
    if sum(len(data) for _, data in files) > MAX_TOTAL_BYTES:
        raise DocumentError("The documents add up to more than 25 MB.")
    return [extract(name, data) for name, data in files]


def read_uploads(request) -> list[Extracted]:
    """Extract the ``documents`` files of a multipart request (none → [])."""
    uploads = request.FILES.getlist("documents") if hasattr(request, "FILES") else []
    return extract_all((f.name, f.read()) for f in uploads)


# ---------------------------------------------------------------------------
# On disk, for the analyst
# ---------------------------------------------------------------------------


def docs_dir(tenant_name: str, requirement_uuid) -> Path:
    from django.conf import settings

    return (
        Path(settings.BASE_DIR)
        / ".agent_mode"
        / "requirements"
        / tenant_name
        / str(requirement_uuid)
        / "docs"
    )


def write_docs_dir(tenant_name: str, requirement) -> Path | None:
    """Write the requirement's documents (originals + text extracts + INDEX.md)."""
    rows = list(requirement.documents.all().order_by("pk"))
    if not rows:
        return None
    root = docs_dir(tenant_name, requirement.object_uuid)
    root.mkdir(parents=True, exist_ok=True)
    index = ["# Documents the user provided", ""]
    for i, row in enumerate(rows, 1):
        stem = f"{i:02d}-{row.name}"
        if row.content_type == KINDS[".pdf"]:
            (root / stem).write_bytes(bytes(row.data))
        text_name = f"{stem}.txt"
        (root / text_name).write_text(row.extracted_text or "", encoding="utf-8")
        detail = (
            f"{row.pages} pages"
            if row.pages
            else (f"sheets: {', '.join(row.sheets)}" if row.sheets else "")
        )
        original = (
            f"`{stem}` (read it directly) and "
            if row.content_type == KINDS[".pdf"]
            else ""
        )
        index.append(
            f"- **{row.name}** — {row.content_type.split('/')[-1]}, {row.size // 1024} KB{', ' + detail if detail else ''}: "
            f"{original}text in `{text_name}`"
        )
    (root / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return root


# A brief this long is a written requirement, not a one-liner: draft from it.
DETAILED_BRIEF_CHARS = 600


def wants_draft(prompt: str, n_documents: int) -> bool:
    """One-pass drafting when the user gave documents or a detailed brief."""
    return n_documents > 0 or len((prompt or "").strip()) >= DETAILED_BRIEF_CHARS


def document_list(rows) -> list:
    return [
        {
            "id": r.pk,
            "name": r.name,
            "size": r.size,
            "content_type": r.content_type,
            "pages": r.pages,
        }
        for r in rows
    ]
