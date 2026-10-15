"""Build report: <ws>/.zas/build_report.html (polished, self-contained) and build_report.md (references/report.md).

    python3 -m zas_test.report --workspace <ws>

Reads spec.resolved.json (incl. lint and intent findings), holes.md, test_results.json (api, ui,
design, scenarios), build_log.json, the test-user emails (never passwords) and .zas/screens/.
Prints the Markdown summary. Exit 0 = Ready, 1 = Ready with gaps, 2 = Not ready.
"""

import argparse
import base64
import html
import io
import os
import re
import sys
import time
from collections import OrderedDict

from . import auth, load_json, load_results
from . import log as blog

LAYERS = ["api", "ui", "design", "scenarios"]
LAYER_INFO = {
    "api": ("API", "Access, forms, workflow, tags, row actions, row scoping and the 360 payload, generated from the spec"),
    "ui": ("UI", "Every page, menu and 360 tab rendered in a real browser for every role"),
    "design": ("Design", "Design lint, tokens, the design tree per role and layout sanity"),
    "scenarios": ("Scenarios", "Each plain-language rule exercised end to end (written from the spec text)"),
}
BLOCKING_LAYERS = {"api", "ui", "design", "scenarios"}
REQUIRED_LAYERS = {"api", "ui", "design"}
# reported, not blocking: platform-dependent / cosmetic, and preview parity (the agent gets fix rounds for it first)
NON_BLOCKING = ("design.layout", "design.gallery", "design.parity")
TONE = {"pass": "green", "fail": "red", "skip": "amber", "done": "green", "covered": "blue", "needs-review": "amber",
        "blocked": "red", "todo": "red", "error": "red", "warn": "amber", "intent": "purple", "ok": "green"}
E_ = html.escape


# ───────────────────────────── data ─────────────────────────────

def holes(ws):
    rows = []
    p = os.path.join(ws, ".zas", "holes.md")
    if not os.path.exists(p):
        return rows
    for line in open(p, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 7 and re.match(r"H-\d+", cells[0]):
            rows.append({"id": cells[0], "kind": cells[1], "path": cells[2].strip("`"), "text": cells[3],
                         "target": cells[4].strip("`"), "status": cells[-1]})
    return rows


def hole_notes(ws):
    """`# zas:note …` (Python) / `// zas:note …` (TS) lines right under a `zas:hole H-NN` marker:
    the implementer's assumptions and wiring, kept in the code so re-runs never lose them."""
    notes = {}
    roots = [os.path.join(ws, "backend"), os.path.join(ws, "frontend", "src", "custom")]
    for root in roots:
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in ("node_modules", "__pycache__", "zas_core")]
            for f in files:
                if not f.endswith((".py", ".ts", ".tsx")):
                    continue
                cur = None
                for line in open(os.path.join(d, f), encoding="utf-8", errors="replace"):
                    m = re.match(r"\s*(?:#|//)\s*zas:hole\s+(H-\d+)", line)
                    if m:
                        cur = m.group(1)
                        continue
                    n = re.match(r"\s*(?:#|//)\s*zas:note\s?(.*)", line)
                    if n and cur:
                        notes.setdefault(cur, []).append(n.group(1).strip())
                    else:
                        cur = None
    return {k: " ".join(v) for k, v in notes.items()}


def manual_steps(ws, M, hs):
    out = []
    for h in [h for h in hs if "/tasks.py::" in h["target"]]:
        rel, fn = h["target"].split("::", 1)
        p = os.path.join(ws, rel)
        src = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        scheduled = re.search(rf"#\s*zas:schedule[^\n]*\n(?:[^\n]*\n){{0,3}}?\s*def {re.escape(fn)}\(", src)
        called = re.search(rf"\b{re.escape(fn)}\(", src.replace(f"def {fn}(", ""))
        if not scheduled and not called:
            out.append(f"Task `{fn}` has no `# zas:schedule` line and nothing calls it: {h['text'][:110]}")
    hooks = [os.path.join(ws, "backend", m["code"], "hooks.py") for m in M["modules"]]
    if any(os.path.exists(p) and "notify" in open(p, encoding="utf-8").read() for p in hooks):
        out.append("Wire a mail/SMS provider in `backend/zas_core/notify.py` `send_via_provider`: messages are logged "
                   "(and written to `.zas/outbox.jsonl` in DEBUG) but not delivered")
    if any("/tasks.py::" in h["target"] for h in hs):
        out.append("Keep a Celery worker and beat running so the scheduled jobs fire")
    out += [f"{h['id']} blocked: {h['text'][:160]}" for h in hs if h["status"] == "blocked"]
    return list(OrderedDict.fromkeys(out))


