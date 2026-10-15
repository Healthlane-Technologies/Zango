# Map: `pages`, `roles[].menu` → React exports, AppBuilder routes, role menus

Package references: `references/zango/packages/appbuilder/api-configuration.md` (routes,
menus, icons, token) and `references/zango/frontend/appbuilder.md` (`ZangoApp`,
`customPages`). **You do not call the AppBuilder API by hand.**
`scripts/zango_platform.py appbuilder` does routes and menus from `.zas/spec.resolved.json`,
reads them back and fails loudly. This file explains what it writes, so you can
check it and fix the spec or the React exports when it fails.

## 1. Every page is a custom React page

The appbuilder shell's own `page_type: "crud"` renderer cannot use the design system,
the quick filters or the 360 route. So **every** spec page is registered as
`page_type: "custom"` and rendered by the `zas` runtime:

| Spec `page.type` | `frontend/src/custom/pages/index.ts` export | AppBuilder route |
|---|---|---|
| `crud` | `export const Page_<code> = makeListPage("<code>")` | `{path: <route>, page_type: "custom", component: "Page_<code>"}` |
| `detail`, hero **has** a crud page | none | **none**: served at `<hero list route>/detail-view/<uuid>` by the list page |
| `detail`, hero has **no** crud page | `export const Page_<code> = makeDetailPage("<code>")` | `{path: "<route without /:id>", component: "Page_<code>"}` |
| `custom` | `export const <component> = makeCustomPage("<code>")` + slot `custom/slots/<component>.tsx` | `{path: <route>, component: "<component>"}` |
| (always) | `export const ZasStyleGuide = ZasGallery` | `{path: "/app/__zas", component: "ZasStyleGuide"}` (design tests, in no menu) |

- The export name **is** the route's `component`. Use `.zas/spec.resolved.json`
  `pages.<code>.export`, which the checker derives (`Page_<code>`, or the spec's `component`).
- AppBuilder matches `<path>/*`, so the 360 under a list route needs no route of its own.
- `route` must start with `/app/`. A `detail` route's `/:id` is dropped. The id is the
  `detail-view/<uuid>` segment.
- Custom pages render inside `makeCustomPage` (toast host, design tokens, error boundary).
  The slot component holds the content ([custom-code](../custom-code.md)).
- `App.tsx` comes from `assets/templates/frontend/App.tsx` (`customPages` + `ZasLogin`).

## 2. Routes (global)

`zango_platform.py appbuilder` builds one route per row above:
`{route_id, name: page.title, path, page_type: "custom", component, icon: <svg>, extra_params: {}}`.

- It **merges** with `get_routes`: a route with the same `path` keeps its `route_id`,
  and routes the spec does not know about are kept. `save_routes` replaces the whole
  list, so it never sends only the new routes.
- It reads back with `get_routes` and maps `path → route_id` for the menus.

## 3. Menus (one config per role)

From `roles[].menu`:

| Spec item | Menu item |
|---|---|
| `{page, label?, icon}` | `{route_id, name: label or page.title, uri: route, icon: <svg>, children: []}` |
| `{group, icon, items: [...]}` | `{route_id: "", name: group, uri: "#", icon: <svg>, children: [...]}` |
| `page` that is a `detail` page served by a list page | not allowed (no route). The checker errors |
| `page` the role cannot access | skipped, with a warning (the checker already warned) |

- **Icons:** lucide names in the spec → inline SVG from `.zas/menu_icons.json`
  (`scripts/lucide_icons.py`). Every route and menu item gets one. A name or an emoji
  ends up as a grey document or a broken `<img>`. Children without an icon get their
  page's icon, or `circle`.
- **Landing:** AppBuilder has no per-role landing setting. The script puts the
  `landing` page first in the role's menu (moving it out of a group if needed) and
  reports the move. Confirm in the live test which page opens after login.
- Role ids: from the App Panel roles API. `create_config` takes the **numeric** id.
  Roles that already have a config are updated (`update_config&pk=`), never duplicated.
- `AnonymousUsers` / `SystemUsers` get no menu.

## 4. Read-back checks (the script runs them; repeat by hand if it fails)

- `get_routes` contains every exported page's route. `component` = export name.
- `get_configs` has **one config per spec role**, and each menu's names match the spec.
- Every menu `route_id` (except groups) exists in `get_routes`. Every `icon` contains `<svg`.
- The built JS exports every `component` (`grep -o "Page_vendors" frontend/dist/...`).
  An export missing from the bundle gives a blank page with no error.
- The token in the config URL lasts 2 hours. On a 302 to `/login/`, re-run the script (it
  fetches a fresh token). Never report the app as done with routes or menus unsaved.
