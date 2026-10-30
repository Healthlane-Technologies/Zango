"""What an approved prototype screen shows, as labels the spec must cover (open mode).

Standard library only: spec_check imports it beside itself, and the platform loads it by path for
the analyst's coverage check before spec_mark_ready (agent_mode/prototype_coverage.py).

``landmarks(dom_html)`` reads one ``dom.<role>.html`` (the prototype's rendered markup, captured by
the probe worker) and returns its labels by kind:

- ``menu``: the items of the page's ``<nav>``, in order, as ``(group, label)``; ``group`` is the last
  small heading above the item, or None.
- ``title``: the h1 (on a record screen it is the record's name, not copy).
- ``heading``: h2-h4 text outside the menu.
- ``column``: table header cells.
- ``tab``: ``role="tab"`` elements, or elements whose class list has ``tab``.
- ``button``: buttons and ``role="button"`` elements outside the menu.
- ``label``: ``<dt>`` and ``<label>`` text (field labels in summaries and forms).
- ``counted``: buttons and tabs drawn with a count ("Open 7" → "Open"): filter chips that show one.
- ``subtitle``: the text right under the page's h1 (``subtitle(dom)``), for the build's parity check.
- ``cells``: per table, the first data row's cells that are more than one plain value, as
  ``{"column", "lines", "icon", "mono"}``: ``lines`` the cell's text blocks in order (a title and a
  muted "SP-2026-0061 · Congress exhibit" under it), ``icon`` "icon" for an icon before the text or
  "initials" for an avatar of initials, ``mono`` the second line set in a monospace class.

Labels are normalised for matching (``norm``); counts at the end ("Open 7") are dropped. Text that
is record data rather than UI copy (IDs, amounts, dates, long sentences) is skipped by ``is_copy``, and
an element marked ``data-zas-chrome`` (the runtime's pager, a record count) with all it holds.
"""

import re
from html.parser import HTMLParser

KINDS = ("menu", "title", "heading", "column", "tab", "button", "label", "counted")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP = {"script", "style", "svg", "template", "noscript"}
CLICKABLE = {"a", "button"}
# Marks what the preview's runtime draws on every page of its kind (a pager, a record count), not
# the spec: such an element and everything in it is left out.
CHROME = "data-zas-chrome"


def norm(text) -> str:
    """Lower case, '&' as 'and', punctuation as spaces, trailing counts dropped."""
    t = str(text or "").lower().replace("&", " and ")
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"(\s\d+)+$", "", t)
    return t


_DATA = re.compile(
    r"^[\W_]*$"                                   # nothing but punctuation
    r"|\b[A-Z]{1,6}-\d{2,}"                       # IDs like SP-2026-0061
    r"|[$€£₹]\s?\d|\d[\d,.]*\s?(k|m|%)\b"         # amounts, percentages
    r"|\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"       # dates
    r"|^\d[\d\s,.:/-]*$",                         # bare numbers
    re.I,
)


def is_copy(text: str) -> bool:
    """UI copy, not record data: short, no IDs, amounts, dates or bare numbers."""
    t = " ".join(str(text or "").split())
    return bool(t) and len(t) <= 48 and len(t.split()) <= 6 and not _DATA.search(t)


class _Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # [tag, attrs, kind or None, text parts]
        self.skip = 0
        self.nav = 0
        self.group = None
        self.out = {k: [] for k in KINDS}

    def _kind(self, tag, a):
        cls = (a.get("class") or "").split()
        role = a.get("role") or ""
        if role == "tab" or "tab" in cls:
            return "tab"
        if self.nav:
            if tag in CLICKABLE or role in ("link", "menuitem") or "nav-item" in cls:
                return "menu"
            if re.fullmatch(r"h[1-6]", tag) or any(c in cls for c in ("nav-label", "group", "nav-group", "section")):
                return "group"
            return None
        if tag == "h1":
            return "title"
        if re.fullmatch(r"h[2-4]", tag):
            return "heading"
        if tag == "th":
            return "column"
        if tag == "button" or role == "button":
            return "button"
        if tag in ("dt", "label"):
            return "label"
        return None

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        if tag in SKIP or self.skip or CHROME in a:
            self.skip += 1
            self.stack.append([tag, a, None, []])
            return
        if tag == "nav":
            self.nav += 1
            self.group = None
        inside = any(f[2] for f in self.stack)  # the outermost labelled element owns the text
        self.stack.append([tag, a, None if inside else self._kind(tag, a), []])

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, a, kind, parts = self.stack.pop()
            if self.skip:
                self.skip -= 1
            elif kind:
                self._emit(kind, " ".join("".join(parts).split()), a)
            elif parts and self.stack:
                self.stack[-1][3].extend([" "] + parts + [" "])  # an element is a word break ("Home 4")
            if t == "nav" and self.nav:
                self.nav -= 1
            if t == tag:
                break

    def handle_data(self, data):
        # text in a labelled element's children reaches it when they close (handle_endtag)
        if self.stack and not self.skip:
            self.stack[-1][3].append(data)

    def _emit(self, kind, text, a):
        if kind in ("button", "tab") and re.search(r"\s\d+$", text):
            self.out["counted"].append(re.sub(r"(\s\d+)+$", "", text).strip())  # "Open 7": a chip with a count
        text = re.sub(r"(\s\d+)+$", "", text).strip()
        if not text:
            return
        if kind == "group":
            self.group = text
        elif kind == "menu":
            self.out["menu"].append((self.group, text))
        elif is_copy(text):
            self.out[kind].append(text)

    def close(self):
        super().close()
        while self.stack:
            self.handle_endtag(self.stack[-1][0])