def gather(ws):
    M = load_json(ws, "spec.resolved.json")
    res = load_results(ws)
    results = res.get("results", [])
    hs = holes(ws)
    steps = blog.latest(blog.load(ws))
    findings = M.get("issues") or []
    blocking = [r for r in results if r["status"] == "fail" and r["layer"] in BLOCKING_LAYERS
                and not r["id"].startswith(NON_BLOCKING)]
    other_fail = [r for r in results if r["status"] == "fail" and r not in blocking]
    skips = [r for r in results if r["status"] == "skip"]
    todo = [h for h in hs if h["status"] == "todo"]
    review = [h for h in hs if h["status"] in ("blocked", "needs-review")]
    step_fail = [s for s in steps if s["status"] == "fail"]
    ran = {r["layer"] for r in results}
    missing = sorted(REQUIRED_LAYERS - ran)
    intents = [i for i in findings if i["level"] == "intent"]
    reasons = []
    if blocking or todo or step_fail or missing:
        verdict, code = "Not ready", 2
        reasons += [f"{len(blocking)} blocking check(s) failed"] if blocking else []
        reasons += [f"{len(todo)} plain-language item(s) not implemented"] if todo else []
        reasons += [f"build step failed: phase {s['phase']} {s['step']}" for s in step_fail]
        reasons += [f"test layer not run: {layer}" for layer in missing]
    elif review or other_fail or skips or intents or "scenarios" not in ran:
        verdict, code = "Ready with gaps", 1
        reasons += [f"{len(review)} plain-language item(s) need review or are blocked"] if review else []
        reasons += [f"{len(other_fail)} non-blocking check(s) failed (screenshot goldens, layout, preview parity)"] if other_fail else []
        reasons += [f"{len(skips)} check(s) skipped, each with its reason"] if skips else []
        reasons += [f"{len(intents)} spec intent finding(s) to look at"] if intents else []
        reasons += ["no scenario tests yet for the plain-language items"] if "scenarios" not in ran else []
    else:
        verdict, code = "Ready", 0
        reasons.append("every blocking check passed and every plain-language item is implemented and proven")
    return {"ws": ws, "M": M, "res": res, "results": results, "holes": hs, "users": auth.load_users(ws), "steps": steps,
            "findings": findings, "blocking": blocking, "skips": skips, "verdict": verdict, "code": code,
            "reasons": reasons, "manual": manual_steps(ws, M, hs), "notes": hole_notes(ws), "other_fail": other_fail}


def counts(rs):
    return {s: sum(1 for r in rs if r["status"] == s) for s in ("pass", "fail", "skip")}


def app_roles(M):
    return [r for r in M["roles"] if r not in ("AnonymousUsers", "SystemUsers")]


# ───────────────────────────── markdown ─────────────────────────────

def to_md(D):
    M, results = D["M"], D["results"]
    out = [f"# {M['app']['name']}: build report", "", f"**Verdict: {D['verdict']}**", ""]
    out += [f"- {r}" for r in D["reasons"]] + [""]
    if D["code"] == 2:
        out += ["Blocking:"] + [f"- `{r['id']}` ({r.get('role') or 'any role'}): {r['title']}: {r['detail'][:240]} (`{r['spec_path']}`)"
                                for r in D["blocking"][:30]] + [""]
    out += ["## How to open it", "", f"- App: {D['users'].get('target', '(unknown)')}/app/"]
    for u in D["users"].get("users", []):
        role = (u.get("roles") or ["?"])[0]
        land = (M["roles"].get(role) or {}).get("landing")
        out.append(f"- {role}: `{u.get('email')}`" + (f", lands on {land}" if land else "") + " (password in `.zas/test_users.json`)")
    out += ["", "## Tests", ""]
    for layer in LAYERS:
        rs = [r for r in results if r["layer"] == layer]
        if not rs:
            out.append(f"- **{layer}**: not run")
            continue
        c = counts(rs)
        out.append(f"- **{layer}**: {c['pass']} passed, {c['fail']} failed, {c['skip']} skipped")
        for r in rs:
            if r["status"] != "pass":
                who = f" [{r['role']}]" if r.get("role") else ""
                out.append(f"  - {r['status'].upper()} `{r['id']}`{who}: {r['title']}. {r['detail'][:240]} (`{r['spec_path']}`)")
    out += ["", "## Spec review", ""]
    out += [f"- **{i['level']}** `{i['where']}`: {i['msg']}" + (f" Fix: {i['fix']}" if i.get("fix") else "") for i in D["findings"]] or ["None."]
    out += ["", "## Plain-language items", "", "| ID | Status | Text | Where |", "|---|---|---|---|"]
    order = {"blocked": 0, "needs-review": 1, "todo": 2, "covered": 3, "done": 4}
    for h in sorted(D["holes"], key=lambda h: (order.get(h["status"], 5), h["id"])):
        out.append(f"| {h['id']} | {h['status']} | {h['text'][:160]} | `{h['target']}` |")
    out += ["", "## Manual steps left", ""] + ([f"- {m}" for m in D["manual"]] or ["None."])
    out += ["", "## Re-running", "", "Edit the YAML, then `spec_check.py <spec> --workspace <ws>` and the phases from 2. "
            "Hand-written hooks, slots, fixtures and scenarios are kept. `--audit-holes` shows what changed.", ""]
    return "\n".join(out)


# ───────────────────────────── html pieces ─────────────────────────────

def md_inline(s):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", E_(str(s)))


