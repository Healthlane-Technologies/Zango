ZAS.screen('sample', c => {
  const s = c.store.get('samples', c.record);
  if (!s) return `<div class="z-empty">This sample no longer exists. <a data-act="go" data-go="samples">Back to samples</a></div>`;
  const at = LAB.STAGES.indexOf(s.stage), log = c.store.list('events', e => e.sample === s.id);
  const next = LAB.STAGES[at + 1], mine = s.assignee === c.persona.name;
  const action = c.role === 'lead' && s.stage === 'Review'
    ? `<button class="btn danger" data-act="reject" data-id="${s.id}">Send back</button><button class="btn pri" data-act="advance" data-id="${s.id}">${c.I('check')}Release result</button>`
    : mine && next && s.stage !== 'Review' ? `<button class="btn pri" data-act="advance" data-id="${s.id}">Move to ${next}</button>` : '';
  return `
  <div class="page-head"><div><p><a data-act="back" style="cursor:pointer">← Samples</a></p><h1><span class="id" style="font-size:20px">${c.h(s.id)}</span> ${c.h(s.label)}</h1></div><div style="display:flex;gap:8px">${action}</div></div>
  <div class="stepper">${LAB.STAGES.map((st, i) => `<div class="step ${i < at ? 'done' : i === at ? 'now' : ''}">${st}</div>`).join('')}</div>
  <div class="grid2">
    <div class="card"><div class="sect">Details</div><dl class="facts">
      <div><dt>Matrix</dt><dd>${c.h(s.matrix)}</dd></div><div><dt>Batch</dt><dd class="id">${c.h(s.batch)}</dd></div>
      <div><dt>Method</dt><dd>${c.h(s.method)}</dd></div><div><dt>Instrument</dt><dd>${c.h(s.instrument)}</dd></div>
      <div><dt>Received</dt><dd>${c.fmt.date(s.received)}</dd></div><div><dt>Due</dt><dd class="${LAB.late(s) ? 'late' : ''}">${c.fmt.date(s.due)}</dd></div></dl></div>
    <div class="card"><div class="sect">Activity</div><ul class="log">${log.map(e => `<li><span class="av">${c.initials(e.who)}</span><div>${c.h(e.text)}<br><small>${c.h(e.who)} · ${c.fmt.rel(e.at)}</small></div></li>`).join('') || '<li><small>No activity yet.</small></li>'}</ul></div>
  </div>`;
});
ZAS.on('advance', d => {
  const s = ZAS.store.get('samples', d.id), next = LAB.STAGES[LAB.STAGES.indexOf(s.stage) + 1];
  ZAS.store.patch('samples', d.id, {stage: next});
  ZAS.store.put('events', {sample: d.id, at: new Date().toISOString(), who: ZAS.ctx().persona.name, text: `Moved to ${next}`});
  ZAS.toast(next === 'Released' ? 'Result released' : `Moved to ${next}`, 'ok');
});
ZAS.on('reject', d => {
  ZAS.store.patch('samples', d.id, {stage: 'On instrument'});
  ZAS.store.put('events', {sample: d.id, at: new Date().toISOString(), who: ZAS.ctx().persona.name, text: 'Sent back for re-run'});
  ZAS.toast('Sent back to the analyst');
});
