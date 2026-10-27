// List tables in the Studio preview's design (toolbar → table → pager, and the record drawer),
// driven by the crud endpoints: server-side paging, sorting (order[0][column]/[dir]), search
// (search[value]), per-column filters (columns[i][search][value]) and quick filters (?qf=).
// Used by list pages and by 360 related tabs. Writes go through dialogs.tsx (crud FormRenderer).
//
// Why not CrudHandler: crud 2.0.0 renders its own header/toolbar/drawer (no inline select
// filters, no group_by or footer totals, a generic "#" drawer, and headerProps.customLeft/
// RightActions are not rendered). Its endpoints are reused unchanged.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, ChevronsUpDown, Download, EllipsisVertical, Inbox, Paperclip, Plus, Search } from "lucide-react";
import * as api from "./api";
import { SPEC, date, detailUrl, number, pageUrl, parentTabUrl, viewUrl } from "./config";
import { ConfirmDialog, FormDialog, useDialog } from "./dialogs";
import { Badge, Banner, Button, Chip, Drawer, EmptyState, Menu, Nil, Skeleton, Timeline, Value, cx, useToast } from "./ui";
import type { MenuItemDef } from "./ui";
import type { FieldValue, SpecColumn, SpecEntity } from "./types";

// ───────── data ─────────
type Meta = {
  columns: { name: string; sortable?: boolean; choices?: { id: string; label: string }[] | null }[];
  has_add_perm?: boolean; has_download_perm?: boolean;
  zas?: { quick_filters: { key: string; label: string; default: boolean }[]; filter_options?: Record<string, string[]> };
};
type Row = Record<string, any> & { object_uuid: string; zas?: { links: Record<string, string>; status?: string; tags?: string[]; hl?: Record<string, string> } };

const NA = (v: any) => v === null || v === undefined || v === "" || v === "NA";
const strip = (v: any) => (typeof v === "string" ? v.replace(/<[^>]*>/g, "").trim() : v);
const hrefOf = (v: any): string | null => (typeof v === "string" ? v.match(/href=['"]([^'"]+)['"]/)?.[1] || null : v?.url || null);

function useMeta(endpoint: string) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    setMeta(null);
    api.get(endpoint, { view: "table", action: "get_table_metadata" })
      .then((j) => { if (live) { const m = api.body(j)?.table_metadata; m ? setMeta(m) : setErr("This list could not be loaded."); } })
      .catch((e) => live && setErr(String(e?.message || e)));
    return () => { live = false; };
  }, [endpoint]);
  return { meta, err };
}

// ───────── cells ─────────
function Cell({ E, col, row, onOpen }: { E: SpecEntity; col: SpecColumn; row: Row; onOpen: (url: string) => void }) {
  const v = row[col.key];
  if (col.source === "status") {
    const code = row.zas?.status;
    const st = code ? E.statuses[code] : Object.values(E.statuses).find((s) => s.label === strip(v));
    return st ? <Badge label={st.label} tone={st.tone} /> : NA(strip(v)) ? <Nil /> : <>{strip(v)}</>;
  }
  if (col.source === "tags") {
    const codes = row.zas?.tags ?? [];
    if (!codes.length) return <Nil />;
    return <>{codes.map((c) => <Chip key={c} label={E.tags[c]?.label || c} tone={E.tags[c]?.tone} />)}</>;
  }
  if (NA(v)) return <Nil />;
  if (col.type === "file" || col.type === "image") {
    const url = hrefOf(v);
    if (!url) return <Nil />;
    const name = decodeURIComponent(url.split("/").pop() || "file");
    return <a className="zas-file zas-link" href={url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}><Paperclip />{name}</a>;
  }
  let text: React.ReactNode = strip(v);
  if (col.type === "date") text = date(strip(v));
  const ch = E.choices?.[col.key];
  if (ch) {
    const opt = Object.values(ch).find((c) => c.label === strip(v));
    if (opt?.tone) return <Badge label={opt.label} tone={opt.tone} />;
  }
  if (col.link_to) {
    // A plain column linking to a parent's 360 (an agreement's ID → request_360) opens the
    // parent, through the row's parent link; the row's own uuid would be the wrong record.
    const hero = SPEC.detail_views[col.link_to]?.hero;
    const up = Object.values(E.parents || {}).find((p) => p.hero === hero && p.fk)?.fk;
    const uuid = col.type === "link" ? row.zas?.links?.[col.key] : up ? row.zas?.links?.[up] : row.object_uuid;
    const url = uuid ? viewUrl(col.link_to, uuid) : null;
    if (url) return <a className="zas-link" href={url} onClick={(e) => { e.preventDefault(); e.stopPropagation(); onOpen(url); }}>{text}</a>;
  }
  return <>{text}</>;
}

