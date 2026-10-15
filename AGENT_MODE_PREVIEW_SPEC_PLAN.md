# Agent Mode: Preview-to-Spec (part 1)

The plan: https://claude.ai/artifact/F2W1J8QMzxHeinXoBbCxxB ("Preview-to-Spec Plan", version 3).
Branch: `feat/agent-mode-app-studio-skill` (on top of the App Studio skill work, which is
still uncommitted; see `AGENT_MODE_APP_STUDIO_SKILL.md`). Started 2026-10-15.

Part 2 (how the build agent receives the approved preview) is planned after part 1 is done.

## Goal

- The YAML stays the only thing that changes; the preview is drawn from it.
- Requests land on the lowest level of the ladder: L0 look, L1 CRUD + workflow,
  L2 declared presentation, L3 custom UI (with a contract), L4 custom logic (typed).
- The analyst gets eyes **for custom screens only**: run each sketch, read a text summary of
  what it drew, and screenshot that one component when the question is visual.
- The user can point at an element, and open the preview in a new tab.

## Phases

| Phase | What | Status |
|---|---|---|
| A | Probe in the preview: spec paths on sketches, `ZAS_PROBE` (sketches / run / runAll / show / box), recording of `ctx.ui` calls and `ctx.rows` reads | **done** |
| B | Headless runner (Playwright child process), automatic check after edits to custom screens, `preview_check` / `preview_look`, gates in `spec_mark_ready`, analyst guidance | **done** (except `preview_compare`, see below) |
| C | "Point", preview focus sent with each message, "Open in new tab" | **done** (tested live in Chrome) |
| D | Widen the YAML: `app.ui`, `type: dashboard` + `blocks`, contracts on custom work, typed custom requirements, custom-work count | **done** (form `layout` deferred, see below) |
| E | Approval bundle (bridge to part 2) | planned in part 2: `Spec-to-Build Plan.html` (https://claude.ai/artifact/7yHY9VGQh7hK1eH5GUmimE), phase F2 |

## Decisions made while building

- **The browser runs in a child process, not a thread.** `preview_probe_worker.py` is a plain
  script (stdlib + Playwright) speaking JSON lines. A sketch with an endless loop cannot be
  interrupted inside the page, so the parent kills the whole process group after 30 s
  (45 s for a screenshot). Nothing is left running in the Celery worker. Tested: Chromium is
  gone after the kill.
- **After a hang**, the same YAML is refused at once; a changed spec starts a fresh runner, up
  to 3 restarts per turn. Then checks are off until the next message.
- **One runner per analyst turn**, started on the first check, killed in the turn's `finally`.
  Start-up is about 10 s on the first check; each run after that is well under a second.
- **Sealed page.** Every request is aborted except Google Fonts (for faithful screenshots).
  js-yaml and lucide are already inlined in `app-studio.html`.
- **Paths are the spec tools' paths**: `/pages/@code`, `/detail_views/@dv/tabs/@code` (index
  when a tab has no code), `.../tabs/@code/sections/<i>`, `/detail_views/@dv/sidebar/<i>`.
  `preview_look` also accepts the index form (`/pages/3`).
- **What triggers the automatic check** (`SpecWorkbench._after_edit`): an edit that changes a
  custom screen's own node reports that screen in full. An edit to `/modules`, `/roles`,
  `/choice_sets`, `/app` or the root re-runs every sketched screen and reports only failures.
  Any other edit runs nothing. A probe failure never blocks the edit; it adds a note.
- **"Looked at" survives turns**: `AgentRequirement.sketch_looks` = {path: hash of the screen
  when last looked at} (migration `0013`). A look stops counting once that screen changes.
- **Gates in `spec_mark_ready`** (only when a probe is available): every sketched screen draws
  without an error or blank for every role, and was looked at since it last changed.
  Without Playwright, or for PSP (no `ZAS_PROBE`), the gates are skipped and the tools are not
  offered.
- **Screenshots**: element-level (a panel), or for a custom page the content area cropped to its
  content. 1280 px, or 390 px for phone. At most 8 per turn. Image tokens only when asked.
