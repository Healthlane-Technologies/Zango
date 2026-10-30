# Open mode: building from an approved prototype

An app is in open mode when its approval bundle has `.zas/bundle/prototype/` (the user approved a
free-form prototype instead of the kit preview). Read `.zas/bundle/prototype/index.md` first: it lists
every screen, its roles and its files, and names the shell's screenshots. When it has a Change column,
read §Change map: it says which screens need structural work.

**The approved page is the contract.** `.zas/bundle/prototype/prototype.html` is exactly what the user
approved. Every screen of the built app must look like it, on every role. When the prototype is the kit
page (a template app: `manifest.json` has `"kit": true`), `studio_verify(["style"])` (design_diff,
§Style parity) compares the computed styles of every part of every screen with that page and fails the
build on what the user changed until they match. Run it before you finish.

What the user approved is the **look**. Behaviour, data, menus and permissions still come from the spec.
The prototype's tokens are already in the runtime (`app.design` → `spec.ui.json`), so standard pages
pick up its palette, fonts, radii and shadows with no code.

**Port, don't redraw.** The platform hands you the prototype itself, on every build:

| Where | What |
|---|---|
| `frontend/src/custom/prototype.css` | Every stylesheet of the prototype, each rule scoped under `.zp`. Import it once (from the files that render `.zp`); never edit it (the lint compares it with the prototype). |
| `.zas/bundle/prototype/source/` | Each of the prototype's scripts as written, and `index.md`: what each file defines, by line. A screen's component, its helpers (pills, avatars, formatters) and its icon set are there. |
| `.zas/bundle/prototype/screens/<id>/` | What each screen rendered, per persona (`shot`, `dom`, `css.used.css`): the reference parity compares with. |

A screen copied from the prototype's own markup and classes matches it; one redrawn on the zas kit only
resembles it. So every rebuild screen, and the shell when `makeShell` cannot draw it, is a **port**:
the prototype's component, in React, under `<div className="zp">`, with the app's data in place of the
demo data (§Screens).

## Change map (`changes.json`)

When the bundle has `changes.json` (an app on a template, or a change request), the prototype was
compared with a **baseline**: the template's starting prototype, or the version the app was last built
from. Each screen has a tag, computed from the parts (the Change column of `index.md`): it says what
**structural** work a screen needs. The look is not in the tags: `changes.json` `look` lists the
stylesheets that changed (`shared/<part>.diff`, the CSS diff) and the classes they touch, and
design_diff checks every screen for it (§Style parity), whatever its tag.

| Tag | Means | What you do |
|---|---|---|
| `unchanged` | The screen and the shared look are as in the baseline. | Build it the standard way from the spec (a kit page, or its hole as in kit mode). On a change request, don't touch it. |
| `restyled` | The screen's structure is the same; the shared look changed (`global`; `look` in `changes.json`). | No structural work. Read `shared/<part>.diff` for what changed, carry it to the parts it styles (`kit.css` on the `.zas-…` selectors, §Style parity), then `studio_verify(["style"])`. |
| `edited` | The screen changed, but most of it is still the baseline. | Port only the change: read `screens/<id>/diff.patch` with the screen's `shot` and `dom`, and edit the existing page or slot. A change the spec says (a column, a status, a button) comes from the spec. |
| `rewritten`, `new` | Mostly new markup, or a screen the baseline didn't have. | Port it in full, as below (§Screens, rebuild), or build it from the spec when it is a kit page. |

`global` says which shared parts changed (`tokens.css`, `app.css`, `shell.js`, `other`). When only
`tokens.css` changed, every screen is `restyled`: update the theme, then `studio_verify(["style"])`.
`removed` lists screens the baseline had and the approved prototype doesn't; their pages are gone from
the spec too.

## Style parity (design_diff)

