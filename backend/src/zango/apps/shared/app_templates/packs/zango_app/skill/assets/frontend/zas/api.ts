// Every call the runtime makes, in one place. Endpoints and params follow the crud
// package exactly (BaseCrudView / ModelTable / BaseDetail / WorkflowBase); see
// references/testing.md for the same list from the API-test side.
import { useCallback, useEffect, useState } from "react";
import type { DetailResponse } from "./types";

export function csrf(): string {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "";
}

export function withParams(endpoint: string, params: Record<string, string | number | null | undefined>): string {
  const [base, qs] = endpoint.split("?");
  const p = new URLSearchParams(qs || "");
  Object.entries(params).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== "") p.set(k, String(v)); });
  const s = p.toString();
  return s ? `${base}?${s}` : base;
}

async function parse(res: Response) {
  const text = await res.text();
  let json: any = null;
  try { json = text ? JSON.parse(text) : null; } catch { json = null; }
  if (!res.ok && !json) throw new Error(`${res.status} ${res.statusText}`);
  return json;
}

export async function get(endpoint: string, params: Record<string, any> = {}) {
  const res = await fetch(withParams(endpoint, params), { credentials: "include", headers: { Accept: "application/json" } });
  return parse(res);
}

export async function post(endpoint: string, params: Record<string, any>, body: Record<string, any> = {}) {
  const fd = new FormData();
  Object.entries(body).forEach(([k, v]) => { if (v !== undefined && v !== null) fd.append(k, v instanceof Blob ? v : String(v)); });
  const res = await fetch(withParams(endpoint, params), {
    method: "POST", credentials: "include", body: fd, headers: { "X-CSRFToken": csrf(), Accept: "application/json" },
  });
  return parse(res);
}

/** response envelope: {success, response: {...}} */
export const body = (j: any) => (j && typeof j === "object" && "response" in j ? j.response : j);

export async function fetchDetail(endpoint: string, uuid: string): Promise<DetailResponse> {
  return body(await get(endpoint, { view: "detail", action: "fetch_item_details", object_uuid: uuid }));
}

export async function fetchTimeline(endpoint: string, uuid: string, tab?: string) {
  return body(await get(endpoint, { view: "detail", action: "zas_timeline", object_uuid: uuid, tab }));
}

/** Status transition without a form. With a form, TransitionDialog uses FormRenderer. */
export async function runTransition(endpoint: string, uuid: string, engineName: string) {
  return post(endpoint, { view: "workflow", action: "process_transition", transition_type: "status", transition_name: engineName, object_uuid: uuid });
}

export async function runTag(endpoint: string, uuid: string, tag: string, state: "enabled" | "disabled") {
  return post(endpoint, { view: "workflow", action: "process_transition", transition_type: "tag", transition_name: tag, transition_state: state, object_uuid: uuid });
}

/** Simple (confirm / delete / download / navigate) row action. */
export async function runRowAction(endpoint: string, uuid: string, key: string) {
  return post(endpoint, { action_type: "row", action_key: key, object_uuid: uuid });
}

/** Rows of a table endpoint without CrudHandler (no QueryClient involved; see entity-360.md §4b). */
export function useTableRows(endpoint: string | null, opts: { length?: number; params?: Record<string, any> } = {}) {
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const key = JSON.stringify(opts.params || {});
  useEffect(() => {
    if (!endpoint) { setRows([]); setTotal(0); setLoading(false); return; }
    let live = true;
    setLoading(true);
    get(endpoint, { ...(opts.params || {}), view: "table", action: "get_table_data", start: 0, length: opts.length ?? 100 })
      .then((j) => {
        if (!live) return;
        const data = j?.data ?? j?.response?.table_data ?? [];
        setRows(data.map(stripHtml));
        setTotal(j?.recordsTotal ?? j?.response?.recordsTotal ?? data.length);
        setError(null);
      })
      .catch((e) => live && setError(String(e)))
      .finally(() => live && setLoading(false));
    return () => { live = false; };
  }, [endpoint, opts.length, key, tick]);
  const refetch = useCallback(() => setTick((t) => t + 1), []);
  return { rows, total, loading, error, refetch };
}

/** _getval columns arrive as HTML strings; keep text only. */
function stripHtml(row: any) {
  const out: any = {};
  for (const [k, v] of Object.entries(row || {})) {
    out[k] = typeof v === "string" && /<[a-z][\s\S]*>/i.test(v) ? v.replace(/<[^>]*>/g, "").trim() : v;
  }
  return out;
}
