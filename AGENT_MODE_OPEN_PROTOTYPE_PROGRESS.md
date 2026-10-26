# Agent Mode: Open Prototype ("Free design"), implementation progress

> **Next session: start Stage 2 (build agent follows the prototype).** Read "Stage 2 handoff" at the
> end of this file first. Plan: https://claude.ai/artifact/LV4oRr4VH9kfjFHWs5ufeF §10 (v6). Local copy: `AGENT_MODE_OPEN_PROTOTYPE_PLAN.html` (repo root); edit it there and republish to the same URL.

Plan: https://claude.ai/artifact/LV4oRr4VH9kfjFHWs5ufeF ("Open Prototype Plan", v6).
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
| Done-when | 3 chat-only runs measured | partly: 1 existing-app run (15 screens, ~$3.8) and 1 HTML import run; no brand-new chat-only app yet |
| U (slice) | Upload an HTML page on new app / change, `proto_import` | **done**, checked in Chrome |
| U (chat) | Files and screenshots in the chat composer, linked to the message | **done 2026-10-26**, checked in Chrome |
| B7 | The YAML covers the prototype: coverage gate in spec_mark_ready, greyed menu items, must-show lists | **done 2026-10-26** (unit-tested; checked against the sponsorship app's approved YAML) |
| P2 | Map contract (`data-zas-*` markers, map check, gates) | **not started** |
| P3 | Probe/look/Point for open mode | **not started** (only location focus works) |

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

## Live run 3: new app from the uploaded HTML (2026-10-23, checked in Chrome)

- New app form: "Describe it", Free design on, the capability-bar HTML attached (232 KB, shown as HTML).
  App `sponsorship_management_hcp` created; first turn ran on Sonnet 5.5 (draft mode, one pass).
- The page showed in the preview as it is from the first write (its own sign-in screen), then on Home
  once the agent's bridge was in: same look, data, nav and banners as the file. Its own "not connected to
  the shared workspace" fallback ran (no `window.claude` in the sandbox), so no compat shim was needed
  for viewing.
- The agent's YAML: 0 errors, 9 warnings; roles Sponsorship Office, Requester, Budget owner, Compliance,
  Legal, Finance, Signatory; organisers, requests (draft → closed, benefits, approvals), agreements,
  payments, evidence, library entities; home dashboard, list pages, full pages for sponsorships and
  organisers; 7 role journeys, 10 flags, 7 open decisions. Its stated gaps: Home can't yet show each
  person only their own waiting work; AI, DocuSign, SAP and screening steps are plain requirements.
- Clicked in Chrome: Home, Organisers, Requests (stage chips, table), a request record (8-stage stepper,
  Run AI review, tabs). No console errors. One nav click landed during the end-of-turn reload and did
  nothing; the next click worked.

## Notes / gotchas

- The SDK's sub-agent tool is named `Agent` in this CLI (allowed both `Agent` and `Task`).
- Sub-agents can run in the background; `background=False` keeps the turn open until they finish.
- Screen writers are told (prompt only) to touch just `screens/<id>.*`; not enforced in code yet.
- `window.claude.use` compatibility (for imported Claude artifacts) is left for the upload phase (U).


## Stage 2 handoff (written 2026-10-23, for the next session)

### Where things stand
- Branch `feat/agent-mode-open-prototype`, commits b3a67f87 … e3267964, all committed (only the unrelated
  `frontend/yarn.lock` is modified). Not pushed.
- Requirement side works for two kinds of prototype:
  1. **Generated**: parts written by the agent; screens are `ZAS.screen('<id>', …)` in `screens/<id>.js`,
     shared look in `tokens.css` / `app.css`, data in `data.js`.
  2. **Imported**: an uploaded page kept as it is (`imported/styles.css`, `imported/script-NN.js`,
     `body.html`) with `manifest.source = "imported"` and a small `zas-bridge.js` calling `ZAS.ready({go})`.
     Its screens are drawn by its own code: there are no per-screen parts.
- Both run in the console frame, and `ZAS.go(screen, {role, record})` opens any manifest screen in both, so
  a headless browser can visit every screen x role.
- Live test apps (local dev DB):
  - `diagnostic_test_voucher` (app 3843f5db-00f2-470b-ac8a-085e4993fa94), requirement
    feb6e6f8-d819-4049-8492-50ab92f3d775: generated, 15 screens, not approved.
  - `sponsorship_management_hcp` (app b056ed46-71d6-4f4f-b540-9ea46f45f6f9): imported from the
    capability-bar HTML, spec 0 errors / 9 warnings, 7 open decisions, not approved.
- **Not done on the requirement side, and it matters for Stage 2:**
  - P2 map contract: prototypes carry no `data-zas-ref` / `data-zas-action` markers and nothing checks
    prototype ↔ YAML coverage. Stage 2 parity by markers (B6) depends on it.
  - `app.design` (free tokens + fonts) is not in `schema.json` yet. B2 needs it.
  - The approval bundle (`approval_bundle.write_bundle`, called from `studio_build.py` L748/781) knows
    nothing about the prototype yet.
  - Approval gate in open mode only checks that a prototype exists (`template_spec.approval_problem`).

### Decisions already made (user)
- Hybrid build: prototype tokens + its shell everywhere; standard runtime screens themed; screens whose
  layout differs are rebuilt as custom pages from the prototype.
- Any pinned library from cdnjs / jsdelivr / unpkg may be used by prototypes; the build ports or replaces it.
- The capability-bar HTML must never enter the repo (memory: sponsorships-html-capability-bar).
- Verify live in Claude in Chrome; the user restarts the Celery worker after backend changes
  (memory: verify-agent-mode-in-chrome).

### Stage 2 order (revised from the plan with what P1 taught us)
0. **S0 — design tokens into the spec** (half a day): `app.design {source: prototype, fonts, tokens}` in
   `packs/zango_app/schema.json` + SCHEMA.md; the analyst writes it from `tokens.css` (generated) or the
   `:root` variables in `imported/styles.css` (imported). A helper `prototype.design_tokens(parts)` can
   pre-fill it.
1. **B1 — bundle** (`approval_bundle.py`): for open requirements write `.zas/bundle/prototype/`:
   `prototype.html` (assembled), `manifest.json`, `design.json`, `libraries.json`, and per screen x role
   `screens/<id>/dom.<role>.html` (rendered DOM after `ZAS.go`, scripts stripped), `shot.<role>.png`
   (1280 px), `css.used.css` (rules matching the snapshot). Reuse the probe worker
   (`preview_probe_worker.py`): add an open-mode runner that loads the assembled page and calls `ZAS.go`;
   allow the CDN hosts there (`FONT_HOSTS` → `PROTO_HOSTS`). Imported pages are one big script: the build
   must port from the DOM snapshot + screenshot, never from the page's code.
2. **B2 — tokens in the runtime** (`assets/frontend/zas/tokens.css`, `config.ts applyTheme`): map
   `app.design.tokens` onto the `--z-*` tokens (ground, card, text levels, borders, brand ramp, semantic
   colours, radii, shadows, fonts) via a generated `tokens.app.css`; load fonts in index.html. Gallery gets
   one themed shot.
3. **B3 — shell**: open mode builds `src/custom/Shell.tsx` from the shell snapshot (look only; menus and
   permissions still from `roles[].menu`); the runtime takes a `shell` slot.
4. **B4 — screens, theme or rebuild**: `spec_check.py` classifies each mapped screen (theme when a standard
   crud/detail/form fits, rebuild otherwise or when forced) and writes the hole text "Approved look:
   .zas/bundle/prototype/screens/<id>/" (extend the existing Approved-look path, `spec_check.py` ~L2095,
   `references/custom-code.md` §Porting a sketch). Libraries: npm twin or zas/SVG, listed in the report.
