// Lifecycles in a journey, as swimlane processes. Pure and deterministic, so the Workflows tab
// redraws on every edit (the agent's, the YAML tab's, Journey Studio's).
//
// The convention (PSP SCHEMA.md "A lifecycle"): any object with a `steps:` list is a lifecycle.
//   states: [new: {start: true}, active, closed: {final: true}]   — codes or single-key maps
//   steps:  [{do, from (code | list), to, by (role | list), automatic, then: [actions]}]
// Each step is a task in its actor's lane; states are events between tasks (start, intermediate,
// end); notification-type actions in `then:` become dashed message flows.

import { joinPointer } from '../pointer';
import type { WfFlow, WfLane, WfNode, WfProcess } from './types';

type Obj = Record<string, unknown>;

const isObj = (v: unknown): v is Obj => !!v && typeof v === 'object' && !Array.isArray(v);
const list = (v: unknown): unknown[] => (Array.isArray(v) ? v : v == null || v === '' ? [] : [v]);

export function humanise(code: string): string {
	const s = String(code).replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim();
	return s ? s[0].toUpperCase() + s.slice(1) : s;
}

const SYSTEM = 'System';
const UNASSIGNED = 'Unassigned';
/** Actions that tell someone something: drawn as message flows. */
const MESSAGE_ACTION = /notif|sms|e-?mail|whatsapp|message|alert|send_|_send|remind|push/i;

interface StateInfo {
	code: string;
	start: boolean;
	final: boolean;
}

function parseStates(raw: unknown): StateInfo[] {
	const out: StateInfo[] = [];
	for (const item of list(raw)) {
		if (typeof item === 'string' || typeof item === 'number') {
			out.push({ code: String(item), start: false, final: false });
		} else if (isObj(item)) {
			const keys = Object.keys(item);
			if (keys.length === 1) {
				const opts = isObj(item[keys[0]]) ? (item[keys[0]] as Obj) : {};
				out.push({ code: keys[0], start: !!opts.start, final: !!opts.final });
			} else if (typeof item.code === 'string') {
				out.push({ code: item.code, start: !!item.start, final: !!item.final });
			}
		}
	}
	return out;
}

/** `then:` items are bare (`apply_scheme`) or single-key maps (`create_task: "Call"`). */
function parseActions(raw: unknown): Array<{ action: string; value: unknown }> {
	const out: Array<{ action: string; value: unknown }> = [];
	for (const item of list(raw)) {
		if (typeof item === 'string') out.push({ action: item, value: undefined });
		else if (isObj(item)) for (const [k, v] of Object.entries(item)) out.push({ action: k, value: v });
	}
	return out;
}

function messageLabel(action: string, value: unknown): string {
	if (typeof value === 'string' && value.trim()) return value.trim();
	if (isObj(value)) {
		for (const k of ['message', 'text', 'template', 'subject', 'title', 'to']) {
			const v = value[k];
			if (typeof v === 'string' && v.trim()) return `${humanise(action)}: ${v.trim()}`;
		}
	}
	return humanise(action);
}

function nameOf(v: unknown, fallback: string): string {
	if (isObj(v)) {
		if (typeof v.name === 'string' && v.name.trim()) return v.name.trim();
		if (typeof v.code === 'string' && v.code) return humanise(v.code);
	}
	return fallback;
}

/** Title and group for the lifecycle at `path` (segments from the root). */
function place(doc: unknown, path: Array<string | number>): { title: string; group: string } {
	const at = (n: number) => path.slice(0, n).reduce<unknown>((v, k) => (isObj(v) || Array.isArray(v) ? (v as Obj)[k as string] : undefined), doc);
	const [top] = path;
	if (top === 'patient' && path.length === 1) return { title: 'Patient lifecycle', group: 'Patient' };
	if (top === 'programs' && typeof path[1] === 'number') {
		const program = nameOf(at(2), `Program ${path[1] + 1}`);
		if (path[2] === 'enrolment' && path.length === 3)
			return { title: `${program}: enrolment`, group: program };
		if (path[2] === 'orders' && typeof path[3] === 'number' && path.length === 4)
			return { title: `${nameOf(at(4), `Order ${path[3] + 1}`)}: order`, group: program };
		return { title: `${program}: ${path.slice(2).filter((p) => typeof p === 'string').map(String).map(humanise).join(' › ')}`, group: program };
	}
	if (top === 'documents' && path.length === 1) return { title: 'Documents', group: 'Documents' };
	if (top === 'masters' && typeof path[1] === 'number')
		return { title: nameOf(at(2), `Reference list ${path[1] + 1}`), group: 'Reference lists' };
	if (top === 'adverse_events' && path.length === 1)
		return { title: 'Adverse events', group: 'Adverse events' };
	const named = nameOf(at(path.length), '');
	return {
		title: named || path.filter((p) => typeof p === 'string').map(String).map(humanise).join(' › ') || 'Lifecycle',
		group: humanise(String(top ?? 'Journey')),
	};
}

