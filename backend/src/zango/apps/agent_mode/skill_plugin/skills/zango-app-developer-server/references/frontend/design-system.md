# Visual Quality Bar

What "polished" means concretely, so it is checkable rather than aspirational.
This applies to every custom page you write: detail views, dashboards, login.

This file is **domain-neutral** — it describes structure, not a house style for
any particular industry. Do not import conventions from any other design skill.

---

## 1. Colour comes from the app theme, never from your imagination

The initializer already sets CSS variables from the app's configured theme. Use
them. An app whose pages use hard-coded hexes will not match its own navbar.

```css
--color-brand-500    /* theme.colors.primary */
--color-gray-500     /* theme.colors.gray */
--color-success-500  /* theme.colors.success */
--color-warning-500  /* theme.colors.warning */
--color-error-500    /* theme.colors.error */
```

In React, read the theme directly when you need a value in JS:

```jsx
import { useAppContext } from '@zango-core/crm-framework';
const { theme, appName, appLogo } = useAppContext();
```

Declare a small token set once per app and use it everywhere:

| Token | Role |
|---|---|
| `brand` / `brand-600` | primary actions, active states, focus rings |
| `text` | primary body text |
| `sub` | secondary text, labels |
| `muted` | meta, timestamps, placeholders |
| `border` | dividers, input and card borders |
| `page` | page ground behind cards |
| `success` / `warning` / `error` | status only — never decoration |

**Never** invent a third palette inside a component. If you need a colour that is
not a token, you are usually decorating something that should be structural.

## 2. Scales — pick from these, do not improvise

- **Spacing**: 4 · 8 · 12 · 16 · 24 · 32 · 48 px. Nothing in between.
- **Type**: 11 (meta) · 12.5 (label) · 14 (body) · 16 (section) · 20–24 (page
  title). One weight step for emphasis (500 → 600/700), not three.
- **Radius**: 4 (chips, inputs inside dense tables) · 10 (inputs, buttons) ·
  14 (cards). One radius per element class, consistently.
- **Elevation**: at most two levels. A card is a 1px border plus a soft shadow;
  a drawer or modal gets the heavier one. Shadows are not decoration.

Density matters more than ornament: an enterprise table that shows 6 rows on a
laptop has failed regardless of how it looks.

## 3. Every data surface needs four states

A page that only handles the happy path is not finished. Implement all four:

| State | Requirement |
|---|---|
| **Loading** | A **skeleton** matching the shape of the content. Never a bare spinner, never an empty div. |
| **Empty** | A short title saying what would be here, one line of guidance, and the primary action if the user can create the thing. |
| **Error** | What failed, in plain language, and a retry affordance. Never a blank page. |
| **Populated** | The real thing. |

A flat grey box that never moves is indistinguishable from a card that has
finished loading and is empty — so skeletons animate (`animate-pulse`).

Empty states are per-tab and per-table, not one for the whole page.

## 4. Page anatomies

### List page
Title + count · search/filter row · table · pagination. The add button belongs
with the title, not adrift at the bottom.

### Detail page
See [entity-360.md](entity-360.md) — header/identity → key facts → overview →
child tabs → timeline.

### Dashboard
1. **KPI row** — 3–5 numbers that matter, each with a label and, where it is
   meaningful, a delta. Not twelve.
2. **Primary visual** — the one chart that answers the main question.
3. **Breakdown** — a table or grouped list supporting that chart.
4. **Worklist** — what this user should act on next, with links through.

Every number on a dashboard must be traceable: clicking it goes to the filtered
list it came from. A KPI that cannot be drilled into is decoration.

## 5. Responsive floor

Every custom page must be usable at **880px** and **480px**.

- Multi-column grids collapse to one column.
- Tables scroll horizontally inside their own container — the **page** never
  scrolls sideways.
- Side-by-side panels stack; decorative panels hide.
- Tab strips scroll rather than wrap into an unreadable pile.

When writing a raw `<style>` block, **media queries go last** — an override with
the same specificity as its base rule is decided by source order alone.

## 6. Copy

- Label things the way the user's business does, taking names from the
  requirement spec — not from the model field names.
- Sentence case for labels and buttons. No ALL-CAPS shouting except small
  letter-spaced eyebrow text.
- Buttons say what happens: *Add patient*, not *Submit*.
- Dates formatted, never raw ISO strings. Nulls render as `—`, never as
  `null`, `undefined` or blank.
- Numbers get thousands separators; currency gets its symbol.

## 7. Constraints you cannot design around

- **No new npm packages.** The build allowlist permits install and build only.
  If a design needs a charting or icon library the template does not already
  ship, redesign — or say so in your summary. Do not attempt to add it.
- **No external fonts or CDN assets.** Use the system font stack already in use.
- **Icons**: use what the template ships; otherwise inline SVG.
- Prefer the framework's own components (`@zango-core/components`,
  `@zango-core/crud/table`) over rebuilding tables, inputs or buttons. A custom
  page is custom *layout*, not custom widgets.

## 8. Checklist

- [ ] All colours from theme tokens; no stray hexes
- [ ] Spacing, type, radius drawn from the scales above
- [ ] Loading skeleton, empty state, error state on every data surface
- [ ] Dashboard KPIs drill through to a filtered list
- [ ] Usable at 880px and 480px; no horizontal page scroll
- [ ] Media queries last in any raw CSS block
- [ ] Labels in business language; nulls render as `—`
- [ ] No new packages, no external fonts, no CDN
