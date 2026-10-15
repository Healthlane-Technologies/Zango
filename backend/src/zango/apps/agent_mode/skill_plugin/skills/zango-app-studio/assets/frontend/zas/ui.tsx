// Design-system components. Every page and slot composes from these; none carries
// its own colours. Each renders the data-zas attributes the design tests read
// (contracts §11).
import React, { createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useTableContext } from "@zango-core/crud/table";
import {
  ArrowRightLeft, CircleAlert, CircleCheck, CirclePlus, Copy, Ellipsis, History, Inbox, Info, Lock,
  OctagonAlert, Pencil, SearchX, Tag, TriangleAlert, X, Circle,
} from "lucide-react";
import { ICONS } from "./icons.gen";
import { SPEC, date, datetime, detailUrl, money, number, percent, relative, tone } from "./config";
import type { FieldValue } from "./types";

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

export function Icon({ name, className }: { name?: string | null; className?: string }) {
  const C = (name && (ICONS as Record<string, React.ComponentType<any>>)[name]) || Circle;
  return <C className={cx("zi", className)} aria-hidden="true" />;
}

// ───────── basics ─────────
type BtnProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "danger" | "danger-primary" | "ghost"; size?: "md" | "sm"; icon?: React.ReactNode; zasKey?: string; zasTone?: string;
};
export function Button({ variant = "default", size = "md", icon, children, className, zasKey, zasTone, ...rest }: BtnProps) {
  const v = { default: "", primary: "pri", danger: "danger", "danger-primary": "danger pri", ghost: "ghost" }[variant];
  return (
    <button type="button" className={cx("zas-btn", v, size === "sm" && "sm", className)} data-zas={zasKey ? "action" : undefined}
      data-zas-key={zasKey} data-zas-tone={zasTone} {...rest}>
      {icon}{children}
    </button>
  );
}

export function Badge({ label, tone: t, zasKey, dot = true }: { label: React.ReactNode; tone?: string | null; zasKey?: string; dot?: boolean }) {
  const tn = tone(t);
  return <span className={cx("zas-badge", `zt-${tn}`)} data-zas="badge" data-zas-key={zasKey} data-zas-tone={tn}>{dot && <i />}{label}</span>;
}

export function Chip({ label, tone: t, zasKey }: { label: React.ReactNode; tone?: string | null; zasKey?: string }) {
  const tn = tone(t);
  return <span className={cx("zas-chip", `zt-${tn}`)} data-zas="badge" data-zas-key={zasKey} data-zas-tone={tn}>{label}</span>;
}

export const Nil = () => <span className="zas-nil">—</span>;

export function Panel({ title, actions, children, zasKey, order, className, icon, note, kit }: {
  title?: React.ReactNode; actions?: React.ReactNode; children: React.ReactNode; zasKey?: string; order?: number; className?: string;
  /** Sketch kit: a header icon, a muted note on the right, and the kit block this panel draws (parity). */
  icon?: string; note?: React.ReactNode; kit?: string;
}) {
  return (
    <div className={cx("zas-panel", className)} data-zas="panel" data-zas-key={zasKey} data-zas-order={order}
      data-zas-kit={kit} data-zas-title={kit && typeof title === "string" ? title : undefined}>
      {title !== undefined && <h3>{icon && <Icon name={icon} />}{title}<span className="zas-sp" />{note && <span className="zas-knote">{note}</span>}{actions}</h3>}
      {children}
    </div>
  );
}

export function EmptyState({ title, text, icon, action, zasKey }: { title: string; text?: string; icon?: React.ReactNode; action?: React.ReactNode; zasKey?: string }) {
  return (
    <div className="zas-empty" data-zas="empty" data-zas-key={zasKey}>
      <div className="ei">{icon || <Inbox />}</div>
      <b>{title}</b>
      {text && <p>{text}</p>}
      {action}
    </div>
  );
}

export function StateBox({ kind, title, text, action }: { kind: "not_found" | "no_access" | "error"; title: string; text?: string; action?: React.ReactNode }) {
  const ic = { not_found: <SearchX />, no_access: <Lock />, error: <CircleAlert /> }[kind];
  return (
    <div className="zas-state" data-zas="empty" data-zas-key={kind}>
      <div className="ei">{ic}</div>
      <b>{title}</b>
      {text && <p style={{ margin: 0 }}>{text}</p>}
      {action && <div style={{ marginTop: 14 }}>{action}</div>}
    </div>
  );
}

