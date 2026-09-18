#!/usr/bin/env python3
"""Guard SKILL.md edits: rules and their force must survive compression.

A literal diff proves no API name vanished. It does NOT prove the instruction
still binds. These four checks cover the ways compression silently weakens a
skill: dropped rule, dropped consequence, dropped emphasis, dropped link.
"""
import re, sys, pathlib

BASE = pathlib.Path(sys.argv[1]); NOW = pathlib.Path(sys.argv[2])
b, n = BASE.read_text(), NOW.read_text()
fail = []

# 1. code literals: API names, flags, paths, component names
# inline code only: no newlines inside, and strip fenced blocks first
strip = lambda s: re.sub(r'```.*?```', '', s, flags=re.S)
lit = lambda s: set(re.findall(r'`([^`\n]+)`', strip(s)))
# crud.md was deliberately split into crud/{core,tables,detail,hooks}.md
EXPECTED_GONE = {
    'frontend/crud.md', 'crud.md',
    # npm allowlist: verified present in BOTH prompt.py frontend_rule (told to
    # the agent every run) and guards.py (enforced). Duplicating it in the
    # skill added nothing.
    'echarts', 'echarts-for-react', 'recharts', 'date-fns', 'clsx',
    'tailwind-merge', 'npm run build', 'npm run build:zango',
    # the appbuilder shell line, quoted only as an example of what NOT to
    # copy; both greppable tells for it are still present.
    "{% zstatic 'packages/appbuilder/js/build.'|add:build_version|add:'.js' %}",
}
lb, ln = lit(b), lit(n)
lost = lb - ln - EXPECTED_GONE
if lost: fail.append(f"LOST literals ({len(lost)}): {sorted(lost)}")

# 2. consequence clauses -- the "or X breaks" that makes a rule bind
def consequences(s):
    pat = r'(?:, or |—|--)\s*(?:the |it |and )?[^.\n]*(?:renders blank|404|403|fails|breaks|dead links|no-op|silently|never appears|is a defect|blocker)[^.\n]*'
    return {re.sub(r'\s+',' ',m).strip().lower() for m in re.findall(pat, s)}
cb, cn = consequences(b), consequences(n)
if cb - cn: fail.append(f"LOST consequences ({len(cb-cn)}): {sorted(cb-cn)[:6]}")

# 3. imperative force
for w in ["never","must","mandatory","always","required","exactly","not optional","MUST"]:
    x, y = len(re.findall(re.escape(w), b)), len(re.findall(re.escape(w), n))
    if y < x: fail.append(f"WEAKER '{w}': {x} -> {y}")

# 4. reference links
def links(s): return set(re.findall(r'\(references/[^)]+\)', s))
lost_links = links(b) - links(n) - {'(references/frontend/crud.md)'}
if lost_links: fail.append(f"LOST links: {sorted(lost_links)}")

print(f"lines {b.count(chr(10))} -> {n.count(chr(10))}")
if fail:
    print("\n".join("FAIL " + f for f in fail)); sys.exit(1)
print("PASS - every rule, consequence, emphasis marker and link preserved")
