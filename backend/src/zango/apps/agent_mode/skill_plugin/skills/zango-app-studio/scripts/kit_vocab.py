"""The kit page's markup next to the runtime's: one vocabulary for the two renderers of a template app.

A template app's approved prototype is the kit page (packs/zango_app/builder/app-studio.html): it draws
the app with `.z-*` (shell, lists, forms) and `.d-*` (record 360) classes. The built app draws the same
pieces with the zas runtime's `.zas-*` classes (assets/frontend/zas). This module says which runtime
class draws what a kit class draws, so the approved look can be compared with the built one element by
element (zas_test/style.py, design_diff) and approved CSS can be carried over.

- CLASS_MAP: every class the kit's stylesheet defines for the app area, to its runtime class, or None
  when the runtime has no such element. tests/apps/agent_mode/test_kit_vocab.py keeps it complete in
  both directions: a kit class missing here, or a runtime class that no longer exists, fails CI.
- CONTEXT_MAP: compound selectors that map differently from their parts (a kit avatar in the user card
  is the shell's avatar, not the 360's).
- PARTS: what design_diff compares on a screen: a label, the kit selector, the runtime selector, which
  property groups, and whether the part depends on the data (a badge only shows when a row has one).
"""

import re

CLASS_MAP = {
    # shell
    "z-shell": "zas-sh",
    "z-side": "zas-sh-side",
    "z-brand": "zas-sh-brand",
    "z-logo": "zas-sh-mark",
    "z-nav": "zas-sh-nav",
    "z-ng": "zas-sh-g",
    "z-ni": "zas-sh-a",
    "z-ni-n": "zas-sh-n",
    "z-user": "zas-sh-user",
    "z-main": "zas-sh-body",
    "z-top": "zas-sh-top",
    "z-content": "zas-sh-main",
    # page, list, table
    "z-ph": "zas-ph",
    "z-lstats": "zas-lstats",
    "z-lstat": "zas-lstat",
    "z-lstat-hint": "zas-lstat-hint",
    "z-crumbs": "zas-crumbs",
    "z-card": "zas-card",
    "z-tb": "zas-tb",
    "z-tbl-w": "zas-tbl-w",
    "z-t": "zas-t",
    "z-search": "zas-search",
    "z-sel": "zas-sel",
    "z-qf": "zas-qf",
    "z-qf-n": "zas-qf-n",
    "z-cell2": "zas-cell2",
    "z-cell-ico": "zas-cell-ico",
    "z-cell-txt": "zas-cell-txt",
    "z-cell-main": "zas-cell-main",
    "z-cell-sub": "zas-cell-sub",
    "z-cpill": "zas-cpill",
    "z-cprog": "zas-cprog",
    "z-cprog-bar": "zas-cprog-bar",
    "z-cprog-t": "zas-cprog-t",
    "z-chips": "zas-chips",
    "z-chip": "zas-chip",
    "z-badge": "zas-badge",
    "z-btn": "zas-btn",
    "z-ib": "zas-ib",
    "z-kebab": "zas-kebab",
    "z-pop": "zas-pop",
    "z-pg": "zas-pg",
    "z-link": "zas-link",
    "z-vsw": "zas-vsw",
    "z-empty": "zas-empty",
    "z-state": "zas-state",
    "z-skel": "zas-skel",
    "z-nil": "zas-nil",
    "z-no": "zas-no",
    "z-yes": "zas-yes",
    "z-file": "zas-file",
    "z-av": "zas-av",
    # drawer
    "z-dw": "zas-dw",
    "z-dw-bg": "zas-dw-bg",
    "z-dw-h": "zas-dw-h",
    "z-dw-b": "zas-dw-b",
    "z-dw-acts": "zas-dw-acts",
    # record 360
    "d-head": "zas-dhead",
    "d-top": "zas-dtop",
    "d-av": "zas-av",
    "d-tt": "zas-dtt",
    "d-sub": "zas-dsub",
    "d-badges": "zas-dbadges",
    "d-acts": "zas-dacts",
    "d-facts": "zas-dfacts",
    "d-fact": "zas-dfact",
    "d-stats": "zas-stats",
    "d-stat": "zas-stat",
    "d-tabs": "zas-tabs",
    "d-tab": "zas-tab",
    "d-cnt": "zas-cnt",
    "d-body": "zas-dbody",
    "d-panel": "zas-panel",
    "d-fields": "zas-fields",
    "d-f": "zas-f",
    "d-ban": "zas-ban",
    "d-stepper": "zas-stepper",
    "d-step": "zas-step",
    "d-copy": "zas-copy",
    "d-cust": "zas-cust",
    # form controls the runtime draws with the crud package's form, not zas classes
    "z-in": None,
    "z-lock": None,
    "z-money": None,
    "z-sw": None,
    "z-pill": None,
    "z-pills": None,
    "z-comp": None,
    "z-num": None,
}

