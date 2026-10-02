// The Workflows tab: the journey's lifecycles and the agent's user journeys, as swimlanes.
// Lifecycles are derived here from the draft on screen, so they follow every edit live.

import { useMemo, useRef, useState } from 'react';
import { Button, cx, EmptyState, Icon, Segmented } from '@/ui';
import { deriveWorkflows } from './workflows/derive';
import { Swimlane } from './workflows/Swimlane';
import type { WfProcess } from './workflows/types';

type Size = 'fit' | 'actual';

const LETTERS = 'abcdefghijklmnopqrstuvwxyz';
const letter = (i: number) => (i < 26 ? LETTERS[i] : `${LETTERS[Math.floor(i / 26) - 1]}${LETTERS[i % 26]}`);

function slug(s: string) {
	return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'workflow';
}

/** The SVG on screen with its title pill on top, as a standalone file. */
function download(svg: SVGSVGElement, title: string) {
	const NS = 'http://www.w3.org/2000/svg';
	const clone = svg.cloneNode(true) as SVGSVGElement;
	const [x, y, w, h] = (clone.getAttribute('viewBox') ?? '0 0 0 0').split(/\s+/).map(Number);
	const head = 44;
	clone.setAttribute('viewBox', `${x} ${y - head} ${w} ${h + head}`);
	clone.setAttribute('width', String(w));
	clone.setAttribute('height', String(h + head));
	clone.removeAttribute('class');
	clone.removeAttribute('style');
	const g = document.createElementNS(NS, 'g');
	const pill = document.createElementNS(NS, 'rect');
	const pw = Math.min(w, Math.max(260, title.length * 8 + 36));
	Object.entries({ x: 0, y: -head + 4, width: pw, height: 28, rx: 14, fill: '#9d9d9d', stroke: '#5a5a5a', 'stroke-width': 1.4 }).forEach(([k, v]) => pill.setAttribute(k, String(v)));
	const text = document.createElementNS(NS, 'text');
	Object.entries({ x: 16, y: -head + 23, 'font-size': 13.5, 'font-weight': 700, fill: '#fff' }).forEach(([k, v]) => text.setAttribute(k, String(v)));
	text.textContent = title;
	g.append(pill, text);
	clone.insertBefore(g, clone.querySelector('defs')?.nextSibling ?? clone.firstChild);
	const blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n', new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' });
	const a = document.createElement('a');
	a.href = URL.createObjectURL(blob);
	a.download = `${slug(title)}.svg`;
	a.click();
	window.setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function ProcessCard({
	process,
	number,
	size,
	onJump,
}: {
	process: WfProcess;
	number: string;
	size: Size;
	onJump?: (pointer: string) => void;
}) {
	const [open, setOpen] = useState(true);
	const svg = useRef<SVGSVGElement>(null);
	const title = `${number} ${process.title}`;
	const steps = process.nodes.filter((n) => n.kind === 'task').length;
	return (
		<section className="sw-proc" data-process={process.id}>
			<div className="sw-ph">
				<button type="button" className="sw-pill" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
					<Icon name="up" size={12} weight={2.4} className={cx('sw-chev', !open && 'shut')} />
					<span className="truncate">{title}</span>
				</button>
				<span className="sw-meta">
					{process.lanes.length} {process.lanes.length === 1 ? 'role' : 'roles'} · {steps} {steps === 1 ? 'step' : 'steps'}
				</span>
				{open && (
					<Button size="xs" variant="ghost" icon="file" className="ml-auto" onClick={() => svg.current && download(svg.current, title)}>
						Download SVG
					</Button>
				)}
			</div>
			{open && (
				<div className={cx('sw-canvas', size)}>
					<Swimlane ref={svg} process={process} onNode={onJump} />
				</div>
			)}
		</section>
	);
}

function Groups({
	processes,
	start,
	size,
	onJump,
}: {
	processes: WfProcess[];
	start: number;
	size: Size;
	onJump?: (pointer: string) => void;
}) {
	const groups = useMemo(() => {
		const out: Array<{ name: string; items: WfProcess[] }> = [];
		for (const p of processes) {
			const name = p.group || 'User journeys';
			const g = out.find((x) => x.name === name);
			if (g) g.items.push(p);
			else out.push({ name, items: [p] });
		}
		return out;
	}, [processes]);
	return (
		<>
			{groups.map((g, gi) => (
				<div key={g.name} className="sw-group">
					<h5 className="sw-gpill">
						{start + gi}. {g.name}
					</h5>
					{g.items.map((p, i) => (
						<ProcessCard
							key={p.id}
							process={p}
							number={`${start + gi}.${letter(i)}`}
							size={size}
							onJump={p.source === 'lifecycle' ? onJump : undefined}
						/>
					))}
				</div>
			))}
		</>
	);
}

export default function WorkflowsPanel({
	doc,
	agent,
	thinking,
	onJump,
}: {
	/** The parsed draft on screen; undefined while its YAML doesn't parse. */
	doc: unknown;
	agent: WfProcess[] | null | undefined;
	thinking?: boolean;
	onJump: (pointer: string) => void;
}) {
	// Keep the last good drawing while the YAML is mid-edit and doesn't parse.
	const last = useRef<WfProcess[]>([]);
	const derived = useMemo(() => {
		if (doc === undefined) return last.current;
		try {
			last.current = deriveWorkflows(doc);
		} catch {
			/* a half-typed journey: keep the last drawing */
		}
		return last.current;
	}, [doc]);
	const described = useMemo(() => (agent ?? []).map((p) => ({ ...p, source: 'agent' as const })), [agent]);
	const [size, setSize] = useState<Size>('fit');
	const derivedGroups = new Set(derived.map((p) => p.group || 'User journeys')).size;

	return (
		<div className="sw">
			<div className="sw-bar">
				<span className="text-[12.5px] text-t3">
					{derived.length} {derived.length === 1 ? 'lifecycle' : 'lifecycles'} · {described.length}{' '}
					{described.length === 1 ? 'user journey' : 'user journeys'}
				</span>
				<span className="ml-auto">
					<Segmented<Size>
						label="Diagram size"
						value={size}
						onChange={setSize}
						options={[
							{ value: 'fit', label: 'Fit' },
							{ value: 'actual', label: 'Actual size' },
						]}
					/>
				</span>
			</div>

			<div className="sw-sec">
				<div className="sw-sh">
					<h4>From the journey</h4>
					<span>How each record moves between states, and who moves it. Click a step to see it in the YAML.</span>
				</div>
				{derived.length ? (
					<Groups processes={derived} start={1} size={size} onJump={onJump} />
				) : (
					<EmptyState title="Workflows appear once the journey has lifecycles">
						A lifecycle is a record with states and steps — the patient, an enrolment, an order.
					</EmptyState>
				)}
			</div>

			<div className="sw-sec">
				<div className="sw-sh">
					<h4>Described by the agent</h4>
					<span>The user journeys the agent read in your material, step by step.</span>
				</div>
				{described.length ? (
					<Groups processes={described} start={derivedGroups + 1} size={size} />
				) : (
					<EmptyState title={thinking ? 'The agent is drafting…' : 'The agent adds user journeys when it drafts'}>
						They show who does what across roles, with the notifications between them.
					</EmptyState>
				)}
			</div>
		</div>
	);
}