5. **B5 — lint** (`scripts/zas_test/design.py`): in open mode colour literals only in the generated token
   file; fonts from `app.design.fonts`; every mapped screen counts as Approved look.
6. **B6 — parity**: until P2 lands, parity = every screen x role opens and one look per screen against
   `shot.<role>.png` (agent look + pixel-diff score in the report). Marker parity (`data-zas-ref`/`-action`
   sets) after P2.

### Guards: runtime first, custom only when nothing declarative fits (user, 2026-10-23)
The build already follows this in kit mode: only `type: custom` pages, custom tabs/panels and
`custom_requirements` become holes; everything else is thin declarative code on the runtime (`ZasTable`,
`RecordDrawer`, `Detail360`, crud endpoints, crud `FormRenderer` for forms). Open mode must not erode it,
because a free-design prototype makes every screen look custom.
1. **Requirement side (open mode), to add in S0:** every prototype screen that shows records maps to a crud
   page, a detail/360 page or a declared view/dashboard, however custom it looks. A `type: custom` page needs
   a stated reason (what no declared page can do) and its contract. Enforce in `_OPEN_PROTOTYPE_APPEND`,
   the zango-prototype skill and a `spec_mark_ready` check that lists custom pages created in open mode with
   their reasons. Once P2 lands, `prototype.screens[].maps` must point at the page.
2. **Build side (B4):** "rebuild as a custom page" is allowed only for (a) screens the spec already marks
   custom, or (b) a crud/detail page whose prototype layout the runtime cannot reach even with tokens and
   screen-level styling. Each rebuild needs a one-line reason in the bundle's `index.md` and in the build
   report. Default for every mapped crud/detail/dashboard page: the runtime component + `app.design` tokens
   + an optional token-only screen stylesheet. `spec_check.py` computes the class; the agent may not upgrade
   a page to custom on its own.

