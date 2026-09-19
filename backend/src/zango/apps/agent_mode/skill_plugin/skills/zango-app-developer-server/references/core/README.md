# Core framework references

Backend fundamentals: modules, models, policies, async tasks and secrets.

Read the file for the thing you are building, at the moment you build it. Each
is self-contained — you do not need the others unless you are writing that
thing too.

| Building | Read | Covers |
|---|---|---|
| A new module | `modules.md` | Folder structure, creating a module, registering it in `settings.json`, import rules |
| A model | `models.md` | `DynamicModelBase`, auto-inherited fields, Zango field types, relationships, constraints |
| Access control | `policies.md` | `policies.json`, view access policies, per-role permissions, registration |
| A background job | `async-tasks.md` | Creating, triggering, scheduling and syncing async tasks |
| An encrypted field or credential | `secrets.md` | When to use secrets, key naming, reading them in code |

A CRUD view needs `modules.md` and `models.md` from here, then the `crud`
package references — see the reference index in SKILL.md STEP 3.
