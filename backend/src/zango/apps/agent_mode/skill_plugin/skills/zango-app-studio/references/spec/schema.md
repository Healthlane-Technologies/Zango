# Spec schema (spec_version 1)

What every key in an App Studio `app_spec.yaml` means, how `scripts/spec_check.py`
normalises it, and which reference covers what it becomes. Read at Phase 1. The
authoritative template is `zango_app_spec.template.yaml`; the cleaned regression copy
is `evals/vendor_hub.yaml`.

After the check, **read `.zas/spec.resolved.json`, not the YAML**. It holds every
default filled in, every alias renamed, every expression parsed (`*_ast`), and every
derived name (contracts.md §1).

## Top level

| Key | Normalised to | Becomes |
|---|---|---|
| `spec_version` | must be `1` (warn otherwise) | — |
| `app.code` | required, snake_case | `settings.json app_name` check, test-user email domain |
| `app.name / description` | `name` defaults to Titleized code | login copy, page titles ([pages-menus](../map/pages-menus.md)) |
| `app.locale / currency / timezone` | default `en-US / USD / UTC` | money/date formatting in `config.ts`, `data.zas.formats` |
| `app.theme.primary` | default `#4F46E5` | `--brand` (frontend tokens) |
| `app.ui.radius` | `sharp` · `rounded` (default) · `soft` | `data-zas-radius` → `--z-r-card/-head/-ctl` |
| `app.ui.density` | `compact` · `comfortable` (default) | `data-zas-density` → `--z-ctl-h`, `--z-cell-y`, `--z-th-y`, `--z-page-pad` |
| `app.custom_requirements[]` | holes `app__req__N` | [custom-code](../custom-code.md) |
| `choice_sets.<code>` | `[{id, label, color?}]` | `<CODE>_CHOICES` constants ([models](../map/models.md)) |
| `roles[]` (list or map) | keyed by `name`; `slug` added | `roles.json`, policies, menus ([access](../map/access.md)) |
| `roles[].landing / menu[]` | menu items `{page, label, icon}` or `{group, icon, items}` | AppBuilder menu per role ([pages-menus](../map/pages-menus.md)) |
| `pages[]` | `title` defaults to the entity plural; `export = Page_<code>` | AppBuilder route ([pages-menus](../map/pages-menus.md)) |
| `modules[]` | `url` = code with `-`; `entity_order` (FK order) | `backend/<code>/` |
| `modules[].entities[]` | see Entity | model + CRUD view |
| `detail_views[]` | `page` back-filled from the detail page | `<Hero>Detail` + `ZasDetail360` ([detail-views](../map/detail-views.md)) |

## Entity

| Key | Default / alias | Becomes |
|---|---|---|
| `code` | required, snake_case, unique app-wide | class names (contracts §1) |
| `name / plural` | Titleized code / `name + "s"` | page titles, add button |
| `kind` | `transactional` (`hero / transactional / child / master`) | decides 360 and menus; no code difference by itself |
| `display` | `name` if present, else first text field, else `id` | `__str__`, FK dropdown label, 360 title fallback |
| `fields[]` | `- key: {…}` → `{key, type=text, label=Titleized, required, readonly}` | model field ([models](../map/models.md)) |
| `fields[].choices` | set code or inline list → `choices:[{id,label,color}]`, `choice_set` kept | `CharField(choices=…)` |
| `fields[].computed` | arithmetic (`a * b`) → `{expr}`; anything else → `{text}` (hole) | `zr.apply_on_save` |
| `fields[].limit_choices` | parsed to an AST against the **target** entity | form queryset filter |
| `fields[].auto.sequence` | needs a `{000…}` counter | `ZasSequence` via `zr.apply_on_save` |
| `parent: {entity, field}` | field must link to entity | child forms preset the FK on 360 tabs |
| `app_user: {role, name, email, mobile, create_on}` | `create_on` default `create`; else parsed to `create_on_ast` | `zas_core.app_user` ([access](../map/access.md)) |
| `access.<Role>` | `{actions, rows, none}`; `can` → `actions`; `none`/`no_access` → no access | policies + row scoping ([access](../map/access.md)) |
| `workflow.statuses` (alias `states`) | `{code, label, color=gray, initial, final}`; `start` → `initial` | `Meta.statuses` ([workflow](../map/workflow.md)) |
| `workflow.transitions` (alias `steps`) | `name` from label; `do`→`label`; `by`→`roles`; `collects`→`form`; `from` list; `trigger: system` / `automatic` → `system` | `status_transitions` (+ `engine` expansion) |
| `workflow.tags` (alias `labels`) | `{code, label, color=gray, enable, disable, system}` | `Meta.tags` + `tag_transitions` |
| `form.create / edit` | `same_as` merged; `sections` or `fields` → `<kind>_resolved: [{title, fields}]` | `<Model>Form` / `<Model>EditForm` ([forms](../map/forms.md)) |
| `validation.rules / duplicate_check` | `when/require_expr/where` parsed to `*_ast` | `ZasFormMixin.clean` |
| `table.columns` | absent → first 6 non-long fields + `status`; `as`→`source`; `custom`→`computed`; `computed` with `path` → `path` | `ModelTable` columns ([tables](../map/tables.md)) |
| `table.columns[].secondary`, `secondary_style`, `icon` | `secondary` → list of field paths (a second, muted line joined by " · "; `secondary_style: mono` sets it monospace); `icon` name → `{by: null, map: {}, default}`, `{by, map, default}` picks per row by a field's value, `initials` draws the value's initials | runtime: row `zas.sub` / `zas.icon`, drawn by `ZasTable` |
| `table.quick_filters` | `key` = slug(label) | `?qf=` filter |
| `table.row_actions` (alias `can_do`) | `type` default **confirm**; `do`→`label`; `by`→`roles` | `row_actions` list |
| `custom_requirements[]` | holes `<entity>__req__N` | [custom-code](../custom-code.md) |

