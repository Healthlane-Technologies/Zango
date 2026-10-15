# Agent Mode: App Studio as the build skill

Branch: `feat/agent-mode-app-studio-skill` (from `feat/console-scaffold`, 2026-10-15)

## Goal

Every Agent Mode build, "Describe it" (from scratch) included, goes the same way:

1. The requirement produces an `app_spec.yaml` (generic Zango app spec, dialect `zango-app/1`).
2. The console shows a live preview of that spec.
3. The build uses the **`zango-app-studio`** skill.

`zango-app-developer-server` must not be used for these builds.

## How it worked before this branch (research, 2026-10-15)

- **"Describe it" was already bound to the generic template.** The binding is in `api/platform/agent_mode_admin/v1/views.py:326-336`, from commit `d0589a78`. The scaffold binds the new app to the generic `zango-app` ("Custom Zango app") template, so the requirement is YAML with a preview.
  - The new-app summary card still says "Requirements chat". That label only names the interview mode (`mode` is `interview` or `draft`); the spec is YAML either way.
- **The studio skill was inside the template pack**, at `shared/app_templates/packs/zango_app/skill/`.
  - It was stored in the DB with each pack version and written to disk as a plugin named `zango-tpl-zango-app`.
  - It was addressed as `zango-tpl-zango-app:zango-app-studio`.
  - Other generic-dialect templates borrowed it through `generic.build_skill_source()`.
- **`agent_mode/studio_build.py` runs the studio pipeline.** It runs spec_check, copies the runtime, prepares the frontend, then runs migrations, roles, users and AppBuilder, then the test layers (api, ui, design, scenarios), fix rounds and the report. It is chosen by `is_studio()`, which checks that the skill directory contains `scripts/spec_check.py`.
- **`zango-app-developer-server` was still used in three places:**
  1. It was **always loaded** in every build session: `options.py` had `skills=[QUALIFIED_SKILL]` plus the template skill.
  2. It was the **fallback** when a requirement had no template (`tasks.py:320`). That covered apps not created through the console wizard.
  3. **PSP needs it.** `packs/psp/skill/SKILL.md` says to use it together with `zango-psp-builder`. PSP is the only template not on `zango-app/1`.
- **Standalone copy:** `~/.claude/skills/zango-app-studio` (Oct 9–10) is OLDER than the repo copy. The repo copy has `references/server-mode.md` and `references/views.md` and newer scripts. **The repo copy is the source of truth.**

## Decisions (from the user)

| Question | Decision |
|---|---|
| "Describe it" → YAML | Bind to the generic "Custom Zango app" template (already the case; kept) |
| Apps with an old markdown spec | Ignore (dev only); no migration |
| Where the skill lives | `agent_mode/skill_plugin/skills/zango-app-studio` (same pattern as dev-server) |
| Playwright / Chromium | Python packages in `backend/requirements/base.txt` only; the Chromium install stays the existing "install Playwright" pending action. Local dev venv: `Zelthy-V2/zango_venv` |
| PSP | Keep `zango-app-developer-server` **only** for PSP (non-studio template builds) |

## Changes made

- [x] **Moved the skill** with `git mv shared/app_templates/packs/zango_app/skill` → `agent_mode/skill_plugin/skills/zango-app-studio`. It is now addressed as `zango-agent-mode:zango-app-studio`.
- [x] **`packs/zango_app/template.json`:** removed `skill_dir` and `build_skill_name`, and bumped the version to **1.1.8** so `seed_bundled_packs` imports a new version on migrate.
  - `SPEC_EXTENSIONS.md` now points at the skill's new path.
- [x] **`shared/app_templates/services/generic.py`:** replaced `build_skill_source()` with `STUDIO_PLUGIN`, `STUDIO_SKILL`, `studio_plugin_dir()` and `builds_with_studio(version)`.
  - Every generic-dialect version is built with the plugin's studio skill, unless the template ships its own skill. Older pinned `zango-app` versions also use the plugin skill.
- [x] **`services/catalogue.py`:** `TemplateView.skill_plugin_slug` became `skill_plugin_name`.
  - `qualified_skill` is `<skill_plugin_name or zango-tpl-<slug>>:<build_skill_name>`.
  - `build_view` uses the studio plugin for generic-dialect versions.
