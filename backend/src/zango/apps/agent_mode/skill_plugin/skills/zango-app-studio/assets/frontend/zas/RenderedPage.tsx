// A crud page drawn by zas-render.js, the file the Studio preview draws with: the same spec and the
// same rows give the same HTML as the approved preview (AGENT_MODE_SHARED_RENDERER_PLAN.html).
// React keeps the shell, routing and the dialogs; this file is the page's host: rows from the crud
// endpoint (server paging), clicks as API calls.
//
// The renderer is synchronous, so a draw is: render, collect what it asked for (metadata, a page of
// rows), fetch, render again, until it asks for nothing new; then the HTML goes on screen.
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import rawSpec from "../custom/spec.raw.json";
import * as api from "./api";
import { SPEC, pageUrl, viewUrl } from "./config";
import { ConfirmDialog, FormDialog, useDialog } from "./dialogs";
import { RecordDrawer } from "./ZasTable";
import { openAiClick } from "./ai";
import { useToast } from "./ui";

// Loaded on first use. The app build folds it into the one stylesheet anyway (cssCodeSplit: false),
// so kit.css is scoped to .zr-page / .zr-pop-root (zas_render.kit_css) to keep it off other pages.
let R: any = null;
let loading: Promise<void> | null = null;
const load = () => loading || (loading = Promise.all([
  import("./lucide.js"), import("./zas-render.js"), import("./kit.css"), import("./rendered.css"),
]).then(() => { R = (globalThis as any).ZasRender; }));
let MODEL: any = null;
/** The model the preview builds from the same spec (zas-render.js build()). */
const model = () => MODEL || (MODEL = R.build(rawSpec));

/** ?zas_renderer=shared|react picks the renderer for list pages (remembered); shared once P0 is verified. */
const DEFAULT_RENDERER: string = "react";
export function sharedRenderer(): boolean {
  try {
    const q = new URLSearchParams(window.location.search).get("zas_renderer");
    if (q) localStorage.setItem("zas.renderer", q);
    return (localStorage.getItem("zas.renderer") || DEFAULT_RENDERER) === "shared";
  } catch { return DEFAULT_RENDERER === "shared"; }
}

type Meta = {
  columns: { name: string; sortable?: boolean }[];
  has_add_perm?: boolean; has_download_perm?: boolean;
  zas?: { role?: string; quick_filters?: { key: string; label: string; count?: number | null }[];
    filter_options?: Record<string, string[]>; subtitle_stat?: number | null; stats?: Record<string, (number | null)[]> };
};
type Result = { rows: any[]; pageRows: any[]; total: number; count: (q: any) => number };
type Hooks = {
  navigate: (url: string) => void;
  toast: (title: string, msg?: string, error?: boolean) => void;
  dialog: (node: React.ReactNode) => void;
  closeDialog: () => void;
  drawer: (d: { entity: string; uuid: string } | null) => void;
};

const EMPTY: Result = { rows: [], pageRows: [], total: 0, count: () => 0 };
const slug = (s: any) => String(s ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "");
const strip = (v: any) => (typeof v === "string" ? v.replace(/<[^>]*>/g, "").trim() : v);
const endpointOf = (code: string) => SPEC.entities[code]?.endpoint;

/** The page's host for zas-render.js (the runtime half of the host contract; the kit's is memory()). */
class PageHost {
  preview = false;
  state: any;
  hooks!: Hooks;
  el: HTMLElement | null = null;
  private known = new Map<string, Map<string, any>>();  // entity → id (object_uuid) → row
  private metas = new Map<string, Meta>();
  private results = new Map<string, Result>();
  private last = new Map<string, Result>();             // a table's previous result while the next loads
  private totals = new Map<string, number>();
  private wants = new Map<string, () => Promise<void>>();
  private drawing = false;
  private again = false;
  private params: Record<string, Record<string, any>> = {};  // a table's last crud params (export)

  constructor(public pageCode: string) {}

  // ---- data -------------------------------------------------------------
  rows = (c: string) => [...(this.known.get(c)?.values() || [])].filter(Boolean);
  row = (c: string, id: any) => this.known.get(c)?.get(String(id));
  visible = (E: any) => this.rows(E.code);  // the server sent only what this role may see

