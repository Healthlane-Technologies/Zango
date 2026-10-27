#!/usr/bin/env python3
"""
lucide_icons.py - resolve the spec's lucide icon names against the installed
lucide-react, then write:

  * frontend/src/zas/icons.gen.ts  - ICONS map with only the icons the app uses
  * .zas/menu_icons.json           - name -> inline SVG for AppBuilder menus/routes
                                     (32x32, stroke=currentColor; never emoji)

    python3 lucide_icons.py --workspace <app workspace>

Needs frontend/node_modules (run after npm install). Unknown names are reported
and fall back to "circle" so the build never breaks on an icon.
"""

import argparse
import json
import os
import re
import sys

RUNTIME_ICONS = ["activity", "plus", "circle", "zap", "pencil", "shopping-cart", "wallet", "clock", "gauge", "layers", "target",
                 "layout-dashboard", "file-text", "users", "settings"]


def collect(resolved):
    names = set(RUNTIME_ICONS)
    for r in resolved.get("roles", {}).values():
        for it in r.get("menu", []):
            if it.get("icon"):
                names.add(it["icon"])
            for sub in it.get("items", []) or []:
                if sub.get("icon"):
                    names.add(sub["icon"])
    for e in resolved.get("entities", {}).values():  # table cells: icon or icon by value
        for c in (e.get("table") or {}).get("columns", []) or []:
            ic = c.get("icon") or {}
            names |= {n for n in [*(ic.get("map") or {}).values(), ic.get("default")] if n and n != "initials"}
    for v in resolved.get("detail_views", {}).values():
        for s in v.get("stats", []) or []:
            if s.get("icon"):
                names.add(s["icon"])
        for b in ((v.get("header") or {}).get("actions") or {}).get("buttons", []) or []:
            if b.get("icon"):
                names.add(b["icon"])
        for t in v.get("tabs", []) or []:
            if t.get("icon"):
                names.add(t["icon"])
    return names


def collect_custom(ws):
    """Icons used by hand-written slots/pages under src/custom: <Icon name="…"/>, icon="…" and icon: "…"."""
    names = set()
    root = os.path.join(ws, "frontend", "src", "custom")
    for d, _, files in os.walk(root):
        for f in files:
            if f.endswith((".tsx", ".ts")):
                src = open(os.path.join(d, f), encoding="utf-8").read()
                for attrs in re.findall(r"<Icon\b([^>]*)>", src):  # also name={x ? "a" : "b"}
                    names |= set(re.findall(r'"([a-z0-9-]+)"', attrs))
                # icon="x" props and icon: "x" in item objects (Kpis, List rows)
                names |= set(re.findall(r'\bicon\s*[:=]\s*["\']([a-z0-9-]+)["\']', src))
    return names


def icon_file(nm, name):
    for ext in (".mjs", ".js"):
        p = os.path.join(nm, "lucide-react", "dist", "esm", "icons", name + ext)
        if os.path.exists(p):
            return p
    return None


def pascal(name):
    return "".join(p[:1].upper() + p[1:] for p in name.split("-"))


def parse(path, name, depth=0):
    src = open(path, encoding="utf-8").read()
    alias = re.search(r"export \{ default \} from '\./([\w-]+)\.m?js'", src)
    if alias and depth < 3:  # renamed icons re-export their new file; the old PascalCase name is still exported
        target = os.path.join(os.path.dirname(path), alias.group(1) + os.path.splitext(path)[1])
        _, elems = parse(target, alias.group(1), depth + 1)
        return pascal(name), elems
    m = re.search(r"const (\w+) = createLucideIcon", src)
    export = m.group(1) if m else pascal(name)
    node = re.search(r"const __iconNode = \[(.*?)\];\s*\n", src, re.S)
    elems = []
    if node:
        for tag, attrs in re.findall(r'\[\s*"(\w+)",\s*\{(.*?)\}\s*\]', node.group(1), re.S):
            kv = dict(re.findall(r'(\w+):\s*"([^"]*)"', attrs))
            kv.pop("key", None)
            elems.append((tag, kv))
    return export, elems


def svg(elems):
    body = "".join("<%s %s/>" % (t, " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())) for t, a in elems)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">' + body + "</svg>")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    a = ap.parse_args(argv)
    ws = a.workspace
    resolved = json.load(open(os.path.join(ws, ".zas", "spec.resolved.json"), encoding="utf-8"))
    nm = os.path.join(ws, "frontend", "node_modules")
    if not os.path.isdir(os.path.join(nm, "lucide-react")):
        print("frontend/node_modules/lucide-react not found: run npm install first", file=sys.stderr)
        return 2
    names = sorted(collect(resolved) | collect_custom(ws))
    found, missing, svgs = {}, [], {}
    for n in names:
        p = icon_file(nm, n)
        if not p:
            missing.append(n)
            continue
        export, elems = parse(p, n)
        if export and elems:
            found[n] = export
            svgs[n] = svg(elems)
        else:
            missing.append(n)
    if "circle" not in found:
        found["circle"] = "Circle"
    for n in missing:
        found[n] = found["circle"]
        svgs[n] = svgs.get("circle", "")
    exports = sorted(set(found.values()))
    ts = ["// Generated by scripts/lucide_icons.py - the lucide icons this app uses. Do not edit.",
          f"import {{ {', '.join(exports)} }} from \"lucide-react\";", "",
          "export const ICONS = {"]
    ts += [f'  "{k}": {v},' for k, v in sorted(found.items())]
    ts += ["} as const;", ""]
    out_ts = os.path.join(ws, "frontend", "src", "zas", "icons.gen.ts")
    os.makedirs(os.path.dirname(out_ts), exist_ok=True)
    text = "\n".join(ts)
    try:
        same = open(out_ts, encoding="utf-8").read() == text
    except OSError:
        same = False
    if not same:  # an unchanged file keeps its mtime, so a deployed build is not reported stale
        open(out_ts, "w", encoding="utf-8").write(text)
    out_json = os.path.join(ws, ".zas", "menu_icons.json")
    json.dump(svgs, open(out_json, "w", encoding="utf-8"), indent=1)
    print(f"{len(found)} icons → {out_ts}; menu SVGs → {out_json}")
    if missing:
        print("Unknown lucide names (using circle): " + ", ".join(missing) +
              ". Rename them in the spec (lucide.dev/icons) and re-run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
