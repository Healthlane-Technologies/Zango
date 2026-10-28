// Component gallery at /app/__zas: every component in every state, with FIXED
// fixture data and the default brand, so its screenshots are identical in every app.
// The design tests compare it against the skill's golden screenshots (testing.md).
//
// /app/__zas?kit=mockup is the app's kit instead (open mode): every piece src/custom/kit/map.json
// names, drawn by the app's kit with the props the map gives, so zas_test.design --only kit can shoot
// it next to the same piece cropped from the approved prototype. &piece=<id> draws one piece, &w=<px>
// sets its width (the crop's). An internal check page; the default gallery stays pinned to ./ui.
import { useLayoutEffect, useState, type CSSProperties } from "react";
import { Plus, Pencil } from "lucide-react";
import { FMT, TONES } from "./config";
import {
  Badge, Banner, Bars, Board, Button, Chip, EmptyState, FieldGrid, Grid, Icon, Kpis, List, MiniTable, Panel, Progress, Skeleton, Stack,
  StatTile, StateBox, Tabs, Timeline, ToastHost,
} from "./ui";
import type { FieldValue } from "./types";
import * as KIT from "./kit";
import kitMap from "../custom/kit/map.json";

// The goldens are drawn with the default app.ui (rounded, comfortable), whatever the app chose.
const GALLERY_DEFAULTS = {
  "--z-r-card": "12px", "--z-r-head": "14px", "--z-r-ctl": "8px", "--z-ctl-h": "36px",
  "--z-cell-y": "11px", "--z-th-y": "10px", "--z-page-pad": "24px 28px 48px",
} as CSSProperties;

const FIELDS: FieldValue[] = [
  { key: "legal_name", label: "Legal name", type: "text", value: "Apex Industries Pvt Ltd", display: "Apex Industries Pvt Ltd" },
  { key: "risk", label: "Risk rating", type: "choice", value: "low", display: "Low", tone: "green" },
  { key: "credit", label: "Credit limit", type: "money", value: 1000000, display: "1000000" },
  { key: "approved_on", label: "Approved on", type: "date", value: "2026-10-02", display: "2026-10-02" },
  { key: "active", label: "Active", type: "boolean", value: true, display: "Yes" },
  { key: "empty", label: "Empty value", type: "text", value: null, display: null },
];
const EVENTS = [
  { kind: "transition", self: true, text: "Approve", from: { label: "Pending Approval", tone: "amber" }, to: { label: "Approved", tone: "green" }, actor: "Meera Iyer", t: "2026-10-02T10:00:00Z", note: "risk rating: low" },
  { kind: "tag", self: true, on: true, tag: { label: "MSME", tone: "teal" }, actor: "Rohan Mehta", t: "2026-10-01T09:00:00Z" },
  { kind: "updated", self: true, changes: { "Payment terms": ["Net 60", "Net 30"] }, actor: "Rohan Mehta", t: "2026-09-30T09:00:00Z" },
  { kind: "created", self: true, entity_name: "Vendor", actor: "Rohan Mehta", t: "2026-09-29T09:00:00Z" },
];

// The sketch kit (custom screens ported from their preview sketch), with fixed rows.
const POS = [
  { po: "PO-00412", vendor: "Apex Industries", amount: "$48,000", status: "Pending", tone: "amber" },
  { po: "PO-00409", vendor: "Northwind Traders", amount: "$12,500", status: "Approved", tone: "green" },
  { po: "PO-00401", vendor: "Globex Supplies", amount: "$7,900", status: "Rejected", tone: "red" },
];

// fixed formats and clock while the gallery is mounted (set before children render, cleared on unmount)
const PINNED = { locale: "en-US", currency: "USD", now: Date.parse("2026-10-08T09:00:00Z") };

type KitEntry = { id: string; component: string; props?: Record<string, any>; built?: string };

const noop = () => undefined;
// pieces whose icon prop is an element: map.json gives a lucide name
const ICON_ELEMENT = new Set(["Button", "EmptyState", "Modal"]);

function kitProps(p: KitEntry): Record<string, any> {
  const props = { ...(p.props || {}) };
  if (ICON_ELEMENT.has(p.component) && typeof props.icon === "string") props.icon = <Icon name={props.icon} />;
  return props;
}