  private remember(code: string, row: any) {
    if (!row) return;
    if (!this.known.has(code)) this.known.set(code, new Map());
    this.known.get(code)!.set(String(row.id), row);
  }

  private want(key: string, run: () => Promise<void>) { if (!this.wants.has(key)) this.wants.set(key, run); }

  meta(E: any): Meta | null {
    const ep = endpointOf(E.code);
    if (!ep) return null;
    const m = this.metas.get(ep);
    if (m) return m;
    this.want("meta:" + ep, async () => {
      const j = await api.get(ep, { view: "table", action: "get_table_metadata" });
      const meta: Meta = api.body(j)?.table_metadata || { columns: [] };
      this.metas.set(ep, meta);
      if (!this.state.role) this.state.role = this.specRole(meta.zas?.role);
    });
    return null;
  }

  /** The spec's name for the signed-in role (the server's may differ in case or punctuation). */
  private specRole(server?: string) {
    const roles: any[] = this.state.M.roles || [];
    return (roles.find((r) => r.name === server) || roles.find((r) => slug(r.name) === slug(server)) || roles[0] || {}).name || null;
  }

  private crudParams(st: any, meta: Meta, all: boolean, ps: number) {
    const idx = new Map(meta.columns.map((c, i) => [c.name, i]));
    const params: Record<string, any> = { view: "table", action: "get_table_data", zas_raw: 1,
      start: all ? 0 : (st.page - 1) * ps, length: all ? 500 : ps };
    if (st.q) params["search[value]"] = st.q;
    Object.entries(st.filters || {}).forEach(([k, v]: [string, any]) => {
      const i = idx.get(k);
      if (i === undefined || !R.filterOn(v)) return;
      params[`columns[${i}][search][value]`] = typeof v === "string" ? v : v.q != null ? v.q : JSON.stringify({ start: v.from, end: v.to });
      params[`columns[${i}][searchable]`] = "true";
    });
    if (st.sort) {
      const k = st.sort.replace(/^-/, "");
      if (idx.has(k)) { params["order[0][column]"] = idx.get(k); params["order[0][dir]"] = st.sort[0] === "-" ? "desc" : "asc"; }
    }
    const qf = st.qf && (meta.zas?.quick_filters || []).find((x) => x.label === st.qf);
    if (qf) params.qf = qf.key;
    return params;
  }

  query = (cfg: any, st: any): Result => {
    const E = cfg.E, ep = endpointOf(E.code), meta = this.meta(E);
    if (!meta || !ep) return EMPTY;
    // views (board, cards, calendar) and footer totals need every matching row, not one page
    const all = !!(cfg.view && cfg.view.type !== "table") || !!(cfg.footer && cfg.footer.length);
    const params = this.crudParams(st, meta, all, cfg.ps);
    this.params[cfg.key] = params;
    const key = ep + "?" + JSON.stringify(params);
    const hit = this.results.get(key);
    if (hit) {
      const pages = Math.max(1, Math.ceil(hit.total / cfg.ps));
      if (!all && st.page > pages) { st.page = pages; return this.query(cfg, st); }
      this.last.set(cfg.key, hit);
      return hit;
    }
    this.want(key, async () => {
      const j = await api.get(ep, params);
      if (j?.success === false || !Array.isArray(j?.data)) throw new Error(api.body(j)?.message || "This list could not be loaded.");
      const rel = (j.data[0]?.zas?.rel || {}) as Record<string, Record<string, any>>;
      Object.entries(rel).forEach(([code, byId]) => Object.values(byId).forEach((r) => this.remember(code, r)));
      const rows = j.data.map((d: any) => ({ ...(d.zas?.raw || { id: d.object_uuid }), _z: d.zas || {}, _crud: d }));
      rows.forEach((r: any) => this.remember(E.code, r));
      const counts = new Map((meta.zas?.quick_filters || []).map((x) => [x.label, x.count ?? 0]));
      const total = j.recordsFiltered ?? j.recordsTotal ?? rows.length;
      this.totals.set(E.code, j.recordsTotal ?? total);
      this.results.set(key, {
        rows, pageRows: all ? rows.slice((st.page - 1) * cfg.ps, st.page * cfg.ps) : rows, total,
        count: (q: any) => (q ? counts.get(q.label) ?? 0 : this.totals.get(E.code) ?? 0),
      });
    });
    return this.last.get(cfg.key) || EMPTY;
  };

