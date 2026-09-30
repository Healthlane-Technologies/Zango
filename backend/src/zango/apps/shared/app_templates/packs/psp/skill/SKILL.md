---
name: zango-psp-builder
description: Build a Zango app from an approved PSP (Patient Support Program) journey spec. Use when the build prompt names this skill and gives a journey YAML file — configure the PSP template's custom/ modules from the spec, hand-author the parts the vocabulary marks as custom, and verify the program loads. Works alongside zango-app-developer-server, which still owns migrations, sync, policies and the frontend build.
version: 0.2.0
---

# PSP builder

The app you are building is a **Patient Support Program** on the Zelthy PSP template.
The template already ships the engine — workflow, programs, documents, wallet and
schemes, masters, the patient 360 page, tasks, timeline. A program is **configured**,
not developed: most of your work is turning the approved `journey.yaml` into the
template's configuration files under `backend/custom/`.

Use this skill **together with** `zango-app-developer-server`. That skill still owns
the server-mode rules, STEP 7 (migrations and sync), `policies.json`, and the frontend
build. This skill tells you *what* to configure from the spec; the other tells you how
to run and verify it on this platform.

## Inputs

- **The spec file.** The build prompt gives an absolute path to the approved journey,
  e.g. `.../spec/journey.yaml`. Read it **in full** before changing anything. It is the
  only source of truth; the chat that produced it is not available to you.
- **The vocabulary.** `../../requirements/SCHEMA.md` (relative to this file) explains every key.
  If a key's meaning is unclear, read it there — never guess from the name.
- **The workspace.** Your working directory is the app. Confirm it is a PSP template
  workspace before you start (see "First, check the workspace").

## First, check the workspace

The template layout is:

```
backend/
  app/          entrypoint — urls, views, policies.json
  config/       app_config.json loader
  custom/       ← the configuration layer — one folder per module (you edit this)
  template/     ← the engine (you do NOT edit this)
app_config.json manifest · endpoints · page_config
```

The platform installs this layout when an app is created from the template, and
restores `backend/template/` (and `frontend/src/template/`) from the template before
every build, so you always start from the published engine. Never edit those paths:
changes there are overwritten on the next build.

If `backend/template/` or `app_config.json` is missing anyway, **stop**. The app was
not created from the PSP template, and configuring it would mean re-implementing the
engine. Report that plainly as the run's outcome.

## How the spec maps onto the template

Work section by section, in this order — later sections refer to codes declared in
earlier ones. `references/mapping.md` has the key-by-key table.

| journey.yaml | Where it goes | Template names |
|---|---|---|
| `roles` | app roles + `policies.json` + role menus | Zango app roles; `ScopeEntry` for `sees_only: own` |
| `masters` | `custom/masters/` (`models.py`, `forms.py`, `tables.py`, `masters_config.py`) | `Master`, `AbstractMaster`, `BaseMasterForm`, `BaseMasterCrudView` |
| `patient` (attributes, states/steps, create, labels, table) | `custom/patient/` (`patient_config.py`, `models.py`, `forms.py`, `tables.py`, `transition_forms.py`) | `BINDING`, `STATUSES`, `TRANSITIONS`, `TAGS`, `TAG_RULES`, `PATIENT_RULES`; `Status`, `Transition`, `Tag`, `TagRule` |
| `patient.consent`, `programs[].consent` | the template's consent configuration on the patient and program modules | see Open questions |
| `catalogue` | the commerce SKU list used by schemes and orders | see Open questions |
| `documents` | `custom/document/` (`document_config.py`, models/forms/tables) | `ENTITIES`, `DOCUMENT_TYPES`; `DocumentType`, `AbstractDocument` |
| `programs` (identity, eligibility, enrolment, document_rules) | `custom/programs/programs_config.py` + enrolment models/forms/tables | `PROGRAM_TYPES`, `PROGRAMS`; `Program`, `AbstractEnrolment` |
| `programs[].schemes` | `custom/programs/schemes_config.py` | `SCHEMES`; `Scheme`, `Accrual`, `Equivalence` |
| `programs[].orders` | order types on the program + order models/forms/tables | `OrderType(redeems=/accrues)`, `AbstractOrder` |
| `detail` | `custom/patient/detail.py` | `Feature(...)` per entry in `features`; custom tabs are hand-authored |
| `extra_modules` | a new `custom/<code>/` module each, hand-authored | ordinary Zango module (models, CRUD view, policies) |
| `adverse_events`, `reports` | hand-authored against the template's patient/enrolment models | see Open questions |
| every `custom_actions` | a named `@custom_action` function in that module | hand-authored from the English text |
| every `custom_requirements` | the layer named by `area` in that module | hand-authored; list each one in your summary |