Checked on the imported sponsorship app (2026-10-23): the ladder held. Pages: `home` dashboard; 12 crud
pages (sponsorships with table + kanban views, organisers, agreements, evidence, payments, templates,
evidence requirements, policy settings, cost centres, agents, integrations); `sponsorship_detail` and
`organiser_detail` as detail pages on `sponsorship_360` / `organiser_360`. **No `type: custom` page.** The
15 manifest screens have no `maps` yet (P2).

### Bug found: specs PyYAML can't read
The imported app's spec has flow mappings with an unquoted `?` inside a value (lines 554, 582, 815, e.g.
`- {name: submit, label: Submit, … Sponsorship Office?, on_done: …}`). The platform loader (ruamel,
`yamlio`) accepts them, so the console shows 0 errors, but PyYAML raises `ParserError`. `spec_check.py`
(the build) reads specs with PyYAML (`yaml.safe_load`), so this spec would break the build. Fix before or in
S0: have the spec tools re-emit risky scalars quoted (or block style) when they write, and make validation
fail on a spec PyYAML can't parse. This is not specific to open mode.

**Fixed (Stage 2 step 1, 2026-10-23):** `yamlio.dump_rt` now double-quotes plain strings with
`? : # , [ ] { }` inside flow collections (`_quote_flow_scalars`), so every spec-tool write is
PyYAML-readable; `yamlio.pyyaml_problem(text)` backs a `yaml_compat` error in `validate_text` (console,
approval) and in `SpecWorkbench.issues()` (agent's validate / mark ready). Tests in `test_spec_engine.py`.
The sponsorship spec in the local DB was rewritten once (data identical, lines 554/582/815 quoted).

**S0 done (2026-10-23, checked live in Chrome on both test apps):**
- `schema.json` (pack **1.1.19**): `app.design {source: prototype, fonts {body, display, mono}, tokens}`
  (free tokens, lowercase names, ≤150) and page `reason` (only on `type: custom`). SCHEMA.md documents both,
  with the canonical token names B2 maps: brand, brand-strong, brand-soft, accent, accent-soft, page, card,
  sunk, nav, text-strong, text, text-2, text-3, text-faint, border-faint, border, border-strong, ok/warn/bad/
  info (+ `-bg`), radius-sm/radius/radius-lg, shadow-sm/shadow/shadow-lg.
- `prototype.design_tokens(parts)`: top-level `:root` custom properties (generated: `tokens.css`; imported:
  every css part; `@media` skipped, later rules win), `var()` resolved, aliases → canonical names, others
  kept; fonts from `--font`/`--display`/`--mono`.
- Tool `proto_design` (spec server, open mode): sets `/app/design`; refuses clearly on a template version
  without `app.design`.
- Guard 1: `spec_mark_ready` in open mode refuses when `app.design` is missing or has drifted from the
  prototype, and refuses a custom page without `reason`; on success it lists custom pages + reasons.
  Same rule in `_OPEN_PROTOTYPE_APPEND` and the zango-prototype skill ("Runtime first: how screens map").
- Live: voucher → brand #0F766E, Plus Jakarta Sans / JetBrains Mono, 28 tokens. Sponsorship → brand
  #234635 (the page's later client-palette override), Inter / JetBrains Mono, 50 tokens; the analyst also
  set `theme.primary` to the brand as the tool asks. Both specs still PyYAML-clean.
- **Gotcha:** requirements pin their template version. The live pack had to be bumped to 1.1.19 and
  imported (`manage.py app_templates import <pack dir> --publish`), and the two test requirements re-pinned
  with `adopt_template(slug)`. Older open requirements stay on their version; the ready gate skips the
  design check for them. There is no UI to move a requirement to a newer template version.
- Found by the guard: the pack's own `example.yaml` has a custom `dashboard` page with no `reason` (fine in
  kit mode; an open-mode spec copied from it would be refused at ready).

**B1 done (2026-10-23):** `.zas/bundle/prototype/` for open requirements.
- `preview_probe_worker.py --open <prototype.html> <out>` (one batch, killable process group, 600 s cap in
  the parent): allows `PROTO_HOSTS` (fonts + cdnjs/jsdelivr/unpkg), visits every manifest screen x role via
  `ZAS.go` (record screens: manifest `sample`, else the first row of `ZAS.store.list(record)`), removes the
  persona bar/toasts, and writes `screens/<id>/dom.<role>.html` (scripts stripped), `shot.<role>.png`
  (1280 px wide, height ≤ 2400), `css.used.css` (matching rules in sheet order, group rules pruned).
  A role whose DOM equals another's is written once (`same_as`). Errors / blank screens per role.