For a kit-page prototype, `studio_verify(["style"])` (or `zas_test.design --only style`) opens
`prototype.html` and the built app on every mapped screen and role, pairs each part of the screen (the
shell, page title, cards, table headers, buttons, badges, the 360's header, avatar, facts, stat cards,
tabs and panels: `scripts/kit_vocab.py` PARTS, kit class → `.zas-…` class) and compares their computed
styles: colours and gradients, borders, radius, shadows, type, spacing, and `::before`/`::after`
decorations. The data doesn't matter: the two pages show different records, a header's look is the same.

- A difference **blocks** (`design.style.<screen>.<role>` fails, and the build with it) when the user
  changed that property: the approved page differs there from the baseline (`baseline.html`, the page
  the user started from). Other differences are listed, never blocking.
- `.zas/style_diff.md`: every difference, blocking first, as `part (.zas-selector) property: approved X ·
  built Y`.
- The platform already carries the creator's look over: `proto_port.py` compiles the prototype's
  `look.css` and `imported/bridge.css` onto the runtime's selectors into `src/zas/look.gen.css` (imported
  by `zas/kit.tsx`, rewritten every build: never edit it). design_diff runs with it in place, so what
  still blocks is what the compile could not carry (a rule on a kit class the runtime has no element
  for is listed at the end of that file) or what the runtime draws differently.
- `.zas/style_fix.css`: the approved values on the runtime selectors for every blocking difference
  (shorthands, decoration placement, colours as `rgb()`). Copy its rules into
  `frontend/src/custom/kit/kit.css` and adjust; keep the `html ` prefix (kit.css loads before
  tokens.css). The palette lint accepts its colours.
- Fix in `kit.css` on the `.zas-…` selector the line names, never in a page's own code: every screen
  drawing that part gets the fix. A part the runtime has no element for is reported as "the approved
  screen shows it, the built one doesn't"; build it from the spec, or report it as a gap.
- After the build's fix rounds the platform runs **style rounds**: what still blocks comes back to you
  with the same lines. What is left after them fails the build.

## The shell

Build the app shell as `src/custom/Shell.tsx` on the runtime's `makeShell`, and pass it to `ZangoApp`
as `customComponents={{ Layout: Shell }}` in `src/App.tsx`. Do not use the kit-mode shell props
(`navbarConfig.customLogo`, `customBottomContent`, `topbarConfig.customLeftContent`) in open mode:
`makeShell` replaces the whole layout, and those props would not show.

```tsx
// src/custom/Shell.tsx — the approved prototype's shell (look only)
import { makeShell } from "../zas";

export default makeShell({
  nav: "brand-strong",          // design token behind the menu
  tone: "dark",                 // light text on it
  brand: { title: "Diagnostic Test Vouchers", subtitle: "Oncology support program", icon: "ticket" },
  groups: "headings",
  user: "side",
});
```

```tsx
// src/App.tsx
import Shell from "./custom/Shell";
// …
<ZApp … customComponents={{ Layout: Shell }} authConfig={{ customComponents: { LoginPage: ZasLogin } }} />
```

Read the shell off each role's home screenshot (index.md lists them), then choose:

| What the screenshot shows | Option |
|---|---|
| Menu down the left side / across the top | `layout: "side"` (default) / `"top"` |
| The menu's background | `nav`: a token name, never a colour: `card` (default), `page`, `sunk`, `brand`, `brand-strong`, `brand-soft`, or any other `app.design` token (read as `--p-<name>`) |
| Light text on a dark menu | `tone: "dark"` (default `"light"`) |
| App name, a second line, a mark | `brand: { title, subtitle, icon }` (lucide name; no icon shows the initials), or `logo: true` for the platform's app logo |
| Small uppercase headings over menu groups / groups that fold | `groups: "headings"` (default) / `"collapsible"` |
| The signed-in user at the sidebar's bottom / in a top bar | `user: "side"` (default for side) / `"top"` |
| The sidebar's user card under the brand, above the menu | `sideUser: "top"` (default: the spec's `app.shell.user`, so usually nothing to pass) |
| A bar over the page with its title | `topbar: true` |
| A sidebar wider or narrower than 240px | `width` |