def pill(label, tone):
    return f'<span class="pill t-{tone}">{E_(str(label))}</span>'


def det(text):
    return f'<div class="det">{E_(str(text)[:400])}</div>' if text else ""


def bar(c):
    tot = max(1, sum(c.values()))
    parts = "".join(f'<span class="b-{k}" style="width:{c[k] * 100 / tot:.2f}%"></span>' for k in ("pass", "skip", "fail") if c[k])
    return f'<div class="bar">{parts}</div>'


def thumb(path, width=520):
    """A screenshot as an inline JPEG data URI: downscaled and cropped to the top of the page."""
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        if im.width > width:
            im = im.resize((width, int(im.height * width / im.width)))
        im = im.crop((0, 0, im.width, min(im.height, int(width * 0.7))))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=74, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def group_of(r):
    if r["layer"] == "scenarios":
        return f"{r.get('hole') or 'scenario'} · {r['title']}"
    parts = r["id"].split(".")
    return parts[1] if r["layer"] in ("ui", "design") and len(parts) > 1 else parts[0]


def kpi(label, value, sub="", cls=""):
    return f'<div class="kpi {cls}"><span>{E_(label)}</span><b>{value}</b><em>{sub}</em></div>'


# ───────────────────────────── html sections ─────────────────────────────

def s_hero(D, by_layer):
    M, app = D["M"], D["M"]["app"]
    tone = {"Ready": "green", "Ready with gaps": "amber", "Not ready": "red"}[D["verdict"]]
    target = D["users"].get("target", "")
    tot = counts(D["results"])
    sc = counts(by_layer["scenarios"])
    hc = {k: sum(1 for h in D["holes"] if h["status"] == k) for k in ("done", "covered", "needs-review", "blocked")}
    initials = "".join(w[0] for w in app["name"].split()[:2]).upper()
    reasons = "".join(f"<li>{md_inline(r)}</li>" for r in D["reasons"])
    open_btn = f'<a class="btn pri" href="{E_(target)}/app/" target="_blank" rel="noreferrer">Open the app ↗</a>' if target else ""
    scen_val = f"{sc['pass']}<small>/{sum(sc.values())}</small>" if by_layer["scenarios"] else "—"
    return f"""
<header class="hero">
  <div class="hero-top">
    <div class="logo">{E_(initials)}</div>
    <div class="ht"><h1>{E_(app['name'])}</h1><p>{E_(app.get('description') or '')}</p>
      <div class="meta"><span>Build report · {time.strftime('%d %b %Y, %H:%M')}</span>
        <span>spec <code>{E_(str(M.get('spec_hash', ''))[:12])}</code></span><span>skill {E_(str(M.get('skill_version', '')))}</span></div></div>
    {open_btn}
  </div>
  <div class="verdict t-{tone}"><div class="vd"><span class="dot"></span>{E_(D['verdict'])}</div><ul>{reasons}</ul></div>
  <div class="kpis">
    {kpi('Checks passed', f"{tot['pass']}<small>/{sum(tot.values())}</small>", f"{tot['fail']} failed · {tot['skip']} skipped", 'k-red' if D['blocking'] else 'k-green')}
    {kpi('Scenarios proven', scen_val, 'plain-language rules run end to end')}
    {kpi('Custom items', f"{hc['done'] + hc['covered']}<small>/{len(D['holes'])}</small>", f"{hc['needs-review']} need review · {hc['blocked']} blocked")}
    {kpi('Built', f"{len(M['entities'])}<small> entities</small>", f"{len(M['pages'])} pages · {len(app_roles(M))} roles · {len(M['modules'])} modules")}
  </div>
</header>"""


def s_open(D):
    M, target = D["M"], D["users"].get("target", "")
    rows = ""
    for u in D["users"].get("users", []):
        role = (u.get("roles") or ["?"])[0]
        R = M["roles"].get(role) or {}
        menu = []
        for it in R.get("menu", []):
            for x in [it] + list(it.get("items") or []):
                if x.get("page"):
                    menu.append(x.get("label") or (M["pages"].get(x["page"]) or {}).get("title") or x["page"])
        land = (M["pages"].get(R.get("landing")) or {}).get("title") or R.get("landing") or "—"
        rows += (f"<tr><td><b>{E_(role)}</b><div class='muted small'>{E_(R.get('description') or '')}</div></td>"
                 f"<td><code>{E_(u.get('email', ''))}</code></td><td>{E_(land)}</td><td>{E_(', '.join(menu))}</td></tr>")
    return f"""<section id="open"><h2>Open the app</h2>
<p class="lead">Sign in at <a href="{E_(target)}/app/" target="_blank" rel="noreferrer">{E_(target)}/app/</a> as a test user. Passwords stay in <code>.zas/test_users.json</code>.</p>
<div class="card"><table><thead><tr><th>Role</th><th>Test user</th><th>Lands on</th><th>Menu</th></tr></thead><tbody>{rows}</tbody></table></div></section>"""