function KitGallery({ only, width }: { only: string | null; width: number | null }) {
  const pieces = (((kitMap as any).pieces || []) as KitEntry[]).filter((p) => !only || p.id === only);
  return (
    <ToastHost>
      <div className="zas zas-page" data-zas="page" data-zas-key="__zas_kit" data-kit-count={pieces.length}>
        {!only && <div className="zas-ph"><div><h1>App kit</h1><p>Each piece of src/custom/kit/map.json, drawn by this app's kit.</p></div></div>}
        {pieces.map((p) => {
          const C = (KIT as Record<string, any>)[p.component];
          const ok = typeof C === "function" && p.component !== "makeShell";
          return (
            <section key={p.id} data-kit-piece={p.id} data-kit-component={p.component} style={{ marginBottom: only ? 0 : 24 }}>
              {!only && <div style={{ fontSize: 12, marginBottom: 6 }}>{p.id} · {p.component}</div>}
              <div data-kit-body={p.id} style={width ? { width } : undefined}>
                {ok ? <C onClose={noop} onChange={noop} {...kitProps(p)} /> : <span data-kit-error="">no kit piece {p.component}</span>}
              </div>
            </section>
          );
        })}
      </div>
    </ToastHost>
  );
}

export default function ZasGallery() {
  const q = new URLSearchParams(window.location.search);
  if (q.get("kit") === "mockup") {
    const w = parseInt(q.get("w") || "", 10);
    return <KitGallery only={q.get("piece")} width={Number.isFinite(w) && w > 0 ? w : null} />;
  }
  return <DefaultGallery />;
}

function DefaultGallery() {
  const [tab, setTab] = useState("one");
  Object.assign(FMT, PINNED);
  useLayoutEffect(() => () => { delete FMT.locale; delete FMT.currency; delete FMT.now; }, []);
  return (
    <ToastHost>
      <div className="zas zas-page" data-zas="page" data-zas-key="__zas" data-zas-pinned="" style={{ ["--brand" as any]: "#4F46E5", ...GALLERY_DEFAULTS }}>
        <div className="zas-ph"><div><h1>Design system</h1><p>Every component and state, with fixed sample data.</p></div></div>
        <div data-gallery="badges" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          {TONES.map((t) => <Badge key={t} label={t} tone={t} zasKey={`badge-${t}`} />)}
          {TONES.map((t) => <Chip key={`c${t}`} label={t} tone={t} zasKey={`chip-${t}`} />)}
        </div>
        <div data-gallery="buttons" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          <Button>Default</Button><Button variant="primary" icon={<Plus />}>Primary</Button><Button variant="danger">Danger</Button>
          <Button variant="danger-primary">Danger primary</Button><Button variant="ghost" icon={<Pencil />}>Ghost</Button>
          <Button size="sm">Small</Button><Button disabled>Disabled</Button>
        </div>
        <div data-gallery="stats" className="zas-stats" style={{ marginBottom: 16 }}>
          <StatTile label="Open POs" value={7} tone="blue" icon="shopping-cart" zasKey="s1" order={0} />
          <StatTile label="Open PO value" value={480000} format="money" tone="indigo" zasKey="s2" order={1} />
          <StatTile label="Credit used" value={0.48} format="percent" tone="green" zasKey="s3" order={2} />
          <StatTile label="Computed" value={null} computed tone="amber" zasKey="s4" order={3} />
        </div>
        <div data-gallery="banners" style={{ marginBottom: 16 }}>
          {["info", "warning", "danger", "success"].map((t, i) => <Banner key={t} tone={t} order={i}>A {t} banner with one line of text.</Banner>)}
        </div>
        <div data-gallery="tabs"><Tabs current={tab} onChange={setTab} tabs={[
          { code: "one", label: "Overview" }, { code: "two", label: "Contacts", count: 3 }, { code: "three", label: "Documents", count: 1, tone: "amber" }]} /></div>
        <div data-gallery="panels" style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 320px", gap: 16 }}>
          <div>
            <Panel title="Fields" zasKey="fields"><FieldGrid fields={FIELDS} /></Panel>
            <Panel title="Timeline" zasKey="timeline"><Timeline events={EVENTS} /></Panel>
          </div>
          <div>
            <Panel title="Loading" zasKey="loading"><div style={{ padding: 16 }}><Skeleton /></div></Panel>
            <Panel title="Empty" zasKey="empty"><EmptyState title="No contacts yet" text="Add the people you deal with at this vendor." /></Panel>
          </div>
        </div>
        <div data-gallery="kit" style={{ marginBottom: 16 }}>
          <Stack>
            <Kpis items={[
              { label: "Open POs", value: 8, icon: "shopping-cart", tone: "blue" },
              { label: "Overdue", value: 3, icon: "triangle-alert", tone: "red", hint: "over 30 days" },
              { label: "PO value", value: 480000, format: "money", tone: "indigo" },
            ]} />
            <Grid>
              <Bars title="Open by status" icon="chart-column" items={[
                { label: "Pending", value: 5, tone: "amber" }, { label: "Approved", value: 9, tone: "green" }, { label: "Rejected", value: 2, tone: "red" }]} />
              <List title="Due soonest" rows={POS} primary="vendor" secondary="po" meta="amount" badge={(r) => ({ text: r.status, tone: r.tone })} />
            </Grid>
            <MiniTable title="Latest POs" rows={POS} columns={[
              { label: "PO", value: "po" }, { label: "Vendor", value: "vendor" }, { label: "Amount", value: "amount", align: "right" },
              { label: "Status", badge: (r) => ({ text: r.status, tone: r.tone }) }]} />
            <Board title="By owner" columns={[
              { title: "Meera Iyer", items: [{ title: "Apex Industries", subtitle: "Waiting 2 days" }] },
              { title: "Unassigned", tone: "gray", items: [] }]} />
            <Panel kit="panel" title="Onboarding" note="2 of 5"><div className="zas-kbody"><Progress done={2} total={5} /></div></Panel>
            <Bars title="Nothing yet" items={[]} empty="No POs this month" />
          </Stack>
        </div>
        <div data-gallery="states"><StateBox kind="not_found" title="Vendor not found" text="It may have been removed or you may not have access." /></div>
      </div>
      {/* Not pinned: the app's own look (app.brand, app.ui, app.design), so the design tests can see
          that every token reaches a component. No golden: it differs per app. */}
      <div className="zas zas-page" data-gallery="themed" data-zas-key="__zas_themed">
        <div className="zas-ph"><div><h1>This app's look</h1><p>The same components with the app's tokens.</p></div></div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          <Button variant="primary" icon={<Plus />}>Primary</Button><Button>Default</Button>
          {(["green", "amber", "red", "blue"] as const).map((t) => <Badge key={t} label={t} tone={t} zasKey={`themed-badge-${t}`} />)}
        </div>
        <Panel title="Fields" zasKey="themed-fields"><FieldGrid fields={FIELDS} /></Panel>
      </div>
    </ToastHost>
  );
}
