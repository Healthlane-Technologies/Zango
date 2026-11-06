# AI agents in Agent Mode: implementation progress

Plan: `AGENT_MODE_AI_AGENTS_PLAN.html` (Reference B = console gap list, Reference C = phases).
Branch: `feat/ai-agents-console-p0` (from `feat/agent-mode-default-preview-design` @ 571c5fa0).

## Phases

| Phase | Scope | Status |
|---|---|---|
| P0 | Console AI page at parity with the classic App Panel (`/platform/apps/:id/ai`) | done (4006629a); UI polish later |
| P1 | `ai:` spec section, schema/rules, checker, analyst interview stage 7a, preview, review panel | done |
| P2 | Build: `zas_core/ai.py` runtime, holes, `zango_platform.py ai` step (placeholder + agents) | not started |
| P3 | Placeholder support in Zango (`is_placeholder`, `…/connect/`, `ProviderNotConnected`), Connect pause, AI tests | not started |

## P0 checklist

Route `apps/:appId/ai` (sidebar item "AI"), pages under `console/src/pages/app/ai/`, tabs via `?tab=`.

- [x] API client `console/src/api/ai.ts` covers every route in `backend/src/zango/api/platform/ai/v1/urls.py` (compare + single-version routes typed; compare is done client-side from inline versions)
- [x] Route `ai` + sidebar entry under Operate; Settings → AI tab removed (`?tab=ai` redirects to `../ai`); `AiSettings.tsx` deleted
- [x] Providers: list + stats, add drawer (service cards from `providers/available/`, credential fields per service, "check credentials and load models" via fetch-models with auth_error vs fallback handling, default model, name, rate limit, budget), edit (blank secret = keep, re-validates after a key change), per-model on/off, check credentials, enable/disable, delete (soft-delete wording), 409 in-use dialog
- [x] Agents: server-paged list (search, status), stats, inline on/off with disable consequences, duplicate, delete; drawer with Settings form (provider → model from enabled models, prompt pickers with preview + inline "New", temperature/max tokens/timeout, Text/Markdown/JSON + schema validation, tools checklist, memory window, live code snippet)
- [x] Agents: Test tab (system/user variables, message when no user prompt, files → multipart), Sessions tab (list, view messages, clear), Usage tab (metrics, snippet)
- [x] Prompts: server-paged list (search, type, show deactivated), stats, create, edit details, new draft version (edit / side by side / changes), version history, make live (with confirm), compare any two versions (word/line diff), deactivate/delete with 409 dialog, activate
- [x] Tools: list with module/safety/status filters, stats, Sync tools, detail drawer (metadata, parameters table, usage, JSON schema)
- [x] Runs: stats strip, filters (agent, provider, status, trigger, memory, date range + Today/7/30 days), session → run → round grouping with expand, detail drawer (conversation with memory split + tool calls/results + files, prompt + variables, cost, details)
- [x] Typecheck (`tsc -b`) and `vite build` pass
- [ ] Side-by-side check in Chrome: localhost:5173/console vs localhost:8000/platform

## P1 checklist

- [x] `schema.json`: top-level `ai` (`$defs` ai, aiProvider, aiAgent, aiTrigger, aiOutput, aiOutputField, aiTool); `customRequirement.uses_ai`
- [x] `rules.json`: unique agent codes; entity / related / tool entity refs; access and trigger roles; `uses_ai` refs (entity and app requirements); button label, schedule cron, transition, tag, form_assist `from`, kind-fields `fields` required
- [x] `spec_check.py` `lint_ai` (runs inside `spec_validate` as build_check): context fields/related/files resolve; output `to` exists and the answer type fits; transition/tag exist; update-trigger loop guard; form_assist needs file fields + kind fields; memory only on chat; chat answers in text/markdown; tools shape; `{event: task}` needs a caller; `uses_ai` callers need a task trigger (warn); review none on a field a workflow condition reads (warn)
- [x] `custom_work.contract_gaps`: `spec_mark_ready` refuses a helper without `acceptance` or `preview.sample` (path `/ai/agents/@code`)
- [x] Docs: SCHEMA.md `## ai` (+ enums, top level, uses_ai, checks); INTERVIEW.md stage 7a with the cue table; DRAFTING.md step 8 + later-turns note; analyst SKILL.md (banned words, AI help question, hidden checklist, spec example)
- [x] `example.yaml` (Vendor Hub): invoice_reader (form_assist), vendor_screening (transition + button, suggest), vendor_assistant (chat, memory, related, tool)
- [x] `template.json` 1.1.39 + changelog + `ai` section; `ui.json` AI helpers section
- [x] Preview (kit `app-studio.html`, simulated with `preview.sample`): AI button on the record header (first visible, rest in ⋯ under "AI"), suggestion card (Use / Discard; review none writes straight away; show = Dismiss), background triggers on create/update/transition/tag with a toast then the card, "Fill from …" in create/edit forms, "Ask AI" chat modal. `zas_render --write` synced kit.css.
- [x] Console review tab: "Help from AI" section (one sentence per helper, when it runs, who checks it, link to App → AI) and an "N AI helpers" pill
- [x] Tests: `test_ai_spec.py` (6); 217 related tests green. `test_skill_plugin` has 8 failures that pre-date this branch (same on a clean stash).
- [x] AI anywhere (pack 1.1.40): `where: record | row | list | form` on button/chat triggers; `type: ai` 360 tabs, summary sections and sidebar panels (`agent`, `title`). Shared renderer (`zas-render.js`) owns `aiAgents/aiClicks/aiListButtons`, adds AI items to `rowActions` (group "AI") and list-header buttons, and calls `H.act('ai', {E, row|rows, agent, trigger})`; the kit host answers in a dialog (Use writes to the row). Checker: `where` only on button/chat, chat not in forms, form buttons need kind fields, `type: ai` names a helper on the hero. Example: row "Screen risk", list "Summarise" (spend_summary), vendor_360 sidebar "Risk screening". 246 related tests green.
- [x] Local DB re-imported: zango-app 1.1.40 published (`import_pack(publish_now=True)` from `Zelthy3_projects/local_dev_project`).
- P2 must implement `act('ai')` in the runtime host (`RenderedPage.tsx`) and the React record/form surfaces for every placement above.

