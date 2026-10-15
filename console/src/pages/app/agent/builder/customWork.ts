// How much of a generic (App Studio) spec the build writes by hand: custom pages, 360 tabs and
// panels, and custom requirements. The same count as agent_mode/custom_work.py, from the YAML on
// screen. Declared dashboards and views are not custom: the runtime builds them.

type Node = Record<string, unknown>;
const list = (v: unknown): Node[] => (Array.isArray(v) ? v.filter((x): x is Node => !!x && typeof x === 'object') : []);

export interface CustomWork {
	screens: number;
	requirements: number;
}

export function customWork(doc: unknown): CustomWork | null {
	if (!doc || typeof doc !== 'object') return null;
	const d = doc as Node;
	let screens = list(d.pages).filter((p) => p.type !== 'crud' && p.type !== 'detail' && p.type !== 'dashboard').length;
	let requirements = list((d.app as Node | undefined)?.custom_requirements).length;
	for (const dv of list(d.detail_views)) {
		for (const tab of list(dv.tabs)) {
			if (tab.type === 'custom') screens++;
			if (tab.type === 'summary' || tab.type === 'fields')
				screens += list(tab.sections).filter((s) => s.type === 'custom').length;
		}
		screens += list(dv.sidebar).filter((s) => s.type === 'custom').length;
		requirements += list(dv.custom_requirements).length;
	}
	for (const m of list(d.modules))
		for (const e of list(m.entities)) requirements += list(e.custom_requirements).length;
	return { screens, requirements };
}
