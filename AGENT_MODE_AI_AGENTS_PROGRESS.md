# AI agents in Agent Mode: implementation progress

Plan: `AGENT_MODE_AI_AGENTS_PLAN.html` (Reference B = console gap list, Reference C = phases).
Branch: `feat/ai-agents-console-p0` (from `feat/agent-mode-default-preview-design` @ 571c5fa0).

## Phases

| Phase | Scope | Status |
|---|---|---|
| P0 | Console AI page at parity with the classic App Panel (`/platform/apps/:id/ai`) | done (4006629a); UI polish later |
| P1 | `ai:` spec section, schema/rules, checker, analyst interview stage 7a, preview, review panel | done |
| P2 | Build: `zas_core/ai.py` runtime, holes, `zango_platform.py ai` step (placeholder + agents) | code + tests done; end-to-end build of the example app not run yet |
| P3 | Hybrid: platform AI accounts (default linked at build) + placeholder support (`is_placeholder`, `…/connect/`, `ProviderNotConnected`); then Connect pause, AI tests | P3a code done; P3b not started |

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

## P2 checklist

- [x] Checker: `resolve_ai()` writes `spec.resolved.json` `ai` (provider defaults; per agent `zango_name`, module, prompts {name, file, variables}, output {format, json_schema}, tools + `tool_entities`, roles default = add/edit roles + trigger roles, run, memory, sample, `when_ast` / related `via` + `where_ast`); `ai_holes()`: `ai_prompt` per helper, `ai_tool` per custom tool, `uses_ai` text + `uses_ai` list on requirement holes; `ui.json` tabs keep `agent`; test plan rows for both kinds
- [x] `--audit-holes`: prompt files present (comments stripped), marker on the system prompt, only declared `{{variables}}`, the data variable used; `uses_ai` holes call `run_from_code("<code>"…)`
- [x] Runtime `zas_core/ai.py`: run/execute/deliver (none → write, suggest → ZasAiSuggestion, show), accept/discard, chat (memory session), form_assist, run_from_code (Result, never raises), on_event (create/update fields/transition/tag/delete snapshot; `when`; loop guard), schedule_tick + cron matcher, payloads, `record_ai`/`clicks`; unavailable = agent missing/off, provider placeholder/unvalidated/off, budget, `ProviderNotConnected` (P3)
- [x] Models `ZasAiRun`, `ZasAiSuggestion`; `tasks.py` (`zas_ai_run`, `zas_ai_tick` with `# zas:schedule * * * * *`, scheduled only when a helper has a schedule trigger); `tools.py` (`zas_search_records`, `zas_read_record`, scoped to the acting role, only the helper's tool entities)
- [x] Hooks: form save (create/update + changed fields), transition done, tag done (enabled), `set_system_tag`, delete row action. Endpoints on the crud view: `GET ?action=zas_ai` (record / run / where=form), `POST zas_ai_run|accept|discard|chat|form`; form `zas_prefill`; 360 payload `zas.ai` + `type: ai` tabs/sections/sidebar (role-filtered); table metadata `zas.ai {row,list,form}`
- [x] Fake AI: `ZAS_AI_FAKE` / `set_fake`, and `.zas/ai_fake.json` under DEBUG (scenario `ctx.ai_fake`, `ctx.ai_run`, `ctx.ai_pending`)
- [x] Frontend `src/zas/ai.tsx`: AiRunDialog (poll 1.5→8s), AiSuggestionCard, AiChatDialog, AiRecordStrip, AiPanel, AiFormBar, md renderer; wired into Detail360 (first AI button + rest in ⋯ "AI", strip under the header, `type: ai` tab/panels), ZasTable (row menu "AI" group, list header buttons), FormDialog (Fill from …/form buttons → remount with `zas_prefill`), RenderedPage `act('ai')`; styles `.zas-ai-*` in tokens.css. Typecheck clean (scratch project on tagrissopap's node_modules)
- [x] Platform: `agent_mode/ai_account.py` `ensure_ai_account` (ORM, keyless, enabled + not validated, supported models; `is_placeholder` set when the field exists); `studio_build` steps `platform:ai_account` + `platform:ai` after sync (skipped without helpers); `zango_platform.py ai` (+ in `all`): account check, prompt files, tools sync + check, prompts (new live version only when the file changed), agents (create with provider/model/temperature/max_tokens/timeout once; later only managed fields when their hash changed), `.zas/ai_state.json`; `schedule` scans `zas_core/tasks.py` when a helper has a schedule
- [x] Skill docs: `references/map/ai.md` (new), SKILL.md (Phase 2/4/5 + index), contracts §10/§10b, custom-code table, testing.md
- [x] Tests: `test_ai_build.py` (7: resolution, holes, audit, platform step idempotent/changed prompt/missing, placeholder account); selftest_runtime AI checks; 316 related tests green except the 8 pre-existing `test_skill_plugin`
- [ ] End to end: build the example (Vendor Hub with AI) in Agent Mode, then click the AI buttons with the placeholder (expect "not set up") and with a key; check a rebuild is a no-op in `ai_state.json`
- Notes: form fill can't put the uploaded file into the package form's file field (the bar says to attach it below). `delete` triggers read a snapshot taken before the delete. No `is_placeholder` yet: the runtime treats `is_validated=False` as not connected.

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

## P3a: platform AI accounts (hybrid), 2026-11-06

Decision (user): hybrid. A platform admin connects an AI service once in Platform → Settings → AI accounts
(stored in the DB, encrypted; nothing in .env or settings). The build links each app's `app-llm` to the
default account; with no working default it makes a placeholder as before.

- [x] `PlatformAIAccount` (public schema, `platform_settings` 0002): service, encrypted config, model list,
      default model, per-app monthly cap, one default, on/off, last check.
- [x] `AppLLMProvider` (ai 0002): `source` own|platform, `platform_account_uuid`, `is_placeholder`;
      `_decrypt_config`/`get_provider_class` read the platform account at call time (key rotation reaches
      every app); `connection_problem()` / `is_connected`; `get_client` raises `ProviderNotConnected`.
- [x] `zango.ai.accounts`: `check_credentials`, `link_platform`, `connect_own` (agents on a model the new
      service lacks move to the new default), `apps_linked_to`. Platform cap is a ceiling on the app budget.
- [x] API `/api/v1/platform/ai-accounts/` (super admins): list (+ services, apps using), create (live check),
      check, get/put (key replace re-checked), delete (409 while apps use it), validate.
- [x] App API: `providers/platform-accounts/`, `providers/<id>/connect/` (platform or own key); list serializer
      adds source/platform_account/is_placeholder/connected/connection_problem; platform/placeholder rows hide config.
- [x] Build: `ensure_ai_account` links to the default (or upgrades a placeholder); runtime `_client` uses `is_connected`.
- [x] Console: Settings → AI accounts (hero, cards, connect wizard, edit drawer, logos); App → AI → Providers
      banner, logos, Connect drawer (platform account or own key), linked-key card in the edit drawer.
- [x] Tests: `test_ai_build` 19 green. Local DB migrated (all 68 apps).
- [x] Claude subscription for local testing (`ai/providers/claude_subscription.py`): same switch as Build with AI
      (`AGENT_MODE_AUTH=subscription` + `CLAUDE_CODE_OAUTH_TOKEN` + DEBUG), one tool-less turn through the Claude
      Code CLI per call; no tools, no files, schema asked for not enforced, cost 0. Hidden and "not connected"
      when the switch is off. The build prefers it for new and waiting accounts.
- [x] Claude Opus 5.5 / Sonnet 5.5 in the Anthropic model list (per-model cache-read price); Sonnet 5.5 is
      the recommended default and the spec default (pack 1.1.41, re-imported locally).
- [x] Checked in Chrome: Settings → AI accounts (empty state, wizard, card, drawer), App → AI → Providers
      (logos, Connect drawer both ways). Local DB has a platform account `claude-subscription-main` (default).
- [ ] P3b: Connect pause at the end of the build, real-AI test step, report section.

## Notes / decisions

- Guardrails tab is skipped (classic panel only shows "coming soon"); agent payload doesn't send `guardrails`.
- Azure OpenAI and Bedrock are offered when the backend registry lists them (classic panel hard-disables them as "coming soon"). Revisit if they should stay hidden.
- Differences from classic on purpose: confirm before making a prompt version live; fetch-models `auth_error` blocks with a clear message instead of silently falling back; tables + drawers instead of expanding rows (console convention).

## Log

- 2026-11-06: P2 code done (checker, runtime back + front, platform AI step, docs, tests). Not yet run end to end in a real build.

- 2026-11-06: AI placements everywhere (rows, list header, forms, 360 tabs/panels); pack 1.1.40 re-imported locally.
- 2026-11-06: P1 done. Output shape settled on `output: {kind, to}` / `fields: [{key, type, to}]` (plan doc updated from `writes`). Local DB keeps pack 1.1.38 until `import_pack(publish_now=True)` (see memory note) — reimport before trying the preview in Agent Mode.
- 2026-11-06: branch created; API contract + classic feature inventory written (scratchpad); all five tabs implemented; tsc + build green. Next: side-by-side check in Chrome on app `EnrollmentAgent` (834cb82a-…), which has 5 providers and 54 invocations.
