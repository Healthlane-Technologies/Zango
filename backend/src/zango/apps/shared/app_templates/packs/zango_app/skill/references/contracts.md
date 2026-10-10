# Contracts

The fixed interfaces between the spec checker, the generated backend, the
`zas_core` runtime, the React runtime and the tests. Every other reference
assumes these. **If you need to change one, change it here first**, then every
place that depends on it.

Read this once at Phase 1. Later phases read only the section they need.

---

## 1. Naming (derived, never invented)

From codes in the spec (`snake_case`). `Pascal()` capitalises each `_` part.

| Thing | Rule | `purchase_order` in module `procurement` |
|---|---|---|
| Module folder | `backend/<module.code>/` | `backend/procurement/` |
| Module URL prefix (`settings.json` `re_path`) | `^<module.code with - for _>/` | `^procurement/` |
| Model class | `Pascal(entity.code)` | `PurchaseOrder` |
| CRUD view | `<Model>CrudView` | `PurchaseOrderCrudView` |
| CRUD path in module `urls.py` | `<entity.code with - for _>/` | `purchase-order/` |
| **CRUD endpoint** (used by React, tests, tabs) | `/<module url>/<entity url>/` | `/procurement/purchase-order/` |
| Table / create form / edit form | `<Model>Table`, `<Model>Form`, `<Model>EditForm` | |
| Workflow | `<Model>Workflow` | |
| Detail class | `<Model>Detail` | |
| Transition form | `<Model><Pascal(transition)>Form` | `PurchaseOrderCancelForm` |
| Tag form | `<Model><Pascal(tag)><Enable\|Disable>Form` | |
| Row action form | `<Model><Pascal(key)>ActionForm` | |
| Policy name | `<Model>Access<N>` (one per distinct feature set) | `PurchaseOrderAccess1` |
| React page export | `Page_<page.code>` | `Page_purchase_orders` |
| Slot export | `Pascal(slot key)` | `OnboardingChecklist` |

The checker writes every derived name into `.zas/spec.resolved.json`
(`entities.<code>.names`). Generated code uses those strings, never re-derives them.

## 2. Workflow names

The engine (`packages/workflow/base/engine.py`) matches `transition["from"]`
against **one** status. A spec transition with `from: [a, b]` expands to one
engine transition per source:

- single `from`: engine name = spec `name` (`approve`)
- several: `<name>__<from>` (`close__acknowledged`, `close__partially_invoiced`)

Every expanded name gets `<engine name>_condition` / `<engine name>_done`
methods on the workflow class, all delegating to **one** hook per spec
transition (section 6). Spec-level code (tests, React, `data.zas`) uses the
**spec** name; `data.zas.actions.transitions[].engine_name` carries the engine
name for the request.

`trigger: system` → `"is_manual": False`. Tags: `Meta.tags = [(code, label), …]`,
`tag_transitions = [{"name": code, "enabled": {...}, "disabled": {...}}]`;
hooks `<tag>_enabled_condition`, `<tag>_enabled_done` (and `disabled`).

## 3. The parent parameter (360 child tabs)

For every `detail_views[].tabs[]` of `type: related_table`, and every
`mini_table` section and `stats.value.{count,sum}` with `via`:

- **param** = `<hero.code>_uuid` (`vendor_uuid`, `purchase_order_uuid`).
  If one child entity reaches the same hero through two different `via` paths,
  the second becomes `<hero.code>__<first hop>_uuid`. The checker resolves this.
- **lookup** = `via` with `.` → `__`, plus `__object_uuid`
  (`purchase_order.vendor` → `purchase_order__vendor__object_uuid`).
- **form preset** = only when `via` is one hop: that FK is preset from the
  param and hidden. Two-hop tabs cannot preset; the checker warns if such a tab
  has `add` enabled.

Read from one place, `entities.<child>.parents` in `spec.json`
(`{"<param>": {"hero", "via", "lookup", "fk"}}`). Generated classes never repeat it:

1. the tab's `api_endpoint`: `<child endpoint>?<param>=<hero object_uuid>` (`Detail360.tsx`, from `spec.ui.json`)
2. `access.parent_filter()`, called by `ZasTableMixin.get_table_data_queryset()` **only when the request action is `get_table_data`/`export_table`**, never on the detail fetch
3. `ZasFormMixin.__init__`: presets and hides `fk` (one-hop only)

Values arrive with a trailing `/` from the router sometimes; strip it. An
unparseable uuid filters to nothing (`.none()`), never a 500.

## 4. Row scoping

`access.<Role>.rows` is normalised into `entities.<e>.access_resolved` in `spec.json` and applied by
`access.scope_queryset()` (called from `ZasTableMixin` and `ZasDetail.get_object`). Nothing is generated:

