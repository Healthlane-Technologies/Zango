# Map: `workflow` → `workflow.py` (+ `tasks.py` for system items)

One `<Model>Workflow` per entity that has a `workflow` block, in `backend/<module>/workflow.py`.
Worked example: `references/examples/vendors/workflow.py`. Package reference:
`references/zango/packages/workflow/` (statuses, transitions, tags, advanced).
Checked against workflow **1.0.1** `base/engine.py`.

## What the engine needs, and where it comes from

| Engine attribute | From `.zas/spec.resolved.json` `entities.<e>.workflow` |
|---|---|
| `Meta.model` | the model |
| `Meta.on_create_status` | `initial` |
| `Meta.statuses = {code: {"label", "color"}}` | `statuses[]`, `color` = **`wf_color`** (not the spec tone) |
| `Meta.tags = [(code, label), …]` | `tags[]`, **including system tags** |
| `status_transitions = [ … ]` | one dict per entry in `transitions[].engine` |
| `tag_transitions = [ … ]` | one dict per **non-system** tag |

`wf_color` is the tone translated to a colour the engine can draw white text on
(`amber` → `orange`, `teal` → `#0E9384`, …). The React runtime ignores it. Badges
read the spec tone from `spec.ui.json`.

## `status_transitions`

`spec_check` expands a transition with several `from` statuses into one engine entry per
status: `{"name": "<name>__<from>", "from": "<from>"}`. A single-`from` transition keeps
its name. **Write one dict per `engine` entry**, never per spec transition:

```python
{"name": "<engine name>", "display_name": "<label>", "description": "",
 "from": "<from>", "to": "<to>",
 "roles": [...],                              # spec roles; omit when empty
 "confirmation_message": "<confirm>",          # only if the spec has confirm
 "form": <Model><Transition>Form,              # only if the spec has a form
 "is_manual": False}                           # only for system transitions (then no roles)
```

`primary`, `tone`, `condition_msg` and `icon` are **not** engine keys. They live in
`spec.json`, and the 360 header (`ZasDetail._zas_actions`) and the React runtime read them.

## Conditions and done hooks: do NOT write methods

`ZasWorkflowMixin.__getattr__` answers the engine's `getattr(self, "<name>_condition")`
and `"<name>_done"` from `spec.json`:

| Spec | Engine calls | Supplied behaviour |
|---|---|---|
| `condition` (expression) | `<engine name>_condition` | `expr.evaluate(condition_ast, obj)` |
| `condition` with `text:` (alone, in `all`, in `any`) | same | the text node calls hook `<entity>__<transition>__condition(request, obj) -> bool` |
| `on_done` | `<engine name>_done` | hook `<entity>__<transition>__done(request, obj, form_data)`, then `app_user.maybe_provision` |
| no `on_done` | `<engine name>_done` | `app_user.maybe_provision` only |
| record created | `<initial status>_done` | `app_user.maybe_provision` (for `create_on: status == <initial>`) |
| tag `enable/disable.condition` | `<tag>_<enabled\|disabled>_condition` | expression, or hook `<entity>__tag_<tag>_<enable\|disable>__condition` |
| tag set / cleared | `<tag>_<enabled\|disabled>_done` | `app_user.maybe_provision` |

Hooks use the **spec transition name**, even for an expanded `<name>__<from>` engine entry,
so one hook serves every `from`. A failing condition hides the transition in the row menu
(engine) and shows it disabled with `condition_msg` on the 360 header (runtime).

The condition runs **before** the dialog opens, on the record alone. The part of a condition that
the move's own form satisfies ("…, or a note is given to override", "a file or pasted text is
provided") is therefore not checked in the condition hook: return True for it there, and enforce it
in the transition form's `clean()` with a field error. Otherwise the button stays disabled and the
user can never open the dialog to type the note.

The engine checks `roles` against the current role. It loads `?object_uuid=` itself.
`ZasWorkflowMixin.get_object_instance` re-applies the role's row scope there (contracts §4),
so a role cannot transition a record it cannot see.

## `tag_transitions`

```python
{"name": "<tag code>",
 "enabled":  {"roles": [...], "confirmation_message": "<enable.confirm>", "form": <Model><Tag>EnableForm},
 "disabled": {"roles": [...], "confirmation_message": "<disable.confirm>"}}
```

If a side is missing from the spec, give that side `{"roles": []}`. The engine reads
empty roles as "everyone", so `ZasWorkflowMixin` answers `<tag>_<side>_condition` with
`False` for a missing side (and for system tags). The checker warns when nobody can set a tag. Tag state lives only in `WorkflowTransaction` rows
(`transition_type="tag"`). The last one decides.

## System transitions and system tags → `tasks.py`

| Spec | Hole / function | Body |
|---|---|---|
| transition `trigger: system` + `text` | `@shared_task def <entity>__<transition>__run()` → int | select records (`zx.to_q(...)` for status filters), call `run_system_transition("<entity>", obj, "<transition>")` each |
| tag `system: true` + `text` | `@shared_task def <entity>__tag_<tag>__sync()` → int | compute the wanted state, call `set_system_tag("<entity>", obj, "<tag>", bool)` (no-op when unchanged) |
| `custom_requirements[]` with `area: scheduled` | `@shared_task def <entity\|app>__req__<n>()` | free |

Imports: `from celery import shared_task`, `from ..zas_core.mixins import run_system_transition, set_system_tag`.
`run_system_transition` builds a request with no user. The engine's role check passes when
there is no current role, and `allow_system=True` lets `is_manual: False` entries run.
**Schedules:** turn the text's timing ("nightly", "daily at 07:00") into a cron line directly above
the task, `# zas:schedule <minute> <hour> <day-of-month> <month> <day-of-week>` (for example
`# zas:schedule 0 7 * * *`). After `zango_platform.py sync` registers the task,
`zango_platform.py schedule` sets and enables the cron through the App Panel API. A task whose text gives
no timing gets no marker and is listed in the report ([report](../report.md)). Background: `references/zango/core/async-tasks.md`.

## CrudView wiring

`workflow = <Model>Workflow` on the CrudView. That gives the table its status column
choices, row-menu transitions and tags, and the `?view=workflow` endpoints the tests use:

- `GET  <endpoint>?view=workflow&action=initialize_form&transition_type=status&transition_name=<engine name>&object_uuid=<uuid>`
- `POST <endpoint>?view=workflow&action=process_transition&transition_type=status&transition_name=<engine name>&object_uuid=<uuid>`
- tags: `transition_type=tag&transition_name=<tag>&transition_state=enabled|disabled`

## Checks before moving on

- Engine names in `status_transitions` = exactly the set of `engine[].name` in the resolved spec.
- Every `form` referenced exists in `forms.py`. Forms import nothing from `workflow.py`
  (`workflow.py` imports forms, never the reverse).
- `Meta.tags` includes system tags. `tag_transitions` excludes them.
- No `<x>_condition` / `<x>_done` methods written by hand. If you need one, the spec item
  belongs in `hooks.py`.
