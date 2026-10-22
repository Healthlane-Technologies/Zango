# Testing: the spec is the oracle

Every check is generated from `.zas/spec.resolved.json` and names the spec path it proves. Nobody
approves a screen. A check passes or fails against the spec, the skill's rules, or the goldens that
ship with the skill. All layers run headless.

## Setup (once per machine)

```bash
pip install requests pyyaml playwright pillow
python3 -m playwright install chromium
cd <skill>/scripts          # run every zas_test module from here
```

Test users come from `zango_platform.py users` (Phase 5): one per role, written to
`<ws>/.zas/test_users.json` (chmod 600) with the app URL as `target`. On first login a user may have
to set a password. `zas_test.auth` does that and saves the new one before sending it. **Never retry
logins with guessed passwords**: repeated failures lock login from this machine for every account.

## Layer 1: API (`python3 -m zas_test.api --workspace <ws>`)

Runs as each role's test user, through the same endpoints the React app calls:

| Group | Proves | Endpoint |
|---|---|---|
| `access` | viewers can open each list, others are refused; Add is refused without `add` | `GET <ep>?action=get_table_metadata`, `POST <ep>?form_type=create_form` |
| `create` | a creator creates each entity from the live form schema; sequences fill; `require` rules and exact `block` duplicates refuse | `GET <ep>?action=initialize_form`, `POST <ep>?form_type=create_form` (multipart) |
| `transitions` | each engine transition moves its `from` to `to` for an allowed role; a viewer outside `roles` is refused | `POST <ep>?view=workflow&action=process_transition&transition_type=status&transition_name=<engine name>&object_uuid=` |
| `tags` | each tag side works for its roles; sides the spec omits and system tags can't be set by anyone | same, `transition_type=tag&transition_state=enabled\|disabled` |
| `row_actions` | each action is in the row menu only for allowed roles and runs (never "not implemented"); downloads return a `url` | `GET <ep>?view=table&action=get_table_data` (`row_actions` per row), `POST <ep>?action_type=row&action_key=&object_uuid=` (+ `form_type=row_action_form`) |
| `scoping` | `rows: {where: status …}` lists exactly the right records; `rows: {own: id}` lists only the bound record, and another record's 360 is `not_found` | table data + `?view=detail&action=fetch_item_details` |
| `detail` | 360 viewers get `zas.access = ok` with numeric stats, others `no_access`; each related tab adds a child through `?<parent param>=` and lists it under that parent only; timelines answer | `?view=detail&action=fetch_item_details\|zas_timeline`, child `<ep>?view=table&action=get_table_data&<param>=<uuid>` |

`--dry-run` lists the planned checks without touching the app. `--only transitions,tags` and
`--role "Finance"` narrow a re-run. Records the tests create are kept (prefixed values like
`Test Legal Name ab12cd`) and listed in `.zas/test_records.json` for the UI layer.

**How records get into the right state.** The runner walks the shortest path of manual transitions
from the initial status, using an allowed role for each step. When a condition needs data the
generator can't invent (a verified GST document, a PAN that matches the GSTIN), the check is
**skipped with the step that blocked it**. Then write `<ws>/.zas/test_fixtures.py`:

```python
def values(ctx, entity, role):
    """Extra/override create values."""
    if entity == "vendor":
        gst = "27ABCDE1234F1Z5"
        return {"gstin": gst, "pan": gst[2:12]}

def before_transition(ctx, entity, name, uuid, role):
    """Prepare data a transition's condition needs."""
    if entity == "vendor" and name == "submit":
        doc = ctx.create("vendor_document", values={"doc_type": "gst_certificate"}, params={"vendor_uuid": uuid})
        ctx.run("vendor_document", doc, "verify")
```

`ctx.create(entity, role=None, values=None, params=None) -> uuid`, `ctx.run(entity, uuid, transition, role=None) -> (ok, msg)`,
`ctx.record(entity, uuid, role=None) -> row`, `ctx.session(role)`. Fixtures are test data, never product logic.

## Layer 2: UI (`python3 -m zas_test.ui --workspace <ws>`)

Python Playwright, headless Chromium, one browser context per role (logged in by cookie, not by typing):