Rules:

- **The menu is the spec's.** `makeShell` draws the platform's menu for the signed-in role
  (`roles[].menu`, saved by `zango_platform.py appbuilder`). A group in the prototype is a menu `group`
  in the spec; a label it shows per role is that role's menu `label`. If the prototype's menu differs
  from the spec's, report it as a spec problem. A menu item's `count` in the spec draws its number
  (`makeShell` fetches it); never hard-code one. Do not hard-code menu items in `Shell.tsx`, except
  the screens not built in this version: `.zas/bundle/prototype/index.md` ("Shell: screens kept in
  the menu, greyed out") lists them, and they go to `makeShell` as `soon`, exactly as written.
- **The user menu is the platform's.** The prototype's persona or role switcher becomes the user card:
  it opens appbuilder's profile drawer (role switch, sessions, password) and logs out through
  `/app/logout`. Trial-account sign-in or persona pickers are prototype-only: do not build them.
- **Options first, else a port.** When the options draw the prototype's shell, use them. When the shell
  has what they can't express (a persona card at the top, a primary button in the sidebar, counts on
  menu items, the prototype's own header), port the prototype's shell component instead: its markup and
  classes under `<div className="zp">`, around the platform's menu and user card:

  ```tsx
  // src/custom/Shell.tsx — the prototype's Sidebar(), ported
  import "./prototype.css";
  import { Link, useLocation } from "react-router-dom";
  import { shellMenu, UserCard } from "../zas";
  import type { LayoutProps } from "../zas";

  export default function Shell({ menu = [], profileInfo = {}, children }: LayoutProps) {
    const items = shellMenu(menu, String(profileInfo.current_role || ""), SOON);  // SOON: index.md's greyed-out screens
    // … the prototype's sidebar markup; each menu link is
    //   <Link to={item.uri} data-zas="shell-nav" className="…the prototype's nav class…">…</Link>
    return <div className="zp shell" data-zas="shell">…<UserCard user={profileInfo} up />…<main>{children}</main></div>;
  }
  ```

  `shellMenu` is the role's platform menu with the landing page in its spec group and the not-built
  screens greyed out; draw its groups and items, never a hard-coded list. A count on a menu item comes
  from the API like any other number. `UserCard` is the platform's profile drawer and logout.
- The shell renders `data-zas="shell"`, `shell-nav` on each menu link and the user card (`makeShell`
  adds `shell-brand`, `shell-user` and, with a top bar, `shell-top`); `zas_test.design --only lint`
  checks that `Shell.tsx` exists, is wired, and draws the platform's menu and user card.

## The kit

Every runtime page (list, 360, drawer, dialogs, dashboards on the zas kit) draws with the zas kit's
pieces. In open mode the app gets **its own kit**, built from the prototype's pieces with the
default kit's interface, so standard pages look like the prototype without rebuilding them.

The kit is for **kit pages** (§Screens). When every mapped screen is a rebuild, they are ported and the
kit can stay empty: the kit check skips.

`frontend/src/custom/kit/` (the platform creates it with an empty stub):

| File | What |
|---|---|
| `index.ts` | Exports the app's version of each piece the prototype shows, under its zas name: `Button`, `Badge`, `Chip`, `Panel`, `StatTile`, `Tabs`, `Timeline`, `FieldGrid`, `Drawer`, `Modal`, `EmptyState`, `Banner`, `Kpis`, `Bars`, `List`, `MiniTable`, `Board`, `Progress`, `ZasTable`, `makeShell`. A piece it doesn't export stays the default kit's. |
| `kit.css` | The prototype's look for kit markup, imported from `index.ts`. |
| `map.json` | Where each piece is in the prototype, so the platform can compare them. |

Build it in this order, before the first record slice:

1. Read the prototype's screens (`dom.<role>.html`, `css.used.css`, `shot.<role>.png`) and list the
   pieces it repeats: its buttons, status badges, cards or panels, stat tiles, tabs, tables, drawers.
   Each is one of the zas pieces above; a prototype part with no zas piece stays in a rebuild slot.
2. For each one, restyle the zas piece rather than writing a new one: a selector in `kit.css` on the
   piece's zas classes (`.zas-btn.pri`, `.zas-panel`, `.zas-tbl th`…), or a wrapper in `index.ts`
   that passes the base piece an extra class (`zk-…`) or a different layout. Keep the props, the
   `data-zas*` attributes and the behaviour: pages, tests and the API rely on them.
3. Write `map.json`, one entry per piece (and per variant that looks different, like a primary and a
   default button):

```json
{
  "pieces": [
    { "id": "button-primary", "component": "Button",
      "props": { "variant": "primary", "icon": "plus", "children": "New request" },
      "mockup": { "screen": "requests", "role": "maya", "selector": ".toolbar .btn.primary", "index": 0 } },
    { "id": "status-badge", "component": "Badge", "props": { "label": "Approved", "tone": "green" },
      "mockup": { "screen": "requests", "role": "maya", "selector": "td .pill.ok" } }
  ]
}
```

   - `mockup`: a prototype screen id and persona from `index.md`, and a CSS selector (with `index`
     when it matches several) for **one** instance of the piece in that screen's DOM.
   - `props`: what draws the same instance with your kit, copying its text (JSON only: text children,
     items arrays; a Button's, EmptyState's or Modal's `icon` as a lucide name). `built`: a selector for
     the element to shoot, only when it isn't the piece's root.
   - `ZasTable` and `makeShell` need data and a page: no map entry; the screen parity compares them.
4. Build, deploy, then `studio_verify` with `{"paths": ["kit"]}` (or `zas_test.design --only kit`):
   each piece is cropped from the live prototype and shot on `/app/__zas?kit=mockup&piece=<id>`; over
   5% different fails it. `.zas/screens/kit/index.html` shows each pair; Read the two images to see
   what differs. After your work, the platform runs kit rounds on what is still over the limit.

Rules:

- Colours: a token (`var(--…)`) or a colour the prototype's own CSS uses (from its `css.used.css`).
  Fonts: `app.design.fonts`. No `url()` or `@import`.
- `kit.css` selectors target kit markup only: `.zas…`, `.zk-…` or `[data-zas…]`.
- Import the base pieces from `../../zas/ui`, `../../zas/ZasTable` or `../../zas/Shell`, never from
  `../../zas` or `../../zas/kit`: those re-export your kit, so a piece would wrap itself.
- Default design (no prototype) leaves the kit empty; the lint refuses kit code there.

## Screens: kit or rebuild

`spec_check` decides, from the spec's `prototype.screens` (SCHEMA.md, `prototype`), and writes the table
at the end of `.zas/bundle/prototype/index.md` (and `plan.md`). Follow it; never change a class yourself.

| Class | When | How it is built |
|---|---|---|
| **kit** | a crud list or 360 page | The standard runtime page (`makeListPage` / `makeViewsPage`, the 360 from its list page), drawn with the app's kit (§The kit) in the prototype's tokens. Optionally `src/custom/screens/<page>.css` for what only this page does differently, imported from `src/custom/pages/index.ts`. |
| **rebuild** | a custom page or dashboard, or a standard page marked `rebuild: true` | Its hole's slot, ported from the approved screen. The hole text names the folder. |
| **prototype-only** | not built | Nothing. |

**Kit.** A kit page is checked by design_diff (§Style parity) when the prototype is the kit page:
run `studio_verify(["style"])` and fix what it reports in `kit.css`, starting from `.zas/style_fix.css`.
For any other prototype, compare the built page with `shot.<role>.png`, part by part, including the
360's header, facts, stat tiles, tabs and panels (a record page has its own `screens/<id>/`: open it as
well as the list). What differs is fixed in the kit piece that draws it (every page using that piece
gets the fix), then in the page's stylesheet. `kit.css` can restyle **any** `.zas-…` element, not only
the pieces in `map.json`: find the prototype's element in `dom.<role>.html`, copy its declarations from
`css.used.css` (gradients, borders, shadows, fonts, letter-spacing, `text-transform`) onto the matching
`.zas-…` selector, and hide what the prototype does not show. A design change can touch any part, so
check every part, not the ones the pieces list names. `prototype.css` does not style kit pages: its
rules sit under `.zp`, which only ported (rebuild) screens render. Anything left is
a gap for the build report, not a reason to write custom code: the lint fails a kit page whose
`Page_<code>` export isn't `makeListPage` / `makeViewsPage`. A screen stylesheet:

- selectors all start with `[data-zas-key="<page>"]` (the page's root);
- values are tokens only: `var(--z-*)`, `var(--p-*)` (other `app.design` tokens), `var(--t-*)`; no colour
  literals, `url()` or `@import`.

**Rebuild: port the prototype's screen.** The slot gets the page's data:

| Hole | Slot props | Data |
|---|---|---|
| `custom_page` (custom page, dashboard) | `api` | its contract's data hook, as in kit mode |
| `rebuild_page` (list page) | `api`, `data: { entity, endpoint, page }` | `api.useTableRows(endpoint)`; rows, filters and row actions through the zas kit (`ZasTable`, `RecordDrawer`) |
| `rebuild_view` (360) | `api`, `zas`, `record`, `refresh` | the 360 payload (header, stats, panels, actions); `api.runTransition`, `runTag`, `runRowAction` |

The runtime routes stay as they are: `makeListPage` renders a `rebuild_page` slot in place of the table, and
the 360 renders a `rebuild_view` slot after its access checks. Before writing a rebuild slot, Read the
screen's `shot.<role>.png` and `dom.<role>.html` (the platform blocks the write until you have). Then:

1. Find the screen's component in `.zas/bundle/prototype/source/index.md` (the function the prototype's
   router renders for that screen id) and Read it, with the small parts it uses (status pills, avatars,
   countdowns, empty states, date formatters, the icon map).
2. Copy it into the slot as React: the same elements, the same `className`s, the same inline styles and
   colours, inside one `<div className="zp">` root (the scope `prototype.css` styles). Shared parts go in
   one module (`src/custom/proto/…`) that the slots import, never redrawn per screen.
3. Replace the demo data with the app's: rows from the slot's data hook, actions through the API, the
   demo's `go("detail", …)` with the app's routes. When the screen shows a field the API doesn't return
   (an age from a birth date, a referral's deadline, a specialist's city), add it in the backend: a
   computed column on the entity's table (`StringCol` + `<name>_getval`, JSON when the screen needs
   several values) or a small read-only view under the module's `urls.py`, scoped with
   `access.scope_queryset` like the list, with its policy for the roles that open the screen.
