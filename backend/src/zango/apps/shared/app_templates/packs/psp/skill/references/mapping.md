# journey.yaml → PSP template, key by key

Rows marked *hand-authored* have no template construct. Write them as ordinary Zango
code in the module named, and list them in the run summary.

## roles
| key | becomes |
|---|---|
| `<Role>: {}` | an app role of that name |
| `sees_only: own` + `scope_field: f` | per-role row scoping via field `f` on every scoped record (`ScopeEntry`); each table's `owned_by` filter |
| `menu[]` | that role's sidebar entries (type → template page) |

## masters[]
| key | becomes |
|---|---|
| `code`, `name`, `plural` | `Master(code, name, crud_url="/masters/<code>/")` + a concrete model/form/table |
| `reserved`, `enabled: false` | keep the master, switched off |
| `fields` | model fields (see "fields" below) |
| `create_by` | who may add rows (`policies.json` + table access) |
| `app_user_role`, `app_user_contact` | rows become signed-in users of that role, using the named contact fields |
| `states`/`steps`, `duplicate_check`, `table` | as for the patient |

## patient
| key | becomes |
|---|---|
| `attributes` | fields on the concrete patient model (subclass `AbstractPatientModel`) |
| `states` / `steps` | `STATUSES` / `TRANSITIONS` in `patient_config.py` |
| `create.by` / `create.form` | create permission and `BasePatientModelForm` field list |
| `create.duplicate_check` | the patient's duplicate rules (`PATIENT_RULES`) |
| `create.on_create` | actions on the start status |
| `labels` | `TAGS`; `apply`/`remove` sides → `TAG_RULES` with their forms and actions |
| `table` | `BasePatientModelTable` subclass + `policies.json` |
| `consent` | template consent configuration (see SKILL.md, Open questions) |

## documents
| key | becomes |
|---|---|
| `attaches_to`, `select` | `ENTITIES` / the document entity; `select` decides which document counts |
| `states` / `steps` | the shared document lifecycle |
| `types[]` | `DocumentType(code, label, entity=...)`; `kind: prescription` keeps the authored prescription columns; `linked_documents` → cascades |

## programs[]
| key | becomes |
|---|---|
| `code`, `name` | `Program(code, name, type=...)` in `PROGRAMS` (+ `PROGRAM_TYPES`) |
| `eligible_when` | the program's create gate `when(...)` with its explain messages |
| `attributes` | fields on the concrete enrolment model (`AbstractEnrolment`) |
| `requires_documents`, `document_rules` | required document types; per-document `create_gate`/edit gates guarded by the program code |
| `enrolment.states` / `steps` / `table` | the program's `statuses`, `transitions` and enrolment table |
| `on_enrol` | actions on enrolment creation |
| `schemes[]` | `Scheme(code, name, program=<code>, accrual=Accrual(buy, get), equivalences=[Equivalence(...)])` in `SCHEMES` |
| `orders[]` | `OrderType(code, name, accrues=earns_credit, redeems=spends_credit, statuses, transitions)` + a concrete order model (`AbstractOrder`) |
| `orders[].lines_at` | when order lines are chosen: at creation, or at the named step |
| `orders[].assigned_by` | per-user scoping of orders to the role and field given |

## detail
| key | becomes |
|---|---|
| `features` | one `Feature(...)` per entry in `custom/patient/detail.py` |
| `custom_tabs` | *hand-authored* tab from the `text` description |

## fields (everywhere)
| spec | model |
|---|---|
| `text`, `long_text`, `phone`, `email`, `url` | char/text fields with the matching validation |
| `number`, `decimal` | integer / decimal fields; `min_value`, `max_value`, `decimal_places`, `multiple_of` |
| `date`, `datetime`, `boolean`, `file` | the matching field |
| `choice`, `multi_choice` | choices from `options`/`choices` |
| `link` → `to: <master>` | a foreign key to that master; `multiple: true` → a mapping model (no M2M) |

## escapes
| key | becomes |
|---|---|
| `custom_actions[]` | *hand-authored* `@custom_action` named `name`, doing what `text` says, wired at that point |
| `custom_requirements[]` | *hand-authored* in the layer named by `area` |
| `extra_modules[]` | *hand-authored* `custom/<code>/` module: models from `entities`, UI per `ui`, attached per `attaches_to` |
