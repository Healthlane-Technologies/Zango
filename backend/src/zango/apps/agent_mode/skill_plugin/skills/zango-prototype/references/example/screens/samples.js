ZAS.screen('samples', c => {
  const f = c.params.stage || 'All', all = c.store.list('samples');
  const rows = f === 'All' ? all : all.filter(s => s.stage === f);
  const chips = ['All', ...LAB.STAGES].map(s => `<button class="chip ${s === f ? 'on' : ''}" data-act="stage-filter" data-stage="${s}">${s}<span class="n">${s === 'All' ? all.length : all.filter(x => x.stage === s).length}</span></button>`).join('');
  return `
  <div class="page-head"><div><h1>Samples</h1><p>Everything received by the lab in the last 30 days</p></div>
    ${c.role === 'lead' ? `<button class="btn pri" data-act="log-sample">${c.I('plus')}Log sample</button>` : ''}</div>
  <div class="chips">${chips}</div>
  <div class="card">${c.table({className: 'tbl', rowAct: 'open', rows, empty: `No samples are in ${c.h(f)}.`,
    columns: [
      {label: 'Sample', render: s => `<span class="id">${c.h(s.id)}</span>`},
      {label: 'What', key: 'label'}, {label: 'Matrix', key: 'matrix'},
      {label: 'Due', render: s => `<span class="${LAB.late(s) ? 'late' : ''}">${c.fmt.date(s.due)}</span>`},
      {label: 'Stage', render: s => c.pill(s.stage, LAB.tone(s.stage))},
      {label: 'Analyst', render: s => `<span class="av" title="${c.h(s.assignee)}">${c.initials(s.assignee)}</span>`}]})}</div>`;
});
ZAS.on('stage-filter', d => ZAS.go('samples', {params: {stage: d.stage}, replace: true}));
ZAS.on('log-sample', () => ZAS.toast('Logging a sample opens the receipt form (not drawn in this example).'));
