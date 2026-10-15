# Agent Mode: Spec-to-Build (part 2)

The plan: `Spec-to-Build Plan.html` (https://claude.ai/artifact/7yHY9VGQh7hK1eH5GUmimE). Part 1 progress: `AGENT_MODE_PREVIEW_SPEC_PLAN.md`.

## Goal

The approved spec reaches the build agent so the built app looks like the preview the user approved, custom screens included:
- **Structure:** port each custom screen's `preview` sketch onto the build's design system (`zas/ui.tsx`), call for call.
- **Look:** a screenshot of every customised screen, plus variants whose structure differs.
- **Check:** a kit-tree parity check in text, then one look per screen.

## Phases

| Phase | What | Status |
|---|---|---|
| F1 | Sketch kit in the design system (`zas/ui.tsx`, `tokens.css`, Gallery), `data-zas-kit` markers in both preview and runtime | **done** |
| F2 | Approval bundle (sketch, contract, kit trees, screenshots) | **done** |
| F3 | Build guidance and hole text (`spec_check.py`, custom-code.md, SKILL.md, prompt) | **done** |
| F4 | Parity check (`zas_test parity`) and the one look | **done** |

## Decisions (2026-10-15)

- No demo data in the built app: it is a real app. Parity compares structure, never values.
- Hand-written markup in sketches is allowed. The analyst gets a warning; the build uses the screenshot and text for those parts.
- A parity failure goes through the agent's test loop (up to 2 fix attempts per screen); what is left is a warning in the build report.
- The comparison screenshots are for the agent only, not shown to the user.

## Changes

### F1: the sketch kit in the design system (done)

- **`zas/ui.tsx`** (skill `assets/frontend/zas/`):
  - New components, with the same arguments as `ctx.ui`: `Stack`, `Grid`, `Kpis`, `Bars`, `List`, `MiniTable`, `Board`, `Progress`, `KitEmpty`, `KitBadge`.
  - `Panel` gains `icon`, `note` and `kit` (backward compatible).
  - `goUrl(go)` / `useGo()` resolve a sketch's `go` (`"page"`, `"page:<id>"` or a URL). A detail page opens the record through `detailUrl`. Outside a router it falls back to `location.assign`.
  - `List` and `MiniTable` cells take a field key (a `FieldValue` shows its `display`) or a function.
- **`tokens.css`:** a "sketch kit" block (`.zas-kstack`, `.zas-kgrid`, `.zas-kbar`, `.zas-kli`, `.zas-kboard`, `.zas-kcol`, `.zas-kcard`, `.zas-ktrack`, `.zas-kbadge`…) with the preview's values, written with runtime tokens and no hex colours.
- **Markers, the same on both sides:**
  - `data-zas-kit="kpis|bars|list|table|board|panel|progress|stack|grid"`, `data-zas-title`, and `data-zas-item` (KPI labels, table columns).
  - The preview's `previewUI` draws them too; `panel` takes an internal `kit`.
- **`scripts/zas_test/kit_tree.js`:** one extractor, `(root) => [{kit, title?, items?, children?}]`, for both the preview (bundle) and the built app (parity). Values are left out on purpose.
- **Gallery:** a `kit` section with fixed rows; `design.py` `SECTIONS` adds `"kit"`. Its golden is not shot yet; re-shoot with `zas_test.design --make-goldens`.
- **Analyst:** `format_result` adds a note on hand-written markup: the build can only match it from a screenshot, so use `ctx.ui` where a block fits.
- Template **1.1.17**.
- **Tests:** `tests/apps/app_templates/test_sketch_kit.py` (6):
  - a CSS twin check, rule for rule, with tokens resolved;
  - no hex in the kit block;
  - components and markers exist;
  - gallery section;
  - a headless extractor run on the example dashboard. The hand-written checklist panel gives `[]`.
- **Change from the plan, "one stylesheet":** the preview keeps its own CSS. A test pins every kit rule to its runtime twin instead, because moving the 650 KB preview onto `tokens.css` is a large rewrite for no visible gain.
- **Type-check:** `ui.tsx` and `Gallery.tsx` compile under `strict` with the console's TypeScript and React types. `lucide-react` and `@zango-core/crud` were stubbed, since no workspace has `node_modules` installed. The kit has not yet rendered in a real built app; that happens with F4's parity run.

### F2: the approval bundle (done)

- **`agent_mode/approval_bundle.py`** (new). `write_bundle(spec_text, out_dir, probe=…)` writes:
  - `index.md`: read first. One section per custom screen: its folder, a kit outline per role variant, the screenshot paths, and notes on hand-written parts.
  - `manifest.json`: the same as data.
  - Per screen, `screens/<screen>/`:
    - `sketch.js`;
    - `contract.json` (title, text, data, interactions, states, acceptance, refs, component, roles, show_when);
    - `view.<role>.json` (roles, record, kit tree, `hand_written`, draws, excerpt, warnings);
    - `shot.<role>.png`;
    - `in_page.<role>.png` for tabs and panels, showing the screen in its 360 page.
  - `screen_folder(path)` turns `/detail_views/@v/sidebar/2` into `detail_views.v.sidebar.2`.
- **Variants:** roles whose kit tree is identical share one view and one screenshot. A hand-written sketch has no tree, so each role is its own variant. At most 3 variants (`MAX_VARIANTS`).
- **`preview_probe_worker.py`:** new ops:
  - `sketches`;
  - `capture`, which runs one screen for every role: `ZAS_PROBE.run` + `show`, the kit tree from `kit_tree.js` on `[data-zas-sketch]`, a group-by-tree step, screenshots, and the in-page shot of `.z-content`.
  - `PreviewProbe.sketches()` / `capture()` use `CAPTURE_TIMEOUT` = 120 s per screen.
- **Where it runs:**
  - `StudioBuild.prepare(emit, template)` calls `write_bundle` right after `spec_check`, writing `<ws>/.zas/bundle/` from the approved spec. `tasks.py` passes `template_build.template`.
  - It is recorded as step `studio:bundle`. A failure is a skipped step with the reason; the build goes on without a bundle.
- **Change from the plan:** the bundle is written at build prepare (a Celery task), not by its own task at Commit. The approved spec is frozen at Commit, so the result is the same, without another task or file storage.
- **Measured on the Stockist spec:**
  - 3 screens in 3.9 s, 296 KB.
  - Verifier Workload: kpis + board.
  - Rejection Analysis: kpis, 2 bars and a table with its 5 columns.
  - Next Steps: a list; all 4 roles share 1 screenshot, plus the in-page shot.
- **Tests:** `tests/apps/agent_mode/test_approval_bundle.py` (8):
  - folder names;
  - without a probe;
  - variants, views and screenshots;
  - a capture error;
  - an unsketched screen;
  - StudioBuild writes the bundle into `.zas/`, and a failure is a skipped step;
  - a headless run on the example.

### F3: build guidance and hole text (done)

- **Order in `StudioBuild.prepare`:** `write_bundle` now runs **before** `spec_check.py`, which does not wipe `.zas/`.
- **`spec_check.py` `attach_bundle(holes, out)`:** reads `.zas/bundle/manifest.json`. Each `custom_page` / `custom_tab` / `custom_panel` hole with a sketched screen gets:
  - `bundle: ".zas/bundle/screens/<folder>/"` in `spec.resolved.json`;
  - in the text: "Approved look: `…`. Port its sketch.js call for call onto the zas kit… the kit outline in .zas/bundle/index.md is what parity checks."
  - "Parts are hand-written markup: match them from its shot.*.png." when a variant is hand-written.
  - The hole `where` `detail_views.v.sidebar[2]` maps to the folder `detail_views.v.sidebar.2`. Without a bundle the holes are as before.
- **`references/custom-code.md`:** a new section, "Porting a sketch":
  - the bundle files;
  - a `ctx.ui` → kit mapping table;
  - what must carry over exactly (and that parity checks it);
  - data logic moves to the hook / `<page>__data` view, which returns what the kit needs;
  - the four states and the contract as tests;
  - hand-written parts are built from the screenshot;
  - role variants.
  - The Slots design-system bullet now lists the kit.
- **`references/design-system.md`:** the component table lists the kit.
- **`SKILL.md`** Phase 6 step 5: a hole that names `.zas/bundle/screens/…` is ported block for block.
- **`prompt.py` `compose_studio_prompt`:** when `.zas/bundle/index.md` exists and the frontend is built, the build steps say the user approved each custom screen, and to port each sketch onto the kit, which the platform checks.
- **Tests:**
  - `HoleTextTests` (2) in `test_approval_bundle.py`: holes name their folder and the hand-written note; no bundle leaves the text unchanged.
  - The `PromptTests` bundle line in `test_studio_build.py`.

### F4: parity check and the one look (done)

- **`scripts/zas_test/design.py`:** a new group, `parity`, in `GROUPS`.
  - For each bundle screen whose hole has a `bundle`, and each variant (its first role), it signs in, then opens:
    - a custom page's route;
    - for a panel or tab, the hero's 360 on a visible test record. A tab or a section inside one clicks `[data-zas="tab"][data-zas-key=…]` first.
  - The root is `[data-zas="page"]`, or `[data-zas="panel"][data-zas-key=<hook key>]` (the key comes from the hole function `<view>__custom__<key>`).
  - It runs `kit_tree.js` on the root and calls `parity_diff(approved, built)`, a `difflib` comparison of `(kit, title)` in order, then labels and columns. Values are never compared.
  - The built screen is saved to `.zas/screens/parity/<folder>.<role>.png`, and the pairs to `.zas/parity_looks.json`.
  - A hand-written variant is a skip, though the look still gets its pair.
  - No bundle: one skip with the reason.
- **`report.py`:** `NON_BLOCKING` adds `design.parity`. Leftovers make the verdict "Ready with gaps", never "Not ready".
- **`studio_build.py`:**
  - `DESIGN_BROWSER_GROUPS` adds `parity`, so failures reach the existing fix rounds (`AGENT_MODE_STUDIO_FIX_ROUNDS`, default 2).
  - `blocking(layers)` ignores `NON_FAILING = ("design.parity",)` for the run's `ok`.
  - **The one look:** after the fix rounds, when the bring-up is OK and nothing waits on the user, `look_digest()` lists approved/built screenshot pairs. `resume_agent` sends it, and the agent opens them with Read and fixes what does not match. Then design `parity` (plus any failing groups) runs again.
- **Docs:**
  - testing.md, design-system.md: the parity rows (no longer "skipped").
  - contracts.md: the kit markers.
- **Tests:**
  - `tests/apps/agent_mode/test_preview_parity.py` (12): the diff (equal, missing/extra, labels, columns order, nesting, renamed title), the target for page / panel / tab-section, the no-bundle skip, non-blocking in the report, the look digest, and `blocking()`.
  - `test_sketch_kit.RuntimeKitParityTests` bundles the **real `zas/ui.tsx`** with the console's esbuild and React, renders a screen, and renders the same screen as a preview sketch. The kit trees are identical, and 11 element pairs have identical computed styles. Checked by eye side by side as well. It skips without the console's `node_modules` or Playwright.
- **Full run:** 620 tests; the only failures are the 8 existing `test_skill_plugin` developer-server ones.

## Not done / next

- **Not yet run end to end in a real build.** That needs a fresh App Studio build with the Celery worker restarted, so that:
  - the bundle appears in `<ws>/.zas/bundle/`;
  - holes say "Approved look";
  - the agent ports the sketches;
  - `design parity` runs;
  - the one look happens.
- **Gallery `kit` golden:** not shot. Run `zas_test.design --make-goldens` on the platform the goldens are compared on.
- **Hand-written sketches** are matched only by eye (the look). The example's checklist panel is one.

## Notes / gotchas
