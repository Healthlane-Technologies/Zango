import { cx } from '@/ui';
import type { BuilderSection } from './sections';

export interface SectionState {
	section: BuilderSection;
	count: number;
	errors: number;
	warnings: number;
	changed: number;
}

export function SectionNav({
	sections,
	active,
	onSelect,
}: {
	sections: SectionState[];
	active: string;
	onSelect: (id: string) => void;
}) {
	return (
		<nav className="bv-nav" aria-label="Sections">
			{sections.map(({ section, count, errors, warnings, changed }) => (
				<button
					key={section.id}
					type="button"
					className={cx('bv-ni', section.id === active && 'on', !count && 'empty')}
					aria-current={section.id === active ? 'true' : undefined}
					onClick={() => onSelect(section.id)}
					title={section.hint}
				>
					<span className="min-w-0 truncate">{section.title}</span>
					<span className="bv-nm">
						{changed > 0 && <i className="bv-dot chg" title={`${changed} changed by the agent`} />}
						{errors > 0 ? (
							<i className="bv-dot err" title={`${errors} error${errors > 1 ? 's' : ''}`} />
						) : warnings > 0 ? (
							<i className="bv-dot wrn" title={`${warnings} warning${warnings > 1 ? 's' : ''}`} />
						) : null}
						<span className="ct">{count || ''}</span>
					</span>
				</button>
			))}
		</nav>
	);
}
