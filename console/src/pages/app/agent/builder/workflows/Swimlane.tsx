// One process as a BPMN-style swimlane, in SVG. Presentation is in attributes rather than CSS
// so a downloaded SVG looks the same as the one on screen.

import { forwardRef, useId, useMemo, type KeyboardEvent } from 'react';
import { G, layout, wrap, type Layout, type PlacedEdge, type PlacedNode } from './layout';
import type { WfProcess } from './types';

const C = {
	lane: '#b8b8b8',
	laneFill: '#fbfbfb',
	head: '#e3e3e3',
	role: '#3d3d3d',
	task: '#e2e2e2',
	text: '#2e2e2e',
	ring: '#8a8a8a',
	hollow: '#f6f6f6',
	end: '#686868',
	endRing: '#454545',
	line: '#6b6b6b',
	note: '#7b7b7b',
};
const FONT = 'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif';

function Lines({ lines, x, y, size, color, weight, lh }: { lines: string[]; x: number; y: number; size: number; color: string; weight?: number; lh: number }) {
	return (
		<text x={x} y={y} fontSize={size} fill={color} fontWeight={weight} textAnchor="middle" fontFamily={FONT}>
			{lines.map((l, i) => (
				<tspan key={i} x={x} dy={i ? lh : 0}>
					{l}
				</tspan>
			))}
		</text>
	);
}

function Envelope({ x, y }: { x: number; y: number }) {
	return (
		<g transform={`translate(${x - 9} ${y - 6})`}>
			<rect width={18} height={12} rx={1.5} fill="#fff" stroke={C.line} strokeWidth={1.1} />
			<path d="M0.6 0.8 L9 7 L17.4 0.8" fill="none" stroke={C.line} strokeWidth={1.1} />
		</g>
	);
}

function Shape({ n }: { n: PlacedNode }) {
	const r = G.eventR;
	switch (n.kind) {
		case 'task':
			return (
				<>
					<rect x={n.x - n.w / 2} y={n.y - n.h / 2} width={n.w} height={n.h} rx={8} fill={C.task} />
					{(() => {
						const lines = wrap(n.label, 19, 3);
						return <Lines lines={lines} x={n.x} y={n.y + 4 - ((lines.length - 1) * 14) / 2} size={11.5} color={C.text} lh={14} />;
					})()}
				</>
			);
		case 'start':
			return <circle cx={n.x} cy={n.y} r={r} fill={C.hollow} stroke={C.ring} strokeWidth={1.6} />;
		case 'end':
			return <circle cx={n.x} cy={n.y} r={r - 1} fill={C.end} stroke={C.endRing} strokeWidth={3} />;
		case 'gateway':
			return (
				<path
					d={`M${n.x} ${n.y - 19} L${n.x + 19} ${n.y} L${n.x} ${n.y + 19} L${n.x - 19} ${n.y} Z`}
					fill={C.hollow}
					stroke={C.ring}
					strokeWidth={1.6}
				/>
			);
		case 'message':
			return (
				<>
					<circle cx={n.x} cy={n.y} r={r} fill={C.hollow} stroke={C.ring} strokeWidth={1.6} />
					<circle cx={n.x} cy={n.y} r={r - 3.5} fill="none" stroke={C.ring} strokeWidth={1.2} />
					<Envelope x={n.x} y={n.y} />
				</>
			);
		default:
			return (
				<>
					<circle cx={n.x} cy={n.y} r={r} fill={C.hollow} stroke={C.ring} strokeWidth={1.6} />
					<circle cx={n.x} cy={n.y} r={r - 3.5} fill="none" stroke={C.ring} strokeWidth={1.2} />
				</>
			);
	}
}

/** The grey words under an event: its note, else (messages, gateways) its label. */
function annotation(n: PlacedNode): string {
	if (n.kind === 'task') return n.note ?? '';
	if (n.kind === 'message' || n.kind === 'gateway') return n.note ? `${n.label} — ${n.note}` : n.label;
	return n.note ?? n.label;
}

function Edge({ e, arrow, dot }: { e: PlacedEdge; arrow: string; dot: string }) {
	const message = e.flow.kind === 'message';
	const d = e.points.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${y}`).join(' ');
	const label = e.flow.label ? wrap(e.flow.label, 24, 3) : [];
	const [mx, my] = e.mid;
	return (
		<g data-flow={`${e.flow.from}->${e.flow.to}`}>
			<path
				d={d}
				fill="none"
				stroke={C.line}
				strokeWidth={1.3}
				strokeDasharray={message ? '4 3' : undefined}
				markerEnd={`url(#${arrow})`}
				markerStart={message ? `url(#${dot})` : undefined}
			/>
			{message && label.length > 0 && <Envelope x={mx} y={my} />}
			{label.length > 0 &&
				(e.vertical ? (
					<text x={mx + 16} y={my + 4 - ((label.length - 1) * 13) / 2} fontSize={11} fill={C.note} fontFamily={FONT}>
						{label.map((l, i) => (
							<tspan key={i} x={mx + 16} dy={i ? 13 : 0}>
								{l}
							</tspan>
						))}
					</text>
				) : (
					<Lines lines={label} x={mx} y={my + (message ? 22 : -8)} size={11} color={C.note} lh={13} />
				))}
		</g>
	);
}

