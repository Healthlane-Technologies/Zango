# Frontend references

Custom React pages: the visual bar, the shared primitives, and the patterns
for each page type.

These are the largest references in the skill. Read each one at the sub-step
that needs it (STEP 5), not while planning.

| Writing | Read | STEP |
|---|---|---|
| Scaffolding, routes, `App.tsx` wiring | `appbuilder.md` | 5a |
| The shared primitive set, before any page | `shared-primitives.md` | 5c |
| Any custom page — the visual bar | `design-system.md` | 5b/5d |
| A detail page with child tables | `entity-360.md` | 5d |
| A page that lists or edits CRUD data | `crud/` | 5d |
| A form | `form.md` | 5d |
| A page driven by workflow status | `workflow.md` | 5d |
| The branded login page | `auth-login.md` | 5e |
| The end-of-frontend check | `verify-gate.md` | 5f |

`crud/` is a directory: `core.md` always (imports, API shapes, `CrudHandler`),
then `tables.md`, `detail.md` or `hooks.md` only as needed.

`design-system.md` is required for every custom page — it is the bar those
pages are held to, not optional background.
