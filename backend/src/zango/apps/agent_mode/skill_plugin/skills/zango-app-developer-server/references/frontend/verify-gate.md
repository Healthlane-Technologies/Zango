# STEP 5 verification gate

The full checklist for the frontend step. SKILL.md carries the summary; this is
the detail behind each item, including the snippets that make the visual items
measurable rather than a matter of taste.

Every item is binding. Any that is false is a bug in your run, not a
nice-to-have — and several of these failure modes return HTTP 200 and look
correct, which is exactly why they are listed.

All of these must be true. Any that is false is a bug in your run, not a
nice-to-have.

**The frontend is wired up:**

1. `frontend/` exists in the workspace.
2. `frontend/zango-build/zango-app.<ts>.min.js` exists and was copied to `static/js/`.
3. `backend/app/templates/app.html` references `js/zango-app.` and contains **neither** `app_initializer_endpoint` **nor** `packages/appbuilder/js/`.
4. At least one registered route has `page_type: "custom"`.
5. `/app/login` renders your branded card, **and its left panel passes the
   §5b fill gate**: at least 4 children, at least 50% vertical fill, no gap
   over 120px. Run the snippet in auth-login.md §5b — a panel holding only a
   brandmark, a headline and a footer is the known failure and looks empty.
   "It has a gradient and a headline" is not the bar.
6. **Routes and menus are saved in the app, verified by reading them back.**
   `action=get_routes` returns your routes (not `[]`), and `action=get_configs`
   returns **one config per role** — count them against the roles in the run
   context. A payload written to a file is not a saved config: if `get_routes`
   still returns `[]`, this step failed no matter what you wrote to disk, and
   the app has no navigation.
7. **Every menu item's `route_id` exists in `get_routes`.** Cross-check the two
   read-backs. Ids invented rather than taken from the save response produce a
   sidebar of dead links, and both API calls still return `success: true`.
8. **Every menu icon is inline SVG** — in that same read-back, every `icon`
   value contains `<svg`, and none is `"📄"`. That value means the icon was
   omitted or arrived corrupted and the backend substituted it, so the whole
   sidebar renders identical. Emoji must not be used at all; see 5h.

**The frontend is actually polished** — these are as binding as the eight above,
and each is checkable with a single grep over `src/custom/`:

9. `src/custom/pages/shared.tsx` exists and exports the primitives from 5c. No
   page re-implements its tab strip or key-facts grid.
10. **No literal hex colour in `src/custom/pages/`.**
   `grep -rn '#[0-9a-fA-F]\{3,8\}\b' src/custom/pages/` returns nothing —
   colours come from `var(--color-*)` tokens.
   `src/custom/auth/` is the one exception: it renders before authentication,
   so it has no tokens in scope and takes its values from the run context's
   `theme:` line instead. Those values must be declared once as custom
   properties and derived from, never sprinkled — and every one of them must
   match `theme:`. A hex there that is not in `theme:` is still a defect.
11. **No inline `style={{...}}` for static styling.** Static styling is Tailwind
   classes; inline styles only for values computed at runtime.
12. Every data surface has a loading skeleton, an empty state and an error
    state — **including each child tab** of every detail page.
13. `Money` / `DateText` are used for all currency and dates, and their
    `LOCALE`/`CURRENCY` came from the requirement spec, not a hard-coded `$`.
14. Each page has one visual anchor; no page is a row of N identical cards.
15. **Every detail page passes the anatomy in design-system.md §6**: identity
    block with avatar + status + at least one action button; `KeyFacts` called
    **with an `anchor`**; Overview built from two or more titled `Section`s
    (never one anonymous card); tabs carrying counts. Open the page and look at
    it — a title, three bare values, a tab strip and one card is a wireframe,
    and it passes every token rule while doing so.
16. **Field labels render.** Open a detail page and confirm the key-facts
    labels are visible. The detail API returns `name`, not `display_name`; a
    component reading only `display_name` blanks every label.
17. **`design-plan.md` exists and the pages match it.** For each focus entity,
    open the page and confirm: the lead card computes what the plan said it
    computes, the right rail is present with the blocks the plan listed, the
    tab empty-state copy is the copy the plan wrote, and the identity strip
    carries its listed facts. A page that satisfies items 8-15 but not its own
    plan is the exact failure this gate was added to catch.
18. **Overview is not a second copy of the header.** Compare the header's key
    facts against the first Overview section. If the same field appears in
    both, Overview is a field dump — rebuild it as the synthesis 5b required.
19. **Open one record and check the page against the stored data.** Read the
    real row (`select ... from <schema>."dynamic_models_<model>" limit 1`) and
    confirm those values appear. A page whose numbers are all `0` is internally
    consistent and uniformly wrong — gate 20 cannot see it, because nothing on
    the page disagrees with anything else. The usual cause is a `BaseDetail`
    with no `Meta.fields`: the payload then carries the *table's* columns, the
    page reads `undefined`, and a `toNum` helper turns that into a confident
    `0`. See entity-360.md §3b.

20. **Any number your page computed matches what is rendered beside it.** If
    a card says "0 quotes" while the table under it shows rows, the fetch hit
    one of the three silent-200 traps in entity-360.md §4b (missing
    `action=get_table_data`, rows at `j.data` not `j.data.records`, or an
    HTML-serialized column read as a boolean). Check the numbers on the
    rendered page — the network tab shows 200 for all three failures.
21. **The page fills the screen.** No large empty band: content width within
    ~300px of `viewport - 260`, and the rail at least 0.6x the main column's
    height. A 1080px column on a 1920px screen leaves ~640px of grey and is the
    observed failure. Snippet in design-system.md §1.

22. **The page is not flat.** Run the snippet in design-system.md §1
    ("Measure it"): at least 2 distinct card fills, every card carrying the
    hairline shadow, and a page ground that differs from the card fill. All-white
    boxes with grey title bars is the observed failure — it passes every
    structural rule and still reads as a wireframe. Confirm by eye that the lead
    card outweighs the section cards below it.

23. **No responsive grid pairs a base `grid-cols-N` with a `md:` variant.**
    `grep -rnE 'grid-cols-[0-9]+ [^"]*(sm|md|lg):grid-cols-' src/custom/`
    must return nothing. In this build the unprefixed utility wins at every
    width, so `grid-cols-1 md:grid-cols-3` silently renders one column and a
    right rail drops below the main content. Use `max-md:grid-cols-1
    md:grid-cols-3` (and `max-md:col-span-2 md:col-span-1`). See
    design-system.md §1.
24. **Labels are human.** No label renders as a raw column name:
    `ESTIMATED_VALUE`, `emd_amount`, `submission_deadline` are defects. The
    detail API's `name` is a column name, not a display label — title-case it
    and strip underscores, or pass an explicit label.
