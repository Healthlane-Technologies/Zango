# Map: `table` → `tables.py` (and `views.py`, `urls.py`)

One `backend/<module>/tables.py` per module. Worked example:
`references/examples/vendors/tables.py`. Package reference:
`references/zango/packages/crud/tables/core.md` (ModelTable, columns, row actions,
`<col>_getval`) and `tables/advanced.md`. Checked against crud **1.0.17** source.

## The class

```python
class VendorTable(ZasTableMixin, ModelTable):
    zas_entity = "vendor"
    pagination = 25                 # table.page_size; a CLASS attribute (crud ignores Meta.pagination)

    <columns>                       # in table.columns order
    row_actions = [<…>]

    def <key>_getval(self, obj): …  # computed / path columns only

    class Meta:
        model = Vendor
        fields = [<every source: field column key that is a model field, in order>]
        detail_class = VendorDetail   # only when the entity is the hero of a detail view
```

Read the columns from `entities.<e>.table.columns` in `.zas/spec.resolved.json`.
Defaults (first 6 non-long fields + `status`) are already filled in there.

## Columns

| Resolved `source` | Column | Kwargs |
|---|---|---|
| `field`, plain | `ModelCol(display_as=…)` | `searchable=True` if `searchable` **or** `filterable`; `sortable=True` if `sortable` |
| `field`, link | `ModelCol(display_as=…, related_object_attribute="<display or target display>")` | as above |
| `field`, builtin (`created_at`, `modified_at`, `id`) | `ModelCol(display_as=…)` | add to `Meta.fields` |
| `status` | `StatusCol(display_as=…, searchable=True)` | needs the workflow on the CrudView |
| `tags` | `TagsCol(display_as=…)` | |
| `computed` | `StringCol(display_as=…)` + `<key>_getval` calling hook `<entity>__col__<key>(obj)` | |
| `path` (`city.state.name`, `vendor_contact[is_primary].email`) | `StringCol(display_as=…)` + `<key>_getval` | see below |

Every column with `roles` → `user_roles=[…]`. `exportable: false` → `exportable=False`.

**getval bodies:**

```python
    def open_po_value_getval(self, obj):  # zas:hole H-11
        return zr.display(hooks.vendor__col__open_po_value(obj), "money")   # column format, if any

    def primary_email_getval(self, obj):  # source: path
        return zr.display(zr.value_of(obj, "vendor_contact[is_primary].email"), None)
```

Use `from ..zas_core import records as zr`. A `format` on a `field` column needs no code
(crud renders model values). A `format` on a computed or path column goes through
`zr.display(value, "<format>")`.

**Not generated in Python:** `link_to` (the frontend turns the cell into a link from
`spec.ui.json`), `row_click` (ListPage wires the 360 route), `quick_filters`,
`default_sort` and the 360 parent filter (`ZasTableMixin` reads them from `spec.json`).
`footer_totals` is not rendered yet. The checker accepts it; mention it in the report.

## Row actions

`row_actions` lists the crud dicts in spec order. Each needs `name`, `key`, `description`
and `type`:

| Spec `type` | crud dict | Extra |
|---|---|---|
| `edit` | `{"type": "form", "form": <Model>EditForm, "roles": form.edit.roles or the row-action roles}` | key **`edit`** |
| `form` | `{"type": "form", "form": <Model><Key>ActionForm}` | form → [forms](forms.md); `on_done` → hook |
| `confirm` | `{"type": "simple", "confirmation_message": <confirm>}` | `on_done` → hook |
| `download` | `{"type": "simple"}` | hook saves the file and returns `{"url": …}` |
| `navigate` | `{"type": "simple"}` | client-side (ListPage/360 read `navigate`/`field_links` from `spec.ui.json`) |
| `delete` | `{"type": "simple", "confirmation_message": "Delete this <name>? This cannot be undone."}` | key **`delete`** |
| entity has `delete` in some role's `access.actions` but no delete row action | add the `delete` entry anyway | |

`roles` on the dict = the spec's row-action `roles` (crud hides the action for other
roles). Leave it out when the spec has none.

### Do NOT hand-write

`can_perform_row_action_<key>` and `process_row_action_<key>`. `ZasTableMixin.__getattr__`
supplies them for every spec action:

- **can_perform**: `show_when`, `form.edit.roles` + `editable_in` (edit), the `delete`
  access action, **and the role's row scope**. Crud's action endpoints load the record by
  uuid without scoping, so `access.in_scope` is checked on every non-list request.
- **process**: `delete` deletes. `navigate` returns the target. Everything else calls hook
  `<entity>__action__<key>(request, obj, form_data) -> dict` (contracts §6). A missing
  hook answers `"<label> is not implemented yet (<fn>)"`, so the test harness reports it.
- `form` actions: crud runs `form.save()` (`ZasActionFormMixin` writes same-name fields),
  then `perform_row_action`. That calls the hook with the cleaned data.

Workflow transitions and tag toggles are **not** row actions. The crud package adds
them to the row menu from the CrudView's `workflow`.

## `views.py` and `urls.py`

```python
class VendorCrudView(ZasCrudViewMixin, BaseCrudView):
    zas_entity = "vendor"
    page_title = "Vendors"            # page.title, else entity plural
    add_btn_title = "Add Vendor"      # table.add_button, else "Add <name>"
    model = Vendor
    form = VendorForm
    table = VendorTable
    workflow = VendorWorkflow         # only if the entity has a workflow
```

`urls.py`: `path("<entity url>/", <Model>CrudView.as_view(), name="<entity code>")`, one per
entity, **including child and master entities with no page of their own**. 360 tabs
call their endpoints. The module is registered in `settings.json` twice: `modules` gets
`{"name": "<module>", "path": "backend.<module>"}`, and `app_routes` gets
`{"module": "<module>", "re_path": "^<module url>/", "url": "urls"}`. The endpoint is
then `/<module url>/<entity url>/` (contracts §1).

## `policies.json`

One policy per distinct feature set among the roles that can `view` the entity
(contracts §5). Each policy lists `<module>.views.<Model>CrudView` with its features. See
[access](access.md).

## Checks before moving on

- `python -m py_compile backend/<module>/tables.py views.py urls.py`
- Every `Meta.fields` entry is a real model field. Columns not in `Meta.fields` are
  declared columns (StringCol/StatusCol/TagsCol).
- Every `type: form` dict has a `form`, and every `simple` action has a spec entry,
  so the mixin can supply `process_row_action_<key>`. Crud raises `ImproperlyConfigured`
  otherwise.
- `pagination` is a class attribute.