| Spec `rows` (kept as written; `where` gains `ast`) | Queryset |
|---|---|
| `all` / absent | unchanged |
| `created_by_me` | `created_by=request.user` |
| `{own: <path>}` | `<path __>__object_uuid=<bound uuid>`; `own: id` → `object_uuid=<bound uuid>` (bound uuid = `access.bound_uuid`: `request.user.app_objects[str(role.id)]`) |
| `{where: <expr>, ast}` | `expr.to_q(ast)` |
| `{text: …}` | `hooks.<entity>__rows__<role slug>(request, qs)`; a missing hook returns **no rows** |
| role not in `access` or `no_access` | no rows, and the role is in no policy for this view (403) |

The `own` binding comes from `app_user` (an `AppUserModel` with
`app_objects[str(role.id)] = str(record.object_uuid)`; see `zas_core/app_user.py`).
Row scoping applies to **every** table request **and** to `ZasDetail.get_object()`.

## 5. Access → policies and runtime checks

| Action | Enforced by |
|---|---|
| `view` | role listed in a `policies.json` policy for the CRUD view |
| `add` | policy feature `add` (+ `form.create.roles` if given) |
| `export` | policy feature `download` |
| `edit` | `row_actions` `edit` entry `roles` + `can_perform_row_action_edit` (`editable_in`, `show_when`) |
| `delete` | `row_actions` `delete` entry (`type: simple`, `process_row_action_delete`) |
| `detail` | `ZasDetail` returns `no_access` for roles without it |

One policy per distinct feature set: roles with `[add, download]` share
`<Model>Access1`, roles with `[]` share `<Model>Access2`, and so on.

## 6. Hooks (hand-written logic)

Every plain-language item becomes one function in `backend/<module>/hooks.py`
(or a React slot, section 9). Generated code calls these; the agent writes
their bodies. Signatures are fixed:

| Spec item | Function | Signature → return |
|---|---|---|
| transition `condition.text` (alone or inside `all`/`any`) | `<entity>__<transition>__condition` | `(request, obj) -> bool` |
| transition `on_done` | `<entity>__<transition>__done` | `(request, obj, form_data: dict) -> None` |
| system transition `text` | `<entity>__<transition>__run` | `() -> int` (records moved); scheduled from `tasks.py` |
| tag enable/disable condition text | `<entity>__tag_<tag>_<enable\|disable>__condition` | `(request, obj) -> bool` |
| system tag `text` | `<entity>__tag_<tag>__sync` | `() -> int`; scheduled |
| `form.create.on_create` | `<entity>__on_create` | `(request, obj) -> None` |
| `validation.rules[].text` | `<entity>__validate__<n>` | `(form, cleaned: dict) -> bool` (True = passes) |
| `access.<Role>.rows.text` | `<entity>__rows__<role slug>` | `(request, qs) -> qs` |
| field `computed` (text) | `<entity>__compute__<field>` | `(obj) -> value`; called on save |
| table column `source: computed` with `shows` | `<entity>__col__<key>` | `(obj) -> value` |
| `row_actions[].on_done` (form, confirm) / `download` text | `<entity>__action__<key>` | `(request, obj, form_data: dict) -> dict` (`{message?, url?}`; a download saves the file and returns its `url`, never an HttpResponse) |
| `detail_views.stats[].value.text` | `<view>__stat__<n>` | `(request, obj) -> number \| None` |
| `detail_views` custom section / tab | `<view>__custom__<key>` | `(request, obj) -> dict` → `data.zas.custom.<key>` |
| `custom_requirements[]` (backend, integration, notification, permission) | `<entity\|app>__req__<n>` | free signature, wired where the text says |
| `custom_requirements[]` (scheduled) | `<entity\|app>__req__<n>` in `tasks.py` | Celery task |

`<transition>` is the **spec** name. `<role slug>` is the role name lower-cased
with non-alphanumerics → `_`. Expressions (non-text) are **generated**, never
hooks.

Every hook carries the marker comment `# zas:hole H-NN` (section 10). Generated
code never overwrites `hooks.py`; re-runs only append missing functions.

## 7. Expressions

Grammar (spec header + extensions the checker accepts):

```
expr     := or_expr
or_expr  := and_expr ("or" and_expr)*
and_expr := not_expr ("and" not_expr)*
not_expr := "not" not_expr | atom
atom     := "(" expr ")" | comparison | unary | has_tag | role_check
comparison := path OP value            OP: == != > >= < <=
            | path ("in" | "not_in") "[" value ("," value)* "]"
unary    := path ("is_set" | "is_empty" | "is_true" | "is_false")
has_tag  := "has_tag" code
role_check := "current_user.role" ("==" | "!=") "\"Role\""
path     := ident ("." ident)*         # status, tags, form.<f>, current_user.*, field paths
value    := number | 'quoted' | "quoted" | bare word | today | today+N | path (right side may be a field path)
```