- `approval_bundle.write_prototype_bundle(parts, out, design=)`: `prototype.html`, `manifest.json`,
  `design.json` (app.design), `libraries.json` (manifest + CDN URLs in any part), `capture.json`, `index.md`
  (screen, title, prototype-only, roles, sample record, files, problems). Called from
  `StudioBuild.write_bundle(…, prototype=parts)`; `tasks.py` passes `requirement.prototype_parts` for
  `preview_mode == "open"`. Never fails the build (step `prototype_bundle` in post_steps).
- Manifest `sample` on record screens: imported pages get a static warning without it (the page keeps its
  own store, so there is no other way to open a real record); skill updated. The sponsorship analyst
  added `req: SP-2026-0058`, `org: pof` live in chat.
- Run on the DB parts of both test apps: voucher 15 screens / 26 snapshots / 12 s / 3.4 MB; sponsorship
  15 screens / 94 snapshots (signin shared by all 7 roles) / 35 s / 21 MB. No errors, no blank screens,
  no blocked requests. Screenshots checked by eye (voucher record page, sponsorship request page).
- Not in B1: `maps` per screen (P2) and the theme/rebuild class (B4) are not in `index.md` yet.
- `test_skill_plugin` has 7 failures + 1 error that predate this branch's Stage 2 work (checked on a stash).

**B2 done (2026-10-26):** prototype tokens reach the zas runtime.
- `spec_check.py` turns `app.design` into CSS shipped in `spec.ui.json` as `app.design.{css,font_url,fonts}`
  (no separate `tokens.app.css`). `DESIGN_MAP` maps canonical names onto `--z-*`, the tone fg/bg (borders are
  a color-mix), and the crud `--color-gray-*` / `--color-brand-*` ramp; other names become `--p-<name>`.
  Values with `;{}<>` or `url(` are dropped with an `app.design` warning. `brand` sets `theme.primary`.
- `config.ts applyTheme()` injects `<style data-zas-design>` + a Google Fonts `<link>` (families other than
  Inter / JetBrains Mono) at runtime, not in `index.html`, because the single-file Zango build may not serve it.
  A zero-specificity `:where(.zas *, .zas-login *)` font rule beats appbuilder's global `* {Inter}`.
- Gallery: the pinned part is marked `data-zas-pinned` and keeps the defaults (goldens unchanged); a new
  unpinned "themed" section shows buttons, badges and a field grid in the app's look. `zas_test.design`
  check `design.tokens.themed` compares its computed colours, radius and font with `app.design`.
- Test: `test_declared_ui.BuildHearsItTests.test_app_design_themes_the_runtime`. `tsc` clean in `src/zas`.
- Live (voucher, scratch frontend on 127.0.0.1:3100 against bright-isle:8000, signed in as PSP Executive):
  login, the Tests crud list (Add Test #0F766E, ground #F3F6F6, borders #DCE5E3, Plus Jakarta Sans in the
  table) and the Add Test FormRenderer modal all use the prototype's look; `/app/__zas` themed section is
  teal + Plus Jakarta Sans while the pinned part keeps the defaults (#4F46E5, Inter, #f7f8fa).
- Found live: the form/crud packages load their own `:root` palettes after tokens.css, so FormRenderer's
  Submit and radios were #5048ed. The design CSS now restates the tokens.css `--color-*` / `--zango-*`
  bridge under `html:root`, which wins. Apps without `app.design` still have that order problem.
- Not in B2: the appbuilder shell (sidebar, top bar, "zelthy" logo) stays Inter; that is B3.

**B3 done (2026-10-26):** the prototype's shell on the runtime.
- The "shell slot" already exists: appbuilder's `ZangoApp` renders `customComponents.Layout` (with `menu`,
  `profileInfo`, `appLogo` and the routed page as `children`) instead of its own navbar + topbar. No fork.
- Runtime `zas/Shell.tsx`: `makeShell(options)` → the Layout component. Options only: `layout` side/top,
  `nav` (a token name, e.g. `brand-strong`; other names read `--p-<name>`), `tone` light/dark, `brand`
  {title, subtitle, icon | logo}, `groups` headings/collapsible, `user` side/top, `topbar`, `width`.
  Colours are all derived in `tokens.css` (`.zas-sh*`), so `src/custom/Shell.tsx` stays colour-free.
- Menu = the platform's for the signed-in role (spec `roles[].menu`); a platform group (item with children)
  draws as a heading or a fold. User card → appbuilder's own `UserProfileDrawer` (role switch, sessions,
  password) and `/app/logout`. The prototype's persona switcher is not built. Markers: `shell`,
  `shell-brand`, `shell-nav`, `shell-user`, `shell-top` (the last three as the kit-mode parity expects).
