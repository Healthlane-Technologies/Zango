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
- Not done in P1 (by design): `where: row|list` buttons are not drawn on list rows yet (row menu lives in zas-render.js); the resolved `ai` model / holes for the build are P2.

## Notes / decisions

- Guardrails tab is skipped (classic panel only shows "coming soon"); agent payload doesn't send `guardrails`.
- Azure OpenAI and Bedrock are offered when the backend registry lists them (classic panel hard-disables them as "coming soon"). Revisit if they should stay hidden.
- Differences from classic on purpose: confirm before making a prompt version live; fetch-models `auth_error` blocks with a clear message instead of silently falling back; tables + drawers instead of expanding rows (console convention).

## Log

- 2026-11-06: P1 done. Output shape settled on `output: {kind, to}` / `fields: [{key, type, to}]` (plan doc updated from `writes`). Local DB keeps pack 1.1.38 until `import_pack(publish_now=True)` (see memory note) — reimport before trying the preview in Agent Mode.
- 2026-11-06: branch created; API contract + classic feature inventory written (scratchpad); all five tabs implemented; tsc + build green. Next: side-by-side check in Chrome on app `EnrollmentAgent` (834cb82a-…), which has 5 providers and 54 invocations.
