// Platform-provided (server mode); rewritten on every build, do not edit.
//
// A crud page that declares `views` in the spec: a switcher over the entity's table and the
// custom views written for this app in src/custom/views/<page>_<type>.tsx. The declared views
// and their settings are in ./views.json (written by the platform from the approved spec).
//
//   import { makeViewsPage } from "../views/ViewsPage";
//   import TasksKanban from "../views/tasks_kanban";
//   export const Page_tasks = makeViewsPage("tasks", { kanban: TasksKanban });
//
// Where the switcher sits follows the approved preview (.zas/bundle, the page's view screenshots):
//   makeViewsPage("tasks", { kanban: TasksKanban }, { switcher: "toolbar" })
// "toolbar": a segmented control in the table's toolbar, before Export (the preview's place);
// "header" (default): tabs above the page. A custom view places `props.switcher` itself.
import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { ListPageView, makeListPage, SPEC, Tabs, ToastHost } from "../../zas";
import declared from "./views.json";

/** One declared view, as in the spec, plus what the platform resolved for it. */
export interface ViewSpec {
  type: string; label: string; icon: string; custom: boolean;
  /** kanban on status: the workflow's transitions, to find the one a move stands for. */
  transitions?: { name: string; label: string; from: string[]; to: string; engine: { name: string; from: string }[]; has_form: boolean; roles: string[] }[];
  [key: string]: any;
}
export interface ViewProps {
  pageCode: string; title: string; entity: string; endpoint: string; view: ViewSpec;
  /** The switcher: in the view's own toolbar row when placement is "toolbar", else its header row. */
  switcher: React.ReactNode;
  /** Where the approved page has the switcher. */
  placement: "header" | "toolbar";
}
export interface ViewsPageOptions {
  /** Where the switcher sits, as in the approved preview. Default "header". */
  switcher?: "header" | "toolbar";
}

const VIEWS = declared as unknown as Record<string, ViewSpec[]>;
const remembered = (page: string): string | null => {
  try { return window.localStorage.getItem(`zas.view.${page}`); } catch { return null; }
};
const remember = (page: string, type: string) => {
  try { window.localStorage.setItem(`zas.view.${page}`, type); } catch { /* private mode */ }
};
const onDetail = (params: Record<string, string | undefined>) =>
  (params["*"] || "").split("/").includes("detail-view") || window.location.pathname.split("/").includes("detail-view");

const pages: Record<string, React.FC> = {};

export function makeViewsPage(pageCode: string, components: Record<string, React.ComponentType<ViewProps>>,
  options: ViewsPageOptions = {}): React.FC {
  const placement = options.switcher === "toolbar" ? "toolbar" : "header";
  if (pages[pageCode]) return pages[pageCode];
  const views = VIEWS[pageCode] || [];
  const Table = makeListPage(pageCode);
  const usable = views.filter((v) => !v.custom || components[v.type]);
  const C: React.FC = () => {
    const params = useParams();
    const first = usable[0]?.type ?? "table";
    const saved = remembered(pageCode);
    const [current, setCurrent] = useState(saved && usable.some((v) => v.type === saved) ? saved : first);
    const page = SPEC.pages[pageCode];
    const E = page?.entity ? SPEC.entities[page.entity] : null;
    // The record's 360 page lives under the list route: the table page owns it.
    if (!page || !E || usable.length < 2 || onDetail(params)) return <Table />;
    const view = usable.find((v) => v.type === current) ?? usable[0];
    const pick = (t: string) => { remember(pageCode, t); setCurrent(t); };
    const switcher = placement === "toolbar" ? (
      <div className="zas-vsw" role="tablist" aria-label="View" data-zas="view-switch" data-zas-key={pageCode} data-zas-place="toolbar">
        {usable.map((v, i) => (
          <button key={v.type} type="button" role="tab" aria-selected={v.type === view.type} className={v.type === view.type ? "on" : undefined}
            onClick={() => pick(v.type)} data-zas="tab" data-zas-key={v.type} data-zas-order={i}>{v.label}</button>
        ))}
      </div>
    ) : (
      <div data-zas="view-switch" data-zas-key={pageCode} data-zas-place="header">
        <Tabs tabs={usable.map((v) => ({ code: v.type, label: v.label }))} current={view.type} onChange={pick} />
      </div>
    );
    const Custom = view.custom ? components[view.type] : null;
    if (!Custom) {
      return placement === "toolbar"
        ? <div className="zas" data-zas-view="table"><ListPageView pageCode={pageCode} toolbar={switcher} /></div>
        : <div className="zas" data-zas-view="table">{switcher}<Table /></div>;
    }
    return (
      <ToastHost>
        <div className="zas zas-page" data-zas="page" data-zas-key={pageCode} data-zas-view={view.type}>
          <Custom pageCode={pageCode} title={page.title} entity={page.entity as string} endpoint={E.endpoint} view={view}
            switcher={switcher} placement={placement} />
        </div>
      </ToastHost>
    );
  };
  C.displayName = `Page_${pageCode}`;
  pages[pageCode] = C;
  return C;
}