## P2 handoff (start here)

Goal (plan Reference C, P2): the example app builds with working AI buttons and suggestion cards; rebuilds are no-ops.
Plan detail: `AGENT_MODE_AI_AGENTS_PLAN.html` Step 4 (build), Step 7 (runtime), Reference A (triggers → runtime table, result delivery).

1. **Checker output** (`zango-app-studio/scripts/spec_check.py`): `lint_ai` exists; still to do: resolve `ai` into `spec.resolved.json` and create holes `ai_prompt` (writes `backend/<module>/ai/<code>.system.md` / `.user.md`) and `ai_tool` (custom tools in `tools.py`); custom requirements with `uses_ai` get the agent's inputs/outputs in their hole brief; `--audit-holes` checks prompts use only declared `{{variables}}` and that `uses_ai` holes call each agent.
2. **Backend runtime** `assets/backend/zas_core/ai.py`: `run(agent, obj, trigger)`, Celery task `zas_ai_run`, models `ZasAiRun` (queued/running/done/failed/unavailable) and `ZasAiSuggestion`, role-checked endpoints (run, status poll, accept/discard, chat with session_id, form assist), built-in tools `zas_read_record` / `zas_search_records` scoped to the acting user, `run_from_code()` for `uses_ai` tasks, fake mode `ZAS_AI_FAKE=1` returning `preview.sample`, event hooks for create/update/transition/tag/delete/schedule. Treat `ProviderNotConnected` / provider None as "unavailable".
3. **Frontend runtime** `assets/frontend/zas/`: implement `act('ai', …)` in `RenderedPage.tsx` (row menus + list header already call it via zas-render.js), plus React surfaces for record header button, suggestion card, `type: ai` tab/panel, form button / form assist, chat panel, status polling (~2s backoff).
4. **Platform step** `zango_platform.py ai` (called from `studio_build.py` after sync): placeholder provider `app-llm` via ORM (no key; `is_placeholder` comes in P3 — until then create it disabled/unvalidated and note it), `POST /ai/tools/sync/`, upsert prompts (new version only when text changed), create agents (provider/model/temperature/max_tokens only on create), `.zas/ai_state.json`.
5. **Skill docs**: zango-app-studio SKILL.md + references for the build agent (prompts, tools, tests with the fake).

Facts for running things:
- Django tests: `cd backend/test_project && /Users/harshshah/Documents/Zelthy_DEV/Zelthy-V2/zango_venv/bin/python manage.py test --noinput <labels>` (zango_env / zelthy3_venv don't work).
- Related suites: `zango.tests.apps.app_templates.test_ai_spec test_generic_pack test_spec_tools test_builder test_preview_probe` and `zango.tests.apps.agent_mode.test_zas_render test_kit test_preview_parity test_preview_fidelity test_approval_bundle test_studio_build test_prototype_coverage` (246 green). Pre-existing: 8 failures in `test_skill_plugin`, `studio_report` log noise in `test_studio_build`.
- Renderer: edit `packs/zango_app/builder/zas-render.js`, then `cd backend/src && PYTHONPATH=. <venv python> -m zango.apps.agent_mode.zas_render --write` (`--check` to verify).
- Re-import the pack after a version bump: from `/Users/harshshah/Documents/Zelthy_DEV/Zelthy3_projects/local_dev_project`, `manage.py shell -c` with `import_pack(PACKS_DIR/'zango_app', publish_now=True)`.
- Preview check: copy `app-studio.html` to scratchpad, serve with `python3 -m http.server`, load the example YAML into `src.value` + `parse()` via the Chrome JS tool.
- Local app with AI data: `EnrollmentAgent` (834cb82a-a5d0-4af9-a0c7-3b5c29d06434). Console at localhost:5173/console needs a login.
- Commit bundles (`backend/src/zango/assets/console`) with console changes; pre-commit runs ruff-format and detect-secrets (use `# pragma: allowlist secret` on fake keys).

## Notes / decisions

- Guardrails tab is skipped (classic panel only shows "coming soon"); agent payload doesn't send `guardrails`.
- Azure OpenAI and Bedrock are offered when the backend registry lists them (classic panel hard-disables them as "coming soon"). Revisit if they should stay hidden.
- Differences from classic on purpose: confirm before making a prompt version live; fetch-models `auth_error` blocks with a clear message instead of silently falling back; tables + drawers instead of expanding rows (console convention).

## Log

- 2026-11-06: AI placements everywhere (rows, list header, forms, 360 tabs/panels); pack 1.1.40 re-imported locally.
- 2026-11-06: P1 done. Output shape settled on `output: {kind, to}` / `fields: [{key, type, to}]` (plan doc updated from `writes`). Local DB keeps pack 1.1.38 until `import_pack(publish_now=True)` (see memory note) — reimport before trying the preview in Agent Mode.
- 2026-11-06: branch created; API contract + classic feature inventory written (scratchpad); all five tabs implemented; tsc + build green. Next: side-by-side check in Chrome on app `EnrollmentAgent` (834cb82a-…), which has 5 providers and 54 invocations.
