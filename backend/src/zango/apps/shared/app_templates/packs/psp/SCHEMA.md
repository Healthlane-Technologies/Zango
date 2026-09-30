# journey.yaml — the PSP requirement spec

This is the **only** output of a PSP interview. It is the same file the Journey
Studio exports, so anything written here is something the template can be
configured to do.

Read this before you write a spec. Do **not** invent keys: a key that is not in
this file cannot be honoured, and the right home for anything the vocabulary
cannot express is a `custom_requirements:` note (see the end).

Top-level keys, in this order:

```
journey:          # required — a short code, e.g. enhertu_pap
name:             # the program's name in words
roles:            # required
masters:          # reference lists
patient:          # required
catalogue:        # products that can be dispensed
documents:
programs:         # required — at least one
detail:           # what the patient 360 page shows
extra_modules:    # capabilities outside the template vocabulary
adverse_events:
reports:
```

---

## Shared shapes

These recur everywhere. Learn them once.

### A field

```yaml
- mobile: { type: phone, required: true }
- gender: { type: choice, options: [female, male, other] }
- city: { type: link, to: city }
- hospital: { type: link, to: hospital, multiple: true }
```

`type` is one of `text`, `phone`, `email`, `number`, `date`, `choice`,
`boolean`, `link`. Document fields may also be `file`.

`link` points at a **master** by its code. `multiple: true` on a link means a
many-to-many, which the generator turns into a mapping record — there is no
ManyToManyField in Zango, so a many-to-many always becomes its own record.

### A lifecycle — `states:` and `steps:`

Any record that moves through stages carries these two keys.

```yaml
states:
  - pending: { start: true }
  - active
  - suspended
  - closed: { final: true }
steps:
  - { do: Activate, from: pending, to: active, by: Executive, then: [add_timeline_entry: "Enrolment activated"] }
  - { do: Suspend, from: active, to: suspended, by: [Manager], then: [cascade_suspend_dependents] }
  - do: Close
    from: active
    to: closed
    by: Manager
    allowed_when:
      all:
        - documents_verified is_true
      explain:
        documents_verified: "Verify the documents before closing."
    collects:
      - closure_reason: { type: text, required: true }
```

- Exactly one state carries `start: true`. A `final: true` state is a resting
  end state.
- `by:` is a single role or a list. Omit it only when `automatic: true`.
- `then:` is a list of **actions** (below).
- `collects:` is a form the user fills while taking the step.
- `allowed_when:` is a **gate** (below).

### Actions — `then:`, `on_create:`, `on_enrol:`, `on_raise:`

Only these exist. Anything else is a `custom_actions:` entry.

| action | what it does |
|---|---|
| `set_status` | set this record's status |
| `set_record_status` | set another named record's status |
| `set_enrolment_status` | set the enrolment's status |
| `set_sibling_enrolments_status` | set the patient's other enrolments |
| `set_child_documents_status` | set documents under this record |
| `set_child_orders_status` | set orders under this record |
| `set_sibling_document_status` | set other documents of the same parent |
| `cascade_suspend_dependents` | suspend everything hanging off this record |
| `apply_scheme` | run the program's accrual scheme |
| `accrue_to_wallet` | add credits |
| `redeem_from_wallet` | spend credits |
| `reverse_credits` | undo a wallet movement |
| `persist_order_lines` | commit the order's lines |
| `add_tag` / `remove_tag` | apply or clear a patient label |
| `create_task` | raise a task |
| `add_timeline_entry` | write to the patient timeline |
| `reject_save` | block the save |

Write an action bare, or with a value: `[add_timeline_entry: "Patient activated", create_task: "Call the patient"]`.

### Gates — `allowed_when:`, `eligible_when:`, `on_upload:`, `on_edit:`

```yaml
eligible_when:
  all:                      # or: any
    - her2_status == her2_positive
    - age >= 18
    - consent_signed is_true
  explain:
    prefix: "This patient cannot be enrolled:"
    her2_status: "Only HER2-positive patients qualify."
```

Operators: `==` `!=` `>=` `>` `<=` `<` `in` `contains` `is_true` `is_false`.
`explain:` is what the user is shown when the gate blocks them — always give
one for any condition a user could reasonably trip.

### Duplicate checks — `duplicate_check:`

```yaml
duplicate_check:
  scope:
    status_in: [new, active]
    with_labels: [consent_signed]
    without_labels: [lead_dropped]
    - registered_at >= 2024-01-01
  rules:
    - match: [mobile]
      compare: normalised          # exact | normalised | fuzzy
      on_match: block              # block | warn
      message: "A patient with this mobile number already exists."
    - compare: custom
      text: "Same name and same date of birth at the same hospital."
      on_match: warn
```

### A list screen — `table:`

Every record that has a list screen may carry one.

