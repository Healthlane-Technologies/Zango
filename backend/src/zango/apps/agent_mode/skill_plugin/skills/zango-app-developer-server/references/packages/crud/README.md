# CRUD package references

`BaseCrudView`, forms and tables — the backend half of a CRUD interface.

A standard CRUD view needs the three `core.md` files below and nothing else.
Read the rest only when a core file does not answer your question.

| Writing | Read | Covers |
|---|---|---|
| The view class | `views/core.md` | `BaseCrudView`, actions, permissions, wiring |
| The form | `forms/core.md` | `BaseForm`, fields, validation, `FormRenderer` |
| The table | `tables/core.md` | Columns, types, pagination, search, sorting |
| Orientation, if CRUD is unfamiliar | `overview.md` | How view + form + table fit together |
| A detail view on a CRUD model | `detail.md` | Detail configuration and layout |

Reach for these **only when a core file does not answer it**:

| Problem | Read |
|---|---|
| Need a method signature or a worked example | `views/reference.md` |
| A view behaves unexpectedly | `views/troubleshooting.md` |
| Custom column rendering, row actions, bulk actions | `tables/advanced.md` |
| Unusual field types, nested or dynamic forms | `forms/examples.md` |

Custom React pages that consume these APIs are a different topic — see the
frontend references.
