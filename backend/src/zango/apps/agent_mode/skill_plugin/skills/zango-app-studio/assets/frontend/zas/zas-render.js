/* zas-render.js: the one renderer for Zango apps.
 *
 * The App Studio preview (zango_app pack, builder/app-studio.html) and the built app's runtime
 * (assets/frontend/zas/) both draw their screens with this file: same spec in, same HTML out.
 * What differs is the host passed to use():
 *
 *   state    S: { M (build(spec)), role, users, me, ui: { tables }, views }
 *   rows(code), row(code, id)        the records the renderer can resolve (links, reverse lookups)
 *   visible(E, role)                 the rows a role may see (in the runtime: what the server sent)
 *   query(cfg, st)                   a table's rows after search, quick filter, filters, sort, page
 *   stat(E, rows, def)               a count or a sum ({where, sum}) for page subtitles and tiles
 *   computed(E, row, c)              a computed column's value (the preview makes one up)
 *   fact(kind, E, row, c)            a column's per-row extras: badge, highlight, secondary, icon
 *   options(E, c, f)                 a link filter's options
 *   act(name, payload)               what a click does: render, go, drawer, create, export, menu,
 *                                    row_action, edit, delete, transition, tag, ai ({E, row?, rows?,
 *                                    agent, trigger}: run an AI helper on a record or a list)
 *   preview                          true in the Studio: draw the data-zas-path pointing marks
 *
 * memory() is the in-memory data half of a host (the preview's demo rows in S.db). The app's host
 * is zas/RenderedPage.tsx. bind(el) wires a container's data-a / data-in / data-ch to the actions.
 *
 * EDIT THIS FILE, NOT ITS COPIES. app-studio.html carries it inline and the runtime gets a copy;
 * `python -m zango.apps.agent_mode.zas_render --write` refreshes both, and a test fails when
 * they drift. Plain JS, no imports: it runs as a classic <script> and as an ES module. */
