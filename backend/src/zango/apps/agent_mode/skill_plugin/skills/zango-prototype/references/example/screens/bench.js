ZAS.screen('bench', c => {
  const mine = c.store.list('samples', s => s.assignee === c.persona.name && s.stage !== 'Released');
  const late = mine.filter(LAB.late), running = mine.filter(s => s.stage === 'On instrument');
  return `
  <div class="page-head"><div><h1>Good morning, ${c.h(c.persona.name.split(' ')[0])}</h1><p>${mine.length} samples on your bench</p></div></div>
  <div class="kpis">
    <div class="card kpi ${late.length ? 'attn' : ''}"><b>${late.length}</b><span>Past due</span></div>
    <div class="card kpi"><b>${running.length}</b><span>On instrument</span></div>
    <div class="card kpi"><b>${mine.filter(s => s.stage === 'Received').length}</b><span>Waiting to start</span></div>
  </div>
  <div class="card">${c.table({className: 'tbl', rowAct: 'open', rows: mine, empty: 'Nothing on your bench. New samples appear here when they are assigned to you.',
    columns: [
      {label: 'Sample', render: s => `<span class="id">${c.h(s.id)}</span>`},
      {label: 'What', key: 'label'},
      {label: 'Due', render: s => `<span class="${LAB.late(s) ? 'late' : ''}">${c.fmt.rel(s.due)}</span>`},
      {label: 'Stage', render: s => c.pill(s.stage, LAB.tone(s.stage))}]})}</div>`;
});
ZAS.on('open', d => ZAS.go('sample', {record: d.id}));