// ───────── the table ─────────
export interface ZasTableProps {
  entity: string;
  endpoint: string;                         // the entity endpoint, plus ?<parent>=<uuid> on a 360 tab
  columns?: string[] | null;                // a 360 tab's subset; null = the list's columns
  rowClick?: string | null;                 // "drawer" | "none" | "preview" | a detail view code
  groupBy?: string | null;
  footer?: string[];
  empty?: { title?: string; text?: string; cta?: string } | null;
  addLabel?: string | null;                 // shows the primary Add button (and the empty-state CTA)
  addParams?: Record<string, string>;       // create-form params (the 360 parent preset)
  page?: { code: string; title: string } | null;  // list page: renders the page header
  pageSize?: number;
  onChanged?: () => void;                   // after any write (the 360 refreshes its header/stats)
  zasKey?: string;
  toolbar?: React.ReactNode;                // extra controls at the toolbar's right, before Export (a view switcher)
}

export function ZasTable(p: ZasTableProps) {
  const E = SPEC.entities[p.entity];
  const navigate = useNavigate();
  const toast = useToast();
  const dlg = useDialog();
  const { meta, err } = useMeta(p.endpoint);
  const [q, setQ] = useState("");
  const [dq, setDq] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [qf, setQf] = useState<string | null | undefined>(undefined);  // undefined = not chosen yet (use the default)
  const [sort, setSort] = useState<{ key: string; desc: boolean } | null>(null);
  const [pageNo, setPageNo] = useState(1);
  const ps = p.footer?.length ? 500 : (p.pageSize || 10);
  const [rows, setRows] = useState<Row[] | null>(null);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  // ?record=<uuid> opens that row's drawer: the way to a record with no 360 of its own (an
  // agreement on the request's tab) when it is not on the first page.
  const [drawer, setDrawer] = useState<string | null>(() => new URLSearchParams(window.location.search).get("record"));
  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => { const t = setTimeout(() => { setDq(q); setPageNo(1); }, 300); return () => clearTimeout(t); }, [q]);

  // columns: the spec's, in spec order, that the server sends for this role (column roles are applied there)
  const metaIdx = useMemo(() => new Map((meta?.columns || []).map((c, i) => [c.name, i])), [meta]);
  const cols = useMemo(() => {
    const keys = Array.isArray(p.columns) ? p.columns : null;
    const base = keys ? keys.map((k) => E.columns.find((c) => c.key === k)).filter(Boolean) as SpecColumn[] : E.columns;
    return meta ? base.filter((c) => metaIdx.has(c.key)) : base;
  }, [E, p.columns, meta, metaIdx]);
  const quick = meta?.zas?.quick_filters || [];
  const activeQf = qf === undefined ? (quick.find((x) => x.default)?.key ?? null) : qf;
  const filterCols = cols.filter((c) => c.filterable);

  useEffect(() => {
    if (!meta) return;
    let live = true;
    const params: Record<string, any> = { view: "table", action: "get_table_data", start: (pageNo - 1) * ps, length: ps };
    if (dq) params["search[value]"] = dq;
    Object.entries(filters).forEach(([k, v]) => {
      const i = metaIdx.get(k);
      if (v === "" || i === undefined) return;
      params[`columns[${i}][search][value]`] = v;
      params[`columns[${i}][searchable]`] = "true";
    });
    if (sort && metaIdx.has(sort.key)) {
      params["order[0][column]"] = metaIdx.get(sort.key);
      params["order[0][dir]"] = sort.desc ? "desc" : "asc";
    }
    if (activeQf) params.qf = activeQf;
    setBusy(true);
    api.get(p.endpoint, params)
      .then((j) => {
        if (!live) return;
        if (j?.success === false || !Array.isArray(j?.data)) { setLoadErr(api.body(j)?.message || "This list could not be loaded."); return; }
        setRows(j.data); setTotal(j.recordsFiltered ?? j.recordsTotal ?? j.data.length); setLoadErr(null);
      })
      .catch((e) => live && setLoadErr(String(e?.message || e)))
      .finally(() => live && setBusy(false));
    return () => { live = false; };
  }, [meta, p.endpoint, pageNo, ps, dq, filters, sort, activeQf, tick, metaIdx]);

  const changed = () => { refetch(); p.onChanged?.(); };
  const openAdd = () => dlg.open(
    <FormDialog spec={{ kind: "create", endpoint: E.endpoint, title: p.addLabel || E.add_button, params: p.addParams }}
      onClose={dlg.close} onDone={() => { dlg.close(); changed(); }} />);
  const canAdd = !!(p.addLabel && meta?.has_add_perm);

  const onRow = (r: Row) => {
    const rc = p.rowClick || E.row_click;
    if (!rc || rc === "none") return;
    if (rc === "preview" || E.field_links?.[rc]) {
      const field = E.field_links?.[rc] || E.field_links?.preview;
      const url = field ? hrefOf(r[field]) : null;
      if (url) { window.open(url, "_blank", "noopener"); return; }
    }
    if (rc.includes("#")) {
      // on that very tab (the request 360's Evidence tab listing evidence) the row opens its drawer
      const u = parentTabUrl(p.entity, rc, r.zas?.links);
      const here = window.location.pathname.replace(/\/$/, "");
      if (u && !here.endsWith(u.split("?")[0].replace(/\/$/, ""))) { navigate(u); return; }
    }
    const V = SPEC.detail_views[rc];
    if (V && V.hero === p.entity) { const u = viewUrl(rc, r.object_uuid); if (u) { navigate(u); return; } }
    setDrawer(r.object_uuid);
  };

  const rowMenu = (r: Row): MenuItemDef[] => (r.row_actions || []).map((a: any) => ({
    key: a.key, label: a.name, danger: a.key === "delete",
    onClick: () => runRowAction(a, r),
  }));
  const runRowAction = (a: any, r: Row) => {
    const nav = E.navigate?.[a.key];
    if (nav) { const u = SPEC.detail_views[nav] ? viewUrl(nav, r.object_uuid) : pageUrl(nav); if (u) navigate(u); return; }
    const field = E.field_links?.[a.key];
    if (field) { const u = hrefOf(r[field]); if (u) window.open(u, "_blank", "noopener"); else toast("No file attached", undefined, true); return; }
    if (a.type === "form") {
      dlg.open(<FormDialog spec={{ kind: "row", endpoint: E.endpoint, title: a.name, uuid: r.object_uuid, actionKey: a.key }}
        onClose={dlg.close} onDone={() => { dlg.close(); changed(); }} />);
      return;
    }
    const run = () => api.runRowAction(E.endpoint, r.object_uuid, a.key);
    if (E.downloads?.includes(a.key)) {
      run().then((res: any) => { const b = api.body(res) ?? {}; b?.url ? window.open(b.url, "_blank", "noopener") : toast(b?.message || "The file could not be generated.", undefined, true); });
      return;
    }
    dlg.open(<ConfirmDialog title={a.name} message={a.confirmation_message || `${a.name}?`} confirmLabel={a.name} danger={a.key === "delete"}
      run={run} onClose={dlg.close} onDone={() => { dlg.close(); changed(); }} />);
  };

  const exportRows = () => {
    const params: Record<string, any> = { view: "table", action: "export_table" };
    if (dq) params["search[value]"] = dq;
    Object.entries(filters).forEach(([k, v]) => { const i = metaIdx.get(k); if (v !== "" && i !== undefined) { params[`columns[${i}][search][value]`] = v; params[`columns[${i}][searchable]`] = "true"; } });
    if (activeQf) params.qf = activeQf;
    api.get(p.endpoint, params)
      .then((j) => toast(api.body(j)?.message || j?.message || "Export started. You will get the file shortly."))
      .catch((e) => toast("Export failed", String(e?.message || e), true));
  };

  const pages = Math.max(1, Math.ceil(total / ps));
  const filtered = !!(dq || activeQf || Object.values(filters).some(Boolean));
  const hasActs = (rows || []).some((r) => (r.row_actions || []).length);

  // group rows (within the page, like the preview)
  const body = useMemo(() => {
    if (!rows) return [];
    if (!p.groupBy) return [{ group: null as string | null, rows }];
    const g: Record<string, Row[]> = {};
    rows.forEach((r) => { const k = NA(strip(r[p.groupBy as string])) ? "—" : String(strip(r[p.groupBy as string])); (g[k] = g[k] || []).push(r); });
    return Object.entries(g).map(([group, rs]) => ({ group, rows: rs }));
  }, [rows, p.groupBy]);

  const addBtn = canAdd ? <Button variant="primary" icon={<Plus />} onClick={openAdd} zasKey="add">{p.addLabel}</Button> : null;
  const es = p.empty || {};

  return (
    <>
      {p.page && (
        <div className="zas-ph">
          <div><h1>{p.page.title}</h1><p>{rows ? `${number(total)} ${total === 1 ? "record" : "records"}` : " "}</p></div>
          <span className="zas-sp" />
          {addBtn}
        </div>
      )}
      <div className="zas-card" data-zas="panel" data-zas-key={p.zasKey || p.entity}>
        <div className="zas-tb">
          <label className="zas-search"><Search />
            <input placeholder={`Search ${E.plural.toLowerCase()}`} value={q} onChange={(e) => setQ(e.target.value)} aria-label={`Search ${E.plural}`} />
          </label>
          {filterCols.map((c) => <FilterSelect key={c.key} E={E} col={c} meta={meta} value={filters[c.key] || ""}
            onChange={(v) => { setFilters((f) => ({ ...f, [c.key]: v })); setPageNo(1); }} />)}
          {quick.length > 0 && (
            <div className="zas-chips" role="group" aria-label="Quick filters">
              {quick.map((x, i) => (
                <button key={x.key} type="button" className={cx("zas-qf", activeQf === x.key && "on")} aria-pressed={activeQf === x.key}
                  data-zas="quick-filter" data-zas-key={x.key} data-zas-order={i}
                  onClick={() => { setQf(activeQf === x.key ? null : x.key); setPageNo(1); }}>{x.label}</button>
              ))}
            </div>
          )}
          <span className="zas-sp" />
          {p.toolbar}
          {meta?.has_download_perm && !p.footer?.length && <Button icon={<Download />} onClick={exportRows} zasKey="export">Export</Button>}
          {!p.page && addBtn}
        </div>
        {err || loadErr ? <div style={{ padding: 14 }}><Banner tone="danger">{err || loadErr}</Banner></div>
          : rows === null ? <div style={{ padding: "8px 16px" }}><Skeleton lines={5} /></div>
          : rows.length === 0 ? (
            <EmptyState zasKey={p.zasKey || p.entity} icon={<Inbox />}
              title={filtered ? "No matching records" : es.title || `No ${E.plural.toLowerCase()} yet`}
              text={filtered ? "Try clearing the search or filters." : es.text}
              action={!filtered && canAdd && (es.cta === "add" || !p.page) ? addBtn : undefined} />
          ) : (
            <>
              <div className={cx("zas-tbl-w", busy && "busy")}>
                <table className="zas-t">
                  <thead><tr>
                    {cols.map((c) => {
                      const sortable = !!meta?.columns[metaIdx.get(c.key) ?? -1]?.sortable && c.source === "field" && !p.groupBy;
                      const on = sort?.key === c.key;
                      return <th key={c.key}>{sortable
                        ? <button type="button" className={cx("srt", on && "on")} onClick={() => { setSort(on ? (sort!.desc ? null : { key: c.key, desc: true }) : { key: c.key, desc: false }); setPageNo(1); }}>
                            {c.label}{on ? (sort!.desc ? <ArrowDown /> : <ArrowUp />) : <ChevronsUpDown />}</button>
                        : c.label}</th>;
                    })}
                    {hasActs && <th aria-label="Actions" />}
                  </tr></thead>
                  <tbody>
                    {body.map(({ group, rows: rs }) => (
                      <React.Fragment key={group ?? "_"}>
                        {group !== null && <tr className="grp"><td colSpan={cols.length + (hasActs ? 1 : 0)}>{group} · {rs.length}</td></tr>}
                        {rs.map((r) => (
                          <tr key={r.object_uuid} data-zas="row" data-zas-key={r.object_uuid} className={(p.rowClick || E.row_click) !== "none" ? "click" : undefined} onClick={() => onRow(r)}>
                            {cols.map((c) => <td key={c.key} className={r.zas?.hl?.[c.key] ? `hl-${r.zas.hl[c.key] === "amber" ? "amber" : "red"}` : undefined}>
                              <Cell E={E} col={c} row={r} onOpen={navigate} /></td>)}
                            {hasActs && <td className="act" onClick={(e) => e.stopPropagation()}>
                              {(r.row_actions || []).length > 0 && <Menu items={rowMenu(r)} trigger={(open) => (
                                <TriggerButton open={open} />)} />}
                            </td>}
                          </tr>
                        ))}
                      </React.Fragment>
                    ))}
                  </tbody>
                  {p.footer?.length ? (
                    <tfoot><tr>
                      {cols.map((c, i) => <td key={c.key} className="num">
                        {p.footer!.includes(c.key) ? number(rows.reduce((a, r) => a + (Number(strip(r[c.key])) || 0), 0)) : i === 0 ? "Total" : ""}</td>)}
                      {hasActs && <td />}
                    </tr></tfoot>
                  ) : null}
                </table>
              </div>
              {(pages > 1 || !p.footer?.length) && (
                <div className="zas-pg">
                  <span>Showing <b>{(pageNo - 1) * ps + 1}–{Math.min(total, pageNo * ps)}</b> of <b>{number(total)}</b></span>
                  <span className="zas-sp" />
                  <Button size="sm" icon={<ArrowLeft />} disabled={pageNo <= 1} onClick={() => setPageNo((n) => n - 1)}>Previous</Button>
                  <Button size="sm" disabled={pageNo >= pages} onClick={() => setPageNo((n) => n + 1)}>Next<ArrowRight /></Button>
                </div>
              )}
            </>
          )}
      </div>
      {drawer && <RecordDrawer entity={p.entity} uuid={drawer} onClose={() => setDrawer(null)} onChanged={changed} />}
      {dlg.dialog}
    </>
  );
}

