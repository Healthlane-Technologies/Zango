// The rail: logo tile (the app's initials on the brand colour), app name and module, who is signed in,
// the persona's menu with a count per list, and the footer. The page draws its own header band.
const COUNTS = {samples: () => ZAS.store.list('samples').length,
  bench: () => ZAS.store.list('samples', s => s.assignee === ZAS.ctx().persona.name && s.stage !== 'Released').length};
ZAS.shell((c, body) => `
  <div class="z-shell">
    <aside class="z-side">
      <div class="z-brand"><div class="z-logo">${c.initials(c.M.title)}</div><div><b>${c.h(c.M.title)}</b><span>${c.h(c.M.subtitle || '')}</span></div></div>
      <div class="z-who">${LAB.av(c.persona.name)}<div><b>${c.h(c.persona.name)}</b><span>${c.h(c.roleLabel)}</span></div></div>
      <nav class="z-nav">${c.nav.map(n => `<a class="z-ni ${n.on ? 'on' : ''}" data-act="go" data-go="${n.id}">${c.I(n.icon || 'circle')}${c.h(n.title)}${COUNTS[n.id] ? `<span class="z-ni-n">${COUNTS[n.id]()}</span>` : ''}</a>`).join('')}</nav>
      <div class="z-foot">${c.h(c.M.title)} · Powered by Zelthy</div>
    </aside>
    <main class="z-main">${body}</main>
  </div>`);