- Build: `references/open-mode.md` (new) §The shell: options table read off each role's home screenshot;
  SKILL.md Phase 6 step 4 + critical rules + reference index; custom-code.md and the App.tsx template point
  there. The bundle's `index.md` now has a Shell line naming each role's home screenshot.
- Lint: `zas_test.design` lint, open mode only (bundle has `prototype/manifest.json`): `src/custom/Shell.tsx`
  exists, uses `makeShell(`, and `App.tsx` has `Layout: Shell`.
- Live (voucher scratch frontend, hand-written Shell.tsx: brand-strong, dark, ticket, headings, user side):
  sidebar #0B4F4A with Plus Jakarta Sans, active item highlighted on list and 360 pages, client-side
  navigation, the user menu opens the profile drawer, and a role switch (Program Admin → PSP Executive)
  redraws the menu from the platform. Not checked: the < 760px layout and `layout: "top"`.
- Seen: the voucher spec's menus have no groups, so the prototype's "Work"/"Masters" headings don't show.
  That is a spec matter (menu `group`), as the plan says; nothing in B3 invents groups.
- Also fixed: `test_prototype.py` had `PrototypeBundleTests` twice (B1); the stale first copy is gone.
- Tests: `test_preview_parity.OpenShellLintTests`, `test_prototype.PrototypeIndexTests`, the bundle test
  checks the Shell line. Same pre-existing failures as before (test_skill_plugin 7+1, dashboard tree).

**B4 built (2026-10-26); its done-criterion (a full sponsorship build passing B6) waits for B6:** screens, theme or rebuild.
- Spec: top-level `prototype {hash, screens: [{id, maps: /pages/@x | /detail_views/@x, only: prototype, why,
  rebuild}]}` in schema.json (the plan's §5.6 shape, taken from P2 because B4 needs it; P2's proto_map will
  write it later), SCHEMA.md section, pack 1.1.20 published; both test requirements re-pinned. Until P2,
  the analyst writes it (`_OPEN_PROTOTYPE_APPEND`, zango-prototype SKILL step 7).
- `spec_check.prototype_screens()`: theme = crud list / 360 (also a detail page → its view); rebuild =
  custom page or dashboard, or `rebuild: true` + `why` (error without why); prototype-only. Lint errors for
  unknown pages/views and duplicates; a warning for manifest screens the spec doesn't list (P2 gates later).
  Not automatic yet: "layout the runtime can't reach" needs P2's refs, so only the analyst forces it.
- Holes: a forced rebuild adds `rebuild_page` (slot `Rebuild<Page>`, props `data {entity, endpoint, page}`)
  or `rebuild_view` (slot `Rebuild<View>`, props `zas`, `record`, `refresh`); `spec.ui.json` marks
  `pages.<x>.rebuild` / `detail_views.<x>.rebuild`. Custom pages keep their `custom_page` hole.
  `attach_prototype` appends "Approved look: .zas/bundle/prototype/screens/<id>/" to each rebuild hole and
  writes the theme/rebuild table into the bundle's `index.md` (replaced on every run) and `plan.md`.
- Runtime: `makeListPage` renders the `rebuild` slot in place of ZasTable (360 sub-route unchanged);
  the 360 renders its `rebuild` slot after the access checks, inside its context.
- Guard (`guards.bundle_rules`): a rebuild slot can't be written before its screen's `shot.*.png` and
  `dom.*.html` are Read; `src/custom/Shell.tsx` before each role's home shot (B3 follow-up).
- Lint: a themed crud page's `Page_<x>` must be `makeListPage` / `makeViewsPage` (no upgrading to custom);
  `src/custom/screens/<page>.css` is allowed for themed pages only, every selector scoped to
  `[data-zas-key="<page>"]`, no colour literals, url() or @import.
- Docs: open-mode.md §Screens (classes, slot props, porting rules, libraries), SKILL Phase 6 step 4.
- Checked: spec_check on the sponsorship spec + its B1 bundle with a mapping per the done criterion →
  home rebuild (dashboard, slot DashboardHome), req rebuild (RebuildSponsorship360), 11 themed, start and
  signin prototype-only; table replaced, not duplicated, on a second run. Live on the voucher scratch
  frontend with throwaway slots: a `rebuild` list page drew rows from its crud endpoint, a `rebuild` 360
  got the payload (title, subtitle); both reverted.
- Tests: BuildHearsItTests (classes, holes, ui flags, index table, why/unknown errors),
  OpenModeScreenGateTests, OpenScreensLintTests. Pre-existing failures unchanged.

**B5 done (2026-10-26):** the design lint follows `app.design` in open mode (bundle has `prototype/`).
- `zas_test/design.py` `OpenDesign`: no colour literals anywhere in `src/custom/` (there is no generated
  token file to exempt: the tokens live in `spec.ui.json`); a literal equal to an `app.design` token is
  reported with its variable (canonical names via `spec_check.DESIGN_MAP`, brand → `var(--brand)`, others
  `var(--p-<name>)`). Inline colour/border/shadow/fill styles only through `var(--…)`. `fontFamily` /
  `font-family` only `app.design.fonts`, generic families or the font variables. `<style>` stays banned.
