// Deterministic left-to-right swimlane layout. Pure: the same process always lands the same way.
//
//   columns — longest path from the start over the flows, cycles broken by a DFS (a step back
//             to an earlier state is drawn as a return arrow over the top, not a column);
//             a message to another lane keeps its column, so it drops straight down
//   rows    — one band per lane; nodes that share a lane and a column stack inside it, a node
//             preferring its predecessor's row so the main path stays straight
//   edges   — orthogonal: straight when level, else a bend in the gap between columns

import type { WfFlow, WfLane, WfNode, WfProcess } from './types';

export const G = {
	header: 30, // the lane's role strip
	padLeft: 22,
	padRight: 26,
	laneGap: 14,
	messageGap: 66, // between lanes a labelled message crosses: room for its envelope and words
	padY: 16, // above the first row and below the last
	rowH: 110,
	shapeY: 42, // a shape's centre, from the top of its row
	colGap: 56,
	taskW: 128,
	taskH: 56,
	eventR: 17,
	noteW: 132,
};

export interface PlacedNode extends WfNode {
	x: number;
	y: number;
	w: number;
	h: number;
	rank: number;
	row: number;
}
export interface PlacedLane extends WfLane {
	y: number;
	h: number;
}
export interface PlacedEdge {
	flow: WfFlow;
	points: Array<[number, number]>;
	/** Where an envelope and label go: the middle of the longest segment. */
	mid: [number, number];
	vertical: boolean;
	back: boolean;
}
export interface Layout {
	width: number;
	height: number;
	lanes: PlacedLane[];
	nodes: PlacedNode[];
	edges: PlacedEdge[];
	/** Flows that name a node the process doesn't have. */
	dropped: number;
}

const annotated = (n: WfNode) => n.kind !== 'task';
function size(n: WfNode): { w: number; h: number } {
	if (n.kind === 'task') return { w: G.taskW, h: G.taskH };
	if (n.kind === 'gateway') return { w: 38, h: 38 };
	return { w: G.eventR * 2, h: G.eventR * 2 };
}

/** Words into at most `lines` lines of `chars` characters, the last one ellipsised. */
export function wrap(text: string, chars: number, lines = 3): string[] {
	const words = String(text ?? '').split(/\s+/).filter(Boolean);
	const out: string[] = [];
	let cur = '';
	for (let i = 0; i < words.length; i++) {
		let w = words[i];
		while (w.length > chars) {
			if (cur) {
				out.push(cur);
				cur = '';
			}
			out.push(w.slice(0, chars - 1) + '-');
			w = w.slice(chars - 1);
		}
		const next = cur ? `${cur} ${w}` : w;
		if (next.length > chars && cur) {
			out.push(cur);
			cur = w;
		} else cur = next;
	}
	if (cur) out.push(cur);
	if (out.length > lines) {
		const kept = out.slice(0, lines);
		const last = kept[lines - 1];
		kept[lines - 1] = (last.length >= chars ? last.slice(0, chars - 1) : last) + '…';
		return kept;
	}
	return out;
}

