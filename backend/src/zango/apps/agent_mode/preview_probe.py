"""The analyst's eyes on its custom screens.

The declarative parts of an App Studio spec (lists, forms, workflows, 360 pages, views) are drawn
by the preview the same way every time; validation is enough for them. A custom page, 360 tab or
panel is drawn by a ``preview`` sketch the analyst writes in JavaScript, and until now only the
user ever saw what it drew. This module runs those sketches in a headless copy of the very page
the console shows, and reports back in three steps, cheapest first:

1. run the sketch for every role that can open the screen: errors, empty output, unknown
   entities and fields (automatic after an edit that touches a custom screen);
2. a text summary of what it drew, recorded from its ``ctx.ui`` calls and ``ctx.rows`` reads;
3. on request (``preview_look``), a screenshot of that one component.

The browser runs in a child process (``preview_probe_worker.py``) started on the first check of a
turn and killed at the end of it, or as soon as a request runs too long: a sketch with an endless
loop cannot hang the turn, and nothing is left running in the Celery worker.

Threading: the probe is called from spec tool handlers (see spec_tools.py), off the event loop
and under the workbench lock. It never touches the ORM; the page is composed beforehand, on the
tenant-bound thread, by ``probe_for``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading

from pathlib import Path


logger = logging.getLogger("zango.agent_mode")

WORKER = Path(__file__).with_name("preview_probe_worker.py")
START_TIMEOUT = 45
REQUEST_TIMEOUT = 30
LOOK_TIMEOUT = 45
CAPTURE_TIMEOUT = 120  # one screen, every role, a few screenshots


class ProbeError(Exception):
    """The probe could not answer (no Playwright, the browser died, a sketch hung)."""


# ---------------------------------------------------------------------------
# Custom screens in a spec (mirrors probeSketches() in app-studio.html)
# ---------------------------------------------------------------------------


def _ref(item, index: int) -> str:
    code = item.get("code") if isinstance(item, dict) else None
    return f"@{code}" if code else str(index)


def custom_screens(doc) -> dict:
    """{spec path: node} for every custom page, 360 tab and 360 panel of a plain spec."""
    out = {}
    if not isinstance(doc, dict):
        return out
    for i, page in enumerate(doc.get("pages") or []):
        # Dashboards are declared block by block: the preview draws them, nothing to sketch.
        if (
            isinstance(page, dict)
            and page.get("code")
            and page.get("type") not in ("crud", "detail", "dashboard")
        ):
            out[f"/pages/@{page['code']}"] = page
    for dv in doc.get("detail_views") or []:
        if not isinstance(dv, dict) or not dv.get("code"):
            continue
        base = f"/detail_views/@{dv['code']}"
        for ti, tab in enumerate(dv.get("tabs") or []):
            if not isinstance(tab, dict):
                continue
            tpath = f"{base}/tabs/{_ref(tab, ti)}"
            if tab.get("type") == "custom":
                out[tpath] = tab
            if tab.get("type") in ("summary", "fields"):
                for si, sec in enumerate(tab.get("sections") or []):
                    if isinstance(sec, dict) and sec.get("type") == "custom":
                        out[f"{tpath}/sections/{si}"] = sec
        for si, sec in enumerate(dv.get("sidebar") or []):
            if isinstance(sec, dict) and sec.get("type") == "custom":
                out[f"{base}/sidebar/{si}"] = sec
    return out


def node_hash(node) -> str:
    return hashlib.sha1(
        json.dumps(node, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def screen_hashes(doc) -> dict:
    return {path: node_hash(node) for path, node in custom_screens(doc).items()}


def is_sketched(node) -> bool:
    return isinstance(node, dict) and bool(str(node.get("preview") or "").strip())


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _reads(result: dict) -> str:
    parts = []
    for r in result.get("reads") or []:
        via = f" via {r['via']}" if r.get("via") else ""
        parts.append(f"{r['entity']}{via} ({r['rows']} rows)")
    return ", ".join(parts)


def format_result(r: dict, *, verbose: bool = True) -> str:
    """One sketch run, as the analyst reads it."""
    head = f"{r.get('path')}"
    if r.get("role"):
        head += f" as {r['role']}"
    if r.get("record"):
        rec = r["record"]
        head += f" on {rec.get('entity')} #{rec.get('id')} ({rec.get('label')})"
    if not r.get("ok"):
        return f"✗ {head}: {r.get('error')}"
    # A warning is not a pass: the screen draws, but not what it is for.
    lines = [f"{'⚠' if r.get('warnings') or r.get('empty_parts') else '✓'} {head}"]
    if verbose:
        if r.get("reads"):
            lines.append(f"  reads: {_reads(r)}")
        for d in r.get("draws") or []:
            lines.append(f"  drew: {d}")
        if not r.get("draws"):
            lines.append(
                f"  drew (hand-written markup, {r.get('text_chars', 0)} chars): {r.get('excerpt', '')}"
            )
            lines.append(
                "  note: the build copies ctx.ui calls block for block; hand-written markup it can only "
                "match from a screenshot. Use ctx.ui where a block fits."
            )
    if r.get("hidden_on_record"):
        lines.append(
            "  note: show_when hides it on every record this role sees; it was run on the first one anyway"
        )
    if r.get("empty_parts"):
        lines.append(
            f"  warning: {r['empty_parts']} part(s) drew nothing for this role (empty panels look broken)"
        )
    for w in r.get("warnings") or []:
        lines.append(f"  warning: {w}")
    return "\n".join(lines)


def problems(results: list) -> list:
    """The runs that would show the user an error, a blank or a placeholder."""
    return [r for r in results if not r.get("ok")]


def format_check(results: list, *, verbose: bool = True, header: str = "") -> str:
    if not results:
        return header + "No custom pages, tabs or panels in the spec."
    bad = problems(results)
    head = header or (
        f"Ran {len(results)} custom-screen sketch run(s): "
        + (f"{len(bad)} problem(s)." if bad else "all drew without errors.")
    )
    body = "\n".join(format_result(r, verbose=verbose) for r in results)
    return f"{head}\n{body}"


# ---------------------------------------------------------------------------
# The child process
# ---------------------------------------------------------------------------


_PLAYWRIGHT: dict = {}


def playwright_available(python: str | None = None) -> bool:
    python = python or sys.executable
    if _PLAYWRIGHT.get(python):
        return True
    try:
        proc = subprocess.run(
            [python, "-c", "import playwright.sync_api"],
            capture_output=True,
            timeout=30,
        )
        _PLAYWRIGHT[python] = proc.returncode == 0
        return _PLAYWRIGHT[python]
    except (OSError, subprocess.SubprocessError):
        return False


class PreviewProbe:
    """One headless preview page for one analyst turn; started lazily, closed with the turn."""

    def __init__(self, html: str, python: str | None = None):
        self.html = html
        self.python = python or sys.executable
        self._proc: subprocess.Popen | None = None
        self._html_file: str | None = None
        self._seq = 0
        self._dead: str | None = None
        self._hung_yaml: str | None = None
        self._restarts = 0
        self._lock = threading.Lock()
        self.looks = 0

    # -- process -------------------------------------------------------------

    def _start(self):
        if self._dead:
            raise ProbeError(self._dead)
        fd, path = tempfile.mkstemp(prefix="zas-preview-", suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(self.html)
        self._html_file = path
        try:
            self._proc = subprocess.Popen(
                [self.python, str(WORKER), path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                bufsize=1,
                start_new_session=True,  # its own process group: killing it takes Chromium too
            )
        except OSError as exc:
            self._fail(f"Could not start the preview runner: {exc}")
        hello = self._read(START_TIMEOUT, expect=0)
        if not hello.get("ok"):
            self._fail(hello.get("error") or "The preview runner did not start.")

    def _fail(self, reason: str, *, permanent: bool = True):
        if permanent:
            self._dead = reason
        self.close()
        raise ProbeError(reason)

    def _read(self, timeout: float, expect: int) -> dict:
        box: dict = {}

        def reader():
            try:
                while True:
                    line = self._proc.stdout.readline()
                    if not line:
                        box["eof"] = True
                        return
                    try:
                        msg = json.loads(line)
                    except ValueError:
                        continue  # stray output from a library
                    if msg.get("id") == expect:
                        box["msg"] = msg
                        return
            except Exception as exc:  # noqa: BLE001
                box["exc"] = exc

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            self._fail(
                f"The preview did not answer within {int(timeout)}s — a sketch probably loops "
                "forever (a `while` whose condition never changes, a recursion). The check was "
                "stopped; fix the sketch and the next edit checks it again.",
                permanent=False,
            )
        if "msg" in box:
            return box["msg"]
        if "exc" in box:
            self._fail(f"The preview runner failed: {box['exc']}")
        self._fail(
            "The preview runner stopped. Is Playwright's Chromium installed "
            f"(`{self.python} -m playwright install chromium`)?"
        )
        return {}  # unreachable

    def _request(self, payload: dict, timeout: float) -> dict:
        with self._lock:
            if (
                payload.get("yaml") is not None
                and payload.get("yaml") == self._hung_yaml
            ):
                raise ProbeError(
                    "This version of the spec hung the preview last time; change the sketch first."
                )
            if self._proc is None or self._proc.poll() is not None:
                if self._proc is not None or self._seq:
                    self._restarts += 1
                    if self._restarts > 3:
                        self._dead = "The preview runner stopped too often this turn; checks are off until the next message."
                self._proc = None
                self._start()
            self._seq += 1
            payload = {**payload, "id": self._seq}
            try:
                self._proc.stdin.write(json.dumps(payload) + "\n")
                self._proc.stdin.flush()
            except (OSError, ValueError) as exc:
                self._fail(f"The preview runner went away: {exc}")
            try:
                msg = self._read(timeout, expect=self._seq)
            except ProbeError:
                if self._dead is None:
                    self._hung_yaml = payload.get("yaml")
                raise
            if not msg.get("ok"):
                raise ProbeError(msg.get("error") or "The preview could not run that.")
            return msg.get("result") or {}

    def close(self):
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                try:
                    proc.kill()
                except OSError:
                    pass
            try:
                proc.wait(timeout=5)
            except subprocess.SubprocessError:
                pass
        if self._html_file:
            try:
                os.unlink(self._html_file)
            except OSError:
                pass
            self._html_file = None

    # -- requests --------------------------------------------------------------

    def check(self, yaml_text: str, paths: list | None = None) -> dict:
        """{parse_error, results: [sketch run, ...]} for ``paths`` (every custom screen if None)."""
        return self._request(
            {"op": "check", "yaml": yaml_text, "paths": paths}, REQUEST_TIMEOUT
        )

    def look(
        self, yaml_text: str, path: str, role=None, record=None, width: int = 1280
    ) -> dict:
        """{show, run, png (base64 or None)} for one custom screen."""
        self.looks += 1
        return self._request(
            {
                "op": "look",
                "yaml": yaml_text,
                "path": path,
                "role": role,
                "record": record,
                "width": width,
            },
            LOOK_TIMEOUT,
        )

    def sketches(self, yaml_text: str) -> dict:
        """{parse_error, sketches: [{path, kind, title, sketched, roles, ...}]}."""
        return self._request({"op": "sketches", "yaml": yaml_text}, REQUEST_TIMEOUT)

    def capture(
        self, yaml_text: str, path: str, kit_tree_js: str, max_variants: int = 3
    ) -> dict:
        """One custom screen for the approval bundle: {variants: [{roles, record, tree, run, png}], in_page}."""
        return self._request(
            {
                "op": "capture",
                "yaml": yaml_text,
                "path": path,
                "kit_tree": kit_tree_js,
                "max_variants": max_variants,
            },
            CAPTURE_TIMEOUT,
        )


def probe_for(template) -> PreviewProbe | None:
    """A probe for ``template``'s preview page, or None when it cannot have one.

    Runs on the tenant-bound thread (it reads the template version). None when probes are
    switched off (``AGENT_MODE_PREVIEW_PROBE = False``), the template has no preview page or
    an older one without ``ZAS_PROBE``, or Playwright is not installed.
    """
    from django.conf import settings

    if not getattr(settings, "AGENT_MODE_PREVIEW_PROBE", True):
        return None
    if (
        template is None
        or not getattr(template, "is_yaml", False)
        or not template.version_uuid
    ):
        return None
    from zango.apps.shared.app_templates.models import AppTemplateVersion
    from zango.apps.shared.app_templates.services.builder import compose
    from zango.apps.shared.app_templates.services.generic import follow_current

    # An app pinned to an older generic version is previewed with the current page.
    version = follow_current(
        AppTemplateVersion.objects.filter(object_uuid=template.version_uuid).first()
    )
    if (
        version is None
        or not version.has_builder
        or "ZAS_PROBE" not in (version.builder_html or "")
    ):
        return None
    if not playwright_available():
        logger.info("agent_mode: preview checks off — Playwright is not installed")
        return None
    return PreviewProbe(compose(version))
