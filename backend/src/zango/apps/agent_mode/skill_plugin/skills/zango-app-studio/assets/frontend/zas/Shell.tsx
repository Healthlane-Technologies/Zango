// The app shell for appbuilder's Layout slot (`customComponents.Layout` in src/App.tsx). Open mode
// builds it from the approved prototype's shell: src/custom/Shell.tsx is
//
//   export default makeShell({ nav: "brand-strong", tone: "dark", brand: { title: "…", icon: "ticket" } });
//
// Only the look is the prototype's. The menu is the platform's for the signed-in role (the spec's
// roles[].menu, saved by zango_platform.py), routing stays appbuilder's (`children` is its outlet),
// and profile, role switch and logout are appbuilder's own (its drawer, its logout API).
import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useLocation } from "react-router-dom";
import * as appbuilder from "@zango-core/appbuilder";
import { ChevronDown, LogOut, UserRound } from "lucide-react";
import * as api from "./api";
import { SPEC, number } from "./config";
import { Icon, cx } from "./ui";

// Exported by appbuilder 1.0.0-rc.1 but missing from its main .d.ts (like ZangoApp's customPages).
const UserProfileDrawer = (appbuilder as any).UserProfileDrawer as React.FC<{ isOpen: boolean; onClose: () => void }>;

/** Sign out the way appbuilder's own drawer does: its logout API (DELETE /api/v1/appauth/logout/;
 * a 401 means the session is already gone), then its sign-in cookie, then the login page. Not
 * appbuilder's /app/logout page: that one posts to /logout, which older servers answer with a 405,
 * so it showed "Logout Error" and left the user signed in. */
export async function logOut(): Promise<void> {
  try {
    await (appbuilder as any).performAppLogout?.();
  } catch {
    // signed out or not, the login page decides
  }
  const host = window.location.hostname;
  const domains = ["", host, ...(host.includes(".") ? [`.${host.split(".").slice(-2).join(".")}`] : [])];
  for (const d of domains) {
    for (const path of ["/", "/app", "/app/"]) {
      document.cookie = `zangocookie=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path}${d ? `; domain=${d}` : ""}`;
    }
  }
  window.location.href = "/app/login";
}

export interface ShellOptions {
  /** "side": a sidebar (default). "top": the menu in a bar across the top. */
  layout?: "side" | "top";
  /** Design token behind the menu: card (default), page, sunk, brand, brand-strong, brand-soft, or any app.design token. */
  nav?: string;
  /** Text on that background: "light" background with dark text (default), or "dark" background with light text. */
  tone?: "light" | "dark";
  /** The header above the menu. Defaults to the app's name and initials; `logo` shows the platform's app logo instead. */
  brand?: { title?: string; subtitle?: string; icon?: string; logo?: boolean };
  /** A menu group as a small heading over its pages (default), or as a collapsible item. */
  groups?: "headings" | "collapsible";
  /** Where the user card and its menu sit: the sidebar's bottom (default for "side") or the top bar. */
  user?: "side" | "top";
  /** In the sidebar: the user card under the brand, above the menu ("top"), or at the bottom (default:
   * the spec's app.shell.user). */
  sideUser?: "bottom" | "top";
  /** A bar over the page with its title (always on for layout "top"). */
  topbar?: boolean;
  /** Sidebar width in px (default 240). */
  width?: number;
  /** Prototype screens not built in this version, greyed out in the menu where the prototype has them
   * (spec prototype.screens[].menu). `group` joins that menu group, or adds it after the group `after`. */
  soon?: SoonItem[];
}

export interface SoonItem { label: string; group?: string; icon?: string; roles?: string[]; after?: string }

export interface PlatformItem { name?: string; label?: string; url?: string; uri?: string; icon?: string; children?: PlatformItem[]; soon?: boolean }
export interface LayoutProps { menu?: PlatformItem[]; profileInfo?: Record<string, any>; appLogo?: string; children?: React.ReactNode }

