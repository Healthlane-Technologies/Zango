// The runtime's public surface. src/custom/pages/index.ts imports from here:
//
//   import { makeListPage, makeDetailPage, makeCustomPage, ZasGallery } from "../../zas";
//   export const Page_vendors = makeListPage("vendors");
//   export const Page_dashboard = makeCustomPage("dashboard");
//   export const ZasStyleGuide = ZasGallery;
//
// Every export name must equal the AppBuilder route's `component`.
//
// src/custom/Shell.tsx (open mode) is `export default makeShell({...})`, passed to ZangoApp as
// customComponents.Layout in src/App.tsx.
//
// src/custom/kit/ (open mode) is the app's own kit pieces; they import the base pieces from
// "../../zas/ui" (never from here: this file re-exports the kit).
import "./fonts.css";
import "./tokens.css";
import { applyTheme } from "./config";

applyTheme();

export { makeListPage, ListPageView } from "./ListPage";
export { RecordDrawer } from "./ZasTable";
export { getDetailComponent, makeDetailPage } from "./Detail360";
export { makeCustomPage } from "./CustomPage";
export { default as ZasLogin } from "./Login";
export { default as ZasGallery } from "./Gallery";
export type { ShellOptions, SoonItem, PlatformItem, LayoutProps } from "./Shell";
// a shell ported from the prototype draws the platform menu and user card with these
export { shellMenu, regrouped, UserCard } from "./Shell";
export { SPEC, detailUrl, viewUrl, pageUrl, money, date, datetime, number, percent, relative, formatValue } from "./config";
export * as api from "./api";
export * from "./ui";
// The app's kit wins over the default pieces of the same name (kit.tsx; src/custom/kit/).
export {
  Button, Badge, Chip, Panel, StatTile, Tabs, Timeline, FieldGrid, Drawer, Modal, EmptyState, Banner, Kpis, Bars, List,
  MiniTable, Board, Progress, ZasTable, makeShell, KIT_PIECES,
} from "./kit";
export type { SlotProps, ZasPayload, FieldValue, Tone } from "./types";
