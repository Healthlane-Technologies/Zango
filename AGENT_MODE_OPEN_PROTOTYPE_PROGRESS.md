# Agent Mode: Open Prototype ("Free design"), implementation progress

Plan: https://claude.ai/artifact/1x8D2VWgxjKYG6N68BhnJC ("Open Prototype Plan", v4).
Branch: `feat/agent-mode-open-prototype` (from `feat/agent-mode-app-studio-skill`). Started 2026-10-23.

Goal of P1: in chat, the requirement agent generates a working HTML prototype of the app in any look
(the capability bar is a 237 KB single-file app with personas, workflows and its own tokens),
written in parts, with the YAML kept in step. The capability-bar file is NOT in the repo and must
never be added (user decision).

## Status

| P1 step | What | Status |
|---|---|---|
| Spike | SDK in-process MCP tools reach sub-agents (`AgentDefinition.mcpServers`, tool name `Agent`) | **done**: 2 parallel writers called `proto_write` (SDK 0.2.152, haiku) |
| P1.1 | Data model + migrations | **done** |
| P1.2 | Assembly (`prototype.py`) + route | **done** |
| P1.3 | `proto_*` tools on the spec server | **done** |
| P1.4 | Screen-writer sub-agent | **done** (options wired; not yet run in a real analyst turn) |
| P1.5 | Turn limits for open mode | **done** |
| P1.6 | Runtime + starter (`prototype_assets/`) | **done** |
| P1.7 | Skill `zango-prototype` + worked example | **done** |
| P1.8 | Console: toggle, `PrototypeFrame`, mode switch | **done** (type-checks; not yet clicked through live) |
| P1.9 | Tests | backend **done** (11 in `test_prototype.py`); API test todo |
| Done-when | 3 chat-only runs measured | todo |

## Backend changes

- `apps/agent_mode/models.py`: `AgentRequirement.preview_mode` ("kit" | "open"), `prototype_parts`
  (JSON {path: text}), `prototype_hash`, `prototype_revision`; `AgentRequirementVersion.prototype_parts`
  / `prototype_hash`, written by `record_spec`. Migration `0016_open_prototype`.
- `apps/shared/agent_mode/models.py`: `AgentAppScaffold.preview_mode` (migration `0006_scaffold_preview_mode`);
  `scaffold.py` passes it to the requirement; admin create view accepts `preview_mode`.