```yaml
table:
  access:
    - Executive: { can: [add, edit, download] }
    - Distributor: { no_access: true }
  columns:
    - name: { searchable: true, sortable: true }
    - status: { search_choices: [new, active, inactive] }
    - city: { shows_from: name }
    - doctor_name: { as: custom, label: Doctor, shows: "the doctor on the latest prescription" }
    - mobile: { roles: [Manager], in_export: false }
  sort: -created_at
  can_do:
    - { do: Call, key: call, kind: confirm, by: Executive, then: [create_task: "Call the patient"] }
    - do: Record outcome
      key: outcome
      kind: form
      by: Executive
      collects:
        - outcome: { type: choice, options: [reached, no answer, wrong number], required: true }
  owned_by:
    - Distributor: { field: distributor }
  row_scope:
    - Executive: "only patients in their own city"
```

- `access:` is per role. A role that may see the list but not add is
  `{ can: [] }`; a role that must not see it at all is `{ no_access: true }` —
  say it explicitly, silence is not a denial.
- Column order here is the column order on screen.
- `as: custom` + `shows:` is a computed column described in plain English.
- `owned_by:` is "sees only their own rows", by the field that points at them.

### Plain-English escapes

Two, and they are different:

```yaml
custom_actions:            # extra behaviour at a point the template already has
  - name: notify_doctor
    text: "Email the prescribing doctor when the enrolment is approved."

custom_requirements:       # a requirement the vocabulary cannot express at all
  - area: frontend         # backend | api | frontend | form | report | integration | permission | notification
    title: "Dose calculator"
    text: "On the order form, work out vials needed from the patient's weight."
```

Both may hang off any record, table, program, order, consent, AE or report.

---

## `roles:`

```yaml
roles:
  Manager: {}
  Executive: {}
  Distributor:
    sees_only: own
    scope_field: distributor
```

`sees_only: own` scopes every screen to the rows that point at that user, via
`scope_field` on the record. The home page is derived per role — it is never
configured.

## `masters:`

Reference lists. `city`, `indication`, `doctor`, `hospital`, `distributor` and
`pharmacy` are **suggested in every journey** and marked `reserved: true`; keep
the ones the program uses, and mark the rest `enabled: false` rather than
deleting them, so the decision is on the record.

```yaml
masters:
  - code: doctor
    name: Doctor
    plural: Doctors
    reserved: true
    create_by: [Manager]
    fields:
      - registration_no: { type: text }
      - specialty: { type: choice, options: [oncology, haematology] }
      - hospital: { type: link, to: hospital, multiple: true }
  - code: pharmacy
    reserved: true
    enabled: false
  - code: distributor
    reserved: true
    app_user_role: Distributor
    app_user_contact: { mobile: phone, email: email }
```

`app_user_role:` turns the master's rows into signed-in users of that role —
that is how a distributor or a doctor logs in and sees only their own patients.
A master may also carry `states:`/`steps:` and a `duplicate_check:`.

## `patient:`

```yaml
patient:
  attributes:
    - name: { type: text, required: true }
    - mobile: { type: phone, required: true }
    - city: { type: link, to: city }
  states: ...
  steps: ...
  create:
    by: [Executive]
    form:
      - name: { required: true }
      - mobile: { required: true }
    duplicate_check: ...
    on_create: [add_timeline_entry: "Patient registered"]
  labels:
    - consent_signed
    - ild_risk_flagged:
        apply:
          by: [Manager]
          then: [create_task: "Review ILD risk", add_timeline_entry: "ILD risk flagged"]
          collects:
            - ild_note: { type: text, required: true }
        remove:
          by: [Manager]
  table: ...
  consent: ...
```

**Labels** are the patient flags a team applies and removes by hand —
"Consent Signed", "Lead Dropped", "ILD Risk". Each side can require a form and
fire actions. They are not the lifecycle; a patient has one status and any
number of labels.

### `patient.consent:`

Every PSP has data-processing consent, most have communication consent, and
programs may carry their own. The lifecycle is fixed —
`pending → granted → withdrawn` — and data consent always blocks patient
creation until granted. What varies is the wording, the version, who may record
or withdraw it, and what withdrawal does.

```yaml
  consent:
    show_on_patient_360: true
    data_processing:
      version: "1.0"
      notice: "I agree to my personal and health data being processed ..."
      record_by: [Executive]
      withdraw_by: [Executive, Manager]
      evidence_document: patient_consent
      on_withdraw: { patient_status: inactive, stop_all_communication: true, open_archival_task: true }
    communication:
      version: "1.0"
      notice: "..."
      record_by: [Executive]
      withdraw_by: [Executive, Manager]
      channels: [sms, whatsapp, email, voice, in_app, post]
    program:
      version: "1.0"
      notice: "..."
      record_by: [Executive]
      withdraw_by: [Manager]
    register_open_to: [Manager]
```

## `catalogue:`

```yaml
catalogue:
  skus:
    - ENH100: { label: "Enhertu 100mg vial", cold_chain: true }
```

## `documents:`

