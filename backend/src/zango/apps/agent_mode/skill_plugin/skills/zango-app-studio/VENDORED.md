# Vendored skill: provenance and delta

**Source:** `~/.claude/skills/zango-app-studio/` (user-level Claude Code skill)
**Vendored as:** `zango-agent-mode:zango-app-studio`

Until 2026-10-15 this skill shipped inside the generic template pack
(`shared/app_templates/packs/zango_app/skill/`). It was stored with each pack
version and addressed as `zango-tpl-zango-app:zango-app-studio`. It now lives in
Agent Mode's own plugin, the same way `zango-app-developer-server` does. Every
template on the generic spec (`zango-app/1`) is built with it
(`shared/app_templates/services/generic.py::builds_with_studio`). That includes
apps started from scratch, which are bound to the generic template.

**This copy is the source of truth.** It is ahead of the standalone skill. Pull
upstream changes in by diffing, never by copying over.

## Delta from the standalone skill

| Path | Change |
|---|---|
| `references/server-mode.md` | **Added.** In Agent Mode the platform runs the skill's scripts (`agent_mode/studio_build.py`) and the agent only writes code. Overrides Phases 0–2, 5 and 7 of `SKILL.md`. |
| `SKILL.md` | Points at `server-mode.md` first, plus fixes made while running in Agent Mode. |
| `references/views.md`, `assets/templates/frontend/views/` | **Added.** Declared list views (board, cards, calendar, timeline) the runtime has no component for are built as custom views. |
| `references/spec/schema.md`, `references/map/*`, `references/testing.md` | Updated alongside the spec extensions in `packs/zango_app/SPEC_EXTENSIONS.md`. |
| `scripts/spec_check.py`, `scripts/zango_platform.py`, `scripts/zango_env.py`, `scripts/zas_test/ui.py` | Fixes made while running in Agent Mode. |

## Runtime requirements

- **Python** (`backend/requirements/base.txt`): `PyYAML` (spec_check), `requests` (the
  platform and test scripts), `playwright` (ui, design and scenario tests), `Pillow` (gallery diff).
- **Chromium** is not installed by the requirements. Until `python -m playwright install chromium`
  has run on the worker, a build pauses with the `install_playwright` pending action
  (`studio_build.py`).
- **Node** is needed for the frontend phase (`config.node_available()`).
- `assets/goldens/` are pinned to darwin and Chromium 153. The gallery check skips itself on
  other platforms.