/** The kebab must hold the ref Menu positions against, so it is a component of its own. */
function TriggerButton({ open }: { open: (anchor?: HTMLElement | null) => void }) {
  return <button type="button" className="zas-kebab" aria-label="Row actions" onClick={(e) => { e.stopPropagation(); open(e.currentTarget); }}><EllipsisVertical /></button>;
}

function FilterSelect({ E, col, meta, value, onChange }: { E: SpecEntity; col: SpecColumn; meta: Meta | null; value: string; onChange: (v: string) => void }) {
  const linkOpts = meta?.zas?.filter_options?.[col.key] || [];  // linked display values among this role's rows
  let opts: [string, string][] = [];
  if (col.source === "status") opts = Object.entries(E.statuses).map(([k, s]) => [k, s.label]);
  else if (E.choices?.[col.key]) opts = Object.entries(E.choices[col.key]).map(([k, c]) => [k, c.label]);
  else if (col.type === "link") opts = linkOpts.map((v) => [v, v]);
  else if (col.type === "boolean") opts = [["true", "Yes"], ["false", "No"]];
  else {
    const mc = meta?.columns.find((c) => c.name === col.key);
    opts = (mc?.choices || []).map((c) => [c.id, c.label]);
  }
  return (
    <select className="zas-sel" value={value} onChange={(e) => onChange(e.target.value)} aria-label={`Filter by ${col.label}`}
      data-zas="filter" data-zas-key={col.key}>
      <option value="">{col.label}: All</option>
      {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  );
}

// ───────── record drawer (the preview's .z-dw) ─────────
type RecordPayload = {
  access: "ok" | "no_access" | "not_found";
  record: { uuid: string; display: string; status: string | null; status_label?: string; status_tone?: string; tags: { code: string; label: string; tone?: string }[] };
  fields: FieldValue[];
  transitions: { name: string; engine_name: string; label: string; primary: boolean; tone?: string | null; confirm?: string | null; has_form: boolean; allowed: boolean; blocked_reason: string | null }[];
  tags: { code: string; label: string; state: "enabled" | "disabled"; allowed: boolean; has_form: boolean; confirm?: string | null; blocked_reason: string | null }[];
  row_actions: { key: string; label: string; type: string; spec_type?: string | null; confirm?: string | null }[];
  events: any[];
};

export function RecordDrawer({ entity, uuid, onClose, onChanged }: { entity: string; uuid: string; onClose: () => void; onChanged?: () => void }) {
  const E = SPEC.entities[entity];
  const navigate = useNavigate();
  const dlg = useDialog();
  const [d, setD] = useState<RecordPayload | null | { error: string }>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let live = true;
    api.get(E.endpoint, { action: "zas_record", object_uuid: uuid })
      .then((j) => live && setD(j?.success === false ? { error: api.body(j)?.message || "The record could not be loaded." } : api.body(j)))
      .catch((e) => live && setD({ error: String(e?.message || e) }));
    return () => { live = false; };
  }, [E.endpoint, uuid, tick]);
  const done = () => { dlg.close(); setTick((t) => t + 1); onChanged?.(); };

  if (!d) return <Drawer title={E.name} onClose={onClose}><div style={{ padding: 20 }}><Skeleton lines={8} /></div></Drawer>;
  if ("error" in d) return <Drawer title={E.name} onClose={onClose}><div style={{ padding: 20 }}><Banner tone="danger">{d.error}</Banner></div></Drawer>;
  if (d.access !== "ok") return <Drawer title={E.name} onClose={onClose}><EmptyState title={d.access === "no_access" ? "You don't have access to this record." : "This record no longer exists."} zasKey={d.access} /></Drawer>;

  const r = d.record;
  const go = (t: RecordPayload["transitions"][number]) => {
    if (!t.allowed) return;
    if (t.has_form) dlg.open(<FormDialog spec={{ kind: "transition", endpoint: E.endpoint, title: t.label, uuid, engineName: t.engine_name, danger: t.tone === "danger" }} onClose={dlg.close} onDone={done} />);
    else dlg.open(<ConfirmDialog title={t.label} message={t.confirm || `${t.label} this ${E.name.toLowerCase()}?`} confirmLabel={t.label} danger={t.tone === "danger"}
      run={() => api.runTransition(E.endpoint, uuid, t.engine_name)} onClose={dlg.close} onDone={done} />);
  };
  const more: MenuItemDef[] = [
    ...d.row_actions.filter((a) => !E.navigate?.[a.key] && !E.field_links?.[a.key]).map((a) => ({
      key: a.key, label: a.label, danger: a.key === "delete",
      onClick: () => a.type === "form"
        ? dlg.open(<FormDialog spec={{ kind: "row", endpoint: E.endpoint, title: a.label, uuid, actionKey: a.key }} onClose={dlg.close} onDone={done} />)
        : dlg.open(<ConfirmDialog title={a.label} message={a.confirm || `${a.label}?`} confirmLabel={a.label} danger={a.key === "delete"}
            run={() => api.runRowAction(E.endpoint, uuid, a.key)} onClose={dlg.close} onDone={() => { done(); if (a.key === "delete") onClose(); }} />),
    })),
    ...d.tags.map((tg) => {
      const state = tg.state === "enabled" ? "disabled" : "enabled";
      const label = (state === "enabled" ? "Mark as " : "Remove ") + tg.label;
      return {
        key: `tag_${tg.code}`, label, disabled: !tg.allowed, title: tg.blocked_reason || undefined, group: "Tags",
        onClick: () => tg.has_form
          ? dlg.open(<FormDialog spec={{ kind: "tag", endpoint: E.endpoint, title: label, uuid, tag: tg.code, state }} onClose={dlg.close} onDone={done} />)
          : dlg.open(<ConfirmDialog title={label} message={tg.confirm || `${label}?`} confirmLabel={label}
              run={() => api.runTag(E.endpoint, uuid, tg.code, state)} onClose={dlg.close} onDone={done} />),
      };
    }),
  ];
  const trs = [...d.transitions].sort((a, b) => Number(b.primary) - Number(a.primary));

  return (
    <Drawer title={r.display || `${E.name}`} onClose={onClose} subtitle={
      <p style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        {E.name}{r.status_label && <> · <Badge label={r.status_label} tone={r.status_tone} /></>}
        {r.tags.map((t) => <Chip key={t.code} label={t.label} tone={t.tone} />)}
      </p>}>
      {(trs.length > 0 || more.length > 0) && (
        <div className="zas-dw-acts">
          {trs.map((t) => (
            <Button key={t.name} size="sm" zasKey={t.name} zasTone={t.tone || undefined}
              variant={t.primary ? (t.tone === "danger" ? "danger-primary" : "primary") : t.tone === "danger" ? "danger" : "default"}
              disabled={!t.allowed} title={t.blocked_reason || undefined} onClick={() => go(t)}>{t.label}</Button>
          ))}
          {more.length > 0 && <Menu items={more} />}
        </div>
      )}
      <LinkedFields fields={d.fields} onOpen={(u) => { onClose(); navigate(u); }} />
      <div style={{ borderTop: "1px solid var(--z-bdf)" }}>
        <div className="zas-ng" style={{ padding: "14px 20px 0" }}>Activity</div>
        <Timeline events={d.events || []} />
      </div>
      {dlg.dialog}
    </Drawer>
  );
}

/** FieldGrid with linked records clickable (a link to an entity that has a 360 opens it). */
function LinkedFields({ fields, onOpen }: { fields: FieldValue[]; onOpen: (url: string) => void }) {
  return (
    <div className="zas-fields" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
      {fields.map((f) => {
        const url = f.type === "link" && f.uuid && f.entity ? detailUrl(f.entity, f.uuid) : null;
        return (
          <div className="zas-f" key={f.key} data-zas="field" data-zas-key={f.key}>
            <span>{f.label}</span>
            <div>{url ? <a className="zas-link" href={url} onClick={(e) => { e.preventDefault(); onOpen(url); }}>{f.display}</a>
              : <Value v={f} />}</div>
          </div>
        );
      })}
    </div>
  );
}
