# Visual Quality Bar

What "polished" means concretely, so it is checkable rather than aspirational.
This applies to every custom page you write: detail views, dashboards, login.

This file is **domain-neutral** — it describes structure, not a house style for
any particular industry. Do not import conventions from any other design skill.

> **Read this before you write a page, not after.** The failure mode this file
> exists to prevent: transcribing the skeleton in
> [entity-360.md](entity-360.md) §7 with the classes swapped for inline styles,
> shipping four near-identical files with no shared primitives, no loading
> state, no empty state, and hard-coded hexes. That is a failed run even though
> every file exists and nothing errors.

---

## The standard you are working to

Output should look like it was designed by a senior product designer at a
top-tier SaaS company — **Linear, Stripe Dashboard, Vercel, Notion, Height,
Mercury**. Not "a clean admin panel". Not a Bootstrap CRUD screen with the
corners rounded.

That bar is concrete and you can check yourself against it:

- Would a designer look at this and see **deliberate decisions** — this number
  is large *because it matters*, these two fields sit together *because they
  are read together* — or would they see every element at the same weight?
- Does the page have a **point of view** about what the user came here to do,
  or is it a form dump with a title?
- Would a screenshot of it look at home in a product launch post?

**The floor is not the target.** Everything in this file — four states, tokens,
one anchor — describes the *minimum* a page must clear. A page that satisfies
every rule here and still looks unfinished **is unfinished**. Rules prevent bad
output; they do not produce good output. Judgement does, and you are expected
to exercise it.

### The failure mode this file exists to prevent

A real run produced: a back link, a title, three unlabelled values floating on
white, a tab strip, and one bare card containing a single field. It satisfied
every mechanical rule — primitives, theme tokens, Tailwind, a skeleton — and
looked like a wireframe. **Mechanical compliance is not design.**

---

## 0. Design brief — answer these before writing code

Six questions, answered silently in under a minute. Do not print them. This is
the step that separates a designed app from a generated one, and skipping it is
why every generated app otherwise looks identical.

1. **What is this app for, in the user's words?** Take the vocabulary from the
   requirement spec — *retailers* and *stock*, not *entities* and *records*.
2. **Which one or two entities does the team live inside all day?** Those earn
   the richest pages and the most design attention.
3. **What is the anchor on each page?** The one number or status the page
   exists for — a balance, a stage, a next appointment. Name it per page. If
   you cannot name it, you do not yet understand the page.
4. **Aesthetic direction** — pick ONE and hold it across every page (see §1a).
   This is what stops every Zango app looking the same.
5. **Density** — an operations tool used all day (compact rows, more per
   screen) or a review/approval tool used occasionally (more breathing room)?
6. **Currency, date format, locale** — inferred from the spec's business
   context, not asked. Set once in `shared.tsx` and record the assumption.

### The one deliberate moment

Every app gets **one element that makes it feel designed** — not decoration,
and not on every page. Pick one and execute it well:

- A hero metric on the landing page with real typographic care (large, tight
  tracking, tabular figures, a sparkline or delta beneath it).
- An identity header that genuinely identifies: monogram, reference code,
  status, and the two facts that matter, laid out with intent.
- A status timeline on the entity with a lifecycle, showing where a record is
  and what happens next.
- A worklist that answers "what should I do now?" rather than listing rows.

One well-executed moment beats five half-executed flourishes. If you cannot
point at yours when you finish, the app does not have one.

## 1a. Aesthetic direction — pick one per app

Without this every app is the same grey-and-indigo CRUD shell. The theme's
brand colour is fixed (§1), but **everything around it is yours to decide**:
surface temperature, density, type treatment, how much colour appears outside
status pills. Choose one direction in the brief and hold it everywhere.

| Direction | For | Surface | Type | Density | Signature |
|---|---|---|---|---|---|
| **Operational** | Dispatch, inventory, order desks — used all day | cool grey (`gray-50` page) | compact 13px, tabular figures everywhere | dense: 12-16px cell padding | numbers carry the page; status colour does real work |
| **Editorial** | Dashboards, reports, exec views | warm off-white | large display numbers, tight tracking (-0.03em) | airy: generous whitespace, 24-32px gaps | one oversized hero metric per screen |
| **Clinical** | Patient, case, compliance records | near-white, restrained | precise 13px, mono for IDs/codes | medium | structure and labelling over ornament; nothing decorative |
| **Approval** | Queues, reviews, sign-off flows | light neutral | clear 14px body | medium-airy | the action is unmissable; state is always visible |

