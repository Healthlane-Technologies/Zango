// A list page in the default look: header band (title + count, subtitle, primary button), then ONE card:
// toolbar (search, segmented status filters with counts, icon buttons), table (sortable headers, two-line
// cells, mono codes, badges, avatars, a chevron), pager. The WHOLE row opens the record page.
const COLS = [
  {key: 'id', label: 'Sample', sort: true, cell: s => `<div class="c-code">${ZAS.h(s.id)}${s.urgent ? '<span class="c-flag">Urgent</span>' : ''}</div><div class="c-sub">${ZAS.h(s.label)}</div>`},
  {key: 'matrix', label: 'Matrix', cell: s => `<div class="c-main">${ZAS.h(s.matrix)}</div><div class="c-sub mono">${ZAS.h(s.batch)}</div>`},
  {key: 'due', label: 'Due', sort: true, cell: s => `<span class="${LAB.late(s) ? 'c-late' : ''}">${ZAS.fmt.date(s.due)}</span>`},
  {key: 'stage', label: 'Stage', cell: s => LAB.badge(s.stage)},
  {key: 'assignee', label: 'Analyst', sort: true, cell: s => LAB.person(s.assignee)}
];
ZAS.screen('samples', c => {
  const p = c.params, f = p.stage || 'All', q = (p.q || '').toLowerCase(), all = c.store.list('samples');
  let rows = all.filter(s => (f === 'All' || s.stage === f) && (!q || `${s.id} ${s.label} ${s.batch}`.toLowerCase().includes(q)));
  if (p.sort) { const [k, dir] = p.sort.split(':'); rows = rows.sort((a, b) => String(a[k]).localeCompare(String(b[k])) * (dir === 'desc' ? -1 : 1)); }
  const seg = ['All', ...LAB.STAGES].map(s => `<button class="${s === f ? 'on' : ''}" data-act="list-filter" data-stage="${s}">${s}<span class="n">${s === 'All' ? all.length : all.filter(x => x.stage === s).length}</span></button>`).join('');
  const head = COLS.map(col => {
    if (!col.sort) return `<th>${col.label}</th>`;
    const asc = p.sort === col.key + ':asc', desc = p.sort === col.key + ':desc';
    return `<th><button class="z-sort ${asc || desc ? 'on' : ''}" data-act="list-sort" data-sort="${col.key}:${asc ? 'desc' : 'asc'}">${col.label}${c.I(asc ? 'chevron-up' : desc ? 'chevron-down' : 'chevrons-up-down', 12)}</button></th>`;
  }).join('');
  const body = rows.map(s => `<tr data-act="open" data-id="${c.h(s.id)}">${COLS.map(col => `<td>${col.cell(s)}</td>`).join('')}<td class="chev">${c.I('chevron-right', 15)}</td></tr>`).join('');
  return `
  <header class="z-top"><div><h1>Samples <span class="z-hc">(${all.length})</span></h1><p>Everything received by the lab in the last 30 days</p></div><div class="sp"></div>
    ${c.role === 'lead' ? `<button class="z-btn pri" data-act="log-sample">${c.I('plus', 15)}Log sample</button>` : ''}</header>
  <div class="z-content"><div class="z-card">
    <div class="z-tb">
      <label class="z-search">${c.I('search', 14)}<input data-act="list-search" placeholder="Search samples…" value="${c.h(p.q || '')}"></label>
      <div class="z-seg">${seg}</div><div class="sp"></div>
      <button class="z-ibb" title="Filters" data-act="soon">${c.I('filter', 15)}</button>
      <button class="z-ibb" title="Export" data-act="soon">${c.I('download', 15)}</button>
    </div>
    ${rows.length ? `<div class="z-tbl-w"><table class="z-t"><thead><tr>${head}<th></th></tr></thead><tbody>${body}</tbody></table></div>
    <div class="z-pgr"><span>Showing <b>1–${rows.length}</b> of <b>${rows.length}</b></span><div class="pager"><button class="on">1</button></div></div>`
    : `<div class="z-empty"><div class="ei">${c.I('test-tubes', 20)}</div><b>No samples here</b><p>Nothing matches ${q ? `“${c.h(p.q)}”` : `the ${c.h(f)} filter`}.</p></div>`}
  </div></div>`;
});
const listGo = change => ZAS.go('samples', {params: Object.assign({}, ZAS.ctx().params, change), replace: true});
ZAS.on('list-filter', d => listGo({stage: d.stage}));
ZAS.on('list-sort', d => listGo({sort: d.sort}));
ZAS.on('list-search', d => listGo({q: d.value}));
ZAS.on('open', d => ZAS.go('sample', {record: d.id}));
ZAS.on('log-sample', () => ZAS.toast('Logging a sample opens the receipt form (not drawn in this example).'));
ZAS.on('soon', () => ZAS.toast('Not drawn in this example.'));
