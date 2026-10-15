# Expressions

One grammar for every condition in the spec, one parser (`zas_core/expr.py`), used by
the checker (lint), by querysets (`to_q`) and by single records (`evaluate`). You
never hand-translate an expression: generated code passes the parsed AST from
`spec.json` to `zas_core`. Read this when a lint message names an expression, or when
a hook needs to build a query the spec way (`zx.to_q(zx.parse("…"), Model)`).

## Where expressions appear

| Spec key | Evaluated by | Against |
|---|---|---|
| `access.<Role>.rows.where` | `access.scope_queryset` → `to_q` | the entity |
| `table.quick_filters[].where` | `ZasTableMixin._zas_quick_filter` → `to_q` | the entity |
| `fields[].limit_choices` | `ZasFormMixin` → `to_q` on the FK queryset | the **linked** entity (`form.*` = this form) |
| `form.*.fields[].show_when` | `ZasFormMixin` → `evaluate` on live form values | the form (re-run on sync) |
| `form.edit.readonly_when[].when` | `ZasFormMixin` → `evaluate` | the instance |
| `validation.rules[].when / require_expr`, `duplicate_check.scope.where` | `ZasFormMixin.clean` | cleaned data / `to_q` |
| `workflow.transitions[].condition`, `tags[].enable/disable.condition` | `ZasWorkflowMixin` → `evaluate` | the record |
| `row_actions[].show_when` | `ZasTableMixin.zas_can_perform` | the row |
| `app_user.create_on` | `app_user.maybe_provision` | the record |
| `detail_views` `show_when`, `count_badge.where`, `stats.value.where`, `columns.highlight.when` | `ZasDetail` | hero / child records |

## Grammar

```
expr     := or_expr
or_expr  := and_expr ("or" and_expr)*
and_expr := not_expr ("and" not_expr)*
not_expr := "not" not_expr | atom
atom     := "(" expr ")" | path OP value | path ("in" | "not_in" | "not in") [v, …]
          | path is_set | is_empty | is_true | is_false
          | [path] has_tag <code> | current_user.role (== | !=) "Role"
```

Structured forms: a YAML list means `all`; `{all: [...]}`, `{any: [...]}`; `{text: "…"}`
is a plain-language node (below). `and`, `or`, `not` and parentheses are extensions
over the template's header and are accepted by the checker and the Studio lint.

## Operators

| Expression | `to_q(model)` | `evaluate(obj)` |
|---|---|---|
| `vendor_type == manufacturer` | `Q(vendor_type="manufacturer")` | `obj.vendor_type == "manufacturer"` |
| `gstin != null` / `x == null` | `~Q(gstin__isnull=True)` | `is not None` |
| `credit_limit >= 500` | `Q(credit_limit__gte=500)` | numeric compare (Decimal → float) |
| `city.name == 'Pune'` | `Q(city__name="Pune")` | attribute walk |
| `end_date > start_date` | `Q(end_date__gt=F("start_date"))` | field vs field |
| `status in [a, b]` | `object_uuid__in` WorkflowState subquery | `current_status(obj) in …` |
| `purchase_order.status == draft` | `purchase_order__object_uuid__in` subquery | status of the related record |
| `x not_in [a]` / `x not in [a]` | `~Q(x__in=[…])` | not any equal |
| `gstin is_set` / `is_empty` | `~Q(isnull) & ~Q("")` for text | not None / not "" / file has a name |
| `is_active is_true` / `is_false` | `Q(is_active=True/False)` | truthy / falsy |
| `has_tag msme` | `object_uuid__in` records whose latest `msme` tag transaction is `enabled` | `"msme" in current_tags(obj)` |
| `vendor has_tag preferred` | same on the related record | same |
| `order_date >= today-30` | `today()` ± N days (`timezone.localdate`) | same |
| `vendor == form.vendor` | value from `ctx["form"]` (query side only on the right) | same |
| `created_by == current_user` | `request.user` | same |
| `current_user.role == "Finance"` | `Q()` or `Q(pk__in=[])` | role check |
| `current_user.vendor` | record bound to the login (`app_user`) | same |

## Values

- numbers, `'quoted'`, `"quoted"`, `true/false`, `null/none`, `today`, `today+N`, `today-N`,
  dotted paths (`a.b`), `form.<field>`, `current_user[.attr]`.
- **A bare word is resolved, not guessed by the parser.** If the left field has `choices`,
  the word is a literal (choice id). Else, if the word is a field on the same model, it is
  that field (`F()` / attribute). Else it is a literal string. Status and tag comparisons
  always take literals. The checker errors when a word is neither a choice of the left
  field nor a field.

## `text` nodes

`{text: "…"}` (alone or inside `all`/`any`) is a plain-language condition. It becomes one
hook (`<entity>__<transition>__condition`, `…__tag_<tag>_<enable|disable>__condition`)
and `evaluate` calls it through `ctx["text"]`. With no hook written yet it counts as
**True** (shown) and the missing hook is listed in `holes.md`. `to_q` refuses a text node:
a plain-language row rule goes through `<entity>__rows__<role>` instead.

## Using it from a hook

```python
from ..zas_core import expr as zx
qs = PurchaseOrder.objects.filter(zx.to_q(zx.parse("status not_in [closed, cancelled]"), PurchaseOrder))
ok = zx.evaluate(zx.parse("gstin is_set and status == draft"), vendor)
zx.current_status(obj); zx.current_tags(obj)   # helpers
```

Verified on Django (sqlite): 17 cases where `to_q` and `evaluate` agree (progress log).
