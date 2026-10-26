# Open mode: building from an approved prototype

An app is in open mode when its approval bundle has `.zas/bundle/prototype/` (the user approved a
free-form prototype instead of the kit preview). Read `.zas/bundle/prototype/index.md` first: it lists
every screen, its roles and its files, and names the shell's screenshots.

What the user approved is the **look**. Behaviour, data, menus and permissions still come from the spec.
The prototype's tokens are already in the runtime (`app.design` → `spec.ui.json`), so standard pages
pick up its palette, fonts, radii and shadows with no code.

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
| A bar over the page with its title | `topbar: true` |
| A sidebar wider or narrower than 240px | `width` |

Rules:

- **The menu is the spec's.** `makeShell` draws the platform's menu for the signed-in role
  (`roles[].menu`, saved by `zango_platform.py appbuilder`). A group in the prototype is a menu `group`
  in the spec; a label it shows per role is that role's menu `label`. If the prototype's menu differs
  from the spec's, report it as a spec problem. Do not hard-code menu items in `Shell.tsx`.
- **The user menu is the platform's.** The prototype's persona or role switcher becomes the user card:
  it opens appbuilder's profile drawer (role switch, sessions, password) and logs out through
  `/app/logout`. Trial-account sign-in or persona pickers are prototype-only: do not build them.
- **Look only through options.** No stylesheet for the shell and no colours in `src/custom/` (the design lint). If the
  shell needs something the options can't express, say so in the build report instead of forking it.
- The shell renders `data-zas="shell"`, `shell-brand`, `shell-nav`, `shell-user` and (with a top bar)
  `shell-top`; `zas_test.design --only lint` checks that `Shell.tsx` exists and is wired.

## Screens: theme or rebuild

`spec_check` decides, from the spec's `prototype.screens` (SCHEMA.md, `prototype`), and writes the table
at the end of `.zas/bundle/prototype/index.md` (and `plan.md`). Follow it; never change a class yourself.

| Class | When | How it is built |
|---|---|---|
| **theme** | a crud list or 360 page | The standard runtime page (`makeListPage` / `makeViewsPage`, the 360 from its list page), already in the prototype's tokens. Optionally `src/custom/screens/<page>.css` for what tokens can't say (filter chips, table density, header treatment), imported from `src/custom/pages/index.ts`. |
| **rebuild** | a custom page or dashboard, or a standard page marked `rebuild: true` | Its hole's slot, ported from the approved screen. The hole text names the folder. |
| **prototype-only** | not built | Nothing. |

**Theme.** Compare the built page with `shot.<role>.png`. Anything left that the runtime can't reach is a
gap for the build report, not a reason to write custom code: the lint fails a themed page whose
`Page_<code>` export isn't `makeListPage` / `makeViewsPage`. A screen stylesheet:

- selectors all start with `[data-zas-key="<page>"]` (the page's root);
- values are tokens only: `var(--z-*)`, `var(--p-*)` (other `app.design` tokens), `var(--t-*)`; no colour
  literals, `url()` or `@import`.

**Rebuild.** The slot gets the page's data, nothing new:

| Hole | Slot props | Data |
|---|---|---|
| `custom_page` (custom page, dashboard) | `api` | its contract's data hook, as in kit mode |
| `rebuild_page` (list page) | `api`, `data: { entity, endpoint, page }` | `api.useTableRows(endpoint)`; rows, filters and row actions through the zas kit (`ZasTable`, `RecordDrawer`) |
| `rebuild_view` (360) | `api`, `zas`, `record`, `refresh` | the 360 payload (header, stats, panels, actions); `api.runTransition`, `runTag`, `runRowAction` |

The runtime routes stay as they are: `makeListPage` renders a `rebuild_page` slot in place of the table, and
the 360 renders a `rebuild_view` slot after its access checks. Before writing a rebuild slot, Read the
screen's `shot.<role>.png` and `dom.<role>.html` (the platform blocks the write until you have). Then:

- port the markup to React on the zas kit; for markup the kit has no block for, write it with the screen's
  classes from `css.used.css`, as zas classes or token-only inline styles;
- keep every `data-zas-ref` / `data-zas-action` marker the snapshot has on the element that shows that
  field or runs that action;
- the prototype's data and scripts are not used: values come from the props above, and actions run through
  the API, so permissions and workflow stay the platform's.

**Libraries** (`libraries.json`): use the npm package of the same library (Chart.js → `chart.js`, ECharts →
`echarts`); when there is none or it doesn't fit, draw it with the zas kit or plain SVG. Name each swap in
the build report.

## Lint (`zas_test.design --only lint`)

Open mode replaces the kit's sketch palettes with the prototype's tokens, for every mapped screen alike:

- No colour literals anywhere in `src/custom/`. A literal that is an `app.design` token is reported with
  the variable to write instead (`#0F766E` → `var(--brand)`, `#E0693F` → `var(--p-coral)`).
- Inline styles may set colours, borders, shadows and fills only through `var(--…)` (or
  `transparent` / `inherit` / `currentColor` / `none`).
- Fonts (`fontFamily`, `font-family`) are `app.design.fonts` families, generic families, or
  `var(--z-font)` / `var(--z-mono)` / `var(--z-display)`.
- `<style>` tags stay banned; stylesheets only as `src/custom/screens/<page>.css` (§Screens).
- Plus the shell and themed-page checks above. Kit mode is unchanged.
