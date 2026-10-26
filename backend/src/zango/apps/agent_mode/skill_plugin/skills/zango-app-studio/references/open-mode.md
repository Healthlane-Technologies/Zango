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
- **Look only through options.** No CSS files and no colours in `src/custom/` (the design lint). If the
  shell needs something the options can't express, say so in the build report instead of forking it.
- The shell renders `data-zas="shell"`, `shell-brand`, `shell-nav`, `shell-user` and (with a top bar)
  `shell-top`; `zas_test.design --only lint` checks that `Shell.tsx` exists and is wired.
