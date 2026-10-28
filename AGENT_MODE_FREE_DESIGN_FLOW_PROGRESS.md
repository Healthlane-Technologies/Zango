# Free design build flow: implementation progress

Plan: `AGENT_MODE_FREE_DESIGN_FLOW_PLAN_v2.html` (same content as `AGENT_MODE_FREE_DESIGN_FLOW_PLAN.html`).
Benchmark app: `zango_isn_hcp` (tenant `a02cab7b-b132-469f-b483-c107d85b7df9`), workspace
`Zelthy3_projects/local_dev_project/workspaces/zango_isn_hcp`.
`skill…` = `backend/src/zango/apps/agent_mode/skill_plugin/skills/zango-app-studio`.

Status legend: ✅ done and verified · 🟡 done, not yet verified end to end · ⏳ in progress · ⬜ not started

## Stage 1: unblock + real references

| Step | Status | What changed | Verified by |
|---|---|---|---|
| A1 field-vs-field rules on forms | ✅ | `skill…/assets/backend/zas_core/mixins.py`: `_FormRecord(values, instance, model=)` carries the model's `_meta`; both call sites pass the form's model. Selftest check added in `skill…/scripts/selftest_runtime.py` ("expr field vs field on a form record"). Workspace: copied the fixed `mixins.py` into `zango_isn_hcp/backend/zas_core/` and removed the agent's `_CaseFormRecord` swap from `backend/cases/forms.py`. | Selftest passes on the fixed runtime and fails on the original. |
| A2 date picking in UI flows | ✅ | `skill…/scripts/zas_test/flows.py` `fill_date`: jumps a year at a time with react-calendar's « » buttons, then by month (up to 240 clicks). Confirmed the crud datepicker renders prev2/next2 in month view. | UI layer on `zango_isn_hcp`: `ui.flow.case.create.hcp` passes (it failed on the DOB before). |
| A3 scenario runner | ✅ | `skill…/scripts/zas_test/scenarios.py` `load()`: puts `.zas/` on `sys.path`, so `from test_fixtures import …` works. | A temporary workspace with a scenario importing `test_fixtures` loads. |
| A3b `'list' object has no attribute 'get'` | n/a | This was the agent's own scenario bug, fixed by the agent in run 2 (H-32 passed). Not a platform bug; dropped from the plan. | n/a |
| A4 cron in platform:schedule | ✅ | Already fixed in `94e7703c`. | Run 2 bring-up scheduled the tasks. |
| B1 fresh page per screen | ✅ | `agent_mode/preview_probe_worker.py` `open_capture`: `fresh()` opens a new page (same browser and context) for the manifest read, each screen × role, and each row probe. CSS is taken on the same page as its DOM: `OPEN_CSS_TEXT_JS` now returns one string per rule (whole `@media` blocks), deduplicated across roles. Load errors and blocked URLs are deduplicated. | ISN prototype: 20 of 24 screens render (was 4). Still blank, crashing in the mockup's own script even on a fresh page: `form`, `email` (hcp, specialist), `sp`, `sp-accepted`. That's B2's job. CSS braces balance. Capture takes 39 s (was 16 s). |
| B4 blank reference ≠ pass | ✅ | `skill…/scripts/zas_test/design.py` `open_parity`: a role whose reference is blank, errored or has no shot gets a **skip** "no reference: <why>" and a `no_reference` row in `parity_looks.json` with no score. It's a skip, not a fail, because the agent can't fix a reference; F1 will route it to us. | Parity on the old bundle: 18 "no reference" skips with reasons, 5 real comparisons, and no 0% scores against blank references. |

