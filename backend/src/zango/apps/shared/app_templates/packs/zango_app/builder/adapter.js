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
 *   page → host  {source:'zango-builder', type:'ready', protocol, capabilities: []}
 *                {source:'zango-builder', type:'error', message}
 * The page never sends 'change': the spec is changed through the agent or the
 * host's own YAML editor, never here.
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
		'display:flex;align-items:center;justify-content:center;font:500 13px Inter,-apple-system,sans-serif;color:#667085}';
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
	}

	window.addEventListener('message', function (event) {
		var msg = event.data;
		if (!msg || msg.source !== 'zango-host') return;
		if (msg.type === 'load') {
			try {
				load(String(msg.yaml || ''));
			} catch (err) {
				send({ type: 'error', message: 'Could not show the preview: ' + err });
			}
		}
	});

	send({ type: 'ready', protocol: PROTOCOL, capabilities: [] });
})();