  stat = (E: any, _rows: any[], def: any) => {
    const meta = this.meta(E);
    if (!def) return this.totals.get(E.code) ?? 0;
    if (!meta) return 0;
    for (const p of Object.values<any>(this.state.M.pages)) {
      if (p.type !== "crud" || p.entity !== E.code) continue;
      if (p.subtitle && p.subtitle.stat === def) return meta.zas?.subtitle_stat ?? 0;
      const i = (p.stats || []).indexOf(def);
      if (i >= 0) return meta.zas?.stats?.[p.code]?.[i] ?? 0;
    }
    return 0;
  };

  computed = (_E: any, row: any, c: any) => {
    const v = strip(row._crud?.[c.key]);
    if (v === undefined || v === null || v === "" || v === "NA") return null;
    if (["money", "percent", "number", "integer"].includes(c.format)) { const n = Number(String(v).replace(/[^0-9.-]/g, "")); return isNaN(n) ? v : n; }
    return v;
  };

  // what the server already worked out for the row (table.columns[] badge / highlight / secondary / icon)
  fact = (kind: string, _E: any, row: any, c: any) => {
    const z = row._z || {};
    if (kind === "badge") return !!z.badge?.[c.key];
    if (kind === "highlight") return !!z.hl?.[c.key];
    if (kind === "secondary") return z.sub?.[c.key] || "";
    if (kind === "icon") return z.icon?.[c.key] || null;
    return null;
  };

  // a link column's filter: the linked records' display values among this role's rows (the server's)
  options = (E: any, c: any) => {
    const ep = endpointOf(E.code);
    const meta = ep ? this.metas.get(ep) : null;
    return (meta?.zas?.filter_options?.[c.key] || []).map((v) => [v, v]);
  };

  // ---- clicks -------------------------------------------------------------
  act = (name: string, p: any = {}): void => {
    const h = this.hooks;
    const ep = p.E ? endpointOf(p.E.code) : null;
    const done = () => { h.closeDialog(); this.invalidate(); this.draw(); };
    switch (name) {
      case "render": return void this.draw();
      case "go": return void this.go(p.page, p.id, p.tab);
      case "drawer": return h.drawer({ entity: p.E.code, uuid: String(p.row.id) });
      case "create":
        return h.dialog(<FormDialog spec={{ kind: "create", endpoint: ep!, title: p.title || SPEC.entities[p.E.code]?.add_button || `Add ${p.E.name}` }}
          onClose={h.closeDialog} onDone={done} />);
      case "export": {
        const params = { ...(this.params["crud_" + p.E.code] || {}), action: "export_table" };
        delete (params as any).start; delete (params as any).length; delete (params as any).zas_raw;
        return void api.get(ep!, params)
          .then((j) => h.toast(api.body(j)?.message || j?.message || "Export started. You will get the file shortly."))
          .catch((e) => h.toast("Export failed", String(e?.message || e), true));
      }
      case "menu": return this.menu(p.anchor, p.items);
      case "ai": {  // an AI helper from a row menu or the list header (zas-render.js aiClicks)
        const t = p.trigger || {}, a = p.agent || {};
        const click: api.AiClick = { agent: a.code, name: a.name || a.code, event: t.event, kind: a.output?.kind || "text",
          label: t.label || (t.event === "chat" ? "Ask AI" : a.name || a.code), icon: t.icon || "sparkles" };
        return openAiClick(click, { endpoint: ep!, where: t.where || "record", uuid: p.row ? String(p.row.id) : undefined,
          uuids: p.rows ? p.rows.map((r: any) => String(r.id)) : undefined, open: h.dialog, close: h.closeDialog,
          onDone: () => { this.invalidate(); void this.draw(); } });
      }
      case "edit":
        return h.dialog(<FormDialog spec={{ kind: "row", endpoint: ep!, title: `Edit ${p.E.name}`, uuid: String(p.row.id), actionKey: "edit" }}
          onClose={h.closeDialog} onDone={done} />);
      case "delete":
        return h.dialog(<ConfirmDialog title={`Delete ${p.E.name}`} message="This can't be undone." confirmLabel="Delete" danger
          run={() => api.runRowAction(ep!, String(p.row.id), "delete")} onClose={h.closeDialog} onDone={done} />);
      case "row_action": return this.rowAction(p.E, p.row, p.a, done);
      case "transition": return void this.workflow(p.E, p.row, (z) => {
        const t = z.actions.transitions.find((x: any) => x.name === p.t.name);
        if (!t) return h.toast(`${p.t.label} is not available`, undefined, true);
        h.dialog(t.has_form
          ? <FormDialog spec={{ kind: "transition", endpoint: ep!, title: t.label, uuid: String(p.row.id), engineName: t.engine_name, danger: t.tone === "danger" }} onClose={h.closeDialog} onDone={done} />
          : <ConfirmDialog title={t.label} message={t.confirm || `${t.label}?`} confirmLabel={t.label} danger={t.tone === "danger"}
            run={() => api.runTransition(ep!, String(p.row.id), t.engine_name)} onClose={h.closeDialog} onDone={done} />);
      });
      case "tag": return void this.workflow(p.E, p.row, (z) => {
        const state = p.on ? "enabled" : "disabled";
        const tg = z.actions.tags.find((x: any) => x.code === p.tag.code);
        if (!tg) return h.toast(`${p.tag.label} is not available`, undefined, true);
        h.dialog(tg.has_form
          ? <FormDialog spec={{ kind: "tag", endpoint: ep!, title: tg.label, uuid: String(p.row.id), tag: tg.code, state }} onClose={h.closeDialog} onDone={done} />
          : <ConfirmDialog title={tg.label} message={tg.confirm || `${tg.label}?`} confirmLabel={p.on ? "Mark" : "Remove"}
            run={() => api.runTag(ep!, String(p.row.id), tg.code, state)} onClose={h.closeDialog} onDone={done} />);
      });
    }
  };

