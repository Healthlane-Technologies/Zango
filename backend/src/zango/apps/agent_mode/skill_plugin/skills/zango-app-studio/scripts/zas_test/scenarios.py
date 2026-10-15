"""
Layer "scenarios": behaviour tests for the spec's plain-language items (holes), written by Claude
per app in <ws>/.zas/test_scenarios.py (references/testing.md §Scenarios).

The generated API layer proves what the spec states structurally (who may do what, which rows).
It cannot know what "Set when the site is active and (no enrollment for 60 days, or an open
critical issue …)" means. A scenario reads that text and checks it end to end: set up the data,
trigger the rule (a transition, a save, a scheduled job), assert the outcome (a tag, a field, a
message, a refused action).

    python3 -m zas_test.scenarios --workspace <ws> [--only H-10,H-17] [--list]

test_scenarios.py:

    from zas_test.scenarios import scenario

    @scenario("H-10", "an active site with an open critical issue is flagged At Risk")
    def at_risk_on_critical_issue(ctx):
        site = ctx.record_in("site", "active")
        ctx.create("site_issue", "CRA", {"site": ctx.pk("site", site), "severity": "critical", ...})
        ctx.call("sites.tasks.site__req__2")           # the nightly job, now
        ctx.expect("at_risk" in ctx.tags("site", site), "at_risk not set")

A scenario passes when it returns, fails on AssertionError (ctx.expect) or any exception, and is
skipped with ctx.skip("reason"). Every hole that is `done`/`needs-review` and has no scenario is
listed as a skip ("no scenario"), so coverage gaps show in the report.
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import traceback

from . import load_json, print_summary, save_results
from .api import Ctx, Skip

_REGISTRY = []
HERE = os.path.dirname(os.path.abspath(__file__))


def scenario(hole, title, roles=None):
    """Register a scenario for hole H-NN (or a spec path such as 'entities.site.access')."""
    def deco(fn):
        _REGISTRY.append({"hole": hole, "title": title, "fn": fn, "roles": roles})
        return fn
    return deco


class ScenarioCtx(Ctx):
    """api.Ctx (create, run, record_in, rows, get/post as a role, fixtures) plus scenario helpers."""

    # ── backend ──
    def call(self, target, *args):
        """Run backend.<target>(*args) in the app's tenant (a scheduled job, a hook). Returns its JSON result."""
        cmd = [sys.executable, os.path.join(HERE, "..", "zango_env.py"), "call", "--workspace", self.ws, "--", target,
               *[str(a) for a in args]]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        line = next((l for l in r.stdout.splitlines() if l.startswith("ZAS_RESULT=")), None)
        if line is None:
            raise AssertionError(f"{target} failed: {(r.stderr or r.stdout)[-600:]}")
        return json.loads(line[len("ZAS_RESULT="):])

    # ── reading records ──
    def pk(self, ent, uuid):
        return str(self.record_payload(ent, uuid)["record"]["pk"])

    def record_payload(self, ent, uuid, role="__any__"):
        """The record drawer payload (contracts §8b): fields, status, tags, transitions, row actions, events."""
        roles = self.roles() if role == "__any__" else [role]
        last = None
        for r in roles:
            if r not in self.sessions or not self.can(ent, r, "view"):
                continue
            code, j = self.get(r, self.ep(ent), action="zas_record", object_uuid=uuid)
            b = self.body(j) or {}
            if b.get("access") == "ok":
                return b
            last = b.get("access")
        raise AssertionError(f"{ent} {uuid} not readable ({last})")

    def field(self, ent, uuid, key, role="__any__"):
        f = next((x for x in self.record_payload(ent, uuid, role)["fields"] if x["key"] == key), None)
        return None if f is None else f.get("value")

    def status(self, ent, uuid):
        return self.record_payload(ent, uuid)["record"]["status"]

    def tags(self, ent, uuid):
        return [t["code"] for t in self.record_payload(ent, uuid)["record"]["tags"]]

    def transitions(self, ent, uuid, role):
        """{spec transition name: allowed} as `role` sees them on this record."""
        return {t["name"]: t["allowed"] for t in self.record_payload(ent, uuid, role)["transitions"]}

    def detail(self, ent, uuid, role):
        """The 360 payload (data.zas) as `role`."""
        code, j = self.get(role, self.ep(ent), view="detail", action="fetch_item_details", object_uuid=uuid)
        return (self.body(j) or {}).get("zas") or {}

    # ── messages ──
    def mark(self):
        return time.time()

    def outbox(self, since=None, event=None):
        """Messages notify() sent (DEBUG outbox, <ws>/.zas/outbox.jsonl) since `mark()`."""
        p = os.path.join(self.ws, ".zas", "outbox.jsonl")
        out = []
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                try:
                    m = json.loads(line)
                except ValueError:
                    continue
                if (since is None or m.get("at", 0) >= since) and (event is None or m.get("event") == event):
                    out.append(m)
        return out

    # ── outcomes ──
    @staticmethod
    def expect(cond, msg):
        if not cond:
            raise AssertionError(msg)

    @staticmethod
    def skip(msg):
        raise Skip(msg)