Plus the structured forms `{all: [...]}`, `{any: [...]}`, `{text: "..."}`
and lists (a YAML list means `all`). `zas_core.expr` compiles one AST to:

- `to_q(model)` → Django `Q` (for querysets; `status` / `has_tag` use workflow
  subqueries; `current_user.*` resolves to a constant; `form.*` is not allowed)
- `evaluate(obj, ctx)` → `bool` (for one record; `ctx` carries `request`,
  `form` values)

A `text` node is a hook reference resolved by the generated code before it
reaches `zas_core`.

## 8. `data.zas` (the 360 payload)

`<Hero>Detail(ZasDetail, BaseDetail).fetch_item_details()` returns the
standard crud payload **plus** `zas`:

```jsonc
{
  "pk": 12, "object_uuid": "…", "title": "…",
  "general_details": {"fields": {…}},          // Meta.fields: every field the page reads
  "workflow_details": {…}, "row_actions": […],
  "zas": {
    "view": "vendor_360",
    "access": "ok",                            // ok | no_access | not_found
    "record": {"uuid": "…", "pk": 12, "status": "approved", "status_label": "Approved",
               "status_tone": "green", "tags": [{"code": "msme", "label": "MSME", "tone": "teal"}]},
    "header": {
      "title": "Apex Industries", "subtitle": "VEN-00012 · Manufacturer · Pune",
      "avatar": {"image": "https://…" | null, "initials": "AI"},
      "badges": [{"key": "status", "label": "Approved", "tone": "green"}],
      "facts": [{"key": "gstin", "label": "GSTIN", "value": "27AAP…", "copy": true,
                 "emphasis": false, "link": {"page": "vendor_360", "uuid": "…"} | null}],
      "banners": [{"tone": "warning", "text": "…"}]
    },
    "stats": [{"key": "s1", "label": "Open POs", "value": 7, "format": "number",
               "tone": "blue", "icon": "shopping-cart", "tab": "purchase_orders"}],
    "tabs": [{"code": "contacts", "count": 3, "count_tone": null}],   // only tabs this role may see
    "panels": {"<tab code | sidebar index>": [{"title": "Commercials", "columns": 2,
               "fields": [{"key": "payment_terms", "label": "Payment terms",
                           "value": "net_30", "display": "Net 30", "type": "choice", "tone": null}],
               "editable": false}]},
    "mini_tables": {"<tab>.<section index>": {"rows": [{…display values…, "uuid": "…"}], "total": 7}},
    "actions": {
      "transitions": [{"name": "approve", "engine_name": "approve", "label": "Approve",
                       "primary": true, "tone": null, "confirm": null, "has_form": true,
                       "allowed": true, "blocked_reason": null}],
      "tags": [{"code": "msme", "label": "MSME", "state": "disabled", "allowed": true,
                "has_form": true, "confirm": "Mark as MSME?"}],
      "buttons": [{"key": "new_po", "label": "New PO", "type": "create_related",
                   "icon": "plus", "entity": "purchase_order", "prefill": {"vendor": "<uuid>"}}],
      "row_actions": ["edit", "resend_invite"]
    },
    "custom": {"<key>": {…}},                  // hook results for custom panels/tabs/stats
    "formats": {"locale": "en-IN", "currency": "INR"}
  }
}
```

Rules: everything role- or `show_when`-dependent is already filtered server-side.
A missing value is `null` (rendered "—"), never `0`. Tones are spec colour names
(`gray blue green amber red purple teal indigo pink`); banner tones are
`info warning danger success`.

## 8b. List rows and the record drawer (any entity)

`ZasTableMixin.post_process_data` adds to every crud row:
`"zas": {"links": {"<link column>": "<linked object_uuid>"}, "status": "<code>", "tags": ["<code>"], "hl": {"<column>": "red"}}`
(`status`/`tags` only for entities with a workflow; `hl` only where a column `highlight.when` is true).
`get_table_metadata` adds `zas.quick_filters` (role-filtered) and `zas.filter_options` (`{<link column>: [display values]}`).