const NAMED: Record<string, string> = {
  card: "var(--z-card)", page: "var(--z-ground)", sunk: "var(--z-sunken)", brand: "var(--brand)",
  "brand-strong": "var(--b600)", "brand-soft": "var(--b50)", text: "var(--z-text)",
};
const navBackground = (t?: string) =>
  !t ? undefined : NAMED[t] || (/^[a-z][a-z0-9-]*$/.test(t) ? `var(--p-${t}, var(--z-card))` : undefined);

const label = (i: PlatformItem) => i.name ?? i.label ?? "";
const href = (i: PlatformItem) => i.url ?? i.uri ?? "#";
const norm = (p: string) => (p.endsWith("/") ? p : p + "/");
const isOn = (i: PlatformItem, path: string): boolean =>
  (href(i) !== "#" && norm(path).startsWith(norm(href(i)))) || (i.children || []).some((c) => isOn(c, path));

function ItemIcon({ icon }: { icon?: string }) {
  if (!icon) return <Icon name="circle" />;
  // the platform menu carries the lucide SVG zango_platform.py saved; a name works too
  if (icon.trim().startsWith("<svg")) return <span className="zi zas-sh-svg" aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon }} />;
  return <Icon name={icon} />;
}

/** The title of the spec page the route belongs to (the longest route that matches). */
function pageTitle(path: string): string {
  let best = "", len = -1;
  for (const p of Object.values(SPEC.pages)) {
    const re = new RegExp("^" + p.route.replace(/\/:[^/]+/g, "/[^/]+").replace(/\/$/, "") + "(/|$)");
    if (re.test(path) && p.route.length > len) { best = p.title; len = p.route.length; }
  }
  return best;
}

const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]!.toUpperCase()).join("") || "U";

export function UserCard({ user, up }: { user: Record<string, any>; up: boolean }) {
  const [pos, setPos] = useState<{ left: number; top?: number; bottom?: number } | null>(null);
  const [drawer, setDrawer] = useState(false);
  const btn = useRef<HTMLButtonElement>(null);
  const name = String(user.name || "User");
  const role = String(user.current_role || user.user_role || "");
  const open = () => {
    const r = btn.current?.getBoundingClientRect();
    if (!r) return;
    setPos(up ? { left: r.left, bottom: window.innerHeight - r.top + 6 } : { left: Math.max(8, r.right - 220), top: r.bottom + 6 });
  };
  return (
    <>
      <button ref={btn} type="button" className="zas-sh-user" data-zas="shell-user" onClick={open} aria-haspopup="menu">
        {user.profile_pic ? <img className="zas-sh-av" src={user.profile_pic} alt="" /> : <span className="zas-sh-av">{initials(name)}</span>}
        <span className="zas-sh-who"><b>{name}</b>{role && <small>{role}</small>}</span>
        <ChevronDown className="zi zas-sh-chev" aria-hidden="true" />
      </button>
      {pos && createPortal(
        <div className="zas" onClick={() => setPos(null)} style={{ position: "fixed", inset: 0, zIndex: 59 }}>
          <div className="zas-pop" style={pos} onClick={(e) => e.stopPropagation()} role="menu">
            <button type="button" role="menuitem" data-zas="action" data-zas-key="profile"
              onClick={() => { setPos(null); setDrawer(true); }}><UserRound />Profile and roles</button>
            <hr />
            <button type="button" role="menuitem" data-zas="action" data-zas-key="logout"
              onClick={() => { setPos(null); void logOut(); }}><LogOut />Log out</button>
          </div>
        </div>, document.body)}
      {drawer && <UserProfileDrawer isOpen={drawer} onClose={() => setDrawer(false)} />}
    </>
  );
}

const same = (a?: string, b?: string) => (a || "").trim().toLowerCase() === (b || "").trim().toLowerCase();

/** appbuilder lands on the first menu item, so zango_platform.py lifts each role's landing page out of
 * its group to the top of the saved menu. Draw it back where the spec's menu has it. */
