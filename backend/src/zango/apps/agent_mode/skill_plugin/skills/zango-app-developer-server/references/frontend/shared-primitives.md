# `shared.tsx` — the primitives every custom page composes from

Write this file **first**, before any detail page or dashboard. Every other
custom page imports from it. See [design-system.md](design-system.md) §4 for
why this is mandatory rather than an optimisation.

## Write it for this app

You are a capable UI engineer: design these primitives for the app in front of
you rather than adopting a generic set. The entities, the vocabulary and the
one thing each page exists for should shape what you build — an app about
shipments wants different primitives from one about prescriptions. Add what the
app actually needs (a `Sparkline` for a metrics dashboard, an avatar image
where entities have photos) and leave out what it does not.

What every version needs, whatever you name it: formatters that are the single
place currency and date format are decided, a page surface, a card, an identity
header, a status chip, a key-facts strip, tabs if the page has them, and all
four states from [design-system.md](design-system.md) §3 — skeleton, empty,
error, populated. Define them at module scope, take colours from theme tokens,
style with Tailwind classes.

**Leaving something out is a design decision, so make it deliberately.** The
list above is structure, and structure alone renders as a correct, flat page.
What gives a detail page presence is the identity treatment — a monogram or
avatar beside the name, the single most important fact raised to anchor weight,
a lifecycle shown as a stepper when the entity has stages, recent activity when
it has history. An observed run designed its primitives well, dropped every one
of those as "not needed", and shipped a page where every element carried the
same weight. It passed every rule in these files and still looked unfinished.
Before you cut a primitive, ask whether the page has anything left that leads
the eye — see design-system.md §4, "give every page one visual anchor".

### Four things you cannot infer — take these exactly

Everything else on this page is your judgement. These four are platform facts,
and guessing them produces code that renders wrong with no error:

1. **The navigate-on-click table body** is
   `<TableBody defaultDetailView="navigate" />`, imported from
   `@zango-core/crud/table`. Export it at module scope and pass it as
   `customTableBody` — defining it inline remounts the table on every render
   and `CrudHandler` loses its state (see [entity-360.md](entity-360.md) §5).

2. **Responsive grids must use `max-md:`, never a bare base class.** In this
   build `grid-cols-1 md:grid-cols-3` renders ONE column at every width — the
   unprefixed utility wins over the responsive variant. Write
   `max-md:grid-cols-1 md:grid-cols-3`. See design-system.md §2.

3. **A page surface is `bg-[color:var(--color-gray-50)]` with an inner
   `max-w-[1600px] px-4 py-6 md:px-6`** — and it goes around detail and custom
   pages only, **never** around a `CrudHandler` list. Which page gets one, and
   what breaks when you get it wrong, is below.

4. **Colours come from the theme's ramps** (`--color-brand-*`, `--color-gray-*`,
   `--color-success/warning/error-*`), never a literal hex. design-system.md §2
   has the full contract and the one login-page exception.

Also not guessable, and not in the worked example below: **Change Logs.** Any
entity on a custom detail page needs it — moving off the default drawer removes
its kebab action and nothing replaces it. Endpoint and payload are in
entity-360.md §4c.

**Field labels: fall back to `name`, and humanise whatever you land on.** The
detail API returns each field as `{type, name, value, …}` — there is no
`display_name` key on it. A primitive that reads only `display_name` renders
every label blank. So try `display_name → label → name → the key`, which
survives either shape — **and then humanise the result**, because `name` and
the key are the raw column names. Without that last step the page ships labels
reading `lease_start_date` and `phone` instead of "Lease start date" and
"Phone", which is what an unfinished screen looks like. An observed run did
exactly this: it wrote its own `FieldGrid` without a humanise step and shipped
snake_case labels across the key-facts strip.

**Empty values arrive as the string `"NA"`, not `null`.** So `value ? x : y`
and `value ?? y` both treat an empty field as present, and the page renders a
literal "NA" where a subtitle, a status or a contact line should be — or shows
a header with "NA" under the title. Normalise once, in the same place you
humanise (`v == null || v === 'NA' || v === '' ? undefined : v`), and let
missing values fall through to the em-dash your primitives already render.

**Open the page and read it** before moving on — labels humanised, no stray
"NA". Which keys exist at all is a separate trap — entity-360.md §3b.

Set `LOCALE` and `CURRENCY` from the requirement's business context. They are
the only place formatting is decided, so a wrong value is wrong on every page
at once.

### A worked example, if you want one

`assets/shared.tsx` beside this `references/` directory is one complete
implementation — 32 primitives that satisfy everything above. Read it when you
want to check a shape or a prop contract.

**It is a reference, not a starting point.** Transcribing it gives every Zango
app the same primitives, which is the failure this file's own quality bar
exists to prevent. Take the four facts above, take an idea if one is useful,
and write your own.

(If you do read it: `ls` the skill directory for the absolute path rather than
typing it from memory — a path that does not resolve fails silently for a
subagent. And note `cp` is denied; only the STEP 5f build deploy is permitted.)

Two things to check against the real scaffold before relying on them: the
`@zango-core/crud/table` exports you import, and the exact theme variable names
the initializer set. Both are in [appbuilder.md](appbuilder.md) and
[crud/core.md](crud/core.md).

---


### Which pages get a `PageShell`

`PageShell` supplies a page surface: a `gray-50` background plus `px-4 py-6
md:px-6` of padding. That is what a detail page needs, because a detail page is
a set of bare `Card`s that would otherwise sit on nothing.

