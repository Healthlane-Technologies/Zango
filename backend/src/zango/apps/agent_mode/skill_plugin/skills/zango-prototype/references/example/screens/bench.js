// A home page in the default look: header band, stat tiles, then a card (icon header) with the work list.
ZAS.screen('bench', c => {
  const mine = c.store.list('samples', s => s.assignee === c.persona.name && s.stage !== 'Released');
  const late = mine.filter(LAB.late), running = mine.filter(s => s.stage === 'On instrument');
  const stat = (icon, label, value, unit, note, tone, alert) => `<div class="z-card z-stat ${alert ? 'alert' : ''} ${tone}">
    <div class="lbl">${c.I(icon, 14)}${label}</div><div class="v">${value}<small>${unit}</small></div><div class="d">${note}</div></div>`;
  return `
  <header class="z-top"><div><h1>Good morning, ${c.h(c.persona.name.split(' ')[0])}</h1><p>${mine.length} samples on your bench</p></div></header>
  <div class="z-content">
    <div class="z-stats">
      ${stat('alarm-clock', 'Past due', late.length, 'samples', 'Past their due date', 't-red', late.length > 0)}
      ${stat('activity', 'On instrument', running.length, 'samples', 'Running now', 't-amber')}
      ${stat('inbox', 'Waiting to start', mine.filter(s => s.stage === 'Received').length, 'samples', 'Received, not prepared', 't-blue')}
    </div>
    <section class="z-card"><div class="z-ch"><div class="ic">${c.I('flask-conical', 16)}</div><div><h3>My bench</h3><p>Samples assigned to you, soonest due first</p></div></div>
      ${mine.length ? `<div class="z-tbl-w"><table class="z-t"><thead><tr><th>Sample</th><th>Due</th><th>Stage</th><th></th></tr></thead><tbody>
        ${mine.sort((a, b) => new Date(a.due) - new Date(b.due)).map(s => `<tr data-act="open" data-id="${c.h(s.id)}">
          <td><div class="c-code">${c.h(s.id)}</div><div class="c-sub">${c.h(s.label)}</div></td>
          <td><span class="${LAB.late(s) ? 'c-late' : ''}">${c.fmt.rel(s.due)}</span></td><td>${LAB.badge(s.stage)}</td>
          <td class="chev">${c.I('chevron-right', 15)}</td></tr>`).join('')}</tbody></table></div>`
        : `<div class="z-empty"><div class="ei">${c.I('check-check', 20)}</div><b>Nothing on your bench</b><p>New samples appear here when they are assigned to you.</p></div>`}
    </section>
  </div>`;
});
