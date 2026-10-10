# Map: forms → `forms.py`

One `backend/<module>/forms.py` per module. Worked example:
`references/examples/vendors/forms.py`. Package reference:
`references/zango/packages/crud/forms/core.md` (BaseForm, BaseSimpleForm, ModelField,
`Meta.order`, `sync_enabled`). This file says which class each spec block becomes and
what **not** to hand-write, because `ZasFormMixin` / `ZasActionFormMixin` already do it.

## Which class for which spec block

| Spec block | Class | Bases | Name (contracts §1) |
|---|---|---|---|
| `form.create` | create form | `ZasFormMixin, BaseForm` | `<Model>Form` |
| `form.edit` | edit form (subclass of create) | `<Model>Form` | `<Model>EditForm` |
| `workflow.transitions[].form` | transition form | `ZasActionFormMixin, BaseSimpleForm` | `<Model><Transition>Form` |
| `workflow.tags[].enable/disable.form` | tag form | `ZasActionFormMixin, BaseSimpleForm` | `<Model><Tag><Enable/Disable>Form` |
| `table.row_actions[type=form].form` | row-action form | `ZasActionFormMixin, BaseForm` (with `Meta.model`) | `<Model><Key>ActionForm` |
| entity with no `form` block | create form with every non-readonly field | as `form.create` | `<Model>Form` |

Mixins always go **first** in the bases. Every class sets `zas_entity = "<entity code>"`.
Create/edit forms also set `zas_form = "create"` / `"edit"`.

## Create / edit forms (`BaseForm`)

One `ModelField` per form field, declared in the order of
`form.<kind>_resolved` from `.zas/spec.resolved.json`:

| Spec (field or per-form override) | `ModelField(...)` kwarg |
|---|---|
| `label` | `label=` |
| `required` | `required=True` (only when the spec field is required) |
| `help` | `description=` |
| `tooltip` | `tooltip=` |
| `pattern` / `pattern_msg` | `pattern=r"…"`, `pattern_msg="…"` |
| money field | `prefix="<currency symbol>"` |
| a field that another field's `show_when` reads | `sync_enabled=True` |

`Meta`:

```python
    class Meta:
        model = Vendor
        title = "Add Vendor"            # form.create.title, else "Add <name>"
        layout = "drawer-half"          # >6 fields; omit for small forms (modal)
        order = [["legal_name", "vendor_type"], ...]   # see Order
        success_message = "Vendor saved."
```

**Order.** Walk `<kind>_resolved` sections in order. Pack each section's fields two per
row (`[[a, b], [c, d], [e]]`). Put `long_text`, `file`, `image`, `json` and
`multi_choice` fields on a row of their own. A section boundary always starts a new row.
`ZasFormMixin.convert_model_form_to_json_schema` drops removed or hidden fields from
`ui:order`, so list every field even when it has a `show_when`.

**Edit form.** Subclass the create form, set `zas_form = "edit"`, and give it its own
`Meta` (title `Edit <name>`, `order` copied from the create form unless `form.edit` lists
other fields). With `same_as: create` and nothing else, the body is only `zas_form` and
`Meta`. If the edit form has fields that the create form lacks, declare them.

**Child entity forms.** Declare the parent FK (`vendor = ModelField(label="Vendor",
required=True)`) even when the spec form leaves it out. The list page needs it. On a 360
tab, `ZasFormMixin` presets it from `?<parent param>=<uuid>` and hides it (contracts §3).

### Do NOT hand-write (the runtime does it from `spec.json`)