A **`CrudHandler` list page is already a finished surface** -- the table ships
its own white card, title bar, filter/search row and internal padding. Wrapping
it in `PageShell` pads an already-padded component, and the result is a grey
band between the sidebar and the table, the table card floating inset instead
of meeting the chrome, and ~48px of horizontal room lost -- enough to clip the
last column on a laptop.

So:

| Page content | Wrapper |
|---|---|
| `CrudHandler` list (the whole page is the table) | **none** -- render it bare |
| Detail page (`PageHeader` + `KeyFacts` + `Tabs` + `Card`s) | `PageShell` |
| Hand-built custom page (dashboard, wizard, report) | `PageShell` |

```jsx
// Right -- the CrudHandler is the page.
const PatientsList = () => (
  <PatientsTable />
);

// Wrong -- double-padded, grey gutter, clipped last column.
const PatientsList = () => (
  <PageShell>
    <PatientsTable />
  </PageShell>
);
```

A list page that needs real chrome above the table (a stat row, a segmented
filter) is a custom page, not a list page: use `PageShell`, and pass the
CrudHandler `headerProps` rather than building a second header beside it.

---

## Card treatments — pick one per block, never the same one five times

**This is the section that decides whether the page looks designed.** A real
run composed a whole detail page from five `Section`s, which is structurally
correct and renders as five identical white boxes with grey title bars — a
wireframe. `Section` is the *plainest* treatment, not the default one.

Choose per block:

### A. `Section` — a plain group of fields

The floor. Use for secondary field groups only, never for the lead block.

```tsx
<Section title="Patient & policy">
  <FieldGrid fields={fields} keys={['patient', 'tpa_name', 'policy_number']} />
</Section>
```

### B. `Card` + `Inset` — the lead card (the one that carries the page)

A card whose sub-blocks sit on their own quiet fill. **The nesting is the
single biggest contributor to perceived quality** — one level of `Inset`
separates "designed" from "boxes".

```tsx
<Card className="mb-4">
  <div className="mb-3 flex items-center justify-between">
    <SectionTitle>Billing summary</SectionTitle>
    <StatusChip label="Partially approved" tone="warn" />
  </div>

  <Meter label="Amount billed"   value={billed}   max={billed} />
  <Meter label="Amount approved" value={approved} max={billed} tone="good" />

  <div className="mt-4 grid max-md:grid-cols-1 gap-3 md:grid-cols-3">
    <MetricTile label="Paid by TPA"  value={<Money value={paid} />}
                qualifier="1 of 3 instalments" tone="warn" />
    <MetricTile label="Outstanding"  value={<Money value={outstanding} />}
                qualifier="Awaiting TPA"       tone="bad" />
    <MetricTile label="Approved"     value={`${pct}%`}
                qualifier="of billed"          tone="good" />
  </div>

  <Inset className="mt-3" tone="warn">
    <b>Pending documents</b> — the discharge summary has not been uploaded.
  </Inset>
</Card>
```

### C. `Card tone=` — a block whose whole meaning is its status

```tsx
<Card tone="bad">
  <SectionTitle>Rejected by TPA</SectionTitle>
  <p className="text-[13px] text-[color:var(--color-gray-700)]">
    Policy lapsed before the admission date. Re-submit under the new policy.
  </p>
</Card>
```

**Never tint for decoration.** Most cards on a page stay plain white; a tint
that appears everywhere stops meaning anything.

### D. `RailCard` — right-rail blocks

Quieter than a main-column card: smaller title, optional count.

```tsx
<RailCard title="At a glance">
  <AtAGlance items={[
    { text: `Patient: ${fields.patient?.value ?? '—'}` },
    { text: `TPA: ${fields.tpa_name?.value ?? '—'}` },
  ]} />
</RailCard>

<RailCard title="Needs attention" count={openItems.length}>
  {openItems.length === 0
    ? <span className="text-[13px] text-[color:var(--color-gray-500)]">No open items right now.</span>
    : openItems.map((i) => <div key={i.key} className="text-[13px]">{i.text}</div>)}
</RailCard>
```

### The composition rule

On any detail page: **exactly one** B (the lead card), zero or one C, as many A
and D as the content needs. If your page has no B, it has no anchor — and that
is the page that reads as a wireframe no matter how correct the data is.

### Numbers never travel alone

`MetricTile` takes a `qualifier` and a `tone` for a reason. `₹0.00` is data;
`₹0.00 · Awaiting TPA` is the answer the page exists to give. **A row of bare
numbers is the wireframe look.** If you cannot write a qualifier for a number,
ask whether that number belongs on the page at all.

---

## Using them — composition is the point

A detail page is composition, and the mix is what separates designed from
wireframe: **one lead `Card` carrying the page** (with `Inset` and metric tiles
inside it), a right rail of secondary blocks, and the plain `Section`
treatment only for field groups underneath. A page built from `Section` alone
is the known failure — five identical white boxes.

The props your detail component receives, and how child tables are wired to
`CrudHandler`, are in [entity-360.md](entity-360.md) §3 and §4 — that file owns
the mechanics, including the traps. `assets/shared.tsx` shows one set of
primitives composed together if you want to see the shape.

## Checklist

- [ ] `shared.tsx` written **before** the first detail page, designed for
      this app rather than transcribed from the worked example
- [ ] `LOCALE` and `CURRENCY` inferred from context and recorded as an assumption
- [ ] Every primitive at module scope, none defined inside a render
- [ ] No page re-implements a primitive the file already exports
- [ ] `defaultDetailView="navigate"`, `max-md:` grids, and the page-surface
      rule all followed (the four facts above)
- [ ] Skeletons shape-matched; `EmptyState` used per tab and per table
- [ ] No literal hex anywhere in `src/custom/`
