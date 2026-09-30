import type { TemplateSummary } from '@/api/templates';
import { Badge, Icon } from '@/ui';
import { categoryStyle, highlight, templateIcon } from './catalog';
import './templates.css';

/** The coloured category tile (prototype `vic`). */
export function TemplateIcon({
	template,
	size = 32,
}: {
	template: Pick<TemplateSummary, 'icon' | 'category'>;
	size?: number;
}) {
	const { bg, fg } = categoryStyle(template.category);
	return (
		<span
			className="vic"
			style={{ background: bg, color: fg, width: size, height: size, borderRadius: size / 4 }}
		>
			<Icon name={templateIcon(template)} size={Math.round(size / 2)} />
		</span>
	);
}

export function BetaBadge() {
	return (
		<Badge tone="violet" className="tb">
			Beta
		</Badge>
	);
}

/** `text` with the search words wrapped in <mark>. */
export function Highlighted({ text, q }: { text: string; q: string }) {
	return (
		<>
			{highlight(text, q).map(([part, hit], i) =>
				hit ? <mark key={i}>{part}</mark> : <span key={i}>{part}</span>,
			)}
		</>
	);
}

export function AgentsTag({ count }: { count: number }) {
	if (!count) return null;
	return (
		<span className="tag-ai" title={`${count} AI agent${count > 1 ? 's' : ''} recommended`}>
			<Icon name="bot" size={13} />
			{count}
		</span>
	);
}
