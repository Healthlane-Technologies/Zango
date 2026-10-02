/*
 * Zango builder bridge for Journey Studio (the PSP journey builder).
 *
 * Injected by the platform after the builder's own scripts, inside a sandboxed
 * iframe (scripts only, opaque origin). It leaves the builder untouched and
 * drives it through the globals it already exposes: J, fromYaml, toYaml,
 * migrate, render, commit/save.
 *
 * Protocol ("zango-builder/1", window.postMessage):
 *   host → builder  {source:'zango-host', type:'load', yaml, readOnly}
 *                   {source:'zango-host', type:'lock', readOnly}
 *                   {source:'zango-host', type:'preview', on}   (the app preview)
 *   builder → host  {source:'zango-builder', type:'ready', protocol}
 *                   {source:'zango-builder', type:'change', yaml}
 *                   {source:'zango-builder', type:'error', message}
 */
(function () {
	'use strict';
	var PROTOCOL = 'zango-builder/1';
	var applying = false;
	var timer = null;

	function send(msg) {
		msg.source = 'zango-builder';
		window.parent.postMessage(msg, '*');
	}

	function setStatus(text) {
		var el = document.getElementById('saved');
		if (el) el.textContent = text;
	}

	// Every edit ends in commit() -> save(). Instead of localStorage (unavailable
	// in the sandbox, and not the source of truth anyway) the YAML goes to the
	// host, which owns saving, conflicts and validation.
	window.save = function () {
		if (applying) return;
		setStatus('Edited');
		clearTimeout(timer);
		timer = setTimeout(function () {
			try {
				send({ type: 'change', yaml: toYaml() });
			} catch (err) {
				send({ type: 'error', message: 'Could not write the journey: ' + err });
			}
		}, 150);
	};

	function lock(readOnly) {
		document.documentElement.classList.toggle('zango-locked', !!readOnly);
	}

	window.addEventListener('message', function (event) {
		var msg = event.data;
		if (!msg || msg.source !== 'zango-host') return;
		if (msg.type === 'load') {
			applying = true;
			try {
				J = migrate(fromYaml(String(msg.yaml || '')));
				render();
				setStatus('');
			} catch (err) {
				send({ type: 'error', message: 'Could not load the journey: ' + err });
			} finally {
				applying = false;
			}
			lock(msg.readOnly);
		} else if (msg.type === 'lock') {
			lock(msg.readOnly);
		} else if (msg.type === 'preview') {
			try {
				setPreview(!!msg.on);
			} catch (err) {
				send({ type: 'error', message: 'Could not open the preview: ' + err });
			}
		}
	});

	// The host's tabs own the preview mode; keep the builder's shortcut from
	// switching it behind their back.
	document.addEventListener(
		'keydown',
		function (e) {
			if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'p' || e.key === 'P')) e.stopImmediatePropagation();
		},
		true
	);

	// The host owns the data: starting over or loading the demo journey here would
	// silently replace the app's journey, so those two header actions are hidden.
	var style = document.createElement('style');
	style.textContent =
		'[data-act="new"],[data-act="example"]{display:none!important}' +
		// Design/Preview is the host's Builder and Preview tabs, and the
		// preview's checks link is its Checks tab.
		'[data-pvmode],:has(>[data-pvmode]),[data-pvchecks]{display:none!important}' +
		'.zango-locked .body,.zango-locked .hd input{pointer-events:none;opacity:.6}' +
		'.zango-locked .hd::after{content:"The agent is editing — read only";margin-left:12px;' +
		'font:500 12px Inter,sans-serif;color:#b45309}';
	document.head.appendChild(style);

	send({ type: 'ready', protocol: PROTOCOL });
})();
