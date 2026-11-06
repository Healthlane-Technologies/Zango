# AI agents in Agent Mode: implementation progress

Plan: `AGENT_MODE_AI_AGENTS_PLAN.html` (Reference B = console gap list, Reference C = phases).
Branch: `feat/ai-agents-console-p0` (from `feat/agent-mode-default-preview-design` @ 571c5fa0).

## Phases

| Phase | Scope | Status |
|---|---|---|
| P0 | Console AI page at parity with the classic App Panel (`/platform/apps/:id/ai`) | in progress |
| P1 | `ai:` spec section, schema/rules, analyst interview stage 7a, preview | not started |
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

## Notes / decisions

- Guardrails tab is skipped (classic panel only shows "coming soon"); agent payload doesn't send `guardrails`.
- Azure OpenAI and Bedrock are offered when the backend registry lists them (classic panel hard-disables them as "coming soon"). Revisit if they should stay hidden.
- Differences from classic on purpose: confirm before making a prompt version live; fetch-models `auth_error` blocks with a clear message instead of silently falling back; tables + drawers instead of expanding rows (console convention).

## Log

- 2026-11-06: branch created; API contract + classic feature inventory written (scratchpad); all five tabs implemented; tsc + build green. Next: side-by-side check in Chrome on app `EnrollmentAgent` (834cb82a-…), which has 5 providers and 54 invocations.