- **Older generic versions** use the current preview page for checks (`follow_current`).
- `AGENT_MODE_PREVIEW_PROBE = False` in settings turns the whole thing off.
- **`preview_compare` is not built yet.** It needs uploaded reference images (open question 3).

- **Pointing lives in the preview page, not the console.** Every element the preview draws that
  maps to the spec carries `data-zas-path` (and `data-zas-label`):
  - menu items;
  - page headers;
  - list column headers;
  - view switcher buttons and views;
  - form fields (entity fields only);
  - the 360 header, its facts, stats, tab buttons and tab bodies;
  - every panel and section;
  - custom sketches.

  A headless test walks every role × page × tab × view × create form of the example spec and checks that every emitted path resolves in the YAML.
- **"Point" is a button the adapter adds to the preview's own bar.** In point mode, a click is captured before the page sees it, so nothing navigates. The nearest element with a path is sent as `focus.pointed`. Esc cancels. A floating pill shows the hint, so the layout doesn't shift.
- **Focus**: the adapter reports `ZAS_LOCATION()` after each render, de-duplicated:
  - role, page, title, path;
  - the record, tab and view, when there are any.

  The console keeps the latest location and the last pointer.
- **Sending**: each reply sends `focus` (the pointer if there is one, else the location).
  - The server cleans it into a small known shape (`preview_focus.py::clean_focus`) and stores it on `AgentRequirementMessage.preview_focus` (migration `0014`).
  - The analyst reads it as a `[Preview: …]` note appended under the message (`focus_note`). The system prompt says what "this"/"here" mean.
- **Full-page preview**: `/console/apps/:appId/agent/:reqId/preview` (`PreviewTabPage`). It sits outside the Shell, so there is no console chrome.
  - It polls the requirement (4 s while open, 2 s while the agent is thinking), so agent edits redraw it.
  - It opens at the place in the URL hash (`goto`).
  - It is read-only. Pointing there reaches the Agent page's chat through `BroadcastChannel('zango-agent-preview')`.

### Phase D decisions (2026-10-15, user answers)

| Question | Decision |
|---|---|
| `app.ui` scope | My call: **`radius`** (sharp, rounded, soft) and **`density`** (compact, comfortable) only. Pure tokens, so the preview and the build cannot drift. No nav style or fonts. |
| Dashboards | **New `type: dashboard`** with `blocks` |
| Uploaded screenshots of an old system (`preview_compare`) | **Skipped for now** |
| Custom-work budget | **Count only**: a pill in the preview header ("2 custom screens · 3 custom rules"), no confirmation step. Custom screens are still drawn in the preview by their `preview` sketch. |

### Phase D design notes

- **Dashboards in the build.** `spec_check` resolves a `type: dashboard` page to a `custom` page:
  - The component is `Dashboard<PascalCode>`; `declared: dashboard` and `blocks` are kept in `spec.resolved.json`.
  - Its hole text lists every block exactly, so the build agent writes it through the existing custom-page machinery (slot, data hook, hole audit, UI tests that open every slot).
  - A deterministic runtime dashboard component (`zas_core` endpoint, URL and policy, plus a React page) can replace this later, the same way list views do.
- **Block grammar**:
  - `kpis` (value: `count: entity` or `sum`/`avg`/`min`/`max: entity.field`, with `where`, `format`, `go`);
  - `bars` (`group_by`, count or `value.sum`);
  - `list` (`primary`, `secondary`, `meta`, `badge`, `sort`, `limit`);
  - `table` (`columns`);
  - `board` (`group_by`, `card`);
  - `grid`, `stack` and `panel` for layout.

  `spec_check.lint_dashboard` checks every entity, field path, `go` page and `where` expression.
- **`event`, not `on`.** PyYAML (used by `spec_check` and the tests) reads the key `on` as `true`. Interactions and triggers use `event:`, and SCHEMA.md warns about it.
- **Contracts.**
  - Custom pages, tabs and panels take `data`, `interactions`, `states`, `acceptance` and `refs`.
  - Custom requirements take `code`, `trigger` (`event` plus `transition`/`tag`/`cron`), `acceptance` and `preview.toast`.
  - `spec_check.contract_text` appends them to the hole text ("Reads… Interactions… Trigger… Acceptance (test each): (1)…").
  - `spec_check` errors on a trigger with an unknown transition or tag, or a schedule without `cron`.
