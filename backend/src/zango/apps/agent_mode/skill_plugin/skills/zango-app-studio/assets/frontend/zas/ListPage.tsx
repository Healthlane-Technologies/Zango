// List pages (spec page.type: crud), in the Studio preview's design: page header (title, record
// count, primary Add button) over ZasTable (search, inline filters, quick filters, export,
// server-side sort and paging, row drawer). When the entity has a 360 view, this page also owns
// its route: <list route>/detail-view/<uuid> renders the 360 (contracts §9).
import React from "react";
import { useParams } from "react-router-dom";
import { SPEC } from "./config";
import { getDetailComponent } from "./Detail360";
import { ToastHost } from "./ui";
import { ZasTable } from "./ZasTable";

function detailUuid(params: Record<string, string | undefined>): string | null {
  // AppBuilder registers "<route>" and matches "<route>/*": the tail arrives in params["*"]
  const parts = (params["*"] || "").split("/").filter(Boolean);
  if (parts[0] === "detail-view" && parts[1]) return parts[1];
  const path = window.location.pathname.split("/").filter(Boolean);
  const i = path.indexOf("detail-view");
  return i >= 0 && path[i + 1] ? path[i + 1] : null;
}

function ListPageInner({ pageCode, toolbar }: { pageCode: string; toolbar?: React.ReactNode }) {
  const params = useParams();
  const page = SPEC.pages[pageCode];
  const E = page?.entity ? SPEC.entities[page.entity] : null;
  if (!page || !E) return <div className="zas zas-page">Unknown page {pageCode}</div>;
  const uuid = detailUuid(params);
  const ownsDetail = !!E.detail_view && SPEC.detail_views[E.detail_view] && E.list_page === pageCode;
  if (uuid && ownsDetail) {
    const Detail = getDetailComponent(E.detail_view as string);
    return <Detail objectUuid={uuid} />;
  }
  return (
    <div className="zas zas-page" data-zas="page" data-zas-key={pageCode}>
      <ZasTable entity={page.entity as string} endpoint={E.endpoint} page={{ code: pageCode, title: page.title }}
        addLabel={E.add_button} rowClick={E.row_click} zasKey={pageCode} toolbar={toolbar} />
    </div>
  );
}

const listPages: Record<string, React.FC> = {};
/** Stable component per page code (export it from pages/index.ts as Page_<code>). */
export function makeListPage(pageCode: string): React.FC {
  if (!listPages[pageCode]) {
    const C: React.FC = () => <ToastHost><ListPageInner pageCode={pageCode} /></ToastHost>;
    C.displayName = `Page_${pageCode}`;
    listPages[pageCode] = C;
  }
  return listPages[pageCode];
}

/** The list page with extra toolbar controls (ViewsPage puts its switcher there). */
export function ListPageView({ pageCode, toolbar }: { pageCode: string; toolbar?: React.ReactNode }) {
  return <ToastHost><ListPageInner pageCode={pageCode} toolbar={toolbar} /></ToastHost>;
}
