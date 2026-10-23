# Agent Mode: Open Prototype ("Free design"), implementation progress

Plan: https://claude.ai/artifact/1x8D2VWgxjKYG6N68BhnJC ("Open Prototype Plan", v4).
Branch: `feat/agent-mode-open-prototype` (from `feat/agent-mode-app-studio-skill`). Started 2026-10-23.

Goal of P1: in chat, the requirement agent generates a working HTML prototype of the app in any look
(the capability bar is a 237 KB single-file app with personas, workflows and its own tokens),
written in parts, with the YAML kept in step. The capability-bar file is NOT in the repo and must
never be added (user decision).

## Status

| P1 step | What | Status |
|---|---|---|
| Spike | SDK in-process MCP tools reach sub-agents (`AgentDefinition.mcpServers`, tool name `Agent`) | **done**: 2 parallel writers called `proto_write` (SDK 0.2.152, haiku) |
| P1.1 | Data model + migrations | **done** |
| P1.2 | Assembly (`prototype.py`) + route | **done** |
| P1.3 | `proto_*` tools on the spec server | **done** |
| P1.4 | Screen-writer sub-agent | **done** (options wired; not yet run in a real analyst turn) |
| P1.5 | Turn limits for open mode | **done** |
| P1.6 | Runtime + starter (`prototype_assets/`) | **done** |
| P1.7 | Skill `zango-prototype` + worked example | **done** |
| P1.8 | Console: toggle, `PrototypeFrame`, mode switch | todo |
| P1.9 | Tests | backend **done** (11 in `test_prototype.py`); API test todo |
| Done-when | 3 chat-only runs measured | todo |

## Backend changes

- `apps/agent_mode/models.py`: `AgentRequirement.preview_mode` ("kit" | "open"), `prototype_parts`
  (JSON {path: text}), `prototype_hash`, `prototype_revision`; `AgentRequirementVersion.prototype_parts`
  / `prototype_hash`, written by `record_spec`. Migration `0016_open_prototype`.
- `apps/shared/agent_mode/models.py`: `AgentAppScaffold.preview_mode` (migration `0006_scaffold_preview_mode`);
  `scaffold.py` passes it to the requirement; admin create view accepts `preview_mode`.
- `apps/agent_mode/prototype.py` (new):
  - part paths `^[a-z0-9][a-z0-9_.-]*(/…){0,2}\.(css|js|json)$`, 150 KB per part, 2 MB total;
  - `manifest_of` / `static_problems`: screens ↔ parts, library hosts (cdnjs, jsdelivr/npm, unpkg, pinned
    version), fonts (Google Fonts only);
  - `js_syntax_error`: `node --check` (system node, else Playwright's bundled node; skipped if none);
  - `assemble`: CSP meta → fonts → runtime CSS → tokens.css, app.css, other css, screens/*.css → body →
    manifest JSON → lucide (unpkg, pinned) → runtime JS → libraries → data.js, shell.js, other js,
    screens/*.js (manifest order) → `ZAS.boot()`. One `<script>` per part with `//# sourceURL=proto/<part>`
    so a throwing part stops only itself and errors name the part. `</script` / `</style` escaped.
  - `PrototypeBench` (outline/write/patch/read/find/remove/rename), emits `{prototype_parts, prototype_hash}`;
  - `proto_tool_specs`, `PROTO_TOOL_NAMES`, `screen_writer_agent()` (`background=False`, maxTurns 40,
    tools: outline/write/patch/read/find + Read + Skill, `mcpServers=["spec"]`).
- `apps/agent_mode/prototype_assets/zas-proto.js|css`: the runtime (ZAS.seed/screen/shell/on/go/back/
  store/files/drawer/modal/toast, helpers h/I/fmt/pill/table/tabs/field/initials, persona bar, `/_blob/`
  fetch from memory, postMessage bridge `source: 'zas-proto'` types ready/location/error; listens for
  `{source: 'zango-console', type: 'goto'}`). Packaged via `setup.py` package_data.
- `spec_tools.py`: `SpecWorkbench(proto=…)`; in open mode `issues()` drops the unsketched-screen rules;
  proto tools appended to `tool_specs`; names in `TOOL_NAMES` / `ALLOWED_TOOL_NAMES`.
- `tasks.py`: open mode builds a `PrototypeBench`, passes `probe=None` (kit probe off), and
  `_record_spec_edit` saves `prototype_parts/hash` and bumps `prototype_revision`.
- `requirements.py`: `PROTOTYPE_SKILL`, `_OPEN_PROTOTYPE_APPEND`; open mode adds `Agent`/`Task`, the
  skill, `agents={"screen-writer": …}`; first draft (no parts yet) gets max_turns 250 and
  `AGENT_MODE_ANALYST_PROTO_BUDGET_USD` (15).
- `template_spec.approval_problem`: open mode needs a prototype; `unfinished_custom_work(sketches=False)`.
- API (`agent_mode/v1`): `_seed_preview_mode` on create (explicit `preview_mode`, else the last approved
  requirement's mode; an open change starts from its prototype parts); `_dispatch_turn` gives an open
  first draft `AGENT_MODE_OPEN_FIRST_TURN_SECONDS` (1500); `GET requirements/<uuid>/prototype/[?v=N]`
  (assembled HTML, CSP + `sandbox` header, ETag); serializers add `preview_mode`, `prototype_revision`,
  `prototype_hash`; availability adds `open_prototype`.
- Settings: `AGENT_MODE_OPEN_PROTOTYPE` (True), `AGENT_MODE_OPEN_FIRST_TURN_SECONDS` (1500),
  `AGENT_MODE_ANALYST_PROTO_BUDGET_USD` (15.0).
- Skill `skill_plugin/skills/zango-prototype/SKILL.md` + `references/example/` (fictional lab sample
  tracker, 8 parts, 13.5 KB): parts, manifest, runtime API, first-draft order, screen brief template, bar.

## How to test

```bash
cd backend/test_project
../../../zango_venv/bin/python manage.py test --noinput zango.tests.apps.app_templates.test_prototype
```

## Notes / gotchas

- The SDK's sub-agent tool is named `Agent` in this CLI (allowed both `Agent` and `Task`).
- Sub-agents can run in the background; `background=False` keeps the turn open until they finish.
- Screen writers are told (prompt only) to touch just `screens/<id>.*`; not enforced in code yet.
- `window.claude.use` compatibility (for imported Claude artifacts) is left for the upload phase (U).