# (kit selector, runtime selector): matched before the class-by-class rewrite.
CONTEXT_MAP = (
    (".z-user .z-av", ".zas-sh-user .zas-sh-av"),
    (".z-side .z-av", ".zas-sh-side .zas-sh-av"),
    # app.shell.user: top: the kit's card carries the line under it, the runtime's wrapper does
    (".z-user.top", ".zas-sh-foot.top"),
)

# Property groups design_diff compares (computed styles).
PROPS = {
    "fill": ("background-color", "background-image"),
    "text": ("color", "font-size", "font-weight", "letter-spacing", "text-transform"),
    "box": ("border-top-width", "border-top-style", "border-top-color", "border-bottom-width",
            "border-bottom-color", "border-left-width", "border-left-color",
            "border-top-left-radius", "border-bottom-right-radius", "box-shadow"),
    "space": ("padding-top", "padding-right", "padding-bottom", "padding-left", "row-gap", "column-gap"),
    "size": ("width", "height"),
}

# id, label, kit selector, runtime selector, property groups, data-dependent
PARTS = (
    ("sidebar", "sidebar", ".z-side", ".zas-sh-side", ("fill", "box"), False),
    ("brand_mark", "brand mark", ".z-logo", ".zas-sh-mark", ("fill", "text", "box", "size"), False),
    ("nav_item", "menu item", ".z-ni:not(.on)", ".zas-sh-a:not(.on)", ("fill", "text", "box", "space"), False),
    ("nav_item_on", "active menu item", ".z-ni.on", ".zas-sh-a.on", ("fill", "text", "box"), False),
    ("nav_group", "menu group heading", ".z-ng", ".zas-sh-g", ("text",), False),
    ("user_card", "user card", ".z-user", ".zas-sh-user", ("fill", "box"), False),
    ("user_card_top", "user card above the menu", ".z-user.top", ".zas-sh-foot.top", ("box",), False),
    ("nav_count", "menu item count", ".z-ni-n", ".zas-sh-n", ("fill", "text", "box"), True),
    ("top_bar", "top bar", ".z-top", ".zas-sh-top", ("fill", "box"), False),
    ("content", "page background", ".z-content", ".zas-sh-main", ("fill",), False),
    ("page_title", "page title", ".z-ph h1", ".zas-ph h1", ("text",), False),
    ("page_sub", "page subtitle", ".z-ph p", ".zas-ph p", ("text",), False),
    ("list_stats", "list KPI row", ".z-lstats", ".zas-lstats", ("space",), False),
    ("list_stat", "list KPI tile", ".z-lstat", ".zas-lstat", ("fill", "box", "space"), False),
    ("list_stat_icon", "list KPI icon", ".z-lstat .si", ".zas-lstat .si", ("box", "size"), False),
    ("list_stat_value", "list KPI value", ".z-lstat b", ".zas-lstat b", ("text",), False),
    ("list_stat_hint", "list KPI hint", ".z-lstat-hint", ".zas-lstat-hint", ("text",), False),
    ("crumbs", "breadcrumbs", ".z-crumbs", ".zas-crumbs", ("text",), False),
    ("card", "card", ".z-card", ".zas-card", ("fill", "box"), False),
    ("toolbar", "table toolbar", ".z-tb", ".zas-tb", ("fill", "box", "space"), False),
    ("table_head", "table header cell", ".z-t th", ".zas-t th", ("fill", "text", "box", "space"), False),
    ("table_cell", "table cell", ".z-t td", ".zas-t td", ("text", "box", "space"), True),
    ("quick_filter", "quick filter", ".z-qf:not(.on)", ".zas-qf:not(.on)", ("fill", "text", "box"), True),
    ("quick_filter_on", "selected quick filter", ".z-qf.on", ".zas-qf.on", ("fill", "text", "box"), True),
    ("quick_filter_count", "quick filter count", ".z-qf-n", ".zas-qf-n", ("text",), True),
    ("cell_main", "list cell value (two-line cell)", ".z-cell-main", ".zas-cell-main", ("text",), True),
    ("cell_sub", "list cell second line", ".z-cell-sub", ".zas-cell-sub", ("text",), True),
    ("cell_icon", "list cell avatar or icon", ".z-cell-ico", ".zas-cell-ico", ("fill", "text", "box", "size"), True),
    ("cell_pill", "pill after a cell value", ".z-cpill", ".zas-cpill", ("text", "box", "space"), True),
    ("cell_progress", "status step bar", ".z-cprog-bar", ".zas-cprog-bar", ("space", "size"), True),
    ("cell_progress_on", "status step bar, done step", ".z-cprog-bar i.on", ".zas-cprog-bar i.on", ("fill", "box"), True),
    ("cell_progress_text", "status step text", ".z-cprog-t", ".zas-cprog-t", ("text",), True),
    ("row_chevron", "row chevron", ".z-t td.chev", ".zas-t td.chev", ("text", "space"), True),
    ("search", "search box", ".z-search", ".zas-search", ("fill", "box"), False),
    ("button", "button", ".z-btn:not(.pri):not(.ghost):not(.d-head *)",
     ".zas-btn:not(.pri):not(.ghost):not(.zas-dhead *)", ("fill", "text", "box"), True),
    ("button_primary", "primary button", ".z-btn.pri:not(.d-head *)", ".zas-btn.pri:not(.zas-dhead *)",
     ("fill", "text", "box"), True),
    ("badge", "status badge", ".z-badge:not(.d-head *)", ".zas-badge:not(.zas-dhead *)", ("text", "box"), True),
    ("chip", "chip", ".z-chip:not(.d-head *)", ".zas-chip:not(.zas-dhead *)", ("text", "box"), True),
    ("empty", "empty state", ".z-empty", ".zas-empty", ("fill", "text"), True),
    ("head", "record header", ".d-head", ".zas-dhead", ("fill", "box", "space"), False),
    ("head_title", "record title", ".d-head h1", ".zas-dhead h1", ("text",), False),
    ("head_sub", "record subtitle", ".d-sub", ".zas-dsub", ("text",), False),
    ("head_button", "record header button", ".d-head .z-btn:not(.pri)", ".zas-dhead .zas-btn:not(.pri)",
     ("fill", "text", "box"), True),
    ("head_button_primary", "record header primary button", ".d-head .z-btn.pri", ".zas-dhead .zas-btn.pri",
     ("fill", "text", "box"), True),
    ("head_badge", "record header badge", ".d-head .z-chip, .d-head .z-badge",
     ".zas-dhead .zas-chip, .zas-dhead .zas-badge", ("text", "box"), True),
    ("avatar", "record avatar", ".d-av", ".zas-dhead .zas-av", ("fill", "text", "box", "size"), False),
    ("stepper", "lifecycle stepper", ".d-stepper", ".zas-stepper", ("box", "space"), False),
    ("step", "lifecycle step", ".d-step:not(.done):not(.cur):not(.end)", ".zas-step:not(.done):not(.cur):not(.end)", ("text",), True),
    ("step_dot", "lifecycle step dot", ".d-step:not(.done):not(.cur):not(.end) i", ".zas-step:not(.done):not(.cur):not(.end) i",
     ("fill", "text", "box", "size"), True),
    ("step_done_dot", "lifecycle step dot, done", ".d-step.done i", ".zas-step.done i", ("fill", "text", "box"), True),
    ("step_cur", "lifecycle step, current", ".d-step.cur", ".zas-step.cur", ("text",), True),
    ("step_cur_dot", "lifecycle step dot, current", ".d-step.cur i", ".zas-step.cur i", ("fill", "text", "box"), True),
    ("step_end_dot", "lifecycle end marker", ".d-step.end i", ".zas-step.end i", ("fill", "text", "box"), True),
    ("facts", "facts row", ".d-facts", ".zas-dfacts", ("box", "space"), False),
    ("fact", "fact", ".d-fact", ".zas-dfact", ("fill", "box", "space"), False),
    ("fact_label", "fact label", ".d-fact > span", ".zas-dfact > span", ("text",), False),
    ("fact_value", "fact value", ".d-fact b", ".zas-dfact b", ("text",), False),
    ("stats", "stat row", ".d-stats", ".zas-stats", ("space",), False),
    ("stat", "stat card", ".d-stat", ".zas-stat", ("fill", "box", "space"), False),
    ("stat_icon", "stat icon", ".d-stat .si", ".zas-stat .si", ("box", "size"), False),
    ("stat_value", "stat value", ".d-stat b", ".zas-stat b", ("text",), False),
    ("tabs", "tab bar", ".d-tabs", ".zas-tabs", ("fill", "box", "space"), False),
    ("tab", "tab", ".d-tab:not(.on)", ".zas-tab:not(.on)", ("fill", "text", "box", "space"), False),
    ("tab_on", "active tab", ".d-tab.on", ".zas-tab.on", ("fill", "text", "box"), False),
    ("panel", "panel", ".d-panel", ".zas-panel", ("fill", "box"), False),
    ("panel_title", "panel title", ".d-panel > h3", ".zas-panel > h3", ("text", "box"), False),
)

