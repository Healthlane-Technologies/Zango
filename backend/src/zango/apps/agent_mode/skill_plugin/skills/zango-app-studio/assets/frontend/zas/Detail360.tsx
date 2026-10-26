// The 360 page for one detail_view. Rendered by the hero list page's CrudHandler
// (customMainDetail) at <list route>/detail-view/<uuid>, or standalone by
// ZasDetailPage. Everything role- or condition-dependent arrives already filtered
// in data.zas (contracts §8); this component only lays it out.
import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, ArrowRightCircle, CircleX, Pencil, Tag as TagIcon, Zap } from "lucide-react";
import * as api from "./api";
import { SPEC, detailUrl, pageUrl, tone, viewUrl } from "./config";
import { ConfirmDialog, FormDialog, useDialog } from "./dialogs";
import { ZasTable } from "./ZasTable";
import * as SLOTS from "../custom/slots";
import {
  Badge, Banner, Button, CopyButton, EmptyState, FieldGrid, Icon, Menu, Panel, Skeleton, StatTile, StateBox, Tabs, Timeline, ToastHost, Value, cx, useStuck,
} from "./ui";
import type { DetailResponse, SpecTab, SpecView, ZasPayload } from "./types";
import type { MenuItemDef } from "./ui";

type Ctx = { view: SpecView; viewCode: string; zas: ZasPayload; endpoint: string; uuid: string; refresh: () => void; goTab: (c: string) => void };
const DetailCtx = createContext<Ctx | null>(null);
const useDetail = () => useContext(DetailCtx) as Ctx;

function Slot({ name, dataKey }: { name?: string; dataKey?: string | null }) {
  const d = useDetail();
  const C = name ? (SLOTS as Record<string, React.ComponentType<any>>)[name] : undefined;
  if (!C) return <EmptyState title="Custom panel not built yet" text={`Slot ${name} is missing from src/custom/slots.`} zasKey={name} />;
  return <C record={d.zas.record} zas={d.zas} data={dataKey ? d.zas.custom?.[dataKey] : undefined} refresh={d.refresh} api={api} />;
}