`GET <entity endpoint>?action=zas_record&object_uuid=<uuid>` (`ZasCrudViewMixin.get` → `detail.record_payload`),
row-scoped like every other read (`access: "not_found"` outside the role's rows, `"no_access"` without view):

```jsonc
{"entity": "site_visit", "access": "ok",
 "record": {"uuid", "pk", "display": "VIS-00028", "status", "status_label", "status_tone", "tags": [{code, label, tone}]},
 "fields": [FieldValue, …],                       // every spec field, display-ready (§8)
 "transitions": [ZasAction, …],                   // same as §8 actions.transitions (workflow_actions())
 "tags": [ZasTagAction, …],
 "row_actions": [{"key", "label", "type": "form|simple", "spec_type", "confirm"}],
 "events": [ …timeline events… ]}                 // created / updated / transition / tag, newest first
```

## 9. `spec.ui.json` (frontend config) and slots

`frontend/src/custom/spec.ui.json` is written by the checker from the resolved
spec. The React runtime reads only this file plus `data.zas`:

```jsonc
{
  "app": {"code", "name", "description", "locale", "currency", "brand": "#4F46E5"},
  "pages": {"<code>": {"type": "crud|detail|custom", "route": "/app/vendors",
             "title", "entity"?, "detail_view"?, "component"?, "export": "Page_vendors"}},
  "entities": {"<code>": {"name", "plural", "endpoint", "display", "list_page"?, "detail_view"?,
             "statuses": {"<code>": {"label", "tone"}}, "tags": {"<code>": {"label", "tone"}},
             "columns": [{"key", "label", "source", "format", "link_to"?, "display"?, "filterable"?, "sortable"?,
                          "searchable"?, "type"?, "to"? /* link target entity */}],
             "fields": [{"key", "label", "type", "to"?, "display"?}],
             "quick_filters": [{"key", "label", "default"}], "row_click", "add_button",
             "footer_totals": []}},
  "detail_views": {"<code>": {"hero", "layout", "back_to", "states", "tabs": [
             {"code", "label", "type", "entity"?, "param"?, "columns"?, "add"?: {"label", "prefill"},
              "row_click"?, "empty_state"?, "group_by"?, "footer_totals"?, "slot"?}],
             "sidebar": [{"type", "title", "slot"?}]}},
  "slots": {"<key>": {"export": "OnboardingChecklist", "hole": "H-15"}}
}
```

Slots live in `frontend/src/custom/slots/<Export>.tsx`, are exported from
`slots/index.ts`, and receive `SlotProps` (`record`, `zas`, `data` =
`zas.custom[key]`, `refresh`, `api`).

**Routing.** A hero's 360 is served by its **list page** (`makeListPage`), which renders the 360
for `<list route>/detail-view/<uuid>` (AppBuilder matches `<route>/*`) and `ZasTable` otherwise.
That list page is the only route owner for the entity; every other place navigates there.
A `detail` page with no list page for its hero gets its own custom route
`<route without :id>/:id` rendering `makeDetailPage`.

## 10. Holes

`.zas/holes.md` lists every plain-language item:

```
| ID | Kind | Spec path | Text | Target | Status |
| H-07 | on_done | entities.vendor.workflow.transitions.approve.on_done | Copy risk_rating… | backend/vendors/hooks.py::vendor__approve__done | todo |
```

Kinds: `condition`, `on_done`, `system_transition`, `tag_condition`,
`system_tag`, `on_create`, `validation`, `rows`, `computed`, `column`,
`row_action`, `stat`, `custom_panel`, `custom_tab`, `custom_page`,
`requirement`. Status: `todo` → `done` | `needs-review` | `blocked` | `covered`. Checked by `spec_check.py --audit-holes`.
The marker `# zas:hole H-07` (Python) or `// zas:hole H-07` (TS) sits on the
line above the function. Hole IDs are stable across re-runs (keyed by spec
path); new items get the next free number.

## 11. `data-zas` attributes (design tests)

Every runtime component renders `data-zas="<kind>"` and, where it applies,
`data-zas-key`, `data-zas-tone`, `data-zas-order`, `data-zas-layout`.

| `data-zas` | On | Keys |
|---|---|---|
| `page` | page root | `key` = page code, `layout` |
| `menu-item` | sidebar link (our nav only) | `key` = page code, `order` |
| `header`, `title`, `subtitle` | 360 header | |
| `badge` | any status/tag/field badge | `key`, `tone` |
| `fact` | header fact | `key`, `order` |
| `banner` | header banner | `tone`, `order` |
| `stat` | stat tile | `key`, `tone`, `order` |
| `tab` | tab button | `key`, `order` |
| `panel` | field panel, mini table, custom slot | `key`, `order` |
| `field` | label/value pair | `key` |
| `action` | header/drawer button | `key` (transition/tag/button key), `tone` |
| `quick-filter` | chip | `key`, `order` |
| `empty` | empty state | `key` = tab or table key |
| `rail` | sidebar column | `layout` |

Preview parity (testing.md) needs the Studio preview to render the same attributes and to
support a deep link. It does not yet, so that check is reported as skipped.