**Stage 1 check on `zango_isn_hcp`** (live server, the agent's workaround removed):
- API layer: 55 passed, 1 failed. Case-create checks that failed before now pass. Remaining failure: `row_action.case.delete_draft` (HTTP 500 "Must be Case instance"), an app-code bug.
- UI layer: 24 passed, 4 failed. Case create passes. Remaining: `/portal/downloads/` and `/portal/dashboard/` return HTTP 500, and the Send dialog doesn't open. All app-code, for the agent.
- The workspace bundle still holds the old blank capture. The next build regenerates it with B1.

## Stage 2: mockup check before approval

| Step | Status | What changed | Verified by |
|---|---|---|---|
| B2 sample + params per screen | ✅ | Root cause: the ISN mockup opens `form` with `{id, step}` and `sp`/`sp-accepted` with a case that has a referral, but the bridge only got `record`. Manifest screens may now carry `params` (an object; validated in `prototype.manifest_of`). The capture passes `meta.params` to `ZAS.go` (`preview_probe_worker.OPEN_GO_JS`), and the runtime forwards it to the imported page's bridge (`prototype_assets/zas-proto.js` `custom.go(screen, {role, record, params})`). `skills/zango-prototype/SKILL.md` tells the analyst to copy how the page itself opens each screen into `sample`/`params`, and the bridge example forwards `params`. | Re-assembled the ISN parts with the new runtime, a bridge that forwards `params`, and `form.params={step:1}` plus `sp`/`sp-accepted`/`email` samples: **24 of 24 screens render, 0 errors**. The `form` shot shows the 6-step create-case wizard. |
| B3 gate the approval | ✅ | `prototype_coverage.render_gaps(bundle)`: built screens (not `only: prototype`) whose snapshot is blank or threw, one line per screen × role. `spec_tools._check_prototype_coverage` refuses "mark ready" with `RENDER_GUIDE` (set `sample`/`params`, make the bridge pass `params`, or mark prototype-only). `coverage_issues` adds the same as approval errors, so Commit is blocked too. **Deviation from the plan:** the build-side backstop doesn't refuse the build (that would strand an already-approved requirement and show the creator a failure). Instead `approval_bundle.prototype_index_md` lists "**No reference** for: …" and tells the build agent not to read those blank shots as the design. | 2 new tests in `test_prototype_coverage.py` (refusal text; a blank prototype-only screen is no gap). On the real captures: the old one gives 3 gaps (`form`, `sp`, `sp-accepted`; `email` is prototype-only), the fixed one 0. |
| C1 screen links in the YAML | ✅ already existed | `prototype.screens[].maps` (`/pages/@…`, `/detail_views/@…`) is written by the analyst and validated by `spec_check`. That's where the bundle's "Maps" column came from. Nothing to build. | `test_prototype_coverage` fixtures use it. |
| C2 field coverage | ✅ already existed | `prototype_coverage.coverage()` already refuses mark-ready when the YAML drops a menu item, column, status tab, section or button the screen shows. On ISN it had nothing to check because 20 screens captured blank. B1–B3 make it effective. | Existing tests (`CoverageTests`, `MarkReadyTests`, `CommitTests`). |

Tests: `cd backend/test_project && …/zango_venv/bin/python manage.py test --noinput zango.tests.apps.agent_mode.test_prototype_coverage zango.tests.apps.agent_mode.test_approval_bundle zango.tests.apps.agent_mode.test_preview_parity zango.tests.apps.agent_mode.test_ui_flows zango.tests.apps.app_templates.test_prototype`: 90 tests, OK.

Not done: the ISN requirement's own stored parts (bridge + manifest) still have the old bridge. Re-running the analyst on it, or patching its manifest/bridge, is part of the benchmark re-run.

## Stage 3: slices + failure routing

| Step | Status | What changed | Verified by |
|---|---|---|---|
| E1 slice plan | ✅ (simplified) | No `slices.json`. The agent names a slice's spec paths when it checks it. The order is in the skill (E3): foundation (all models, app module, shell, first build), then the main record's slice, then the records it depends on, then `plan.md` order. Writing all models first keeps migrations and foreign keys sane. | n/a |
| Test scope | ✅ | `zas_test/__init__.py`: `ZAS_TEST_SCOPE` (comma-separated spec paths) with `in_scope()` on segment boundaries (`entities.case` ≠ `entities.case_document`). `check()` in api/ui/design skips out-of-scope checks; scenarios skip holes outside the scope. `save_results` replaces only in-scope results and drops stray out-of-scope ones. | `test_build_slices.ScopeTests`. Live: `ZAS_TEST_SCOPE=entities.case zas_test.api` ran 15 checks and kept the other 51 API results. |
| E2 `studio_verify` tool | ✅ main-thread half live; 🟡 the agent's side needs a real run | New `agent_mode/studio_tools.py`: an in-process MCP server `zas_build` with `studio_verify(paths)` and `report_platform_issue`. A tool call is a `ToolCall` pushed onto the stream queue (`kind="tool_call"`); `tasks._drive_stream(on_tool_call=…)` runs it on the main thread (tenant connection, ORM-safe) and replies; the tool waits off the event loop. `verify_slice` = `bring_up` + `verify(only={api, ui, design:[parity], scenarios}, scope=paths)` → a slice brief (reported platform issues left out). `StudioBuild.verify(scope=)` / `_run_layer(scope=)` pass `ZAS_TEST_SCOPE` and read back only in-scope results. `options.build_agent_options(tool_push=)` registers the server for studio builds (new run and fix rounds) and sets `MCP_TOOL_TIMEOUT` to 23 min. During fix rounds the tool reuses `finish()`'s open service account (`StudioBuild.live_creds`); opening it again would reset its password and disable it on exit. | `test_build_slices.ToolTests` (5), `test_build_skills.test_a_studio_build_gets_the_slice_check_tools`. **Live on `zango_isn_hcp`** (Django shell, real tenant and service account): `studio_verify(["entities.case","pages.my_cases"])` took 162 s, all 11 bring-up steps passed, and the reply lists exactly the slice's 4 failing checks (delete_draft 500, Send dialog, `dash` parity gaps, H-09/H-12 send). |
| E3 build order in the skill | ✅ | `skill…/references/server-mode.md`: new section "Build in slices, and check each one yourself"; the fix-rounds paragraph mentions `report_platform_issue` and the repeat rule. `SKILL.md` Phase 2: don't patch the runtime from app code; inside the platform, report it. | `test_skill_plugin`: the same 7 failures + 1 error as the baseline (pre-existing, see below). |
| E4 final loop stays | ✅ | Unchanged apart from F1/F2. | Existing `test_studio_build` tests pass. |
| F1 owner per failure | ✅ mostly existed | `studio_status.kind()` already kept our own test-code exceptions ("harness") away from the agent. New: `StudioBuild._for_agent(layers, stuck)` = without harness, without reported platform issues (`.zas/platform_issues.json`), without stuck checks. The fix loop's condition, `sort_failures` and the digest use it; the verdict still counts everything. **Finding:** the ISN form-rule bug surfaced as an ordinary HTTP 400 from the app, so no traceback rule would have caught it. Only the agent can tell, hence `report_platform_issue`. | `RepeatTests.test_a_reported_platform_failure_gets_no_round`. |
| F2 repeat detector | ✅ | `_signature(failure)` = check id + the first 200 characters of the detail with numbers and UUIDs masked (a retried create gets a new ZC number). A failure sent in a round that comes back with the same signature is "stuck": not sent again, still in the verdict, and announced in the run log. | `RepeatTests` (signature ignores record numbers; a failure that doesn't move gets exactly one round). |
| F3 no runtime patching | ✅ | `guards.runtime_tamper`: Write/Edit/MultiEdit under `<ws>/backend/zas_core/` are denied, and so are `.py` writes that assign to a name imported from `zas_core` (e.g. `_zm._FormRecord = …`, `ZasFormMixin.clean = …`), with a message pointing to `report_platform_issue`. The platform's own copies use `cp`, not these tools. | `RuntimeGuardTests` (4, including through the hook). |

Tests: `test_build_slices` (15, new), `test_build_skills` (4), `test_studio_build`, `test_guards`, `test_stream_background`, `test_fix_round_totals`: all pass. **Full `agent_mode` + `app_templates` suites: 802 tests, 18 failures + 1 error, all pre-existing.** Checked by stashing only this work's files and re-running the failing tests on the baseline: identical 18 + 1 (pack starter/example checks, `test_skill_plugin` text checks, `test_preview_focus` wiring, `test_sketch_kit`).

Still to prove with a real build: the agent actually calls `studio_verify` per slice, the pump-side wait (the MCP call blocking for minutes) holds, and turns/cost compared with run 1+2 (160 turns, $25).

## Stage 4: kit from the mockup

Generic for any prototype: the platform hard-codes no mockup's pieces. The build agent reads each app's
prototype and writes that app's kit and map; the platform only crops by the map's selectors and compares.

| Step | Status | What changed | Verified by |
|---|---|---|---|
| D1 same interface as the default kit | ✅ | New runtime `assets/frontend/zas/kit.tsx`: each piece (`Button`, `Badge`, `Chip`, `Panel`, `StatTile`, `Tabs`, `Timeline`, `FieldGrid`, `Drawer`, `Modal`, `EmptyState`, `Banner`, `Kpis`, `Bars`, `List`, `MiniTable`, `Board`, `Progress`, `ZasTable`, `makeShell`) is the app's own from `src/custom/kit/index.ts` when exported, else the default. Resolved at render time, so a custom piece can wrap the base one without an import loop. `ZasTable`, `Detail360`, `ListPage`, `dialogs`, `renderers` and `CustomPage` import those pieces through `./kit`; `zas/index.ts` re-exports the kit over `./ui`. **Deviation:** no Vite alias. The Vite config comes from the scaffold, and the kit module needs no config. Stub `assets/templates/frontend/kit/{index.ts,map.json}`, copied by `prepare_frontend` when missing (never overwritten) and by SKILL.md Phase 6 step 2. | Scratch frontend (a real app's `src` + new runtime): `tsc --noEmit` clean, `npm run build:zango` OK with and without an override. Vite harness + Playwright: the app's Button reaches the runtime's own `ConfirmDialog` (2 of 2 buttons), the default gallery stays on the base kit, no console errors. |
| D2 kit map | ✅ | `frontend/src/custom/kit/map.json` (**deviation:** not `.zas/kit.map.json`, because the gallery imports it): `{id, component, props, mockup: {screen, role, selector, index}, built?}`. `zas_test/kit.py` `map_problems`: real screen and persona, a known piece, unique ids, and every piece `index.ts` exports has an entry. `ZasTable`/`makeShell` are left to screen parity. | `test_kit.KitMapTests` (5). |
| D3 kit gallery (internal) | ✅ | `Gallery.tsx`: `/app/__zas?kit=mockup[&piece=<id>&w=<px>]` draws each map piece with the app's kit and the map's props (icon names → `<Icon>` for Button/EmptyState/Modal). The default gallery and goldens are unchanged. The test writes `.zas/screens/kit/index.html`: each prototype crop next to the app's piece. | Harness: gallery kit mode renders and is shot. |
| D4 automatic diff gate | ✅ | `zas_test.design --only kit` (`kit.py g_kit`) crops each piece from the live `prototype.html` (opened as the capture opens it: `ZAS.go` with sample/params) and shoots the app's piece at the crop's width. Score = the larger of the share of differing pixels (both centred, 1.5 px blur, never stretched) and the size gap; over 5% fails `design.kit.<id>` (spec path `kit.<id>`). `studio_build`: `kit` is in the design groups; `design.kit` is NON_FAILING (report `NON_BLOCKING` too) and is kept out of the fix rounds (`_for_agent`). New `kit_rounds()` (`AGENT_MODE_KIT_ROUNDS`, default 3) runs before the look rounds with `kit_digest`: re-run kit only (scope `kit`, merged back into the design layer by `_merge_scoped`), stop when all pieces pass or the agent changes nothing. Look rounds then re-shoot. `studio_verify` accepts `kit` paths, and `SLICE_LAYERS.design` includes `kit`. Creator approval: none. | Real crop from a prototype vs a harness piece: visually identical, 2 px narrower → **3.6%** (the first pixel-exact metric said 14%, so I replaced it); a white button vs the prototype's → ~97%. `test_kit.KitScoreTests`, `KitRoundTests` (3 rounds then report gap with the build OK; stops after 1 round once it matches; scoped merge). |
| D5 drop "theme" | ✅ | `spec_check`: class `theme` → **`kit`** ("standard page drawn with the app's kit"); index.md table "kit or rebuild". `design.py` accepts both (`STANDARD_CLASSES`) for specs checked earlier. Kit lint (`kit_problems`): colours = tokens or the prototype's own CSS palette; `kit.css` selectors only on kit markup (`.zas*`, `.zk-*`, `[data-zas…]`); no import of `../../zas` / `../../zas/kit` from the kit; kit code refused in default design. `open-mode.md`: new "The kit" section; Screens table "kit or rebuild". `server-mode.md`: the Free design foundation slice builds the kit and checks `{"paths": ["kit"]}`. `approval_bundle` index.md: build the kit first. The look-round digest names the kit as the lever. Pack `SCHEMA.md` still says "themed": left so the pack keeps 1.1.22 (no re-import). | `test_declared_ui` (class `kit`), `test_kit.KitLintTests` (3), `test_preview_parity` updated. |

Tests: `test_kit` (17, new). **Full `agent_mode` + `app_templates`: 820 tests, 18 failures + 1 error: the same pre-existing set as before Stage 4.**

Still to prove with a real build: that the agent picks sensible pieces and selectors from a mockup, how many kit rounds that takes, and the screens' median parity after the kit.

## Next
1. **Benchmark build**: `zango_isn_hcp` was deleted on 2026-10-27 (app, schema, domain); the user re-runs it
   as a new app with the requirement and mockup imported again. That build exercises Stages 1–4 together.
2. Measure it: kit pieces within 5% after the kit rounds, the screens' median parity, turns and cost
   against run 1+2 (160 turns, $25).

## Notes and decisions
- 2026-10-27: Stage 4 must stay generic: nothing is built for one particular prototype (user).
- 2026-10-27: The kit step is an automatic gate. App creators never approve it (user decision).
- 2026-10-27: Creators see progress, not failures. Kit gaps and platform issues go to the internal report.

## Stage 5: what the called_isn_hcp run (2026-10-28) showed

Run 2 on 1.1.22 with Stage 1-4: verdict "Not ready", 24/25 design checks failed, the app looks unlike the mockup.

Root causes (all in the pipeline, none app-specific):
1. Capture never checks it landed: `form` and `help` references are the My cases screen (help is a toast in the mockup, form needs a record). OPEN_GO_JS does not compare ZAS.state.screen with the asked screen.
2. Shell chrome = intersection over every captured screen of a persona; 5 shell-less screens (link pages, email) empty it, so sidebar labels are demanded on every screen; every screen fails on the same unfixable items and the fix loop drops them after one round.
3. Prototype tooling (the mockup's screen jumper, "Open screens", "Screens") is treated as app content.
4. Parity opens routes literally: `/app/cases/:id/review`, `/app/r/:token`; record pages show "Case not found"; the four link states all open the same URL.
5. look_score is a mean grey difference: a structurally different page scores 5%; it cannot drive look rounds.
6. No demo data: the app (and every parity shot) shows API-fixture junk ("Test Full name 2an60z", "NA", 17 drafts); test users are not named after the personas.
7. Kit stage did nothing: map had 3 pieces, kit exports none (17 lines of CSS); nothing requires the map to cover the pieces the screens use.
8. Shell is makeShell options only: cannot draw the mockup's persona card, CTA, nav counts. Landing page is hoisted out of its menu group by zango_platform.py.
9. Raw ISO timestamps reach the screen (Case 360 header); no check catches them.
10. Feedback budget: 2 fix rounds, 2 look rounds of ~1 min each for 20 rebuilt screens.

### Stage 5 proof (2026-10-28, called_isn_hcp by hand)

My cases and Case 360 ported from the prototype's own code (Dashboard(), Case360()) with its stylesheet scoped
under `.zp` and its seed data loaded: near one-for-one with the mockup (look score 0.16 / 0.12 vs 0.59 / 0.57
for the agent's redraw). Needed two backend reads the spec did not give (a row_card column, a case360 view).

### Stage 5 pipeline changes

| # | Change | Where |
|---|---|---|
| E1 | Capture: a screen whose capture shows another screen (router fell back, toast only) gets an error, so parity has no wrong reference | preview_probe_worker.did_not_open |
| E2 | Shell chrome: labels on >= 1/3 (and >= 3) of a persona's screens, not on all (bare link pages emptied it) | design.shell_chrome |
| E3 | Route params: `:id` filled with a record of the entity whose list page the route sits under; a token param skips with the reason | browser.fill_route |
| E4 | Look score: 1 - F1 of edge maps (layout), not mean grey; calibrated on this app (redraw 0.54-0.59, port 0.12-0.16, unrelated 0.44) | design.look_score |
| E5 | Raw ISO timestamps fail ui page, ui detail tabs and parity; zas_core field_value formats dates without a field def, display() in local time | browser.raw_dates, records.py |
| E6 | Port mode: proto_port.py writes `src/custom/prototype.css` (scoped `.zp`) and `.zas/bundle/prototype/source/` + index.md; run by prepare_frontend | scripts/proto_port.py, studio_build |
| E7 | Runtime: no padding around a `.zp` screen | assets/frontend/zas/tokens.css |
| E8 | Lint (open mode): literals allowed when the prototype uses them; inline styles free; prototype fonts; prototype.css must be unedited | design.OpenDesign, prototype_css_problems |
| E9 | Docs: open-mode.md "Port, don't redraw", ported shell, demo data, lint, parity; SKILL.md; hole text; bundle index.md ("never from scripts" removed) | references, spec_check, approval_bundle |
| E10 | Demo data: agent writes backend/demo_data.py load(users); platform runs `agent_mode_demo_data` before design and after the tests; failure = design.demo_data | management command, studio_build.load_demo_data |
| E11 | Test users named after the prototype's personas | zango_platform.persona_name |
| E12 | Shell: ported shell allowed (shellMenu + UserCard + markers); landing page drawn back in its spec group | Shell.tsx regrouped/shellMenu, design.open_shell_problems |
| E13 | Kit optional when every mapped screen is a rebuild | kit.g_kit |
| E14 | Parity: a time-of-day greeting matches any time of day | proto_landmarks.content_gaps |
| T | tests/apps/agent_mode/test_port_mode.py (19); full agent_mode + app_templates: 839 tests, the same 18 failures + 1 error as the baseline | |

Live check on called_isn_hcp: lint passes the ported screens; demo loader via the command (24 cases); parity: no shell noise, link pages skipped with the reason, ported screens 16-17% vs redrawn 38-67%. help/form still compared with the old capture (recaptured on the next build).

| E15 | Look rounds on the score (open mode): send screens over AGENT_MODE_LOOK_LIMIT (0.25) and parity gaps, worst first; stop when all within, a round gains < AGENT_MODE_LOOK_MIN_GAIN (0.03) and fixes no gap, the agent changes nothing, or AGENT_MODE_LOOK_MAX_ROUNDS (5); .zas/look_rounds.json; report shows 58% → 31% → 18%. Default design keeps AGENT_MODE_STUDIO_LOOK_ROUNDS (0 = off in both) | studio_build.prototype_look_rounds, report.look_path |
| E16 | The spec step and Commit for build skip a capture problem on a screen the YAML marks `only: prototype` (they read only the manifest's before); the guide names the fix for a screen that showed another one | prototype_coverage.render_gaps(bundle, doc), spec_tools |

Not done: kit-class crud pages still draw with the kit (Stage 6, planned).


## Stage 6 (planned, not started): copy list pages on a behaviour hook

Decided 2026-10-28, deferred by the user. Plan: AGENT_MODE_FREE_DESIGN_FLOW_PLAN_v2.html phase G.

| # | Step |
|---|---|
| G1 | `useListPage(page)` in the runtime: search, filters, sort, paging (server side), quick-filter counts, export, Add/Edit/Delete forms, row actions + workflow with permissions, view switcher; makeListPage rebuilt on it |
| G2 | Open mode: a mapped crud list page (and its 360) is rebuild by default; `kit: true` keeps the standard page |
| G3 | Copied markup keeps the standard markers; ui.py checks Add, quick filters and row actions on copied pages too (drop the `browser.rebuilt` skip) |
| G4 | Lint: a copied list page may not load every row and filter in the browser |
| G5 | Prove on called_isn_hcp My cases (now client-side over 500 rows, pager inert), then a fresh build |

Why not plain "copy by default": per-page rewiring doesn't scale, drifts from the spec, and is tested less. Backend unchanged either way. About 2 days.
