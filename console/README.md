# Zango Console

The redesigned platform panel. It is served at `/console/`, alongside the existing
App Panel (`frontend/`, served at `/platform/`). The two share no code.

- Design reference: [`design/prototype.html`](design/prototype.html). Tokens are ported to
  `src/styles/tokens.css` and exposed to Tailwind in `tailwind.config.ts`.
- Scope: only screens backed by existing `/api/v1/...` endpoints.

## Develop

```sh
npm install
npm run dev          # http://localhost:5173/console/
```

The Vite dev server proxies `/api`, `/auth`, `/static` and `/session_security` to Django on
`http://localhost:8000`. Set `ZANGO_DEV_SERVER` to use another address. Sign in through
the proxied `/auth/login/`, and the session cookie works for both servers.

## Build

```sh
npm run build        # type-check, then write the bundle into backend/src/zango/assets/console/
```

The build writes `console.<timestamp>.min.js` and `.min.css` and removes any earlier
build. `tenancy/templates/console.html` loads them with the `use_latest` filter, which
picks the newest timestamp. Commit the bundle, as with `assets/app_panel/js`.

## Layout

| Path | Contents |
| --- | --- |
| `src/api/` | `client.ts`: fetch wrapper that unwraps `{ success, response }`, sends CSRF, flattens DRF errors into one message, and redirects to login on 401/403. `hooks.ts`: `useAppId`, `useApiMutation` (toasts and invalidation), and `toFormData` (pass `repeatArrays` for views that read a field with `getlist`). Each resource module has query keys and hooks. |
| `src/ui/` | Primitives: Button, Badge, Card, Table, Pagination/usePaged, Tabs, Segmented, FilterSelect, Field, FieldGroup, Switch/SwitchField/SwitchRow, Checkbox, KeyValues, CodeBlock, Drawer, Modal, ConfirmModal, Menu/RowMenu, SaveBar, toast, Icon, useDebounced. Most are shown at `/console/_ui`. |
| `src/shell/` | Sidebar (workspace and app modes), breadcrumbs, top bar, ⌘K palette. Nav items are in `nav.ts`. |
| `src/pages/` | Route screens. Unbuilt screens use `Placeholder`, which links to the classic panel. |
| `src/styles/` | `tokens.css`, `components.css` (ported from the prototype), base styles |

To give a route a breadcrumb, set `handle: { crumb }` on it (see `router.tsx`).

Component styles live in `components.css`, not in Tailwind utilities, so they match the
prototype exactly. Tailwind leaves out any component class it can't find written in full
in the source, so write class names out instead of building them (`'bd-green'`, not
`` `bd-${tone}` ``).

Don't put code in a `lib/` directory, because the repo `.gitignore` ignores `**/lib/`.