// ───────── header ─────────
function Header({ data }: { data: DetailResponse }) {
  const d = useDetail();
  const z = d.zas;
  const navigate = useNavigate();
  const dlg = useDialog();
  const ref = useRef<HTMLDivElement>(null);
  const stuck = useStuck(ref);
  const sticky = !!d.view.sticky_header;
  const hero = SPEC.entities[d.view.hero];

  const done = () => { dlg.close(); d.refresh(); };
  const runTransition = (t: ZasPayload["actions"]["transitions"][number]) => {
    if (!t.allowed) return;
    if (t.has_form) {
      dlg.open(<FormDialog spec={{ kind: "transition", endpoint: d.endpoint, title: t.label, uuid: d.uuid, engineName: t.engine_name, danger: t.tone === "danger" }}
        onClose={dlg.close} onDone={done} />);
    } else {
      dlg.open(<ConfirmDialog title={t.label} message={t.confirm || `${t.label} this ${hero.name.toLowerCase()}?`} confirmLabel={t.label}
        danger={t.tone === "danger"} run={() => api.runTransition(d.endpoint, d.uuid, t.engine_name)} onClose={dlg.close} onDone={done} />);
    }
  };
  const toggleTag = (tg: ZasPayload["actions"]["tags"][number]) => {
    const state = tg.state === "enabled" ? "disabled" : "enabled";
    const label = (state === "enabled" ? "Mark " : "Remove ") + tg.label;
    if (tg.has_form) {
      dlg.open(<FormDialog spec={{ kind: "tag", endpoint: d.endpoint, title: label, uuid: d.uuid, tag: tg.code, state }} onClose={dlg.close} onDone={done} />);
    } else {
      dlg.open(<ConfirmDialog title={label} message={tg.confirm || `${label}?`} confirmLabel={label}
        run={() => api.runTag(d.endpoint, d.uuid, tg.code, state)} onClose={dlg.close} onDone={done} />);
    }
  };
  const rowAction = (key: string, label: string, confirm?: string | null) => {
    const ra = (data.row_actions || []).find((r: any) => r.key === key);
    if (ra?.type === "form" || key === "edit") {
      dlg.open(<FormDialog spec={{ kind: "row", endpoint: d.endpoint, title: label, uuid: d.uuid, actionKey: key }} onClose={dlg.close} onDone={done} />);
    } else {
      const target = hero.navigate?.[key];
      if (target) {
        const url = SPEC.detail_views[target] ? viewUrl(target, d.uuid) : pageUrl(target);
        if (url) { navigate(url); return; }
      }
      dlg.open(<ConfirmDialog title={label} message={confirm || ra?.confirmation_message || `${label}?`} confirmLabel={label}
        danger={key === "delete"} run={() => api.runRowAction(d.endpoint, d.uuid, key)} onClose={dlg.close}
        onDone={(r) => { dlg.close(); if (key === "delete") navigate(pageUrl(d.view.back_to || "") || "/app"); else d.refresh(); if (r?.navigate) navigate(r.navigate); }} />);
    }
  };

  // primary transition + up to 2 others as buttons, the rest in the menu
  const trs = z.actions.transitions;
  const visible = [...trs.filter((t) => t.primary), ...trs.filter((t) => !t.primary)].slice(0, 3);
  const more: MenuItemDef[] = trs.filter((t) => !visible.includes(t)).map((t) => ({
    key: t.name, label: t.label, danger: t.tone === "danger", disabled: !t.allowed, title: t.blocked_reason || undefined,
    icon: t.tone === "danger" ? <CircleX /> : <ArrowRightCircle />, onClick: () => runTransition(t),
  }));
  const buttons: React.ReactNode[] = [];
  z.actions.buttons.forEach((b) => {
    if (b.type === "create_related" && b.entity) {
      const T = SPEC.entities[b.entity];
      buttons.push(<Button key={b.key} zasKey={b.key} icon={<Icon name={b.icon || "plus"} />} onClick={() => dlg.open(
        <FormDialog spec={{ kind: "create", endpoint: T.endpoint, title: b.label, params: b.param ? { [b.param]: d.uuid } : {} }}
          onClose={dlg.close} onDone={(r) => { dlg.close(); const u = r?.object_uuid && detailUrl(b.entity as string, r.object_uuid); if (u) navigate(u); else d.refresh(); }} />)}>{b.label}</Button>);
    } else if (b.type === "edit") {
      buttons.push(<Button key={b.key} zasKey={b.key} icon={<Pencil />} onClick={() => rowAction("edit", b.label || "Edit")}>{b.label || "Edit"}</Button>);
    } else if (b.type === "row_action" && b.row_action) {
      more.push({ key: b.key, label: b.label, icon: <Zap />, onClick: () => rowAction(b.row_action as string, b.label, b.confirm) });
    }
  });
  const listed = new Set(z.actions.buttons.map((b) => b.row_action || (b.type === "edit" ? "edit" : "")));
  z.actions.row_actions.filter((k) => !listed.has(k)).forEach((k) => {
    const ra = (data.row_actions || []).find((r: any) => r.key === k);
    if (!ra || hero.field_links?.[k]) return;
    more.push({ key: k, label: ra.name || k, icon: k === "edit" ? <Pencil /> : <Zap />, danger: k === "delete", group: "Actions", onClick: () => rowAction(k, ra.name || k) });
  });
  z.actions.tags.forEach((tg, i) => more.push({
    key: "tag:" + tg.code, group: i === 0 ? "Tags" : undefined, icon: <TagIcon />, disabled: !tg.allowed, title: tg.blocked_reason || undefined,
    label: (tg.state === "enabled" ? "Remove " : "Mark ") + tg.label, onClick: () => toggleTag(tg),
  }));

  const h = z.header;
  return (
    <div ref={ref} className={cx("zas-dhead", sticky && "sticky")} data-zas="header">
      <div className="zas-dtop">
        <div className="zas-av" style={stuck ? { width: 36, height: 36, fontSize: 13, borderRadius: 10 } : undefined}>
          {h.avatar.image ? <img src={h.avatar.image} alt="" /> : h.avatar.initials}
        </div>
        <div className="zas-dtt">
          <h1 data-zas="title">{h.title}</h1>
          {!stuck && h.subtitle && <div className="zas-dsub" data-zas="subtitle">{h.subtitle}</div>}
          {h.badges.length > 0 && (
            <div className="zas-dbadges">{h.badges.map((b) => b.kind === "tag"
              ? <span key={b.key} className={cx("zas-chip", `zt-${tone(b.tone)}`)} data-zas="badge" data-zas-key={b.key} data-zas-tone={tone(b.tone)}>{b.label}</span>
              : <Badge key={b.key} label={b.label} tone={b.tone} zasKey={b.key} />)}</div>
          )}
        </div>
        <div className="zas-dacts">
          {[...visible].reverse().map((t) => (
            <Button key={t.name} zasKey={t.name} zasTone={t.tone || undefined} disabled={!t.allowed} title={t.blocked_reason || undefined}
              variant={t.primary ? (t.tone === "danger" ? "danger-primary" : "primary") : t.tone === "danger" ? "danger" : "default"}
              icon={t.tone === "danger" ? <CircleX /> : <ArrowRightCircle />} onClick={() => runTransition(t)}>{t.label}</Button>
          ))}
          {buttons}
          <Menu items={more} />
        </div>
      </div>
      {!stuck && h.facts.length > 0 && (
        <div className="zas-dfacts">
          {h.facts.map((f) => (
            <div className="zas-dfact" key={f.key} data-zas="fact" data-zas-key={f.key} data-zas-order={f.order}>
              <span>{f.label}</span>
              <b className={f.emphasis ? "em" : undefined}>
                {f.link ? <a className="zas-link" onClick={() => { const u = viewUrl(f.link!.view, f.link!.uuid); if (u) navigate(u); }}>{f.display ?? "—"}</a>
                  : f.type ? <Value v={{ key: f.key, label: f.label, type: f.format || f.type, value: f.value, display: f.display }} /> : (f.display ?? "—")}
                {f.copy && f.display && <CopyButton text={String(f.value ?? f.display)} />}
              </b>
            </div>
          ))}
        </div>
      )}
      {!stuck && h.banners.map((b) => <Banner key={b.order} tone={b.tone} order={b.order}>{b.text}</Banner>)}
      {dlg.dialog}
    </div>
  );
}