| Group | Proves |
|---|---|
| `login` | `/app/` shows the branded login (`data-zas="login"`), so the app serves its own build |
| `pages` | every page in each role's menu renders (`[data-zas="page"][data-zas-key=<code>]`) with no console errors or 5xx; Add shown iff the role can add; quick-filter chips equal the spec's for that role; every menu label and group is on screen |
| `detail` | for each 360 and role: viewers get the header and exactly the tabs the role may see, in spec order; each tab opens without errors or "not implemented"; non-viewers get the no-access state |
| `flows` | the journeys end to end ([`zas_test/flows.py`](../scripts/zas_test/flows.py)): per entity, the first role that may create it fills the create form through its real widgets and submits; the record is walked along the longest chain of manual moves from the 360 header, and every other manual move runs on a record the API walks to its from-status; each 360 tab whose child the role may add gets one child. After every step it checks the screen (dialog closed, status badge, no browser errors) and the backend (record saved with the typed values, status is `to`, a timeline event written) |

Screenshots of every page, 360 and tab, per role, land in `.zas/screens/<role>/`; a failed flow step
lands in `.zas/screens/flows/`.

`flows` fills forms with the same values the API layer posts and runs the same
`.zas/test_fixtures.py` hooks (`values`, `transition_values`, `before_transition`, `record_for`), so a
fixture written for the API layer already covers it. The API layer stays: it proves what a browser
cannot, that the server refuses a role the UI merely hides a button from (`access`, `transitions`,
`scoping`). Read the two together: when a flow step fails it repeats the step over the API with the same
values and says which side broke.

## Layer 3: design (`python3 -m zas_test.design --workspace <ws>`)

| Check | Reference | Blocking |
|---|---|---|
| `lint` | rules in [design-system](design-system.md): no colour literals, colour/font inline styles, stylesheets, foreign UI imports or placeholder copy in `src/custom` | yes |
| `tokens` | computed styles on `/app/__zas` vs `tokens.css`: primary button, nine tones, Inter, card shape, the app brand on `--brand` | yes |
| `tree` | per 360 × viewer: facts in spec order, stats ordered, status badge tone = the spec's colour, sidebar rail iff the layout has one | yes |
| `gallery` | `/app/__zas` sections vs `<skill>/assets/goldens/*.png` (≤1% pixels differ; the gallery pins en-US/USD, UTC and a fixed clock) | no: skipped with a reason on another OS/Chromium build |
| `layout` | menu pages and 360s at 1440 and 1280 px: no sideways scroll, no clipped titles, facts, stats or tabs | no (reported) |
| preview parity | each custom screen's approved kit tree (`.zas/bundle/`) | `design --only parity`: blocks, titles, KPI labels and table columns per approved role, in order, plus each block's look (gradient, coloured fill, chart, avatars, accent borders; hand-drawn blocks paired by their words) (`kit_tree.js` on both sides, values never compared). Reported, not blocking: failures go to the fix rounds first. Also the bundle's standard screens: each list page with views, per view (the switcher in the toolbar or above the page, and that view showing), and the app shell (`data-zas="shell-brand"`, `"shell-user"`, `"shell-top"` where the approved shell has them). Writes `.zas/screens/parity/` and `.zas/parity_looks.json` for the look rounds (up to `AGENT_MODE_STUDIO_LOOK_ROUNDS`, re-shot after each change) |

After the machine checks, **look at the screenshots yourself** (`.zas/screens/`): open each
role's main pages and 360s and compare them with the rubric: alignment, spacing, hierarchy,
truncation, contrast, finished look. Fix high-severity findings in the spec mapping or slots (never with
colour hacks), re-run, at most two rounds. Report the rest in the build report. This review never waits
for a person.

## Spec intent review (`spec_check.py`, before any code)

The generated layers prove the app does what the spec **says**. They pass on a spec that says the
wrong thing (a CRA scoped to "own site" saw no documents and every test agreed). `spec_check` therefore
cross-checks access, workflow, forms, tables and 360s and reports `intent` findings: a role that can run
a transition but sees no records, Add/Edit roles without the access action, a 360 viewer without
`detail`, a child listed wider than its scoped parent, a role that adds records its own `rows` hide.
`own` rows for a role that no `app_user` login binds are an **error** (that role would see nothing).
Intent findings don't stop the build. Claude reads each one: if the spec is clearly self-contradictory,
say so in the final message with the suggested fix; never change the spec's meaning silently.

