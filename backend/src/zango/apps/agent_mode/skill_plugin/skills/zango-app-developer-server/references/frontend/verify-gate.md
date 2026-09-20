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

9. `src/custom/pages/tokens.css` exists, and `shared.tsx` imports it and
   exports the primitives from 5c. No page re-implements its tab strip or
   key-facts grid. Without `tokens.css` every primitive loses its colours,
   shadows and font — the app builds and ships unstyled.
10. **No literal hex colour in any `.tsx` under `src/custom/pages/`.**
   `grep -rn '#[0-9a-fA-F]\{3,8\}\b' src/custom/pages/ --include='*.tsx'`
   returns nothing — colours come from `var(--*)` tokens.
   `tokens.css` is the one file where a literal is allowed, and **only** for
   the `--accent` steps — a second hue the theme does not supply. Brand, gray,
   success, error and warning all have theme ramps and must be aliased from
   them (`var(--color-brand-500)`), never hard-coded, or the app stops
   re-skinning with its tenant.
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
15. **Every detail page passes the anatomy in entity-360.md §6**: identity
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
    a hand-rolled `fetch` instead of `useTable` (entity-360.md §4b), or an
    HTML-serialized `_getval` column read as a boolean — which `useTable`
    passes through untouched. Check the numbers on the rendered page; the
    network tab shows 200 for every one of these failures.
21. **The page fills the screen.** No large empty band. Your pages render
    inside the platform's sidebar chrome, so the usable area is roughly
    `viewport - 260px`. A 1080px column on a 1920px screen leaves ~640px of
    flat grey and is the observed failure. Run this on the finished page:

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

    - **`ratio` must be >= 0.6.** Below that the rail is stranded — move
      content into it (identity/at-a-glance, status with who changed it and
      when, open items, recent activity — activity grows with the record and
      is what fills a rail naturally), or fold its items into the main column
      and drop the rail entirely. Do not leave it half empty.
    - **`contentWidth` must be within ~300px of `viewport - 260`.** A much
      smaller number means a `max-w-*` cap is fighting the layout. `PageShell`
      uses `max-w-[1600px]` — do not narrow it, and do not add a second
      `max-w-*` inside it.

    If the whole page ends at the fold with nothing below it, that is not a
    layout bug — the page does not have enough on it. Revisit `design-plan.md`.

22. **The page is not flat.** Run this on the finished page:

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

    - **`distinctFills` must be >= 2.** All-white means no `Inset`, no `tone`,
      no sunken surface — see [design/treatments.md](design/treatments.md).
    - **`withShadow` must equal `cards`.** The hairline is on the `Card`
      primitive; zero shadows means pages are hand-rolling
      `<div className="border">` instead of composing `Card`.
    - **`pageGround` must differ from the card fill.** White cards on a white
      page is the unfinished look.

    And one check no snippet catches, so do it by eye: **the lead card must not
    be the same size and weight as the section cards below it.** If the one
    deliberate moment from your design plan renders as the second of four
    identical boxes, it is not an anchor — it is a list item.

23. **No responsive grid pairs a base `grid-cols-N` with a `md:` variant.**
    `grep -rnE 'grid-cols-[0-9]+ [^"]*(sm|md|lg):grid-cols-' src/custom/`
    must return nothing. In this build the unprefixed utility wins at every
    width, so `grid-cols-1 md:grid-cols-3` silently renders one column and a
    right rail drops below the main content. Use `max-md:grid-cols-1
    md:grid-cols-3` (and `max-md:col-span-2 md:col-span-1`).
24. **Every table of an entity opens that entity's custom detail page.** For
    each entity with a `customMainDetail`, the number of `CrudHandler`s hitting
    its endpoint must equal the number passing the three detail props:
    `grep -rn "<endpoint>" src/custom/ | wc -l` vs
    `grep -rn "customMainDetail" src/custom/ | wc -l`. A dashboard worklist or
    role landing page listing the same records without them opens the
    framework's default drawer instead — the same record opening two different
    ways depending on where it was clicked. Both return 200 and the drawer
    looks plausible, so opening only the list page never reveals it. See
    entity-360.md §2.
24b. **No entity's `enableDetailViewRoute` wrapper is mounted as a child tab
    on another entity's detail page.** This is the opposite defect from 24 —
    the wrapper *is* wired correctly, and that's exactly what breaks it.
    Nested under `/app/<parent>/detail-view/<uuid>`, its route resolves
    relative to that mount point, can never match, and the click silently
    falls back to the **parent's list page** — not a 404, not a console error
    a passing grep would catch. Check every child-tab `CrudHandler`:
    `grep -rn "enableDetailViewRoute" src/custom/pages/*Detail.tsx` must return
    nothing. A `defaultDetailView={{ action: 'navigate', navigateUrlTemplate:
    ... }}` on that same child-tab `CrudHandler` is not the fix either — it
    renders the framework's generic default detail view instead of the
    child's `customMainDetail`, which is its own distinct failure that also
    returns 200 and looks plausible. The only correct fix is a custom
    `customTableBody` wrapping `TableBody` with `defaultDetailView={{ action:
    'custom', customHandler }}`, calling `useNavigate()` to push an absolute
    path to the child's real top-level route — see entity-360.md §4's code
    example. `customHandler` receives the raw react-table `Row`, not the row
    data: read the id off `row.original`, not `row` directly, or the pushed
    URL ends in `.../detail-view/undefined`. Then click-test it: open a
    parent's detail page, open a child tab, click a row, and confirm the URL
    and the page are the *child's own* detail page, rendering its actual
    `customMainDetail` component. See entity-360.md §4 → "Never use another
    entity's `enableDetailViewRoute` wrapper as a child tab".
25. **Labels are human.** No label renders as a raw column name:
    `ESTIMATED_VALUE`, `emd_amount`, `submission_deadline` are defects. The
    detail API's `name` is a column name, not a display label — title-case it
    and strip underscores, or pass an explicit label.

26. **Tier-2 custom detail pages (no child tables) match the same bar as
    entity-360.** For every entity given a "custom detail, no tabs" page under
    SKILL.md decision test 2: identity block with avatar + status + action,
    a synthesis lead card (not a field dump), a right rail carrying flat state,
    and one anchor. A page here that is a single narrow column of label/value rows is
    the entity-360 field-dump failure with the tabs removed instead of fixed.

27. **Every `customMainDetail` page — entity-360 or tier-2 — replaces the
    Change Logs action the default drawer had.** Grep for
    `fetch_audit_logs` under every directory containing a `*Detail.tsx`
    component used as `customMainDetail`; a page with none is missing the
    capability every other entity in the app still has via the drawer. See
    entity-360.md §4c. This applies regardless of whether the page has tabs —
    "no timeline tab" is not a reason to skip it.