export interface SwimlaneProps {
	process: WfProcess;
	/** Show a node's place in the journey (derived nodes carry a pointer). */
	onNode?: (pointer: string) => void;
}

export const Swimlane = forwardRef<SVGSVGElement, SwimlaneProps>(function Swimlane({ process, onNode }, ref) {
	const L: Layout = useMemo(() => layout(process), [process]);
	const uid = useId().replace(/[^a-zA-Z0-9_-]/g, '');
	const arrow = `sw-a-${uid}`;
	const dot = `sw-d-${uid}`;
	const titleId = `sw-t-${uid}`;
	const pad = 1;
	const W = Math.ceil(L.width) + pad * 2;
	const H = Math.ceil(L.height) + pad * 2;

	// A flow leaving or entering a shape through its bottom would run through a note under it,
	// so those notes move to the shape's lower right.
	const bottomHooked = useMemo(() => {
		const out = new Set<string>();
		for (const e of L.edges) {
			const [x1, y1] = e.points[0];
			const [x2, y2] = e.points[e.points.length - 1];
			const s = L.nodes.find((n) => n.id === e.flow.from);
			const t = L.nodes.find((n) => n.id === e.flow.to);
			if (s && Math.abs(x1 - s.x) < 1 && y1 > s.y) out.add(s.id);
			if (t && Math.abs(x2 - t.x) < 1 && y2 > t.y) out.add(t.id);
		}
		return out;
	}, [L]);

	const activate = (n: PlacedNode) => n.pointer && onNode?.(n.pointer);
	const onKey = (e: KeyboardEvent, n: PlacedNode) => {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			activate(n);
		}
	};

	return (
		<svg
			ref={ref}
			xmlns="http://www.w3.org/2000/svg"
			className="sw-svg"
			viewBox={`${-pad} ${-pad} ${W} ${H}`}
			width={W}
			height={H}
			style={{ maxWidth: W, minWidth: Math.min(W, Math.max(640, W * 0.7)) }}
			role="img"
			aria-labelledby={titleId}
			fontFamily={FONT}
		>
			<title id={titleId}>
				{process.title}: {process.lanes.map((l) => l.role).join(', ')}
			</title>
			<defs>
				<marker id={arrow} viewBox="0 0 10 10" refX={9} refY={5} markerWidth={8} markerHeight={8} orient="auto-start-reverse">
					<path d="M0 0.8 L10 5 L0 9.2 Z" fill={C.line} />
				</marker>
				<marker id={dot} viewBox="0 0 10 10" refX={5} refY={5} markerWidth={6} markerHeight={6}>
					<circle cx={5} cy={5} r={4} fill={C.line} />
				</marker>
			</defs>
			{L.lanes.map((lane) => {
				const cy = lane.y + lane.h / 2;
				const cx = G.header / 2;
				return (
					<g key={lane.id} data-lane={lane.role}>
						<rect x={0} y={lane.y} width={L.width} height={lane.h} rx={8} fill={C.laneFill} stroke={C.lane} strokeWidth={1.2} />
						<path
							d={`M${G.header} ${lane.y} H8 Q0 ${lane.y} 0 ${lane.y + 8} V${lane.y + lane.h - 8} Q0 ${lane.y + lane.h} 8 ${lane.y + lane.h} H${G.header} Z`}
							fill={C.head}
							stroke={C.lane}
							strokeWidth={1.2}
						/>
						<text
							x={cx}
							y={cy}
							transform={`rotate(-90 ${cx} ${cy})`}
							textAnchor="middle"
							dominantBaseline="central"
							fontSize={12.5}
							fontWeight={700}
							fill={C.role}
						>
							{lane.role.length > 32 ? lane.role.slice(0, 31) + '…' : lane.role}
						</text>
					</g>
				);
			})}
			{L.edges.map((e, i) => (
				<Edge key={i} e={e} arrow={arrow} dot={dot} />
			))}
			{L.nodes.map((n) => {
				const note = annotation(n);
				const lines = note ? wrap(note, 22, 3) : [];
				const below = n.y + n.h / 2 + (n.kind === 'task' ? 14 : 15);
				const aside = bottomHooked.has(n.id) && n.kind !== 'task';
				const hit = !!(n.pointer && onNode && n.kind === 'task');
				return (
					<g
						key={n.id}
						data-node={n.id}
						className={hit ? 'sw-hit' : undefined}
						role={hit ? 'button' : undefined}
						tabIndex={hit ? 0 : undefined}
						aria-label={hit ? `${n.label} — show in YAML` : undefined}
						onClick={hit ? () => activate(n) : undefined}
						onKeyDown={hit ? (e) => onKey(e, n) : undefined}
					>
						<title>{n.kind === 'task' ? n.label : annotation(n) || n.label}</title>
						<Shape n={n} />
						{lines.length > 0 &&
							(aside ? (
								<text x={n.x + n.w / 2 + 8} y={n.y + n.h / 2 + 8} fontSize={11} fill={C.note} fontFamily={FONT}>
									{lines.map((l, i) => (
										<tspan key={i} x={n.x + n.w / 2 + 8} dy={i ? 13 : 0}>
											{l}
										</tspan>
									))}
								</text>
							) : (
								<Lines lines={lines} x={n.x} y={below} size={11} color={C.note} lh={13} />
							))}
					</g>
				);
			})}
		</svg>
	);
});