4. Keep the screen's states (loading, empty, error) as the prototype draws them.

And:

- show everything the hole text's "It must show" list names (its headings, columns, tabs, buttons and
  labels, in those words); a panel the screen has is never dropped for a simpler one;
- keep every `data-zas-ref` / `data-zas-action` marker the snapshot has on the element that shows that
  field or runs that action;
- every workflow move, tag and row action the screen offers, wherever it sits (header, rail, a link in
  a panel), carries `data-zas="action"` and `data-zas-key="<transition or action name>"`: a kit `Button`
  with `zasKey`, or those two attributes on your own element. The flow check finds the move by that key;
- the prototype's runtime is not used (its router, store, timers, toasts): values come from the props and
  the API, so permissions and workflow stay the platform's. Its *code* is what you port.
- a requirement wins over the prototype: where the screen shows what a requirement forbids (a
  specialist's email to a doctor), leave it out and say so in a `zas:note`.

## Demo data (`backend/demo_data.py`)

The approved screens show the prototype's sample records; the app should open on the same ones, not on
the test records the API tests leave. Write `backend/demo_data.py`:

```python
# backend/demo_data.py — the prototype's sample data (source/…: its seed arrays), loaded by the platform
def load(users):
    """Replace the app's records with the prototype's sample data; return {entity: count}.
    users: {spec role: AppUserModel}, the test users; make each the prototype's persona for that role
    (its name; the records the persona owns in the prototype)."""
```

- Copy the prototype's own seed values (names, statuses, dates, notes) and map them to the app's
  models; dates relative to the prototype's "now" are shifted to the real now.
- Replace, not add: delete the records the tests made (children first), then create. Set workflow
  status through the workflow package's state rows, as the app's records keep it.
- The platform runs it (`manage.py agent_mode_demo_data <app>`, one transaction) before the screens are
  compared with the prototype, and after the tests, so the creator opens the demo data. A loader that
  raises is a design failure for the fix round (`design.demo_data`).
- The test users already carry the personas' names (`zango_platform.py users`).

**Libraries** (`libraries.json`): use the npm package of the same library (Chart.js → `chart.js`, ECharts →
`echarts`); when there is none or it doesn't fit, draw it with the zas kit or plain SVG. Name each swap in
the build report.

## Lint (`zas_test.design --only lint`)

Open mode lets ported code keep the prototype's look as written:

- Colour literals in `src/custom/` must be colours the approved prototype uses (its page, styles and
  scripts); any other colour fails. Tokens (`var(--…)`) are always fine.
- Inline styles are free (ported markup keeps the prototype's), apart from that colour rule.
- Fonts (`fontFamily`, `font-family`) are the prototype's families, `app.design.fonts`, generic
  families, or `var(--z-font)` / `var(--z-mono)` / `var(--z-display)`.
- `src/custom/prototype.css` must be exactly what the platform wrote. No other stylesheet in
  `src/custom/` except `screens/<page>.css` for a kit page (§Screens); `<style>` tags stay banned.
- Plus the shell, kit (§The kit) and kit-page checks above. Kit mode is unchanged.

## Parity (`zas_test.design --only parity`)

Until the prototype carries field and action markers (P2), parity in open mode is:

- **Every mapped screen opens as each of its roles** (prototype personas are matched to spec roles by
  the manifest's role label): no console or page errors, no 5xx, no error or no-access state, no raw
  timestamps. A record screen opens a record the role can see; a route's `:id` is filled with a record
  of the entity whose list page the route sits under (`/app/cases/:id/review` → a case). A route
  parameter that names no record (a link token) is not opened: the check skips it with that reason.
- **What it shows**: the approved screen's titles, columns, tabs, buttons and labels must be on the
  built one. Labels the persona's prototype shows on a third or more of its screens are its shell
  (menu, top bar, the prototype's screen jumper): checked with the shell, not per screen.
- A prototype screen that did not open when it was captured (its capture shows another screen: the
  manifest gave no record or params it needs, or it only shows a toast) has no reference: skipped,
  and listed with the capture's problems.
- **One look per screen**: the built page, shot at 1280 px, next to the approved `shot.<role>.png`, with
  a look-difference score: how differently the two are laid out (edges in the first screen; 0% = the
  same, a different layout is 40% and more; a faithful port with demo data sits near 10–15%). The
  score goes to the build report. A score over 40% (`ZAS_LOOK_FAIL`: a different layout, not demo
  data) also fails the screen's parity check, so it counts in the verdict.
- **Look rounds** run on that score: each round sends the screens still over 25% (and those with a
  parity problem), worst first; the platform rebuilds and re-shoots after your changes. They go on
  while a screen gets at least 3 points closer, up to 5 rounds, and stop when every screen is within
  the limit (AGENT_MODE_LOOK_LIMIT, _MIN_GAIN, _MAX_ROUNDS). The report shows each screen's path
  (58% → 31% → 18%).

Log each library swap so the report lists it:
`python -m zas_test.log --workspace <ws> --phase 6 --step "library: Chart.js" --status ok --detail "npm chart.js 4.4"`
(or `--detail "redrawn with zas Bars"`).