export function regrouped(menu: PlatformItem[], role: string): PlatformItem[] {
  const spec = (SPEC.menus || {})[role] || Object.entries(SPEC.menus || {}).find(([r]) => same(r, role))?.[1];
  const land = spec?.landing, route = land ? SPEC.pages[land]?.route : undefined;
  if (!spec || !route) return menu;
  const group = (spec.items || []).find((g: any) => g.group && (g.items || []).some((i: any) => i.page === land)) as any;
  const at = menu.findIndex((it) => !it.children?.length && norm(href(it)) === norm(route));
  const target = group ? menu.find((it) => it.children?.length && same(label(it), group.group)) : undefined;
  if (at < 0 || !target) return menu;
  const item = menu[at];
  const out = menu.filter((_, i) => i !== at).map((it) => (it === target ? { ...it, children: [...it.children!] } : it));
  const kids = out.find((it) => it.children && same(label(it), group.group))!.children!;
  kids.splice(Math.min(kids.length, (group.items || []).findIndex((i: any) => i.page === land)), 0, item);
  return out;
}

/** The menu a shell draws for the signed-in role: the platform's, landing page back in its group, with
 * the not-built prototype screens greyed out. A shell ported from the prototype uses it too. */
export function shellMenu(menu: PlatformItem[], role: string, soon: SoonItem[] = []): PlatformItem[] {
  const items = regrouped(menu, role);
  return soon.length ? withSoon(items, soon, role) : items;
}

/** The platform menu with the role's not-built prototype screens added, greyed out. */
function withSoon(menu: PlatformItem[], soon: SoonItem[], role: string): PlatformItem[] {
  const out = menu.map((it) => (it.children ? { ...it, children: [...it.children] } : it));
  for (const s of soon) {
    if (s.roles?.length && !s.roles.some((r) => same(r, role))) continue;
    const item: PlatformItem = { name: s.label, icon: s.icon, soon: true };
    const group = s.group ? out.find((it) => it.children && same(label(it), s.group)) : undefined;
    if (group) { group.children!.push(item); continue; }
    const added = s.group ? { name: s.group, children: [item] } : item;
    const at = s.after ? out.findIndex((it) => same(label(it), s.after)) : -1;
    if (at >= 0) out.splice(at + 1, 0, added); else out.push(added);
  }
  return out;
}

/** roles[].menu[].count: the number on a menu item, by its route: how many rows of the page's entity the
 * role sees (the item's `where` applied), from that entity's table metadata (zas.menu_count). */
function useMenuCounts(role: string, path: string): Record<string, number> {
  const [counts, setCounts] = useState<Record<string, number>>({});
  useEffect(() => {
    const spec = (SPEC.menus || {})[role] || Object.entries(SPEC.menus || {}).find(([r]) => same(r, role))?.[1];
    const items = (spec?.items || []).flatMap((it: any) => (it.items ? it.items : [it])).filter((i: any) => i.count && i.page);
    let live = true;
    for (const i of items) {
      const page = SPEC.pages[i.page];
      const E = page?.entity ? SPEC.entities[page.entity] : undefined;
      if (!page || !E) continue;
      api.get(E.endpoint, { view: "table", action: "get_table_metadata", zas_menu: i.page })
        .then((j) => {
          const n = api.body(j)?.table_metadata?.zas?.menu_count;
          if (live && typeof n === "number") setCounts((c) => ({ ...c, [norm(page.route)]: n }));
        })
        .catch(() => undefined);
    }
    return () => { live = false; };
  }, [role, path]);  // refreshed on navigation, so a count follows the records the user just changed
  return counts;
}

function NavCount({ it, counts }: { it: PlatformItem; counts: Record<string, number> }) {
  const n = href(it) !== "#" ? counts[norm(href(it))] : undefined;
  return n === undefined ? null : <span className="zas-sh-n" data-zas="shell-count">{number(n)}</span>;
}