def _registry():
    """The registry test_scenarios.py fills. Under `python -m zas_test.scenarios` this file is
    __main__, and `from zas_test.scenarios import scenario` imports a second copy: use that one."""
    import importlib
    return importlib.import_module("zas_test.scenarios")._REGISTRY


def load(ws):
    p = os.path.join(ws, ".zas", "test_scenarios.py")
    _registry().clear()
    if not os.path.exists(p):
        return False
    spec = importlib.util.spec_from_file_location("zas_test_scenarios", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--only", help="comma-separated hole ids")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    M = load_json(a.workspace, "spec.resolved.json")
    holes = {h["id"]: h for h in M.get("holes", [])}
    statuses = _hole_statuses(a.workspace)
    found = load(a.workspace)
    registry = _registry()
    only = {x.strip() for x in (a.only or "").split(",") if x.strip()}
    if a.list:
        for s in registry:
            print(f"{s['hole']:<8} {s['fn'].__name__:<44} {s['title']}")
        return 0
    C = ScenarioCtx(a.workspace)
    C.login_all()
    results = []
    for s in registry:
        if only and s["hole"] not in only:
            continue
        h = holes.get(s["hole"], {})
        res = {"layer": "scenarios", "id": f"scenario.{s['hole']}.{s['fn'].__name__}", "title": s["title"],
               "role": None, "spec_path": h.get("where", s["hole"]), "hole": s["hole"], "status": "pass", "detail": ""}
        t0 = time.time()
        try:
            s["fn"](C)
        except Skip as e:
            res.update(status="skip", detail=str(e))
        except AssertionError as e:
            res.update(status="fail", detail=str(e)[:600])
        except Exception as e:
            res.update(status="fail", detail=f"{e!r} {traceback.format_exc(limit=3)[-400:]}")
        res["seconds"] = round(time.time() - t0, 1)
        results.append(res)
        print(f"  {res['status'].upper():<4} {s['hole']:<6} {s['title']}" + (f"  ({res['detail'][:160]})" if res["detail"] else ""))
    if not only:
        covered = {s["hole"] for s in registry}
        for hid, h in holes.items():
            if hid in covered or statuses.get(hid) in ("covered", "blocked"):
                continue
            results.append({"layer": "scenarios", "id": f"scenario.{hid}.none", "title": f"{hid}: {h.get('text', '')[:90]}",
                            "role": None, "spec_path": h.get("where", hid), "hole": hid, "status": "skip",
                            "detail": "no scenario written for this item" if found else "no .zas/test_scenarios.py"})
    save_results(a.workspace, "scenarios", results, {"file": ".zas/test_scenarios.py" if found else None})
    print_summary("scenarios", results)
    return 1 if any(r["status"] == "fail" for r in results) else 0


def _hole_statuses(ws):
    out = {}
    p = os.path.join(ws, ".zas", "holes.md")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 7 and cells[0].startswith("H-"):
                out[cells[0]] = cells[-1]
    return out


if __name__ == "__main__":
    sys.exit(main())
