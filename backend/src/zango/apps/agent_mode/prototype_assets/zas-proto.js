/* ZAS prototype runtime: injected into every open-mode prototype by prototype.assemble().
 * Router, persona switch, in-memory store and files, click delegation, a few helpers,
 * and the bridge to the console (location, errors, goto). The prototype may use all of it,
 * some of it, or register its own navigator with ZAS.ready({go}). */
(function () {
  'use strict';
  var M = {};
  try { M = JSON.parse((document.getElementById('zas-proto') || {}).textContent || '{}'); } catch (e) {}
  M.screens = M.screens || []; M.roles = M.roles || {};
  var roleCodes = Object.keys(M.roles);

  function post(type, data) {
    try { parent.postMessage(Object.assign({ source: 'zas-proto', type: type }, data || {}), '*'); } catch (e) {}
  }
  function partOf(file) { var i = String(file || '').indexOf('proto/'); return i < 0 ? '' : String(file).slice(i + 6); }
  var errors = [];
  function report(part, message, line) {
    var e = { part: part || '', message: String(message || 'Error').slice(0, 500), line: line || 0 };
    errors.push(e); if (errors.length > 50) errors.shift();
    post('error', e);
  }
  window.addEventListener('error', function (ev) { report(partOf(ev.filename), ev.message, ev.lineno); });
  window.addEventListener('unhandledrejection', function (ev) { report('', (ev.reason && ev.reason.message) || ev.reason); });

  /* ---------- helpers ---------- */
  function h(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function I(name, size) {
    return '<i data-lucide="' + h(name) + '" class="zi" style="width:' + (size || 16) + 'px;height:' + (size || 16) + 'px"></i>';
  }
  var fmt = {
    num: function (n, d) { return Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: d == null ? 0 : d }); },
    money: function (n, cur) {
      try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: cur || M.currency || 'USD', maximumFractionDigits: 0 }).format(n || 0); }
      catch (e) { return (cur || '$') + fmt.num(n); }
    },
    date: function (d, opts) { if (!d) return ''; var x = new Date(d); return isNaN(x) ? String(d) : x.toLocaleDateString(undefined, opts || { day: 'numeric', month: 'short', year: 'numeric' }); },
    rel: function (d) {
      if (!d) return ''; var s = (new Date(d) - Date.now()) / 1000, a = Math.abs(s);
      var u = a < 3600 ? ['minute', 60] : a < 86400 ? ['hour', 3600] : a < 2592000 ? ['day', 86400] : ['month', 2592000];
      try { return new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' }).format(Math.round(s / u[1]), u[0]); } catch (e) { return fmt.date(d); }
    }
  };
  function pill(text, tone) { return '<span class="z-pill' + (tone ? ' z-' + h(tone) : '') + '">' + h(text) + '</span>'; }
  function table(o) {
    var cols = o.columns || [], rows = o.rows || [];
    if (!rows.length) return '<div class="z-empty">' + (o.empty || 'Nothing here yet.') + '</div>';
    var head = cols.map(function (c) { return '<th' + (c.align ? ' style="text-align:' + c.align + '"' : '') + '>' + h(c.label) + '</th>'; }).join('');
    var body = rows.map(function (r) {
      var act = o.rowAct ? ' data-act="' + h(o.rowAct) + '" data-id="' + h(r.id) + '" class="z-row"' : '';
      return '<tr' + act + '>' + cols.map(function (c) {
        var v = c.render ? c.render(r) : h(r[c.key]);
        return '<td' + (c.align ? ' style="text-align:' + c.align + '"' : '') + '>' + v + '</td>';
      }).join('') + '</tr>';
    }).join('');
    return '<div class="z-table-wrap"><table class="z-table' + (o.className ? ' ' + o.className : '') + '"><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table></div>';
  }
  function tabs(items, active, act) {
    return '<div class="z-tabs" role="tablist">' + items.map(function (t) {
      var id = t.id || t[0], label = t.label || t[1];
      return '<button role="tab" class="z-tab' + (id === active ? ' on' : '') + '" data-act="' + h(act || 'tab') + '" data-tab="' + h(id) + '">' + h(label) + (t.count != null ? ' <span class="z-count">' + h(t.count) + '</span>' : '') + '</button>';
    }).join('') + '</div>';
  }
  function field(label, input, hint) {
    return '<label class="z-field"><span class="z-label">' + h(label) + '</span>' + input + (hint ? '<span class="z-hint">' + h(hint) + '</span>' : '') + '</label>';
  }
  function initials(name) { return String(name || '?').split(/\s+/).map(function (p) { return p[0]; }).slice(0, 2).join('').toUpperCase(); }

  /* ---------- store and files (in memory, per preview session) ---------- */
  var db = {}, listeners = [], seq = 0, dirty = false;
  function changed() { if (dirty) return; dirty = true; Promise.resolve().then(function () { dirty = false; listeners.forEach(function (f) { try { f(); } catch (e) { report('', e.message); } }); render(); }); }
  var store = {
    seed: function (data) { Object.keys(data || {}).forEach(function (c) { db[c] = (data[c] || []).map(function (d) { return Object.assign({}, d); }); }); },
    list: function (c, where) { var rows = (db[c] || []).slice(); return typeof where === 'function' ? rows.filter(where) : rows; },
    get: function (c, id) { return (db[c] || []).find(function (d) { return String(d.id) === String(id); }) || null; },
    put: function (c, doc) {
      db[c] = db[c] || []; doc = Object.assign({}, doc);
      if (doc.id == null) doc.id = (c.slice(0, 2).toUpperCase()) + '-' + (Date.now() % 100000 + (++seq));
      var i = db[c].findIndex(function (d) { return String(d.id) === String(doc.id); });
      if (i < 0) db[c].unshift(doc); else db[c][i] = doc;
      changed(); return doc;
    },
    patch: function (c, id, fields) { var d = store.get(c, id); if (!d) return null; Object.assign(d, fields); changed(); return d; },
    remove: function (c, id) { db[c] = (db[c] || []).filter(function (d) { return String(d.id) !== String(id); }); changed(); },
    onChange: function (f) { listeners.push(f); }
  };
  var blobs = {};
  var files = {
    add: function (file) {
      var id = 'f' + Date.now().toString(36) + (++seq);
      blobs[id] = file;
      return Promise.resolve({ id: id, name: file.name, type: file.type, size: file.size, url: URL.createObjectURL(file) });
    },
    get: function (id) { return blobs[id] || null; },
    url: function (id) { return blobs[id] ? URL.createObjectURL(blobs[id]) : ''; }
  };
  var realFetch = window.fetch && window.fetch.bind(window);
  window.fetch = function (input, init) {
    var url = typeof input === 'string' ? input : (input && input.url) || '';
    var m = url.match(/\/_blob\/([^/?#]+)/);
    if (m) return Promise.resolve(blobs[m[1]] ? new Response(blobs[m[1]]) : new Response('', { status: 404 }));
    return realFetch ? realFetch(input, init) : Promise.reject(new Error('fetch is not available in the prototype'));
  };

  /* ---------- screens, shell, router ---------- */
  var screens = {}, shell = null, custom = null, handlers = {};
  var state = { screen: '', role: M.default_role || roleCodes[0] || '', record: null, params: {} }, history = [];
  function meta(id) { return M.screens.find(function (s) { return s.id === id; }) || { id: id }; }
  function allowed(id, role) { var s = meta(id); return !s.roles || !s.roles.length || s.roles.indexOf(role) >= 0; }
  function home(role) {
    var hm = M.home && M.home[role];
    if (hm && allowed(hm, role)) return hm;
    if (M.start && allowed(M.start, role)) return M.start;
    var first = M.screens.find(function (s) { return allowed(s.id, role) && !s.record && s.nav !== false; });
    return first ? first.id : (M.screens[0] || {}).id || '';
  }
  function persona(role) { var p = M.personas && M.personas[role]; return Object.assign({ code: role, label: M.roles[role] || role }, p || {}); }
  function nav(role) {
    return M.screens.filter(function (s) { return s.nav !== false && !s.record && allowed(s.id, role); })
      .map(function (s) { return { id: s.id, title: s.title || s.id, icon: s.icon || '', group: s.group || '', on: s.id === state.screen || s.id === (meta(state.screen).parent || '') }; });
  }
  function ctx() {
    return {
      screen: state.screen, role: state.role, record: state.record, params: state.params,
      roleLabel: M.roles[state.role] || state.role, persona: persona(state.role), roles: M.roles,
      nav: nav(state.role), meta: meta(state.screen), M: M,
      store: store, files: files, go: go, back: back, toast: toast,
      h: h, I: I, fmt: fmt, pill: pill, table: table, tabs: tabs, field: field, initials: initials
    };
  }
  function go(screen, opts) {
    opts = opts || {};
    if (opts.role && M.roles[opts.role] !== undefined) state.role = opts.role;
    if (custom) { custom.go(screen, { role: state.role, record: opts.record }); state.screen = screen; locate(); return; }
    if (!screen || !screens[screen] || !allowed(screen, state.role)) screen = home(state.role);
    if (!opts.replace && state.screen) history.push({ screen: state.screen, record: state.record, params: state.params });
    state.screen = screen; state.record = opts.record == null ? null : opts.record; state.params = opts.params || {};
    render(); try { (document.scrollingElement || document.body).scrollTop = 0; } catch (e) {}
  }
  function back() { var p = history.pop(); if (p) { state.screen = p.screen; state.record = p.record; state.params = p.params; render(); } }
  function locate() {
    var m = meta(state.screen);
    post('location', { screen: state.screen, title: m.title || state.screen, role: state.role, roleLabel: M.roles[state.role] || state.role, record: state.record });
  }
  var root;
  function render() {
    if (custom || !root) return;
    var c = ctx(), id = state.screen, def = screens[id], body;
    try { body = def ? def.render(c) : '<div class="z-empty">No screen yet.</div>'; }
    catch (e) { report('screens/' + id + '.js', e.message); body = '<div class="z-error"><b>This screen failed to draw.</b><br>' + h(e.message) + '</div>'; }
    body = '<div data-zas-screen="' + h(id) + '">' + (body || '') + '</div>';
    var html = body;
    if (shell) { try { html = shell.render(c, body); } catch (e) { report('shell.js', e.message); } }
    root.innerHTML = html + personaBar();
    if (def && def.mount) { try { def.mount(root.querySelector('[data-zas-screen]'), c); } catch (e) { report('screens/' + id + '.js', e.message); } }
    if (shell && shell.mount) { try { shell.mount(root, c); } catch (e) { report('shell.js', e.message); } }
    if (window.lucide && lucide.createIcons) { try { lucide.createIcons(); } catch (e) {} }
    locate();
  }
  function personaBar() {
    if (M.persona_bar === false || roleCodes.length < 2) return '';
    return '<div class="z-persona" title="Switch persona (prototype only)"><span>Viewing as</span><select data-act="zas-role" aria-label="Persona">' +
      roleCodes.map(function (r) { return '<option value="' + h(r) + '"' + (r === state.role ? ' selected' : '') + '>' + h(M.roles[r]) + '</option>'; }).join('') + '</select></div>';
  }

  /* ---------- overlays ---------- */
  function overlay(cls, html) {
    var old = document.querySelector('.' + cls); if (old) old.remove();
    if (html === false || html == null) return;
    var el = document.createElement('div'); el.className = cls;
    el.innerHTML = '<div class="' + cls + '-back" data-act="zas-close"></div><div class="' + cls + '-panel" role="dialog">' + html + '</div>';
    document.body.appendChild(el);
    if (window.lucide && lucide.createIcons) { try { lucide.createIcons(); } catch (e) {} }
  }
  function toast(msg, tone) {
    var el = document.createElement('div'); el.className = 'z-toast' + (tone ? ' z-' + tone : ''); el.textContent = msg;
    document.body.appendChild(el); setTimeout(function () { el.remove(); }, 2600);
  }

  /* ---------- events ---------- */
  function on(act, fn) { handlers[act] = fn; }
  function dispatch(el, ev, extra) {
    var act = el.getAttribute('data-act'), fn = handlers[act];
    if (act === 'zas-close') { overlay('z-drawer', false); overlay('z-modal', false); return; }
    if (act === 'zas-role') { if (ev.type === 'change') go(home(el.value), { role: el.value, replace: true }); return; }
    if (act === 'go') { ev.preventDefault(); go(el.getAttribute('data-go'), { record: el.getAttribute('data-record') }); return; }
    if (act === 'back') { back(); return; }
    if (!fn) return;
    try { fn(Object.assign({}, el.dataset, extra || {}), el, ev, ctx()); }
    catch (e) { report('', 'Action "' + act + '": ' + e.message); }
  }
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('[data-act]');
    if (!el || el.tagName === 'SELECT' || el.tagName === 'FORM' || (el.tagName === 'INPUT' && el.type !== 'button' && el.type !== 'checkbox')) return;
    dispatch(el, ev);
  });
  document.addEventListener('change', function (ev) {
    var el = ev.target;
    if (el.matches && el.matches('select[data-act],input[data-act],textarea[data-act]')) dispatch(el, ev, { value: el.type === 'checkbox' ? el.checked : el.value, files: el.files });
  });
  document.addEventListener('submit', function (ev) {
    var form = ev.target; if (!form.matches('form[data-act]')) return;
    ev.preventDefault();
    var data = {}; new FormData(form).forEach(function (v, k) { data[k] = v; });
    dispatch(form, ev, { form: data });
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { overlay('z-drawer', false); overlay('z-modal', false); } });
  window.addEventListener('message', function (ev) {
    var d = ev.data || {};
    if (d.source !== 'zango-console') return;
    if (d.type === 'goto') go(d.screen, { role: d.role, record: d.record, replace: true });
  });

  window.ZAS = {
    M: M, state: state, errors: errors, store: store, files: files, fmt: fmt,
    h: h, I: I, pill: pill, table: table, tabs: tabs, field: field, initials: initials,
    seed: store.seed, on: on, go: go, back: back, render: render, ctx: ctx, toast: toast,
    drawer: function (html) { overlay('z-drawer', html); }, modal: function (html) { overlay('z-modal', html); },
    screen: function (id, def) { screens[id] = typeof def === 'function' ? { render: def } : def; },
    shell: function (def) { shell = typeof def === 'function' ? { render: def } : def; },
    ready: function (nav) { custom = nav; },
    at: function (screen, o) { state.screen = screen; o = o || {}; if (o.role) state.role = o.role; state.record = o.record == null ? null : o.record; locate(); },
    boot: function () {
      root = document.getElementById('zas-app');
      // An imported page draws itself; until it registers ZAS.ready, leave it alone.
      if (custom || !Object.keys(screens).length) { post('ready', { screens: M.screens.map(function (s) { return s.id; }) }); return; }
      state.screen = home(state.role);
      render();
      post('ready', { screens: Object.keys(screens) });
    }
  };
})();
