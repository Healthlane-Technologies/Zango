import { useEffect, useRef, useState } from 'react';
import type { RunEvent } from '@/api/agentRuns';
import { cx, Icon } from '@/ui';
import { timeOfDay } from './format';

// Event kinds from AgentRunEvent.EventKind; the label shown in the kind column.
const KIND: Record<string, string> = {
	sys: 'system',
	init: 'session',
	assistant: 'agent',
	thinking: 'think',
	tool_use: 'tool',
	tool_result: 'result',
	skill: 'skill',
	user: 'input',
	compact: 'compact',
	hook_deny: 'blocked',
	post_step: 'step',
	stdout: 'stdout',
	stderr: 'stderr',
	result: 'done',
	error: 'error',
};

/** Line tone, matching the prototype log's .hd/.ok/.wn/.ag classes. */
function tone(e: RunEvent): string {
	if (e.is_error || e.kind === 'error' || e.kind === 'hook_deny' || e.level === 'err') return 'er';
	if (e.kind === 'stderr' || e.level === 'warn') return 'wn';
	if (e.kind === 'result' || e.kind === 'post_step') return 'ok';
	if (e.kind === 'assistant') return 'hd';
	if (e.kind === 'skill') return 'ag';
	if (e.kind === 'thinking') return 'th';
	return '';
}

function summary(e: RunEvent): string {
	if (e.message) return e.message;
	if (e.tool_name) return e.tool_name;
	return '';
}

/**
 * The raw event stream: one line per event, click a line with a payload to see it. Sticks to the
 * bottom while you're at the bottom; scrolling up to read stops the auto-scroll.
 */
export function RunLog({
	events,
	live,
	total,
}: {
	events: RunEvent[];
	live: boolean;
	total?: number;
}) {
	const bodyRef = useRef<HTMLDivElement>(null);
	const pinned = useRef(true);
	const [open, setOpen] = useState<Set<number>>(new Set());

	useEffect(() => {
		const el = bodyRef.current;
		if (el && pinned.current) el.scrollTop = el.scrollHeight;
	}, [events.length]);

	const toggle = (seq: number) =>
		setOpen((s) => {
			const next = new Set(s);
			if (next.has(seq)) next.delete(seq);
			else next.add(seq);
			return next;
		});

	return (
		<div className="rp-log">
			<div className="lh">
				{live ? (
					<span className="spin" style={{ color: 'var(--accent)' }} />
				) : (
					<Icon name="logs" size={13} />
				)}
				<b>Build log</b>
				<span>{live ? '· streaming' : '· complete'}</span>
				<span className="num ml-auto">{(total ?? events.length).toLocaleString()} events</span>
			</div>
			<div
				ref={bodyRef}
				className="lb"
				onScroll={(e) => {
					const el = e.currentTarget;
					pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 24;
				}}
			>
				{events.length === 0 && (
					<div className="px-4 py-2 text-t4">Waiting for the first event…</div>
				)}
				{events.map((e) => {
					const hasData =
						e.data !== null &&
						e.data !== undefined &&
						!(typeof e.data === 'object' && !Object.keys(e.data as object).length);
					const isOpen = open.has(e.seq);
					return (
						<div key={e.seq}>
							<div
								className={cx('ln', tone(e), hasData && 'x')}
								role={hasData ? 'button' : undefined}
								tabIndex={hasData ? 0 : undefined}
								aria-expanded={hasData ? isOpen : undefined}
								onClick={hasData ? () => toggle(e.seq) : undefined}
								onKeyDown={
									hasData
										? (ev) => {
												if (ev.key === 'Enter' || ev.key === ' ') {
													ev.preventDefault();
													toggle(e.seq);
												}
											}
										: undefined
								}
							>
								<span className="no">{e.seq}</span>
								<span className="ts">{timeOfDay(e.ts)}</span>
								<span className="k">{KIND[e.kind] ?? e.kind}</span>
								<span className="tx">
									{e.tool_name && e.kind === 'tool_use' && !e.message.startsWith(e.tool_name)
										? `${e.tool_name} · `
										: ''}
									{summary(e)}
								</span>
							</div>
							{isOpen && <pre className="raw">{JSON.stringify(e.data, null, 2)}</pre>}
						</div>
					);
				})}
			</div>
		</div>
	);
}