globalThis.ZasRender = (function () {
'use strict';
let H = null, S = null;
function use(host){ H = host; S = host.state; }
const rerender = () => H.act('render');
const nav = (page, id, tab) => H.act('go', { page, id, tab });
const drawer = (E, row) => H.act('drawer', { E, row });
const menu = (anchor, items) => H.act('menu', { anchor, items });
const visibleRows = (E, role) => H.visible(E, role || S.role);

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const arr = v => v == null ? [] : Array.isArray(v) ? v : [v];
const isObj = v => v && typeof v === 'object' && !Array.isArray(v);
const titleize = s => String(s == null ? '' : s).replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().replace(/\b\w/g, c => c.toUpperCase());
const empty = v => v == null || v === '' || (Array.isArray(v) && !v.length);
function hash(s){ let h = 2166136261; s = String(s); for (let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
const pad = (n, w) => String(n).padStart(w, '0');
const todayISO = () => new Date().toISOString().slice(0, 10);
function kv(list){
  if (!list) return [];
  if (isObj(list)) return Object.entries(list).map(([k, v]) => ({ key: k, ...(isObj(v) ? v : {}) }));
  return arr(list).map(it => {
    if (typeof it === 'string' || typeof it === 'number') return { key: String(it) };
    if (isObj(it)){
      const ks = Object.keys(it);
      if (ks.length === 1 && (it[ks[0]] == null || isObj(it[ks[0]]))) return { key: ks[0], ...(it[ks[0]] || {}) };
      return { ...it };
    }
    return { key: String(it) };
  });
}
/* action / input registry for delegated handlers */
let ACT = [];
const resetActs = () => { ACT = []; };
const actAt = i => ACT[i];
const A = fn => { ACT.push(fn); return ACT.length - 1; };
/* icons */
function iconOK(n){ const lu = globalThis.lucide; if (!lu || !lu.icons) return true; const p = String(n).split('-').map(s => s ? s[0].toUpperCase() + s.slice(1) : '').join(''); return !!lu.icons[p]; }
const ic = (n, cls) => `<i data-lucide="${esc(n && iconOK(n) ? n : 'circle-dot')}"${cls ? ` class="${cls}"` : ''}></i>`;
function paintIcons(){ try { globalThis.lucide.createIcons(); } catch (e) {} }
/* tones */
const TONES = { gray: ['#F2F4F7', '#344054', '#EAECF0'], blue: ['#EFF8FF', '#175CD3', '#B2DDFF'], green: ['#ECFDF3', '#067647', '#ABEFC6'], amber: ['#FFFAEB', '#B54708', '#FEDF89'], red: ['#FEF3F2', '#B42318', '#FECDCA'], purple: ['#F4F3FF', '#5925DC', '#D9D6FE'], teal: ['#F0FDF9', '#107569', '#99F6E0'], indigo: ['#EEF4FF', '#3538CD', '#C7D7FE'], pink: ['#FDF2FA', '#C11574', '#FCCEEE'] };
const tone = t => TONES[t] || TONES.gray;
const badge = (l, t) => { const c = tone(t); return `<span class="z-badge" style="background:${c[0]};color:${c[1]};border-color:${c[2]}"><i></i>${esc(l)}</span>`; };
const chip = (l, t) => { const c = tone(t); return `<span class="z-chip" style="background:${c[0]};color:${c[1]}">${esc(l)}</span>`; };
const AVC = ['#4F46E5', '#0E7490', '#7C3AED', '#1E40AF', '#0F766E', '#B45309', '#BE185D', '#334155'];
const avColor = s => AVC[hash(s) % AVC.length];
const initials = s => { const p = String(s || '?').trim().split(/\s+/); return ((p[0] || '?')[0] + (p[1] ? p[1][0] : '')).toUpperCase(); };
const BUILTIN = ['id', 'created_at', 'created_by', 'modified_at', 'modified_by'];
const BUILTIN_F = { id: { type: 'integer', label: 'ID' }, created_at: { type: 'datetime', label: 'Created' }, modified_at: { type: 'datetime', label: 'Modified' }, created_by: { type: 'user', label: 'Created by' }, modified_by: { type: 'user', label: 'Modified by' } };
function normChoices(c, sets){
  if (typeof c === 'string') c = sets[c];
  return arr(c).map(x => {
    if (typeof x !== 'object' || x == null) return { id: String(x), label: titleize(x) };
    if ('id' in x) return { ...x, id: String(x.id), label: x.label != null ? String(x.label) : titleize(x.id) };
    const k = Object.keys(x)[0]; const v = x[k];
    return { id: k, label: typeof v === 'string' ? v : (v && v.label) || titleize(k), ...(isObj(v) ? v : {}) };
  });
}
function normField(f, sets){ f = { ...f }; f.type = f.type || 'text'; if (f.choices) f.opts = normChoices(f.choices, sets); f.label = f.label || titleize(f.key); return f; }
function normCodes(list){ return arr(list).map(s => typeof s === 'string' ? { code: s } : s.code ? { ...s } : (() => { const k = Object.keys(s)[0]; return { code: k, ...(isObj(s[k]) ? s[k] : {}) }; })()); }
function normAccess(a){
  if (!a) return null; const out = {};
  const put = (role, v) => { if (v === 'none' || v == null || (isObj(v) && v.no_access)) { out[role] = { none: true, actions: new Set() }; return; } out[role] = { actions: new Set(arr(v.actions || v.can)), rows: v.rows }; };
  if (Array.isArray(a)) a.forEach(o => isObj(o) && Object.entries(o).forEach(([r, v]) => put(r, v))); else Object.entries(a).forEach(([r, v]) => put(r, v));
  return out;
}
function normCol(E, c){
  let src = c.source || c.as;
  if (src === 'custom') src = 'computed';
  if (!src) src = c.key === 'status' && E.wf ? 'status' : c.key === 'tags' && E.wf ? 'tags' : (E.fmap[c.key] || BUILTIN.includes(c.key)) ? 'field' : c.path ? 'path' : 'computed';
  const f = E.fmap[c.key] || BUILTIN_F[c.key];
  return { ...c, source: src, label: c.label || (f && f.label) || titleize(c.key), roles: c.roles ? arr(c.roles) : null };
}
function normEntity(e, m, sets){
  const E = { ...e, code: e.code, name: e.name || titleize(e.code), module: m };
  E.plural = e.plural || E.name + 's';
  E.fields = kv(e.fields).map(f => normField(f, sets));
  E.fmap = {}; E.fields.forEach(f => { E.fmap[f.key] = f; });
  E.display = e.display || (E.fmap.name ? 'name' : (E.fields.find(f => f.type === 'text') || {}).key || 'id');
  const w = e.workflow;
  if (w){
    const st = normCodes(w.statuses || w.states).map(s => ({ ...s, label: s.label || titleize(s.code), color: s.color || 'gray', initial: !!(s.initial || s.start), final: !!s.final }));
    const smap = {}; st.forEach(s => { smap[s.code] = s; });
    const initial = (st.find(s => s.initial) || st[0] || {}).code;
    const trs = arr(w.transitions || w.steps).map(t => ({ ...t, name: t.name || String(t.label || t.do || 'step').toLowerCase().replace(/\W+/g, '_'), label: t.label || t.do || titleize(t.name), from: arr(t.from), roles: arr(t.roles || t.by), form: kv(t.form || t.collects).map(f => normField(f, sets)), system: t.trigger === 'system' || !!t.automatic }));
    const tags = normCodes(w.tags || w.labels).map(t => ({ ...t, label: t.label || titleize(t.code), color: t.color || 'gray' }));
    tags.forEach(t => ['enable', 'disable'].forEach(k => { t[k] = t[k] ? { ...t[k], roles: arr(t[k].roles), form: kv(t[k].form).map(f => normField(f, sets)) } : null; }));
    E.wf = { statuses: st, smap, initial, trs, tags, tmap: Object.fromEntries(tags.map(t => [t.code, t])) };
  }
  const tb = e.table || {}; E.table = tb;
  let cols = kv(tb.columns);
  if (!cols.length){ cols = E.fields.filter(f => !['long_text', 'json', 'file', 'image'].includes(f.type)).slice(0, 6).map(f => ({ key: f.key })); if (E.wf) cols.push({ key: 'status' }); }
  E.cols = cols.map(c => normCol(E, c));
  E.ractions = arr(tb.row_actions || tb.can_do).map(a => ({ ...a, key: a.key || String(a.label || a.do).toLowerCase().replace(/\W+/g, '_'), label: a.label || a.do || titleize(a.key), roles: (a.roles || a.by) ? arr(a.roles || a.by) : null, type: a.type || a.kind || 'confirm', form: kv(a.form).map(f => normField(f, sets)) }));
  E.acc = normAccess(e.access || tb.access);
  E.form = e.form || {};
  E.validation = e.validation || {};
  return E;
}
const VIEW_TYPES = { table: 'table', kanban: 'kanban', cards: 'layout-grid', calendar: 'calendar-days', timeline: 'git-commit-vertical' };
const VIEW_LABEL = { table: 'Table', kanban: 'Board', cards: 'Cards', calendar: 'Calendar', timeline: 'Timeline' };
function normViews(v){
  return arr(v).map(x => typeof x === 'string' ? { type: x } : isObj(x) ? { ...x, type: x.type || 'table' } : null).filter(Boolean)
    .map(x => ({ ...x, card: isObj(x.card) ? { ...x.card, fields: arr(x.card.fields) } : x.type === 'cards' || x.type === 'kanban' ? { fields: [] } : x.card, columns: x.columns ? arr(x.columns) : null }));
}
function build(spec){
  const M = { spec, app: spec.app || {}, sets: spec.choice_sets || {}, roles: [], role: {}, pages: {}, ents: {}, entList: [], dvs: {}, mods: [] };
  let roles = spec.roles || [];
  if (isObj(roles)) roles = Object.entries(roles).map(([name, v]) => ({ name, ...(v || {}) }));
  roles.forEach(r => { const RR = { ...r, name: r.name || r.code, menu: arr(r.menu) }; M.roles.push(RR); M.role[RR.name] = RR; });
  arr(spec.modules).forEach(mod => { const m = { ...mod, ents: [] }; M.mods.push(m); arr(mod.entities).forEach(e => { if (!e || !e.code) return; const E = normEntity(e, m, M.sets); M.ents[E.code] = E; M.entList.push(E); m.ents.push(E); }); });
  arr(spec.pages).forEach(p => { if (!p || !p.code) return; M.pages[p.code] = { ...p, title: p.title || (p.entity && M.ents[p.entity] && M.ents[p.entity].plural) || titleize(p.code), views: normViews(p.views) }; });
  arr(spec.detail_views).forEach(v => { if (!v || !v.code) return; M.dvs[v.code] = { ...v, tabs: arr(v.tabs) }; });
  Object.values(M.pages).forEach(p => {
    if (p.type === 'detail' && M.dvs[p.detail_view]) M.dvs[p.detail_view].page = p;
    if (p.type === 'crud' && M.ents[p.entity] && !M.ents[p.entity].page) M.ents[p.entity].page = p;
  });
  Object.values(M.dvs).forEach(v => { if (M.ents[v.hero] && !M.ents[v.hero].dv) M.ents[v.hero].dv = v; });
  autoViews(M);
  return M;
}
/* Every record opens full page. An entity with a list page and no detail view gets a generated one
   (<entity>_record: code + title, the workflow stepper, a tab per entity that links to it, Activity),
   and every detail view opens on Overview (all fields; long text in its own panel) unless it already
   has a summary/fields tab. Same rules as spec_check.auto_views, so the built app matches. */
const LONG_TYPES = ['long_text', 'json'];
function autoViews(M){
  AUTO_PATHS.length = 0;
  M.entList.forEach(E => {
    if (E.dv || !E.page) return;
    const code = E.code + '_record'; if (M.dvs[code] || M.pages[code]) return;
    const codeKey = (E.fields.find(f => f.auto && f.auto.sequence) || {}).key;
    const tk = E.display && E.display !== codeKey ? E.display : ((E.fields.find(f => f.key !== codeKey && ['text', 'link'].includes(f.type)) || {}).key || E.display);
    const facts = E.fields.filter(f => f.key !== tk && f.key !== codeKey && ['choice', 'link'].includes(f.type)).slice(0, 4).map(f => ({ label: f.label, field: f.key }));
    const steps = E.wf ? E.wf.statuses.filter(s => !s.final || s.color === 'green').map(s => s.code) : [];
    const kids = []; M.entList.forEach(T => { if (T !== E) T.fields.forEach(f => { if (f.type === 'link' && f.to === E.code) kids.push({ T, via: f.key }); }); });
    const seen = new Set();
    const tabs = kids.map(({ T, via }) => { let c = T.code; if (seen.has(c)) c += '_' + via; seen.add(c); return { code: c, label: T.plural, type: 'related_table', entity: T.code, via, count_badge: true, columns: T.cols.map(x => x.key).filter(k => k !== via) }; });
    tabs.push({ code: 'activity', label: 'Activity', type: 'timeline', sources: [{ entity: E.code }, ...kids.map(k => ({ entity: k.T.code, via: k.via }))] });
    const side = E.cols.map(c => c.key).filter(k => E.fmap[k] && k !== codeKey && k !== tk).slice(0, 5);
    const header = { title: tk, subtitle: codeKey ? [`{${codeKey}}`] : [], badges: E.wf ? [{ source: 'status' }] : [], facts, actions: { transitions: true, buttons: E.form.edit ? [{ key: 'edit', label: 'Edit', type: 'edit' }] : [] } };
    if (steps.length >= 2) header.stepper = { steps };
    const dv = { code, hero: E.code, auto: true, back_to: E.page.code, layout: 'header_tabs_sidebar', header, sidebar: side.length ? [{ type: 'fields', title: `${E.name} summary`, fields: side }] : [], tabs };
    const page = { code, type: 'detail', detail_view: code, auto: true, route: String(E.page.route || '/app/' + E.code).replace(/\/+$/, '') + '/:id', title: E.name, views: [] };
    M.dvs[code] = dv; M.pages[code] = page; dv.page = page; E.dv = dv;
    AUTO_PATHS.push(`/detail_views/@${code}`, `/pages/@${code}`);
  });
  Object.values(M.dvs).forEach(dv => {
    const E = M.ents[dv.hero]; if (!E || dv.tabs.some(t => t && (t.code === 'overview' || t.type === 'summary' || t.type === 'fields'))) return;
    const longs = E.fields.filter(f => LONG_TYPES.includes(f.type));
    if (!dv.auto) AUTO_PATHS.push(`/detail_views/@${dv.code}/tabs/@overview`);
    dv.tabs = [{ code: 'overview', label: 'Overview', type: 'summary', auto: true, sections: [
      { type: 'fields', title: `${E.name} details`, fields: E.fields.filter(f => !LONG_TYPES.includes(f.type)).map(f => f.key), columns: 3 },
      ...longs.map(f => ({ type: 'fields', title: f.label, icon: 'align-left', fields: [f.key], columns: 1, show_when: `${f.key} is_set` }))] }, ...dv.tabs];
  });
}

const rowsOf = c => H.rows(c) || [];
const getRow = (c, id) => H.row(c, id);
const curUser = () => (S.users[S.role] || [])[0] || 'Demo User';
/* ═════════════════════════ paths, expressions, formatting ═════════════════════════ */
const UNK = Symbol('unknown');
function rp(E, row, path, ctx){
  ctx = ctx || {};
  if (path == null) return { v: undefined };
  const segs = String(path).split('.');
  if (segs[0] === 'current_user'){ if (segs[1] === 'role') return { v: S.role }; if (segs[1] === 'name') return { v: curUser() }; const me = S.me[S.role]; return { v: me && (segs[1] === me.entity || segs[1] === 'id') ? me.id : undefined }; }
  // `form.x` is a transition form's value — unless the entity has a field called `form`.
  if (segs[0] === 'form' && (ctx.form || !(E && E.fmap && E.fmap.form))){ if (!ctx.form) throw UNK; return { v: ctx.form[segs[1]] }; }
  if (segs[0] === 'today') return { v: todayISO() };
  let cur = row, CE = E, f = null, v;
  for (let i = 0; i < segs.length; i++){
    const s = segs[i]; if (!cur) return { v: undefined };
    const m = s.match(/^(\w+)\[(.*)\]$/);
    if (m){
      const C = S.M.ents[m[1]]; if (!C) return { v: undefined };
      const lf = C.fields.find(x => x.type === 'link' && x.to === CE.code);
      const cands = rowsOf(C.code).filter(r => lf && r[lf.key] === cur.id);
      cur = cands.find(r => !m[2] ? true : C.fmap[m[2]] ? !!r[m[2]] : evalCond(m[2], { E: C, row: r }) !== false); CE = C;
      if (i === segs.length - 1) return { v: cur ? cur.id : undefined, E: C, f: { type: 'link', to: C.code }, row: cur };
      continue;
    }
    f = CE && CE.fmap[s];
    v = cur[s];
    if (i < segs.length - 1){
      if (f && f.type === 'link'){
        if (f.to === 'app_user') return { v, f: { type: 'text' } };
        const T = S.M.ents[f.to]; cur = T ? getRow(T.code, v) : null; CE = T;
      } else return { v: undefined };
    }
  }
  const last = segs[segs.length - 1];
  return { v, E: CE, f: f || (last === 'status' ? { type: 'status' } : last === 'tags' ? { type: 'tags' } : BUILTIN_F[last]), row: cur };
}
function knownPath(p, ctx){ const s = String(p).split('.')[0].replace(/\[.*$/, ''); return s === 'status' || s === 'tags' || s === 'current_user' || s === 'form' || BUILTIN.includes(s) || !!(ctx.E && ctx.E.fmap[s]) || !!(S.M && S.M.ents[s]); }
function lit(x, ctx){
  x = String(x).trim();
  if (/^".*"$|^'.*'$/.test(x)) return x.slice(1, -1);
  if (/^-?\d+(\.\d+)?$/.test(x)) return +x;
  if (x === 'today') return todayISO();
  if (x === 'true') return true; if (x === 'false') return false; if (x === 'null') return null;
  if (/^[\w.\[\]]+$/.test(x) && knownPath(x, ctx) && (x.includes('.') || (ctx.E && ctx.E.fmap[x]))) return rp(ctx.E, ctx.row, x, ctx).v;
  return x;
}
function cmp(a, op, b){
  const na = typeof a === 'number' || (a !== '' && a != null && !isNaN(+a) && typeof a !== 'boolean'), nb = typeof b === 'number' || (b !== '' && b != null && !isNaN(+b) && typeof b !== 'boolean');
  if (na && nb){ a = +a; b = +b; } else { a = a == null ? '' : String(a); b = b == null ? '' : String(b); }
  switch (op){ case '==': return a === b; case '!=': return a !== b; case '>': return a > b; case '>=': return a >= b; case '<': return a < b; case '<=': return a <= b; }
  return null;
}
function combine(vals, mode){
  if (mode === 'all'){ if (vals.includes(false)) return false; return vals.includes(null) ? null : true; }
  if (vals.includes(true)) return true; return vals.includes(null) ? null : false;
}
function evalStr(s, ctx){
  s = String(s).trim(); if (!s) return true;
  const ors = s.split(/\s+or\s+/i); if (ors.length > 1) return combine(ors.map(x => evalStr(x, ctx)), 'any');
  const ands = s.split(/\s+and\s+/i); if (ands.length > 1) return combine(ands.map(x => evalStr(x, ctx)), 'all');
  if (/^not\s+/i.test(s)){ const v = evalStr(s.replace(/^not\s+/i, ''), ctx); return v == null ? null : !v; }
  if (s[0] === '(' && s.endsWith(')')) return evalStr(s.slice(1, -1), ctx);
  try {
    let m;
    if ((m = s.match(/^has_tag\s+(\w+)$/))) return arr(ctx.row && ctx.row.tags).includes(m[1]);
    if ((m = s.match(/^([\w.\[\]]+)\s+(not_in|in)\s+\[(.*)\]$/))){ if (!knownPath(m[1], ctx)) return null; const v = rp(ctx.E, ctx.row, m[1], ctx).v; const list = m[3].split(',').map(x => lit(x, ctx)); const hit = list.some(x => String(x) === String(v)); return m[2] === 'in' ? hit : !hit; }
    if ((m = s.match(/^([\w.\[\]]+)\s+(is_set|is_empty|is_true|is_false)$/))){ if (!knownPath(m[1], ctx)) return null; const v = rp(ctx.E, ctx.row, m[1], ctx).v; return { is_set: !empty(v), is_empty: empty(v), is_true: v === true || v === 'true', is_false: !v }[m[2]]; }
    if ((m = s.match(/^([\w.\[\]]+)\s*(==|!=|>=|<=|>|<)\s*(.+)$/))){ if (!knownPath(m[1], ctx)) return null; return cmp(rp(ctx.E, ctx.row, m[1], ctx).v, m[2], lit(m[3], ctx)); }
  } catch (e) { if (e === UNK) return null; }
  return null;
}
function evalCond(c, ctx){
  if (c == null || c === '') return true;
  if (typeof c === 'boolean') return c;
  if (typeof c === 'string') return evalStr(c, ctx);
  if (Array.isArray(c)) return combine(c.map(x => evalCond(x, ctx)), 'all');
  if (isObj(c)){
    const parts = [];
    if (c.all) parts.push(combine(arr(c.all).map(x => evalCond(x, ctx)), 'all'));
    if (c.any) parts.push(combine(arr(c.any).map(x => evalCond(x, ctx)), 'any'));
    if (c.text) parts.push(null);
    return parts.length ? combine(parts, 'all') : null;
  }
  return null;
}
function condTexts(c){ if (!c) return []; if (typeof c === 'string') return []; if (Array.isArray(c)) return c.flatMap(condTexts); const o = []; if (c.text) o.push(c.text); arr(c.all).concat(arr(c.any)).forEach(x => o.push(...condTexts(x))); return o; }
function condExprs(c){ if (!c) return []; if (typeof c === 'string') return [c]; if (Array.isArray(c)) return c.flatMap(condExprs); return arr(c.all).concat(arr(c.any)).flatMap(condExprs); }

const LOCALE = () => (S.M && S.M.app.locale) || 'en-IN';
function money(v){ try { return new Intl.NumberFormat(LOCALE(), { style: 'currency', currency: (S.M && S.M.app.currency) || 'USD', maximumFractionDigits: 0 }).format(+v); } catch (e) { return String(v); } }
function fdate(v){ const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleDateString(LOCALE(), { day: 'numeric', month: 'short', year: 'numeric' }); }
function fdt(v){ const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleDateString(LOCALE(), { day: 'numeric', month: 'short' }) + ', ' + d.toLocaleTimeString(LOCALE(), { hour: '2-digit', minute: '2-digit' }); }
function rel(v){ const d = (Date.now() - new Date(v).getTime()) / 1000; if (d < 60) return 'just now'; if (d < 3600) return Math.floor(d / 60) + 'm ago'; if (d < 86400) return Math.floor(d / 3600) + 'h ago'; if (d < 86400 * 30) return Math.floor(d / 86400) + 'd ago'; return fdate(v); }
function txt(f, v, E){
  if (empty(v)) return '';
  const t = f && f.type;
  if (t === 'status'){ const s = E && E.wf && E.wf.smap[v]; return s ? s.label : titleize(v); }
  if (t === 'tags') return arr(v).map(c => { const tg = E && E.wf && E.wf.tmap[c]; return tg ? tg.label : titleize(c); }).join(', ');
  if (t === 'choice'){ const o = (f.opts || []).find(o => o.id == v); return o ? o.label : String(v); }
  if (t === 'multi_choice') return arr(v).map(x => txt({ ...f, type: 'choice' }, x)).join(', ');
  if (t === 'link'){ if (f.to === 'app_user') return String(v); const T = S.M.ents[f.to]; const r = T && getRow(T.code, v); return r ? String(plain(T, r, T.display) || '#' + r.id) : ''; }
  if (t === 'multi_link') return arr(v).map(x => txt({ ...f, type: 'link' }, x)).join(', ');
  if (t === 'boolean') return v ? 'Yes' : 'No';
  if (t === 'money') return money(v);
  if (t === 'percent') return Math.round(+v) + '%';
  if (t === 'date') return fdate(v);
  if (t === 'datetime') return fdt(v);
  if (t === 'integer' && /year|yob|^yr/.test(f.key || '')) return String(v);
  if (t === 'decimal' || t === 'integer') return (+v).toLocaleString(LOCALE());
  return String(v);
}
function plain(E, row, path){ const r = rp(E, row, path); return txt(r.f, r.v, r.E); }
function interp(tpl, E, row){ return String(tpl).replace(/\{([^}]+)\}/g, (m, p) => plain(E, row, p.trim()) || '—'); }
function fmt(f, v, opt){
  opt = opt || {};
  if (empty(v)) return '<span class="z-nil">—</span>';
  const t = f && f.type;
  switch (t){
    case 'status': { const s = opt.E && opt.E.wf && opt.E.wf.smap[v]; return badge(s ? s.label : titleize(v), s ? s.color : 'gray'); }
    case 'tags': return arr(v).map(c => { const tg = opt.E && opt.E.wf && opt.E.wf.tmap[c]; return chip(tg ? tg.label : titleize(c), tg ? tg.color : 'gray'); }).join('');
    case 'choice': { const o = (f.opts || []).find(o => o.id == v); return o && o.color ? badge(o.label, o.color) : esc(o ? o.label : v); }
    case 'link': {
      if (f.to === 'app_user') return esc(v);
      const T = S.M.ents[f.to]; const r = T && getRow(T.code, v); if (!r) return '<span class="z-nil">—</span>';
      const label = plain(T, r, opt.display || T.display) || '#' + r.id;
      const dv = T.dv; const page = dv && dv.page;
      if (opt.link !== false && page && canPage(page) && visibleRows(T).includes(r)) return `<a class="z-link" data-a="${A(e => { e.stopPropagation(); nav(page.code, r.id); })}">${esc(label)}</a>`;
      return esc(label);
    }
    case 'boolean': return v ? '<span class="z-yes">Yes</span>' : '<span class="z-no">No</span>';
    case 'money': case 'percent': case 'integer': case 'decimal': return `<span class="z-num">${esc(txt(f, v))}</span>`;
    case 'file': return `<span class="z-file">${ic('paperclip')}${esc(v)}</span>`;
    case 'url': return `<a class="z-link" href="#" onclick="return false">${esc(v)}</a>`;
    case 'long_text': return `<span title="${esc(v)}">${esc(String(v).length > 70 && !opt.full ? String(v).slice(0, 70) + '…' : v)}</span>`;
    default: return esc(txt(f, v, opt.E));
  }
}

/* ═════════════════════════ access ═════════════════════════ */
function can(E, action, role){
  role = role || S.role;
  if (!E.acc) return true;
  const a = E.acc[role]; if (!a || a.none) return false;
  if (action === 'view' || action === 'detail') return true;
  return a.actions.has(action);
}
function memVisible(E, role){
  role = role || S.role;
  if (!can(E, 'view', role)) return [];
  const rows = rowsOf(E.code); const a = E.acc && E.acc[role]; const sc = a && a.rows;
  if (!sc || sc === 'all') return rows;
  if (sc === 'created_by_me') return rows.filter(r => r.created_by === curUser());
  if (isObj(sc) && sc.own){ const me = S.me[role]; if (!me) return []; return rows.filter(r => sc.own === 'id' ? (E.code === me.entity && r.id === me.id) : rp(E, r, sc.own).v === me.id); }
  if (isObj(sc) && sc.where) return rows.filter(r => evalCond(sc.where, { E, row: r }) !== false);
  return rows;
}
function scopeLabel(sc){ if (!sc || sc === 'all') return 'all rows'; if (sc === 'created_by_me') return 'created by me'; if (sc.own) return `own via ${sc.own}`; if (sc.where) return sc.where; if (sc.text) return 'custom: ' + sc.text; return JSON.stringify(sc); }
function canPage(p, role){
  role = role || S.role; if (!p) return false;
  if (p.roles && !arr(p.roles).includes(role)) return false;
  if (p.type === 'crud') return !!S.M.ents[p.entity] && can(S.M.ents[p.entity], 'view', role);
  if (p.type === 'detail'){ const dv = S.M.dvs[p.detail_view]; if (!dv) return false; if (dv.roles && !arr(dv.roles).includes(role)) return false; return !!S.M.ents[dv.hero] && can(S.M.ents[dv.hero], dv.auto ? 'view' : 'detail', role); }
  return true;
}
const roleOK = x => !x || !x.roles || arr(x.roles).includes(S.role);
const showOK = (x, E, row) => !x || !x.show_when || evalCond(x.show_when, { E, row }) !== false;

/* Spec paths on what the preview draws, so the user can point at it ("make this bigger") and the
   agent knows which part of the YAML they mean. Paths are the spec tools' (@code, @key, index). */
const AUTO_PATHS = [];
const zp = (path, label) => H.preview && path && !AUTO_PATHS.some(a => path === a || path.startsWith(a + '/')) ? ` data-zas-path="${esc(path)}"${label ? ` data-zas-label="${esc(label)}"` : ''}` : '';
const entPath = E => E && E.module && E.module.code ? `/modules/@${E.module.code}/entities/@${E.code}` : '';
const stateBox = (i, t, d, extra) => `<div class="z-state"><div class="ei">${ic(i)}</div><b>${esc(t)}</b><div>${esc(d || '')}</div>${extra || ''}</div>`;
/* ═════════════════════════ tables ═════════════════════════ */
function colsFor(E, spec){
  if (!spec || spec === 'inherit') return E.cols;
  return kv(spec).map(c => { const base = E.cols.find(x => x.key === c.key); return base ? { ...base, ...c, source: base.source, label: c.label || base.label } : normCol(E, c); });
}
function cellOf(E, row, c){
  if (c.source === 'status') return { v: row.status, f: { type: 'status' }, E };
  if (c.source === 'tags') return { v: row.tags, f: { type: 'tags' }, E };
  if (c.source === 'computed' && !c.path) return { v: H.computed(E, row, c), f: { type: c.format || 'text' }, E, computed: true };
  const r = rp(E, row, c.path || c.key);
  if (c.format && r.f) r.f = { ...r.f, type: c.format === 'number' ? 'decimal' : c.format };
  return r;
}
/* A record code ("CP-006", "VEN-00012"): drawn in mono, as the runtime does (ZasTable CODE_RE). */
const CODE_RE = /^[A-Z][A-Z0-9]{0,6}[-\/]\d[\w-]*$/;
function cellHTML(E, row, c){
  const r = cellOf(E, row, c);
  if (r.computed && r.v == null) return `<span class="z-comp" title="${esc(c.shows || 'computed')}">${esc(c.label)}</span>`;
  let h = fmt(r.f, r.v, { E: r.E || E, display: c.display });
  if (c.source !== 'status' && typeof r.v === 'string' && CODE_RE.test(r.v.trim())) h = `<span class="z-code">${h}</span>`;
  if (r.computed) h = `<span class="z-comp" title="Computed (dummy value): ${esc(c.shows || '')}">${h}</span>`;
  if (c.link_to && S.M.dvs[c.link_to] && S.M.dvs[c.link_to].page && S.M.dvs[c.link_to].hero === E.code && r.f && r.f.type !== 'link') h = `<a class="z-link" data-a="${A(e => { e.stopPropagation(); nav(S.M.dvs[c.link_to].page.code, row.id); })}">${h}</a>`;
  // table.columns[].badge: a pill after the value on the rows where `when` holds
  const bd = isObj(c.badge) ? c.badge : null;
  if (bd && bd.label && bd.when != null && H.fact('badge', E, row, c)){ const t = tone(bd.tone || 'gray'); h += `<span class="z-cpill" style="background:${t[0]};color:${t[1]};border-color:${t[2]}">${esc(bd.label)}</span>`; }
  // table.columns[].progress: a status column's step bar and "Step i of n" (the workflow's order, or steps)
  if (c.progress && c.source === 'status' && E.wf){
    const steps = isObj(c.progress) && arr(c.progress.steps).length ? arr(c.progress.steps).map(String) : E.wf.statuses.map(s => s.code);
    const at = steps.indexOf(row.status);
    if (at >= 0) h = `<div class="z-cprog"><span>${h}</span><div class="z-cprog-bar">${steps.map((x, i) => `<i${i <= at ? ' class="on"' : ''}></i>`).join('')}</div><div class="z-cprog-t">Step ${at + 1} of ${steps.length}</div></div>`;
  }
  // table.columns[].secondary / icon: an icon, the value, and a muted second line (as the app draws it)
  const sub = c.secondary ? H.fact('secondary', E, row, c) || '' : '';
  const icn = H.fact('icon', E, row, c);
  if (!sub && !icn) return h;
  const ico = icn === 'initials' ? `<span class="z-cell-ico ini">${esc(initialsOf(txt(r.f, r.v, r.E || E)))}</span>` : icn ? `<span class="z-cell-ico">${ic(icn)}</span>` : '';
  return `<div class="z-cell2">${ico}<div class="z-cell-txt"><div class="z-cell-main">${h}</div>${sub ? `<div class="z-cell-sub${c.secondary_style === 'mono' ? ' mono' : ''}">${esc(sub)}</div>` : ''}</div></div>`;
}
const initialsOf = t => String(t || '').split(/\s+/).filter(w => /^[A-Za-z]/.test(w)).slice(0, 2).map(w => w[0].toUpperCase()).join('');
function cellIcon(E, row, icon){
  if (!icon) return null;
  if (typeof icon === 'string') return icon;
  if (!icon.by) return icon.default || null;
  let raw; try { raw = rp(E, row, icon.by).v; } catch (e) { raw = undefined; }
  const map = icon.map || {}; return map[String(raw)] || icon.default || null;
}
function tState(key, init){ return S.ui.tables[key] || (S.ui.tables[key] = { q: '', sort: init.sort || null, filters: {}, qf: init.qf || null, page: 1, fopen: false }); }
function filterOpts(E, c){
  if (c.source === 'status') return (E.wf ? E.wf.statuses : []).map(s => [s.code, s.label]);
  if (c.source === 'tags') return (E.wf ? E.wf.tags : []).map(s => [s.code, s.label]);
  const f = E.fmap[c.key];
  if (!f) return [];
  if (f.opts) return f.opts.map(o => [o.id, o.label]);
  if (f.type === 'boolean') return [['true', 'Yes'], ['false', 'No']];
  return H.options(E, c, f);
}
/* The filter panel, as the crud table draws it: one control per filterable column. Choices, status,
   tags, yes/no and links pick a value; dates take a from–to range; the rest match text. */
function filterKind(E, c){
  if (c.source === 'status' || c.source === 'tags') return 'select';
  const f = E.fmap[c.key];
  if (!f) return 'select';
  if (f.opts || ['boolean', 'link'].includes(f.type)) return 'select';
  if (['date', 'datetime'].includes(f.type)) return 'date';
  return 'text';
}
// as the crud endpoint applies them: a text filter matches exactly (iexact), a date range once both ends are set
const filterOn = v => v != null && v !== '' && (typeof v !== 'object' || (v.q != null ? !!String(v.q).trim() : !!(v.from && v.to)));
function filterHit(E, row, c, v){
  const cv = cellOf(E, row, c).v;
  if (typeof v === 'string') return Array.isArray(cv) ? cv.map(String).includes(v) : String(cv) === v;
  if (v.q != null){ const x = cellOf(E, row, c); return txt(x.f, x.v, x.E || E).trim().toLowerCase() === String(v.q).trim().toLowerCase(); }
  const d = cv == null ? '' : String(cv).slice(0, 10);
  return !!d && d >= v.from && d <= v.to;
}
function filterPanel(E, key, st, filt){
  const set = (k, v) => { st.filters[k] = v; st.page = 1; rerender(); };
  const fid = k => 'f_' + (key + '_' + k).replace(/\W/g, '_');
  const fields = filt.map(c => {
    const kind = filterKind(E, c), v = st.filters[c.key];
    let ctl;
    if (kind === 'select') ctl = `<select class="z-fin" data-ch="${A(x => set(c.key, x))}"><option value="">Select ${esc(c.label)}</option>${filterOpts(E, c).map(([o, l]) => `<option value="${esc(o)}" ${v === o ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select>`;
    else if (kind === 'date') { const d = isObj(v) ? v : {}; ctl = `<div class="z-fin z-fdate"><input type="date" value="${esc(d.from || '')}" data-ch="${A(x => set(c.key, { ...d, from: x }))}">${ic('arrow-right')}<input type="date" value="${esc(d.to || '')}" data-ch="${A(x => set(c.key, { ...d, to: x }))}">${ic('calendar')}</div>`; }
    else ctl = `<label class="z-fin z-ftext">${ic('search')}<input id="${fid(c.key)}" value="${esc(isObj(v) ? v.q || '' : '')}" placeholder="Search ${esc(c.label.toLowerCase())}" data-in="${A(x => set(c.key, { q: x }))}"></label>`;
    return `<div class="z-ff"><span>${esc(c.label)}</span>${ctl}</div>`;
  }).join('');
  const close = A(() => { st.fopen = false; rerender(); });
  return `<aside class="z-card z-fpanel" data-zas-chrome><div class="z-fph"><b>Filters</b><button class="z-ib" title="Close" data-a="${close}">${ic('x')}</button></div><div class="z-fpb">${fields}</div>
    <div class="z-fpf"><span>Results update as you choose.</span><button class="z-flink" data-a="${A(() => { st.filters = {}; st.page = 1; rerender(); })}">Clear all</button><button class="z-btn pri xs" data-a="${close}">Done</button></div></aside>`;
}
function sortKey(E, row, c){ const r = cellOf(E, row, c); if (r.v == null) return ''; if (typeof r.v === 'number') return r.v; if (r.f && ['date', 'datetime'].includes(r.f.type)) return String(r.v); return txt(r.f, r.v, r.E || E).toLowerCase(); }
/* cfg: key, E, rows, cols, rowClick, pageSize, quick, add, footer, group_by, empty, hero */
function renderTable(cfg){
  const { E } = cfg;
  // Pointing: the whole card is the entity's table, a cell its column, a chip its quick filter.
  const tPath = entPath(E) ? `${entPath(E)}/table` : '';
  const card = `<div class="z-card"${zp(tPath, `${E.plural} table`)}>`;
  const cols = cfg.cols.filter(c => !c.roles || c.roles.includes(S.role));
  const quick = arr(cfg.quick).filter(q => roleOK(q));
  const ds = cfg.defaultSort || E.table.default_sort || '-created_at';
  const st = tState(cfg.key, { sort: ds, qf: null });
  const ps = cfg.pageSize || E.table.page_size || 10;
  // The host searches, filters, sorts and pages (the preview in memory, the app on the server):
  // rows = every match in order (views and footer totals), pageRows = this page's.
  const res = H.query({ ...cfg, cols, quick, ps }, st);
  const rows = res.rows, total = res.total, pages = Math.max(1, Math.ceil(total / ps)), pageRows = res.pageRows;
  const filt = cols.filter(c => c.filterable);
  const id = 'q_' + cfg.key.replace(/\W/g, '_');
  const nf = Object.values(st.filters).filter(filterOn).length;
  const qPath = q => arr(E.table.quick_filters).includes(q) ? zp(`${tPath}/quick_filters/${arr(E.table.quick_filters).indexOf(q)}`, `${q.label} filter`) : '';
  // table.status_tabs (default on): no quick filters, a filterable status column → All + a tab per status, the
  // same filter as the panel's Status (the crud endpoint's column filter)
  const stc = !quick.length && E.wf && E.table.status_tabs !== false ? filt.find(c => c.source === 'status') : null;
  const stTabs = stc ? `<div class="z-chips"><button class="z-qf ${filterOn(st.filters[stc.key]) ? '' : 'on'}" data-zas-chrome data-a="${A(() => { st.filters[stc.key] = ''; st.page = 1; rerender(); })}">All</button>${E.wf.statuses.map(x => `<button class="z-qf ${st.filters[stc.key] === x.code ? 'on' : ''}" data-zas-chrome data-a="${A(() => { st.filters[stc.key] = x.code; st.page = 1; rerender(); })}">${esc(x.label)}</button>`).join('')}</div>` : '';
  let tb = `<div class="z-tb"><label class="z-search">${ic('search')}<input id="${id}" placeholder="Search ${esc(E.plural.toLowerCase())}" value="${esc(st.q)}" data-in="${A(v => { st.q = v; st.page = 1; rerender(); })}"></label>
    ${quick.length ? `<div class="z-chips"><button class="z-qf ${st.qf ? '' : 'on'}" data-zas-chrome data-a="${A(() => { st.qf = null; st.page = 1; rerender(); })}">All<span class="z-qf-n">${res.count(null)}</span></button>${quick.map(q => `<button class="z-qf ${st.qf === q.label ? 'on' : ''}"${qPath(q)} data-a="${A(() => { st.qf = st.qf === q.label ? null : q.label; st.page = 1; rerender(); })}">${esc(q.label)}${q.count ? `<span class="z-qf-n">${res.count(q)}</span>` : ''}</button>`).join('')}</div>` : stTabs}
    <span class="sp"></span>${cfg.right || ''}${filt.length ? `<button class="z-ibb ${st.fopen ? 'on' : ''}" title="Filters" data-zas-chrome data-a="${A(() => { st.fopen = !st.fopen; rerender(); })}">${ic('filter')}${nf ? `<span class="z-fbadge">${nf}</span>` : ''}</button>` : ''}</div>`;
  const withFilters = inner => st.fopen && filt.length ? `<div class="z-lwrap">${inner}${filterPanel(E, cfg.key, st, filt)}</div>` : inner;
  if (cfg.view && cfg.view.type !== 'table') return withFilters(`${card}${tb}<div style="display:contents"${cfg.page ? zp(`/pages/@${cfg.page.code}/views/${S.views[cfg.page.code] || 0}`, `${cfg.view.type} view`) : ''}>${viewHTML(cfg, rows)}</div></div>`);
  const hasActs = pageRows.some(r => rowActions(E, r).length);
  const chev = !(E.table && E.table.row_chevron === false);  // table.row_chevron (default on): a chevron in a last cell of clickable rows
  const colPath = c => entPath(E) ? (E.table && E.table.columns ? `${entPath(E)}/table/columns/@${c.key}` : `${entPath(E)}/table`) : '';
  const th = cols.map(c => { const sortable = c.sortable; const k = c.key; const on = st.sort && st.sort.replace(/^-/, '') === k; return `<th${zp(colPath(c), `${c.label} column`)}>${sortable ? `<button data-a="${A(() => { st.sort = on && st.sort[0] !== '-' ? '-' + k : k; rerender(); })}">${esc(c.label)}${ic(on ? (st.sort[0] === '-' ? 'arrow-down' : 'arrow-up') : 'chevrons-up-down')}</button>` : esc(c.label)}</th>`; }).join('') + (hasActs ? '<th></th>' : '') + (chev ? '<th></th>' : '');
  const rowTr = r => {
    const click = cfg.rowClick ? A(() => cfg.rowClick(r)) : null;
    const acts = rowActions(E, r);
    return `<tr ${click != null ? `class="click" data-a="${click}"` : ''}>${cols.map(c => { let cls = ''; if (c.highlight && H.fact('highlight', E, r, c)) cls = 'hl-' + (c.highlight.tone || 'red'); return `<td class="${cls}"${zp(colPath(c), `${c.label} column`)}>${cellHTML(E, r, c)}</td>`; }).join('')}${hasActs ? `<td class="act">${acts.length ? `<button class="z-kebab" data-a="${A((e, el) => { e.stopPropagation(); menu(el, acts); })}">${ic('ellipsis-vertical')}</button>` : ''}</td>` : ''}${chev ? `<td class="chev">${click != null ? ic('chevron-right') : ''}</td>` : ''}</tr>`;
  };
  let body;
  if (cfg.group_by){ const groups = {}; pageRows.forEach(r => { const g = plain(E, r, cfg.group_by) || '—'; (groups[g] = groups[g] || []).push(r); }); body = Object.entries(groups).map(([g, rs]) => `<tr class="grp"><td colspan="${cols.length + (hasActs ? 1 : 0) + (chev ? 1 : 0)}">${esc(g)} · ${rs.length}</td></tr>` + rs.map(rowTr).join('')).join(''); }
  else body = pageRows.map(rowTr).join('');
  const foot = arr(cfg.footer).length ? `<tfoot><tr>${cols.map((c, i) => { if (arr(cfg.footer).includes(c.key)){ const sum = rows.reduce((a, r) => a + (+cellOf(E, r, c).v || 0), 0); return `<td>${fmt(cellOf(E, rows[0] || {}, c).f || { type: 'decimal' }, sum)}</td>`; } return `<td>${i === 0 ? 'Total' : ''}</td>`; }).join('')}${hasActs ? '<td></td>' : ''}${chev ? '<td></td>' : ''}</tr></tfoot>` : '';
  const em = cfg.empty || {};
  const emptyHTML = `<div class="z-empty"><div class="ei">${ic('inbox')}</div><b>${esc(st.q || st.qf || Object.values(st.filters).some(Boolean) ? 'No matching records' : em.title || `No ${E.plural.toLowerCase()} yet`)}</b><p>${esc(st.q || st.qf ? 'Try clearing the search or filters.' : em.text || '')}</p>${!st.q && em.cta === 'add' && cfg.addBtn ? cfg.addBtn : ''}</div>`;
  const goPage = n => A(() => { if (n >= 1 && n <= pages && n !== st.page){ st.page = n; rerender(); } });
  const nums = pages <= 7 ? [...Array(pages).keys()].map(i => i + 1) : [...new Set([1, st.page - 1, st.page, st.page + 1, pages])].filter(n => n >= 1 && n <= pages).sort((a, b) => a - b);
  const pager = `<span class="z-pager"><button ${st.page <= 1 ? 'disabled' : ''} data-a="${goPage(st.page - 1)}">${ic('chevron-left')}</button>${nums.map((n, i) => `${i && n - nums[i - 1] > 1 ? '<span class="gap">…</span>' : ''}<button class="${n === st.page ? 'on' : ''}" data-a="${goPage(n)}">${n}</button>`).join('')}<button ${st.page >= pages ? 'disabled' : ''} data-a="${goPage(st.page + 1)}">${ic('chevron-right')}</button></span>`;
  return withFilters(`${card}${tb}${total ? `<div class="z-tbl-w"><table class="z-t"><thead><tr>${th}</tr></thead><tbody>${body}</tbody>${foot}</table></div>
    <div class="z-pg" data-zas-chrome><span>Showing <b>${(st.page - 1) * ps + 1}–${Math.min(total, st.page * ps)}</b> of <b>${total}</b></span><span class="z-pgsz">${ps} / page</span><span class="sp"></span>${pager}</div>` : emptyHTML}</div>`);
}
function rowClickFor(E, target){
  target = target || E.table.row_click || (E.dv ? E.dv.code : 'drawer');
  if (target === 'none') return null;
  if (String(target).includes('#')){
    const [vc, tc] = String(target).split('#'); const dv = S.M.dvs[vc]; const tb = dv && arr(dv.tabs).find(t => t.code === tc);
    if (dv && tb && dv.page && canPage(dv.page)) return r => { const pid = rp(E, r, tb.via).v; return pid ? nav(dv.page.code, pid, tc) : drawer(E, r); };
    return r => drawer(E, r);
  }
  if (S.M.dvs[target]){ const dv = S.M.dvs[target]; if (dv.page && canPage(dv.page) && dv.hero === E.code) return r => nav(dv.page.code, r.id); return r => drawer(E, r); }
  const ra = E.ractions.find(a => a.key === target); if (ra) return r => H.act('row_action', { E, row: r, a: ra });
  return r => drawer(E, r);
}
/* pages[].subtitle: its text, then " · " and the stat's live figure ({count | sum, where, format, suffix}) */
function pageSubtitle(E, p, rows){
  const sub = typeof p.subtitle === 'string' ? { text: p.subtitle } : p.subtitle;
  if (!sub || typeof sub !== 'object') return null;
  let figure = '';
  const st = sub.stat;
  if (st && typeof st === 'object'){
    const v = H.stat(E, rows, st);
    figure = [txt({ type: st.format || (st.sum ? 'decimal' : 'integer') }, v, E) || String(v), st.suffix].filter(Boolean).join(' ');
  }
  const out = [sub.text, figure].filter(Boolean).join(' · ');
  return out || null;
}
/* pages[].stats: KPI tiles over the page's rows ({label, count | sum, where, format, icon, tone, hint}) */
function listStats(E, p, rows){
  const tiles = arr(p.stats).filter(t => isObj(t) && t.label);
  if (!tiles.length) return '';
  return `<div class="z-lstats"${zp(`/pages/@${p.code}/stats`, 'KPI tiles')}>${tiles.map((t, i) => {
    const v = H.stat(E, rows, t);
    const c = tone(t.tone || ['indigo', 'teal', 'amber', 'pink', 'blue', 'purple'][i % 6]);
    return `<div class="z-lstat"${zp(`/pages/@${p.code}/stats/${i}`, t.label)}><div class="si" style="background:${c[0]};color:${c[1]}">${ic(t.icon || ['activity', 'wallet', 'clock', 'gauge', 'layers', 'target'][i % 6])}</div><div style="flex:1;min-width:0"><span>${esc(t.label)}</span><b>${esc(fmtStat(v, t.format))}</b>${t.hint ? `<span class="z-lstat-hint">${esc(t.hint)}</span>` : ''}</div></div>`;
  }).join('')}</div>`;
}
function renderCrud(E, p){
  const rows = visibleRows(E);
  const addLabel = E.table.add_button || `Add ${E.name}`;
  const canAdd = can(E, 'add') && E.form.create && roleOK(E.form.create);
  const addBtn = canAdd ? `<button class="z-btn pri"${zp(entPath(E) ? `${entPath(E)}/form/create` : '', `${addLabel} form`)} data-a="${A(() => H.act('create', { E, title: E.table.add_button }))}">${ic('plus')}${esc(addLabel)}</button>` : '';
  const exp = can(E, 'export') ? `<button class="z-btn sm" data-a="${A(() => H.act('export', { E, count: H.stat(E, rows, null) }))}">${ic('download')}Export</button>` : '';
  const sc = E.acc && E.acc[S.role] && E.acc[S.role].rows;
  const sub = pageSubtitle(E, p, rows);
  // the record count sits in the title ("Vendors (12)"); the line under it is the page's subtitle, if any
  return `<div class="z-ph"${zp(`/pages/@${p.code}`, p.title)}><div><h1>${esc(p.title)} <span class="z-hc" data-zas-chrome>(${H.stat(E, rows, null)})</span></h1>${sub != null ? `<p>${esc(sub)}</p>` : sc && sc !== 'all' ? `<p data-zas-chrome>Scoped to <b>${esc(scopeLabel(sc))}</b></p>` : ''}</div><span class="sp"></span>${aiListButtons(E, rows)}${addBtn}</div>
    ${listStats(E, p, rows)}${renderTable({ key: 'crud_' + E.code, E, rows, cols: E.cols, rowClick: rowClickFor(E), quick: E.table.quick_filters, right: viewSwitch(p) + exp, empty: { cta: 'add' }, addBtn, footer: E.table.footer_totals, group_by: E.table.group_by, view: curView(p), page: p })}`;
}

/* ═════════════════════════ list views ═════════════════════════ */
function curView(p){ if (!p.views || !p.views.length) return null; const i = S.views[p.code] || 0; return p.views[i] || p.views[0]; }
function viewSwitch(p){
  if (!p.views || p.views.length < 2) return '';
  const cur = S.views[p.code] || 0;
  return `<div class="z-vsw" role="tablist" aria-label="View">${p.views.map((v, i) => `<button class="${i === cur ? 'on' : ''}"${zp(`/pages/@${p.code}/views/${i}`, v.label || VIEW_LABEL[v.type] || v.type)} title="${esc(v.label || VIEW_LABEL[v.type] || v.type)}" data-a="${A(() => { S.views[p.code] = i; rerender(); })}">${ic(VIEW_TYPES[v.type] || 'square')}${esc(v.label || VIEW_LABEL[v.type] || titleize(v.type))}</button>`).join('')}</div>`;
}
function viewHTML(cfg, rows){
  const v = cfg.view;
  if (v.type === 'kanban') return kanbanHTML(cfg, v, rows);
  if (v.type === 'cards') return cardsHTML(cfg, v, rows);
  if (v.type === 'calendar') return calendarHTML(cfg, v, rows);
  if (v.type === 'timeline') return tlViewHTML(cfg, v, rows);
  return stateBox('square', 'Unknown view', v.type);
}
function cardInner(E, card, row){
  card = card || {};
  const title = plain(E, row, card.title || E.display) || `${E.name} #${row.id}`;
  const sub = card.subtitle ? plain(E, row, card.subtitle) : '';
  const fl = arr(card.fields).map(k => { const r = rp(E, row, k); const f = r.f || E.fmap[k]; const lab = (f && f.label) || titleize(String(k).split('.').pop()); return `<span><em>${esc(lab)}</em>${fmt(r.f, r.v, { E: r.E || E, link: false })}</span>`; }).join('');
  let bd = '';
  if (card.badge){
    const r = rp(E, row, card.badge); const f = r.f || (card.badge === 'status' ? { type: 'status' } : null);
    if (!empty(r.v)) bd = `<div class="bd">${f && ['status', 'tags', 'choice'].includes(f.type) ? fmt(f, r.v, { E: r.E || E }) : badge(txt(f, r.v, r.E || E), 'gray')}</div>`;
  }
  return `<b>${esc(title)}</b>${sub ? `<div class="sub">${esc(sub)}</div>` : ''}${fl ? `<div class="fl">${fl}</div>` : ''}${bd}`;
}
function groupsFor(E, key, rows){
  if (key === 'status' && E.wf) return E.wf.statuses.map(s => ({ v: s.code, label: s.label, color: s.color }));
  const f = E.fmap[key];
  if (f && f.opts) return f.opts.map(o => ({ v: o.id, label: o.label, color: o.color || 'gray' }));
  if (f && f.type === 'boolean') return [{ v: true, label: 'Yes', color: 'green' }, { v: false, label: 'No', color: 'gray' }];
  const seen = []; rows.forEach(r => { const x = r[key]; if (!seen.some(g => g.v == x)) seen.push({ v: x, label: x == null ? '—' : txt(f, x, E) || String(x), color: 'gray' }); });
  return seen;
}
function moveMode(E, v){ return v.move || (v.group_by === 'status' ? 'transitions' : 'update'); }
function kanbanHTML(cfg, v, rows){
  const E = cfg.E; const key = v.group_by || (E.wf ? 'status' : null);
  if (!key) return stateBox('kanban', 'Board needs group_by', 'Set group_by to status or a choice field.');
  let groups = groupsFor(E, key, rows);
  if (v.columns) groups = v.columns.map(c => groups.find(g => String(g.v) === String(c)) || { v: c, label: titleize(c), color: 'gray' });
  const mode = moveMode(E, v);
  const click = cfg.rowClick;
  const bid = 'kb_' + cfg.key.replace(/\W/g, '_');
  S.kb = S.kb || {}; S.kb[bid] = { e: E.code, key, mode, view: v };
  const draggable = r => mode === 'none' ? false : mode === 'transitions' ? !!(E.wf && E.wf.trs.some(t => trAllowed(t, r))) : can(E, 'edit') && editableNow(E, r) !== false;
  return `<div class="kb" data-kboard="${bid}">${groups.map(g => {
    const rs = rows.filter(r => String(r[key]) === String(g.v));
    const c = tone(g.color);
    return `<div class="kb-col" data-kcol="${esc(String(g.v))}"><div class="kb-h"><i class="dot" style="background:${c[1]}"></i>${esc(g.label)}<span class="n">${rs.length}</span></div>
      <div class="kb-b">${rs.length ? rs.map(r => `<div class="kb-card" ${draggable(r) ? 'draggable="true"' : ''} data-kcard="${r.id}" ${click ? `data-a="${A(() => click(r))}"` : ''}>${cardInner(E, v.card, r)}</div>`).join('') : '<div class="kb-empty">Nothing here</div>'}</div></div>`;
  }).join('')}</div>`;
}
function cardsHTML(cfg, v, rows){
  const E = cfg.E; const click = cfg.rowClick;
  if (!rows.length) return `<div class="z-empty"><div class="ei">${ic('inbox')}</div><b>No ${esc(E.plural.toLowerCase())}</b></div>`;
  return `<div class="vc-grid">${rows.map(r => { const t = plain(E, r, (v.card && v.card.title) || E.display) || '#' + r.id; return `<div class="vc-card" ${click ? `data-a="${A(() => click(r))}"` : ''}><div class="vc-img" style="background:${avColor(t)}">${v.card && v.card.image && r[v.card.image] ? ic('image') : esc(initials(t))}</div><div class="vc-in">${cardInner(E, v.card, r)}</div></div>`; }).join('')}</div>`;
}
const ymd = d => `${d.getFullYear()}-${pad(d.getMonth() + 1, 2)}-${pad(d.getDate(), 2)}`;
function calendarHTML(cfg, v, rows){
  const E = cfg.E; const click = cfg.rowClick; const key = 'cal_' + cfg.key;
  if (!v.date_field) return stateBox('calendar-days', 'Calendar needs date_field', '');
  const now = new Date(); const ym = S.views[key] || `${now.getFullYear()}-${pad(now.getMonth() + 1, 2)}`;
  const [Y, Mo] = ym.split('-').map(Number); const first = new Date(Y, Mo - 1, 1);
  const shift = n => { const d = new Date(Y, Mo - 1 + n, 1); S.views[key] = `${d.getFullYear()}-${pad(d.getMonth() + 1, 2)}`; rerender(); };
  const start = new Date(first); start.setDate(1 - ((first.getDay() + 6) % 7));
  const byDay = {}; const undated = [];
  const colorOf = r => { if (!v.color_by) return 'indigo'; if (v.color_by === 'status' && E.wf){ const s = E.wf.smap[r.status]; return s ? s.color : 'gray'; } const f = E.fmap[v.color_by]; const o = f && f.opts && f.opts.find(o => o.id == r[v.color_by]); return (o && o.color) || 'gray'; };
  rows.forEach(r => {
    const a = r[v.date_field]; if (empty(a)){ undated.push(r); return; }
    const s0 = new Date(String(a).slice(0, 10) + 'T00:00:00'); let e0 = v.end_field && r[v.end_field] ? new Date(String(r[v.end_field]).slice(0, 10) + 'T00:00:00') : s0;
    if (isNaN(s0)){ undated.push(r); return; } if (isNaN(e0) || e0 < s0) e0 = s0;
    const span = Math.round((e0 - s0) / 864e5);
    if (span > 14){ (byDay[ymd(s0)] = byDay[ymd(s0)] || []).push({ r, edge: 'start' }); (byDay[ymd(e0)] = byDay[ymd(e0)] || []).push({ r, edge: 'end' }); return; }
    for (let d = new Date(s0), n = 0; d <= e0 && n < 42; d.setDate(d.getDate() + 1), n++) (byDay[ymd(d)] = byDay[ymd(d)] || []).push({ r });
  });
  const title = r => plain(E, r, v.title || E.display) || '#' + r.id;
  const chipFor = ({ r, edge }) => { const c = tone(colorOf(r)); const mark = edge === 'start' ? '▸ ' : edge === 'end' ? '◂ ' : ''; const tip = edge ? `${title(r)} (${edge === 'start' ? 'starts' : 'ends'})` : title(r); return `<div class="cal-e" style="background:${c[0]};color:${c[1]};border-color:${c[2] || c[0]}" title="${esc(tip)}" ${click ? `data-a="${A(e => { e.stopPropagation(); click(r); })}"` : ''}>${mark}${esc(title(r))}</div>`; };
  const today = ymd(now);
  let cells = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => `<div class="dw">${d}</div>`).join('');
  for (let i = 0; i < 42; i++){
    const d = new Date(start); d.setDate(start.getDate() + i); const k = ymd(d); const ev = byDay[k] || [];
    const more = ev.length > 3 ? `<span class="cal-more" data-a="${A((e, el) => { e.stopPropagation(); menu(el, ev.map(({ r, edge }) => ({ label: (edge === 'start' ? '▸ ' : edge === 'end' ? '◂ ' : '') + title(r), icon: 'calendar', run: () => click && click(r) }))); })}">+${ev.length - 3} more</span>` : '';
    cells += `<div class="cal-d ${d.getMonth() !== Mo - 1 ? 'out' : ''} ${k === today ? 'today' : ''}"><span class="dn">${d.getDate()}</span>${ev.slice(0, 3).map(chipFor).join('')}${more}</div>`;
  }
  const label = first.toLocaleDateString(LOCALE(), { month: 'long', year: 'numeric' });
  return `<div class="cal"><div class="cal-m"><div class="cal-h"><h4>${esc(label)}</h4><button class="z-btn sm" title="Previous month" data-a="${A(() => shift(-1))}">${ic('chevron-left')}</button><button class="z-btn sm" data-a="${A(() => { delete S.views[key]; rerender(); })}">Today</button><button class="z-btn sm" title="Next month" data-a="${A(() => shift(1))}">${ic('chevron-right')}</button></div><div class="cal-g">${cells}</div></div>
    ${undated.length ? `<div class="cal-side"><h5>No ${esc(((E.fmap[v.date_field] || BUILTIN_F[v.date_field] || {}).label || titleize(v.date_field)).toLowerCase())} · ${undated.length}</h5>${undated.slice(0, 20).map(r => `<div class="it" ${click ? `data-a="${A(() => click(r))}"` : ''}>${esc(title(r))}</div>`).join('')}</div>` : ''}</div>`;
}
function tlViewHTML(cfg, v, rows){
  const E = cfg.E; const click = cfg.rowClick;
  if (!v.date_field) return stateBox('git-commit-vertical', 'Timeline needs date_field', '');
  const dated = rows.filter(r => !empty(r[v.date_field])).sort((a, b) => String(b[v.date_field]).localeCompare(String(a[v.date_field])));
  const f = E.fmap[v.date_field] || BUILTIN_F[v.date_field] || { type: 'date' };
  const item = r => `<div class="vt-i" ${click ? `data-a="${A(() => click(r))}"` : ''}><div class="dt">${esc(txt(f, r[v.date_field]))}</div><b>${esc(plain(E, r, v.title || E.display) || '#' + r.id)}</b><div class="row2">${E.wf ? fmt({ type: 'status' }, r.status, { E }) : ''}${v.card ? arr(v.card.fields).map(k => esc(plain(E, r, k))).filter(Boolean).join(' · ') : ''}</div></div>`;
  const months = list => { let out = '', last = ''; list.forEach(r => { const d = new Date(String(r[v.date_field]).slice(0, 10)); const m = isNaN(d) ? '' : d.toLocaleDateString(LOCALE(), { month: 'long', year: 'numeric' }); if (m !== last){ out += `<div class="vt-m">${esc(m)}</div>`; last = m; } out += item(r); }); return out; };
  if (!dated.length) return `<div class="z-empty"><div class="ei">${ic('git-commit-vertical')}</div><b>Nothing dated yet</b></div>`;
  if (!v.group_by) return `<div class="vt">${months(dated)}</div>`;
  return `<div class="vt">${groupsFor(E, v.group_by, dated).map(g => { const rs = dated.filter(r => String(r[v.group_by]) === String(g.v)); if (!rs.length) return ''; const c = tone(g.color); return `<div class="vt-lane"><h4><i class="dot" style="width:8px;height:8px;border-radius:50%;background:${c[1]};display:inline-block"></i>${esc(g.label)} <span class="pv-muted">${rs.length}</span></h4>${months(rs)}</div>`; }).join('')}</div>`;
}
function editableNow(E, row){ const ed = E.form.edit; if (!ed) return false; if (ed.editable_in && E.wf && !arr(ed.editable_in).includes(row.status)) return false; return true; }
function trAllowed(t, row){ return !t.system && t.from.includes(row.status) && (!t.roles.length || t.roles.includes(S.role)); }
/* AI helpers (spec ai.agents): where a person can run them. `where` on a button / chat trigger:
   record (the record page, default), row (a list row's menu), list (the list page header),
   form (inside the create / edit form). The host runs them (act 'ai'). */
const aiAgents = E => arr(S.M && S.M.spec && S.M.spec.ai && S.M.spec.ai.agents).filter(a => isObj(a) && a.code && (!E || a.entity === E.code));
const aiName = a => a.name || titleize(a.code);
const aiTrigs = (a, ev) => arr(a.triggers).filter(t => isObj(t) && t.event === ev);
function aiRoleOK(a, t){ const rs = arr((t && t.roles) || (a.access && a.access.roles)); return !rs.length || rs.includes(S.role); }
/* [{agent, trigger}] a person may click at `where` (on `row` when given). */
function aiClicks(E, where, row){
  const out = [];
  aiAgents(E).forEach(a => arr(a.triggers).forEach(t => {
    if (!isObj(t) || !['button', 'chat'].includes(t.event) || (t.where || 'record') !== where || !aiRoleOK(a, t)) return;
    if (row && t.when && evalCond(t.when, { E, row }) === false) return;
    out.push({ agent: a, trigger: t });
  }));
  return out;
}
const aiLabel = (c) => c.trigger.label || (c.trigger.event === 'chat' ? 'Ask AI' : aiName(c.agent));
function aiListButtons(E, rows){
  return aiClicks(E, 'list').map(c => `<button class="z-btn ai"${zp(`/ai/agents/@${c.agent.code}`, aiName(c.agent))} data-a="${A(() => H.act('ai', { E, rows, agent: c.agent, trigger: c.trigger }))}">${ic(c.trigger.icon || (c.trigger.event === 'chat' ? 'message-circle' : 'sparkles'))}${esc(aiLabel(c))}</button>`).join('');
}
function rowActions(E, row, opts){
  opts = opts || {}; const items = [];
  E.ractions.forEach(a => {
    if (a.roles && !a.roles.includes(S.role)) return;
    if (a.type === 'edit' && (!can(E, 'edit') && !a.roles || !editableNow(E, row))) return;
    if (!showOK(a, E, row)) return;
    items.push({ label: a.label, icon: { edit: 'pencil', form: 'square-pen', confirm: 'send', navigate: 'external-link', download: 'download' }[a.type] || 'zap', run: () => H.act('row_action', { E, row, a }) });
  });
  if (!E.ractions.some(a => a.type === 'edit') && can(E, 'edit') && editableNow(E, row) && roleOK(E.form.edit)) items.unshift({ label: 'Edit', icon: 'pencil', run: () => H.act('edit', { E, row }) });
  aiClicks(E, 'row', row).forEach((c, i) => items.push({ group: i === 0 ? 'AI' : null, label: aiLabel(c), icon: c.trigger.icon || 'sparkles', run: () => H.act('ai', { E, row, agent: c.agent, trigger: c.trigger }) }));
  if (can(E, 'delete')) items.push({ label: 'Delete', icon: 'trash-2', tone: 'danger', run: () => H.act('delete', { E, row }) });
  if (E.wf){
    const trs = E.wf.trs.filter(t => trAllowed(t, row));
    if (!opts.noTransitions) trs.forEach((t, i) => items.push({ group: i === 0 ? 'Workflow' : null, label: t.label, icon: t.tone === 'danger' ? 'circle-x' : 'arrow-right-circle', tone: t.tone, run: () => H.act('transition', { E, row, t }) }));
    const tg = E.wf.tags.filter(t => !t.system).map(t => { const on = row.tags.includes(t.code); const side = on ? t.disable : t.enable; if (!side || (side.roles.length && !side.roles.includes(S.role))) return null; return { label: (on ? 'Remove ' : 'Mark ') + t.label, icon: on ? 'tag' : 'tag', run: () => H.act('tag', { E, row, tag: t, on: !on }) }; }).filter(Boolean);
    tg.forEach((x, i) => items.push({ ...x, group: i === 0 ? 'Tags' : null }));
    const sys = E.wf.trs.filter(t => t.system && t.from.includes(row.status));
    sys.forEach((t, i) => items.push({ group: i === 0 ? 'Simulate system' : null, label: t.label, icon: 'cpu', muted: true, run: () => H.act('transition', { E, row, t }) }));
  }
  return items;
}
function fmtStat(v, format){ if (v == null) return '—'; if (format === 'money') return money(v); if (format === 'percent') return Math.round(v <= 1 && v > 0 ? v * 100 : v) + '%'; if (format === 'days') return v + 'd'; return (+v).toLocaleString(LOCALE()); }

/* ═════════════════════════ menus and events ═════════════════════════ */
// items: [{label, icon, run, group?, tone?, muted?}]; close() runs before the item's own run()
function menuHTML(items, close){
  let h = ''; items.forEach((it, i) => { if (it.group) h += `${i ? '<hr>' : ''}<div class="g">${esc(it.group)}</div>`; h += `<button class="${it.tone === 'danger' ? 'danger' : ''} ${it.muted ? 'muted' : ''}" data-a="${A(() => { close(); it.run(); })}">${ic(it.icon || 'dot')}${esc(it.label)}</button>`; });
  return `<div class="z-pop" id="pop">${h}</div>`;
}
/* One delegated listener per kind on a container: data-a (click), data-in (input), data-ch (change).
   The kit has its own on document (it also handles data-go and the popover); the app binds its page. */
function bind(el){
  const on = (type, attr, val) => el.addEventListener(type, e => {
    const t = e.target.closest && e.target.closest(`[${attr}]`); if (!t || !el.contains(t) || t.disabled) return;
    const fn = ACT[+t.getAttribute(attr)]; if (fn) fn(val(e, t), t);
  });
  on('click', 'data-a', e => e);
  on('input', 'data-in', (e, t) => t.value);
  on('change', 'data-ch', (e, t) => t.type === 'checkbox' ? t.checked : t.type === 'file' ? ((t.files[0] || {}).name || '') : t.value);
}

/* ═════════════════════════ in-memory data (the preview's demo rows) ═════════════════════════ */
function memQuery(cfg, st){
  const { E, cols, quick, ps } = cfg;
  let rows = cfg.rows.slice();
  const qf = quick.find(q => q.label === st.qf); if (qf) rows = rows.filter(r => evalCond(qf.where, { E, row: r }) !== false);
  Object.entries(st.filters).forEach(([k, v]) => { if (!filterOn(v)) return; const c = cols.find(x => x.key === k); if (!c) return; rows = rows.filter(r => filterHit(E, r, c, v)); });
  if (st.q){ const q = st.q.toLowerCase(); const sc = cols.filter(c => c.searchable); const scs = sc.length ? sc : cols; rows = rows.filter(r => scs.some(c => { const x = cellOf(E, r, c); return txt(x.f, x.v, x.E || E).toLowerCase().includes(q); })); }
  if (st.sort){ const desc = st.sort[0] === '-'; const k = st.sort.replace(/^-/, ''); const c = cols.find(x => x.key === k) || normCol(E, { key: k }); rows.sort((a, b) => { const x = sortKey(E, a, c), y = sortKey(E, b, c); return (x < y ? -1 : x > y ? 1 : 0) * (desc ? -1 : 1); }); }
  const total = rows.length; const pages = Math.max(1, Math.ceil(total / ps)); if (st.page > pages) st.page = pages;
  return { rows, total, pageRows: rows.slice((st.page - 1) * ps, st.page * ps),
    count: q => q ? cfg.rows.filter(r => evalCond(q.where, { E, row: r }) !== false).length : cfg.rows.length };
}
// def: null (how many rows) or {where, sum} (pages[].subtitle.stat, pages[].stats tiles)
function memStat(E, rows, def){
  if (!def) return rows.length;
  const rs = rows.filter(r => { try { return evalCond(def.where, { E, row: r }) !== false; } catch (e) { return true; } });
  return def.sum ? rs.reduce((a, r) => a + (+r[def.sum] || 0), 0) : rs.length;
}
function memComputed(E, row, c){
  const h = hash(E.code + row.id + c.key);
  return c.format === 'money' ? (h % 900 + 10) * 1000 : c.format === 'percent' ? h % 101 : c.format === 'number' || c.format === 'integer' ? h % 60 : null;
}
function memFact(kind, E, row, c){
  if (kind === 'badge') return evalCond(c.badge.when, { E, row }) === true;
  if (kind === 'highlight') return evalCond(c.highlight.when, { E, row }) === true;
  if (kind === 'secondary') return arr(c.secondary).map(p => { try { const x = rp(E, row, p); return txt(x.f, x.v, x.E || E); } catch (e) { return ''; } }).filter(Boolean).join(' · ');
  if (kind === 'icon') return cellIcon(E, row, c.icon);
  return null;
}
// a filter's options when they come from the rows: a link's records, else the values in use
function memOptions(E, c, f){
  if (f.type === 'link'){ const ids = [...new Set(visibleRows(E).map(r => r[f.key]).filter(v => v != null))]; return ids.map(id => [String(id), txt(f, id)]).sort((a, b) => a[1].localeCompare(b[1])); }
  const vals = [...new Set(rowsOf(E.code).map(r => r[f.key]).filter(v => !empty(v)))].slice(0, 30); return vals.map(v => [String(v), String(v)]);
}
function memory(){
  return {
    computed: memComputed,
    fact: memFact,
    options: memOptions,
    rows: c => (S.db && S.db[c]) || [],
    row: (c, id) => rowsOf(c).find(r => r.id == id),
    visible: memVisible,
    query: memQuery,
    stat: memStat,
  };
}

return Object.freeze({ use, memory, visibleRows, menuHTML, bind, esc, arr, isObj, titleize, empty, hash, pad, todayISO, kv, resetActs, actAt, A, iconOK, ic, paintIcons, TONES, tone, badge, chip, AVC, avColor, initials, BUILTIN, BUILTIN_F, normChoices, normField, normCodes, normAccess, normCol, normEntity, VIEW_TYPES, VIEW_LABEL, normViews, build, LONG_TYPES, autoViews, rowsOf, getRow, curUser, UNK, rp, knownPath, lit, cmp, combine, evalStr, evalCond, condTexts, condExprs, LOCALE, money, fdate, fdt, rel, txt, plain, interp, fmt, can, scopeLabel, canPage, roleOK, showOK, AUTO_PATHS, zp, entPath, stateBox, colsFor, cellOf, CODE_RE, cellHTML, initialsOf, cellIcon, tState, filterOpts, filterKind, filterOn, filterHit, filterPanel, sortKey, renderTable, rowClickFor, pageSubtitle, listStats, renderCrud, curView, viewSwitch, viewHTML, cardInner, groupsFor, moveMode, kanbanHTML, cardsHTML, ymd, calendarHTML, tlViewHTML, editableNow, trAllowed, rowActions, fmtStat, aiAgents, aiName, aiTrigs, aiRoleOK, aiClicks, aiLabel, aiListButtons });
})();