export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => <div key={i} className="zas-skel" style={{ width: `${90 - i * 17}%` }} />)}
    </div>
  );
}

export function Banner({ tone: t = "info", children, order }: { tone?: string; children: React.ReactNode; order?: number }) {
  const ic = { warning: <TriangleAlert />, danger: <OctagonAlert />, success: <CircleCheck />, info: <Info /> }[t] || <Info />;
  return <div className={cx("zas-ban", t)} data-zas="banner" data-zas-tone={t} data-zas-order={order}>{ic}<div>{children}</div></div>;
}

// ───────── values ─────────
export function Value({ v, format }: { v: FieldValue | null | undefined; format?: string | null }) {
  if (!v || v.display === null || v.display === undefined || v.display === "") return <Nil />;
  const t = format || v.type;
  if (t === "status" || ((t === "choice" || t === "multi_choice") && v.tone)) return <Badge label={v.display} tone={v.tone} />;
  if (t === "tags") return <>{(v.items || []).map((x) => <Chip key={x.code} label={x.label} tone={x.tone} />)}</>;
  if (t === "money") return <span className="num">{money(v.value)}</span>;
  if (t === "percent") return <span className="num">{percent(v.value)}</span>;
  if (t === "integer" || t === "decimal") return <span className="num">{number(v.value)}</span>;
  if (t === "date") return <>{date(v.value)}</>;
  if (t === "datetime") return <>{datetime(v.value)}</>;
  if (t === "boolean") return <span className={v.value ? "zas-yes" : "zas-no"}>{v.value ? "Yes" : "No"}</span>;
  if ((t === "file" || t === "image") && v.url) return <a className="zas-link" href={v.url} target="_blank" rel="noreferrer">{v.display}</a>;
  if (t === "email") return <a className="zas-link" href={`mailto:${v.display}`}>{v.display}</a>;
  if (t === "url") return <a className="zas-link" href={String(v.value)} target="_blank" rel="noreferrer">{v.display}</a>;
  return <>{v.display}</>;
}

export function FieldGrid({ fields, columns = 2 }: { fields: FieldValue[]; columns?: number }) {
  return (
    <div className="zas-fields" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
      {fields.map((f) => (
        <div className="zas-f" key={f.key} data-zas="field" data-zas-key={f.key}>
          <span>{f.label}</span>
          <div><Value v={f} /></div>
        </div>
      ))}
    </div>
  );
}

export function StatTile({ label, value, format, tone: t, icon, computed, onClick, zasKey, order }: {
  label: string; value: number | null; format?: string; tone?: string | null; icon?: string; computed?: boolean;
  onClick?: () => void; zasKey?: string; order?: number;
}) {
  const tn = tone(t);
  const inner = (
    <>
      <div className="si"><Icon name={icon || "activity"} /></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <span>{label}</span>
        <b className={computed ? "comp" : undefined}>{value === null || value === undefined ? "—"
          : format === "money" ? money(value) : format === "percent" ? percent(value) : format === "days" ? `${value}d` : number(value)}</b>
      </div>
    </>
  );
  const attrs = { "data-zas": "stat", "data-zas-key": zasKey, "data-zas-tone": tn, "data-zas-order": order };
  return onClick
    ? <button type="button" className={cx("zas-stat click", `zt-${tn}`)} onClick={onClick} {...attrs}>{inner}</button>
    : <div className={cx("zas-stat", `zt-${tn}`)} {...attrs}>{inner}</div>;
}