Then decide **where colour appears beyond status pills** — the anchor card's
tint, an accent border on the active row, a tinted section header. An app whose
only colour is a row of coloured chips reads as unfinished.

**Never** let this collapse into "default": if you did not consciously pick a
direction, you picked Operational by accident and it will look it.

---

## 1. Colour comes from the app theme, never from your imagination

The initializer already sets CSS variables from the app's configured theme, as
**full ramps** — `25` through `950` for brand and gray, plus semantic colours.
Use them. An app whose pages use hard-coded hexes will not match its own
navbar, and will not re-skin when the tenant's brand colour changes.

```css
--color-brand-50 … --color-brand-500 … --color-brand-950   /* theme.colors.primary */
--color-gray-50  … --color-gray-500  … --color-gray-950    /* theme.colors.gray */
--color-success-500   --color-warning-500   --color-error-500
```

Because the ramps already exist, you never need `color-mix()` to build tints:
`--color-brand-50` is your tinted surface, `--color-brand-500` your action
colour, `--color-brand-700` your hover.

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

**Never** invent a third palette inside a component. A literal hex in a custom
page (`#5048ED`, `#667085`) is a defect: it is the theme colour copied by hand,
so it silently stops matching the moment the tenant re-brands.

The **login page is the single exception**, because it renders before
authentication and has no tokens in scope. It takes its values from the run
context's `theme:` line, declared once as custom properties and derived from —
see [auth-login.md](auth-login.md). If you need a
colour that is not a token, you are usually decorating something that should be
structural.

### The page must fill the screen — no large empty band

**The observed failure:** a claim detail page on a 1920px screen rendered its
content in a 1080px column, leaving **~640px of flat grey** down the right and
ending exactly at the fold with nothing below it. Every card was correct; the
page still looked wrong, because a third of it was empty.

Two independent causes, both worth checking:

**1. The shell cap is too narrow.** Your pages render *inside* the platform's
sidebar chrome, so the usable area is roughly `viewport − 260px`. A 1080px cap
wastes everything past it. `PageShell` uses `max-w-[1600px]`: wide enough to
fill a laptop, capped so text lines do not run to absurd lengths on an
ultrawide. **Do not narrow it**, and do not add a second `max-w-*` inside it.

For comparison, the reference PSP patient page fills **1598px** of a 1920px
viewport and runs 1433px tall — it uses the screen it is given.

**2. The rail runs out of content.** A `2:1` split only reads as a designed
layout when both columns have something in them. The same failing page had a
713px main column beside a 331px rail, so the bottom half of the rail was bare
grey. Fix it by moving content into the rail, not by deleting the rail:

- the identity/at-a-glance block
- current status with who changed it and when
- open items / attention flags
- contact or metadata that does not belong in the main flow
- recent activity — **activity is content**, and it is what fills a rail
  naturally, because it grows with the record

Measure it:

```js
const aside = document.querySelector('aside');
const main  = aside.parentElement.firstElementChild;
({ mainH: Math.round(main.getBoundingClientRect().height),
   railH: Math.round(aside.getBoundingClientRect().height),
   ratio: (aside.getBoundingClientRect().height /
           main.getBoundingClientRect().height).toFixed(2),
   contentWidth: Math.round(main.parentElement.getBoundingClientRect().width),
   viewport: window.innerWidth })
```

- **`ratio` should be ≥ 0.6.** Below that the rail is stranded — add content or
  fold the rail's items into the main column and drop it entirely.
- **`contentWidth` should be within ~300px of the usable area**
  (`viewport − 260`). A much smaller number means a cap is fighting the layout.

And if the whole page ends at the fold with nothing below it, that is not a
layout bug — the page does not have enough on it. Revisit the design plan.


### Responsive grids — never pair a base `grid-cols-N` with a `md:` variant

**In this build `grid-cols-1 md:grid-cols-3` renders ONE column at every
width.** The unprefixed utility is emitted after the responsive variant in the
same cascade layer, so it wins even above the breakpoint. The responsive class
is dead, and nothing warns you — the class is in the DOM and the CSS rule
exists, it just never applies.

Use `max-<bp>:` for the small-screen value instead, so the two utilities never
compete:

