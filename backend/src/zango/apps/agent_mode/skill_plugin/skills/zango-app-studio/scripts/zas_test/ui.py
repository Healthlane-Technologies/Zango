"""
Layer 2: the app in a real headless browser (Python Playwright), per role, checked against the spec.
It proves what the API layer cannot: pages render, the right controls are on screen for each role,
and the 360 shows what the spec lays out. Run after the API layer (which leaves records to open in
<ws>/.zas/test_records.json).

    python3 -m zas_test.ui --workspace <ws> [--role "Finance"] [--only login,pages,detail]

Groups:
  login    anonymous /app/ shows the branded login (data-zas="login"), not the stock one
  pages    per role × page in its menu: page renders ([data-zas="page"]), no console errors / 5xx,
           Add button shown iff the role can add, quick-filter chips = spec chips for the role,
           every menu label is on screen; screenshot → .zas/screens/<role>/<page>.png
  detail   per 360 × role: viewers see header + stats + the tabs the role may see, in spec order;
           others see the no-access state; no header banner is blank; every tab opens without error
           and is not blank;
           screenshot → .zas/screens/<role>/<view>.png
  flows    the journeys end to end, checked on screen and in the backend after each step: create
           from the list page, every manual workflow move from the 360, child adds from 360 tabs
           (zas_test/flows.py)
Results: <ws>/.zas/test_results.json (layer "ui"). Exit 1 when any check fails.
"""

import argparse
import json
import os
import re
import sys

from . import auth, browser, in_scope, load_json, print_summary, save_results

