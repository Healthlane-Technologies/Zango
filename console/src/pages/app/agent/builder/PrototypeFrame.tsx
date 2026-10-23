// The open prototype (Free design): the app the agent writes, in its own look, shown as-is.
//
// The server assembles the agent's parts into one page (prototype.py) with its own CSP. It runs
// in a sandbox with scripts only, so it can't read the console's cookies or call its API. The
// page's runtime (zas-proto.js) reports where the user is ("location") and what failed ("error");
// we send "goto" so a reload after the agent's next write lands where the user was.

import { useEffect, useRef, useState } from 'react';
import { usePrototypeHtml, type PreviewFocus } from '@/api/agentMode';
import { ErrorState, Icon, Skeleton } from '@/ui';

const SANDBOX = 'allow-scripts allow-popups allow-forms';

export interface ProtoPlace {
	screen: string;
	role?: string;
	record?: string | number | null;
}

type FromProto =
	| { source: 'zas-proto'; type: 'ready'; screens?: string[] }
	| {
			source: 'zas-proto';
			type: 'location';
			screen: string;
			title?: string;
			role?: string;
			roleLabel?: string;
			record?: string | number | null;
	  }
	| { source: 'zas-proto'; type: 'error'; part?: string; message?: string };

/** What the chat sends with a reply: the screen and persona the user was on. */
export function protoFocus(at: Extract<FromProto, { type: 'location' }>): PreviewFocus {
	const part = `screens/${at.screen}.js`;
	return {
		role: at.roleLabel || at.role,
		page: at.screen,
		title: `${at.title || at.screen} (${part})`,
		...(at.record != null && at.record !== ''
			? { record: { entity: 'record', id: String(at.record), label: String(at.record) } }
			: {}),
	};
}

export function PrototypeFrame({
	appId,
	reqId,
	revision,
	onFocus,
	goto,
	className,
}: {
	appId: string;
	reqId: string;
	/** The requirement's prototype_revision: a new one reloads the page. */
	revision: number | undefined;
	onFocus?: (focus: PreviewFocus) => void;
	/** Open this place on first load (the full-page preview). */
	goto?: ProtoPlace | null;
	className?: string;
}) {
	const page = usePrototypeHtml(appId, reqId, revision);
	const frame = useRef<HTMLIFrameElement>(null);
	// Where the user is, so the page reopens there after the agent's next write.
	const place = useRef<ProtoPlace | null>(goto ?? null);
	const onFocusRef = useRef(onFocus);
	onFocusRef.current = onFocus;
	const [failure, setFailure] = useState<{ part?: string; message?: string } | null>(null);

	useEffect(() => {
		const onMessage = (event: MessageEvent) => {
			if (!frame.current || event.source !== frame.current.contentWindow) return;
			const msg = event.data as FromProto;
			if (!msg || msg.source !== 'zas-proto') return;
			if (msg.type === 'ready') {
				setFailure(null);
				if (place.current?.screen)
					frame.current.contentWindow?.postMessage(
						{ source: 'zango-console', type: 'goto', ...place.current },
						'*',
					);
			} else if (msg.type === 'location' && msg.screen) {
				place.current = { screen: msg.screen, role: msg.role, record: msg.record ?? null };
				onFocusRef.current?.(protoFocus(msg));
			} else if (msg.type === 'error') {
				setFailure({ part: msg.part, message: msg.message });
			}
		};
		window.addEventListener('message', onMessage);
		return () => window.removeEventListener('message', onMessage);
	}, []);

	if (page.error) {
		return (
			<div className="card">
				<ErrorState error={page.error as Error} onRetry={() => page.refetch()} />
			</div>
		);
	}
	return (
		<div className={className ? `emb ${className}` : 'emb'}>
			{failure && (
				<div className="bld-note err" role="alert">
					<Icon name="alert" size={13} />
					<span className="min-w-0 truncate">
						{failure.part ? <b>{failure.part}: </b> : null}
						{failure.message || 'Part of the prototype failed to run.'}
					</span>
				</div>
			)}
			{page.data ? (
				<iframe
					ref={frame}
					className="emb-frame"
					title="App prototype"
					sandbox={SANDBOX}
					srcDoc={page.data}
				/>
			) : page.isLoading || !revision ? (
				<div className="grid gap-3 p-4">
					<Skeleton width="40%" height={18} />
					<Skeleton height={320} />
				</div>
			) : (
				<div className="p-6 text-t3">No prototype yet.</div>
			)}
		</div>
	);
}