| Spec | Done by |
|---|---|
| parent FK preset + hide on 360 tabs | `ZasFormMixin.__init__` step 1 |
| `show_when` (server side, re-checked on every sync) | `ZasFormMixin.__init__` step 2 (removes the field) |
| `form.edit.readonly_when` | `ZasFormMixin.__init__` (disabled + `readonly` property) |
| `fields[].limit_choices` | `ZasFormMixin.__init__` (queryset filter) |
| `validation.rules` (`when`/`require`/`require_expr`) | `ZasFormMixin.clean` |
| `validation.rules[].text` | `ZasFormMixin.clean` calls hook `<entity>__validate__<n>(form, cleaned)` → bool |
| `validation.duplicate_check` | `ZasFormMixin.clean` + `zas_core.dupes` |
| `on_fail/on_match: warn` | `zas_confirm` checkbox, added automatically |
| `form.create.on_create` (text) | `ZasFormMixin.save` calls hook `<entity>__on_create(request, obj)` |
| `app_user` with `create_on: create` | `ZasFormMixin.save` → `app_user.maybe_provision` |
| `form.create.roles` (who sees *Add*) | `ZasCrudViewMixin.display_add_button_check` + `post` |
| `form.edit.roles` / `editable_in` (who sees *Edit*) | `ZasTableMixin.zas_can_perform("edit")` |
| title | `convert_model_form_to_json_schema` |
| sequences / arithmetic computed fields | `zr.apply_on_save` in the model ([models](models.md)) |

Never put a readonly, `auto` or `computed` field on a create/edit form. The checker
warns, and the runtime fills it on save.

### Hand-write only

- `clean_<field>` for `file`/`image` `accept` and `max_size_mb` (the vendors example's
  `VendorDocumentForm.clean_file`), and for `multi_choice` value checks.
- `min` / `max` on numbers: `clean_<field>` raising `forms.ValidationError("Must be at least 0.")`.
- Nothing else. Logic described in plain language goes to `hooks.py` ([custom-code](../custom-code.md)).

## Transition, tag and row-action forms

Fields are **plain Django form fields**, not `ModelField`. These forms are not ModelForms
(BaseSimpleForm), or their fields are not model fields.

| Spec field type | Django field |
|---|---|
| `text` | `forms.CharField(max_length=…)`; with `pattern` → `forms.RegexField(regex=…)` |
| `long_text` | `forms.CharField(widget=forms.Textarea)` |
| `integer` / `decimal` / `money` | `forms.IntegerField` / `forms.DecimalField(decimal_places=2)` |
| `boolean` | `forms.BooleanField(required=False)` |
| `date` / `datetime` | `forms.DateField` / `forms.DateTimeField` |
| `email` / `url` | `forms.EmailField` / `forms.URLField` |
| `choice` | `forms.ChoiceField(choices=<SET>_CHOICES)`; import the constant from `.models` |
| `link` | `forms.ModelChoiceField(queryset=<Model>.objects.all())` |
| `file` | `forms.FileField` |

`required=` follows the spec (default False). `Meta` has `title` (the transition, tag or
action label), `order` (one field per row) and `layout = "drawer-half"` for more than 3 fields.

**Same-name write-back.** When a form field has the same key as an entity field
(`risk_rating` on `approve`), `ZasActionFormMixin.save` writes it to the record. The
`done` hook does not need to copy it. Every value is also handed to the hook as
`form_data` (contracts §6). Transition `done` hooks read it from the
`WorkflowTransaction.data["form_data"]`. Row-action hooks get it from `request._zas_form_data`.

**Row-action forms** are `BaseForm` with `Meta.model = <Model>`. The crud package binds
them to the row (`instance`). Their fields are still plain `forms.*Field`, so the mixin
controls what is written.

## Wiring

- Create/edit → `<Model>CrudView.form` and `row_actions[{key:"edit", type:"form", form: <Model>EditForm}]`
  ([tables](tables.md)).
- Transition forms → `status_transitions[].form`. Tag forms → `tag_transitions[].enabled/disabled.form`
  ([workflow](workflow.md)).
- Row-action forms → `row_actions[{type: "form", form: …}]`.

## Checks before moving on

- `python -m py_compile backend/<module>/forms.py`
- Every name in `Meta.order` is a declared field (rjsf fails on unknown names).
- No `ModelField` on a `BaseSimpleForm`.
- `ModelField` objects are class level and shared. Never set `self.declared_fields[x].properties[...]`
  directly. Use `self._zas_set_prop(x, …)`, which copies first.
