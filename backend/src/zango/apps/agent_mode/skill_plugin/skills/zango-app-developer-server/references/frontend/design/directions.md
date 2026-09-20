# Aesthetic direction — pick one row

Asking an agent to "commit to a direction" produces the average of every
admin panel it has seen. Picking a **row** does not. Choose one in the STEP 5b
brief, record it in `design-plan.md`, and hold it across every page.

The brand hue is fixed by the tenant theme. What this table sets is the second
hue, the surface temperature, the density, and how loud the type runs.

| Direction | Fits | Accent | Page surface | Density | Display type |
|---|---|---|---|---|---|
| **precision** | An all-day operational worklist: dispatch, inventory, claims, ops consoles | Teal `#2FB59E` | cool `#FAFAFB` | dense — 12-13px body, `py-2` rows, ~35% air | 26-28px, -0.035em |
| **editorial** | Reviewed and approved a few times a day: proposals, MLR, underwriting, case review | Gold `#C79A2E` | warm `#FAFAF8` | airy — 14px body, `py-3.5` rows, ~55% air | 34-40px, -0.04em |
| **ledger** | Money and records: billing, rent, payroll, reconciliation | Slate-blue `#4E6E9C` | neutral `#FAFAFA` | dense, figure-led — mono for every amount | 30px, -0.035em, tabular |
| **care** | A person is the subject: patients, tenants, students, members | Coral `#E3705B` | peach `#FBFAF7` | airy, larger text — 14-15px body | 28-32px, -0.03em |
| **console** | Systems and health: monitoring, assets, infrastructure | Violet `#7C6BD9` | cool `#F9FAFB` | very dense, mono-heavy | 24-26px, -0.04em |

Set the accent as `--accent` in `tokens.css`, along with its `-50`/`-600`/`-700`
steps (mix toward white and black from the base).

## Applying the row

**Density** decides row padding, body size and how much fits on a screen —
`py-2` and 12.5px for dense, `py-3.5` and 14px for airy. Apply it everywhere;
a dense page with airy cards reads as neither.

**Display type** decides the page title and hero figure. Take the size and
tracking straight from the row.

**Accent** goes on section-header icons, rail top-accents, and data emphasis.
Never on destructive actions, and never as a second status colour.

## The rules that outrank the row

- **Never let it collapse into "default."** Not picking a row is picking the
  generic one, and it will look it.
- **One row per app**, not per page. Two directions across four pages reads
  as two half-finished apps.
- **The anchor still applies** — see [treatments.md](treatments.md). A row
  sets the palette and rhythm; it does not tell you what the page is for.

## The one deliberate moment

Each app gets one element executed with real care — not decoration, and not
repeated on every page:

- a hero figure with genuine typographic attention (large, tight tracking,
  tabular, a delta or meter beneath it)
- an identity header that actually identifies: monogram, reference, status,
  and the two facts that matter
- a status timeline for an entity whose lifecycle is a sequence
- a worklist that answers "what should I do now?" rather than listing rows

One executed well beats five half-done. If you cannot point at yours when you
finish, the app does not have one.