def s_tests(D, by_layer):
    cards = ""
    for layer in LAYERS:
        rs, (name, desc) = by_layer[layer], LAYER_INFO[layer]
        if not rs:
            cards += f'<div class="lc"><div class="lh"><b>{name}</b>{pill("not run", "gray")}</div><p>{E_(desc)}</p></div>'
            continue
        c = counts(rs)
        at = D["res"].get("runs", {}).get(layer, {}).get("at", "")
        tone = "red" if any(r in D["blocking"] for r in rs) else ("amber" if c["fail"] or c["skip"] else "green")
        cards += (f'<a class="lc" href="#layer-{layer}"><div class="lh"><b>{name}</b>{pill(str(c["pass"]) + "/" + str(len(rs)), tone)}</div>'
                  f'<p>{E_(desc)}</p>{bar(c)}<div class="lf"><span>{c["pass"]} passed</span><span>{c["fail"]} failed</span>'
                  f'<span>{c["skip"]} skipped</span><span class="muted">{E_(at)}</span></div></a>')
    attn = sorted((r for r in D["results"] if r["status"] != "pass"),
                  key=lambda r: (0 if r in D["blocking"] else 2 if r["status"] == "fail" else 1, r["layer"], r["id"]))
    folded, rest = OrderedDict(), []
    for r in attn:
        pre = next((p for p in NON_BLOCKING if r["id"].startswith(p)), None)
        if r["status"] == "fail" and pre:
            folded.setdefault(pre, []).append(r)
        else:
            rest.append(r)
    rows = ""
    for r in rest:
        blocking = r in D["blocking"]
        label = ("blocking " if blocking else "") + r["status"]
        who = f' <span class="muted">as {E_(r["role"])}</span>' if r.get("role") else ""
        rows += (f'<div class="issue"><div>{pill(label, "red" if blocking else TONE[r["status"]])}<div class="lay">{E_(r["layer"])}</div></div>'
                 f'<div><b>{E_(r["title"])}</b>{who}<div class="muted small"><code>{E_(r["spec_path"])}</code></div>{det(r.get("detail"))}</div></div>')
    why = {"design.gallery": "Component screenshots differ from the skill's goldens. Non-blocking: goldens are shot with "
                             "a fixed shell width and font build, so a different sidebar or platform changes the size.",
           "design.layout": "Layout sanity at 1280/1440 px. Non-blocking: cosmetic."}
    for pre, rs in folded.items():
        items = "".join(f"<li><b>{E_(r['title'])}</b>: {E_(r.get('detail', '')[:160])}</li>" for r in rs)
        rows += (f'<div class="issue"><div>{pill("non-blocking", "gray")}<div class="lay">{E_(rs[0]["layer"])}</div></div>'
                 f'<div><b>{len(rs)} × {E_(pre)}</b><div class="muted small">{E_(why.get(pre, "Reported, not blocking."))}</div>'
                 f'<ul class="mini">{items}</ul></div></div>')
    attn_html = rows or '<p class="ok">Nothing failed or was skipped.</p>'
    detail = ""
    for layer in LAYERS:
        rs = by_layer[layer]
        if not rs:
            continue
        groups = OrderedDict()
        for r in rs:
            groups.setdefault(group_of(r), []).append(r)
        inner = ""
        for g, grs in groups.items():
            c = counts(grs)
            st = "fail" if c["fail"] else ("skip" if c["skip"] else "pass")
            lines = ""
            for r in grs:
                extra = det(r.get("detail")) if r["status"] != "pass" else ""
                lines += (f'<tr><td>{pill(r["status"], TONE[r["status"]])}</td><td>{E_(r["title"])}</td>'
                          f'<td class="muted">{E_(r.get("role") or "")}</td><td><code>{E_(r["spec_path"])}</code>{extra}</td></tr>')
            inner += (f'<details{" open" if st == "fail" else ""}><summary>{pill(st, TONE[st])}<b>{E_(g)}</b>'
                      f'<span class="muted">{c["pass"]} passed · {c["fail"]} failed · {c["skip"]} skipped</span></summary>'
                      f'<table class="tight"><tbody>{lines}</tbody></table></details>')
        detail += f'<div class="ld" id="layer-{layer}"><h3>{LAYER_INFO[layer][0]}</h3>{inner}</div>'
    return f"""<section id="tests"><h2>Tests</h2>
<p class="lead">Every check names the spec path it proves. The generated layers prove the app does what the spec says; scenarios prove each plain-language rule behaves as written.</p>
<div class="lcs">{cards}</div><h3>Needs attention</h3><div class="card list">{attn_html}</div><h3>All checks</h3>{detail}</section>"""