BLOCK = {"div", "p", "small", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6"}


class _Cells(HTMLParser):
    """The first data row of each table, cell by cell (see ``cells`` in the module doc)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # [tag, attrs, block id or None]
        self.skip = 0
        self.tables = []     # {"heads": [], "rows": 0, "cells": []}
        self.th = None       # header text parts
        self.td = None       # {"blocks": {id: [parts]}, "order": [ids], "icon": bool, "mono": set}
        self.n = 0

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == "img" and self.td is not None and not self.td["order"]:
                self.td["icon"] = True
            return
        a = dict(attrs)
        T = self.tables[-1] if self.tables else None
        if tag == "svg" and self.td is not None and not self.td["order"]:
            self.td["icon"] = True
        if tag in SKIP or self.skip:
            self.skip += 1
            self.stack.append([tag, a, None])
            return
        if tag == "table":
            self.tables.append({"heads": [], "rows": 0, "cells": []})
        elif T is not None and tag == "th":
            self.th = []
        elif T is not None and tag == "td":
            T["in_row"] = True
            if T["rows"] == 0:
                self.td = {"blocks": {}, "order": [], "icon": False, "mono": set()}
        self.n += 1
        bid = self.n if tag in BLOCK else None
        if bid and self.td is not None and ("mono" in (a.get("class") or "").split()
                                             or "mono" in (a.get("style") or "")):
            self.td["mono"].add(bid)
        self.stack.append([tag, a, bid])

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, a, bid = self.stack.pop()
            if self.skip:
                self.skip -= 1
            elif t == "th" and self.th is not None and self.tables:
                self.tables[-1]["heads"].append(" ".join("".join(self.th).split()))
                self.th = None
            elif t == "td" and self.td is not None and self.tables:
                td, self.td = self.td, None
                lines = [" ".join("".join(td["blocks"][b]).split()) for b in td["order"]]
                order = [b for b, x in zip(td["order"], lines) if x]
                lines = [x for x in lines if x]
                icon = "icon" if td["icon"] and lines else None
                if len(lines) > 1 and re.fullmatch(r"[A-Z]{1,3}", lines[0]):
                    icon, lines, order = "initials", lines[1:], order[1:]  # an avatar ("NO")
                self.tables[-1]["cells"].append(
                    {"lines": lines, "icon": icon, "mono": len(order) > 1 and order[1] in td["mono"]})
            elif t == "tr" and self.tables and self.tables[-1].pop("in_row", False):
                self.tables[-1]["rows"] += 1  # a data row ended: only the first one is read
            if t == tag:
                break

    def handle_data(self, data):
        if self.skip:
            return
        if self.th is not None:
            self.th.append(data)
        elif self.td is not None and data.strip():
            bid = next((b for _, _, b in reversed(self.stack) if b), None)
            if bid not in self.td["blocks"]:
                self.td["blocks"][bid] = []
                self.td["order"].append(bid)
            self.td["blocks"][bid].append(data)


def cells(dom_html: str) -> list:
    """Cells of each table's first data row that show more than one plain value."""
    r = _Cells()
    r.feed(dom_html or "")
    out = []
    for T in r.tables:
        for i, c in enumerate(T["cells"]):
            if len(c["lines"]) > 1 or c["icon"]:
                head = T["heads"][i] if i < len(T["heads"]) else ""
                out.append({"column": head, "index": i, **c})
    return out


def subtitle(dom_html: str):
    """The first paragraph after the page's h1, as text, or None."""
    m = re.search(r"<h1\b[^>]*>.*?</h1>(.*)", dom_html or "", re.S | re.I)
    if not m:
        return None
    p = re.search(r"<(p|div)\b([^>]*)>((?:(?!<(?:p|div|h\d|table|button)\b).)*?)</\1>", m.group(1)[:4000], re.S | re.I)
    if p and CHROME in p.group(2):
        return None
    text = " ".join(re.sub(r"<[^>]+>", " ", p.group(3)).split()) if p else ""
    return text or None


def landmarks(dom_html: str) -> dict:
    """Labels by kind (see the module doc), each kind de-duplicated in page order."""
    r = _Reader()
    r.feed(dom_html or "")
    r.close()
    out = {}
    for k, items in r.out.items():
        seen, keep = set(), []
        for it in items:
            key = (it[0], norm(it[1])) if k == "menu" else norm(it)
            if key not in seen:
                seen.add(key)
                keep.append(it)
        out[k] = keep
    out["cells"] = cells(dom_html)
    sub = subtitle(dom_html)
    out["subtitle"] = [sub] if sub else []
    return out


CONTENT = ("title", "heading", "column", "tab", "button", "label")
_WORD = re.compile(r"[a-z]{3,}")


def _words(text):
    return set(_WORD.findall(norm(text)))


# a greeting that follows the clock: captured in the afternoon, the app may be shot in the morning
_GREETING = re.compile(r"\bgood (?:morning|afternoon|evening)\b")


def _clockless(n: str) -> str:
    return _GREETING.sub("good day", n)


def content_gaps(approved_dom: str, built_dom: str, built_text: str, skip=(), record=False,
                 ignore_words=(), drawn_cells=(), subtitle_words=None) -> list:
    """What the approved screen shows that the built one doesn't, as problems for the fix round.

    A label counts as shown when its words appear anywhere in the built page's text (the kit draws a
    heading or a chip with other tags than the prototype). ``skip``: normalised labels to leave out
    (the screen's not_built, the persona's shell chrome). ``record``: the h1 and the line under it
    are the record's data. ``ignore_words``: the demo personas' names and titles ("Good morning,
    Elena" is matched as "good morning"). ``drawn_cells``: normalised column labels the spec already
    draws with a second line or icon (an empty line there is test data, not a gap).
    ``subtitle_words``: the subtitle words every persona's version shares (the rest is per persona).
    Also compared: filter chips that show a count, the subtitle under the h1, and each table's
    first-row cells (a second line, an icon or initials)."""
    want, got = landmarks(approved_dom), landmarks(built_dom)
    # "Open48": a chip's count drawn right after its label is a separate word
    text = " " + _clockless(norm(re.sub(r"(?<=[A-Za-z])(?=\d)", " ", built_text or ""))) + " "
    skip = {norm(x) for x in skip}
    ignore = {w for x in ignore_words for w in norm(x).split()}
    probs, seen = [], set()
    for kind in CONTENT:
        if kind == "title" and record:
            continue
        for label in want.get(kind, []):
            n = norm(label)
            if not n or n in skip:
                continue
            if ignore:  # "Good morning, Elena" → "good morning"; a persona chip leaves nothing
                n = " ".join(w for w in n.split() if w not in ignore)
                if not _WORD.search(n):
                    continue
            if n in skip or n in seen:
                continue
            seen.add(n)
            if f" {_clockless(n)} " not in text:
                probs.append(f"missing {kind} {label!r}")
    counted = {norm(x) for x in got.get("counted", [])}
    for label in want.get("counted", []):
        n = norm(label)
        if n not in skip and f" {n} " in text and n not in counted:
            probs.append(f"filter chip {label!r} shows no count (the approved screen shows one)")
    sub = None if record else subtitle(approved_dom)
    if sub and norm(sub) not in skip:
        mine = subtitle(built_dom) or ""
        a = (set(subtitle_words) if subtitle_words is not None else _words(sub)) - ignore
        b = _words(mine) - ignore
        if a and len(a & b) / len(a) < 0.5:
            probs.append(f"subtitle under the title: approved {sub!r}, built {mine or 'none'!r}")
    if "data-zas=\"empty\"" not in (built_dom or ""):
        built_cells = {c["index"]: c for c in cells(built_dom)}
        drawn = {norm(x) for x in drawn_cells}
        for c in cells(approved_dom):
            if norm(c["column"]) in drawn or (c["index"] == 0 and "#0" in drawn_cells):
                continue
            b = built_cells.get(c["index"]) or {"lines": [], "icon": None}
            need = []
            if len(c["lines"]) > 1 and len(b["lines"]) < 2:
                need.append(f"a second line ({c['lines'][1]!r})")
            if c["icon"] and not b["icon"]:
                need.append("initials" if c["icon"] == "initials" else "an icon")
            if need:
                probs.append(f"column {c['column']!r} cells lack " + " and ".join(need))
    return probs
