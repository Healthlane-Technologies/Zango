# Map: fields → `models.py`

Write one `backend/<module>/models.py` per module, entities in `modules[].entity_order`
(links inside the module point backwards). Worked example:
`references/examples/vendors/models.py`. Framework rules (DynamicModelBase, ZForeignKey,
migrations) are in `references/zango/core/models.md`; this file says which pattern each
spec key needs.

## Imports

```python
import datetime
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from zango.apps.appauth.models import AppUserModel          # only if a field links to app_user
from zango.apps.dynamic_models.fields import ZForeignKey
from zango.apps.dynamic_models.models import DynamicModelBase
from zango.core.storage_utils import ZFileField
from ..masters.models import City                           # earlier module (module_order)
from ..zas_core import records as zr
```

## Field type → Django field

| Spec `type` | Field | Notes |
|---|---|---|
| `text` | `CharField(max_length=<max_length or 255>)` | |
| `long_text` | `TextField()` | |
| `integer` | `IntegerField()` | `min/max` are form-side |
| `decimal` | `DecimalField(max_digits=14, decimal_places=2)` | |
| `money` | `DecimalField(max_digits=16, decimal_places=2)` | currency is app-wide (`app.currency`) |
| `percent` | `DecimalField(max_digits=7, decimal_places=4)` | store 0–1 or 0–100 consistently with the spec text |
| `boolean` | `BooleanField(default=<default or False>)` | never null |
| `date` / `datetime` / `time` | `DateField` / `DateTimeField` / `TimeField` | `default: today` → `default=timezone.localdate` (callable) |
| `email` | `EmailField(max_length=255)` | |
| `phone` | `PhoneNumberField()` | never `CharField`; see note |
| `url` | `URLField()` | |
| `choice` | `CharField(max_length=50, choices=<SET>_CHOICES)` | |
| `multi_choice` | `JSONField(default=list, blank=True)` | choices validated by the form |
| `link` | `ZForeignKey(<Model>, on_delete=…, related_name="+")` | see Links |
| `link` to `app_user` | `models.ForeignKey(AppUserModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")` | never Django `User` |
| `multi_link` | an intermediary model `<Entity><Field>Link(entity FK, target FK)` | no ManyToMany in Zango; report it |
| `file` / `image` | `ZFileField()` | `accept` / `max_size_mb` are form-side (`clean_<field>`) |
| `json` | `JSONField(default=dict, blank=True)` | |

**Required vs optional.** `required: true` and not readonly/auto/computed → no
`null/blank`. Everything else → `null=True, blank=True` (`CharField` too, so an
untouched sequence or computed value is `NULL`, not `""`). Readonly, `auto` and
`computed` fields are **always** `null=True, blank=True`; they are filled by code.

Also: `label` → verbose name (first positional arg); `help` → `help_text`;
`unique: true` → `unique=True`; `default` → `default=` (choice id string, number,
bool). `pattern`, `min`, `max`, `tooltip` are form concerns ([forms](forms.md)).

## Choices

One module-level constant per choice set or inline list, named from the set code or the
field: `VENDOR_TYPE_CHOICES = [("manufacturer", "Manufacturer"), …]`. Choice colours stay
in the spec (badges read `spec.json`), never in the model.

## Links

| Spec `on_delete` | Django |
|---|---|
| `cascade` | `models.CASCADE` (child entities: always) |
| `protect` / absent on a required link | `models.PROTECT` |
| `set_null` / absent on an optional link | `models.SET_NULL` (needs `null=True`) |

- Always the **imported class**, never a string. Links into a later module are not
  allowed by the checker (module cycle); move the entity.
- `related_name="+"`: the runtime only walks links forwards (`child__parent__object_uuid`),
  and `+` avoids reverse-accessor clashes when two fields link to the same model.
- **Self link** (`category.parent: {to: category}`): define the class, then
  `Category.add_to_class("parent", ZForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"))`.

## Phone numbers

`PhoneNumberField` stores E.164. A spec `pattern` like `^[6-9][0-9]{9}$` (10 digits, no
`+91`) is applied to the **form input**; the stored value still parses with the app's
default region. If saving 10-digit numbers fails, set `PHONENUMBER_DEFAULT_REGION` for the
deployment rather than switching to `CharField`, and note it in the report.

## `save()` - always

```python
    def save(self, *args, **kwargs):
        zr.apply_on_save(self, "<entity code>")   # sequences + computed fields from spec.json
        super().save(*args, **kwargs)
```

`zr.apply_on_save` fills `auto.sequence` fields once (`zr.next_sequence`, row-locked
`ZasSequence`, per year when the format has `{YY}`/`{YYYY}`), evaluates arithmetic
`computed` fields (`quantity * unit_price`, `+ - * /`, dotted paths, `None` if any operand
is `None`, money quantised to 0.01), and calls `<entity>__compute__<field>` hooks for
text `computed` fields. A computed field that depends on **other** records (e.g. a PO total
from its lines) also needs the child's save/delete to re-save the parent: do that in the
hook's companion code and say so in `holes.md`.

## Never

- `class Meta:` on a model, `models.Model`, `ManyToManyField`, string FK targets.
- A `status` field: the workflow package owns status ([workflow](workflow.md)). `status`
  and `tags` are reserved names (the checker errors on them).
- Business logic in `save()` beyond `zr.apply_on_save`: hand logic goes in `hooks.py`.

`__str__` returns the spec `display` field (`return self.legal_name or ""`).