def s_access(D):
    M = D["M"]
    roles = app_roles(M)
    failing = {(r.get("role"), r["spec_path"].split(".")[1]) for r in D["results"]
               if r["status"] == "fail" and r["spec_path"].startswith("entities.") and "." in r["spec_path"]}
    body = ""
    for E in M["entities"].values():
        tds = ""
        for role in roles:
            a = (E.get("access_resolved") or {}).get(role) if E.get("access") else {"actions": ["view", "add", "edit", "export", "detail"]}
            if not a or a.get("none"):
                tds += '<td class="na">—</td>'
                continue
            rows = a.get("rows")
            if rows in (None, "all"):
                scope = "all rows"
            elif isinstance(rows, dict):
                scope = rows.get("where") or (f"own {rows['own']}" if "own" in rows else rows.get("text") or "custom")
            else:
                scope = str(rows)
            chips = "".join(f"<i>{E_(x)}</i>" for x in sorted(a.get("actions", [])))
            cls = ' class="bad"' if (role, E["code"]) in failing else ""
            tds += f'<td{cls}><div class="acts">{chips}</div><div class="scope">{E_(scope)}</div></td>'
        body += f'<tr><th><b>{E_(E["name"])}</b><div class="muted small"><code>{E_(E["names"]["endpoint"])}</code></div></th>{tds}</tr>'
    head = "".join(f"<th>{E_(r)}</th>" for r in roles)
    return f"""<section id="access"><h2>Access by role</h2>
<p class="lead">What each role may do on each entity and which rows it sees (enforced server-side on lists, details, row actions and transitions). A red cell has a failing check.</p>
<div class="card scroll"><table class="matrix"><thead><tr><th>Entity</th>{head}</tr></thead><tbody>{body}</tbody></table></div></section>"""


def s_items(D, by_layer):
    scen = {}
    for r in by_layer["scenarios"]:
        if r.get("hole") and not r["id"].endswith(".none"):
            scen.setdefault(r["hole"], []).append(r)
    order = {"blocked": 0, "needs-review": 1, "todo": 2, "done": 3, "covered": 4}
    out = ""
    for h in sorted(D["holes"], key=lambda h: (order.get(h["status"], 5), int(h["id"][2:]))):
        rs = scen.get(h["id"], [])
        if rs:
            st = "fail" if any(r["status"] == "fail" for r in rs) else "pass" if all(r["status"] == "pass" for r in rs) else "skip"
            sp = pill("scenario " + st, TONE[st])
        elif h["status"] in ("covered", "blocked"):
            sp = ""
        else:
            sp = pill("no scenario", "gray")
        proofs = "".join(f'<li>{pill(r["status"], TONE[r["status"]])}{E_(r["title"])}{det(r.get("detail")) if r["status"] == "fail" else ""}</li>' for r in rs)
        proofs = f'<ul class="proofs">{proofs}</ul>' if proofs else ""
        note = D["notes"].get(h["id"])
        if note:
            proofs = f'<div class="note n-{E_(h["status"])}">{md_inline(note)}</div>' + proofs
        out += (f'<div class="item"><div class="iid">{E_(h["id"])}</div><div class="ib"><div class="ih">{pill(h["status"], TONE.get(h["status"], "gray"))}'
                f'<span class="kind">{E_(h["kind"])}</span>{sp}</div><p>{md_inline(h["text"])}</p>'
                f'<div class="muted small"><code>{E_(h["path"])}</code> → <code>{E_(h["target"])}</code></div>{proofs}</div></div>')
    return f"""<section id="items"><h2>Plain-language items</h2>
<p class="lead">Every rule the spec wrote in prose became code (a hook, a scheduled job, a panel or a page), with the scenario that proves it.</p>
<div class="items">{out}</div></section>"""


def s_review(D):
    order = {"error": 0, "intent": 1, "warn": 2}
    rows = ""
    for i in sorted(D["findings"], key=lambda i: order.get(i["level"], 3)):
        fix = f'<div class="fix">Fix: {md_inline(i["fix"])}</div>' if i.get("fix") else ""
        rows += (f'<div class="issue"><div>{pill(i["level"], TONE.get(i["level"], "gray"))}</div><div><b>{md_inline(i["msg"])}</b>'
                 f'<div class="muted small"><code>{E_(i["where"])}</code></div>{fix}</div></div>')
    rows = rows or '<p class="ok">No errors, warnings or intent findings.</p>'
    return f"""<section id="review"><h2>Spec review</h2>
<p class="lead"><b>Intent</b> findings are valid spec that is probably not what was meant (a role that can act but never see, a child listed wider than its parent). Tests pass on these, because tests check what the spec says.</p>
<div class="card list">{rows}</div></section>"""


def s_built(D):
    M = D["M"]
    mods = ""
    for m in M["modules"]:
        trs = ""
        for c in m.get("entity_order") or m["entities"]:
            E = M["entities"][c]
            wf = E.get("workflow") or {}
            wfs = (f"{len(wf.get('statuses', []))} statuses · {len(wf.get('transitions', []))} transitions · {len(wf.get('tags', []))} tags"
                   if wf else '<span class="muted">no workflow</span>')
            trs += (f"<tr><td><b>{E_(E['name'])}</b><div class='muted small'>{E_(E.get('kind', ''))}</div></td>"
                    f"<td><code>{E_(E['names']['model'])}</code></td><td><code>{E_(E['names']['endpoint'])}</code></td>"
                    f"<td>{len(E['fields'])}</td><td>{wfs}</td><td>{len(E.get('policies', []))}</td></tr>")
        mods += (f"<h3>{E_(m['name'])} <span class='muted'>backend/{E_(m['code'])}/</span></h3><div class='card'><table><thead><tr>"
                 f"<th>Entity</th><th>Model</th><th>Endpoint</th><th>Fields</th><th>Workflow</th><th>Policies</th></tr></thead><tbody>{trs}</tbody></table></div>")
    pages = ""
    for c, p in M["pages"].items():
        who = [r for r, R in M["roles"].items()
               if any(it.get("page") == c or any(s.get("page") == c for s in it.get("items") or []) for it in R.get("menu", []))]
        pages += (f"<tr><td><b>{E_(p.get('title') or c)}</b></td><td>{E_(p['type'])}</td>"
                  f"<td><code>{E_(p.get('route', ''))}</code></td><td>{E_(', '.join(who))}</td></tr>")
    return f"""<section id="built"><h2>What was built</h2>{mods}
<h3>Pages</h3><div class="card"><table><thead><tr><th>Page</th><th>Type</th><th>Route</th><th>In the menu of</th></tr></thead><tbody>{pages}</tbody></table></div></section>"""