// ───────── panels ─────────
function Panels({ list }: { list: ZasPayload["panels"][string] }) {
  const d = useDetail();
  const navigate = useNavigate();
  return (
    <>
      {list.map((p) => {
        if (p.type === "fields") {
          return <Panel key={p.key} title={p.title} zasKey={p.key} order={p.order}><FieldGrid fields={p.fields || []} columns={p.columns || (p.key.startsWith("sidebar") ? 1 : 2)} /></Panel>;
        }
        if (p.type === "mini_table") {
          const mt = d.zas.mini_tables[p.key];
          const T = mt && SPEC.entities[mt.entity];
          return (
            <Panel key={p.key} title={p.title} zasKey={p.key} order={p.order}
              actions={mt?.see_all_tab ? <button type="button" className="zas-link" onClick={() => d.goTab(mt.see_all_tab as string)}>See all <ArrowRight /></button> : undefined}>
              {!mt || !mt.rows.length ? <EmptyState title={`No ${T?.plural.toLowerCase() || "records"} yet`} zasKey={p.key} /> : (
                <table className="zas-t"><tbody>
                  {mt.rows.map((r) => {
                    const url = detailUrl(mt.entity, r.uuid);
                    return (
                      <tr key={r.uuid} className={url ? "click" : undefined} onClick={url ? () => navigate(url) : undefined}>
                        {Object.values(r.cells).map((c) => <td key={c.key}><Value v={c} /></td>)}
                      </tr>
                    );
                  })}
                </tbody></table>
              )}
            </Panel>
          );
        }
        if (p.type === "custom") {
          const slotName = d.view.sidebar.find((s) => s.key === p.key)?.slot
            || (SPEC.slots && Object.values(SPEC.slots).find((s) => s.data_key === p.key)?.export);
          return <Panel key={p.key} title={p.title} zasKey={p.key} order={p.order}><Slot name={slotName} dataKey={p.key} /></Panel>;
        }
        if (p.type === "timeline") return <Panel key={p.key} title={p.title} zasKey={p.key} order={p.order}><TimelineBlock limit={6} /></Panel>;
        return null;
      })}
    </>
  );
}