  private go(page: string, id?: any, tab?: string) {
    const P = this.state.M.pages[page];
    const url = P && P.type === "detail" && id != null ? viewUrl(P.detail_view, String(id), tab) : pageUrl(page);
    if (url) this.hooks.navigate(url);
  }

  /** The record's workflow actions as the server allows them (engine names, forms), then run(). */
  private async workflow(E: any, row: any, run: (z: any) => void) {
    try {
      const d = await api.fetchDetail(endpointOf(E.code), String(row.id));
      if (d?.zas) run(d.zas); else this.hooks.toast("This record could not be loaded", undefined, true);
    } catch (e: any) { this.hooks.toast("This record could not be loaded", String(e?.message || e), true); }
  }

  private rowAction(E: any, row: any, a: any, done: () => void): void {
    const h = this.hooks, ep = endpointOf(E.code)!, uuid = String(row.id), U = SPEC.entities[E.code];
    if (a.type === "edit") return this.act("edit", { E, row });
    if (a.type === "navigate") {
      const to = a.to;
      if (to && typeof to === "object" && to.field) {
        const href = String(row._crud?.[to.field] || "").match(/href=['"]([^'"]+)['"]/)?.[1];
        return href ? void window.open(href, "_blank", "noopener") : h.toast("No file attached", undefined, true);
      }
      const dv = this.state.M.dvs[to];
      return dv && dv.page ? this.go(dv.page.code, uuid) : this.go(to);
    }
    if (a.type === "form") {
      return h.dialog(<FormDialog spec={{ kind: "row", endpoint: ep, title: a.label, uuid, actionKey: a.key }} onClose={h.closeDialog} onDone={done} />);
    }
    const run = () => api.runRowAction(ep, uuid, a.key);
    if (a.type === "download" || U?.downloads?.includes(a.key)) {
      return void run().then((res: any) => { const b = api.body(res) ?? {}; b?.url ? window.open(b.url, "_blank", "noopener") : h.toast(b?.message || "The file could not be generated.", undefined, true); });
    }
    h.dialog(<ConfirmDialog title={a.label} message={a.confirm || `${a.label}?`} confirmLabel={a.label}
      run={run} onClose={h.closeDialog} onDone={done} />);
  }