function* lifecycles(node: unknown, path: Array<string | number> = []): Generator<{ obj: Obj; path: Array<string | number> }> {
	if (Array.isArray(node)) {
		for (let i = 0; i < node.length; i++) yield* lifecycles(node[i], [...path, i]);
		return;
	}
	if (!isObj(node)) return;
	if (Array.isArray(node.steps) && node.steps.length) yield { obj: node, path };
	for (const [k, v] of Object.entries(node)) {
		if (k === 'steps' || k === 'states') continue;
		yield* lifecycles(v, [...path, k]);
	}
}

/** Where a lifecycle's parts live in the spec, when it isn't PSP's `states`/`steps` shape. */
interface Shape {
	title: string;
	group: string;
	step: (i: number) => string;
	action: (i: number, j: number) => string;
	state: (i: number) => string;
}

/** One lifecycle as a process. `null` when it has no usable step. */
export function processFor(
	obj: Obj,
	path: Array<string | number>,
	doc: unknown,
	shape?: Shape,
): WfProcess | null {
	const base = joinPointer(path);
	const stepAt = shape?.step ?? ((i: number) => `${base}/steps/${i}`);
	const actionAt = shape?.action ?? ((i: number, j: number) => `${base}/steps/${i}/then/${j}`);
	const stateAt = shape?.state ?? ((i: number) => `${base}/states/${i}`);
	const steps = (obj.steps as unknown[]).filter(isObj);
	if (!steps.length) return null;

	const declared = parseStates(obj.states);
	const info = new Map(declared.map((s) => [s.code, s]));
	const lanes: WfLane[] = [];
	const laneOf = (role: string) => {
		let lane = lanes.find((l) => l.role === role);
		if (!lane) {
			lane = { id: `lane:${role}`, role };
			lanes.push(lane);
		}
		return lane.id;
	};

	const actorOf = (step: Obj) => {
		const roles = list(step.by).map(String).filter(Boolean);
		if (step.automatic || step.auto) return { role: SYSTEM, also: roles };
		if (!roles.length) return { role: UNASSIGNED, also: [] };
		return { role: roles[0], also: roles.slice(1) };
	};

	// Step indices in the source list (steps that aren't maps are skipped but keep numbering).
	const all = obj.steps as unknown[];
	const tasks: WfNode[] = [];
	const flows: WfFlow[] = [];
	const messages: WfNode[] = [];
	const incomingLane = new Map<string, string>();
	const outgoingLane = new Map<string, string>();
	const touched: string[] = [];
	const touch = (code: string) => {
		if (!touched.includes(code)) touched.push(code);
	};

	all.forEach((step, i) => {
		if (!isObj(step)) return;
		const actor = actorOf(step);
		const lane = laneOf(actor.role);
		const id = `t:${i}`;
		tasks.push({
			id,
			lane,
			kind: 'task',
			label: String(step.do ?? '').trim() || `Step ${i + 1}`,
			note: actor.also.length ? `${actor.role === SYSTEM ? 'Automatic' : 'or'} ${actor.also.join(', ')}` : step.automatic || step.auto ? 'Automatic' : undefined,
			pointer: stepAt(i),
		});
		for (const from of list(step.from).map(String)) {
			touch(from);
			flows.push({ from: `s:${from}`, to: id, kind: 'sequence' });
			if (!outgoingLane.has(from)) outgoingLane.set(from, lane);
		}
		if (step.to != null && step.to !== '') {
			const to = String(step.to);
			touch(to);
			flows.push({ from: id, to: `s:${to}`, kind: 'sequence' });
			if (!incomingLane.has(to)) incomingLane.set(to, lane);
		}
		parseActions(step.then).forEach(({ action, value }, j) => {
			if (!MESSAGE_ACTION.test(action)) return;
			const mid = `m:${i}:${j}`;
			messages.push({ id: mid, lane, kind: 'message', label: messageLabel(action, value), pointer: actionAt(i, j) });
			flows.push({ from: id, to: mid, kind: 'message' });
		});
	});

	// The start state: the one marked, else the first declared, else the first step's `from`.
	const startCode = declared.find((s) => s.start)?.code ?? declared[0]?.code ?? touched[0];
	if (startCode) touch(startCode);
	// Declared order first, then states only steps mention.
	const codes = [...declared.map((s) => s.code).filter((c) => touched.includes(c)), ...touched.filter((c) => !info.has(c))];
	const hasOut = new Set(flows.filter((f) => f.kind === 'sequence' && f.from.startsWith('s:')).map((f) => f.from.slice(2)));

	const states: WfNode[] = codes.map((code) => {
		const s = info.get(code);
		const kind = code === startCode ? 'start' : s?.final || !hasOut.has(code) ? 'end' : 'event';
		const lane =
			kind === 'start'
				? (outgoingLane.get(code) ?? incomingLane.get(code))
				: (incomingLane.get(code) ?? outgoingLane.get(code));
		const idx = declared.findIndex((d) => d.code === code);
		return {
			id: `s:${code}`,
			lane: lane ?? laneOf(UNASSIGNED),
			kind,
			label: humanise(code),
			note: humanise(code),
			pointer: idx >= 0 ? stateAt(idx) : undefined,
		};
	});

	// Things the record tells someone outside its steps: on_create/on_enrol/on_raise, notify_client.
	const start = states.find((s) => s.kind === 'start');
	if (start) {
		for (const key of Object.keys(obj).filter((k) => /^on_/.test(k) && Array.isArray(obj[k]))) {
			parseActions(obj[key]).forEach(({ action, value }, j) => {
				if (!MESSAGE_ACTION.test(action)) return;
				const mid = `m:${key}:${j}`;
				messages.push({ id: mid, lane: start.lane, kind: 'message', label: messageLabel(action, value), pointer: `${base}/${key}/${j}` });
				flows.push({ from: start.id, to: mid, kind: 'message' });
			});
		}
		if (isObj(obj.notify_client)) {
			const n = obj.notify_client;
			const mid = 'm:notify_client';
			messages.push({
				id: mid,
				lane: start.lane,
				kind: 'message',
				label: `Notify client${n.on ? ` (${humanise(String(n.on))})` : ''}`,
				note: list(n.to).map(String).join(', ') || undefined,
				pointer: `${base}/notify_client`,
			});
			flows.push({ from: start.id, to: mid, kind: 'message' });
		}
	}

	const { title, group } = shape ?? place(doc, path);
	return {
		id: `lc:${base || '/'}`,
		title,
		group,
		source: 'lifecycle',
		lanes,
		nodes: [...states, ...tasks, ...messages],
		flows,
		pointer: base,
	};
}

