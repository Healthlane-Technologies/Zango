"""zas_test - generated tests for an App Studio app. See references/testing.md.

    python3 -m zas_test.api    --workspace <ws>   # layer 1: API checks from the spec
    python3 -m zas_test.ui     --workspace <ws>   # layer 2: Playwright specs (generate + run)
    python3 -m zas_test.design --workspace <ws>   # design checks (lint, gallery, tokens, tree, layout)

Run from <skill>/scripts (or put it on PYTHONPATH). Needs `pip install requests`;
the UI and design layers need Node + `@playwright/test` in frontend/.
Results from every layer go to <ws>/.zas/test_results.json.
"""

import json
import os
import time

RESULTS = "test_results.json"


def results_path(ws):
    return os.path.join(ws, ".zas", RESULTS)


def load_results(ws):
    try:
        with open(results_path(ws), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"runs": {}, "results": []}


def save_results(ws, layer, results, meta=None):
    """Replace this layer's results in .zas/test_results.json, keep the other layers'."""
    data = load_results(ws)
    data["results"] = [r for r in data.get("results", []) if r.get("layer") != layer] + results
    data.setdefault("runs", {})[layer] = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), **(meta or {}),
                                          "counts": counts(results)}
    os.makedirs(os.path.dirname(results_path(ws)), exist_ok=True)
    with open(results_path(ws), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, default=str)
    return data


def counts(results):
    c = {"pass": 0, "fail": 0, "skip": 0}
    for r in results:
        c[r["status"]] = c.get(r["status"], 0) + 1
    return c


def print_summary(layer, results):
    c = counts(results)
    print(f"\n[{layer}] {c['pass']} passed, {c['fail']} failed, {c['skip']} skipped")
    for r in results:
        if r["status"] == "fail":
            who = f" [{r['role']}]" if r.get("role") else ""
            print(f"  FAIL {r['id']}{who} {r['title']}\n       {r.get('spec_path', '')}: {r.get('detail', '')}")


def load_json(ws, name):
    with open(os.path.join(ws, ".zas", name), encoding="utf-8") as f:
        return json.load(f)