GROUPS = ["login", "pages", "detail", "flows"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


class UI:
    def __init__(self, ws, roles_filter=None):
        self.ws = ws
        self.M = load_json(ws, "spec.resolved.json")
        self.users = auth.load_users(ws)
        self.target = self.users.get("target")
        if not self.target:
            raise SystemExit(f"no target in {auth.users_path(ws)}: run zango_platform.py users first")
        try:
            self.records = load_json(ws, "test_records.json")
        except (OSError, ValueError):
            self.records = {}
        self.roles = [r for r in self.M["roles"] if r not in ("AnonymousUsers", "SystemUsers")
                      and (not roles_filter or r in roles_filter)]
        self.results = []

    def add(self, id, title, role, path, status, detail=""):
        self.results.append({"layer": "ui", "id": id, "title": title, "role": role, "spec_path": path,
                             "status": status, "detail": str(detail)[:600]})

    def check(self, id, title, role, path, fn):
        if not in_scope(path):
            return
        try:
            good, detail = fn()
            self.add(id, title, role, path, "pass" if good else "fail", "" if good else detail)
        except SkipCheck as e:
            self.add(id, title, role, path, "skip", e)
        except Exception as e:
            self.add(id, title, role, path, "fail", repr(e)[:500])

    def can(self, ent, role, action):
        E = self.M["entities"][ent]
        if not E.get("access"):
            return True
        a = (E.get("access_resolved") or {}).get(role)
        return bool(a) and not a.get("none") and action in a["actions"]

    def menu_pages(self, role):
        out = []
        for it in self.M["roles"][role].get("menu", []):
            for i in (it.get("items") or [it]):
                if i.get("page"):
                    out.append((i["page"], i.get("label") or self.M["pages"][i["page"]].get("title") or i["page"]))
        return out


class SkipCheck(Exception):
    pass


def g_login(U, b):
    def t():
        rp = browser.RolePage(b, U.target)
        try:
            rp.open("/app/", wait='[data-zas="login"], form')
            has = rp.page.locator('[data-zas="login"]').count() > 0
            rp.shot(U.ws, "anonymous", "login")
            return has, "the stock appbuilder login rendered instead of ZasLogin (App.tsx authConfig / app.html build?)"
        finally:
            rp.close()
    U.check("ui.login", "branded login page", None, "app", t)


def g_pages(U, b):
    for role in U.roles:
        try:
            s = auth.login(U.ws, role)
        except auth.AuthError as e:
            U.add(f"ui.login.{slug(role)}", f"log in as {role}", role, f"roles.{role}", "fail", e)
            continue
        rp = browser.RolePage(b, U.target, s)
        try:
            pages = U.menu_pages(role)
            for code, label in pages:
                P = U.M["pages"][code]
                path = f"pages.{code}"

                def t_page(code=code, P=P):
                    rp.open(P["route"])
                    root = rp.page.locator(f'[data-zas="page"][data-zas-key="{code}"]')
                    if root.count() == 0:
                        return False, f"no [data-zas=page][data-zas-key={code}] (export {P['export']} missing from pages/index.ts or the build?)"
                    rp.shot(U.ws, slug(role), code)
                    body = rp.page.inner_text("body")
                    if "is not implemented yet" in body:
                        return False, "a hole is shown as not implemented"
                    probs = list(rp.errors)
                    if browser.raw_dates(body):
                        probs.append(browser.raw_dates(body))
                    if P.get("type") == "crud" and not browser.rebuilt(U.M, "page", code):
                        E = U.M["entities"][P["entity"]]
                        add_label = (E.get("table") or {}).get("add_button") or E["names"].get("add_label") or f"Add {E['name']}"
                        cr = (E.get("form") or {}).get("create") or {}
                        want_add = U.can(P["entity"], role, "add") and (not cr.get("roles") or role in cr["roles"])
                        # the kit's Add button, not any button with that text: a status chip can share the label
                        has_add = rp.page.locator('[data-zas="action"][data-zas-key="add"]').count() > 0
                        if want_add != has_add:
                            probs.append(f"Add button {'missing' if want_add else 'shown'} (looked for {add_label!r})")
                        qfs = [q["label"] for q in (E.get("table") or {}).get("quick_filters", []) if not q.get("roles") or role in q["roles"]]
                        chips = [re.sub(r"\s*\d[\d,]*$", "", c.strip())  # "Open 7": the count is not the label
                                 for c in rp.page.locator('[data-zas="quick-filter"]').all_inner_texts()]
                        if chips != qfs:
                            probs.append(f"quick filters {chips} != spec {qfs}")
                        for i, label in enumerate(chips):  # each chip lists rows (run 8: "All" was a 500)
                            rp.page.locator('[data-zas="quick-filter"]').nth(i).click()
                            rp.page.wait_for_timeout(600)
                            if rp.page.locator('[data-zas="load-error"]').count():
                                probs.append(f"the {label!r} chip fails to list: "
                                             f"{rp.page.locator('[data-zas=load-error]').first.inner_text()[:120]}")
                    return not probs, "; ".join(probs)
                U.check(f"ui.page.{code}.{slug(role)}", f"{label} renders", role, path, t_page)

            def t_menu():
                rp.open(U.M["pages"][pages[0][0]]["route"]) if pages else None
                groups = [it["group"] for it in U.M["roles"][role].get("menu", []) if it.get("group")]
                for g in groups:  # menu groups start collapsed: open them before reading the items
                    try:
                        rp.page.get_by_text(g, exact=True).first.click(timeout=3000)
                        rp.page.wait_for_timeout(300)
                    except Exception:
                        pass
                # inner_text applies CSS text-transform: a group heading styled uppercase reads
                # "LIBRARY", so compare without case.
                text = rp.page.inner_text("body").casefold()
                missing = [lbl for _, lbl in pages if lbl.casefold() not in text]
                missing += [g for g in groups if g.casefold() not in text]
                return not missing, f"not on screen: {missing}"
            if pages:
                U.check(f"ui.menu.{slug(role)}", "menu items on screen", role, f"roles.{role}.menu", t_menu)
        finally:
            rp.close()


def g_detail(U, b):
    for vcode, V in (U.M.get("detail_views") or {}).items():
        hero = V["hero"]
        uids = U.records.get(hero) or []
        for role in U.roles:
            viewer = (not V.get("roles") or role in V["roles"]) and U.can(hero, role, "detail")

            def t_view(role=role, viewer=viewer, V=V, vcode=vcode, uids=uids):
                if not uids:
                    raise SkipCheck(f"no {hero} record to open: run zas_test.api first")
                s = auth.login(U.ws, role)
                uid = browser.visible_uid(U.M, hero, s, uids) if viewer else uids[-1]
                path = browser.detail_path(U.M, hero, uid)
                rp = browser.RolePage(b, U.target, s)
                try:
                    rp.open(path, wait='[data-zas="header"], [data-zas="empty"]')
                    rp.page.wait_for_timeout(300)
                    rp.shot(U.ws, slug(role), vcode)
                    if not viewer:
                        st = rp.page.locator('[data-zas="empty"][data-zas-key="no_access"], [data-zas="empty"][data-zas-key="not_found"]').count()
                        return st > 0, "a non-viewer was shown the page"
                    if rp.page.locator('[data-zas="header"]').count() == 0:
                        return False, "no header (not_found? row scoping?)"
                    probs = list(rp.errors)
                    blank = rp.page.eval_on_selector_all('[data-zas="banner"]', "els => els.filter(e => !e.innerText.trim()).length")
                    if blank:
                        probs.append(f"{blank} header banner(s) with no text")
                    want_tabs = [t["code"] for t in V.get("tabs") or []
                                 if (not t.get("roles") or role in t["roles"])
                                 and (t.get("type") != "related_table" or U.can(t["entity"], role, "view"))]
                    got_tabs = rp.page.eval_on_selector_all('[data-zas="tab"]', "els => els.map(e => e.dataset.zasKey)")
                    extra = [x for x in got_tabs if x not in want_tabs]
                    if extra or [x for x in want_tabs if x in got_tabs] != got_tabs:
                        probs.append(f"tabs {got_tabs} vs spec {want_tabs}")
                    for code in got_tabs:
                        rp.errors.clear()
                        rp.page.locator(f'[data-zas="tab"][data-zas-key="{code}"]').first.click()
                        rp.page.wait_for_load_state("networkidle")
                        rp.page.wait_for_timeout(200)
                        body = rp.page.locator('[data-zas="page"]').first.inner_text()
                        if "is not implemented yet" in body:
                            probs.append(f"tab {code}: hole not implemented")
                        if browser.raw_dates(body):
                            probs.append(f"tab {code}: {browser.raw_dates(body)}")
                        if rp.errors:
                            probs.append(f"tab {code}: {rp.errors[:2]}")
                        rp.shot(U.ws, slug(role), f"{vcode}__{code}")
                    return not probs, "; ".join(probs)
                finally:
                    rp.close()
            U.check(f"ui.detail.{vcode}.{slug(role)}", f"{vcode} {'renders' if viewer else 'refused'}", role, f"detail_views.{vcode}", t_view)


def g_flows(U, b):
    from .flows import g_flows as run
    run(U, b)


RUNNERS = {"login": g_login, "pages": g_pages, "detail": g_detail, "flows": g_flows}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--only")
    ap.add_argument("--role", action="append")
    a = ap.parse_args(argv)
    groups = [g for g in (a.only or ",".join(GROUPS)).split(",") if g]
    U = UI(a.workspace, a.role)
    with browser.browser() as b:
        for g in groups:
            RUNNERS[g](U, b)
    save_results(a.workspace, "ui", U.results, {"groups": groups})
    print_summary("ui", U.results)
    return 1 if any(r["status"] == "fail" for r in U.results) else 0


if __name__ == "__main__":
    sys.exit(main())