// --- Zango app spec v1 ('zango-app/1') ------------------------------------------------------
//
//   modules: [{code, name, entities: [{code, name, workflow: {statuses, transitions}}]}]
//   statuses:    [{code, label, initial?, final?}]
//   transitions: [{name, label, from (code | list), to, roles: [...], trigger: system?, on_done?}]
// Mapped onto the same states/steps shape: a transition is a task in its first role's lane,
// `trigger: system` is the System lane, and an `on_done` that tells someone is a message flow.

export const ZANGO_APP_DIALECT = 'zango-app/1';

const TELLS = /\b(e-?mail|sms|whatsapp|notif\w*|push)\b/i;

function tellLabel(text: string): string {
	const m = TELLS.exec(text)?.[1].toLowerCase() ?? '';
	if (m.startsWith('e')) return 'Email';
	if (m === 'sms') return 'SMS';
	if (m === 'whatsapp') return 'WhatsApp';
	return 'Notification';
}

export function isZangoAppSpec(doc: unknown): boolean {
	return isObj(doc) && Array.isArray(doc.modules) && ('spec_version' in doc || isObj(doc.app));
}

function zangoAppWorkflows(doc: Obj): WfProcess[] {
	const out: WfProcess[] = [];
	list(doc.modules).forEach((mod, mi) => {
		if (!isObj(mod)) return;
		const group = nameOf(mod, `Module ${mi + 1}`);
		list(mod.entities).forEach((ent, ei) => {
			if (!isObj(ent) || !isObj(ent.workflow)) return;
			const wf = ent.workflow as Obj;
			const transitions = list(wf.transitions);
			if (!transitions.some(isObj)) return;
			const path = ['modules', mi, 'entities', ei, 'workflow'];
			const base = joinPointer(path);
			const states = list(wf.statuses).map((st) =>
				isObj(st) && st.code != null
					? { [String(st.code)]: { start: !!st.initial, final: !!st.final } }
					: st,
			);
			const steps = transitions.map((t) => {
				if (!isObj(t)) return t;
				const tells = [t.on_done, t.text, t.confirm]
					.filter((v): v is string => typeof v === 'string' && TELLS.test(v))
					.slice(0, 1)
					.map((v) => ({ notify: `${tellLabel(v)} notification` }));
				return {
					do: String(t.label ?? '').trim() || humanise(String(t.name ?? '')),
					from: t.from,
					to: t.to,
					by: t.roles,
					automatic: t.trigger === 'system',
					then: tells,
				};
			});
			const name = nameOf(ent, `Entity ${ei + 1}`);
			const p = processFor({ states, steps }, path, doc, {
				title: `${name} lifecycle`,
				group,
				step: (i) => `${base}/transitions/${i}`,
				action: (i) => {
					const t = transitions[i];
					const key = isObj(t) ? ['on_done', 'text', 'confirm'].find((k) => typeof t[k] === 'string' && TELLS.test(t[k] as string)) : undefined;
					return `${base}/transitions/${i}${key ? `/${key}` : ''}`;
				},
				state: (i) => `${base}/statuses/${i}`,
			});
			if (p) out.push(p);
		});
	});
	return out;
}

/** Every lifecycle in the spec, in document order. `dialect` picks the spec's vocabulary. */
export function deriveWorkflows(doc: unknown, dialect?: string): WfProcess[] {
	if (dialect === ZANGO_APP_DIALECT || (!dialect && isZangoAppSpec(doc)))
		return isObj(doc) ? zangoAppWorkflows(doc) : [];
	const out: WfProcess[] = [];
	for (const { obj, path } of lifecycles(doc)) {
		const p = processFor(obj, path, doc);
		if (p) out.push(p);
	}
	return out;
}