Derived per entity: `names` (model, view, table, form, edit_form, workflow, detail, url,
endpoint, url_name), `parents` (contracts §3), `policies`, `access_resolved` (all roles,
all actions when `access` is absent), `workflow.statuses[].wf_color`.

## Detail view

| Key | Normalised | Becomes |
|---|---|---|
| `hero, title, back_to, layout, roles` | `layout` default `header_tabs` | `zas_view` config |
| `header.{avatar, title, subtitle, badges, facts, actions, banners}` | `show_when` → `show_when_ast` | `data.zas.header` |
| `stats[].value.{count, sum, field, text}` | `where` → `where_ast`; registers a parent param | `data.zas.stats` |
| `sidebar[] / tabs[].sections[]` | `type` default `fields` | `data.zas.panels` / `mini_tables` |
| `tabs[]` (`related_table`) | adds `param`, `preset` (one-hop FK) | child `ZasTable` on `<endpoint>?<param>=<uuid>` |
| `tabs[]` (`custom`) / sidebar `custom` | hole + slot `Pascal(label)Tab` / `Pascal(title)` | `frontend/src/custom/slots/` |

## Lint: errors (stop the build)

- spec not a mapping; missing/non-snake `app.code`; duplicate role/module/entity/page/tab/transition/row-action codes
- reserved names: role `AnonymousUsers`/`SystemUsers`, role > 50 chars, module `app`/`zas_core`/`packages`, field names in `RESERVED` (`id pk object_uuid created_* modified_* objects save delete clean meta status tags check`)
- unknown: field type, kind, page type, tab/section type, layout, access action, row-action type, column source, format, choice set, role anywhere, link target, display field, detail view in `row_click`/`link_to`/`after_create`
- expressions that do not parse or do not resolve (path, status code, choice value, tag, `has_tag` on a status, role in `current_user.role`)
- workflow: no statuses, >1 initial, unknown from/to, empty `from`, tag code clashes with a status
- forms: unknown field; `editable_in` not a status; `readonly_when` unknown field
- validation: rule with no `require`/`require_expr`/`text`; bad `compare`/`on_match`/`on_fail`/`threshold`
- `via` that does not end at the hero; tab `add` when the child has no `form.create`
- `auto.sequence` without `{000}`; `default: today` on a non-date; pattern that does not compile; choice default not in choices
- modules linking to each other in a cycle (Python import cycle)
- **text cut at a comma inside `{ }`** (a key with a space and no value)

## Lint: warnings (build continues, report them)

no `access` block; role without menu; menu page the role cannot access; actions without `view`;
transition without roles or without `condition_msg`; system transition with roles; non-`danger`
tone; >1 primary per status; tag nobody can set; required field missing from the create form;
readonly/auto/computed field on a form; computed field not readonly; label typo (`Byy`, doubled
words); non-spec colour; `multi_link` (mapping model); two-hop tab with `add`; sidebar with
`header_tabs`; `{field}` that is a transition-form field; custom page without `text`; 360 tab hidden for a
role that can open the 360 but has no `view` on the tab entity.

## The five template bugs the checker caught

| Where | Bug | Fix in `evals/vendor_hub.yaml` |
|---|---|---|
| `purchase_order.fields.vendor.limit_choices` | `has_tag on_hold` - `on_hold` is a status | `status == approved` |
| `purchase_order.fields.total_amount.computed` | text cut at the comma inside `{ }` | quoted |
| `purchase_order.table.row_actions.download_pdf.text` | cut at a comma | quoted |
| `vendor_360.tabs.documents.empty_state.text` | cut at a comma | quoted |
| `purchase_order.fields.expected_by.label` | "Expected Byy" (warning) | "Expected By" |