```html
<!-- WRONG: one column at every width -->
<div class="grid grid-cols-1 md:grid-cols-3">
<div class="grid grid-cols-2 md:grid-cols-4">   <!-- stuck at 2 -->

<!-- RIGHT -->
<div class="grid max-md:grid-cols-1 md:grid-cols-3">
<div class="grid max-md:grid-cols-2 md:grid-cols-4">
```

The same applies to `col-span`: write `max-md:col-span-2 md:col-span-1`, not
`col-span-2 md:col-span-1`.

**Verify it, do not assume it.** In the browser console on a rendered page:

```js
getComputedStyle(document.querySelector('aside').parentElement).gridTemplateColumns
```

Two tracks where you expect three (or one where you expect four) means you hit
this. A right rail that renders correctly but sits *below* the main column
instead of beside it is the classic symptom.

### Surfaces are layered, not flat

Three tones per page, not one. This is what produces depth in modern UI, and it
costs nothing:

| Surface | Value | Use |
|---|---|---|
| page | `--color-gray-50` | the ground behind everything |
| card | `#fff` | cards, panels, raised elements |
| sunken | `--color-gray-100` | secondary sections, table header rows, hover |
| tinted | `--color-brand-50` | selected/active states, the anchor card |

A page that is pure white end to end reads as unfinished. The 1–2% step between
page and card is the whole effect.

**Three more things separate a designed card from a white box**, and they are
what makes generated pages read as basic even when the structure is right:

1. **Nesting.** A lead card holds its sub-blocks on their own quiet fill
   (`Inset`) rather than stacking flat rows. This does more for perceived
   quality than any other single change — the reference PSP page puts its
   regimen and monitoring blocks on inset surfaces inside the treatment card.
2. **Tone carries meaning.** `Card` and `Inset` take `tone` — good / warn /
   bad / info. A healthy monitoring block is green; an overdue task is amber.
   **Never tint for decoration.** If every card is tinted nothing reads as
   important, so most cards on a page stay plain white.
3. **Numbers travel with a qualifier.** `MetricTile` renders value + qualifier
   + status dot: `218k/µL · Normal`, `96% · Good`, `1 of 1 · Complete`. A bare
   number is data; the qualifier is the answer. **A row of bare numbers is the
   wireframe look** — it is exactly what shipped on wapp5.

Shadows stay a hairline (`0 1px 2px rgba(16,24,40,.04)`), never a drop shadow.
Depth comes from fill and border, not blur.

#### Measure it — "flat" has a number

These rules keep being satisfied on paper and missed in the output: the page
has cards, so the rule "use cards" passes, while every card is the same white
box with a grey title bar. A real run shipped six identical cards stacked
vertically and read as a wireframe. Run this on the finished page:

```js
const cards = [...document.querySelectorAll('*')].filter(e => {
  const s = getComputedStyle(e);
  return s.borderWidth !== '0px' && s.borderRadius !== '0px'
      && e.getBoundingClientRect().width > 240;
});
const bg = new Set(cards.map(c => getComputedStyle(c).backgroundColor));
({ cards: cards.length, distinctFills: bg.size,
   withShadow: cards.filter(c => getComputedStyle(c).boxShadow !== 'none').length,
   pageGround: getComputedStyle(document.body).backgroundColor })
```

- **`distinctFills` must be ≥ 2.** All-white means no `Inset`, no `tone`, no
  sunken surface — the three-tone table above is decorative until something on
  the page actually uses a second fill.
- **`withShadow` must equal `cards`.** The hairline is on the `Card` primitive;
  zero shadows means the pages are hand-rolling `<div className="border">`
  instead of composing `Card`.
- **`pageGround` must differ from the card fill.** White cards on a white page
  is the "unfinished" look named above.

And one check no snippet catches, so do it by eye: **the lead card must not be
the same size and weight as the section cards below it.** If the one deliberate
moment from your design plan renders as the second of four identical boxes, it
is not an anchor — it is a list item. Give it a tinted anchor figure at the
display size from §2, and keep the cards under it plain.

---

## 2. Scales — pick from these, do not improvise

- **Spacing**: 4 · 8 · 12 · 16 · 24 · 32 · 48 px. Nothing in between.
- **Type**: 11 (meta) · 12.5 (label) · 14 (body) · 16 (section) · 20–24 (page
  title) · 28–32 (hero metric). One weight step for emphasis (500 → 600/700),
  not three.
