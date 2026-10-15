"""Append one build step to <ws>/.zas/build_log.json (read by zas_test.report).

    python3 -m zas_test.log --workspace <ws> --phase 5 --step "ws_migrate" --status ok [--detail "..."]
"""

import argparse
import json
import os
import sys
import time


def path(ws):
    return os.path.join(ws, ".zas", "build_log.json")


def load(ws):
    try:
        with open(path(ws), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def append(ws, phase, step, status, detail=""):
    entries = load(ws)
    entries.append({"phase": int(phase), "step": step, "status": status, "detail": detail,
                    "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    os.makedirs(os.path.dirname(path(ws)), exist_ok=True)
    with open(path(ws), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=1, ensure_ascii=False)
    return entries


def latest(entries):
    """Last entry per (phase, step), plus how many earlier attempts it had."""
    out, tries = {}, {}
    for e in entries:
        k = (e["phase"], e["step"])
        tries[k] = tries.get(k, 0) + 1
        out[k] = {**e, "attempts": tries[k]}
    return [out[k] for k in sorted(out, key=lambda k: (k[0], [x["step"] for x in entries].index(k[1])))]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--phase", required=True, type=int)
    ap.add_argument("--step", required=True)
    ap.add_argument("--status", required=True, choices=["ok", "fail", "skip"])
    ap.add_argument("--detail", default="")
    a = ap.parse_args(argv)
    append(a.workspace, a.phase, a.step, a.status, a.detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
