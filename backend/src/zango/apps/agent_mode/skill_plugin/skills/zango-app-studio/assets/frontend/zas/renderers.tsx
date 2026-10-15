// Cell renderers shared by list pages and 360 child tabs: spec tones on status and tags,
// and the row-action menu (navigate actions route client-side; file links open the file).
import { useNavigate } from "react-router-dom";
import { SPEC, detailUrl, pageUrl } from "./config";
import * as api from "./api";
import { Badge, Chip, Menu, useToast } from "./ui";
import type { SpecEntity } from "./types";

export function statusRenderer(spec: SpecEntity) {
  return ({ statusValue, value }: any) => {
    const label = statusValue?.status_label ?? (typeof value === "string" ? value.replace(/<[^>]*>/g, "") : "");
    if (!label) return null;
    const st = Object.values(spec.statuses).find((s) => s.label === label);
    return <span className="zas"><Badge label={label} tone={st?.tone} /></span>;
  };
}

export function tagsRenderer(spec: SpecEntity) {
  return ({ tags }: any) => (
    <span className="zas">
      {(tags || []).map((t: string) => {
        const tg = Object.values(spec.tags).find((x) => x.label === t);
        return <Chip key={t} label={t} tone={tg?.tone} />;
      })}
    </span>
  );
}

/** Row actions menu in our design; navigate actions route client-side. */
function RowActionsMenu({ spec, actions, row, onActionClick }: { spec: SpecEntity; actions: any[]; row: any; onActionClick: (a: any) => void }) {
    const navigate = useNavigate();
    const toast = useToast();
    const items = (actions || []).map((a: any) => ({
      key: a.key, label: a.name || a.label, danger: a.key === "delete",
      onClick: () => {
        const original = row?.original || row;
        const fileField = spec.field_links?.[a.key];
        if (fileField) {
          const v = original?.[fileField];
          const url = typeof v === "string" ? (v.match(/href="([^"]+)"/)?.[1] || (/^(https?:)?\/\//.test(v) || v.startsWith("/") ? v : null)) : v?.url;
          if (url) { window.open(url, "_blank", "noopener"); return; }
        }
        const target = spec.navigate?.[a.key];
        if (target) {
          const uuid = (row?.original || row)?.object_uuid;
          const url = SPEC.detail_views[target] ? detailUrl(SPEC.detail_views[target].hero, uuid) : pageUrl(target);
          if (url) { navigate(url); return; }
        }
        if (spec.downloads?.includes(a.key)) {  // hook saves the file and returns {url}; crud's own flow would drop it
          const uuid = (row?.original || row)?.object_uuid;
          api.runRowAction(spec.endpoint, uuid, a.key).then((res: any) => {
            const r = api.body(res) ?? {};
            if (res?.success === false || !r?.url) { toast(r?.message || "The file could not be generated.", undefined, true); return; }
            window.open(r.url, "_blank", "noopener");
          }).catch((e: any) => toast("Download failed", String(e?.message || e), true));
          return;
        }
        onActionClick(a);
      },
    }));
    return <span className="zas"><Menu items={items} /></span>;
}

// one stable renderer set per entity (CrudHandler props must not change identity every render)
const cache: Record<string, { status: any; tags: any; actions: any }> = {};
export function renderersFor(spec: SpecEntity) {
  const k = spec.endpoint;
  if (!cache[k]) {
    cache[k] = {
      status: statusRenderer(spec),
      tags: tagsRenderer(spec),
      actions: (p: any) => <RowActionsMenu spec={spec} actions={p.actions} row={p.row} onActionClick={p.onActionClick} />,
    };
  }
  return cache[k];
}
export const actionsRenderer = (spec: SpecEntity) => renderersFor(spec).actions;