- **Radius**: 4 (chips, inputs inside dense tables) · 10 (inputs, buttons) ·
  14 (cards). One radius per element class, consistently.
- **Elevation**: at most two levels. A card is a 1px border plus a soft shadow;
  a drawer or modal gets the heavier one. Shadows are not decoration.
- **Numerals**: every metric, money column and quantity gets
  `font-variant-numeric: tabular-nums`, so figures line up between rows.

Density matters more than ornament: an enterprise table that shows 6 rows on a
laptop has failed regardless of how it looks.

---

## 3. Every data surface needs four states

A page that only handles the happy path is not finished. Implement all four:

| State | Requirement |
|---|---|
| **Loading** | A **skeleton** matching the shape of the content. Never a bare spinner, never an empty div. |
| **Empty** | A short title saying what would be here, one line of guidance, and the primary action if the user can create the thing. |
| **Error** | What failed, in plain language, and a retry affordance. Never a blank page. |
| **Populated** | The real thing. |

A flat grey box that never moves is indistinguishable from a card that has
finished loading and is empty — so skeletons animate.

Empty states are **per-tab and per-table**, not one for the whole page. A detail
page with four child tabs needs four empty states.

**Skeletons match the shape of what is coming.** Not one grey rectangle: if the
content is a key-facts strip, the skeleton is four short label/value pairs; if
it is a table, it is header-height plus five rows. Shape is the entire point —
a generic box tells the user nothing about what is loading.

Empty-state copy is specific and written in the business's language:

| Instead of | Write |
|---|---|
| "No data" | "No sales orders yet" |
| "Empty" | "No invoices for this retailer" / "Nothing to approve" |
| "No records found" | "No products match these filters" + *Clear filters* |

---

## 4. Build shared primitives first — do not repeat layout markup

**Before writing any detail page, write `src/custom/pages/shared.tsx`.** Every
page then composes from it. This is not an optimisation; it is the difference
between one polished app and four pages that each drifted.

A repo where `RetailerDetail`, `SupplierDetail` and `SalesOrderDetail` each
hand-roll their own tab strip and key-facts grid is a failed run — the fourth
one always diverges, and no fix can be applied in one place.

At minimum `shared.tsx` exports:

| Primitive | Responsibility |
|---|---|
| `PageShell` | max-width, page padding, page surface |
| `PageHeader` | back link, title, reference, status chip, actions |
| `KeyFacts` | the 4–8 field label/value strip |
| `Tabs` | the tab strip, including counts |
| `Card` / `SectionTitle` | the standard panel |
| `StatusChip` | semantic colour from workflow status |
| `Skeleton` | shimmer block, shape-matched by props |
| `EmptyState` | icon + title + guidance + optional action |
| `ErrorState` | message + retry |
| `Money` / `DateText` / `Num` | locale-correct formatting, `—` for null |
| `NavigateTableBody` | the stable module-scope table body (see entity-360 §5) |

Rules for these primitives:

- They live at **module scope** and are defined once. Never define a component
  inside another component's render — see [entity-360.md](entity-360.md) §5.
- They take their colours from theme tokens only.
- `Money`, `DateText` and `Num` are the **only** places formatting is decided,
  so currency and date format are correct everywhere by construction.

A detail page should then read as composition, roughly:

```jsx
<PageShell>
  <PageHeader backTo="/retailers" title={data.title} status={...} />
  <KeyFacts fields={fields} keys={KEY_FACTS} />
  <Tabs value={tab} onChange={setTab} items={TAB_ITEMS} />
  {tab === 'overview' ? <OverviewSections … /> : <ChildTable … />}
</PageShell>
```

If your detail page is 100 lines of inline-styled JSX, you skipped this step.

---

## 5. Use Tailwind classes, not inline `style` objects

The scaffold ships **Tailwind v4** (`@tailwindcss/vite`, `tailwind.config.ts`,
and `@import "tailwindcss"` in `src/index.css`). Use it.

Inline `style={{...}}` objects cannot express hover, focus, responsive
breakpoints or `prefers-reduced-motion` — so a page written that way is
structurally incapable of meeting §3, §7 and §8 of this file. Converting the
example snippets in this repo from classes to inline styles is a downgrade, not
a translation.

Reference theme tokens from classes via arbitrary values:

