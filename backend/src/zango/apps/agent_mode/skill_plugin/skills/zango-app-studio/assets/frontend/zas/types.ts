// Shapes shared by the runtime. Contracts: references/contracts.md §8 (data.zas) and §9 (spec.ui.json).

export type Tone = "gray" | "blue" | "green" | "amber" | "red" | "purple" | "teal" | "indigo" | "pink";

export interface SpecColumn {
  key: string; label: string; source: string; format?: string; link_to?: string; display?: string;
  filterable?: boolean; sortable?: boolean; searchable?: boolean; type?: string; to?: string;
  // a second, muted line under the value and an icon before it (the row's zas.sub / zas.icon)
  secondary?: string[]; secondary_style?: "plain" | "mono"; icon?: { by: string | null; map: Record<string, string>; default: string | null };
}
export interface SpecField { key: string; label: string; type: string; to?: string; display?: string }
export interface SpecEntity {
  name: string; plural: string; kind: string; endpoint: string; display: string;
  list_page?: string | null; detail_view?: string | null;
  statuses: Record<string, { label: string; tone: Tone }>;
  tags: Record<string, { label: string; tone: Tone }>;
  choices: Record<string, Record<string, { label: string; tone?: Tone | null }>>;
  columns: SpecColumn[];
  quick_filters: { key: string; label: string; default: boolean }[];
  row_click: string; add_button: string; footer_totals: string[];
  parents: Record<string, { hero: string; fk: string | null }>;
  navigate: Record<string, string>; field_links: Record<string, string>; downloads?: string[];
  fields?: SpecField[];
}
export interface SpecTab {
  code: string; label: string; type: "summary" | "related_table" | "timeline" | "fields" | "custom";
  entity?: string; param?: string; columns?: string[] | "inherit"; row_click?: string;
  empty_state?: { title?: string; text?: string; cta?: string }; group_by?: string; footer_totals?: string[];
  add?: { label: string; prefill: Record<string, string> } | null; preset?: string | null; slot?: string; icon?: string;
  quick_filters?: unknown; page_size?: number; default_sort?: string;
}
export interface SpecView {
  hero: string; layout: "header_tabs" | "header_tabs_sidebar" | "header_sidebar_tabs_left"; back_to?: string;
  page?: string; states: Record<string, any>; tabs: SpecTab[];
  sidebar: { type: string; title?: string; key: string; slot?: string }[]; sticky_header?: boolean;
  rebuild?: string;  // open mode: the slot that draws this 360 from the approved prototype
}
export interface SpecPage { type: "crud" | "detail" | "custom"; route: string; title: string; entity?: string; detail_view?: string; roles?: string[]; export: string; rebuild?: string }
export interface MenuItem { page?: string; label?: string; icon?: string; group?: string; items?: MenuItem[] }
export interface SpecUi {
  app: { code: string; name: string; description: string; locale: string; currency: string; brand: string; ui?: { radius?: "sharp" | "rounded" | "soft"; density?: "compact" | "comfortable" }; design?: { css?: string; font_url?: string | null; fonts?: Record<string, string> }; roles: { name: string; description: string }[];
    modules: { code: string; name: string; description: string }[] };
  pages: Record<string, SpecPage>;
  entities: Record<string, SpecEntity>;
  detail_views: Record<string, SpecView>;
  slots: Record<string, { export: string; hole: string; kind: string; data_key: string | null }>;
  menus: Record<string, { landing?: string; items: MenuItem[] }>;
}

export interface FieldValue {
  key: string; label: string; type: string; value: any; display: string | null; tone?: Tone | null;
  url?: string | null; uuid?: string | null; entity?: string; items?: { code: string; label: string; tone?: Tone }[];
}
export interface ZasAction { name: string; engine_name: string; label: string; primary: boolean; tone?: string | null; confirm?: string | null; has_form: boolean; allowed: boolean; blocked_reason: string | null }
export interface ZasTagAction { code: string; label: string; tone?: Tone; state: "enabled" | "disabled"; allowed: boolean; has_form: boolean; confirm?: string | null; blocked_reason: string | null }
export interface ZasButton { key: string; label: string; icon?: string; type: string; row_action?: string; action_type?: string; confirm?: string;
  entity?: string; prefill?: Record<string, string>; param?: string | null; to?: any; order: number }
export interface ZasPanel { key: string; type: "fields" | "mini_table" | "custom" | "timeline"; title?: string; columns?: number; fields?: FieldValue[]; editable?: boolean; order: number }
export interface ZasPayload {
  view: string; access: "ok" | "no_access" | "not_found"; states?: Record<string, any>; back_to?: string; error?: string;
  record: { uuid: string; pk: number; status: string | null; status_label: string | null; status_tone: Tone | null; tags: { code: string; label: string; tone: Tone }[]; display: string };
  header: { title: string; subtitle: string; avatar: { image: string | null; initials: string };
    badges: { key: string; label: string; tone: Tone; kind?: string }[];
    facts: { key: string; label: string; value: any; display: string | null; type?: string; format?: string; copy: boolean; emphasis: boolean; link: { view: string; uuid: string } | null; order: number }[];
    banners: { tone: string; text: string; order: number }[] };
  stats: { key: string; label: string; value: number | null; format: string; tone?: Tone | null; icon?: string; tab?: string; computed: boolean; order: number }[];
  tabs: { code: string; count: number | null; count_tone: Tone | null; can_add?: boolean; order: number }[];
  panels: Record<string, ZasPanel[]>;
  mini_tables: Record<string, { entity: string; rows: { uuid: string; cells: Record<string, FieldValue> }[]; total: number; see_all_tab?: string }>;
  actions: { transitions: ZasAction[]; tags: ZasTagAction[]; buttons: ZasButton[]; row_actions: string[] };
  custom: Record<string, any>;
  formats: { locale: string; currency: string };
}
export interface DetailResponse {
  pk?: number; object_uuid?: string; title?: string; general_details?: any; workflow_details?: any; row_actions?: any[]; zas?: ZasPayload;
}

export interface SlotProps {
  record?: ZasPayload["record"]; zas?: ZasPayload; data?: any; refresh?: () => void;
  api: typeof import("./api");
}