def s_screens(D):
    sd = os.path.join(D["ws"], ".zas", "screens")
    if not os.path.isdir(sd):
        return ""
    out = ""
    for role in sorted(os.listdir(sd)):
        p = os.path.join(sd, role)
        if role == "gallery" or not os.path.isdir(p):
            continue
        tiles = ""
        for f in sorted(os.listdir(p)):
            src = thumb(os.path.join(p, f)) if f.endswith(".png") else None
            if src:
                cap = f[:-4].replace("__", " · ").replace("_", " ")
                tiles += f'<figure><img loading="lazy" src="{src}" alt="{E_(role)}: {E_(cap)}"><figcaption>{E_(cap)}</figcaption></figure>'
        if tiles:
            out += f'<details{" open" if not out else ""}><summary><b>{E_(role.replace("_", " ").title())}</b></summary><div class="shots">{tiles}</div></details>'
    if not out:
        return ""
    return f'<section id="screens"><h2>Screens</h2><p class="lead">Captured by the UI tests, per role. Full-size PNGs are in <code>.zas/screens/</code>.</p>{out}</section>'


def s_next(D):
    man = "".join(f"<li>{md_inline(m)}</li>" for m in D["manual"]) or "<li>None.</li>"
    tl = ""
    for s in D["steps"]:
        tries = f' <span class="muted">after {s["attempts"]} attempts</span>' if s.get("attempts", 1) > 1 else ""
        sub = f'<div class="muted small">{E_(s["detail"])}</div>' if s.get("detail") else ""
        tl += f'<li class="s-{E_(s["status"])}"><span class="ph">Phase {E_(str(s["phase"]))}</span><b>{E_(s["step"])}</b>{tries}{sub}</li>'
    return f"""<section id="next"><h2>Manual steps left</h2><div class="card pad"><ul class="checks">{man}</ul></div>
<h2 class="mt">Build timeline</h2><ol class="tl">{tl}</ol>
<h2 class="mt">Re-running</h2><div class="card pad"><p>Edit the YAML, then run <code>spec_check.py &lt;spec&gt; --workspace &lt;ws&gt;</code> and the build from Phase 2. Hand-written hooks, slots, fixtures and scenarios are kept; <code>--audit-holes</code> shows what changed.</p></div></section>"""


def to_html(D):
    M, app = D["M"], D["M"]["app"]
    by_layer = {layer: [r for r in D["results"] if r["layer"] == layer] for layer in LAYERS}
    screens = s_screens(D)
    body = (s_hero(D, by_layer) + s_open(D) + s_tests(D, by_layer) + s_access(D) + s_items(D, by_layer)
            + s_review(D) + s_built(D) + screens + s_next(D))
    links = [("open", "Open the app"), ("tests", "Tests"), ("access", "Access by role"), ("items", "Plain-language items"),
             ("review", "Spec review"), ("built", "What was built"), ("screens", "Screens"), ("next", "Next steps")]
    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in links if i != "screens" or screens)
    brand = (app.get("theme") or {}).get("primary") or "#4F46E5"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E_(app["name"])} · Build report</title><style>{CSS.replace("__BRAND__", brand)}</style></head>'
            f'<body><div class="wrap"><nav class="toc"><div class="tb">{E_(app["name"])}</div>{nav}</nav><main>{body}'
            f'<footer>Zango App Studio build report · <code>python -m zas_test.report --workspace {E_(os.path.basename(D["ws"]))}</code></footer>'
            f'</main></div></body></html>')