```jsx
<span className="text-[color:var(--color-gray-500)] text-xs font-medium" />
<div className="rounded-xl border border-[color:var(--color-gray-200)] bg-white p-4" />
<button className="bg-[color:var(--color-brand-500)] hover:bg-[color:var(--color-brand-700)] transition-colors" />
```

Inline styles remain acceptable for genuinely dynamic values — a computed bar
width, a colour chosen from data at runtime.

---

## 6. Page anatomies

### List page
Title + count · search/filter row · table · pagination. The add button belongs
with the title, not adrift at the bottom.

### Detail page

See [entity-360.md](entity-360.md) for the data mechanics. The **visual** bar,
which is what gets missed:

```
< Patients                                                    [...]
(AR)  Asha Rao   [Active v]  [Interpreter required]  [+ Add tag]
      PT-0042 · 08 May 1975 · 51 yrs · Female · +91 98… · Dr Mehta   <- identity strip
 Overview │ Programs 1 │ Bills 2 │ Timeline │ Notes 1              <- counts
┌───────────────────────────────────────────┬──────────────────────┐
│ [icon] Diagnostics & Lab Testing [Completed]│ Patient status      │  <- RIGHT RAIL
│ Corvanel 25mg · Regimen complete           │  • Active           │
│                                            │  since 17 Aug 2026  │
│ TESTING SCHEDULE          ┌──────────────┐ │  Moved by Vedant    │
│ Tumour Marker Panel  1/1  │ REGIMEN      │ ├──────────────────────┤
│ ████████████████████████  │ Corvanel …   │ │ At a glance         │
│ Fully used                └──────────────┘ │  ▫ Prefers SMS      │
│                           ┌──────────────┐ │  ▫ Interpreter req. │
│ 1 of 1 funded tests used  │ ✓ MONITORING │ │  ▫ Victoria 8788    │
│ ████████████████ 100%     │ Regimen done │ │  ▫ Reg. 17 Aug 2026 │
│                           └──────────────┘ ├──────────────────────┤
│ ┌─────────┬─────────┬─────────┐            │ Open tasks  1       │
│ │TESTS    │NEXT DUE │PATHOLOGY│            │  Enrol in a program │
│ │1 of 1  ✓│ -  Done │ -       │            │  Overdue by 30 days │
│ └─────────┴─────────┴─────────┘            ├──────────────────────┤
├───────────────────────────────────────────┤ Consent             │
│ ⟳ Recent activity  10      Full timeline → │  ✓ Signed           │
│  17 AUG 2026  Monday            6 events   │  Method  Physical   │
│  ● Active  17:40 · Vedant                  │                     │
│    [New] → [Active]                        │                     │
└───────────────────────────────────────────┴──────────────────────┘
```

Non-negotiable, and each is visible in a screenshot:

1. **Identity block + identity strip.** Avatar/monogram, title, status chip,
   and at least one action. Below the title, a **strip of four to six inline
   facts** that identify the record — reference, key dates, the relationship
   that matters, contact. A title and one chip is a wireframe.

2. **The lead card is a synthesis, not a field dump.** The first block inside
   Overview answers the question the page exists for, computed from several
   fields plus derived state: progress against an allowance, a countdown with
   a readiness list, a balance with its ageing. **Re-listing the header's key
   facts in Overview is the most common failure and is never acceptable** — if
   a field is in the header, it does not reappear below.

3. **Main column + right rail** is the default layout (roughly 2:1). The rail
   carries the flat state: current status *with who changed it and when*, an
   at-a-glance list of flat attributes, open tasks, and any consent or
   compliance block. Putting the flat fields here is what frees Overview to be
   a synthesis. Drop to one column only when there is genuinely no state to
   park — and say so in `design-plan.md`.

4. **Key facts, with one anchor**, when the entity has a number the page exists
   for. `KeyFacts` takes an `anchor` prop; use it. On an entity whose story is
   progress rather than a single number, the lead card replaces it — do not
   ship both a KeyFacts row and a lead card saying the same thing.

5. **Tabs carry counts.** `Programs 1` tells the user something; `Programs`
   does not.

6. **Every tab has all four states** (§3), including an `EmptyState` whose copy
   names the thing. Write that copy in `design-plan.md`, not at the keyboard.