- **Gate** (`agent_mode/custom_work.py`, in `spec_mark_ready`): every custom screen and every custom requirement needs `acceptance`; notification and scheduled requirements need a `trigger`.
  - This applies with or without Playwright.
  - **Existing drafts with custom screens will need the analyst to add acceptance before "ready".**
- **The preview**:
  - draws dashboards (`renderDashboard`, using the same `ctx.ui` kit as sketches), with `data-zas-path` on every block for pointing;
  - applies `app.ui` via `data-zas-radius` / `data-zas-density` on `<html>`;
  - shows `data` and `acceptance` under "Build notes";
  - simulates typed requirements: a create or transition shows the `preview.toast` (or the text) as a toast "(simulated)".
- **The runtime** (`assets/frontend/zas`):
  - `tokens.css` now uses `--z-r-card`, `--z-r-head`, `--z-r-ctl`, `--z-ctl-h`, `--z-cell-y`, `--z-th-y` and `--z-page-pad`, redefined for `html[data-zas-radius|density]`;
  - `config.ts applyTheme()` sets the attributes;
  - `Gallery.tsx` pins the defaults so the goldens and the "card radius 12px" design test don't move;
  - `types.ts` gains `app.ui`.
- **Deferred: form `layout` (steps, two_column).** crud's FormRenderer has no steps today, so this needs runtime work first.

## Changes

Preview page (template pack `zango_app`, now **1.1.9**):
- `builder/app-studio.html`:
  - `runPreview` is split into `execPreview` (returns `{html, error}`) and `runPreview`, which wraps the output in `data-zas-sketch="<path>"`.
  - `recordingUI` records one summary line per `ctx.ui` call. The `ctx.rows` / `related` / `entity` / `fmt` wrappers record what was read and warn on unknown entities or fields.
  - Custom tabs and panels carry `data-zas-panel="<path>"`. A `tabPath()` helper was added.
  - New `ZAS_PROBE` section: `probeSketches`, `probeRecord`, `probeRun`, `probeShow`, `probeBox`, `runAll`. Links to pages that don't exist are flagged.
- `builder/adapter.js`: `window.zangoLoad = load` for headless use.
- `DRAFTING.md`: guidance in step 5 and "Later turns".
- `template.json`: now **1.1.11**, with an updated changelog.
  - 1.1.8 → 1.1.11 were all dev-only imports on this branch.
  - Consider one version for the commit; any version above what is in the DB works.
- `builder/app-studio.html` (phase C):
  - the `zp()` / `entPath()` helpers and `data-zas-path` across the renderers;
  - `sectionHTML` now wraps `sectionInner`;
  - a `zas:render` event;
  - `window.ZAS_LOCATION` and `window.ZAS_GOTO`.
- `builder/adapter.js` (phase C):
  - focus reporting, the "Point" button and point mode, and the `goto` message;
  - capabilities `['focus', 'goto']`.

Agent Mode:
- New `agent_mode/preview_probe_worker.py`: the headless runner.
- New `agent_mode/preview_probe.py`:
  - `PreviewProbe` (check, look, close), `probe_for(template)`;
  - `custom_screens` / `screen_hashes`, `format_check` / `format_result`.
- `agent_mode/spec_tools.py`:
  - workbench takes `probe` and `sketch_looks`;
  - `_after_edit` runs on every commit;
  - new methods `preview_check`, `preview_look`, `_check_screens_ready` (used by `mark_ready`), `close`;
  - tools `preview_check` and `preview_look`, offered only with a probe;
  - handlers run via `asyncio.to_thread`, and a dict result passes through (image content).
- `agent_mode/models.py`: `AgentRequirement.sketch_looks`, plus migration `0013_requirement_sketch_looks`.
- `agent_mode/tasks.py`:
  - builds the probe for the analyst turn;
  - records `sketch_looks` edits;
  - closes the bench in `finally`;
  - passes `preview=` to the options.