- `apps/agent_mode/prototype.py` (new):
  - part paths `^[a-z0-9][a-z0-9_.-]*(/…){0,2}\.(css|js|json)$`, 150 KB per part, 2 MB total;
  - `manifest_of` / `static_problems`: screens ↔ parts, library hosts (cdnjs, jsdelivr/npm, unpkg, pinned
    version), fonts (Google Fonts only);
  - `js_syntax_error`: `node --check` (system node, else Playwright's bundled node; skipped if none);
  - `assemble`: CSP meta → fonts → runtime CSS → tokens.css, app.css, other css, screens/*.css → body →
    manifest JSON → lucide (unpkg, pinned) → runtime JS → libraries → data.js, shell.js, other js,
    screens/*.js (manifest order) → `ZAS.boot()`. One `<script>` per part with `//# sourceURL=proto/<part>`
    so a throwing part stops only itself and errors name the part. `</script` / `</style` escaped.
  - `PrototypeBench` (outline/write/patch/read/find/remove/rename), emits `{prototype_parts, prototype_hash}`;
  - `proto_tool_specs`, `PROTO_TOOL_NAMES`, `screen_writer_agent()` (`background=False`, maxTurns 40,
    tools: outline/write/patch/read/find + Read + Skill, `mcpServers=["spec"]`).
- `apps/agent_mode/prototype_assets/zas-proto.js|css`: the runtime (ZAS.seed/screen/shell/on/go/back/
  store/files/drawer/modal/toast, helpers h/I/fmt/pill/table/tabs/field/initials, persona bar, `/_blob/`
  fetch from memory, postMessage bridge `source: 'zas-proto'` types ready/location/error; listens for
  `{source: 'zango-console', type: 'goto'}`). Packaged via `setup.py` package_data.
- `spec_tools.py`: `SpecWorkbench(proto=…)`; in open mode `issues()` drops the unsketched-screen rules;
  proto tools appended to `tool_specs`; names in `TOOL_NAMES` / `ALLOWED_TOOL_NAMES`.
- `tasks.py`: open mode builds a `PrototypeBench`, passes `probe=None` (kit probe off), and
  `_record_spec_edit` saves `prototype_parts/hash` and bumps `prototype_revision`.
- `requirements.py`: `PROTOTYPE_SKILL`, `_OPEN_PROTOTYPE_APPEND`; open mode adds `Agent`/`Task`, the
  skill, `agents={"screen-writer": …}`; first draft (no parts yet) gets max_turns 250 and
  `AGENT_MODE_ANALYST_PROTO_BUDGET_USD` (15).
- `template_spec.approval_problem`: open mode needs a prototype; `unfinished_custom_work(sketches=False)`.
- API (`agent_mode/v1`): `_seed_preview_mode` on create (explicit `preview_mode`, else the last approved
  requirement's mode; an open change starts from its prototype parts); `_dispatch_turn` gives an open
  first draft `AGENT_MODE_OPEN_FIRST_TURN_SECONDS` (1500); `GET requirements/<uuid>/prototype/[?v=N]`
  (assembled HTML, CSP + `sandbox` header, ETag); serializers add `preview_mode`, `prototype_revision`,
  `prototype_hash`; availability adds `open_prototype`.
- Settings: `AGENT_MODE_OPEN_PROTOTYPE` (True), `AGENT_MODE_OPEN_FIRST_TURN_SECONDS` (1500),
  `AGENT_MODE_ANALYST_PROTO_BUDGET_USD` (15.0).
- Skill `skill_plugin/skills/zango-prototype/SKILL.md` + `references/example/` (fictional lab sample
  tracker, 8 parts, 13.5 KB): parts, manifest, runtime API, first-draft order, screen brief template, bar.

## Console changes

- `api/agentMode.ts`: `preview_mode`, `prototype_revision`, `prototype_hash` on the requirement;
  `open_prototype` on availability; `preview_mode` on `NewRoundInput`; `prototypeUrl`, `usePrototypeHtml`
  (keyed by revision, keeps the previous page while the next loads).
- `api/scaffolds.ts`: `preview_mode` on `createScaffold`.
- `pages/new/NewAppForm.tsx`: section 3 "Design" with a "Free design" switch (also `?design=free`), and a
  Design row in the summary. A change on an existing app inherits the mode server-side.
- `builder/PrototypeFrame.tsx` (new): srcdoc iframe, `sandbox="allow-scripts allow-popups allow-forms"`;
  listens for `zas-proto` ready/location/error; sends `goto` on reload so the user stays on their screen;
  location → `PreviewFocus` {role label, page = screen id, title "Title (screens/<id>.js)", record}.
- `TemplateBuilderPanel.tsx`: open mode uses `PrototypeFrame`, no "edit in builder", and the generating
  cover shows only until the first prototype revision.
- `PreviewTabPage.tsx`: open mode renders `PrototypeFrame` (opens at the hash's `page`).
- `tsc -b`: no new errors (the 4 existing ones are the known missing `logs/` sources and vite node types).

## How to test

```bash
cd backend/test_project
../../../zango_venv/bin/python manage.py test --noinput zango.tests.apps.app_templates.test_prototype
```

## Live run 1 (2026-10-23, diagnostic_test_voucher, Sonnet 5.5, subscription)

- Prompt: free design of the existing app, every persona's home, lists, voucher record page, issue/redeem/
  report upload/invoice review flows, no questions.
- Result: 165 s, $1.11. The analyst wrote manifest (15 screens), tokens, app.css, data.js, shell.js and
  `screens/psp_home.js` (28 KB, first visible part at 30 s), then launched 5 screen writers in one
  message. **The writers died**: the CLI starts sub-agents as "Async agent launched", the analyst's turn
  ended, the stream closed the client and killed them. `AgentDefinition(background=False)` had no effect.
- Fix: open mode sets `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in the analyst env. Verified with the spike:
  `Agent` calls then return the writer's final answer, and two writers still run in parallel.
- Needs a worker restart, then a new run.
- Console 500s seen during the run were not from this work: the browser held an app-user session cookie
  for `localhost` (AppUserModelBackend), which the public-schema console can't resolve. Clear the cookies
  and sign in again.

## Live run 2 (same requirement, after the fix and a worker restart)

- A console reply ended in 12 s with "(no reply)": two `proto_outline` calls were "interrupted before a
  result". A replay of the same code path in a shell (Haiku) worked, so this looks like a one-off (the
  transcript shows subscription rate-limit events). Not reproduced since.
- Turn limits: a later turn only had 600 s / $4. Fixed: `prototype.is_drafting(parts)` (no parts, or
  manifest screens without a part) gives any such turn the first draft's limits (analyst options and
  `_dispatch_turn`).
- Then "write every remaining screen": the analyst launched 5 screen writers in one message; all 14
  missing screens (plus 4 screen CSS parts) landed between 44 s and 115 s, the analyst validated the
  spec and patched one screen; 134 s, $2.73.
- Checked in Chrome (full-page preview): PSP home (KPIs, reports to review, status bars, expiring),
  Vouchers (21, status chips, search, table/board), voucher record (stepper, patient & prescription,
  documents tabs, validity, lab, activity), "Mark report shared" → in-prototype confirm modal → status,
  stepper and activity update, toast. Patients and Lab invoices draw with domain data. No console errors.
- Not checked in Chrome: switching persona (the native select inside the sandboxed frame can't be
  driven by the browser tool; covered by the headless runtime tests).

## Slice of U: import an uploaded HTML page (2026-10-23)

- `documents.py`: `.html`/`.htm` accepted (`text/html`); the extract is an outline (title, headings,
  buttons/links, table columns, labels) that says to use `proto_import`; the original is written to the
  docs dir and INDEX.md says how to import it.
- `prototype.import_html(html)`: styles → `imported/styles.css`; inline scripts → `imported/script-NN.js`
  in order, unchanged (non-JS script elements stay in the body); allowed library scripts and Google Fonts
  → manifest; other script hosts dropped with a note; remaining markup → `body.html`; starter manifest
  `{"source": "imported", screens: [], roles: {}}`. Elements are matched in document order, so a `<style`
  inside a script's string stays in the script.
- `body.html` is the one HTML part (assembled before `#zas-app`); `imported/*` and `body.html` may be up to
  1 MB each (a script can't be split). An imported prototype is never "drafting" and must have a part
  calling `ZAS.ready({go})` (static problem until it does). Runtime boot draws nothing over an imported
  page.
- `PrototypeBench(documents=…)` + tool `proto_import(document)`; `tasks.py` passes the requirement's HTML
  documents. Prompt and skill: import first, never redraw, fill manifest, add `zas-bridge.js`, write YAML.
- Console: `ACCEPTED` in `pages/new/intake.tsx` adds html/htm (new-app form and the change modal).
- Checked locally (not in the repo): the capability-bar file splits into one 159 KB script (parses),
  77 KB of styles, its Google Fonts link and 0.3 KB of body markup.
- Tests: 16 in `test_prototype.py` (import split, rules, html document outline, headless drive of an
  imported page through its own router).

## Notes / gotchas

- The SDK's sub-agent tool is named `Agent` in this CLI (allowed both `Agent` and `Task`).
- Sub-agents can run in the background; `background=False` keeps the turn open until they finish.
- Screen writers are told (prompt only) to touch just `screens/<id>.*`; not enforced in code yet.
- `window.claude.use` compatibility (for imported Claude artifacts) is left for the upload phase (U).
