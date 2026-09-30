import { useMemo, useState } from 'react';
import type { TemplateSummary } from '@/api/templates';
import { EmptyState, ErrorState, Icon, Skeleton, cx } from '@/ui';
import { categories, filterTemplates } from '../workspace/templates/catalog';
import { TemplateIcon } from '../workspace/templates/parts';

/** Inline template chooser for the New app form (prototype vNew .tpick). */
export function TemplatePicker({
	templates,
	loading,
	error,
	onRetry,
	value,
	onChange,
	disabled,
}: {
	templates: TemplateSummary[] | undefined;
	loading: boolean;
	error: Error | null;
	onRetry: () => void;
	value: string | null;
	onChange: (slug: string) => void;
	disabled?: boolean;
}) {
	const [q, setQ] = useState('');
	const [category, setCategory] = useState('');
	const all = templates ?? [];
	const cats = useMemo(() => categories(all), [all]);
	const list = useMemo(
		() => filterTemplates(all, { q, category, sort: 'used', withAgents: false, used: false }),
		[all, q, category],
	);

	return (
		<div className="tpick">
			<div className="tp-h">
				<label className="tsearch">
					<Icon name="search" />
					<input
						value={q}
						onChange={(e) => setQ(e.target.value)}
						placeholder={`Search ${all.length || ''} templates`.replace('  ', ' ')}
						aria-label="Search templates"
						autoComplete="off"
						disabled={disabled}
					/>
				</label>
				<select
					className="select w-[190px]"
					aria-label="Category"
					value={category}
					onChange={(e) => setCategory(e.target.value)}
					disabled={disabled}
				>
					<option value="">All categories</option>
					{cats.map(([name]) => (
						<option key={name} value={name}>
							{name}
						</option>
					))}
				</select>
			</div>
			<div className="tp-l" role="radiogroup" aria-label="Template">
				{error && <ErrorState error={error} onRetry={onRetry} />}
				{loading &&
					Array.from({ length: 3 }, (_, i) => (
						<div key={i} className="tprow">
							<Skeleton width={28} height={28} />
							<span className="mid grid gap-1.5">
								<Skeleton width="45%" />
								<Skeleton width="75%" />
							</span>
						</div>
					))}
				{!loading && !error && !list.length && (
					<EmptyState title={all.length ? 'No templates match' : 'No templates published yet'}>
						{all.length ? 'Try another term or category.' : 'Describe the app instead.'}
					</EmptyState>
				)}
				{list.map((t) => {
					const on = t.slug === value;
					return (
						<button
							key={t.slug}
							type="button"
							role="radio"
							aria-checked={on}
							disabled={disabled}
							className={cx('tprow', on && 'on')}
							onClick={() => onChange(t.slug)}
						>
							<span className="rd" />
							<TemplateIcon template={t} size={28} />
							<span className="mid">
								<b>{t.name}</b>
								<small>{t.one_liner || t.catalogue.description}</small>
							</span>
							<span className="meta">
								<span className="mono">v{t.version}</span>
								<br />
								{t.catalogue.packages?.length ?? 0} packages
							</span>
						</button>
					);
				})}
			</div>
		</div>
	);
}