- `agent_mode/requirements.py`: `_PREVIEW_TOOLS_APPEND` in the analyst's system prompt when the preview tools are on.

Phase C, backend:
- New `agent_mode/preview_focus.py`: `clean_focus`, `focus_note`.
- `models.py`: `AgentRequirementMessage.preview_focus`, plus migration `0014_message_preview_focus`.
- `api/platform/agent_mode/v1/views.py`: the messages POST takes `focus`; `_append_user_message(..., focus)`.
- `serializers.py`: messages include `preview_focus`.
- `tasks.py`: the analyst prompt is the message plus `focus_note(...)`.
- `requirements.py`: `_SPEC_TOOLS_APPEND` explains the `[Preview: …]` note.

Phase C, console (`console/src`):
- `api/agentMode.ts`: the `PreviewFocus` type; `RequirementMessage.preview_focus`; `useSendMessage` takes `{content, focus}`.
- `builder/EmbeddedBuilder.tsx`: `onFocus`, `goto` and `className` props; the `focus` message.
- `builder/registry.ts` and `TemplateBuilderHost.tsx`: `onPreviewFocus` passes through.
- `builder/TemplateBuilderPanel.tsx`: tracks the place; adds the "Open the preview in a new tab" link (`ext` icon) in the pane header.
- `AgentPage.tsx`: pointer state, the BroadcastChannel listener, and `sendReply` (sends the focus, clears the pointer on success).
- `agent/Thread.tsx`: the pointer chip above the composer (× to clear; the placeholder becomes "What should change about it?"); "Pointed at …" under sent user messages.
- `agent/agent.css`: `.ptr` and `.ptr-sent`.
- New `agent/previewChannel.ts` and `agent/PreviewTabPage.tsx`; a route in `router.tsx`; `.pvtab*` styles in `builder.css`.

Phase D, pack (`zango_app`, now **1.1.12**):
- `schema.json`: `app.ui`; page type `dashboard` + `blocks` (`dashBlock`, `dashKpi`, `dashValue`, `dashBars`, `dashList`, `dashTable`, `dashBoard`); contract `$defs` on page, tab and sidebar; `customRequirement` gains `code`, `trigger`, `acceptance` and `preview`.
- `SCHEMA.md`: `app.ui`; "Dashboards: `type: dashboard`"; "Contracts for custom work".
- `DRAFTING.md`: the five-level ladder in "Later turns"; dashboards in the skeleton step; contracts in step 5.
- `SPEC_EXTENSIONS.md`: §3 dashboards, §4 contracts, §5 `app.ui` (the build contract).
- `example.yaml`:
  - Finance lands on a declared `finance_home` dashboard;
  - the custom dashboard and the checklist panel carry contracts;
  - all four custom requirements carry `trigger` and/or `acceptance`.
- `builder/app-studio.html`: dashboard renderer, `app.ui` CSS, build-notes contract, simulated effects; the probe skips dashboards.

Phase D, build skill (`skill_plugin/skills/zango-app-studio`):
- `scripts/spec_check.py`:
  - `UI_RADIUS` / `UI_DENSITY` validation, and `app.ui` in `spec.ui.json`;
  - `DASH_*`, `dashboard_text`, `lint_dashboard` and `contract_text`;
  - trigger lint;
  - contracts appended to every custom hole.
- `assets/frontend/zas/`: `tokens.css`, `config.ts`, `Gallery.tsx`, `types.ts`.
- `references/spec/schema.md` and `references/design-system.md`: `app.ui`.

Phase D, agent mode and console:
- New `agent_mode/custom_work.py`: `custom_requirements`, `contract_gaps`, `counts`. The gate is in `spec_tools.mark_ready`.
- `preview_probe.custom_screens` skips dashboards.
- Console: new `builder/customWork.ts`; the "N custom screens · N custom rules" pill in `TemplateBuilderPanel`, with `.pv-pill.custom` styling.