```yaml
documents:
  attaches_to: program_enrolment  # or patient
  select: latest_active           # or latest
  states: ...
  steps: ...
  types:
    - prescription:
        reserved: true
        kind: prescription
        fields:
          - indication: { type: link, to: indication, required: true }
          - doctor: { type: link, to: doctor, required: true }
          - prescription_date: { type: date, required: true }
    - income_proof
    - hcp_recommendation:
        linked_documents: [prescription]
```

A prescription type is seeded in every journey. Every document already carries
its file, original name, type and parent — never re-declare those.

## `programs:`

One entry per program a patient can be enrolled onto. Most journeys have one.

```yaml
programs:
  - code: pap
    name: Patient Assistance Program
    eligible_when: ...
    attributes:
      - annual_income: { type: number }
    schemes:
      - code: bxgy
        name: Buy 3 get 2
        accrual: { buy: 3, get: 2 }
        equivalences:
          - { sku: ENH100, factor: 1, base_sku: ENH100 }
    on_enrol: [add_timeline_entry: "Enrolled"]
    requires_documents: [prescription, income_proof]
    document_rules:
      - document: prescription
        on_upload:
          all:
            - prescription_date >= enrolment_date
          explain:
            prescription_date: "The prescription must not pre-date the enrolment."
        duplicate_check: ...
    enrolment:
      states: ...
      steps: ...
      table: ...
    consent:
      use: blanket                 # or its own version/notice/record_by/withdraw_by
      required_before: active
      on_withdraw: { enrolment_status: suspended, cascade_suspend_dependents: true, open_archival_task: true }
    orders:
      - code: free_dispense
        name: Free dispense
        spends_credit: true
        allowed_skus: [ENH100]
        lines_at: create           # or { step: Approve }
        assigned_by: { role: Distributor, field: distributor }
        collects:
          - requested_units: { type: number, required: true }
        allowed_when: ...
        on_raise: [redeem_from_wallet]
        states: ...
        steps: ...
        table: ...
```

- `earns_credit: true` / `spends_credit: true` connect an order type to the
  wallet — a paid order accrues, a free dispense redeems.
- `lines_at:` says when the products on the order are chosen: at creation, or at
  a named later step (once approved, say).
- `assigned_by:` routes each order to the scoped role that must act on it.

## `detail:` — the patient 360 page

```yaml
detail:
  features: [enrolments, documents, orders, wallet, timeline, tasks, notes]
  custom_tabs:
    - code: clinical
      label: Clinical
      text: "HER2 status, ECOG and the dose history, newest first."
```

`features` is drawn from exactly that list. Anything else is a custom tab
described in plain English.

## `extra_modules:`

A whole capability the template does not have. Each becomes a new hand-authored
module, so keep them few and say plainly what they are for.

```yaml
extra_modules:
  - code: nurse_visits
    name: Nurse visits
    purpose: "Schedule and record home nursing visits for patients on therapy."
    attaches_to: patient          # patient | enrolment | order | standalone
    ui: patient_tab               # own_page | patient_tab | both | backend_only
    entities:
      - name: visit
        fields:
          - visit_date: { type: date, required: true }
          - nurse: { type: link, to: nurse }
```

## `adverse_events:`

```yaml
adverse_events:
  intake: in_system               # or client_portal
  attaches_to: patient
  report_by: [Executive, Manager]
  patient_self_report: true
  show_on_patient_360: true
  serious_sla_hours: 24
  processing_basis: legal_obligation
  attributes:
    - description: { type: text, required: true }
  states: ...
  steps: ...
  notify_client:
    on: serious                   # or all
    to: [pv@client.com]
    attach_record: true
  table: ...
```

`awareness_date` and `serious` are built in — never declare them. AE capture
runs regardless of communication consent.

## `reports:`

```yaml
reports:
  items:
    - code: enrolment_summary
      label: Enrolment summary
      purpose: "How many patients enrolled, by month and by city."
      category: program           # program | supply | field | governance
      kind: aggregate             # listing | aggregate | audit
      audience: client            # internal | client | regulator | auditor
      primary: enrolment
      joins:
        - { to: patient, on: patient = patient.id, type: left, cardinality: many_to_one, origin: journey }
      columns:
        - { source: patient, field: city, label: City }
        - { source: enrolment, field: id, aggregate: count, label: Patients }
      group_by: [patient.city, enrolment.created_at by month]
      filters:
        - { source: enrolment, field: status, op: "==", value: active }
      parameters:
        - { name: period, type: date_range, required: true }
      privacy:
        exclude_withdrawn_consent: true
        small_cell_suppression: below 5
      access:
        run_by: [Manager]
        schedule: monthly         # on_demand | daily | weekly | monthly | month_close
        delivery: [in_app, xlsx]  # in_app | csv | xlsx | pdf | email
        link_expiry_days: 7
      layout: { sort: city asc, totals: true }
```

Role scope always applies, exports are always logged, and a client report always
excludes patients whose data consent is withdrawn — those are not knobs.