- Every mapped screen gets these rules (sketch palettes are off in open mode); the "Approved look" read
  gate covers rebuild slots and the shell (B4). Themed screens' look comparison is B6's look round.
- Kit mode unchanged (test). Docs: open-mode.md §Lint, SKILL critical rules.
- Tests: `test_preview_parity.OpenDesignLintTests` (g_lint end to end with a stub Dx).

**B6 first part done (2026-10-26); marker parity waits for P2:** parity against the prototype.
- `zas_test.design` parity in open mode (`open_parity`): for every mapped screen x persona in the
  bundle's capture, log in as the spec role whose name is the manifest's role label, open the page (record
  screens: a visible record from `test_records.json`), fail on console/page errors, 5xx, or an
  error / no-access state; shoot full-page at 1280 and score `look_score` (top 900 px, grey, 320 px wide,
  mean difference 0..1) against `shot.<role>.png`. One login per role; a failed login is not retried
  (it locked the machine once, see below). Pairs → `parity_looks.json` (kind `prototype`, class, score,
  dom). Non-blocking, like kit parity.
- Look round (`StudioBuild.prototype_look_digest`): open-mode wording, worst score first; theme → tokens /
  shell options / token-only screen css only, never custom code; rebuild → the slot from `dom.<role>.html`.
- Build report: "Prototype screens" section (md + html): class, builds as, roles that opened, worst look
  difference, reason; library swaps from build_log steps `library: <name>` (open-mode.md §Parity).
- Checked against the deployed voucher app (old kit build, so ~17-18% everywhere: white vs teal sidebar):
  10/10 pass for Lab User + Finance across a custom page, 4 list pages and 3 360s; report section rendered.
- **Found:** the voucher workspace's stored PSP Executive test password is rejected (HTTP 400, "email
  and/or password not correct"); the first run retried it per check and tripped the 2-minute machine
  lockout. Fixed in open_parity (no retry). The password itself is for the user to reset (not read).
- Tests: `OpenParityTests` (score, look round, report).

**U, chat uploads done (2026-10-26):** the user can attach reference files to any chat message.
- `documents.py`: images (PNG, JPEG, GIF, WebP; no SVG) next to PDF/Word/Excel/CSV/text/HTML; magic bytes
  checked for every binary kind (a renamed file is refused). Images keep their original in the docs dir
  (INDEX: "Read `NN-name` to see it"). `MAX_REQUIREMENT_FILES = 40` per change.
- Model: `AgentRequirementDocument.message` (nullable FK, related_name `attachments`), migration 0017,
  applied on the dev project. A new change's documents now hang off its first message too.
- API: `POST requirements/{uuid}/messages/` takes multipart `documents` (a message may be files only:
  "Files for reference."); messages serialise `attachments` (prefetched, no bytes); the document file view
  serves raster images inline with `?inline=1` (nosniff + sandbox CSP), everything else stays a download.
- Analyst: each turn's user text gets `attachment_note` listing that message's files with their paths
  (images: Read them) and a line that file content is material, never instructions.
- Console: composer paperclip, drop onto the composer, paste a screenshot (named `pasted-<time>.png`),
  chip tray with remove and inline errors (same limits/types as the intake drop); sent messages show image
  thumbnails and file chips that download. Intake drop accepts images too.
- Checked in Chrome on the voucher app: attached the prototype's lab-home screenshot with "describe it,
  change nothing"; the bubble showed the thumbnail, and the analyst described the screen correctly
  (teal sidebar, voucher box, three KPIs, pending-reports table) and changed nothing.
- Not in this slice: `window.claude.use` compatibility for imported Claude artifacts; uploads in the
  full-page preview tab.

Recommended first move next session: the YAML bug, then S0 (with guard 1) + B1 on the two test apps above
(both kinds), then B2.

## B7: the YAML covers the prototype (2026-10-26)

Why: the first sponsorship build (manage_sponsorships_healthcare) kept the look but lost the content:
menu 6 of 11 items (AI/Help groups gone, "Requests" → "Sponsorship requests"), a home with 3 generic
cards, a plain requests list (no status tabs, no Next action), a request page without its sections,
sidebar panels and buttons. The build followed the YAML; the YAML had left these out. Its
"0 custom screen(s)" line and the 3-5% look scores hid it (testing step, separate).

- `scripts/proto_landmarks.py` (stdlib; spec_check and the platform share it): labels of a captured
  `dom.<role>.html` by kind: menu `(group, label)`, title (h1), headings, columns, tabs, buttons, field
  labels; counts dropped, IDs/amounts/dates/long text skipped.
