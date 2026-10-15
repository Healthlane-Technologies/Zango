# Workflow package references

Status-based lifecycle management: statuses, transitions, tags and the
utilities that query them.

Read the file for what you are writing, when you write it.

| Writing | Read | Covers |
|---|---|---|
| Any workflow at all — start here | `overview.md` | What workflows are, architecture, `workflow.py` shape |
| Status definitions | `statuses.md` | Status list, colors, initial status |
| Transitions between statuses | `transitions.md` | Simple and form-based transitions, role permissions |
| Secondary classification | `tags.md` | Tag definitions, tag transitions, management |
| Querying by status or tag | `utils.md` | Filtering helpers |
| Conditions, done methods, system transitions | `advanced.md` | Conditional transitions, post-transition logic, complete examples |

`overview.md` plus `statuses.md` and `transitions.md` cover an ordinary
lifecycle. Read `tags.md`, `utils.md` or `advanced.md` only when the app
actually needs what they describe.
