# Agent Mode — Polished Frontend & Branded Login

**Status: all 11 steps complete.** Verified: every reference link resolves, no
stale "Node unavailable" / "do not scaffold" guidance remains.

Branch: `feat/agent-mode-polished-frontend`
Plan: `agent-mode-polished-frontend-plan.html`
Scope: skill/prompt content only, under
`backend/src/zango/apps/agent_mode/skill_plugin/skills/`

## Steps

| # | Step | File | Status |
|---|------|------|--------|
| 1 | entity-360 reference | `references/frontend/entity-360.md` | ☑ |
| 2 | auth/login reference | `references/frontend/auth-login.md` | ☑ |
| 3 | design-system reference | `references/frontend/design-system.md` | ☑ |
| 4 | STEP 3 UX defaults inverted | `SKILL.md` | ☑ |
| 5 | STEP 5a bundle + login route fix | `SKILL.md` | ☑ |
| 6 | STEP 5d rewritten (Node guaranteed) | `SKILL.md` | ☑ |
| 7 | STEP 5e branded login added | `SKILL.md` | ☑ |
| 8 | Reference table + STEP 7 summary | `SKILL.md` | ☑ |
| 9 | Stale "Node unavailable" banners removed | `references/*` | ☑ |
| 10 | Analyst skill de-conflicted | `zango-requirements-analyst/SKILL.md` | ☑ |
| 11 | VENDORED.md delta recorded | `VENDORED.md` | ☑ |

Legend: ☐ todo · ◐ in progress · ☑ done

## Decisions locked
- Branded login: ALWAYS, no toggle. Archetype = au-psp split-screen.
- Entity-360: agent decides how many; always a FULL-PAGE route, never a drawer.
- Node: guaranteed — delete "Node unavailable" branches, don't make conditional.
- design-system.md: domain-neutral, must NOT reuse `pharma-enterprise-ui`.
- Upstream port to `zelthy-claude-skills`: deferred until proven in a real run.

## Notes
- **Corrected while writing entity-360.md:** the child-table server filter is
  `get_table_data_queryset()` on the **table class** (reads
  `self.crud_view_instance.request`), NOT `get_queryset()` on the view —
  `BaseCrudView` has no such method, so that override would silently no-op and
  leave child tables unfiltered. Verified in `packages/crud/tables.md`.
- Skill header + description updated; version 1.0.0 -> 1.1.0.
- Server-mode banners in 5 reference files corrected rather than deleted: the
  read-only-Bash part is still true, but the "npm/npx cannot run, Node is
  unavailable" claim is not.
- `customMainDetail` receives **camelCase** props; the large snake_case example in
  `frontend/crud.md` is for `customDrawerDetail` only. Both documented.

## Not done (deliberate)
- **No upstream port** to `zelthy-claude-skills`. The three new references are
  written to be portable; contribute them once proven in a real run.
- **No runtime test.** These are prompt/doc changes; the real check is an
  Agent Mode run that produces an app with an entity-360 page and a branded
  login. Worth doing before this reaches users.
