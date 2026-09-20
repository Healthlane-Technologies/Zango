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
    # Frontend delegation (5c/5d/5e dispatching Task/Agent subagents) was
    # removed outright: measured worse than writing inline on every real run
    # (parallel dispatch re-read the same shared reference material once per
    # page, 3-9x'ing cache-creation/output/thinking for a net cost increase
    # over a zero-delegation baseline). These literals only existed to name
    # the dispatch-and-wait protocol (TaskOutput/agentId) and the on-disk
    # check for subagent output; with no subagent, there is nothing to wait
    # on or verify against a background write.
    'TaskOutput', 'agentId', 'find', 'ls', 'ls frontend/src/custom/pages/',
    'Read',
    # design-system.md was deleted after a rule-by-rule audit: 17 of its 19
    # rules were already stated in 3-7 other files each (max-md grid rule,
    # four states, primitive list, PageShell placement, module scope, anchor,
    # tier-2 pages, Tailwind-not-inline, responsive floor, tabular-nums,
    # money/locale, lucide, Inter, the six brief questions, direction). The
    # two genuinely unique items were MOVED before the delete: the two
    # measurement snippets -> verify-gate.md items 21/22, and the copy rules
    # -> shared-primitives.md. Its npm allowlist was already in prompt.py
    # (told to the agent every run) and enforced in guards.py. What is gone
    # is ~19 narrated failure anecdotes, which bound no rule.
    'design-system.md',
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
#
# A marker may be deliberately retired when the rule it was binding was
# itself wrong. Each entry below is one such removal, with the reason --
# the count is allowed to drop by exactly the number of entries for that
# word, and no further.
RETIRED_EMPHASIS = {
    # "inline is always correct" made delegation of 5c-5e unreachable in
    # practice: two consecutive runs dispatched 0 and 1 subagents, wrote the
    # frontend inline from a context already carrying the whole backend
    # phase, and one peaked at 359k -> compacted mid-build. Delegation is
    # now the default with two named fallbacks; the 5f on-disk gate, not
    # inline-by-default, is what makes it safe.
    "always": 1,
    # Frontend delegation was removed outright (see EXPECTED_GONE above) --
    # measured worse than writing inline on every real run. The 2 "never"
    # drops are rules that only made sense with subagents in the picture
    # ("never let parallel agents edit index.js", "the gate is never
    # delegated" -- meaningless with nothing to delegate to). The 1 "must"
    # drop is the dispatch protocol's own "the rules below are what must end
    # up in the file" framing device, not a rule about the file's content.
    "never": 2,
    "must": 1,
}
for w in ["never","must","mandatory","always","required","exactly","not optional","MUST"]:
    x, y = len(re.findall(re.escape(w), b)), len(re.findall(re.escape(w), n))
    allowed = RETIRED_EMPHASIS.get(w, 0)
    if y < x - allowed:
        fail.append(f"WEAKER '{w}': {x} -> {y} (allowed drop: {allowed})")

# 4. reference links
def links(s): return set(re.findall(r'\(references/[^)]+\)', s))
# The STEP 3 reference index points at DIRECTORIES, not files, so the agent
# must list one and choose from its README before it can read anything. A
# resolved file path in that table is an immediately actionable Read, and the
# agent front-loads the whole table during planning -- measured: 13 reference
# docs read back-to-back before a single line of code, ~71% of one run's
# cache-read bill. Directory rows broke that batch (13 reads / 0 writes ->
# 5 reads / write / 4 reads). Every file below is still reachable, one hop
# later, via its directory's README.md index -- and any file still named at
# its point of use inside a STEP keeps its link.
DIR_INDEXED = {
    '(references/core/models.md)', '(references/core/policies.md)',
    '(references/core/async-tasks.md)', '(references/core/secrets.md)',
    '(references/packages/crud/views/core.md)',
    '(references/packages/crud/views/reference.md)',
    '(references/packages/crud/views/troubleshooting.md)',
    '(references/packages/crud/forms/core.md)',
    '(references/packages/crud/forms/examples.md)',
    '(references/packages/crud/tables/core.md)',
    '(references/packages/crud/tables/advanced.md)',
    '(references/packages/workflow/overview.md)',
    '(references/packages/workflow/statuses.md)',
    '(references/packages/workflow/transitions.md)',
    '(references/packages/workflow/tags.md)',
    '(references/packages/workflow/utils.md)',
    '(references/packages/workflow/advanced.md)',
    '(references/frontend/crud/tables.md)',
    '(references/frontend/crud/hooks.md)',
}
# design-system.md: deleted, see EXPECTED_GONE. Its two unique items moved to
# verify-gate.md (the measurement snippets) and shared-primitives.md (the copy
# rules); every other rule it held was already stated in 3-7 other files.
DELETED_DOCS = {'(references/frontend/design-system.md)'}
lost_links = (links(b) - links(n) - {'(references/frontend/crud.md)'}
              - DIR_INDEXED - DELETED_DOCS)
if lost_links: fail.append(f"LOST links: {sorted(lost_links)}")

print(f"lines {b.count(chr(10))} -> {n.count(chr(10))}")
if fail:
    print("\n".join("FAIL " + f for f in fail)); sys.exit(1)
print("PASS - every rule, consequence, emphasis marker and link preserved")
