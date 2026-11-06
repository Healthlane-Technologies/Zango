import { Link } from 'react-router-dom';
import { Icon } from '@/ui';

// The spec's `ai.agents` in plain words for the review tab: one sentence per helper, and where
// the AI account gets connected (never in the chat; the key goes into the console).

type Node = Record<string, unknown>;
const list = (v: unknown): Node[] =>
	Array.isArray(v) ? v.filter((x): x is Node => !!x && typeof x === 'object') : [];
const str = (v: unknown) => (typeof v === 'string' ? v : '');

const WHEN: Record<string, (t: Node) => string> = {
	create: () => 'when a record is added',
	update: (t) =>
		Array.isArray(t.fields) && t.fields.length
			? `when ${t.fields.join(', ')} changes`
			: 'when a record changes',
	delete: () => 'when a record is removed',
	transition: (t) => `after “${str(t.transition)}”`,
	tag: (t) => `when tagged “${str(t.tag)}”`,
	schedule: (t) => `on a schedule (${str(t.cron)})`,
	button: (t) =>
		`from a “${str(t.label) || 'AI'}” button ${
			{ row: 'in each list row', list: 'on the list', form: 'in the form' }[str(t.where)] ??
			'on the record'
		}`,
	form_assist: (t) => `from “${str(t.label) || 'Fill from document'}” in the form`,
	chat: (t) => `as an “Ask AI” chat ${str(t.where) === 'list' ? 'on the list' : 'on the record'}`,
	task: () => 'from the app’s own background logic',
};

const REVIEW: Record<string, string> = {
	suggest: 'a person confirms it first',
	none: 'applied straight away',
	show: 'shown only',
};

export function aiAgents(doc: unknown): Node[] {
	const ai = doc && typeof doc === 'object' ? (doc as Node).ai : null;
	return ai && typeof ai === 'object' ? list((ai as Node).agents) : [];
}

export function AiHelpers({ appId, doc }: { appId: string; doc: unknown }) {
	const agents = aiAgents(doc);
	if (!agents.length) return null;
	return (
		<section className="rv-sec">
			<div className="rv-h">
				<h4>Help from AI</h4>
				<span className="ct">{agents.length}</span>
			</div>
			<ul className="rv-ai">
				{agents.map((a) => {
					const when = list(a.triggers)
						.map((t) => WHEN[str(t.event)]?.(t))
						.filter(Boolean)
						.join(', ');
					return (
						<li key={str(a.code)}>
							<Icon name="bot" size={13} />
							<div>
								<b>{str(a.name) || str(a.code)}</b> {str(a.purpose)}
								<small>
									{[when && `Runs ${when}`, REVIEW[str(a.review) || 'suggest']]
										.filter(Boolean)
										.join(' · ')}
								</small>
							</div>
						</li>
					);
				})}
			</ul>
			<p className="rv-ai-note">
				These need an AI account. The build sets them up either way; you add the key in{' '}
				<Link to={`/apps/${appId}/ai?tab=providers`}>App → AI</Link> now or later, and they start
				working without a rebuild.
			</p>
		</section>
	);
}