export function layout(process: WfProcess): Layout {
	// Lanes: declared ones, then any a node names that wasn't declared.
	const lanes: WfLane[] = [...process.lanes];
	for (const n of process.nodes)
		if (!lanes.some((l) => l.id === n.lane)) lanes.push({ id: n.lane, role: n.lane });
	const laneIdx = new Map(lanes.map((l, i) => [l.id, i]));

	const nodes = process.nodes.filter((n, i, all) => all.findIndex((m) => m.id === n.id) === i);
	const byId = new Map(nodes.map((n) => [n.id, n]));
	const flows = process.flows.filter((f) => byId.has(f.from) && byId.has(f.to) && f.from !== f.to);
	const dropped = process.flows.length - flows.length;
	const weight = (f: WfFlow) =>
		f.kind === 'message' && byId.get(f.from)!.lane !== byId.get(f.to)!.lane ? 0 : 1;

	const out = new Map<string, WfFlow[]>();
	const inDeg = new Map<string, number>(nodes.map((n) => [n.id, 0]));
	for (const f of flows) {
		out.set(f.from, [...(out.get(f.from) ?? []), f]);
		inDeg.set(f.to, (inDeg.get(f.to) ?? 0) + 1);
	}

	// Break cycles: DFS from the starts (then sources, then whatever is left), in node order.
	const back = new Set<WfFlow>();
	const state = new Map<string, 1 | 2>();
	const discovery: string[] = [];
	const visit = (id: string) => {
		state.set(id, 1);
		discovery.push(id);
		for (const f of out.get(id) ?? []) {
			const s = state.get(f.to);
			if (s === 1) back.add(f);
			else if (!s) visit(f.to);
		}
		state.set(id, 2);
	};
	const roots = [
		...nodes.filter((n) => n.kind === 'start'),
		...nodes.filter((n) => n.kind !== 'start' && !inDeg.get(n.id)),
		...nodes,
	];
	for (const n of roots) if (!state.has(n.id)) visit(n.id);
	const order = new Map(discovery.map((id, i) => [id, i]));

	// Longest path over what's left (Kahn's order).
	const rank = new Map<string, number>(nodes.map((n) => [n.id, 0]));
	const fwd = flows.filter((f) => !back.has(f));
	const deg = new Map<string, number>(nodes.map((n) => [n.id, 0]));
	for (const f of fwd) deg.set(f.to, deg.get(f.to)! + 1);
	const queue = nodes.filter((n) => !deg.get(n.id)).map((n) => n.id);
	queue.sort((a, b) => order.get(a)! - order.get(b)!);
	while (queue.length) {
		const id = queue.shift()!;
		for (const f of fwd.filter((g) => g.from === id)) {
			rank.set(f.to, Math.max(rank.get(f.to)!, rank.get(id)! + weight(f)));
			deg.set(f.to, deg.get(f.to)! - 1);
			if (!deg.get(f.to)) queue.push(f.to);
		}
	}

	// Rows inside each lane.
	const row = new Map<string, number>();
	const taken = new Set<string>();
	const sorted = [...nodes].sort(
		(a, b) => rank.get(a.id)! - rank.get(b.id)! || order.get(a.id)! - order.get(b.id)!,
	);
	for (const n of sorted) {
		const pred = fwd.find((f) => f.to === n.id && byId.get(f.from)!.lane === n.lane && row.has(f.from));
		let r = pred ? row.get(pred.from)! : 0;
		while (taken.has(`${n.lane}|${rank.get(n.id)}|${r}`)) r++;
		taken.add(`${n.lane}|${rank.get(n.id)}|${r}`);
		row.set(n.id, r);
	}

	// Columns: as wide as their widest shape or annotation.
	const ranks = Math.max(0, ...nodes.map((n) => rank.get(n.id)!)) + 1;
	const colW = Array.from({ length: ranks }, (_, c) => {
		const inCol = nodes.filter((n) => rank.get(n.id) === c);
		return Math.max(48, ...inCol.map((n) => Math.max(size(n).w, annotated(n) ? G.noteW : 0))) + G.colGap;
	});
	// A labelled flow into the next column needs room for its words between the two.
	const extra = Array.from({ length: ranks }, () => 0);
	for (const f of flows) {
		const rs = rank.get(f.from)!;
		const rt = rank.get(f.to)!;
		if (f.label && rt === rs + 1 && byId.get(f.from)!.lane === byId.get(f.to)!.lane)
			extra[rt] = Math.max(extra[rt], Math.min(24, f.label.length) * 6 + 24 - G.colGap);
	}
	const colX: number[] = [];
	let x = G.header + G.padLeft;
	colW.forEach((w, c) => {
		x += extra[c];
		colX.push(x + w / 2);
		x += w;
	});
	const colRight = (c: number) => colX[c] + colW[c] / 2;
	const width = x + G.padRight;

	// Lanes stacked top to bottom, each tall enough for its role written down the strip; the
	// rows sit in the middle of a lane that's taller than they need.
	const crossings = new Set<number>();
	for (const f of flows) {
		if (f.kind !== 'message' || !f.label) continue;
		const [a, b] = [laneIdx.get(byId.get(f.from)!.lane)!, laneIdx.get(byId.get(f.to)!.lane)!].sort((p, q) => p - q);
		for (let i = a; i < b; i++) crossings.add(i);
	}
	const placedLanes: PlacedLane[] = [];
	const inset = new Map<string, number>();
	let y = 0;
	lanes.forEach((lane, i) => {
		const rows = Math.max(1, ...nodes.filter((n) => n.lane === lane.id).map((n) => row.get(n.id)! + 1));
		const need = G.padY * 2 + rows * G.rowH - 14;
		const h = Math.max(need, Math.min(lane.role.length, 32) * 7.4 + 28);
		inset.set(lane.id, (h - need) / 2);
		placedLanes.push({ ...lane, y, h });
		y += h + (i < lanes.length - 1 ? (crossings.has(i) ? G.messageGap : G.laneGap) : 0);
	});
	const height = Math.max(0, y);
	const laneTop = (id: string) => placedLanes[laneIdx.get(id)!].y + inset.get(id)!;

	const placed: PlacedNode[] = nodes.map((n) => {
		const { w, h } = size(n);
		const r = row.get(n.id)!;
		return {
			...n,
			w,
			h,
			rank: rank.get(n.id)!,
			row: r,
			x: colX[rank.get(n.id)!],
			y: laneTop(n.lane) + G.padY + r * G.rowH + G.shapeY,
		};
	});
	const at = new Map(placed.map((n) => [n.id, n]));

	let backs = 0;
	const edges: PlacedEdge[] = flows.map((flow) => {
		const s = at.get(flow.from)!;
		const t = at.get(flow.to)!;
		let points: Array<[number, number]>;
		const isBack = back.has(flow) || t.rank < s.rank || (t.rank === s.rank && weight(flow) === 1);
		if (t.rank === s.rank && !isBack) {
			// Same column, another lane: straight down (or up).
			const down = t.y > s.y;
			points = [
				[s.x, s.y + (down ? s.h / 2 : -s.h / 2)],
				[t.x, t.y + (down ? -t.h / 2 : t.h / 2)],
			];
		} else if (!isBack) {
			const a: [number, number] = [s.x + s.w / 2, s.y];
			const b: [number, number] = [t.x - t.w / 2, t.y];
			if (Math.abs(a[1] - b[1]) < 1) points = [a, b];
			else {
				const bx = t.rank === s.rank + 1 ? colRight(s.rank) : Math.min(colRight(s.rank), b[0] - 14);
				points = [a, [bx, a[1]], [bx, b[1]], b];
			}
		} else {
			// Back to an earlier column: up out of the source, along the top of the row, down in.
			const top = Math.min(s.y - s.h / 2, t.y - t.h / 2);
			const yb = Math.min(
				laneTop(s.lane) + G.padY + s.row * G.rowH,
				laneTop(t.lane) + G.padY + t.row * G.rowH,
			) + 2 - (backs++ % 4) * 4;
			const lift = Math.min(yb, top - 8);
			points = [
				[s.x, s.y - s.h / 2],
				[s.x, lift],
				[t.x, lift],
				[t.x, t.y - t.h / 2],
			];
		}
		let best = 0;
		let mid: [number, number] = points[0];
		let vertical = false;
		for (let i = 1; i < points.length; i++) {
			const [x1, y1] = points[i - 1];
			const [x2, y2] = points[i];
			const len = Math.abs(x2 - x1) + Math.abs(y2 - y1);
			if (len > best) {
				best = len;
				mid = [(x1 + x2) / 2, (y1 + y2) / 2];
				vertical = Math.abs(x2 - x1) < 1;
			}
		}
		return { flow, points, mid, vertical, back: isBack };
	});

	return { width, height, lanes: placedLanes, nodes: placed, edges, dropped };
}
