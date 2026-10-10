# Map: `detail_views` → `<Model>Detail` + 360 page

A 360 page has three parts, and you write only the first one. Mechanics and pitfalls:
`references/zango/entity-360.md` (19 rules, each handled by the runtime) and
`references/zango/child-tables.md` (the parent parameter). Package background:
`references/zango/packages/crud/detail.md`. Worked example:
`references/examples/vendors/detail.py`.

| Part | Who | What |
|---|---|---|
| `backend/<module>/detail.py` | **you** | `<Model>Detail(ZasDetail, BaseDetail)`: `zas_view` + `Meta.fields` |
| `data.zas` payload | `zas_core.detail.ZasDetail` | header, stats, tabs, panels, mini tables, actions, custom data (contracts §8) |
| React page | `zas/Detail360.tsx` | layout, tabs, child tables, dialogs, states, slots |

## The detail class

```python
from ...packages.crud.detail.base import BaseDetail
from ..zas_core.detail import ZasDetail


class VendorDetail(ZasDetail, BaseDetail):
    zas_view = "vendor_360"

    class Meta:
        fields = ["id", <every field of the hero, in spec order>]
```

- One class per `detail_views[]` entry, in the **hero's** module. Name: `<Hero Model>Detail`.
- `Meta.fields` = `id` + **every** hero field. Without it the package payload carries only
  the table columns, and slots that read `general_details` show "—".
- Wire it with `Meta.detail_class = <Model>Detail` on the hero's table ([tables](tables.md)).
- Nothing else. **Do not** add `Meta.sections`, `get_sections` or `get_general_details`, and do
  not override `fetch_item_details`. `ZasDetail.fetch_item_details` calls `super()`, then adds
  `data["zas"] = self.zas_payload(obj)`. Extra data goes through a hook (below).
- Entities without a detail view get no detail class. `row_click: drawer` uses the package's
  default drawer.

## How each spec key is served (nothing to generate)

| Spec | Payload / behaviour |
|---|---|
| `roles`, hero `access.detail` | `ZasDetail.get` → `zas.access = "no_access"` |
| unknown uuid or out of the role's rows | `get_object` uses the scoped table queryset → `zas.access = "not_found"` (HTTP 200) |
| `header.title / subtitle / avatar / badges / facts / banners` | `zas.header`, `{field}` templates via `records.interpolate`, `show_when` + `roles` applied |
| `header.actions.transitions / tags` | `zas.actions.transitions` with `allowed` + `blocked_reason` (`condition_msg`), `primary`, `tone` |
| `header.actions.buttons` (`edit`, `create_related`, `row_action`) | `zas.actions.buttons`, checked against access, `show_when`, row-action gates |
| `stats[].value.count / sum / field` | `zas.stats` (query via `parents` lookup + `where_ast`) |
| `stats[].value.text` | hook `<view>__stat__<n>(request, obj) -> number \| None` |
| `sidebar[]` / summary `sections[]` of type `fields` | `zas.panels.<tab>` / `zas.panels.sidebar` (display-ready `FieldValue`s) |
| `mini_table` | `zas.mini_tables.<key>` (rows, limit, sort, `see_all_tab`) |
| `tabs[type=related_table]` | `zas.tabs[]` (count badge, `can_add`). The React tab loads `<child endpoint>?<param>=<uuid>` |
| `tabs[type=timeline]` / timeline section | `?action=zas_timeline&tab=<code>`: audit log + workflow transactions from `sources` |
| `tabs[type=custom]`, sidebar `custom` | hook `<view>__custom__<key>(request, obj) -> dict` → `zas.custom.<key>`, plus a React slot |
| `states` | `zas.states`, rendered by `StateBox` |
| tab whose entity the role cannot `view` | dropped from `zas.tabs` (the checker warns) |

The checker records hook names, keys and slot export names in `.zas/holes.md`. Copy them.

## Hooks for a 360 (in the hero's `hooks.py`)

```python
# zas:hole H-19
def vendor_360__stat__4(request, obj):
    """Open PO value / credit_limit."""
    ...
    return None if not obj.credit_limit else float(open_value / obj.credit_limit)

# zas:hole H-20
def vendor_360__custom__onboarding_checklist(request, obj):
    """Checklist of the 4 document types…"""
    return {"items": [{"label": "GST certificate", "done": True}, ...], "done": 3, "total": 5}
```

Return `None` for "unknown", never `0`. Custom data must be JSON-serialisable (dates as ISO strings).
The hook computes the data, and the slot only renders it ([custom-code](../custom-code.md)).

## Routing and the React side

- The hero's list page owns the 360 route: `<list route>/detail-view/<uuid>` (contracts §9).
  `pages/index.ts` exports the list page with `makeListPage("<page code>")`. The `detail`
  page itself gets **no AppBuilder route** when its hero has a crud page.
- A `detail` page whose hero has no crud page gets a custom route
  `<route without :id>/:id`, exported as `makeDetailPage("<view code>")` ([pages-menus](pages-menus.md)).
- Slots: `frontend/src/custom/slots/<Export>.tsx`, from `assets/templates/frontend/slots/Slot.tsx.tmpl`,
  exported in `slots/index.ts`. Props: `record`, `zas`, `data` (= `zas.custom[key]`), `refresh`, `api`.

## Checks before moving on

- `python -m py_compile backend/<module>/detail.py`
- `GET <hero endpoint>?view=detail&action=fetch_item_details&object_uuid=<uuid>` as each
  viewer role returns `zas.access == "ok"`, and as a role outside `roles` returns `no_access`
  (the API test layer runs both, see [testing](../testing.md)).
- Every `<view>__stat__` / `__custom__` hole is `done` or reported.
