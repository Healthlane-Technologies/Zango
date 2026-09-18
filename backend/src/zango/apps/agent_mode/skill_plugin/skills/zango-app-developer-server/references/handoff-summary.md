# Hand-off summary — what the final report must contain

Read this at STEP 7, when the build is done and you are writing the summary.
Nothing earlier in the run depends on it.

The platform's run prompt already requires the basics (files, models,
migrations, policies, roles, assumptions, manual steps). This is the Zango
-specific expansion: each line is something a reader cannot verify for
themselves without opening the workspace, and several are claims that have
been reported as done when they were not.

## The checklist

- files created and modified
- models added or changed, and whether migrations will be needed
- policies added, and any roles that must be created by an operator
- packages required but not installed
- roles you defined and the test users you declared
- whether `frontend/` was scaffolded and built, and the exact bundle filename
- whether `/app/` serves **your own bundle** (not appbuilder's) — quote the
  `src` line from `app.html`
- whether routes **and** menu configs were accepted (read back, not POST status)
- which entities got an entity-360 page, and why each remaining model did not
- that every child table is filtered **server-side**, not just by query string
- whether the branded login is live, and which of the three login paths
  (single-role, multi-role, first-login) you verified
- the result of the migration/sync commands you ran
- assumptions you made in place of asking
- remaining manual steps, including any React work you could not do

## Restarts

You cannot restart the app server or Celery. If you changed `models.py`,
`tasks.py` or `settings.json`, **say so** — a restart is needed before the
change takes effect, and only an operator can do it.

## Honesty rules

- A step you could not complete is a **remaining manual step**, named as such.
  Never report a blocked step as done.
- "The POST returned success" is not evidence for routes or menus. Quote the
  read-back.
- If you skipped an entity-360 page for a model that qualified under STEP 3,
  say which model and why — that is a design decision the reader must be able
  to disagree with.
