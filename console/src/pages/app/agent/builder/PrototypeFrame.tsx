// The open prototype (Free design): the app the agent writes, in its own look, shown as-is.
//
// The server assembles the agent's parts into one page (prototype.py) with its own CSP. It runs
// in a sandbox with scripts only, so it can't read the console's cookies or call its API. The
// page's runtime (zas-proto.js) reports where the user is ("location") and what failed ("error");
// we send "goto" so a reload after the agent's next write lands where the user was.

import { useEffect, useRef, useState, type RefObject } from 'react';
import { usePrototypeHtml, type PreviewFocus } from '@/api/agentMode';
import { ErrorState, Icon, Skeleton } from '@/ui';

const SANDBOX = 'allow-scripts allow-popups allow-forms';
// The prototype is drawn at a desktop width and scaled to fit the pane. Laid out at the pane's
// own width, a mockup's responsive CSS kicks in (a sidebar became a top bar with its group
// labels hidden), and the user approves a layout the built app never has.
const DESKTOP_WIDTH = 1280;

/** The scale that fits a DESKTOP_WIDTH page into the stage, and the stage's height. */
function useFit(stage: RefObject<HTMLDivElement | null>, active: boolean) {
	const [fit, setFit] = useState({ scale: 1, height: 0 });
	useEffect(() => {
		const el = stage.current;
		if (!el || !active) return;
		const measure = () =>
			setFit({ scale: Math.min(1, el.clientWidth / DESKTOP_WIDTH), height: el.clientHeight });
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(el);
		return () => observer.disconnect();
	}, [stage, active]);
	return fit;
}

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
	const stage = useRef<HTMLDivElement>(null);
	const fit = useFit(stage, !!page.data);

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
				<div ref={stage} className="emb-frame emb-stage">
					<iframe
						ref={frame}
						title="App prototype"
						sandbox={SANDBOX}
						srcDoc={page.data}
						style={
							fit.scale < 1
								? {
										width: DESKTOP_WIDTH,
										height: fit.height / fit.scale,
										transform: `scale(${fit.scale})`,
										transformOrigin: '0 0',
									}
								: undefined
						}
					/>
				</div>
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
