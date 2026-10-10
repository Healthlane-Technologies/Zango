# Interviewing for a custom Zango app

Use this only when the user gave a short brief and no documents. With real
material (an SOP, an RFP, a detailed brief) follow `DRAFTING.md` instead and
draft the whole app in one pass.

Read `SCHEMA.md` before your first question and `starter.yaml`, where every
app begins. `example.yaml` (Vendor Hub) is a complete app; look at it when you
are unsure how much detail an answer needs.

The build re-checks the spec with its own checker (`build_check` issues in
`spec_validate`): quote prose values inside `{ }`, use only the listed column
formats, and keep modules from linking to each other in a cycle — see
"Writing YAML the build reads the same way" in `SCHEMA.md`.

## The two rules

**1. The app takes shape on screen as you go.** The user watches a live,
clickable preview of the spec beside the chat: menus, list pages, forms,
statuses and 360 pages with demo data. After every reply, write what you
learned into the spec with the spec tools before you ask anything else:
`spec_outline` to see where things stand, `spec_get` to read a part,
`spec_set` / `spec_add` / `spec_remove` / `spec_move` for small changes and
`spec_replace_section` for a whole section or module. Paths are JSON
Pointers; `@code` picks a list item by its code, name or single key
(`/modules/@core/entities/@record/fields/@notes`). A change that does not fit
is refused with the reason — fix the value instead of retrying it.

Never leave the preview broken: when you add a page, add it to a menu; when a
page lists an entity, declare the entity; when a role appears in access or a
transition, declare the role.

**2. Everything starts answered.** Propose, don't ask open questions. Each
question carries a sensible default pre-selected, taken from the brief or
from how apps like this usually work, so a user who agrees can just send.

## Stages

Three or four questions per turn. Skip a stage when the brief already answers
it. Eight to ten turns is a complete app.

1. **The app.** What it is for and who it serves. Name it (`app.name`,
   `app.code`) yourself; never ask for a code. Locale and currency only if the
   brief hints at a country.
2. **Who uses it.** The roles, and for each: what they mainly do, and whether
   they see every record or only their own (`rows: {own: ...}`,
   `created_by_me`). External users (vendors, customers, field partners) get an
   `app_user` link on the entity that represents them.
3. **What it keeps track of.** The main records (entities) and how they relate:
   which one is the centre (`hero`), which have their own lifecycle
   (`transactional`), which only live under a parent (`child`), and which are
   lookup lists (`master`). Write modules, entities and fields with sensible
   defaults; ask only about fields that change the process (IDs, amounts,
   dates, documents, who it belongs to).
4. **How records move.** For each record with a lifecycle: the statuses, who
   moves it between them, what each step collects, what must be true first
   (`condition`), and what happens after (`on_done`). Ask about approvals and
   maker-checker explicitly. Tags for flags that cut across statuses.
5. **Who can do what.** Fill `access` per role for every entity; confirm the
   non-obvious ones (who can delete, who can export, what external users see).
6. **Screens.** Menus and landing pages per role, list columns, quick filters
   ("Pending my approval"), row actions, and whether the centre record needs a
   360 page (`detail_views`) with related tabs and a timeline. Dashboards and
   anything bespoke become `custom` pages described in `text`.
7. **Rules and the rest.** Validation and duplicate checks, notifications,
   scheduled jobs, integrations, reports — as `validation`, `on_done` and
   `custom_requirements` with specific, testable text.

When the app is complete and `spec_validate` reports no errors, describe how
each role gets its main work done with `spec_set_workflows` (see `DRAFTING.md`
§5), then call `spec_mark_ready` with a one-line summary.
