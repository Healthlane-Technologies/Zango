// src/custom/pages/index.ts - one export per AppBuilder route. The export name MUST equal
// the route's `component` (Page_<page code>, or the spec's `component` for custom pages).
// Written in Phase 6 from .zas/spec.ui.json "pages"; detail pages need no export when
// their hero has a list page (the list page's CrudHandler serves <route>/detail-view/<uuid>).
import { makeCustomPage, makeDetailPage, makeListPage, ZasGallery } from "../../zas";

export const Page_vendors = makeListPage("vendors");                 // pages.vendors (crud)
export const Page_purchase_orders = makeListPage("purchase_orders");
export const ProcurementDashboard = makeCustomPage("dashboard");     // pages.dashboard (custom, component: ProcurementDashboard)
// export const Page_<code> = makeDetailPage("<code>");              // only for a detail page whose hero has NO list page
export const ZasStyleGuide = ZasGallery;                             // /app/__zas - design tests
void makeDetailPage;
