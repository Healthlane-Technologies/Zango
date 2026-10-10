# evals/vendor_hub.yaml: what a correct build looks like

`vendor_hub.yaml` is the App Studio template spec with its five spec bugs fixed (see
`references/spec/schema.md`). Use it to check the skill after any change: run the build on a fresh
app named `vendor_hub` and compare against this file. Numbers marked **(offline)** can be checked
without a Zango app and were verified on 2026-10-09.

## Phase 1: checker (offline)

`python3 scripts/spec_check.py evals/vendor_hub.yaml --out /tmp/vh` → exit 0, **0 errors, 6 warnings**:

1. `entities.vendor_contact.validation.rules[0]`: text rule without message
2. `detail_views.vendor_360.header.banners[0]`: `{hold_reason}` is a transition form field
3. `detail_views.vendor_360.header.banners[2]`: `{reject_reason}` is a transition form field
4. to 6. `detail_views.vendor_360.tabs.contacts|documents|contracts`: hidden for Finance

Counts: 9 entities in 3 modules, 9 pages, 2 detail views, 4 roles, 22 policies,
25 engine transitions, **38 holes** (on_done 9, system_transition 4, validation 4, requirement 4,
condition 3, row_action 3, system_tag 2, column 2, computed 2, stat 2, on_create 1, custom_panel 1,
custom_page 1).

Module order and entity order: `masters` (city, category) → `vendors` (vendor, vendor_contact,
vendor_document) → `procurement` (contract, purchase_order, po_line, invoice).

The raw template (`zango_app_spec.template.yaml`) must give **exit 1 with exactly 4 errors**:
`has_tag on_hold` on a status, and three texts cut at a comma inside `{ }`.

## Phases 2 to 3: code (offline parts)

- `python3 scripts/selftest_runtime.py` → 26 PASS, `ALL OK`.
- Generated modules compile (`python -m py_compile`). Class names, endpoints and policy names follow
  contracts §1. `references/examples/vendors/` is the reference for the `vendors` module.
- No generated `can_perform_row_action_*`, `process_row_action_*`, `*_condition`, `*_done` or `get_table_data_queryset`.

## Phase 4: holes

`spec_check.py … --workspace <ws> --audit-holes` → exit 0. Expected statuses:

| Hole | Status |
|---|---|
| `vendor__req__1` (GSTIN lookup, GST portal) | `blocked`: endpoint and credentials needed |
| `vendor__on_create`, `vendor__submit__done` ("activity log") | `covered`: the timeline |
| `vendor__approve__done`, `vendor__hold__done`, `vendor__release__done` | `done` (as in `references/examples/vendors/hooks.py`) |
| `vendor_360__custom__*` (onboarding checklist) + slot `OnboardingChecklist` | `done` |
| `ProcurementDashboard` (custom page) + data view | `done` |
| everything else | `done` or `needs-review` with the guess stated |

## Phases 5 to 6: platform

- Roles: Procurement Executive, Procurement Manager, Finance, Vendor User. 4 test users.
- AppBuilder: **8 routes** (vendors, contracts, purchase_orders, invoices, cities, categories,
  dashboard → `ProcurementDashboard`, `__zas` → `ZasStyleGuide`). There is no route for
  `vendor_360` / `po_360`: they're served by the list pages at `/app/vendors/detail-view/<uuid>`
  and `/app/purchase-orders/detail-view/<uuid>`.
- Menus: Procurement Executive 5 top-level items (vendors first = landing, "Master Data" group),
  Procurement Manager 6, with `purchase_orders` moved first as the landing. Finance 2 (invoices first),
  Vendor User 2 ("My Purchase Orders" first). Every icon is an inline SVG.
- `zas_test.design --only lint` passes.

## Phase 7: tests

- `zas_test.api --dry-run` → **146 checks planned** (offline).
- Live run: no `fail` in `access`, `create`, `transitions`, `tags`, `row_actions`, `detail`. Expected
  skips without fixtures: transitions whose path passes `vendor.submit` (needs a verified GST document)
  and `purchase_order.submit`. With the fixture shown in `references/testing.md`, those pass.
- Scoping: Finance lists only approved vendors and only POs in `[acknowledged, partially_invoiced, closed]`.
  Vendor User lists only its own vendor, and another vendor's 360 is `not_found`.
- UI: the branded login; every menu page renders for every role; the vendor 360 shows 7 tabs for
  Procurement Manager, 6 for Procurement Executive (the invoices tab is limited to Manager, Finance and
  Vendor User), and 4 for Finance (overview, purchase orders, invoices, activity; warnings 4 to 6).
- Design: `lint`, `tokens` and `tree` pass. `gallery` passes on macOS with Chromium 153 (the
  goldens' platform) and is skipped elsewhere. `layout` reports nothing at 1440 px.
- Report verdict: **Ready with gaps** (the blocked GSTIN lookup, the notification provider). Every
  scheduled task has a `# zas:schedule` line, so `zango_platform.py schedule` sets all of them.