- `agent_mode/prototype_coverage.py`: per screen, labels not said in the YAML it maps to (page/360 and
  the entities they show). Skips persona names, shell chrome (on every screen), record titles, screens
  that render like an earlier one, `not_built` texts. Rebuilt screens go to the build instead. Menu: per
  persona when menus differ; when all personas share one menu, every item must be in some role's menu
  and the fullest role keeps groups and order.
- `spec_mark_ready` (open mode) runs it after app.design: capture via `write_prototype_bundle` into
  `$TMPDIR/zas-proto-coverage/<parts hash>`; refuses with each gap and where it goes; no browser → note.
- Schema (pack 1.1.21): `prototype.screens[].menu {label, group, icon, roles}` and
  `not_built [{text, why}]`; SCHEMA.md, requirements.py prompt and zango-prototype SKILL.md say the YAML
  covers everything ("The YAML covers the prototype" table); "rebuild only when the user insists" is gone.
- Build: spec_check passes `menu` rows to index.md ("Shell: screens kept in the menu, greyed out" →
  `makeShell({soon})`, new groups placed after the prototype's previous group) and adds "It must show: …"
  to rebuild holes; `not_built` listed for the report. `makeShell` gained `soon` (greyed, not links).
- On the sponsorship approved YAML the gate lists: menu 'Requests', 'Agents', 'Templates', 'Evidence
  requirements', 'Getting started', 'Integrations'; home 'Your work', 'Sponsorships by stage'; requests
  'Next action' + 3 status tabs; request 'Package and benefits', 'Amounts', 'Next action', 'Run AI
  review', 'View text', 'Withdraw request', 'Received via'; organisers/agreements columns; policy fields.
- Tests: `test_prototype_coverage.py` (12, fictional lab fixture). 125 pass with parity/guards/declared_ui/prototype.
- Limits: KPI captions that are not headings aren't read; label matching is by text within the screen's
  YAML scope (a word used elsewhere in the entity can count as covered).
- Next: re-run the sponsorship requirement so the analyst fixes the YAML through the gate, then build.
  Testing fixes (look score, test-data cleanup, demo data) after that.

## Testing step 1: which failures are the app's (2026-10-26, sponsorship build)

Checked against the spec, the test code and the app (Chrome as Sponsorship Office; screenshots for others):

| Failure | Verdict | Why |
|---|---|---|
| Agreement steps "from the 360" time out (4) | test bug | agreement, payment, evidence_item have no 360; rows open a drawer. ui flows assume a 360 |
| Payment / Evidence "360 did not open for Requester" | test bug | same: no 360 for those entities |
| Finance: request_360 not_found (api + ui + design.tree) | test bug | api.g_detail opens a fresh record (status submitted); Finance's rows are `status in [payment, event, evidence, closed]` |
| Requester: Withdraw 403 (4) | test bug | g_transitions runs as `allowed[0]` (Requester) on a record someone else created; Requester rows are created_by_me |
| Mark executed: "No transition available" | test bug, plus a small UX gap | free-text condition "fully signed copy attached" is false on a test record; the refusal says "No transition available", not the condition_msg |
| Signatory on organiser_360 | small app (runtime) bug, no leak | the 360 shows "This page could not load / Error: 403 Forbidden" with "Back to Organisers" instead of the No access state |

So none of the red results is a wrong permission or broken workflow in the app itself.

## B7b: list rows open where the prototype opens them (2026-10-26)

The mockup has no agreement/payment/evidence record page: a row on Agreements or Evidence opens its
request on the Agreement / Evidence tab. The YAML could not say that (row_click: a 360, drawer or none),
so the build opened a drawer.

- `row_click: <view>#<tab>` (pack 1.1.22): the row's parent 360 on the tab that lists this entity.
  spec_check and the kit preview validate it (view exists, tab is a related_table of this entity);
  ZasTable navigates via `parentTabUrl` (the parent's uuid from row `zas.links`, which now always
  carry parent FKs, mixins.py); Detail360 opens `?tab=<code>`; the kit preview follows it too.
- Capture: after each list screen, the worker clicks the first row and records `row_opens`
  {screen, record, tab, overlay} in capture.json (~41 s for this 14-screen, 7-persona prototype).
- Coverage: `row_gaps` compares row_opens with `table.row_click`. On the sponsorship YAML it adds:
  agreements → `request_360#agreement`, evidence → `request_360#evidence` (both "drawer" now).
- Also: Detail360 shows the No access state on a 403 (was "This page could not load / 403").
- Tests: RowTargetTests (2) in test_prototype_coverage.py; coverage/parity/guards pass. 10 failures in
  app_templates pack tests (ordering_portal, compliance_monitoring, rems_compliance, sketch_kit)
  fail identically on the committed code before this change.
- Pending (testing step, uncommitted): zas_test/api.py scope-aware records (`record_for`), test
  crashes reported as "test could not run" skips.

## Run 2 (bright-slate, 2026-10-26)

- The new app was pinned to zango_app 1.1.20: the 1.1.21/1.1.22 bumps were never imported into the local DB (packs seed only on migrate). Imported and published 1.1.22, moved the app's binding and requirement pin to it mid-gathering.
- The B7 gate, run offline on draft rev 14, catches the preview-only menu items (Agents in AI; Getting started and Integrations in Help; these screens are prototype-only with no `menu` entry), the agreement/evidence row targets (`request_360#agreement` / `#evidence`, now drawer), and missing columns, headings, buttons and labels on home, requests, request, organisers, organiser, agreements and policy. The analyst will be refused at mark-ready until each is placed in the YAML, set to `rebuild`, or listed under `not_built`.

## B7c: the gate can't be skipped, and reads 360s strictly (2026-10-26)

Run 3 (tidy-osprey, pack 1.1.22): the analyst never called spec_mark_ready and told the user to press
Commit for build, which only validated the schema. The YAML (rev 32) had the greyed-out menu items
right, but the request 360 had no Closure tab, extra Benefits/Documents tabs and none of the Summary /
Package and benefits / Business rationale / Amounts / Next action panels; the organiser 360 had no
Agreements or Profile; every role had the full menu.

- `template_spec.approval_problem` (open mode) runs `prototype_gaps` → `prototype_coverage.coverage_issues`;
  gaps return 409 `{issues, agent_prompt}`. AgentPage sends `agent_prompt` + the issues to the agent and
  commits again after its turn (the existing unfinished-custom-work path). No browser: commit goes through.
- `GUIDE` (shared by spec_mark_ready and Commit) adds: one shared menu doesn't say who sees what; 360 tabs
  are the prototype's only; a heading is a `title`, not a field.
- Headings/titles match `scope_titles` (every `title`, tab labels) instead of all scope strings; a 360's tabs
  match its view's tab labels exactly, and view tabs the prototype lacks are `extra_tab` gaps.
- Fixed false alarms: not-built menu items are placed where Shell's `withSoon` puts them (`_place`) before
  the order check; a button on more than half of a persona's screens (4+) is shell chrome.
- Prompt and zango-prototype SKILL.md say the same. 6 new tests (20 in the module). The 5
  TemplateFenceTests errors in test_requirements also fail on HEAD (missing test-DB table).
- Run 4 (solar-summit): greyed-out items followed the spec's prototype.screens order (Integrations before
  Getting started), so the shell would draw them out of the prototype's order and the check flagged it.
  `soon_items` and `_menu_labels` now order them by the manifest's screen order.
