import { useEffect, useRef, useState } from 'react';
import { isRunActive, type RunStatus } from '@/api/agentMode';
import { fetchTail, TAIL_PAGE, type RunEvent, type TailResponse } from '@/api/agentRuns';
import { mergeEvents } from './events';

// Same cadence as the classic panel: a queued run changes nothing worth a request every
// second; a running one should feel live.
const POLL_QUEUED_MS = 3000;
const POLL_RUNNING_MS = 1200;

export interface RunTail {
	events: RunEvent[];
	status: RunStatus | undefined;
	phase: string;
	isTerminal: boolean;
	progress: TailResponse['progress'] | undefined;
	/** The first page has arrived. */
	ready: boolean;
	error: Error | null;
}

const EMPTY: RunTail = {
	events: [],
	status: undefined,
	phase: 'preparing',
	isTerminal: false,
	progress: undefined,
	ready: false,
	error: null,
};

/**
 * Follow a run's event stream with `?after_seq=` until it is terminal. A finished run is read
 * to the end once (pages of TAIL_PAGE) and then left alone. `onTerminal` fires once when a run
 * that was live when we started watching finishes.
 */
export function useRunTail(
	appId: string,
	runId: string | undefined,
	onTerminal?: () => void,
): RunTail {
	const [tail, setTail] = useState<RunTail>(EMPTY);
	const onTerminalRef = useRef(onTerminal);
	onTerminalRef.current = onTerminal;

	useEffect(() => {
		setTail(EMPTY);
		if (!runId) return;
		let cancelled = false;
		let timer: ReturnType<typeof setTimeout> | undefined;
		let seq = 0;
		let sawLive = false;

		const poll = async () => {
			let r: TailResponse;
			try {
				r = await fetchTail(appId, runId, seq);
			} catch (e) {
				if (cancelled) return;
				setTail((t) => ({ ...t, ready: true, error: e as Error }));
				timer = setTimeout(poll, POLL_QUEUED_MS);
				return;
			}
			if (cancelled) return;
			if (r.events.length) seq = r.next_seq ?? r.events[r.events.length - 1].seq;
			setTail((t) => ({
				events: mergeEvents(t.events, r.events),
				status: r.status,
				phase: r.phase || t.phase,
				isTerminal: r.is_terminal,
				progress: r.progress,
				ready: true,
				error: null,
			}));
			// A full page means there is more behind it right now; fetch it straight away.
			if (r.events.length >= TAIL_PAGE) {
				timer = setTimeout(poll, 0);
				return;
			}
			if (r.is_terminal) {
				if (sawLive) onTerminalRef.current?.();
				return;
			}
			sawLive = true;
			timer = setTimeout(
				poll,
				isRunActive(r.status) && r.status !== 'queued' ? POLL_RUNNING_MS : POLL_QUEUED_MS,
			);
		};
		poll();
		return () => {
			cancelled = true;
			if (timer) clearTimeout(timer);
		};
	}, [appId, runId]);

	return tail;
}