Tests:
- New `tests/apps/app_templates/test_declared_ui.py` (12 tests): schema, build checker, gate, `spec_check` hole texts, and a headless dashboard render.
- New `tests/apps/app_templates/test_preview_probe.py`: 21 tests, including the headless path walk.
- New `tests/apps/agent_mode/test_preview_focus.py`: 9 tests. It uses a stand-in probe for the workbench, and real headless Chromium for 3 tests, skipped without Playwright.

## How to test

```bash
source ../zango_venv/bin/activate            # i.e. Zelthy-V2/zango_venv
cd backend/test_project
python manage.py test --noinput zango.tests.apps.app_templates.test_preview_probe
python manage.py test --noinput zango.tests.apps.agent_mode zango.tests.apps.app_templates
```

Result (2026-10-15, after phase D): 576 tests; the only failures are the 8 developer-server tests in
`test_skill_plugin.py` that were already failing before this work (see `AGENT_MODE_APP_STUDIO_SKILL.md`).

Dev project (done 2026-10-15):
- `migrate_schemas` applied `0013` and `0014`, and `zango-app` 1.1.12 is current.
- `probe_for` + `check(example)` against the dev DB: 6/6 sketch runs clean.

Manual end to end:
1. Restart the Celery worker: `celery -A local_dev_project worker -l INFO -Q celery,agent_mode`.
2. In a "Describe it" requirement, ask for a dashboard. The analyst's tool results should show "Custom screens this edit changed …" with KPI values. It should call `preview_look`, and `spec_mark_ready` should be refused until it has.

Live check, phase D: the preview header on `stockist_onboarding` shows "1 custom screen · 1 custom rule".

Live check in Chrome (vite dev server on :5173, Django on :8000, app `stockist_onboarding`):
- **Point → Status column**: the chip reads "Pointing at Status column · My Applications · as Stockist", with the path `/modules/@core/entities/@stockist_application/table/columns/@status`.
- **The full-page preview** opened at the hashed place. Pointing there at the City column set the chip in the chat tab.
- No message was sent during the check.

### Fixes after user testing (2026-10-15)

**1. The analyst rewrote `text` instead of sketching.**
- User report: they pointed at the "Next Steps" custom panel and asked for "what will actually come". The analyst rewrote the panel's `text` (the grey placeholder) and offered "Ready to build?".
- What was right: the tools did report "✗ … No preview sketch yet", and `spec_mark_ready` would have refused.
- The fixes:
  - (a) `SpecWorkbench._after_edit` appends a directive "NOT DONE: … no `preview` sketch … changing `text` changes nothing they can see" for every touched unsketched screen.
  - (b) `focus_note(focus, spec_doc)` adds a line when the user points at an unsketched custom screen. `tasks._plain_spec(req)` supplies the doc.
  - (c) `_SPEC_TOOLS_APPEND`: call `spec_mark_ready` before offering to build, and never offer while it refuses.

**2. Pointing at a table row did nothing.**
- Now the whole table card points at `<entity>/table`, each cell at its column, each quick-filter chip at its filter, and the Add button at `<entity>/form/create`.
- 360 banners and badges have their own paths.
- A click on something without a path falls back to the page instead of doing nothing.
- Template 1.1.13 → **1.1.14**.

**Chrome flows tested (all pass):**
- a cell → `table/columns/@city`, "Mumbai";
- empty table space → `table`;
- New Application → `form/create`;
- menu item → `/roles/@Stockist/menu/0`;
- empty page → `/pages/@my_applications`;
- 360 Company Info → `sidebar/0`;
- Activity tab → `tabs/@activity`;
- banner → `header/banners/1`;
- Verified badge → `header/badges/0`;
- Next Steps → `sidebar/1`;
- Esc cancels Point;
- the full-page tab deep-links to a 360 record.

**3. Gates the model can skip, and checks that read as a pass (from the analyst transcripts).**
- Where the transcripts are: `<project>/.agent_mode/home/.claude/projects/<workspace-slug>/<AgentRequirement.session_id>.jsonl` (every thought, tool call and result), plus `.agent_mode/home/.claude/debug/<session_id>.txt`.
- Board turn (Haiku 4.5, set by `AgentModeSettings.analyst_model`):
  - it offered "Build the app?" without calling `spec_mark_ready`;
  - it added the board to all three list pages, though the user pointed at one.