function TimelineBlock({ tab, limit }: { tab?: string; limit?: number }) {
  const d = useDetail();
  const [events, setEvents] = useState<any[] | null>(null);
  useEffect(() => {
    let live = true;
    api.fetchTimeline(d.endpoint, d.uuid, tab).then((r) => live && setEvents(r?.events || [])).catch(() => live && setEvents([]));
    return () => { live = false; };
  }, [d.endpoint, d.uuid, tab, d.zas]);
  if (events === null) return <div style={{ padding: 16 }}><Skeleton /></div>;
  return <Timeline events={limit ? events.slice(0, limit) : events} />;
}

// ───────── related tab: ZasTable on the child's endpoint, filtered by ?<param>=<hero uuid> ─────────
function RelatedTab({ tab, canAdd }: { tab: SpecTab; canAdd: boolean }) {
  const d = useDetail();
  const child = SPEC.entities[tab.entity as string];
  const endpoint = `${child.endpoint}?${tab.param}=${d.uuid}`;
  return (
    <ZasTable key={endpoint} entity={tab.entity as string} endpoint={endpoint} zasKey={tab.code}
      columns={Array.isArray(tab.columns) ? tab.columns : null}
      rowClick={tab.row_click || child.row_click} groupBy={tab.group_by || null} footer={tab.footer_totals || []}
      empty={tab.empty_state || null}
      addLabel={canAdd ? (tab.add?.label || `Add ${child.name}`) : null} addParams={{ [tab.param as string]: d.uuid }}
      onChanged={d.refresh} />
  );
}

// ───────── body ─────────
function TabBody({ tab, canAdd }: { tab: SpecTab; canAdd: boolean }) {
  const d = useDetail();
  if (tab.type === "related_table") return <RelatedTab tab={tab} canAdd={canAdd} />;
  if (tab.type === "timeline") return <Panel title={tab.label} zasKey={tab.code}><TimelineBlock tab={tab.code} /></Panel>;
  if (tab.type === "custom") return <Panel title={tab.label} zasKey={tab.code}><Slot name={tab.slot} dataKey={tab.code} /></Panel>;
  const list = d.zas.panels[tab.code] || [];
  if (!list.length) return <EmptyState title="Nothing to show here yet" zasKey={tab.code} />;
  return <Panels list={list} />;
}