CLASS = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")


def runtime_class(kit_class):
    """The runtime class for a kit class, None when it has none, or the class itself when it is not a
    kit class (state classes like `on`, `pri`, `sm` are shared)."""
    if kit_class in CLASS_MAP:
        return CLASS_MAP[kit_class]
    return kit_class


def translate_selector(selector):
    """A kit selector as the runtime's, or None when part of it has no runtime counterpart."""
    sel = selector.strip()
    for kit, rt in CONTEXT_MAP:
        sel = sel.replace(kit, rt)
    missing = []

    def sub(m):
        name = m.group(1)
        if name.startswith("zas-"):
            return m.group(0)
        rt = runtime_class(name)
        if rt is None:
            missing.append(name)
            return m.group(0)
        return "." + rt
    out = CLASS.sub(sub, sel)
    return None if missing else out


def classes_of(selector):
    """The classes a selector names (`.d-head h1` → {"d-head"})."""
    return set(CLASS.findall(selector or ""))


def part_classes(part):
    """The kit classes a part's selector names, without shared state classes."""
    return {c for c in classes_of(part[2]) if c in CLASS_MAP}


def touched_parts(touched):
    """The part ids a set of touched kit classes reaches; "*" in touched reaches every part."""
    if "*" in touched:
        return {p[0] for p in PARTS}
    return {p[0] for p in PARTS if part_classes(p) & set(touched)}


