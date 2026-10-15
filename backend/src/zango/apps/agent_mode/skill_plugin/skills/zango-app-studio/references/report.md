# The build report (Phase 7, the last step)

The user gets one report, built by `python -m zas_test.report --workspace <ws>` from files the
earlier phases wrote. It writes `<ws>/.zas/build_report.html`, a designed, self-contained page (brand
colour from the spec, light/dark, sticky section nav, screenshots embedded as downscaled JPEGs, no external
assets, so it can be mailed or attached as is), and `<ws>/.zas/build_report.md` (the summary as text).

HTML sections: verdict banner with its reasons and four summary tiles (checks, scenarios, custom items,
what was built) · Open the app (URL, test users, landing page, menu per role) · Tests (a card per layer
with a pass/skip/fail bar; **Needs attention** lists blocking failures, then skips, then non-blocking
failures folded per kind; every check grouped and expandable) · Access by role (entity × role matrix of
actions and row scope; a red cell has a failing check) · Plain-language items (status, kind, spec text,
target, the `zas:note`, and the scenarios that prove it) · Spec review (errors, intent findings, warnings,
each with the fix) · What was built (modules, entities, endpoints, workflow sizes, pages) · Screens (per
role) · Manual steps, build timeline, re-running. Put the Markdown summary in your
final message and give the path to the HTML.

Inputs: `.zas/spec.resolved.json`, `.zas/issues.md`, `.zas/holes.md`, `.zas/test_results.json`,
`.zas/build_log.json` (one entry per phase step, below), `.zas/test_users.json` (emails only).

## Sections, in order

1. **Verdict.** One line, one of: *Ready*, meaning every blocking check passed (api, ui, design and
   scenarios), no hole is `todo`, and there are no skips, review items or intent findings. *Ready with gaps*, meaning blocking checks passed and some holes are `blocked` or
   `needs-review`, or non-blocking checks failed. *Not ready*, meaning a blocking check failed,
   listed right under the verdict.
2. **How to open it.** The app URL, the test users (email + role; passwords stay in the file),
   and the landing page per role.
3. **What was built.** Modules → entities → pages, with counts of policies, routes, menus,
   holes and tests. Then the spec-to-code map: each entity's model, CrudView, table, forms,
   workflow, detail class and endpoint.
4. **Spec warnings** from `issues.md`, each with its spec path and the fix the checker
   suggested. Errors never reach a report: the build stops at Phase 1.
5. **Plain-language items.** Every hole: ID, spec path, text, target, status. Show
   `needs-review` guesses and `blocked` dependencies in full ("GST lookup: needs API endpoint and
   credentials in App Panel → Secrets").
6. **Tests.** Per layer (api, ui, design): pass/fail/skip counts, then every failure and skip
   with its spec path and detail. Skips always carry a reason ("preview parity: Studio has no
   deep link yet").
7. **Manual steps left.** Only things the skill cannot do itself: scheduled tasks with no
   `# zas:schedule` line (the spec text gave no timing), secrets to add,
   notification provider to wire (`zas_core/notify.py send_via_provider`), and known runtime
   gaps (`footer_totals`).
8. **Re-running.** `spec_check.py … --workspace <ws>` after editing the YAML, then the phases
   from 2. Hand-written hooks and slots are kept, and the holes audit shows what changed.

## `build_log.json`

Every phase step appends `{"phase": n, "step": "...", "status": "ok|fail|skip", "detail": "...",
"at": "..."}`. Use `python -m zas_test.log --workspace <ws> --phase 5 --step "ws_migrate" --status ok`.
A step that failed and was fixed gets two entries. The report shows the last one and counts
the retries.

## Honesty rules

- Never write *Ready* while any blocking test fails, any hole is `todo`, or routes/menus
  were not read back.
- A skipped check is not a pass. Say why it was skipped.
- Report each fix you made to the spec's intent (a renamed field, a dropped column) as a
  change, with the reason. Silent fixes are not allowed.
