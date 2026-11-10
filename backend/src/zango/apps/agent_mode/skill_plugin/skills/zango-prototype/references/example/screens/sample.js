// A record page in the default look: header band (back link, icon tile, mono code + status badge, name,
// meta line, actions, a stepper with dates, tabs with counts), then the body: cards with icon headers on
// the left, a summary rail on the right.
ZAS.screen('sample', c => {
  const s = c.store.get('samples', c.record);
  if (!s) return `<div class="z-empty"><b>This sample no longer exists.</b><p><a class="d-back" data-act="go" data-go="samples">Back to samples</a></p></div>`;
  const at = LAB.STAGES.indexOf(s.stage), log = c.store.list('events', e => e.sample === s.id);
  const next = LAB.STAGES[at + 1], mine = s.assignee === c.persona.name, tab = c.params.tab || 'overview';
  const action = c.role === 'lead' && s.stage === 'Review'
    ? `<button class="z-btn danger" data-act="reject" data-id="${s.id}">Send back</button><button class="z-btn pri" data-act="advance" data-id="${s.id}">${c.I('check', 15)}Release result</button>`
    : mine && next && s.stage !== 'Review' ? `<button class="z-btn pri" data-act="advance" data-id="${s.id}">${c.I('arrow-right-circle', 15)}Move to ${next}</button>` : '';
  const when = st => (log.find(e => e.stage === st) || {}).at;
  const steps = LAB.STAGES.map((st, i) => {
    const cls = i < at ? 'done' : i === at ? 'cur' : '';
    const sub = i < at ? c.fmt.date(when(st) || s.received) : i === at ? 'Current step' : '';
    return `<div class="d-step ${cls}"><i>${i < at ? c.I('check', 12) : i + 1}</i><div><b>${st}</b><span>${sub}</span></div></div>`;
  }).join('');
  const tabs = [['overview', 'Overview'], ['activity', 'Activity', log.length]]
    .map(([id, label, n]) => `<button role="tab" aria-selected="${tab === id}" class="d-tab ${tab === id ? 'on' : ''}" data-act="rec-tab" data-tab="${id}">${label}${n != null ? `<span class="n">${n}</span>` : ''}</button>`).join('');
  const f = (label, value, wide) => `<div class="d-f ${wide ? 'wide' : ''}"><dt>${label}</dt><dd>${value || '<span class="z-nil">—</span>'}</dd></div>`;
  const overview = `
    <section class="z-card d-panel"><div class="z-ch"><div class="ic">${c.I('flask-conical', 16)}</div><div><h3>Sample details</h3><p>Everything recorded at receipt.</p></div></div>
      <dl class="d-fields">${f('Matrix', c.h(s.matrix))}${f('Batch', `<span class="mono">${c.h(s.batch)}</span>`)}${f('Method', c.h(s.method))}
        ${f('Instrument', c.h(s.instrument))}${f('Received', c.fmt.date(s.received))}${f('Due', `<span class="${LAB.late(s) ? 'c-late' : ''}">${c.fmt.date(s.due)}</span>`)}
        ${f('Analyst', LAB.person(s.assignee))}${f('Stage', LAB.badge(s.stage))}</dl></section>`;
  const activity = `
    <section class="z-card d-panel"><div class="z-ch"><div class="ic">${c.I('history', 16)}</div><div><h3>Activity</h3><p>Every step, newest first.</p></div></div>
      ${log.length ? `<ul class="tl">${log.map(e => `<li class="t-brand"><span class="dt">${c.I('circle-dot', 13)}</span><div><b>${c.h(e.text)}</b><span>${c.h(e.who)} · ${c.fmt.rel(e.at)}</span></div></li>`).join('')}</ul>`
        : '<div class="z-empty"><p>No activity yet.</p></div>'}</section>`;
  return `
  <div class="d-head">
    <a class="d-back" data-act="go" data-go="samples">${c.I('arrow-left', 14)}Back to Samples</a>
    <div class="d-top"><div class="d-tile">${c.I('test-tube', 22)}</div>
      <div class="d-tt"><h1>${c.h(s.id)} ${LAB.badge(s.stage)}</h1><h2>${c.h(s.label)}</h2>
        <div class="d-meta"><span>${c.h(s.matrix)}</span><i class="dot"></i><span class="mono">${c.h(s.batch)}</span><i class="dot"></i><span>${c.h(s.method)}</span></div></div>
      <div class="d-acts">${action}</div></div>
    <div class="d-stepper">${steps}</div>
    <div class="d-tabs" role="tablist">${tabs}</div>
  </div>
  <div class="d-body">
    <div class="d-main">${tab === 'activity' ? activity : overview}</div>
    <aside class="d-rail">
      <div class="z-card"><div class="d-rh">${c.I('info', 15)}Summary</div>
        <div class="kvrow"><span>Code</span><span class="mono">${c.h(s.id)}</span></div>
        <div class="kvrow"><span>Analyst</span><span>${LAB.person(s.assignee)}</span></div>
        <div class="kvrow"><span>Due</span><span>${c.fmt.date(s.due)}</span></div></div>
      <div class="z-card"><div class="d-rh">${c.I('workflow', 15)}Workflow<span class="sp"></span>${LAB.badge(s.stage)}</div>
        <p>${LAB.STAGES.join(' → ')}. Each move is logged with who made it and when.</p></div>
    </aside>
  </div>`;
});
ZAS.on('rec-tab', d => ZAS.go('sample', {record: ZAS.ctx().record, params: {tab: d.tab}, replace: true}));
ZAS.on('advance', d => {
  const s = ZAS.store.get('samples', d.id), next = LAB.STAGES[LAB.STAGES.indexOf(s.stage) + 1];
  ZAS.store.patch('samples', d.id, {stage: next});
  ZAS.store.put('events', {sample: d.id, at: new Date().toISOString(), who: ZAS.ctx().persona.name, stage: next, text: `Moved to ${next}`});
  ZAS.toast(next === 'Released' ? 'Result released' : `Moved to ${next}`, 'ok');
});
ZAS.on('reject', d => {
  ZAS.store.patch('samples', d.id, {stage: 'On instrument'});
  ZAS.store.put('events', {sample: d.id, at: new Date().toISOString(), who: ZAS.ctx().persona.name, stage: 'On instrument', text: 'Sent back for re-run'});
  ZAS.toast('Sent back to the analyst');
});