- Verifier Workload turn (Sonnet 5.5):
  - the automatic check said ✓ while the board drew a single "Unassigned" column;
  - no screenshot was taken (`sketch_looks` stayed `{}`);
  - `assigned_verifier` was generated from any user, or none.
- The fixes:
  - (a) **Approval gate on the server.** `template_spec.unfinished_custom_work()` is called from `approval_problem()` and refuses with a 409 and `issues` for unsketched custom screens and `contract_gaps`. `AgentPage.onCommit` sends the list back to the agent as a message. The look gate stays in `spec_mark_ready` only, since Playwright is not run in a web request.
  - (b) **Automatic screenshot.** `SpecWorkbench._auto_look()` runs after an edit changes a sketched custom screen that drew without error and has not been looked at since it changed. It covers up to `AUTO_LOOKS` = 2 screens per edit, within `MAX_LOOKS` = 8 per turn. The PNG is queued in `_pending_images`; `make_handler` sends it before the text, and the screenshot updates `sketch_looks`. `preview_look` now shares `_look()`.
  - (c) **Field reads.** In the preview, `ctx.rows` / `ctx.related` / `ctx.record` return read-through proxies (`pvWatch`, unwrapped by `PV_RAW` in `rowEntity` and `ctx.fmt`). These record each field a sketch reads, and `probeRun` warns: "`<entity>.<field>` is empty on all N demo row(s) the sketch read it from". `format_result` marks any run with warnings or empty parts as ⚠ instead of ✓.
  - (d) **Role-aware demo users.** `userRoleOf(f)`: a link to `app_user` whose key or label names a role (`assigned_verifier`) picks from that role's users, filled 85% of the time.
  - Template **1.1.15**. `_PREVIEW_TOOLS_APPEND` explains ⚠ and the attached screenshot.
- Tests: `AutoLookTests`, `ApprovalGateTests` and two headless tests (an empty-field warning, role users) in `test_preview_probe.py`. Result: 588 run, and the only failures are the 8 existing `test_skill_plugin` ones.
- Verified on the live Stockist spec: the check now reports ⚠ for `assigned_verifier` and `submitted_at`, and approval would be refused for 4 missing contract items.
- **No "is it finished?" step for the user (template 1.1.16).** The user looks at the preview and presses Commit for build. Nothing else is asked of them.
  - The analyst is told never to ask whether to finish, mark ready or build (`_SPEC_TOOLS_APPEND`, INTERVIEW.md).
  - `SpecWorkbench._contract_nudge()`: an edit to pages, 360 views or custom requirements returns "NOT DONE: these custom parts have no contract yet" with `contract_gaps`, so contracts get written in the turn that adds the screen.
  - `AgentPage.onCommit`: a 409 with unfinished custom work sends the list to the agent, then commits again automatically once the agent's turn ends (a single retry). If the work is still unfinished after that, the error is shown.
  - Tests: `ContractNudgeTests`. Result: 591 run, and the only failures are the 8 existing ones.
- **Still open:** the spec cannot steer demo values (no per-field `demo` hint), so when a screen needs a value that is rare in the generated data, the analyst can only tell the user.

## Notes / gotchas

- **The console bundle could not be rebuilt.** `console/src/pages/app/logs/` (AccessLogs, AuditLogs) is caught by `.gitignore`'s `logs/` rule and was never committed, so `vite build` fails on `LogsPage.tsx`.
  - The committed bundle in `backend/src/zango/assets/console` is unchanged and does **not** include phase C yet.
  - Test with `npm run dev` in `console/` (http://localhost:5173/console/…).
  - Before release: add `!console/src/pages/app/logs/` to `.gitignore`, commit those sources, then `npx vite build`.

- The first check of a turn waits for Chromium to start (about 10 s).
- **Screenshots use the seeded demo data.** Numbers are stable across runs but change when the spec changes the data shape.
- `ctx.today` uses the real date, so date-based KPIs move day to day.
- `probe_for` reads the template version on the tenant-bound thread. The tool handlers never touch the ORM.