  // the row menu: the renderer's markup, placed as the kit places it (under the button, flipped up near the bottom)
  private pop: HTMLDivElement | null = null;
  closeMenu = () => { if (this.pop) this.pop.innerHTML = ""; };
  private menu(anchor: HTMLElement, items: any[]) {
    if (!R) return;
    if (!this.pop) { this.pop = document.createElement("div"); this.pop.className = "zr-pop-root"; document.body.appendChild(this.pop); R.bind(this.pop); }
    const r = anchor.getBoundingClientRect();
    this.pop.innerHTML = R.menuHTML(items, this.closeMenu);
    const el = this.pop.firstElementChild as HTMLElement;
    const w = 230; const top = r.bottom + 4;
    el.style.left = Math.max(8, Math.min(window.innerWidth - w - 10, r.right - w)) + "px"; el.style.top = top + "px"; el.style.minWidth = w + "px";
    R.paintIcons();
    const hh = el.getBoundingClientRect().height;
    if (top + hh > window.innerHeight - 8) el.style.top = Math.max(8, r.top - hh - 4) + "px";
  }

  // ---- drawing ------------------------------------------------------------
  invalidate() { this.results.clear(); this.metas.clear(); }

  async draw(): Promise<void> {
    if (this.drawing) { this.again = true; return; }
    this.drawing = true;
    try {
      await load();
      if (!this.state) this.state = { M: model(), role: null, users: {}, me: {}, ui: { tables: {}, drawer: null }, views: {} };
      for (let pass = 0; pass < 6; pass++) {
        this.wants.clear();
        R.use(this); R.resetActs();
        const html = this.renderOnce();
        if (!this.wants.size) { this.paint(html); return; }
        await Promise.all([...this.wants.values()].map((run) => run().catch((e) => this.hooks.toast("Could not load", String(e?.message || e), true))));
      }
    } finally {
      this.drawing = false;
      if (this.again) { this.again = false; void this.draw(); }
    }
  }

  private renderOnce(): string {
    const M = this.state.M, p = M.pages[this.pageCode], E = p && M.ents[p.entity];
    if (!E) return R.stateBox("compass", "Nothing to show", `No page ${this.pageCode} in the spec.`);
    return R.renderCrud(E, p);
  }

  // as the kit's render(): the field being typed in keeps its focus and caret
  private paint(html: string) {
    if (!this.el) return;
    const act = document.activeElement as HTMLInputElement | null;
    const fid = act && act.id, sel = act && act.selectionStart;
    this.closeMenu();
    this.el.innerHTML = html;
    R.paintIcons();
    if (fid) { const el = document.getElementById(fid) as HTMLInputElement | null; if (el) { el.focus(); try { if (sel != null) el.setSelectionRange(sel, sel); } catch { /* not a text field */ } } }
  }
}

/** A crud page body drawn by the shared renderer, inside the React shell. */
export function RenderedCrud({ pageCode }: { pageCode: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const toast = useToast();
  const dlg = useDialog();
  const [drawer, setDrawer] = useState<{ entity: string; uuid: string } | null>(null);
  const host = useRef<PageHost | null>(null);
  if (!host.current) host.current = new PageHost(pageCode);
  host.current.hooks = { navigate, toast, dialog: dlg.open, closeDialog: dlg.close, drawer: setDrawer };
  useEffect(() => {
    const h = host.current!;
    h.el = ref.current;
    void load().then(() => { if (h.el) R.bind(h.el); });
    const outside = (e: MouseEvent) => { if (!(e.target as HTMLElement).closest?.(".z-pop, [data-a]")) h.closeMenu(); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") h.closeMenu(); };
    document.addEventListener("click", outside);
    document.addEventListener("keydown", esc);
    void h.draw();
    return () => { h.el = null; h.closeMenu(); document.removeEventListener("click", outside); document.removeEventListener("keydown", esc); };
  }, []);
  return (
    <div className="zapp zr-page" data-zas="page" data-zas-key={pageCode} data-zas-renderer="shared">
      <div className="z-content" ref={ref} />
      {dlg.dialog}
      {drawer && <RecordDrawer entity={drawer.entity} uuid={drawer.uuid} onClose={() => setDrawer(null)}
        onChanged={() => { host.current!.invalidate(); void host.current!.draw(); }} />}
    </div>
  );
}
