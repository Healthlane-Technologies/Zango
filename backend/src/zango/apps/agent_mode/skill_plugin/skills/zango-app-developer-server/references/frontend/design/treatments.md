# Card treatments and page composition

The single clearest tell of a generated page is **every block rendered the
same way** — white, bordered, same radius, same padding, stacked. Fixing it is
mechanical: pick two or three treatments per page from this library and assign
them by role.

Read [tokens.md](tokens.md) first; every recipe here uses its variables.

---

## The treatments

### A. Bordered card — the workhorse

```css
.pe-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: transform var(--dur) var(--ease-out),
              box-shadow var(--dur) var(--ease-out),
              border-color var(--dur) var(--ease-out);
}
.pe-card-interactive:hover {
  transform: translateY(-2px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}
```

40-50% of blocks on a page. Add `pe-card-interactive` **only** when the card
navigates or opens something — a card that lifts and does nothing is a lie.

### B. Sunken band — grouped metrics

A recessed strip with internal dividers, rather than N separate white tiles.
Reads as one instrument panel attached to what sits above it, and removes a
whole row of competing card edges.

```tsx
<div className="grid overflow-hidden rounded-xl border sm:grid-cols-3"
     style={{ background: 'var(--surface-sunken)', borderColor: 'var(--border)' }}>
  <div style={{ borderRight: '1px solid var(--border)' }}><Stat … /></div>
  <div style={{ borderRight: '1px solid var(--border)' }}><Stat … /></div>
  <Stat … />
</div>
```

### C. Gradient hero — the wow moment. **One per page, maximum.**

```css
.pe-hero {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-active) 100%);
  color: var(--text-inverse);
}
.pe-hero::before {          /* subtle mesh, NOT clipped white circles */
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 80% 20%, rgba(255,255,255,.18), transparent),
    radial-gradient(ellipse 70% 50% at 20% 80%, rgba(255,255,255,.08), transparent);
  pointer-events: none;
}
```

Put the identity (monogram, title, 3-4 inline facts) on the left and **the one
figure the page exists for** on the right, at 44-56px. Content inside needs
`position: relative` to sit above the mesh.

Partially-clipped white circles are the dated version of this — the radial
mesh is the replacement.

### D. Top-accent — differentiating a stack

```css
.pe-top-accent      { border-top: 3px solid var(--brand); }
.pe-top-accent-teal { border-top: 3px solid var(--accent); }
.pe-top-accent-warn { border-top: 3px solid var(--warn); }
```

For rail blocks. Three identical white boxes stacked vertically is the rail's
version of the four-equal-cards problem; colouring the top edge by category
fixes it with one line each.

### E. Tinted — quiet emphasis

`background: var(--surface-tinted)` with a transparent border. For a block
that matters more than its neighbours but is not the hero.

---

## Composing a page

**The anchor rule.** Every page has exactly one element visually heavier than
everything else — the hero figure, the primary chart, the identity header.
Name it before writing. If you cannot, you do not yet know what the page is
for, and it will come out as a form dump.

**A working detail-page composition:**

| Band | Treatment |
|---|---|
| Identity + anchor figure | C (gradient hero) |
| Supporting metrics | B (sunken band) |
| Tabs | plain, on the page ground |
| Main column blocks | A, with a sunken header bar |
| Rail blocks | A + D, accent colour varying by category |

That is three distinct treatments and a clear anchor — enough that the page
never reads as a uniform grid.

**Section header bars.** Give a card's header the sunken tone and a bottom
border:

```tsx
<header className="border-b px-4 py-2.5"
        style={{ background: 'var(--surface-sunken)', borderColor: 'var(--border)' }}>
```

This is what makes a block read as a titled panel rather than a white
rectangle with bold text at the top. Cheap, and it applies to every section.

---

## Colour beyond status chips

A page whose only colour is a row of coloured pills reads as unfinished. Put
colour in at least three places:

- the hero gradient
- rail top-accents (brand / accent / warn by category)
- tinted list rows for items needing attention (`--warn-50` ground,
  `--warn-700` text)
- an icon in a section header tinted `--accent-600`

The accent hue exists for exactly this. Using only `--brand` leaves the page
monochrome.

---

## Checks

- [ ] Two or more treatments used; no row of identical cards
- [ ] Exactly one anchor, and you can point at it
- [ ] Three surface tones visible (page / card / sunken)
- [ ] Colour in three or more places, not only status chips
- [ ] Every interactive element responds on hover
- [ ] Entrance staggered with `Rise`
- [ ] Compound shadows — no single-layer `box-shadow`
- [ ] No hard-coded brand or gray hex