7. **Activity is content.** Anything with a history gets a recent-activity
   list — timestamp, actor, and the transition (`New → Active`), with a link
   to the full timeline. This is what makes a record feel alive rather than
   stored. Each entry gets a one-line human explanation, not just the event
   name: *"Document DOC-004 validated. Subsidy slab determined: 75%."*

8. **An entity whose status is a SEQUENCE gets a `ProcessStepper`** across the
   top of Overview — the named stages left to right, the current one marked,
   later ones muted. A status field like `Created → Submitted → Verified →
   Approved` carries the whole lifecycle, and a lone chip throws all of it
   away: the user cannot see how far the record got or what happens next.

   Apply the test before reaching for it. **Ordered** (`Identified →
   Submitted → Awarded`) gets a stepper. A **flat set of independent flags**
   (`Active`, `Interpreter required`, `VIP`) does not — those are chips, and
   forcing them into a stepper invents an order that does not exist.

9. **Empty states are invitations, not apologies.** The empty state of a tab
   the user is expected to act on carries the action itself — an upload zone,
   a create button — plus the rule that governs it (*"SLA: invoice within 48
   hours of order creation. Auto-reminder sent."*). "No data" is a defect.

A page with a title, three bare values, a tab strip and one card containing a
single field is **not finished**, even though every rule about tokens and
Tailwind was followed. Check it against the sketch above before moving on.

### Dashboard
1. **KPI row** — 3–5 numbers that matter, each with a label and, where it is
   meaningful, a delta. Not twelve.
2. **Primary visual** — the one chart that answers the main question.
3. **Breakdown** — a table or grouped list supporting that chart.
4. **Worklist** — what this user should act on next, with links through.

Every number on a dashboard must be traceable: clicking it goes to the filtered
list it came from. A KPI that cannot be drilled into is decoration.

### Give every page one visual anchor

The most common tell of generated UI is **N equal cards in a row**: same size,
same padding, same weight, nothing leading the eye. Break it deliberately.

- The primary KPI is larger, or spans two columns, or sits on
  `--color-brand-50` while its neighbours are plain white with a border.
- On a detail page the anchor is usually the identity header plus the single
  most important fact (a balance, a status, a total).
- Vary the rhythm down the page: dense table → breathing summary → dense table.

One dominant element per page. Not zero, and not five competing.

---

## 7. Motion — restrained, and never the only signal

Modern enterprise UI is not static, but this is an operations tool, not a
marketing site. The bar:

- **Transitions on state change**: hover, active tab, drawer open/close.
  150–220ms, `cubic-bezier(0.22, 1, 0.36, 1)`. Never `linear`.
- **Skeleton shimmer** while loading, as in §3.
- **Every interactive element responds to hover** — background, border or
  elevation shift. A row, tab or button with no hover state reads as disabled.
- **Focus rings are never removed.** `focus-visible` must be clearly visible;
  keyboard users navigate these apps all day.

Do not add entrance animations to tables or list rows — content that moves on
every data refresh is an irritation in an app someone uses for six hours.

Always include, once, in `index.css`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 8. Responsive floor

Every custom page must be usable at **880px** and **480px**.

- Multi-column grids collapse to one column.
- Tables scroll horizontally inside their own container — the **page** never
  scrolls sideways.
- Side-by-side panels stack; decorative panels hide.
- Tab strips scroll rather than wrap into an unreadable pile.

Prefer Tailwind's responsive prefixes (`md:grid-cols-4`). When writing a raw
`<style>` block, **media queries go last** — an override with the same
specificity as its base rule is decided by source order alone.

---

## 9. Copy

- Label things the way the user's business does, taking names from the
  requirement spec — not from the model field names.
- Sentence case for labels and buttons. No ALL-CAPS shouting except small
  letter-spaced eyebrow text.
- Buttons say what happens: *Add patient*, not *Submit*. *Confirm order*, not
  *OK*.
- Dates formatted, never raw ISO strings. Nulls render as `—`, never as
  `null`, `undefined` or blank.
- Numbers get thousands separators; currency gets **the app's** symbol, taken
  from the requirement spec — never a hard-coded `$`.
- Money is right-aligned and tabular in tables, so columns compare by eye.

---

## 10. What you may use — and the real constraints

Earlier versions of this file forbade icons and web fonts. **That was wrong**,
and it is a large part of why generated apps looked plain. The accurate picture:

### Icons — use them

**`lucide-react` is already installed** (it ships transitively with
`@zango-core`). No install needed, just import:

```tsx
import { Calendar, Receipt, Stethoscope, TrendingUp } from 'lucide-react';

<Calendar size={16} strokeWidth={1.75} className="text-[color:var(--color-gray-500)]" />
```

Rules: one size per context (16px inline, 20px in headers, 44px in empty
states), one stroke width (1.5-1.75) across the app, and always
`currentColor` via a text class so icons follow the surface. Icons belong on
menu items, empty states, buttons that do something specific, and key-fact
cards — not scattered as decoration.

### Typography — use a real typeface

There is **no CSP**, and the platform's own frontend already loads Google
Fonts. Put this at the top of `src/index.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..700&family=JetBrains+Mono:wght@400;500&display=swap');

:root { --font-sans: 'Inter', system-ui, sans-serif;
        --font-mono: 'JetBrains Mono', ui-monospace, monospace; }
body { font-family: var(--font-sans);
       font-feature-settings: 'cv11','ss01'; font-optical-sizing: auto; }
```

Then: **Inter for everything**, `font-optical-sizing` on so large text uses
the right letterforms; **JetBrains Mono for IDs, reference codes and batch
numbers** — it makes a reference look like a reference. Use variable weights
between the usual stops (450 for body, 530 for medium emphasis, 575 for
sub-headings) for finer hierarchy than 400/500/600 gives you. Always keep a
real fallback stack so a blocked request degrades rather than breaks.

### Charts — one approved library

`echarts` + `echarts-for-react` (or `recharts`) may be installed:

```bash
npm install echarts echarts-for-react
```

Only these are permitted, plus `date-fns`, `clsx`, `tailwind-merge`. Any other
package is denied by the build guard — the package name is the security
boundary, since `npm install` runs lifecycle scripts. Do not attempt others;
say so in your summary if you genuinely need one.

For a single trend, a hand-built CSS bar row or inline-SVG sparkline is often
better than pulling in a chart library — fewer bytes, full token control.

### The real constraints

- **No package outside the list above.** The guard denies it.
- **Bash cannot write files** (except the one build-deploy copy), so anything
  you need must be generated by the build or written with the Write tool.
- **Prefer the framework's own components** (`@zango-core/components`,
  `@zango-core/crud/table`) over rebuilding tables, inputs or buttons. A custom
  page is custom *layout*, not custom widgets.
