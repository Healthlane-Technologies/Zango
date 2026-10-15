// A template's own builder (e.g. the PSP Journey Studio), hosted as-is in a sandboxed iframe.
//
// The page is superadmin-authored code, so it runs with scripts only: no same-origin, so it
// can't read the console's cookies or call its API. It talks to us over postMessage
// ("zango-builder/1", see the template's adapter.js): we `load` the draft into it and `lock`
// it while the agent works; it reports every edit as a `change` with the whole YAML, which
// becomes an ordinary draft edit (SaveBar, conflicts, validation all as for the YAML tab).
// The same page shows the app's live preview: `preview` switches it into its simulated app.
// A preview-only page (App Studio) ignores `preview` and never reports a `change`; `ready`
// says which the page is through `capabilities` ('edit', 'preview', 'focus', 'goto').
// App Studio also reports `focus` — where the user is, and what they clicked after "Point" —
// and takes `goto` to open a place (the full-page preview opens where the user was).

import { useCallback, useEffect, useRef, useState } from 'react';
import { useBuilderHtml, type PreviewFocus } from '@/api/agentMode';
import { ErrorState, Icon, Skeleton } from '@/ui';

const SANDBOX = 'allow-scripts allow-downloads allow-popups allow-modals';

type FromBuilder =
	| { source: 'zango-builder'; type: 'ready'; protocol?: string; capabilities?: string[] }
	| { source: 'zango-builder'; type: 'change'; yaml: string }
	| { source: 'zango-builder'; type: 'error'; message: string }
	| { source: 'zango-builder'; type: 'focus'; focus: PreviewFocus };

// The server stores specs without trailing whitespace; that difference is not an edit.
const norm = (s: string | null | undefined) => (s ?? '').replace(/\s+$/, '');

export function EmbeddedBuilder({
	url,
	text,
	readOnly,
	onChange,
	hidden,
	preview = false,
	onReady,
	onFocus,
	goto,
	className,
}: {
	url: string;
	/** The draft on screen. Loaded into the builder whenever it changes from outside it. */
	text: string;
	readOnly: boolean;
	onChange: (yaml: string) => void;
	/** Kept mounted (and its UI state alive) while another tab is showing. */
	hidden?: boolean;
	/** Show the builder's own preview of the app instead of its editor. */
	preview?: boolean;
	/** The page's declared capabilities, once it is ready (undefined: it didn't say). */
	onReady?: (capabilities: string[] | undefined) => void;
	/** Where the user is in the preview (and what they pointed at), as the page reports it. */
	onFocus?: (focus: PreviewFocus) => void;
	/** Open this place once the page has the spec. */
	goto?: PreviewFocus | null;
	className?: string;
}) {
	const page = useBuilderHtml(url);
	const frame = useRef<HTMLIFrameElement>(null);
	const ready = useRef(false);
	// The text the builder already holds: whatever we last loaded or it last reported.
	const known = useRef<string | null>(null);
	const [error, setError] = useState<string | null>(null);

	const latest = useRef({ text, readOnly, onChange, preview, onReady, onFocus, goto });
	latest.current = { text, readOnly, onChange, preview, onReady, onFocus, goto };
	const wentTo = useRef(false);

	const post = useCallback((message: Record<string, unknown>) => {
		frame.current?.contentWindow?.postMessage({ source: 'zango-host', ...message }, '*');
	}, []);

	const load = useCallback(() => {
		const { text: t, readOnly: ro } = latest.current;
		known.current = norm(t);
		post({ type: 'load', yaml: t, readOnly: ro });
		// A reload re-renders the editor; the preview is rebuilt from the new journey.
		if (latest.current.preview) post({ type: 'preview', on: true });
		if (latest.current.goto && !wentTo.current) {
			wentTo.current = true;
			post({ type: 'goto', location: latest.current.goto });
		}
	}, [post]);

	useEffect(() => {
		const onMessage = (event: MessageEvent) => {
			if (!frame.current || event.source !== frame.current.contentWindow) return;
			const msg = event.data as FromBuilder;
			if (!msg || msg.source !== 'zango-builder') return;
			if (msg.type === 'ready') {
				ready.current = true;
				setError(null);
				latest.current.onReady?.(
					Array.isArray(msg.capabilities) ? msg.capabilities.map(String) : undefined,
				);
				load();
			} else if (msg.type === 'change' && typeof msg.yaml === 'string') {
				known.current = norm(msg.yaml);
				setError(null);
				latest.current.onChange(msg.yaml);
			} else if (msg.type === 'focus' && msg.focus && typeof msg.focus === 'object') {
				latest.current.onFocus?.(msg.focus);
			} else if (msg.type === 'error') {
				setError(String(msg.message || 'The builder reported an error.'));
			}
		};
		window.addEventListener('message', onMessage);
		return () => window.removeEventListener('message', onMessage);
	}, [load]);

	// A new srcdoc is a new page: wait for its `ready` again.
	useEffect(() => {
		ready.current = false;
		known.current = null;
	}, [page.data]);

	// Outside changes (the agent's edit, a YAML-tab edit, discard, a conflict review) — but
	// never an echo of the builder's own change, which would reset its UI and scroll.
	useEffect(() => {
		if (ready.current && norm(text) !== known.current) load();
	}, [text, load]);

	useEffect(() => {
		if (ready.current) post({ type: 'lock', readOnly });
	}, [readOnly, post]);

	// Re-sent whenever the page comes on screen, so the tab wins over the page's own switch.
	useEffect(() => {
		if (ready.current && !hidden) post({ type: 'preview', on: preview });
	}, [preview, hidden, post]);

	if (page.error) {
		return (
			<div className="card">
				<ErrorState error={page.error as Error} onRetry={() => page.refetch()} />
			</div>
		);
	}
	return (
		<div className={className ? `emb ${className}` : 'emb'} hidden={hidden}>
			{error && (
				<div className="bld-note err" role="alert">
					<Icon name="alert" size={13} />
					{error}
				</div>
			)}
			{page.data ? (
				<iframe
					ref={frame}
					className="emb-frame"
					title={preview ? 'App preview' : 'Template builder'}
					sandbox={SANDBOX}
					srcDoc={page.data}
				/>
			) : (
				<div className="grid gap-3 p-4">
					<Skeleton width="40%" height={18} />
					<Skeleton height={320} />
				</div>
			)}
		</div>
	);
}
