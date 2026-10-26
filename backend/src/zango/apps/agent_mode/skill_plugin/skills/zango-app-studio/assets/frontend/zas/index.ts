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
import "./fonts.css";
import "./tokens.css";
import { applyTheme } from "./config";

applyTheme();

export { makeListPage, ListPageView } from "./ListPage";
export { RecordDrawer, ZasTable } from "./ZasTable";
export { getDetailComponent, makeDetailPage } from "./Detail360";
export { makeCustomPage } from "./CustomPage";
export { default as ZasLogin } from "./Login";
export { default as ZasGallery } from "./Gallery";
export { makeShell } from "./Shell";
export type { ShellOptions } from "./Shell";
export { SPEC, detailUrl, viewUrl, pageUrl, money, date, datetime, number, percent, relative, formatValue } from "./config";
export * as api from "./api";
export * from "./ui";
export type { SlotProps, ZasPayload, FieldValue, Tone } from "./types";
