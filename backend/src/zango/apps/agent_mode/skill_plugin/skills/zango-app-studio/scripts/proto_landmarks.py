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

Labels are normalised for matching (``norm``); counts at the end ("Open 7") are dropped. Text that
is record data rather than UI copy (IDs, amounts, dates, long sentences) is skipped by ``is_copy``.
"""

import re
from html.parser import HTMLParser

KINDS = ("menu", "title", "heading", "column", "tab", "button", "label")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP = {"script", "style", "svg", "template", "noscript"}
CLICKABLE = {"a", "button"}


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
        if tag in SKIP or self.skip:
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
    return out