- [x] **`services/packs.py`:** lint no longer warns "no build skill" for generic-dialect packs.
- [x] **`agent_mode/prompt.py`:** `SKILL_NAME` and `QUALIFIED_SKILL` became `STUDIO_SKILL_NAME`/`STUDIO_SKILL` and `DEVELOPER_SKILL_NAME`/`DEVELOPER_SKILL`.
  - `compose_prompt` and `compose_resume_prompt` take the skill explicitly.
  - Removed the unused `template_preamble` and `_TEMPLATE_PREAMBLE`.
- [x] **`agent_mode/tasks.py`:** no fallback skill. A run without a YAML template spec fails with `StudioError("NoAppSpec", …)`.
- [x] **`agent_mode/options.py`:** `skills` holds only the template's build skill.
  - `DEVELOPER_SKILL` is added only when the build is **not** a studio build, which today means PSP.
  - The template plugin dir is added only if it differs from `SKILL_PLUGIN_DIR`.
- [x] **`agent_mode/template_binding.py::seed_from_binding`:** an app with no binding now gets the generic template, so every new requirement is YAML.
- [x] **`api/platform/agent_mode/v1/views.py` (start run):**
  - Raw-prompt runs are refused with 400.
  - A requirement without a YAML template spec is refused with 409 and a clear message.
- [x] **`management/commands/agent_mode_repl.py`:** dispatches `STUDIO_SKILL`.
- [x] Removed the stray `skill_plugin/.DS_Store`.

- [x] **`backend/requirements/base.txt`:** added `Pillow==12.0.0`, `playwright==1.63.0`, `PyYAML==6.0.2` and `requests==2.32.5`.
  - These are the versions already installed and working in `Zelthy-V2/zango_venv`, so `pip install -r` there is a no-op.
  - Chromium (`~/Library/Caches/ms-playwright/chromium-1243`) is already installed locally.
- [x] **Skill files:**
  - Added `skill_plugin/skills/zango-app-studio/VENDORED.md` (provenance, delta from the standalone skill, runtime requirements).
  - Updated the `plugin.json` description.
  - Updated the `template_build.py` docstrings.
- [x] **Tests:**
  - Updated `test_skill_plugin.py` (adds `StudioSkillPluginTests`), `test_mapper.py`, `test_requirements.py`, `test_studio_build.py`, `test_app_templates.py` and `app_templates/test_generic_fallback.py`.
  - New `tests/apps/agent_mode/test_build_skills.py` checks which skills a build loads: studio only, or PSP plus the developer skill.

## Test status (2026-10-15)

```
source ../zango_venv/bin/activate            # i.e. Zelthy-V2/zango_venv
cd backend/test_project
python manage.py test --noinput zango.tests.apps.agent_mode zango.tests.apps.app_templates
```

The run gives 534 tests, with 7 failures and 1 error. **None of these come from this branch:**

- All 8 are in `test_skill_plugin.py` (`SkillPluginTests`, `MenuConfigGuidanceTests` and `FrontendSetupGuidanceTests`).
- They assert wording that is no longer in `zango-app-developer-server/SKILL.md`, which has been unchanged since `d0ec7f55` (2026-09-20). One also reads `references/packages/crud/forms.md`, which was split into `forms/`.
- Not fixed, because that skill is now PSP-only. Either fix them or trim the assertions to what PSP relies on.

## Still to do

- [ ] Manual end-to-end:
  1. "Describe it" in the console.
  2. Spec draft + preview.
  3. Approve.
  4. Build.
  5. Confirm `AgentRun.skill_name == zango-agent-mode:zango-app-studio` and that the init event lists only that skill.
- [ ] Run `migrate` (or restart) so `seed_bundled_packs` imports `zango-app` 1.1.8.
- [ ] Decide on the stale developer-server tests (see above).
- [ ] Not committed yet.

## Notes / gotchas

- **The pack's DB versions keep their old skill files.** Versions ≤1.1.7 of `zango-app` still carry the skill in `AppTemplateVersionFile`, and `materialise()` still writes it to disk. Builds no longer use that copy: `builds_with_studio` points at the plugin.
- **The studio skill writes to its own directory in two cases.** It says "runtime bugs are fixed in `<skill>/assets/`", and `--make-goldens` writes to `assets/`. On a server the skill dir is read-only to the agent (guard `read_roots`), which is fine for builds.
- **The design goldens are pinned to darwin with Chromium 153**, so the gallery check skips itself on Linux workers.