function NavItems({ items, groups, path, counts = {} }: { items: PlatformItem[]; groups: "headings" | "collapsible"; path: string; counts?: Record<string, number> }) {
  const [shut, setShut] = useState<Record<string, boolean>>({});
  return (
    <>
      {items.map((it, i) => {
        const kids = it.children || [];
        if (it.soon) {
          return (
            <span key={i} className="zas-sh-a soon" aria-disabled="true" title="Not in this version" data-zas="shell-soon">
              <ItemIcon icon={it.icon} /><span>{label(it)}</span>
            </span>
          );
        }
        if (!kids.length) {
          return (
            <Link key={i} to={href(it)} className={cx("zas-sh-a", isOn(it, path) && "on")} data-zas="shell-nav" data-zas-key={href(it)}>
              <ItemIcon icon={it.icon} /><span>{label(it)}</span><NavCount it={it} counts={counts} />
            </Link>
          );
        }
        if (groups === "headings") {
          return (
            <React.Fragment key={i}>
              <div className="zas-sh-g">{label(it)}</div>
              <NavItems items={kids} groups={groups} path={path} counts={counts} />
            </React.Fragment>
          );
        }
        const closed = shut[i] ?? !isOn(it, path);
        return (
          <React.Fragment key={i}>
            <button type="button" className={cx("zas-sh-a", isOn(it, path) && "in")} aria-expanded={!closed}
              onClick={() => setShut({ ...shut, [i]: !closed })}>
              <ItemIcon icon={it.icon} /><span>{label(it)}</span><ChevronDown className={cx("zi zas-sh-chev", !closed && "up")} />
            </button>
            {!closed && <div className="zas-sh-sub"><NavItems items={kids} groups={groups} path={path} counts={counts} /></div>}
          </React.Fragment>
        );
      })}
    </>
  );
}

export function makeShell(options: ShellOptions = {}): React.FC<LayoutProps> {
  const o = { layout: "side" as const, tone: "light" as const, groups: "headings" as const, width: 240, ...options };
  const userAt = o.user || (o.layout === "top" ? "top" : "side");
  const showTop = o.layout === "top" || !!o.topbar || userAt === "top";
  const sideUser = o.sideUser || SPEC.app.shell?.user || "bottom";

  function ZasShell({ menu = [], profileInfo = {}, appLogo, children }: LayoutProps) {
    const { pathname } = useLocation();
    const main = useRef<HTMLElement>(null);
    useEffect(() => { main.current?.scrollTo?.(0, 0); }, [pathname]);
    const title = pageTitle(pathname);
    const b = o.brand || {};
    const brand = (
      <Link to="/app" className="zas-sh-brand" data-zas="shell-brand">
        {b.logo && appLogo ? <img src={appLogo} alt="" /> : <span className="zas-sh-mark">{b.icon ? <Icon name={b.icon} /> : initials(b.title || SPEC.app.name)}</span>}
        <span className="zas-sh-name">{b.title || SPEC.app.name}{b.subtitle && <small>{b.subtitle}</small>}</span>
      </Link>
    );
    const role = String(profileInfo.current_role || profileInfo.user_role || "");
    const items = shellMenu(menu, role, o.soon || []);
    const counts = useMenuCounts(role, pathname);
    const nav = <nav className="zas-sh-nav"><NavItems items={items} groups={o.groups} path={pathname} counts={counts} /></nav>;
    return (
      <div className={cx("zas zas-sh", `is-${o.layout}`, o.tone === "dark" && "dark")} data-zas="shell"
        style={{ "--zas-sh-bg": navBackground(o.nav), "--zas-sh-w": `${o.width}px` } as React.CSSProperties}>
        {o.layout === "side" && (
          <aside className="zas-sh-side">
            {brand}
            {userAt === "side" && sideUser === "top" && <div className="zas-sh-foot top"><UserCard user={profileInfo} up={false} /></div>}
            {nav}
            {userAt === "side" && sideUser !== "top" && <div className="zas-sh-foot"><UserCard user={profileInfo} up /></div>}
          </aside>
        )}
        <div className="zas-sh-body">
          {showTop && (
            <header className="zas-sh-top" data-zas="shell-top">
              {o.layout === "top" ? <>{brand}{nav}</> : <h1 className="zas-sh-title">{title}</h1>}
              {userAt === "top" && <UserCard user={profileInfo} up={false} />}
            </header>
          )}
          <main ref={main} className="zas-sh-main">{children}</main>
        </div>
      </div>
    );
  }
  return ZasShell;
}
