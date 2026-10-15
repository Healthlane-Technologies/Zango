/*
 * Zango preview bridge for App Studio (the Zango app spec v1 previewer).
 *
 * Injected by the platform after the page's own scripts, inside a sandboxed
 * iframe (scripts only, opaque origin). The page is a preview, not an editor:
 * its YAML pane and header are hidden, and the host's spec is the only one it
 * ever shows. It drives the page through the globals it already has: S (state)
 * and parse(text), which rebuilds the app and keeps the current page and role
 * when they still exist in the new spec.
 *
 * Protocol ("zango-builder/1", window.postMessage):
 *   host → page  {source:'zango-host', type:'load', yaml, readOnly}
 *                {source:'zango-host', type:'lock', readOnly}      (ignored)
 *                {source:'zango-host', type:'preview', on}         (ignored: always a preview)
 *                {source:'zango-host', type:'goto', location}       (open a place: role, page, record, tab)
 *   page → host  {source:'zango-builder', type:'ready', protocol, capabilities: ['focus', 'goto']}
 *                {source:'zango-builder', type:'error', message}
 *                {source:'zango-builder', type:'focus', focus}     where the user is ({role, page,
 *                  title, path, record?, tab?, view?}), on every move; with `pointed`
 *                  ({path, label, text}) when they used "Point" and clicked something.
 *                  Paths are the spec tools' paths into the YAML.
 * The page never sends 'change': the spec is changed through the agent or the
 * host's own YAML editor, never here.
 *
 * Headless checks (agent_mode/preview_probe.py) load the page directly, without a
 * host: they call window.zangoLoad(yaml), then the page's own window.ZAS_PROBE.
 */
(function () {
	'use strict';
	var PROTOCOL = 'zango-builder/1';
	var loaded = false;

	function send(msg) {
		msg.source = 'zango-builder';
		window.parent.postMessage(msg, '*');
	}

	// Preview only: drop the editor pane and the studio header. Until the host's
	// spec arrives, the built-in sample (already rendered at boot) stays hidden
	// behind a neutral placeholder, so it never passes for the user's app.
	var style = document.createElement('style');
	style.textContent =
		'.hd,.ed{display:none!important}' +
		'.body{grid-template-columns:1fr!important}' +
		'html:not(.zango-loaded) #pvbar,html:not(.zango-loaded) #zapp>*{visibility:hidden}' +
		'html:not(.zango-loaded) #zapp::after{content:"Waiting for the spec\\2026";position:absolute;inset:0;' +
		'display:flex;align-items:center;justify-content:center;font:500 13px Inter,-apple-system,sans-serif;color:#667085}' +
		'.zas-point.on{background:#4F46E5;color:#fff;border-color:#4F46E5}' +
		'.zas-picking #zapp,.zas-picking #zapp *{cursor:crosshair!important}' +
		'.zas-hover{outline:2px solid #4F46E5!important;outline-offset:2px;border-radius:6px}' +
		'.zas-picking body::after{content:"Click the part you mean \\00B7  Esc to cancel";position:fixed;left:50%;bottom:14px;' +
		'transform:translateX(-50%);padding:6px 12px;border-radius:999px;background:#4F46E5;color:#fff;' +
		'font:500 12px Inter,-apple-system,sans-serif;box-shadow:0 4px 14px rgba(16,24,40,.18);pointer-events:none;z-index:2147483647}';
	document.head.appendChild(style);

	function load(text) {
		if (!loaded) {
			// Forget the sample's page, role and demo data: start the host's app
			// on its own landing page. If its YAML does not parse, there is no
			// "last valid version" to fall back on, so say so rather than show
			// the sample.
			S.M = null;
			S.route = null;
			S.role = null;
			S.builtFor = null;
		}
		var src = document.getElementById('src');
		if (src) src.value = text;
		parse(text);
		if (!loaded) {
			loaded = true;
			document.documentElement.classList.add('zango-loaded');
		}
		pointButton();
		reportFocus();
	}

	window.zangoLoad = load;

	// -- where the user is, and what they point at --------------------------------------------

	var lastFocus = '';
	var focusTimer = null;
	var picking = false;
	var hovered = null;

	function location() {
		try {
			return window.ZAS_LOCATION ? window.ZAS_LOCATION() : null;
		} catch (err) {
			return null;
		}
	}

	function reportFocus() {
		var focus = location();
		var key = JSON.stringify(focus);
		if (!focus || key === lastFocus) return;
		lastFocus = key;
		send({ type: 'focus', focus: focus });
	}

	function setPicking(on) {
		picking = on;
		document.documentElement.classList.toggle('zas-picking', on);
		if (!on && hovered) {
			hovered.classList.remove('zas-hover');
			hovered = null;
		}
		var btn = document.getElementById('zasPoint');
		if (btn) btn.classList.toggle('on', on);
	}

	function pointButton() {
		var bar = document.getElementById('pvbar');
		if (!bar || document.getElementById('zasPoint')) return;
		var btn = document.createElement('button');
		btn.id = 'zasPoint';
		btn.type = 'button';
		btn.className = 'btn sm zas-point' + (picking ? ' on' : '');
		btn.title = 'Point at a part of the app, then tell the agent what to change';
		btn.textContent = 'Point';
		btn.addEventListener('click', function (e) {
			e.stopPropagation();
			setPicking(!picking);
		});
		bar.insertBefore(btn, bar.firstChild);
	}

	document.addEventListener('zas:render', function () {
		if (!loaded) return;
		pointButton();
		clearTimeout(focusTimer);
		focusTimer = setTimeout(reportFocus, 120);
	});

	document.addEventListener(
		'mouseover',
		function (e) {
			if (!picking) return;
			var el = e.target.closest && e.target.closest('[data-zas-path]');
			if (el === hovered) return;
			if (hovered) hovered.classList.remove('zas-hover');
			hovered = el;
			if (el) el.classList.add('zas-hover');
		},
		true,
	);

	document.addEventListener(
		'click',
		function (e) {
			if (!picking || (e.target.closest && e.target.closest('#zasPoint'))) return;
			e.preventDefault();
			e.stopPropagation();
			var el = e.target.closest && e.target.closest('[data-zas-path]');
			setPicking(false);
			var focus = location() || {};
			if (!el && !focus.path) return;
			// Nothing of the spec drawn here (a gap, the menu bar): point at the page itself.
			focus.pointed = {
				path: el ? el.getAttribute('data-zas-path') : focus.path,
				label: el ? el.getAttribute('data-zas-label') || '' : focus.title || 'this page',
				text: String(e.target.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 80),
			};
			send({ type: 'focus', focus: focus });
		},
		true,
	);

	document.addEventListener('keydown', function (e) {
		if (picking && e.key === 'Escape') setPicking(false);
	});

	window.addEventListener('message', function (event) {
		var msg = event.data;
		if (!msg || msg.source !== 'zango-host') return;
		if (msg.type === 'goto') {
			try {
				if (window.ZAS_GOTO) window.ZAS_GOTO(msg.location);
			} catch (err) {
				/* a place that no longer exists: stay where we are */
			}
		} else if (msg.type === 'load') {
			try {
				load(String(msg.yaml || ''));
			} catch (err) {
				send({ type: 'error', message: 'Could not show the preview: ' + err });
			}
		}
	});

	send({ type: 'ready', protocol: PROTOCOL, capabilities: ['focus', 'goto'] });
})();