## Fixtures (`.zas/test_fixtures.py`, written by Claude)

`spec_check` writes `.zas/test_plan.md`. Its **Fixture needs** list is everything the generated tests
cannot invent: conditions to make true before a transition, form values a later condition reads, rows
rules that need the record linked to the test user, the record a bound login must own. Start from
`assets/templates/tests/test_fixtures.py.tmpl` and implement each item (`values`, `transition_values`,
`before_transition`, `record_for`). Re-run `zas_test.api`: a `Skip … Add a before_transition fixture`
names the next one to write.

Two rules from live builds: give the app_user login **one** dedicated record (a hook such as
"close-out disables the login" would otherwise lock the test user out mid-run), and never bind it by
editing the database: walk the record through the spec's `create_on` like a user would.

## Layer 4: scenarios (`python3 -m zas_test.scenarios --workspace <ws>`)

One behaviour test per plain-language item, written by Claude from **Scenarios to write** in
`test_plan.md`, in `.zas/test_scenarios.py` (template: `assets/templates/tests/test_scenarios.py.tmpl`).
A scenario reads the hole's text and checks it end to end: set up data, trigger the rule (a transition,
a save, `ctx.call("<module>.tasks.<fn>")` for a scheduled job), assert the outcome (`ctx.tags`,
`ctx.field`, `ctx.transitions`, `ctx.detail`, `ctx.outbox` for messages).

- `ctx.call` runs backend code in the tenant through `zango_env.py call` (no Celery needed).
- `ctx.outbox` reads `<ws>/.zas/outbox.jsonl`, which `notify()` appends to in DEBUG only.
- Holes without a scenario (other than `covered`/`blocked`) are reported as skips, so gaps are visible.
- **Prove a scenario can fail** for the riskiest rule (break the hook on purpose, run `--only H-NN`,
  see it fail, restore). A suite that cannot fail proves nothing.
- A failing scenario is a finding: fix the hook, or, when the spec text is ambiguous, keep the hook's
  stated guess, mark the hole `needs-review`, and say what was assumed. Never loosen the assertion.

## Reading failures

| Failing check id | Look at |
|---|---|
| `access.*` | `policies.json` + `zango_platform.py sync` / `check`; `access_resolved` in spec.json |
| `create.*` | the form class ([forms](map/forms.md)), the model, `ZasFormMixin`; the error JSON is in the detail |
| `transition*` | `workflow.py` engine entries, the condition hook, `ZasWorkflowMixin`; "does not start from" = status walk |
| `tag*` | `tag_transitions`, `Meta.tags`; "not possible" failing = a side the spec omits was allowed |
| `row_action*` | `row_actions` dicts, the `__action__` hook, `zas_can_perform` (`show_when`, `editable_in`, scope) |
| `scoping.*` | `access.scope_queryset`, `app_user` binding (`create_on`), the rows hook |
| `detail.*` | `<Model>Detail`, `Meta.detail_class`, child `parents`, the tab's `param` |
| `ui.page.*` | `pages/index.ts` export = route `component`; build copied to `static/js`; AppBuilder routes |
| `ui.detail.*` | `ListPage` route ownership, `detail_path`; screenshots in `.zas/screens/<role>/` |
| `ui.flow.*` "the API accepted the same values" | the browser side: the field's `pattern` against what its widget submits (a phone widget sends `+<cc>…`), a `show_when` hiding a required field, a form default (a callable model default is served as `"<function …>"`); the on-screen errors are in the detail |
| `ui.flow.*` "the API refused them too" | the backend, as for `create.*` / `transition*` above |
| `ui.flow.*` "saved, but" | the saved row differs from what was typed, or the form served a broken default; fix the form or model, not the check |
| `design.lint` | the file and line in the detail |
| `scenario.H-NN.*` | the hole's hook/task in `backend/<module>/hooks.py` / `tasks.py`; the scenario names the spec text it proves |

Fix the cause in generated code, a hook, a slot, or the skill's runtime (`assets/`), then re-run only the
failing group. Never edit the tests or results to pass, and never mark a skip as a pass. The report
lists every skip with its reason ([report](report.md)).