Then register every configuration module in `app_config.json` → `manifest`
(`PATIENT_CONFIG`, `PROGRAMS_CONFIG`, `SCHEMES_CONFIG`, `DOCUMENT_CONFIG`,
`MASTERS_CONFIG`, `ACTIVITY_CONFIG`) and add screens under `endpoints` and
`page_config` only where the defaults are not enough.

### Translating the shared shapes

- **States → `Status`.** `- pending: { start: true }` becomes
  `Status("pending", "Pending", on_create=True)`. Labels are the code in words.
- **Steps → `Transition`.** `{ do: Approve, from: a, to: b, by: [Manager] }` becomes
  `Transition("a", "b", label="Approve", user_roles=["Manager"])`.
  `automatic: true` → `manual=False`. `collects:` → a transition form in
  `transition_forms.py` passed as `form=`.
- **`then:` / `on_*:` → `actions=[...]`.** Each vocabulary action maps to the template
  helper of the same name, e.g. `add_timeline_entry: "Enrolled"` →
  `add_timeline_entry("Enrolled")`. Never invent a helper: an action that is not in
  the vocabulary is a `custom_actions:` entry.
- **Gates → `when(...)`.** `all:` → `all_of(...)`, `any:` → `any_of(...)`;
  `age >= 18` → `field("age") >= 18`; `x is_true` → `field("x").is_true()`. Carry every
  `explain:` message into the gate, since that is what the user is shown when blocked.
- **Fields.** `type: link, multiple: true` is a many-to-many. Zango has no
  ManyToManyField, so create a mapping model. `choice` options become field choices.
  Validation keys (`max_length`, `unique`, `pattern`, …) become model/form validation.
- **`table:`** becomes the module's table class (columns in spec order; `searchable`,
  `sortable`, `search_choices`, `shows_from`), `policies.json` view access per role
  (`can:`/`no_access:`), `can_do:` row actions, and `owned_by:` as the table's
  `get_table_data_queryset()` filter for that role.

## Rules

- **Do not edit `backend/template/`.** It is shared, centrally maintained engine code.
  If the spec needs something the engine cannot do, it belongs in `custom/` as
  hand-authored code. If you hit that case, say so in the summary.
- **Do not add behaviour the spec does not ask for**, and do not drop anything it
  does. Every key in the spec must be accounted for in your summary: configured,
  hand-authored, or impossible with the reason.
- **Keep codes exactly as written.** Status, program, master and document codes are
  stored data and referenced across modules; renaming one breaks the others.
- **Reserved masters and documents** marked `enabled: false` are kept but switched
  off, not deleted.
- **Consent and adverse events are not optional plumbing.** Data-processing consent
  blocks patient creation until granted, and AE capture runs regardless of
  communication consent. Do not weaken either to make something simpler.

## Verify

1. The configuration loads. The template validates each block and then the whole
   program at load time. A typo or an undeclared status is a load error, so run the
   app's checks (STEP 7 of `zango-app-developer-server`) and fix everything reported.
2. Migrations and sync succeed (STEP 7).
3. Walk the spec once more and tick every section and every `custom_*` entry against
   what you built.
4. In the run summary, list:
   - what was configured, per section;
   - every hand-authored piece (`custom_actions`, `custom_requirements`, extra modules);
   - anything you could not do, with the reason.

## Open questions

These are not settled in the material available to this skill. Handle them
conservatively and report what you did:

- **Consent, catalogue, adverse events and reports.** The template docs cover patient,
  programs, schemes, documents, masters, activity and detail views, but they do not
  document spec models for these four. Look in `backend/template/` for existing
  support first. If there is none, hand-author them in `custom/` and flag each one in
  the summary.
- **Role menus** (`roles.*.menu`). Match them to the template's pages
  (`/app/patients`, `/app/programs`, `/app/benefits`, `/app/masters`). Keep the default
  sidebar for any role without a menu.
