# Map: `roles`, `access`, `app_user` → roles, `policies.json`, scoping, logins

Access has four layers. Only one of them (`policies.json`) is a file you write. The other
three come from `spec.json` at runtime or from `scripts/zango_platform.py`.

| Layer | Spec | Where it lives |
|---|---|---|
| 1. Roles exist | `roles[]` | Zango App Panel (`zango_platform.py roles`) |
| 2. A role can open a CRUD endpoint, and its features | `access.<Role>.actions` | `backend/<module>/policies.json` (+ `sync`) |
| 3. Which rows, which buttons | `access.<Role>.rows`, row-action/transition/tag `roles`, `form.*.roles` | `zas_core` (from `spec.json`) + `roles` in the generated dicts |
| 4. A record owns a login | `entities.<e>.app_user` | `zas_core.app_user` (automatic) |

Package background: `references/zango/core/policies.md`, `references/zango/app-panel-api.md`.

## 1. Roles

Every `roles[].name` becomes a Zango user role with that exact name. Names are
case-sensitive, and the runtime compares names, not ids. `AnonymousUsers` and `SystemUsers`
already exist and are reserved (the checker errors). Create the roles **before** syncing
policies, because a policy that names a missing role is not bound.

```bash
python <skill>/scripts/zango_platform.py roles --workspace <ws>   # idempotent: creates missing roles only
```

## 2. `policies.json`: one per module

Read `entities.<e>.policies` from the resolved spec. The checker has already grouped roles
by identical feature sets and named the policies `<Model>Access<N>` (contracts §5).
Write them as-is:

```json
{"policies": [
  {"name": "VendorAccess1",
   "description": "Vendors for Procurement Executive (add, export).",
   "statement": {"permissions": [
     {"name": "backend.vendors.views.VendorCrudView", "type": "view", "features": ["add", "download"]}]},
   "roles": ["Procurement Executive"]}
]}
```

| Spec action | Policy effect |
|---|---|
| `view` | the role is in some policy for the view (without one it gets a 403 on the endpoint) |
| `add` | feature `add` |
| `export` | feature `download` |
| `edit`, `delete`, `detail` | none (no crud feature). Enforced at runtime (layer 3) |

- Permission `name` = `backend.<module>.views.<Model>CrudView`, the dotted import path from the workspace root.
- **Child entities shown on a 360 tab need a policy too.** A tab calls the child's
  endpoint as the viewer. A role without `view` on the tab entity does not see the tab
  (`ZasDetail` drops it). The checker warns `hidden for <roles>` so this is a decision,
  not an accident. Do not "fix" it in code. Report it, and the spec author adds the role.
- Keep the module's `app.html`/`views.py` policy from `assets/templates/app-module/policies.json`
  in the `app` module. Every role needs it to load the shell.
- After writing: `python <skill>/scripts/zango_platform.py sync --workspace <ws>` (runs
  `ws_sync`/sync_policies). Then read the policies back and compare names and roles.

## 3. Runtime enforcement (nothing to generate)

| Spec | Enforced by |
|---|---|
| `rows: all / created_by_me / {own} / {where} / {text}` (`own` only for the role that `app_user` logs in; `spec_check` errors otherwise, because any other role would see **no rows**: use `where: "<parent>.<user link> == current_user"`) | `access.scope_queryset` on every table request, the detail fetch, row actions and workflow transitions (contracts §4) |
| `rows: {text}` | hook `<entity>__rows__<role slug>(request, qs) -> qs` in `hooks.py`. Without it the role sees **no rows** |
| `actions` lacks `edit` | `ZasTableMixin.zas_can_perform("edit")` hides Edit |
| `actions` lacks `delete` | hides Delete |
| `actions` lacks `detail` | `ZasDetail.get` answers `zas.access = "no_access"` and the 360 shows the no-access state |
| `form.create.roles` | `ZasCrudViewMixin`: Add button hidden, POST refused |
| `form.edit.roles`, `editable_in` | Edit hidden per row |
| transition / tag / row-action `roles` | the `roles` key of the generated dict (engine / crud) |
| `quick_filters[].roles`, column `roles` | metadata filtered per role / `user_roles=` |
| no `access` block on the entity | everyone listed in a policy sees everything (the checker warns) |

Roles in a generated dict and roles in `spec.json` must match. The dicts are written
from the resolved spec, so copy them, never retype them.

## 4. `app_user`: records that own a login

```yaml
app_user: {role: Vendor User, name: legal_name, email: email, mobile: phone, create_on: status == approved}
```

`zas_core.app_user` creates (or reuses, by email/mobile) an `AppUserModel` with that role
and binds it: `app_objects[str(role.id)] = str(record.object_uuid)`. That binding drives
`rows: {own: <path>}` for every entity reachable from the record (`own: id` on the
vendor itself, `own: vendor` on a PO, `own: purchase_order.vendor` on a PO line).

| `create_on` | Fires from |
|---|---|
| `create` (default) | `ZasFormMixin.save` |
| an expression | after every transition and tag change (`ZasWorkflowMixin` done hooks) and on create. Provisioned once the expression is true |

It is idempotent and never raises. A failed login is logged, and the record is kept.
Hooks may call `app_user.provision(obj, "<entity>", request)` and
`app_user.set_active(obj, "<entity>", bool)` (the vendors example: hold → disable,
release → enable). The generated password is never shown. The user sets one on first
login, and test users are made separately (`zango_platform.py users`, [testing](../testing.md)).

## Test users

`zango_platform.py users --workspace <ws>` creates one user per role
(`test.<role slug>@<app code>.test`), with a generated password, and writes
`<ws>/.zas/test_users.json` (chmod 600, never printed, never committed). For an `app_user`
role it also creates one record of the owning entity, so `rows: {own}` has something
to match. The run report lists the emails, never the passwords.

## Checks before moving on

- Every role that a menu shows a page to can `view` that page's entity (checker warning
  "menu page the role cannot access").
- `policies.json` validates as JSON. Every permission `name` imports
  (`python -c "import backend.<module>.views"` inside the container).
- After `sync`, each role in `roles[]` has the expected policies (`zango_platform.py check`).