function Page({ viewCode, uuid, initial }: { viewCode: string; uuid: string; initial?: DetailResponse }) {
  const view = SPEC.detail_views[viewCode];
  const hero = SPEC.entities[view.hero];
  const navigate = useNavigate();
  const [data, setData] = useState<DetailResponse | null>(initial?.zas ? initial : null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<string | null>(null);

  const load = useCallback(() => {
    api.fetchDetail(hero.endpoint, uuid).then((r) => { setData(r); setErr(null); }).catch((e) => setErr(String(e)));
  }, [hero.endpoint, uuid]);
  useEffect(() => { load(); }, [load]);

  const back = view.back_to && pageUrl(view.back_to);
  const backBtn = back ? <Button icon={<ArrowLeft />} onClick={() => navigate(back)}>Back to {SPEC.pages[view.back_to as string]?.title}</Button> : undefined;

  if (err) return <div className="zas zas-page"><StateBox kind="error" title="This page could not load" text={err} action={backBtn} /></div>;
  if (!data || !data.zas) return <div className="zas zas-page" aria-busy="true"><div className="zas-dhead"><Skeleton lines={4} /></div></div>;
  const z = data.zas;
  if (z.access === "not_found") {
    const nf = view.states?.not_found || {};
    return <div className="zas zas-page"><StateBox kind="not_found" title={nf.title || `${hero.name} not found`} text={nf.text || "It may have been removed or you may not have access."} action={backBtn} /></div>;
  }
  if (z.access === "no_access") {
    return <div className="zas zas-page"><StateBox kind="no_access" title="No access" text={view.states?.no_access?.text || `You don't have access to this ${hero.name.toLowerCase()}.`} action={backBtn} /></div>;
  }
  if (z.error) return <div className="zas zas-page"><StateBox kind="error" title="This page could not load" text={z.error} action={backBtn} /></div>;

  if (view.rebuild) {
    // open mode: the approved prototype screen, ported onto a slot over the same 360 payload
    const R = (SLOTS as Record<string, React.ComponentType<any>>)[view.rebuild];
    return (
      <DetailCtx.Provider value={{ view, viewCode, zas: z, endpoint: hero.endpoint, uuid, refresh: load, goTab: setTab }}>
        <div className="zas zas-page" data-zas="page" data-zas-key={view.page || viewCode} data-zas-rebuild={view.rebuild}>
          {R ? <R api={api} zas={z} record={z.record} refresh={load} />
            : <EmptyState title="This page is not built yet" text={`Add ${view.rebuild} to src/custom/slots.`} zasKey={viewCode} />}
        </div>
      </DetailCtx.Provider>
    );
  }
  const tabs = view.tabs.filter((t) => z.tabs.some((x) => x.code === t.code));
  const cur = tabs.find((t) => t.code === tab) || tabs[0];
  const counts = Object.fromEntries(z.tabs.map((t) => [t.code, t]));
  const ctx: Ctx = { view, viewCode, zas: z, endpoint: hero.endpoint, uuid, refresh: load, goTab: setTab };
  const side = z.panels.sidebar || [];
  const layout = view.layout || "header_tabs";
  const main = (
    <div style={{ minWidth: 0 }}>
      {tabs.length > 0 && <Tabs current={cur?.code || ""} onChange={setTab}
        tabs={tabs.map((t) => ({ code: t.code, label: t.label, icon: t.icon, count: counts[t.code]?.count, tone: counts[t.code]?.count_tone }))} />}
      {cur ? <TabBody key={cur.code} tab={cur} canAdd={!!counts[cur.code]?.can_add} /> : <EmptyState title="No tabs" />}
    </div>
  );
  const rail = side.length && layout !== "header_tabs" ? <div data-zas="rail" data-zas-layout={layout} style={{ minWidth: 0 }}><Panels list={side} /></div> : null;

  return (
    <DetailCtx.Provider value={ctx}>
      <div className="zas zas-page" data-zas="page" data-zas-key={view.page || viewCode} data-zas-layout={layout}>
        {back && <div className="zas-crumbs"><a onClick={() => navigate(back)}>{SPEC.pages[view.back_to as string]?.title}</a><span>/</span><b>{z.header.title}</b></div>}
        <Header data={data} />
        {z.stats.length > 0 && (
          <div className="zas-stats">
            {z.stats.map((s) => <StatTile key={s.key} zasKey={s.key} order={s.order} label={s.label} value={s.value} format={s.format}
              tone={s.tone || ["indigo", "teal", "amber", "pink", "blue", "purple"][s.order % 6]} icon={s.icon} computed={s.computed}
              onClick={s.tab && tabs.some((t) => t.code === s.tab) ? () => setTab(s.tab as string) : undefined} />)}
          </div>
        )}
        <div className={cx("zas-dbody", rail && (layout === "header_sidebar_tabs_left" ? "sl" : "sr"))}>
          {rail && layout === "header_sidebar_tabs_left" ? <>{rail}{main}</> : <>{main}{rail}</>}
        </div>
      </div>
    </DetailCtx.Provider>
  );
}

const detailComponents: Record<string, React.FC<any>> = {};
/** Stable component per view, for CrudHandler.customMainDetail (props are camelCase). */
export function getDetailComponent(viewCode: string): React.FC<any> {
  if (!detailComponents[viewCode]) {
    const C: React.FC<any> = ({ objectUuid, data }) => {
      const params = useParams();
      const uuid = objectUuid || params.object_uuid || params.id;
      if (!uuid) return null;
      return <Page key={uuid} viewCode={viewCode} uuid={uuid} initial={data} />;
    };
    C.displayName = `Detail_${viewCode}`;
    detailComponents[viewCode] = C;
  }
  return detailComponents[viewCode];
}

/** Standalone route (<route>/:id) for a detail page whose hero has no list page. */
export function makeDetailPage(pageCode: string): React.FC {
  const viewCode = SPEC.pages[pageCode]?.detail_view as string;
  const C: React.FC = () => {
    const params = useParams();
    // AppBuilder registers "<route>" and matches "<route>/*", so the id arrives in "*", not ":id"
    const tail = (params["*"] || "").split("/").filter(Boolean)[0];
    const last = window.location.pathname.split("/").filter(Boolean).pop();
    const uuid = params.id || params.object_uuid || tail || (last && /^[0-9a-f-]{32,36}$/i.test(last) ? last : undefined);
    return uuid ? <ToastHost><Page key={uuid} viewCode={viewCode} uuid={uuid} /></ToastHost> : null;
  };
  C.displayName = `Page_${pageCode}`;
  return C;
}