export function Tabs({ tabs, current, onChange }: {
  tabs: { code: string; label: string; count?: number | null; tone?: string | null; icon?: string }[]; current: string; onChange: (c: string) => void;
}) {
  return (
    <div className="zas-tabs" role="tablist">
      {tabs.map((t, i) => (
        <button key={t.code} type="button" role="tab" aria-selected={t.code === current} className={cx("zas-tab", t.code === current && "on")}
          onClick={() => onChange(t.code)} data-zas="tab" data-zas-key={t.code} data-zas-order={i}>
          {t.icon && <Icon name={t.icon} />}{t.label}
          {t.count !== null && t.count !== undefined && (
            <span className={cx("zas-cnt", t.tone && `zt-${tone(t.tone)}`)} data-zas-tone={t.tone || undefined}>{t.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}

export function Timeline({ events, emptyText = "No activity yet" }: { events: any[]; emptyText?: string }) {
  if (!events.length) return <EmptyState title={emptyText} icon={<History />} zasKey="timeline" />;
  return (
    <div className="zas-tl">
      {events.map((e, i) => {
        let ic = <CirclePlus />, tn: string = "blue", bodyEl: React.ReactNode;
        const on = e.self ? "" : ` on ${String(e.entity_name || "").toLowerCase()} `;
        if (e.kind === "transition") {
          ic = <ArrowRightLeft />; tn = e.to?.tone || "indigo";
          bodyEl = <><b>{e.text}</b>{!e.self && <>{on}<b>{e.record}</b></>} · <Badge label={e.from?.label} tone={e.from?.tone} dot={false} /> → <Badge label={e.to?.label} tone={e.to?.tone} dot={false} /></>;
        } else if (e.kind === "tag") {
          ic = <Tag />; tn = e.tag?.tone || "gray";
          bodyEl = <>{e.on ? "Tagged " : "Removed tag "}<Chip label={e.tag?.label} tone={e.tag?.tone} />{!e.self && <> on <b>{e.record}</b></>}</>;
        } else if (e.kind === "updated") {
          ic = <Pencil />; tn = "gray";
          const ch = Object.entries(e.changes || {}).map(([k, v]: any) => `${k}: ${v?.[0] ?? "—"} → ${v?.[1] ?? "—"}`).join("; ");
          bodyEl = <>Updated {!e.self && <><b>{e.record}</b> · </>}<span>{ch}</span></>;
        } else {
          bodyEl = e.self ? <b>{e.entity_name} created</b> : <>{e.entity_name} <b>{e.record}</b> created</>;
        }
        return (
          <div className="zas-tli" key={i}>
            <div className={cx("zas-tld", `zt-${tone(tn)}`)}>{ic}</div>
            <div className="zas-tlb">{bodyEl}<div className="zas-tlm">{[e.actor, relative(e.t)].filter(Boolean).join(" · ")}</div>
              {e.note && <div className="zas-tln">{e.note}</div>}</div>
          </div>
        );
      })}
    </div>
  );
}

export function CopyButton({ text }: { text: string }) {
  const toast = useToast();
  return (
    <button type="button" className="zas-copy" title="Copy" aria-label="Copy" onClick={() => {
      navigator.clipboard?.writeText(text).then(() => toast("Copied", text), () => toast("Copy failed", "Select the text and copy it manually.", true));
    }}><Copy /></button>
  );
}

// ───────── overlays ─────────
export interface MenuItemDef { label: string; icon?: React.ReactNode; onClick?: () => void; danger?: boolean; disabled?: boolean; title?: string; group?: string; key?: string }

export function Menu({ items, trigger }: { items: MenuItemDef[]; trigger?: (open: (anchor?: HTMLElement | null) => void) => React.ReactNode }) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const open = (anchor?: HTMLElement | null) => {  // a custom trigger passes its own element
    const r = (anchor || btn.current)?.getBoundingClientRect();
    if (r) setPos({ x: Math.max(8, r.right - 220), y: r.bottom + 6 });
  };
  useEffect(() => {
    if (!pos) return;
    const close = () => setPos(null);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => { window.removeEventListener("scroll", close, true); window.removeEventListener("resize", close); };
  }, [pos]);
  if (!items.length) return null;
  return (
    <>
      {trigger ? trigger(open) : (
        <button ref={btn} type="button" className="zas-btn" style={{ padding: "0 10px" }} aria-label="More actions" onClick={() => open()}><Ellipsis /></button>
      )}
      {pos && createPortal(
        <div className="zas" onClick={() => setPos(null)} style={{ position: "fixed", inset: 0, zIndex: 59 }}>
          <div className="zas-pop" style={{ left: pos.x, top: pos.y }} onClick={(e) => e.stopPropagation()} role="menu">
            {items.map((it, i) => (
              <React.Fragment key={it.key || i}>
                {it.group && (i === 0 || items[i - 1].group !== it.group) && <div className="g">{it.group}</div>}
                <button type="button" role="menuitem" className={cx("zas-mi", it.danger && "danger")} disabled={it.disabled} title={it.title}
                  data-zas="action" data-zas-key={it.key}
                  onClick={() => { setPos(null); it.onClick?.(); }}>{it.icon}{it.label}</button>
              </React.Fragment>
            ))}
          </div>
        </div>, document.body)}
    </>
  );
}

export function Modal({ title, subtitle, icon, iconTone, wide, onClose, children, footer }: {
  title: string; subtitle?: string; icon?: React.ReactNode; iconTone?: string; wide?: boolean; onClose: () => void;
  children: React.ReactNode; footer?: React.ReactNode;
}) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return createPortal(
    <div className="zas">
      <div className="zas-mo-bg" onClick={onClose} />
      <div className={cx("zas-mo", wide && "wide")} role="dialog" aria-modal="true" aria-label={title}>
        <div className="zas-mo-h">
          {icon && <div className={cx("mi", iconTone && `zt-${tone(iconTone)}`)}>{icon}</div>}
          <div style={{ flex: 1, minWidth: 0 }}><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>
          <button type="button" className="zas-ib" onClick={onClose} aria-label="Close"><X /></button>
        </div>
        <div className="zas-mo-b">{children}</div>
        {footer && <div className="zas-mo-f">{footer}</div>}
      </div>
    </div>, document.body);
}

export function Drawer({ title, subtitle, onClose, children }: { title: string; subtitle?: React.ReactNode; onClose: () => void; children: React.ReactNode }) {
  return createPortal(
    <div className="zas">
      <div className="zas-dw-bg" onClick={onClose} />
      <aside className="zas-dw" role="dialog" aria-label={title}>
        <div className="zas-dw-h"><div style={{ flex: 1, minWidth: 0 }}><h2>{title}</h2>{subtitle}</div>
          <button type="button" className="zas-ib" onClick={onClose} aria-label="Close"><X /></button></div>
        <div className="zas-dw-b">{children}</div>
      </aside>
    </div>, document.body);
}

// ───────── toasts ─────────
type ToastFn = (title: string, msg?: string, error?: boolean) => void;
const ToastCtx = createContext<ToastFn>(() => undefined);
export const useToast = () => useContext(ToastCtx);

export function ToastHost({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<{ id: number; title: string; msg?: string; error?: boolean }[]>([]);
  const push = useCallback<ToastFn>((title, msg, error) => {
    const id = Date.now() + Math.random();
    setItems((x) => [...x, { id, title, msg, error }]);
    setTimeout(() => setItems((x) => x.filter((t) => t.id !== id)), error ? 6500 : 3200);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      {createPortal(
        <div className="zas zas-toasts" aria-live="polite">
          {items.map((t) => <div key={t.id} className={cx("zas-toast", t.error && "err")}><b>{t.error ? <CircleAlert /> : <CircleCheck />}{t.title}</b>{t.msg && <p>{t.msg}</p>}</div>)}
        </div>, document.body)}
    </ToastCtx.Provider>
  );
}

/** Collapses a header to one line once it scrolls out (spec: sticky header requirement). */
export function useStuck(ref: React.RefObject<HTMLElement | null>) {
  const [stuck, setStuck] = useState(false);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const sentinel = document.createElement("div");
    el.parentElement?.insertBefore(sentinel, el);
    const io = new IntersectionObserver(([e]) => setStuck(!e.isIntersecting));
    io.observe(sentinel);
    return () => { io.disconnect(); sentinel.remove(); };
  }, [ref]);
  return stuck;
}

/** The CrudHandler table context when rendered inside one, else null (the package exports only the throwing hook). */
export function useTableCtx(): any {
  try {
    return useTableContext();
  } catch {
    return null;
  }
}

// ───────── sketch kit ─────────
// The Studio preview's ctx.ui, as components with the same arguments, so a custom screen's
// `preview` sketch ports call for call (references/custom-code.md, "Porting a sketch"):
//   ctx.ui.stack(a, b)              → <Stack>{a}{b}</Stack>
//   ctx.ui.kpis([...])              → <Kpis items={[...]} />
//   ctx.ui.bars(title, items, o)    → <Bars title={title} items={items} {...o} />
//   ctx.ui.list(title, rows, o)     → <List title={title} rows={rows} {...o} />
//   ctx.ui.table(title, rows, c, o) → <MiniTable title={title} rows={rows} columns={c} {...o} />
//   ctx.ui.board(title, columns)    → <Board title={title} columns={columns} />
//   ctx.ui.progress(d, t, label)    → <Progress done={d} total={t} label={label} />
//   ctx.ui.panel / empty / badge    → <Panel kit="panel"> / <KitEmpty> / <KitBadge>
// Each block marks itself with data-zas-kit (and its title), the same markers the preview draws:
// the parity check compares the two trees (zas_test parity).

/** A sketch's `go`: "page" or "page:<id>" (a detail page opens that record), or a URL. */
export type Go = string | null | undefined;

export function goUrl(go: Go): string | null {
  if (!go) return null;
  if (go.startsWith("/")) return go;
  const [code, id] = go.split(":");
  const page = SPEC.pages[code];
  if (!page) return null;
  if (id && page.type === "detail" && page.entity) return detailUrl(page.entity, id) || page.route.replace(/:id\b/, id);
  return id ? page.route.replace(/:id\b/, id) : page.route;
}

function useGo(): (go: Go) => void {
  let navigate: ((to: string) => void) | null = null;
  try {
    navigate = useNavigate();  // the gallery renders without a router
  } catch {
    navigate = null;
  }
  return (go) => {
    const url = goUrl(go);
    if (url) (navigate ? navigate(url) : window.location.assign(url));
  };
}

const goProps = (go: Go, open: (g: Go) => void) =>
  go ? { onClick: () => open(go), role: "link" as const, tabIndex: 0, onKeyDown: (e: React.KeyboardEvent) => { if (e.key === "Enter") open(go); } } : {};

type Cell<R> = string | ((row: R) => React.ReactNode) | null | undefined;
type BadgeOf<R> = ((row: R) => { text: React.ReactNode; tone?: string | null } | null | undefined) | null | undefined;

function cellOf<R>(row: R, c: Cell<R>): React.ReactNode {
  if (typeof c === "function") return c(row);
  if (c == null) return "";
  const v = (row as any)?.[c];
  if (v && typeof v === "object" && "display" in v) return v.display ?? "—";  // a FieldValue from the API
  return v == null ? "" : String(v);
}

export function Stack({ children }: { children: React.ReactNode }) {
  return <div className="zas-kstack" data-zas-kit="stack">{children}</div>;
}

export function Grid({ children }: { children: React.ReactNode }) {
  return <div className="zas-kgrid" data-zas-kit="grid">{children}</div>;
}

export function KitEmpty({ text }: { text?: string }) {
  return <div className="zas-kempty">{text || "Nothing to show yet"}</div>;
}

export function KitBadge({ text, tone: t }: { text: React.ReactNode; tone?: string | null }) {
  return <span className={cx("zas-kbadge", `zt-${tone(t || "gray")}`)}>{text}</span>;
}

export interface Kpi { label: string; value: React.ReactNode; icon?: string; tone?: string | null; hint?: React.ReactNode; go?: Go; format?: "money" | "percent" | "number" }

export function Kpis({ items }: { items: Kpi[] }) {
  const open = useGo();
  const shown = (k: Kpi) => k.value === null || k.value === undefined ? "—"
    : typeof k.value === "number" ? (k.format === "money" ? money(k.value) : k.format === "percent" ? percent(k.value) : k.format === "number" ? number(k.value) : String(k.value))
    : k.value;
  return (
    <div className="zas-stats" style={{ marginTop: 0 }} data-zas-kit="kpis">
      {items.map((k, i) => (
        <div key={`${k.label}-${i}`} className={cx("zas-stat", k.go && "click", `zt-${tone(k.tone || "indigo")}`)} data-zas-item={k.label} {...goProps(k.go, open)}>
          <div className="si"><Icon name={k.icon || "activity"} /></div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <span>{k.label}</span>
            <b>{shown(k)}</b>
            {k.hint && <span className="zas-khint">{k.hint}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

export interface BarItem { label: React.ReactNode; value: number; display?: React.ReactNode; tone?: string | null; go?: Go }

export function Bars({ title, items, tone: t, empty, icon, note }: { title: string; items: BarItem[]; tone?: string | null; empty?: string; icon?: string; note?: React.ReactNode }) {
  const open = useGo();
  const top = Math.max(1, ...items.map((i) => Number(i.value) || 0));
  return (
    <Panel kit="bars" title={title} icon={icon} note={note}>
      {items.length ? (
        <div className="zas-kbody">
          {items.map((i, n) => (
            <div key={n} className={cx("zas-kbar", i.go && "click")} {...goProps(i.go, open)}>
              <span>{i.label}</span>
              <div className="zas-ktrack"><i className={`zt-${tone(i.tone || t || "indigo")}`} style={{ width: `${Math.round(((Number(i.value) || 0) / top) * 100)}%`, ["--kf" as any]: "var(--tf)" }} /></div>
              <b>{i.display ?? i.value}</b>
            </div>
          ))}
        </div>
      ) : <KitEmpty text={empty} />}
    </Panel>
  );
}

export function List<R>({ title, rows, primary, secondary, meta, badge, go, limit = 8, empty, note, icon }: {
  title: string; rows: R[]; primary: Cell<R>; secondary?: Cell<R>; meta?: Cell<R>; badge?: BadgeOf<R>; go?: (row: R) => Go;
  limit?: number; empty?: string; note?: React.ReactNode; icon?: string;
}) {
  const open = useGo();
  const items = rows.slice(0, limit);
  return (
    <Panel kit="list" title={title} icon={icon} note={note ?? (rows.length > items.length ? `${items.length} of ${rows.length}` : undefined)}>
      {items.length ? items.map((r, n) => {
        const g = go?.(r);
        const b = badge?.(r);
        return (
          <div key={n} className={cx("zas-kli", g && "click")} {...goProps(g, open)}>
            <div className="zas-kmain"><div>{cellOf(r, primary)}</div>{secondary && <div className="zas-ksub">{cellOf(r, secondary)}</div>}</div>
            {b && <KitBadge text={b.text} tone={b.tone} />}
            {meta && <span className="zas-kmeta">{cellOf(r, meta)}</span>}
          </div>
        );
      }) : <KitEmpty text={empty} />}
    </Panel>
  );
}

export interface MiniColumn<R> { label: string; value?: Cell<R>; align?: "left" | "right" | "center"; badge?: BadgeOf<R> }

export function MiniTable<R>({ title, rows, columns, go, limit = 10, empty, note, icon }: {
  title: string; rows: R[]; columns: MiniColumn<R>[]; go?: (row: R) => Go; limit?: number; empty?: string; note?: React.ReactNode; icon?: string;
}) {
  const open = useGo();
  const items = rows.slice(0, limit);
  return (
    <Panel kit="table" title={title} icon={icon} note={note}>
      {items.length ? (
        <div className="zas-tbl-w">
          <table className="zas-t">
            <thead><tr>{columns.map((c) => <th key={c.label} style={{ textAlign: c.align || "left" }} data-zas-item={c.label}>{c.label}</th>)}</tr></thead>
            <tbody>
              {items.map((r, n) => {
                const g = go?.(r);
                return (
                  <tr key={n} className={g ? "click" : undefined} {...goProps(g, open)}>
                    {columns.map((c) => {
                      const b = c.badge?.(r);
                      return <td key={c.label} style={{ textAlign: c.align || "left" }}>{c.badge ? (b ? <KitBadge text={b.text} tone={b.tone} /> : null) : cellOf(r, c.value)}</td>;
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : <KitEmpty text={empty} />}
    </Panel>
  );
}

export interface BoardColumn { title: React.ReactNode; tone?: string | null; items: { title: React.ReactNode; subtitle?: React.ReactNode; go?: Go }[] }

export function Board({ title, columns, note, icon }: { title: string; columns: BoardColumn[]; note?: React.ReactNode; icon?: string }) {
  const open = useGo();
  return (
    <Panel kit="board" title={title} icon={icon} note={note}>
      <div className="zas-kboard">
        {columns.map((c, n) => (
          <div key={n} className="zas-kcol">
            <h4>{c.tone ? <KitBadge text={c.title} tone={c.tone} /> : c.title} <span className="zas-kmuted">{c.items.length}</span></h4>
            {c.items.length ? c.items.map((i, k) => (
              <div key={k} className={cx("zas-kcard", i.go && "click")} {...goProps(i.go, open)}>
                {i.title}{i.subtitle && <span className="zas-kmuted">{i.subtitle}</span>}
              </div>
            )) : <span className="zas-kmuted">—</span>}
          </div>
        ))}
      </div>
    </Panel>
  );
}

export function Progress({ done, total, label }: { done: number; total: number; label?: React.ReactNode }) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <div className="zas-kprog" data-zas-kit="progress">
      <span>{label ?? `${done} of ${total} done`}</span>
      <div className="zas-ktrack"><i style={{ width: `${pct}%` }} /></div>
    </div>
  );
}
