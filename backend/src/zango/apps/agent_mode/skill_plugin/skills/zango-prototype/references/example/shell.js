ZAS.shell((c, body) => `
  <div class="app">
    <aside class="side">
      <div class="brand">${c.I('microscope', 20)}<span>Sample Tracker</span></div>
      ${c.nav.map(n => `<a class="nav-a ${n.on ? 'on' : ''}" data-act="go" data-go="${n.id}">${c.I(n.icon || 'circle')}${c.h(n.title)}</a>`).join('')}
      <div class="me"><div class="av">${c.initials(c.persona.name)}</div><div>${c.h(c.persona.name)}<small>${c.h(c.roleLabel)}</small></div></div>
    </aside>
    <main class="main">${body}</main>
  </div>`);
