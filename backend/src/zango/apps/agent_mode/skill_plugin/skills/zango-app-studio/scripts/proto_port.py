#!/usr/bin/env python3
"""Open mode: hand the approved prototype's own look and code to the build, as they are.

    proto_port.py --workspace <ws>

Reads <ws>/.zas/bundle/prototype/prototype.html (the page the user approved) and writes:

  frontend/src/custom/prototype.css   every stylesheet of the prototype (not the zas runtime's), each
                                      rule scoped under `.zp`: a screen renders inside
                                      <div className="zp"> and gets the prototype's classes, tokens and
                                      fonts; nothing leaks onto the platform's pages. :root / html /
                                      body rules become the scope itself (their page box is dropped).
  .zas/bundle/prototype/source/       each of the prototype's scripts as its own file (its data-part
                                      name), and index.md: what each file defines, top-level name by
                                      line, so a screen's component can be found and ported.

Both are the platform's: written on every build, never edited (open-mode.md, "Port, don't redraw").
Without a prototype bundle it does nothing.
"""

import argparse
import json
import os
import re
import sys

SCOPE = ".zp"
ROOTS = re.compile(r"^(?::root|:host|html|body)(?![\w-])")
# the page's own box (html/body height, overflow, margin) belongs to the app shell, not a screen: a rule
# on the bare scope keeps only what children inherit
INHERITED = re.compile(r"^(--|font|color|line-height|letter-spacing|-webkit-font-smoothing|-moz-osx|text-rendering|"
                       r"-webkit-text-size-adjust|tab-size|-moz-tab-size|-o-tab-size|color-scheme|background)")
TAG = re.compile(r"<(style|script)\b([^>]*)>(.*?)</\1\s*>", re.S | re.I)
MINIFIED = 400  # mean line length above which a script is a bundled library, not the prototype's code


def split_top(s, sep=","):
    out, depth, cur = [], 0, []
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def scope_selector(sel):
    parts = []
    for p in split_top(sel):
        p = p.strip()
        if not p:
            continue
        rooted, m = False, ROOTS.match(p)
        while m:  # html body .x / :root .x / body.dark .x: the root words become the scope itself
            rooted, p = True, p[m.end():]
            m = ROOTS.match(p.lstrip()) if p[:1] in (" ", ">") else None
            if m:
                p = p.lstrip()
        if not rooted:
            parts.append(f"{SCOPE} {p}")
        elif not p.strip():
            parts.append(SCOPE)
        elif p[0] in ".:#[":
            parts.append(SCOPE + p)
        else:
            parts.append(f"{SCOPE} {p.strip().lstrip('>').strip()}")
    return ",".join(parts)


def blocks(css):
    """(prelude, body) per top-level block; comments and @import / @charset dropped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            return
        pre = css[i:j].strip()
        if ";" in pre:  # "@import url(x); .a" : only the last statement owns the block
            pre = pre[pre.rfind(";") + 1:].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        yield pre, css[j + 1:k - 1]
        i = k


def scope_css(css):
    out = []
    for pre, body in blocks(css):
        low = pre.lower()
        if not pre:
            continue
        if low.startswith(("@font-face", "@keyframes", "@-webkit-keyframes", "@property", "@page", "@counter-style")):
            out.append(f"{pre}{{{body}}}")
        elif low.startswith(("@media", "@supports", "@container", "@layer")):
            inner = scope_css(body)
            if inner:
                out.append(f"{pre}{{{inner}}}")
        elif low.startswith("@"):
            continue
        else:
            sel = scope_selector(pre)
            if not sel:
                continue
            if all(s == SCOPE for s in sel.split(",")):
                body = ";".join(d.strip() for d in split_top(body, ";")
                                if d.strip() and INHERITED.match(d.split(":", 1)[0].strip().lower()))
                if not body:
                    continue
            out.append(f"{sel}{{{body}}}")
    return "\n".join(out)


def parts(html):
    """The prototype's own <style> and <script> bodies, in page order: (kind, name, body). The zas
    runtime's, JSON data blocks and external scripts are left out."""
    out, n = [], {"style": 0, "script": 0}
    for m in TAG.finditer(html):
        kind, attrs, body = m.group(1).lower(), m.group(2), m.group(3)
        if 'data-zas="runtime"' in attrs or re.search(r"\bsrc=", attrs) or "application/json" in attrs:
            continue
        if not body.strip():
            continue
        n[kind] += 1
        name = re.search(r'data-part="([^"]+)"', attrs)
        name = name.group(1) if name else f"inline/{kind}-{n[kind]:02d}.{'css' if kind == 'style' else 'js'}"
        out.append((kind, name, body))
    return out


DEF = re.compile(r"^(?:export\s+)?(?:async\s+)?(?:function\s*\*?\s*([A-Za-z_$][\w$]*)|(?:const|let|var|class)\s+([A-Za-z_$][\w$]*))")


def outline(name, body):
    lines = body.split("\n")
    mean = sum(len(x) for x in lines) / max(1, len(lines))
    if mean > MINIFIED:
        return [f"## {name}", "", f"A bundled library ({len(body) // 1024} KB, minified): not the prototype's own code.", ""]
    defs = []
    for i, line in enumerate(lines, 1):
        m = DEF.match(line)
        if m:
            defs.append((i, m.group(1) or m.group(2)))
    out = [f"## {name}", "", f"{len(lines)} lines. Top-level definitions (line: name):", ""]
    out += [", ".join(f"{i}: `{d}`" for i, d in defs[k:k + 8]) for k in range(0, len(defs), 8)] or ["(none)"]
    return out + [""]


HEADER = ("/* The approved prototype's stylesheets, every rule scoped under .zp (proto_port.py).\n"
          "   Written by the platform on every build: do not edit. */\n")


def prototype_html(ws):
    """The approved page's text, or None without a prototype bundle."""
    try:
        with open(os.path.join(ws, ".zas", "bundle", "prototype", "prototype.html"), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def stylesheet(html):
    """frontend/src/custom/prototype.css for this page, as written."""
    return HEADER + "\n".join(scope_css(body) for kind, _, body in parts(html) if kind == "style") + "\n"


def run(ws):
    proto = os.path.join(ws, ".zas", "bundle", "prototype")
    html = prototype_html(ws)
    if html is None:
        return {"skipped": "no prototype bundle"}
    found = parts(html)
    css = stylesheet(html)
    custom = os.path.join(ws, "frontend", "src", "custom")
    os.makedirs(custom, exist_ok=True)
    with open(os.path.join(custom, "prototype.css"), "w", encoding="utf-8") as f:
        f.write(css)
    src = os.path.join(proto, "source")
    os.makedirs(src, exist_ok=True)
    index = ["# The prototype's source", "",
             "Each of the approved prototype's scripts and stylesheets, as written. Port a screen from its",
             "component here (find it by name below, then Read that line range); `prototype.css` in",
             "`frontend/src/custom/` is the stylesheets, already scoped under `.zp`.", ""]
    files = []
    for kind, name, body in found:
        rel = re.sub(r"[^\w./-]+", "_", name).lstrip("./")
        path = os.path.join(src, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body.strip("\n") + "\n")
        files.append(rel)
        index += outline(f"source/{rel}", body) if kind == "script" else [f"## source/{rel}", "", "A stylesheet (in prototype.css, scoped).", ""]
    with open(os.path.join(src, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index))
    return {"css_bytes": len(css), "files": files}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True)
    a = ap.parse_args()
    print(json.dumps(run(os.path.abspath(a.workspace))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
