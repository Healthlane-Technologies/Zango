// The app's spec (written by spec_check.py, copied to src/custom/spec.ui.json in Phase 6),
// navigation helpers, and value formatting in the app's locale and currency.
import specJson from "../custom/spec.ui.json";
import type { SpecUi, Tone } from "./types";

export const SPEC = specJson as unknown as SpecUi;

export function applyTheme() {
  if (typeof document === "undefined") return;
  document.documentElement.style.setProperty("--brand", SPEC.app.brand || "#4F46E5");
}

/** URL of an entity's 360 page: served by its list page's CrudHandler (contracts §9). */
export function detailUrl(entityCode: string, uuid: string): string | null {
  const E = SPEC.entities[entityCode];
  if (!E) return null;
  if (E.list_page && SPEC.pages[E.list_page]) return `${SPEC.pages[E.list_page].route}/detail-view/${uuid}`;
  const view = E.detail_view && SPEC.detail_views[E.detail_view];
  const page = view && view.page && SPEC.pages[view.page];
  return page ? page.route.replace(/\/:id$/, "") + "/" + uuid : null;
}

export function viewUrl(viewCode: string, uuid: string): string | null {
  const V = SPEC.detail_views[viewCode];
  return V ? detailUrl(V.hero, uuid) : null;
}

export function pageUrl(code: string): string | null {
  return SPEC.pages[code]?.route ?? null;
}

export const TONES: Tone[] = ["gray", "blue", "green", "amber", "red", "purple", "teal", "indigo", "pink"];
export const tone = (t?: string | null): Tone => (t && (TONES as string[]).includes(t) ? (t as Tone) : "gray");

/** Format override: the component gallery pins these so its screenshots match the goldens in every app. */
export const FMT: { locale?: string; currency?: string; now?: number } = {};
const loc = () => FMT.locale || SPEC.app.locale || "en-US";
const cur = () => FMT.currency || SPEC.app.currency || "USD";

export function money(v: any): string {
  if (v === null || v === undefined || v === "") return "—";
  try {
    return new Intl.NumberFormat(loc(), { style: "currency", currency: cur(), maximumFractionDigits: 0 }).format(Number(v));
  } catch { return String(v); }
}
export function number(v: any): string {
  if (v === null || v === undefined || v === "") return "—";
  return Number(v).toLocaleString(loc());
}
export function percent(v: any): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = Number(v);
  return Math.round(n <= 1 && n > 0 ? n * 100 : n) + "%";
}
export function date(v: any): string {
  if (!v) return "—";
  const d = new Date(v);
  return isNaN(+d) ? String(v) : d.toLocaleDateString(loc(), { day: "numeric", month: "short", year: "numeric" });
}
export function datetime(v: any): string {
  if (!v) return "—";
  const d = new Date(v);
  return isNaN(+d) ? String(v) : d.toLocaleDateString(loc(), { day: "numeric", month: "short" }) + ", " + d.toLocaleTimeString(loc(), { hour: "2-digit", minute: "2-digit" });
}
export function relative(v: any): string {
  if (!v) return "";
  const s = ((FMT.now ?? Date.now()) - new Date(v).getTime()) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return Math.floor(s / 60) + "m ago";
  if (s < 86400) return Math.floor(s / 3600) + "h ago";
  if (s < 86400 * 30) return Math.floor(s / 86400) + "d ago";
  return date(v);
}
export function formatValue(v: any, format?: string | null): string {
  if (format === "money") return money(v);
  if (format === "percent") return percent(v);
  if (format === "days") return v === null || v === undefined ? "—" : `${v}d`;
  if (format === "date") return date(v);
  if (format === "datetime") return datetime(v);
  return number(v);
}