- **Dark mode is not required.** Do not spend budget on it unless asked.

## 11. Checklist

**Design (judgement — check these by looking at the page, not by grepping):**
- [ ] Design brief answered; aesthetic direction consciously chosen (§0, §1a)
- [ ] Each page's anchor is identifiable at a glance
- [ ] The app's one deliberate moment exists and you can point at it
- [ ] No page is a row of N identical cards
- [ ] A screenshot would look at home in a product post — if not, keep going

**Structure:**
- [ ] `shared.tsx` exists and exports the primitives in §4
- [ ] No detail page hand-rolls its own tab strip or key-facts grid
- [ ] Three surface tones present (page ≠ card ≠ sunken/tinted)
- [ ] Detail pages match the §6 anatomy: identity block with avatar + status +
      action, `KeyFacts` **with an `anchor`**, Overview as 2+ titled `Section`s,
      tabs with counts

**States:**
- [ ] Loading skeleton, empty state, error state on **every** data surface
- [ ] Skeletons match content shape; child tabs each have their own empty state
- [ ] Empty-state copy names the thing in business language

**Style:**
- [ ] All colours from theme tokens; **no literal hex in `src/custom/pages/`**
- [ ] Tailwind classes, not inline `style` objects, for static styling
- [ ] Inter loaded; JetBrains Mono on IDs and reference codes
- [ ] `lucide-react` icons at one size and stroke width per context
- [ ] Spacing, type, radius from the §2 scales; metrics use `tabular-nums`
- [ ] Hover and `focus-visible` on every interactive element
- [ ] `prefers-reduced-motion` block present in `index.css`

**Content:**
- [ ] Labels in business language; nulls render as `—`
- [ ] Currency and date format via `Money` / `DateText`
- [ ] Field labels actually visible (API returns `name`, not `display_name`)
- [ ] Dashboard KPIs drill through to a filtered list

**Constraints:**
- [ ] Usable at 880px and 480px; no horizontal page scroll
- [ ] No package outside the approved list