- Run 4, rev 35: the preview drew one menu (11 items) for all seven personas while the YAML gave each role its
  own subset (Signatory: Home, Requests, Agreements). The gate's shared-menu mode let that through. Removed:
  each persona's menu must equal its role's `roles[].menu` in both directions (missing and extra items, groups,
  order). The fix goes in the prototype (proto_patch its menu render with persona → hidden items), never by
  widening a role: the user approves what the preview shows each persona. Import step 5 and the prompt say so.

## B7d: the preview is the app (2026-10-26)

Run 5 (pack 1.1.22, strict menus) passed the gate only through not_built: 19 entries, most of them renames
("Amounts are part of the Request section", "built as Legal threshold"), while the preview still showed
them. The request and organiser 360s differed in layout (stage tracker, banner, Overview sections, three
side panels, stat cards, a tab-less organiser page), which label matching can't see.

The rule now, in the gate, prompt and skill: the user approves the preview as the app; what it shows is
built exactly, and nothing it doesn't show.
- `not_built` no longer hides a label: one the preview still shows is a `still_shown` gap. Leaving
  something out needs the user's agreement and a proto_patch that takes it out of the preview.
- An uploaded page's (manifest `source: imported`) record screens must be `rebuild: true`
  (`needs_rebuild` gap): the build ports them from the screen, with the "It must show" list.
- Never rename the preview's words to fit the YAML.
On run 5's YAML the gate now refuses: req and org need rebuild; the not_built headings, labels and
policy fields are still in the preview. 24 tests.

### Run 6 (e72dc4f1, 2026-10-26)
- Analyst asked 6 decisions before mark_ready. Gate run by hand on its yml: Home grouped under Sponsorships (prototype: no group), home "Open getting started", requests "Waiting on me" / "Event & evidence".
- Missed until now: a rebuilt 360 skipped the tab check. The yml's request page added "Benefits"; the organiser page had 3 tabs where the mockup has none. Fix: `_tab_gaps` runs on rebuilt screens too, and a record screen drawn without tabs gets none (spec_check accepts `tabs: []`).
