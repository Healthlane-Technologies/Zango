/* The app shell (menu per role) and the engine every screen runs on: lists with search, filters,
   sorting and quick filters, create/edit forms, row actions, status changes (with their dialogs and
   what they do to other records) and the record drawer. It reads what each record type is made of
   from CFG (data.js); the screens only say which one to draw. */
(function () {
  var Z = ZAS, h = Z.h, I = Z.I, fmt = Z.fmt, S = Z.store, C = window.CFG, E = C.entities;
  var P = window.P = { ui: {} }, seq = 0;

  function role() { return Z.state.role; }
  function persona() { return C.personas[role()] || {}; }
  function opt(list, id) { return (list || []).filter(function (o) { return o.id === id; })[0]; }
  function pad(n, w) { n = String(n); while (n.length < w) n = '0' + n; return n; }
  function screenTitle(id) { var s = (Z.M.screens || []).filter(function (x) { return x.id === id; })[0]; return s ? s.title : id; }
  P.choices = function (f) { return C.choices[f.choices] || []; };
  P.get = function (ek, id) { return S.get(E[ek].collection, id); };
  P.name = function (ek, id) { var r = P.get(ek, id); return r ? r[E[ek].display] : ''; };
  P.can = function (ek, act) { var a = (E[ek].access || {})[role()]; return !!a && a.indexOf(act) >= 0; };
  P.badge = function (label, color) { return '<span class="bd bd-' + h(color || 'gray') + '">' + h(label) + '</span>'; };
  P.status = function (ek, r) {
    var s = (E[ek].statuses || []).filter(function (x) { return x.code === r.status; })[0];
    return s ? P.badge(s.label, s.color) : '';
  };
  P.statusLabel = function (ek, code) { var s = (E[ek].statuses || []).filter(function (x) { return x.code === code; })[0]; return s ? s.label : code; };

  /* ----- values ----- */
  P.plain = function (ek, k, r) {
    var e = E[ek], f = e.fields[k], v = r[k];
    if (k === 'status') return P.statusLabel(ek, v);
    if (!f) return v == null ? '' : v;
    if (f.type === 'link') return P.name(f.to, v);
    if (f.type === 'choice') { var o = opt(P.choices(f), v); return o ? o.label : v || ''; }
    if (f.type === 'multi') return (v || []).map(function (x) { var o = opt(P.choices(f), x); return o ? o.label : x; }).join(', ');
    return v == null ? '' : v;
  };
  P.cell = function (ek, k, r) {
    var f = E[ek].fields[k], v = r[k];
    if (k === 'status') return P.status(ek, r);
    if (!f) return h(v);
    if (f.type === 'money') return v === '' || v == null ? '<span class="mut">—</span>' : fmt.money(v);
    if (f.type === 'date') return fmt.date(v);
    if (f.type === 'bool') return v ? 'Yes' : 'No';
    if (f.type === 'link') return h(P.name(f.to, v));
    if (f.type === 'choice') { var o = opt(P.choices(f), v); return o && o.color ? P.badge(o.label, o.color) : h(o ? o.label : v); }
    if (f.type === 'multi') {
      var n = (v || []).length; if (!n) return '<span class="mut">—</span>';
      var first = opt(P.choices(f), v[0]);
      return P.badge((first ? first.label.split(' ').slice(0, 2).join(' ') : v[0]) + (n > 1 ? ' +' + (n - 1) : ''), 'amber');
    }
    if (f.type === 'number') return v == null || v === '' ? '<span class="mut">—</span>' : h(v);
    return h(v == null ? '' : v);
  };
  P.rows = function (ek) {
    var e = E[ek], rows = S.list(e.collection), sc = e.scope && e.scope[role()];
    if (sc) { var me = persona()[sc]; rows = rows.filter(function (r) { return r[sc] === me; }); }
    return rows;
  };

  /* ----- shell ----- */
  function navItem(it, c) {
    var label = it.label || screenTitle(it.screen), meta = c.meta || {};
    var on = it.screen === c.screen || it.screen === meta.parent;
    return '<a href="#" class="nav-i' + (on ? ' on' : '') + '" data-act="go" data-go="' + h(it.screen) + '" data-nav="' + h(it.screen) + '">' + I(it.icon || 'circle', 16) + '<span>' + h(label) + '</span></a>';
  }
  Z.shell({
    render: function (c, body) {
      var items = (C.menus[c.role] || []).map(function (it) {
        if (it.group) return '<div class="nav-group">' + h(it.group) + '</div>' + it.items.map(function (x) { return navItem(x, c); }).join('');
        return navItem(it, c);
      }).join('');
      var p = C.personas[c.role] || {};
      return '<div class="app"><aside class="side"><div class="brand"><div class="mark">V&amp;</div><div><div class="bn">' + h(Z.M.title || 'Voucher & Coupon Management') +
        '</div><div class="bs">' + h(p.title || c.roleLabel) + '</div></div></div><nav class="nav">' + items + '</nav>' +
        '<div class="who"><div class="av">' + h(Z.initials(p.name || c.roleLabel)) + '</div><div><div class="wn">' + h(p.name || '') + '</div><div class="ws">' + h(p.title || c.roleLabel) + '</div></div></div></aside>' +
        '<main class="main">' + body + '</main></div>';
    }
  });

  /* ----- lists ----- */
  function uiOf(id) {
    var k = id + ':' + role();
    return P.ui[k] = P.ui[k] || { q: '', f: {}, sort: null, qk: undefined, page: 0 };
  }
  function quickOf(e) { return (e.quick || []).filter(function (q) { return !q.roles || q.roles.indexOf(role()) >= 0; }); }
  function visible(ek, id) {
    var e = E[ek], u = uiOf(id), quick = quickOf(e);
    if (u.qk === undefined) { var d = -1; quick.forEach(function (q, i) { if (q.def && d < 0) d = i; }); u.qk = d >= 0 ? d : null; }
    if (!u.sort) u.sort = e.sort;
    var qs = u.q.toLowerCase();
    var rows = P.rows(ek).filter(function (r) {
      if (qs && !e.columns.some(function (c) { return c.search && String(P.plain(ek, c.k, r)).toLowerCase().indexOf(qs) >= 0; })) return false;
      for (var k in u.f) if (u.f[k] !== '' && String(r[k]) !== u.f[k]) return false;
      if (u.qk != null && quick[u.qk] && !quick[u.qk].test(r)) return false;
      return true;
    });
    var desc = u.sort.charAt(0) === '-', sk = desc ? u.sort.slice(1) : u.sort;
    rows.sort(function (a, b) {
      var x = P.plain(ek, sk, a), y = P.plain(ek, sk, b);
      if (x === '' || x == null) x = a.created_at || a.id; if (y === '' || y == null) y = b.created_at || b.id;
      var r = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true });
      return desc ? -r : r;
    });
    return rows;
  }
  function tableHtml(ek, id, rows, o) {
    o = o || {};
    var e = E[ek], u = uiOf(id), size = o.size || 10, pages = Math.max(1, Math.ceil(rows.length / size));
    if (u.page >= pages) u.page = pages - 1;
    var shown = o.all ? rows : rows.slice(u.page * size, u.page * size + size);
    var cols = o.columns ? e.columns.filter(function (c) { return o.columns.indexOf(c.k) >= 0; }) : e.columns;
    if (!rows.length) return '<div class="empty">' + I('inbox', 22) + '<div>Nothing matches yet.</div></div>';
    var desc = (u.sort || '').charAt(0) === '-', sk = desc ? u.sort.slice(1) : u.sort;
    var head = cols.map(function (c) {
      var arrow = c.sort && !o.columns && sk === c.k ? (desc ? ' ↓' : ' ↑') : '';
      return '<th' + (c.sort && !o.columns ? ' class="srt" data-act="srt" data-id="' + h(id) + '" data-k="' + h(c.k) + '"' : '') + '>' + h(c.label) + arrow + '</th>';
    }).join('') + '<th class="ka"></th>';
    var body = shown.map(function (r) {
      var rowAct = e.rowClick && P.can(ek, 'detail') ? 'data-act="row" data-ek="' + ek + '" data-id="' + h(r.id) + '"' : 'data-act="view" data-ek="' + ek + '" data-id="' + h(r.id) + '"';
      return '<tr class="z-row" ' + rowAct + '>' + cols.map(function (c) {
        var f = e.fields[c.k], right = f && (f.type === 'money' || f.type === 'number');
        return '<td' + (right ? ' class="r"' : c.link ? ' class="lnk"' : '') + '>' + P.cell(ek, c.k, r) + '</td>';
      }).join('') + '<td class="ka">' + (rowMenu(ek, r).length ? '<button class="kb" data-act="menu" data-ek="' + ek + '" data-id="' + h(r.id) + '" aria-label="Actions">' + I('more-vertical', 16) + '</button>' : '') + '</td></tr>';
    }).join('');
    var foot = '';
    if (e.totals && !o.columns) {
      foot = '<tfoot><tr>' + cols.map(function (c, i) {
        if (e.totals.indexOf(c.k) < 0) return '<td>' + (i === 0 ? 'Total' : '') + '</td>';
        return '<td class="r">' + fmt.money(rows.reduce(function (s, r) { return s + (Number(r[c.k]) || 0); }, 0)) + '</td>';
      }).join('') + '<td></td></tr></tfoot>';
    }
    var pager = pages > 1 && !o.all ? '<div class="pager" data-zas-chrome><span>Showing ' + (u.page * size + 1) + '–' + Math.min(rows.length, u.page * size + size) + ' of ' + rows.length +
      '</span><span><button class="btn sm" data-act="pg" data-id="' + h(id) + '" data-d="-1"' + (u.page === 0 ? ' disabled' : '') + '>Previous</button> <button class="btn sm" data-act="pg" data-id="' + h(id) + '" data-d="1"' + (u.page >= pages - 1 ? ' disabled' : '') + '>Next</button></span></div>' : '';
    return '<div class="tw"><table class="tbl"><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody>' + foot + '</table></div>' + pager;
  }
  P.table = tableHtml;
  P.list = function (id, ek, o) {
    o = o || {};
    var e = E[ek], u = uiOf(id), rows = visible(ek, id), quick = quickOf(e), total = P.rows(ek).length;
    var filters = e.columns.filter(function (c) { return c.filter; }).map(function (c) {
      var f = e.fields[c.k], options = [];
      if (c.k === 'status') options = (e.statuses || []).map(function (s) { return [s.code, s.label]; });
      else if (f.type === 'choice') options = P.choices(f).map(function (x) { return [x.id, x.label]; });
      else if (f.type === 'link') options = S.list(E[f.to].collection).map(function (x) { return [x.id, x[E[f.to].display]]; });
      else if (f.type === 'bool') options = [['true', 'Yes'], ['false', 'No']];
      return '<select class="sel" data-act="flt" data-id="' + h(id) + '" data-k="' + h(c.k) + '" aria-label="' + h(c.label) + '"><option value="">' + h(c.label) + ': All</option>' +
        options.map(function (x) { return '<option value="' + h(x[0]) + '"' + (u.f[c.k] === String(x[0]) ? ' selected' : '') + '>' + h(x[1]) + '</option>'; }).join('') + '</select>';
    }).join('');
    var chips = quick.map(function (q, i) { return '<button class="chip' + (u.qk === i ? ' on' : '') + '" data-act="qk" data-id="' + h(id) + '" data-i="' + i + '">' + h(q.label) + '</button>'; }).join('');
    var add = P.can(ek, 'add') && e.add ? '<button class="btn pri" data-act="new" data-ek="' + ek + '">' + I('plus', 16) + h(e.add.label) + '</button>' : '';
    var exp = P.can(ek, 'export') ? '<button class="btn" data-act="export" data-ek="' + ek + '">' + I('download', 16) + 'Export</button>' : '';
    return '<div class="ph"><div><h1>' + h(o.title || screenTitle(id)) + '</h1><p class="sub" data-zas-chrome>' + total + ' record' + (total === 1 ? '' : 's') + '.</p></div><div class="ph-a">' + add + '</div></div>' +
      '<div class="card"><div class="tb"><label class="srch">' + I('search', 15) + '<input class="in" data-q="' + h(id) + '" data-ek="' + ek + '" placeholder="Search ' + h(e.plural.toLowerCase()) + '" value="' + h(u.q) + '"></label>' +
      filters + chips + '<span class="sp"></span>' + exp + '</div><div class="lst" data-lst="' + h(id) + '" data-ek="' + ek + '">' + tableHtml(ek, id, rows) + '</div></div>';
  };
  document.addEventListener('input', function (ev) {
    var el = ev.target; if (!el.matches || !el.matches('input[data-q]')) return;
    var id = el.getAttribute('data-q'), ek = el.getAttribute('data-ek'), u = uiOf(id);
    u.q = el.value; u.page = 0;
    var host = document.querySelector('[data-lst="' + id + '"]');
    if (host) { host.innerHTML = tableHtml(ek, id, visible(ek, id)); if (window.lucide && lucide.createIcons) { try { lucide.createIcons(); } catch (e) {} } }
  });
  Z.on('srt', function (d) { var u = uiOf(d.id); u.sort = u.sort === d.k ? '-' + d.k : d.k; Z.render(); });
  Z.on('flt', function (d) { var u = uiOf(d.id); u.f[d.k] = d.value; u.page = 0; Z.render(); });
  Z.on('qk', function (d) { var u = uiOf(d.id), i = Number(d.i); u.qk = u.qk === i ? null : i; u.page = 0; Z.render(); });
  Z.on('pg', function (d) { var u = uiOf(d.id); u.page += Number(d.d); Z.render(); });
  Z.on('export', function (d) { Z.toast('Exported ' + visible(d.ek, Z.state.screen).length + ' rows (a file in the built app)'); });
  Z.on('row', function (d) { Z.go(E[d.ek].rowClick, { record: d.id }); });

  /* ----- row menu, record drawer ----- */
  function transitionsFor(ek, r) {
    return (E[ek].transitions || []).filter(function (t) { return t.roles && t.roles.indexOf(role()) >= 0 && t.from.indexOf(r.status) >= 0; });
  }
  P.transitionsFor = transitionsFor;
  function canEdit(ek, r) { var e = E[ek]; return P.can(ek, 'edit') && (!e.editable || e.editable.indexOf(r.status) >= 0); }
  function rowMenu(ek, r) {
    var items = [];
    if (canEdit(ek, r)) items.push({ name: '_edit', label: 'Edit' });
    transitionsFor(ek, r).forEach(function (t) { items.push({ name: t.name, label: t.label, tone: t.tone }); });
    return items;
  }
  function closeMenu() { var m = document.querySelector('.pop'); if (m) m.remove(); }
  document.addEventListener('click', function (ev) { if (!ev.target.closest('.pop,[data-act="menu"]')) closeMenu(); });
  Z.on('menu', function (d, el, ev) {
    ev.stopPropagation(); var had = document.querySelector('.pop'); closeMenu(); if (had && had.getAttribute('data-for') === d.id) return;
    var r = P.get(d.ek, d.id); if (!r) return;
    var b = el.getBoundingClientRect(), m = document.createElement('div');
    m.className = 'pop'; m.setAttribute('data-for', d.id);
    m.style.cssText = 'position:fixed;top:' + (b.bottom + 4) + 'px;left:' + Math.max(8, b.right - 184) + 'px';
    m.innerHTML = rowMenu(d.ek, r).map(function (it) { return '<button class="' + (it.tone === 'danger' ? 'dng' : '') + '" data-act="rowact" data-ek="' + d.ek + '" data-id="' + h(d.id) + '" data-name="' + h(it.name) + '">' + h(it.label) + '</button>'; }).join('');
    document.body.appendChild(m);
  });
  Z.on('rowact', function (d) { closeMenu(); if (d.name === '_edit') P.form(d.ek, d.id); else P.transition(d.ek, d.id, d.name); });
  Z.on('view', function (d) { P.view(d.ek, d.id); });
  P.view = function (ek, id) {
    var e = E[ek], r = P.get(ek, id); if (!r) return;
    var keys = Object.keys(e.fields).filter(function (k) { return r[k] !== undefined && r[k] !== ''; });
    var acts = transitionsFor(ek, r).map(function (t) { return '<button class="btn' + (t.primary ? ' pri' : '') + (t.tone === 'danger' ? ' dng' : '') + '" data-act="rowact" data-ek="' + ek + '" data-id="' + h(id) + '" data-name="' + h(t.name) + '">' + h(t.label) + '</button>'; }).join('') +
      (canEdit(ek, r) ? '<button class="btn" data-act="rowact" data-ek="' + ek + '" data-id="' + h(id) + '" data-name="_edit">Edit</button>' : '');
    Z.drawer('<div class="dw-h"><div><h2>' + h(r[e.display]) + '</h2><p>' + h(e.name) + '</p></div>' + (e.statuses ? P.status(ek, r) : '') + '<button class="x" data-act="zas-close" aria-label="Close">' + I('x', 18) + '</button></div>' +
      '<div class="dw-b"><dl class="dl">' + keys.map(function (k) { return '<dt>' + h(e.fields[k].label) + '</dt><dd>' + P.cell(ek, k, r) + '</dd>'; }).join('') + '</dl></div>' + (acts ? '<div class="dw-f">' + acts + '</div>' : ''));
  };

  /* ----- forms ----- */
  function fieldHtml(ek, k, val, preset) {
    var f = E[ek].fields[k], id = 'f_' + k, v = val != null ? val : (f.def != null ? f.def : ''), t = f.type, input;
    if (t === 'bool') return '<div class="fld"><label class="chk"><input type="checkbox" name="' + k + '"' + (v ? ' checked' : '') + '> ' + h(f.label) + (f.req ? '<span class="rq">*</span>' : '') + '</label></div>';
    if (t === 'choice') {
      var list = P.choices(f);
      input = list.length <= 4 ? '<div class="pills"><input type="hidden" name="' + k + '" value="' + h(v) + '">' + list.map(function (o) { return '<button type="button" class="pill' + (String(v) === o.id ? ' on' : '') + '" data-act="pill" data-v="' + h(o.id) + '">' + h(o.label) + '</button>'; }).join('') + '</div>' :
        '<select class="sel in" id="' + id + '" name="' + k + '"><option value="">Select…</option>' + list.map(function (o) { return '<option value="' + h(o.id) + '"' + (String(v) === o.id ? ' selected' : '') + '>' + h(o.label) + '</option>'; }).join('') + '</select>';
    } else if (t === 'link') {
      var tgt = E[f.to], rows = S.list(tgt.collection).filter(function (r) { return !f.only || f.only(r); });
      input = '<select class="sel in" id="' + id + '" name="' + k + '"><option value="">Select ' + h(tgt.name.toLowerCase()) + '…</option>' + rows.map(function (r) { return '<option value="' + h(r.id) + '"' + (String(v) === r.id ? ' selected' : '') + '>' + h(r[tgt.display]) + '</option>'; }).join('') + '</select>';
    } else if (t === 'long') input = '<textarea class="in" id="' + id + '" name="' + k + '" rows="3">' + h(v) + '</textarea>';
    else if (t === 'file') input = '<input class="in" id="' + id + '" type="file" name="' + k + '" accept=".pdf,.jpg,.png">';
    else if (t === 'money') input = '<div class="money"><span>₹</span><input class="in" id="' + id + '" type="number" min="0" name="' + k + '" value="' + h(v) + '"></div>';
    else input = '<input class="in" id="' + id + '" type="' + (t === 'number' ? 'number' : t === 'date' ? 'date' : t === 'email' ? 'email' : 'text') + '" name="' + k + '" value="' + h(v) + '"' + (f.ph ? ' placeholder="' + h(f.ph) + '"' : '') + '>';
    return '<div class="fld' + (t === 'long' ? ' full' : '') + '"><label for="' + id + '">' + h(f.label) + (f.req ? '<span class="rq">*</span>' : '') + '</label>' + input + (f.help ? '<small>' + h(f.help) + '</small>' : '') + '</div>';
  }
  Z.on('pill', function (d, el) {
    var wrap = el.parentNode, input = wrap.querySelector('input'), on = el.classList.contains('on');
    wrap.querySelectorAll('.pill').forEach(function (b) { b.classList.remove('on'); });
    if (!on) el.classList.add('on'); input.value = on ? '' : d.v;
  });
  P.form = function (ek, id, preset) {
    var e = E[ek], r = id ? P.get(ek, id) : null, a = e.add;
    var secs = (a.sections || []).map(function (s) {
      return (s.title ? '<div class="fsec">' + h(s.title) + '</div>' : '') + '<div class="fg">' + s.fields.map(function (k) { return fieldHtml(ek, k, r ? r[k] : preset && preset[k]); }).join('') + '</div>';
    }).join('');
    Z.modal('<form data-act="save" data-ek="' + ek + '" data-id="' + h(id || '') + '"><div class="mo-h"><h2>' + h(r ? 'Edit ' + e.name : a.title) + '</h2><button type="button" class="x" data-act="zas-close" aria-label="Close">' + I('x', 18) + '</button></div><div class="mo-b">' + secs +
      '</div><div class="mo-f"><span class="sp"></span><button type="button" class="btn" data-act="zas-close">Cancel</button><button type="submit" class="btn pri">' + (r ? 'Save' : 'Create') + '</button></div></form>');
  };
  Z.on('new', function (d) { P.form(d.ek, '', P.preset); P.preset = null; });
  function readValues(ek, form, keys) {
    var out = {}, miss = [];
    keys.forEach(function (k) {
      var f = E[ek].fields[k], v = form[k];
      if (f.type === 'bool') v = form[k] === 'on';
      else if (f.type === 'number' || f.type === 'money') v = v === '' || v == null ? '' : Number(v);
      else if (f.type === 'file') v = v && v.name ? v.name : '';
      else v = v == null ? '' : String(v).trim();
      if (f.req && f.type !== 'bool' && (v === '' || v == null)) miss.push(k);
      if (f.req && f.type === 'bool' && !v) miss.push(k);
      out[k] = v;
    });
    return { vals: out, missing: miss };
  }
  function markMissing(miss) {
    document.querySelectorAll('.z-modal .fld').forEach(function (f) { f.classList.remove('bad'); });
    miss.forEach(function (k) { var el = document.querySelector('.z-modal [name="' + k + '"]'); if (el && el.closest('.fld')) el.closest('.fld').classList.add('bad'); });
  }
  Z.on('save', function (d) {
    var ek = d.ek, e = E[ek], id = d.id, keys = [];
    e.add.sections.forEach(function (s) { keys = keys.concat(s.fields); });
    var got = readValues(ek, d.form, keys);
    if (got.missing.length) { markMissing(got.missing); Z.toast('Fill the required fields first', 'bad'); return; }
    var v = got.vals;
    if (ek === 'campaign' && v.end_date <= v.start_date) { Z.toast('The end date must be after the start date.', 'bad'); return; }
    var dup = (e.unique || []).filter(function (u) {
      return S.list(e.collection).some(function (r) { return r.id !== id && u.keys.every(function (k) { return String(r[k]) === String(v[k] != null ? v[k] : ek === 'redemption' && k === 'pharmacy' ? persona().pharmacy : ''); }); });
    })[0];
    if (dup) { Z.toast(dup.msg, 'bad'); return; }
    if (id) { S.patch(e.collection, id, v); Z.overlayClose(); Z.toast(e.name + ' saved'); return; }
    var doc = Object.assign({ id: ek.slice(0, 2) + (Date.now() % 100000) + (++seq) }, v);
    if (e.initial) doc.status = e.initial;
    doc.created_at = C.today;
    var msg = (P.created[ek] || function () { return e.name + ' created'; })(doc);
    S.put(e.collection, doc);
    Z.overlayClose();
    Z.toast(msg || e.name + ' created');
    if (ek === 'campaign') Z.go('campaign_360', { record: doc.id });
  });
  Z.overlayClose = function () { var b = document.querySelector('.z-modal-back'); if (b) b.click(); };

  /* what creating a record does to the rest */
  function count(coll, f) { return S.list(coll, f).length; }
  function approve(r) {
    var v = P.get('voucher', r.voucher), c = v && P.get('campaign', v.campaign);
    if (v) { var left = Math.max(0, (v.uses_left || 1) - 1); S.patch('voucher', v.id, { uses_left: left, status: left === 0 ? 'redeemed' : v.status }); }
    if (c) S.patch('campaign', c.id, { spent: (c.spent || 0) + (r.benefit_amount || 0) });
  }
  P.created = {
    campaign: function (d) { d.campaign_code = 'VC-26-' + pad(count('campaign', function (r) { return r.campaign_code.indexOf('VC-26-') === 0; }) + 1, 3); d.spent = 0; S.put('activity', { entity: 'campaign', ref: d.id, ts: C.today, text: 'Campaign created by ' + persona().name }); return 'Campaign ' + d.campaign_code + ' created as a draft'; },
    voucher: function (d) {
      var c = P.get('campaign', d.campaign); d.code = 'VCH-26-' + pad(count('voucher') + 1, 6); d.issued_on = C.today; d.uses_left = c ? c.uses_per_voucher || 1 : 1;
      S.put('activity', { entity: 'voucher', ref: d.campaign, ts: C.today, text: 'Voucher ' + d.code + ' issued' }); return 'Voucher ' + d.code + ' issued and sent to the patient';
    },
    patient: function (d) { d.patient_id = 'PT-' + pad(count('patient') + 1, 6); return 'Patient ' + d.patient_id + ' enrolled'; },
    pharmacy: function (d) { d.pharmacy_code = 'PH-' + pad(count('pharmacy') + 1, 4); },
    settlement: function (d) {
      d.settlement_no = 'ST-26-' + pad(count('settlement') + 1, 4); d.payment_ref = '';
      var ym = String(d.month).slice(0, 7), mine = S.list('redemption', function (r) { return r.pharmacy === d.pharmacy && r.status === 'approved' && String(r.bill_date).slice(0, 7) === ym; });
      d.lines = mine.length; d.amount = mine.reduce(function (s, r) { return s + (r.benefit_amount || 0); }, 0);
      return 'Settlement ' + d.settlement_no + ' created with ' + d.lines + ' redemptions';
    },
    redemption: function (d) {
      var v = P.get('voucher', d.voucher), c = v && P.get('campaign', v.campaign), p = P.get('product', c && c.product);
      d.redemption_no = 'RD-26-' + pad(count('redemption') + 1, 6); d.pharmacy = persona().pharmacy;
      var raw = 0;
      if (c) raw = c.benefit_kind === 'percent' ? d.bill_amount * c.benefit_value / 100 : c.benefit_kind === 'amount' ? c.benefit_value * d.packs : (p ? p.mrp : 0) * c.benefit_value;
      d.benefit_amount = Math.round(c && c.max_benefit ? Math.min(raw, c.max_benefit) : raw);
      d.fraud_hits = [];
      if (c && c.max_benefit && raw > c.max_benefit) d.fraud_hits.push('amount_cap');
      if (v && d.bill_date > v.expires_on) d.fraud_hits.push('expired');
      d.status = d.fraud_hits.length ? 'flagged' : 'approved';
      if (d.status === 'approved') approve(d);
      return d.status === 'flagged' ? 'Redemption flagged for review: ' + d.fraud_hits.length + ' fraud rule' + (d.fraud_hits.length > 1 ? 's' : '') + ' hit' : 'Redemption approved: benefit ' + fmt.money(d.benefit_amount);
    }
  };

  /* ----- status changes ----- */
  P.transition = function (ek, id, name) {
    var e = E[ek], r = P.get(ek, id), t = (e.transitions || []).filter(function (x) { return x.name === name; })[0]; if (!r || !t) return;
    var why = t.check && t.check(r); if (why) { Z.toast(why, 'bad'); return; }
    if (!t.form && !t.confirm) { P.applyTransition(ek, id, t, {}); return; }
    var fields = t.form ? Object.keys(t.form).map(function (k) { return fieldHtmlT(t.form, k); }).join('') : '';
    var to = (e.statuses || []).filter(function (s) { return s.code === t.to; })[0], from = (e.statuses || []).filter(function (s) { return s.code === r.status; })[0];
    Z.modal('<form data-act="tsave" data-ek="' + ek + '" data-id="' + h(id) + '" data-name="' + h(name) + '"><div class="mo-h"><div class="mi">' + I('arrow-right-circle', 18) + '</div><div class="grow"><h2>' + h(t.label) + '</h2><p>' + h(e.name) + ' · ' + h(r[e.display]) + '</p></div><button type="button" class="x" data-act="zas-close" aria-label="Close">' + I('x', 18) + '</button></div>' +
      '<div class="mo-b">' + (from && to && from.code !== to.code ? '<div class="flow">' + P.badge(from.label, from.color) + I('arrow-right', 16) + P.badge(to.label, to.color) + '</div>' : '') +
      (t.confirm ? '<p class="cf">' + h(t.confirm) + '</p>' : '') + (fields ? '<div class="fg">' + fields + '</div>' : '') + (t.note ? '<div class="nt">' + I('info', 15) + '<span>' + h(t.note) + '</span></div>' : '') +
      '</div><div class="mo-f"><span class="sp"></span><button type="button" class="btn" data-act="zas-close">Cancel</button><button type="submit" class="btn ' + (t.tone === 'danger' ? 'dng' : 'pri') + '">' + h(t.label) + '</button></div></form>');
  };
  function fieldHtmlT(form, k) {
    E.__t = { fields: form }; var out = fieldHtml('__t', k, ''); delete E.__t; return out;
  }
  Z.on('tsave', function (d) {
    var ek = d.ek, e = E[ek], t = (e.transitions || []).filter(function (x) { return x.name === d.name; })[0];
    var vals = {};
    if (t.form) {
      E.__t = { fields: t.form }; var got = readValues('__t', d.form, Object.keys(t.form)); delete E.__t;
      if (got.missing.length) { markMissing(got.missing); Z.toast('Fill the required fields first', 'bad'); return; }
      vals = got.vals;
    }
    Z.overlayClose(); P.applyTransition(ek, d.id, t, vals);
  });
  P.applyTransition = function (ek, id, t, vals) {
    var e = E[ek], r = P.get(ek, id), was = r.status;
    var patch = { status: t.to };
    var extra = Object.keys(vals).map(function (k) { var v = vals[k]; var f = t.form[k]; if (f.type === 'choice') { var o = opt(C.choices[f.choices], v); v = o ? o.label : v; } return v; }).filter(Boolean).join(' · ');
    S.patch(e.collection, id, patch);
    if (t.hook === 'approve') approve(P.get(ek, id));
    var cid = ek === 'campaign' ? id : ek === 'voucher' ? r.campaign : null;
    if (cid) S.put('activity', { entity: ek, ref: cid, ts: C.today, text: (ek === 'voucher' ? 'Voucher ' + r.code + ': ' : '') + t.label + (was !== t.to ? ' (' + P.statusLabel(ek, was) + ' → ' + P.statusLabel(ek, t.to) + ')' : '') + (extra ? ': ' + extra : '') });
    Z.toast(t.note || e.name + ' ' + (was !== t.to ? 'is now ' + P.statusLabel(ek, t.to) : t.label.toLowerCase() + ' done'));
  };
})();