def _blocks(css):
    """Top-level (prelude, body) pairs of a stylesheet: a rule's selector and declarations, or an
    at-rule and its inner stylesheet."""
    out, depth, start, prelude = [], 0, 0, ""
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                prelude, start = css[start:i].strip(), i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append((prelude, css[start:i]))
                start = i + 1
    return out


def compile_css(css):
    """A kit-page stylesheet (the creator's look.css, the bridge) for the runtime: each rule's kit
    selectors rewritten to the runtime's, prefixed `html ` so they win over the runtime's tokens.css.
    A selector naming no kit class (the studio chrome, :root) is left out; one naming a kit class the
    runtime has no element for is listed in ``skipped``. Returns (css, skipped)."""
    css = re.sub(r"/\*.*?\*/", "", css or "", flags=re.S)
    out, skipped = [], []
    for prelude, body in _blocks(css):
        if prelude.startswith("@media") or prelude.startswith("@supports"):
            inner, sk = compile_css(body)
            skipped += sk
            if inner.strip():
                out.append(f"{prelude} {{\n{inner}\n}}")
            continue
        if prelude.startswith("@"):
            continue
        sels = []
        for sel in prelude.split(","):
            sel = re.sub(r"\s+", " ", sel).strip()
            kit = {c for c in classes_of(sel) if c in CLASS_MAP}
            if not kit:
                continue
            rt = translate_selector(sel)
            if rt is None:
                skipped.append(sel)
                continue
            sels.append("html " + rt)
        if sels:
            decls = re.sub(r"\s+", " ", body).strip()
            out.append(f"{', '.join(sels)} {{ {decls} }}")
    return "\n".join(out), skipped
