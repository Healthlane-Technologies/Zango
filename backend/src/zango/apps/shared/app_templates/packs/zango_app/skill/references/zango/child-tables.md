# Child tables: the parent parameter, end to end

How a 360 tab lists only one parent's children. Contract: `contracts.md` §3. Lookups use **`object_uuid`**.

A 360 tab, mini table, stat or timeline source that lists another entity's rows
is that entity's **own** CRUD endpoint with one query parameter naming the hero.
The parameter is spelled in three places; all three are generated from the
resolved spec, so they cannot drift.

```
spec detail_views.vendor_360.tabs.contacts {entity: vendor_contact, via: vendor}
        │  spec_check.Spec.add_parent()
        ▼
.zas/spec.resolved.json  entities.vendor_contact.parents =
        {"vendor_uuid": {"param": "vendor_uuid", "lookup": "vendor__object_uuid",
                         "hero": "vendor", "via": "vendor", "fk": "vendor"}}
        │  copied to backend/zas_core/spec.json and frontend/src/custom/spec.ui.json
        ├─► 1. React   RelatedTab  api_endpoint = /vendors/vendor-contact/?vendor_uuid=<uuid>
        ├─► 2. Table   ZasTableMixin.get_table_data_queryset → access.parent_filter()
        └─► 3. Form    ZasFormMixin.__init__ presets + hides `vendor`
```

## 1. Derivation (`scripts/spec_check.py`, `Spec.add_parent`)

| Rule | Value |
|---|---|
| param | `<hero.code>_uuid`; a second, different `via` to the same hero → `<hero>__<first hop>_uuid` |
| lookup | `via` with `.` → `__`, plus `__object_uuid` |
| fk (form preset) | the `via` field when `via` is one hop; `None` for two hops |
| `via` omitted | the child's single link to the hero; zero or several links → lint error |
| registered by | `related_table` tabs, `mini_table` sections, `stats.value.count/sum`, timeline sources, `create_related` buttons |

vendor_hub results (`.zas/plan.md`):

| Child | Param | Lookup | Preset |
|---|---|---|---|
| `vendor_contact` | `vendor_uuid` | `vendor__object_uuid` | `vendor` |
| `vendor_document` | `vendor_uuid` | `vendor__object_uuid` | `vendor` |
| `contract` | `vendor_uuid` | `vendor__object_uuid` | `vendor` |
| `purchase_order` | `vendor_uuid` | `vendor__object_uuid` | `vendor` |
| `po_line` | `purchase_order_uuid` | `purchase_order__object_uuid` | `purchase_order` |
| `invoice` | `vendor_uuid` | `purchase_order__vendor__object_uuid` | — (two hops; add is off) |
| `invoice` | `purchase_order_uuid` | `purchase_order__object_uuid` | `purchase_order` |

## 2. Backend: the table (`zas_core/mixins.py` `ZasTableMixin`)

```python
def get_table_data_queryset(self):
    qs = super().get_table_data_queryset()
    req = self._zas_request()
    qs = access.scope_queryset(self.zas_entity, qs, req)        # ALWAYS: role rows
    if access.request_action(req) in access.TABLE_ACTIONS:      # get_table_data / export_table only
        qs = access.parent_filter(self.zas_entity, qs, req)     # ?<param>=<uuid>
        qs = self._zas_quick_filter(qs, req)                    # ?qf=<key>
        ...default_sort
    return qs
```

- **Scope always, parent filter only on list requests.** `BaseDetail.get_object()`
  looks the record up through this same queryset; if the parent filter applied
  there, a filtered endpoint would 500 the detail fetch (entity-360 pitfall 3).
- `access.parent_filter` strips a trailing `/`, validates with `clean_uuid()`;
  an unparseable value returns `qs.none()`, never a 500.
- The parameter **narrows**, it never widens: role scoping runs first, so a forged
  `?vendor_uuid=<someone else's>` on a `rows: {own: vendor}` role returns nothing.
- Do **not** write a `get_table_data_queryset` in a generated table. If a hook truly
  needs one, call `super()` first; skipping it drops scoping for every role.
- There is no `get_queryset()` on `BaseCrudView`; overriding that name does nothing.

## 3. Backend: the form (`ZasFormMixin.__init__`)

For each `entities.<child>.parents` entry with an `fk`, when the request carries the
param and the form is a create:

1. resolve the hero by `object_uuid`; if missing, leave the field as a normal select;
2. `self.fields[fk].initial = hero.pk` and `self.initial[fk] = hero.pk`;
3. `_zas_set_prop(fk, hidden=True)` — rebinds a **`copy.copy` of the class-level
   `ModelField`**. `BaseForm.__init__` fills `declared_fields` with the class objects, so
   mutating `properties` in place would hide the FK on the standalone list page too,
   on a warm worker, with no visible cause.

`hidden` renders `"ui:widget": "hidden"`; the value still submits, so the FK saves.
The child form must declare the FK as a `ModelField` (see
`references/examples/vendors/forms.py` `VendorContactForm.vendor`) so the list page
can still pick it. Two-hop parents (`invoice` via `purchase_order.vendor`) cannot be
preset: lint warns when such a tab has `add`.

## 4. Frontend (`zas/Detail360.tsx`)

| Piece | Behaviour |
|---|---|
| `RelatedTab` | `ZasTable` on `${child.endpoint}?${tab.param}=${uuid}` (group_by, footer_totals, inline filters, row drawer); its Add button → `FormDialog` kind `create`, `params: {[param]: uuid}` (`dialogs.paramsFor` puts it in both `getParams` and `postParams`) |
| `RelatedBody` (module scope) | spec `empty_state` when the tab is empty and unfiltered; column subset via `setColumnVisibility`; row click per `row_click` (`custom` → child 360, `drawer`, `none`) |
| after add | `refetchRef.current()` (the tab's own `refetch`) and `d.refresh()` (badges, stats) |
| mini tables | server-side in `ZasDetail._mini_table()` via `_children()` (same lookup + `scope_queryset`), rows click → `detailUrl()` |
| counts | `ZasDetail._zas_tabs()` → `_children().count()` (+ `count_badge.where`) |

## 5. Verify

| Check | How (per role, from `zas_test/api.py` or by hand) | Expect |
|---|---|---|
| filter applies | `GET <child>?view=table&action=get_table_data&<param>=<A>` | only A's children |
| forged parent | same with a parent B the role cannot see | `data: []` |
| bad value | `<param>=not-a-uuid` | `data: []`, HTTP 200 |
| detail unaffected | `GET <child>?<param>=<A>&view=detail&action=fetch_item_details&object_uuid=<child of B the role may see>` | the record (filter ignored on detail) |
| preset | `GET <child>?action=initialize_form&<param>=<A>` | the FK has `ui:widget: hidden` and default A's pk |
| standalone form | `GET <child>?action=initialize_form` afterwards | the FK is a visible select again |
| UI | add from the tab | the record lands under A; badge +1 without reload |
