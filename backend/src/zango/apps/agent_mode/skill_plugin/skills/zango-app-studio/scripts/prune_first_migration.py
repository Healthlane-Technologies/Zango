#!/usr/bin/env python3
"""
Remove package-owned models from a fresh tenant's first app migration.

    python3 <skill>/scripts/prune_first_migration.py <workspace>/migrations/0001_initial.py [--check]

Why: on a newly provisioned tenant, `ws_makemigration` sweeps the models the appbuilder/crud/
workflow packages own into the app's `0001_initial` (they share the `dynamic_models` app label
and there is no earlier app migration to diff against). Their tables already exist, created by
the package migrations at install, so `ws_migrate` then fails with
`relation "dynamic_models_workflowfile" already exists`. `--fake-initial` does not help: the
migration mixes those tables with the app's genuinely new ones.

What it does: drops every operation that creates or alters one of PACKAGE_MODELS (CreateModel
by `name=`, AddField/AlterField/AddIndex/... by `model_name=`), keeps everything else in its
original order and formatting, and writes a `.bak` beside the file first. It then fails if any
kept operation still points at a pruned model (an FK from an app model to a package model
would need a dependency on the package's migration instead; stop and report that).

--check only reports what it would remove (exit 1 if anything would be).
"""
import argparse
import ast
import re
import shutil
import sys

# The package-owned models ws_makemigration is known to sweep in. Extend this set if a newer
# package adds one (the ws_migrate error names the table: dynamic_models_<model lowercased>).
PACKAGE_MODELS = {
    "WorkflowFile", "WorkflowState", "WorkflowTransaction", "WorkflowTransactionFile",
    "DataUploadModel",
}


def _kw(call, name):
    for k in call.keywords:
        if k.arg == name and isinstance(k.value, ast.Constant):
            return k.value.value
    return None


def _target(call):
    """The model an operation acts on: CreateModel/DeleteModel use name=, the rest model_name=."""
    return _kw(call, "model_name") or _kw(call, "name")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    src = open(a.path).read()
    tree = ast.parse(src)
    ops = next((n.value for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "operations" for t in n.targets)
                and isinstance(n.value, ast.List)), None)
    if ops is None:
        sys.exit(f"{a.path}: no `operations = [...]` list found")

    pkg = {m.lower() for m in PACKAGE_MODELS}
    drop = [op for op in ops.elts if isinstance(op, ast.Call) and str(_target(op) or "").lower() in pkg]
    names = [f"{op.func.attr}({_target(op)})" for op in drop if isinstance(op.func, ast.Attribute)]
    if not drop:
        print(f"{a.path}: nothing to prune (no package-owned models found)")
        return
    print(f"{a.path}: package-owned operations: {', '.join(names)}")
    if a.check:
        sys.exit(1)

    lines = src.splitlines(keepends=True)
    cut = set()
    for op in drop:                                   # whole-line ranges, incl. the trailing comma
        cut.update(range(op.lineno - 1, op.end_lineno))
    out = "".join(l for i, l in enumerate(lines) if i not in cut)

    kept = ast.parse(out)                             # still valid Python, and no dangling FK
    pattern = re.compile(r"['\"](?:dynamic_models\.)?(%s)['\"]" % "|".join(PACKAGE_MODELS), re.I)
    dangling = sorted({m.group(1) for m in pattern.finditer(out)})
    if dangling:
        sys.exit(f"{a.path}: NOT written: kept operations still reference {dangling}. An app model "
                 "points at a package model; add a dependency on the package migration instead "
                 "and report it.")
    del kept

    shutil.copy2(a.path, a.path + ".bak")
    open(a.path, "w").write(out)
    print(f"{a.path}: removed {len(drop)} operation(s); original kept at {a.path}.bak")


if __name__ == "__main__":
    main()
