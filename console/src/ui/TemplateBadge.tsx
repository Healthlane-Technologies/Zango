import { Link } from 'react-router-dom';
import { Icon } from './Icon';

/** The template an app or requirement is built on: name + pinned version, linking to its page. */
export function TemplateBadge({
	template,
}: {
	template: { slug: string; name: string; version?: string };
}) {
	return (
		<Link
			to={`/templates/${template.slug}`}
			className="tbadge"
			title={`Built on the ${template.name} template`}
			onClick={(e) => e.stopPropagation()}
		>
			<Icon name="tpl" size={13} />
			<span className="min-w-0 truncate">{template.name}</span>
			{template.version && <span className="v">v{template.version}</span>}
		</Link>
	);
}