CSS = """
:root{--brand:__BRAND__;--text:#101828;--sub:#475467;--muted:#667085;--bd:#eaecf0;--bdf:#f2f4f7;--ground:#f7f8fa;--card:#fff;--head:#f9fafb;
--green:#067647;--green-bg:#ecfdf3;--green-bd:#abefc6;--amber:#b54708;--amber-bg:#fffaeb;--amber-bd:#fedf89;--red:#b42318;--red-bg:#fef3f2;--red-bd:#fecdca;
--blue:#175cd3;--blue-bg:#eff8ff;--blue-bd:#b2ddff;--purple:#5925dc;--purple-bg:#f4f3ff;--purple-bd:#d9d6fe;--gray:#344054;--gray-bg:#f2f4f7;--gray-bd:#eaecf0}
@media (prefers-color-scheme:dark){:root{--text:#f2f4f7;--sub:#cecfd2;--muted:#94969c;--bd:#2a2f3a;--bdf:#22262f;--ground:#0c0f14;--card:#151922;--head:#1a1f29;
--green:#47cd89;--green-bg:#0b2b1d;--green-bd:#085d3a;--amber:#fdb022;--amber-bg:#2b1d08;--amber-bd:#93370d;--red:#f97066;--red-bg:#2d1110;--red-bd:#912018;
--blue:#53b1fd;--blue-bg:#0b1d33;--blue-bd:#1849a9;--purple:#9b8afb;--purple-bg:#1d1638;--purple-bd:#4a1fb8;--gray:#cecfd2;--gray-bg:#22262f;--gray-bd:#333741}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--ground);color:var(--text);font:14px/1.55 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--brand)}code{font:12px "JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--gray-bg);padding:1px 5px;border-radius:5px;color:var(--sub);word-break:break-word}
.wrap{display:grid;grid-template-columns:200px minmax(0,1fr);max-width:1320px;margin:0 auto;gap:32px;padding:28px 28px 64px}
.toc{position:sticky;top:24px;align-self:start;display:flex;flex-direction:column;gap:2px}.toc .tb{font-weight:650;margin:0 0 10px 10px}
.toc a{color:var(--sub);text-decoration:none;padding:7px 10px;border-radius:8px;font-weight:500;font-size:13.5px}.toc a:hover{background:var(--card);color:var(--text)}
@media (max-width:900px){.wrap{grid-template-columns:1fr;padding:16px}.toc{display:none}}
.hero{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:24px;box-shadow:0 1px 3px rgba(16,24,40,.06)}
.hero-top{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap}
.logo{width:52px;height:52px;border-radius:14px;background:var(--brand);color:#fff;display:grid;place-items:center;font-weight:700;font-size:18px;flex:none}
.ht{flex:1;min-width:240px}.ht h1{margin:0;font-size:24px;letter-spacing:-.02em}.ht p{margin:4px 0 8px;color:var(--sub)}
.meta{display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:12.5px}
.btn{display:inline-flex;align-items:center;height:38px;padding:0 16px;border-radius:9px;font-weight:600;text-decoration:none;border:1px solid var(--bd);white-space:nowrap}
.btn.pri{background:var(--brand);border-color:var(--brand);color:#fff}.btn.pri:hover{filter:brightness(.94)}
.verdict{margin-top:18px;border-radius:12px;padding:14px 16px;border:1px solid}.verdict .vd{display:flex;align-items:center;gap:9px;font-weight:700;font-size:16px}
.verdict ul{margin:6px 0 0;padding-left:20px;color:var(--sub)}.dot{width:10px;height:10px;border-radius:50%;background:currentColor;flex:none}
.t-green{background:var(--green-bg);color:var(--green);border-color:var(--green-bd)}.t-amber{background:var(--amber-bg);color:var(--amber);border-color:var(--amber-bd)}
.t-red{background:var(--red-bg);color:var(--red);border-color:var(--red-bd)}.t-blue{background:var(--blue-bg);color:var(--blue);border-color:var(--blue-bd)}
.t-purple{background:var(--purple-bg);color:var(--purple);border-color:var(--purple-bd)}.t-gray{background:var(--gray-bg);color:var(--gray);border-color:var(--gray-bd)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:16px}
.kpi{border:1px solid var(--bd);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;background:var(--head)}
.kpi span{color:var(--muted);font-size:12.5px;font-weight:550}.kpi b{font-size:28px;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1.25}
.kpi b small{font-size:15px;color:var(--muted);font-weight:550}.kpi em{font-style:normal;color:var(--muted);font-size:12.5px}
.kpi.k-green b{color:var(--green)}.kpi.k-red b{color:var(--red)}
section{margin-top:40px;scroll-margin-top:20px}h2{font-size:18px;margin:0 0 6px;letter-spacing:-.01em}h2.mt{margin-top:28px}h3{font-size:14px;margin:22px 0 10px}
.lead{color:var(--sub);margin:0 0 14px;max-width:860px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;box-shadow:0 1px 2px rgba(16,24,40,.04);overflow:hidden}.card.pad{padding:14px 18px}.card.pad p{margin:0}.scroll{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--bdf);vertical-align:top}
thead th{background:var(--head);color:var(--sub);font-size:12px;font-weight:600;white-space:nowrap}tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}
table.tight td{padding:7px 12px}.muted{color:var(--muted)}.small{font-size:12px}.ok{color:var(--green);padding:14px 18px;margin:0;font-weight:550}
.pill{display:inline-flex;align-items:center;height:22px;padding:0 9px;border-radius:999px;font-size:11.5px;font-weight:600;border:1px solid;white-space:nowrap;margin-right:6px}
.lcs{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.lc{display:block;background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 16px;text-decoration:none;color:inherit;transition:border-color .12s}
.lc:hover{border-color:var(--brand)}.lh{display:flex;justify-content:space-between;align-items:center}.lc p{color:var(--muted);font-size:12.5px;margin:6px 0 10px;min-height:38px}
.bar{display:flex;height:8px;border-radius:999px;overflow:hidden;background:var(--bdf)}.b-pass{background:var(--green)}.b-skip{background:var(--amber)}.b-fail{background:var(--red)}
.lf{display:flex;gap:12px;font-size:12px;color:var(--sub);margin-top:8px;flex-wrap:wrap}.lf .muted{margin-left:auto}
.list .issue{display:grid;grid-template-columns:140px minmax(0,1fr);gap:12px;padding:12px 16px;border-bottom:1px solid var(--bdf)}.list .issue:last-child{border-bottom:0}
.lay{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:5px}
.det{margin-top:6px;font:12px "JetBrains Mono",ui-monospace,monospace;color:var(--sub);background:var(--head);border:1px solid var(--bdf);border-radius:8px;padding:6px 9px;white-space:pre-wrap;word-break:break-word}
.mini{margin:6px 0 0;padding-left:18px;font-size:12.5px;color:var(--sub)}.mini li{margin:2px 0}
.fix{margin-top:6px;font-size:12.5px;color:var(--sub)}
details{background:var(--card);border:1px solid var(--bd);border-radius:10px;margin-bottom:8px;overflow:hidden}
summary{cursor:pointer;padding:10px 14px;display:flex;gap:8px;align-items:center;list-style:none}summary::-webkit-details-marker{display:none}
summary::before{content:"";flex:none;width:7px;height:7px;border-right:2px solid var(--muted);border-bottom:2px solid var(--muted);transform:rotate(-45deg);margin:0 4px 0 2px;transition:transform .12s}
details[open]>summary::before{transform:rotate(45deg)}
summary .muted{margin-left:auto;font-size:12px}details[open] summary{border-bottom:1px solid var(--bdf)}
.matrix th:first-child{position:sticky;left:0;background:var(--card);min-width:190px;z-index:1}.matrix td{min-width:150px}.matrix td.na{color:var(--muted);text-align:center}
.matrix td.bad{background:var(--red-bg)}.acts{display:flex;flex-wrap:wrap;gap:4px}
.acts i{font-style:normal;font-size:11px;font-weight:600;padding:1px 7px;border-radius:6px;background:var(--blue-bg);color:var(--blue)}
.scope{margin-top:5px;font-size:11.5px;color:var(--muted);font-family:"JetBrains Mono",ui-monospace,monospace;word-break:break-word}
.items{display:grid;gap:10px}.item{display:grid;grid-template-columns:58px minmax(0,1fr);background:var(--card);border:1px solid var(--bd);border-radius:12px;overflow:hidden}
.iid{background:var(--head);display:grid;place-items:center;font-weight:700;color:var(--sub);font-size:12.5px;border-right:1px solid var(--bdf)}
.ib{padding:12px 16px}.ib p{margin:6px 0}.ih{display:flex;align-items:center;flex-wrap:wrap;gap:2px}
.kind{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-right:8px}
.note{margin:8px 0 0;padding:8px 11px;border-radius:8px;font-size:13px;color:var(--sub);background:var(--head);border:1px solid var(--bdf)}
.note.n-needs-review{background:var(--amber-bg);border-color:var(--amber-bd);color:var(--amber)}
.proofs{list-style:none;margin:8px 0 0;padding:8px 0 0;border-top:1px dashed var(--bd);font-size:13px;color:var(--sub)}.proofs li{padding:2px 0}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;padding:14px}
figure{margin:0;border:1px solid var(--bd);border-radius:10px;overflow:hidden;background:var(--head)}figure img{display:block;width:100%;height:auto}
figcaption{padding:7px 10px;font-size:12px;color:var(--sub);text-transform:capitalize}
.checks{margin:0;padding-left:20px}.checks li{margin:4px 0}
.tl{list-style:none;margin:0 0 0 6px;padding:0;border-left:2px solid var(--bd)}.tl li{position:relative;padding:4px 0 10px 18px}
.tl li::before{content:"";position:absolute;left:-7px;top:9px;width:12px;height:12px;border-radius:50%;background:var(--green);border:2px solid var(--ground)}
.tl li.s-fail::before{background:var(--red)}.tl li.s-skip::before{background:var(--amber)}
.ph{font-size:11px;color:var(--muted);margin-right:8px;text-transform:uppercase;letter-spacing:.06em}
footer{margin-top:44px;color:var(--muted);font-size:12px}
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", required=True)
    a = ap.parse_args(argv)
    D = gather(a.workspace)
    md = to_md(D)
    d = os.path.join(a.workspace, ".zas")
    with open(os.path.join(d, "build_report.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(d, "build_report.html"), "w", encoding="utf-8") as f:
        f.write(to_html(D))
    print(md)
    print(f"\n→ {os.path.join(d, 'build_report.html')}")
    return D["code"]


if __name__ == "__main__":
    sys.exit(main())
