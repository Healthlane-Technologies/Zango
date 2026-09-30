import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTemplates, type TemplateSummary } from '@/api/templates';
import {
	Button,
	ButtonLink,
	EmptyState,
	ErrorState,
	Icon,
	Page,
	PageHeader,
	Skeleton,
	cx,
} from '@/ui';
import {
	SORTS,
	categories,
	categoryStyle,
	filterTemplates,
	groupTemplates,
	hasAgents,
	type SortKey,
} from './catalog';
import { AgentsTag, BetaBadge, Highlighted, TemplateIcon } from './parts';
import { TemplateQuickView } from './TemplateQuickView';

/** Focus the search box on `/`, unless the user is already typing somewhere. */
function useSlashFocus(ref: React.RefObject<HTMLInputElement>) {
	useEffect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
			const el = document.activeElement as HTMLElement | null;
			if (el && (/INPUT|TEXTAREA|SELECT/.test(el.tagName) || el.isContentEditable)) return;
			e.preventDefault();
			ref.current?.focus();
			ref.current?.select();
		};
		document.addEventListener('keydown', onKey);
		return () => document.removeEventListener('keydown', onKey);
	}, [ref]);
}

function Row({ t, q, onOpen }: { t: TemplateSummary; q: string; onOpen: () => void }) {
	return (
		<button type="button" className="trow" onClick={onOpen}>
			<TemplateIcon template={t} size={30} />
			<span className="tm">
				<b>
					<Highlighted text={t.name} q={q} /> {t.is_beta && <BetaBadge />}
				</b>
				<small>{t.one_liner || t.catalogue.description}</small>
			</span>
			<span className="tx">
				<AgentsTag count={t.catalogue.recommended_agents?.length ?? 0} />
				{t.apps_using > 0 && (
					<span className="num" title="Apps built on this template">
						{t.apps_using} {t.apps_using === 1 ? 'app' : 'apps'}
					</span>
				)}
				<span className="mono">v{t.version}</span>
			</span>
		</button>
	);
}

/** The template gallery (prototype vTemplates). Filters live in the URL so they survive a reload. */
export function TemplatesPage() {
	const { data: all, isLoading, error, refetch } = useTemplates();
	const [params, setParams] = useSearchParams();
	const [q, setQ] = useState(params.get('q') ?? '');
	const category = params.get('category') ?? '';
	const sort = (params.get('sort') as SortKey) in SORTS ? (params.get('sort') as SortKey) : 'used';
	const withAgents = params.get('agents') === '1';
	const used = params.get('used') === '1';
	const [open, setOpen] = useState<TemplateSummary | null>(null);
	const searchRef = useRef<HTMLInputElement>(null);
	useSlashFocus(searchRef);

	const setParam = (key: string, value: string) => {
		const next = new URLSearchParams(params);
		if (value) next.set(key, value);
		else next.delete(key);
		setParams(next, { replace: true });
	};
	useEffect(() => {
		const t = setTimeout(() => setParam('q', q.trim()), 250);
		return () => clearTimeout(t);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [q]);

	const filters = { q, category, sort, withAgents, used };
	const list = useMemo(
		() => filterTemplates(all ?? [], filters),
		[all, q, category, sort, withAgents, used],
	); // eslint-disable-line react-hooks/exhaustive-deps
	const groups = useMemo(() => groupTemplates(list, { q, category }), [list, q, category]);
	const cats = useMemo(() => categories(all ?? []), [all]);
	const clear = () => {
		setQ('');
		setParams({}, { replace: true });
	};

	return (
		<Page wide>
			<PageHeader
				title="Templates"
				description="Validated starting points the agent tailors to your requirements."
				actions={
					<ButtonLink to="/apps/new" icon="plus">
						Start blank
					</ButtonLink>
				}
			/>
			{error ? (
				<div className="card">
					<ErrorState error={error} onRetry={() => refetch()} />
				</div>
			) : (
				<div className="tlib">
					<nav className="trail" aria-label="Template categories">
						<button
							type="button"
							className={cx('tr-i', !category && 'on')}
							onClick={() => setParam('category', '')}
						>
							<span className="sw" style={{ background: 'var(--t3)' }} />
							<span className="tl">All templates</span>
							<span className="tc num">{all?.length ?? '–'}</span>
						</button>
						{cats.map(([name, count]) => (
							<button
								key={name}
								type="button"
								className={cx('tr-i', category === name && 'on')}
								onClick={() => setParam('category', name)}
							>
								<span className="sw" style={{ background: categoryStyle(name).fg }} />
								<span className="tl">{name}</span>
								<span className="tc num">{count}</span>
							</button>
						))}
						<div className="tr-f">
							<h4>Show only</h4>
							<label className="tchk">
								<input
									type="checkbox"
									checked={withAgents}
									disabled={!all?.some(hasAgents)}
									onChange={(e) => setParam('agents', e.target.checked ? '1' : '')}
								/>
								<span>Includes AI agents</span>
							</label>
							<label className="tchk">
								<input
									type="checkbox"
									checked={used}
									onChange={(e) => setParam('used', e.target.checked ? '1' : '')}
								/>
								<span>Used by an app</span>
							</label>
						</div>
					</nav>

					<section className="tmain">
						<div className="toolbar tbar">
							<label className="tsearch">
								<Icon name="search" />
								<input
									ref={searchRef}
									value={q}
									onChange={(e) => setQ(e.target.value)}
									placeholder="Search templates"
									aria-label="Search templates"
									autoComplete="off"
								/>
								<kbd>/</kbd>
							</label>
							<select
								className="select w-[200px]"
								aria-label="Category"
								value={category}
								onChange={(e) => setParam('category', e.target.value)}
							>
								<option value="">All categories</option>
								{cats.map(([name]) => (
									<option key={name} value={name}>
										{name}
									</option>
								))}
							</select>
							<select
								className="select w-[170px]"
								aria-label="Sort"
								value={sort}
								onChange={(e) => setParam('sort', e.target.value === 'used' ? '' : e.target.value)}
							>
								{(Object.keys(SORTS) as SortKey[]).map((k) => (
									<option key={k} value={k}>
										{SORTS[k][0]}
									</option>
								))}
							</select>
							{all && (
								<span className="num ml-auto text-[12.5px] text-t3">
									{list.length} of {all.length}
								</span>
							)}
						</div>

						{isLoading && (
							<div className="tlist">
								{Array.from({ length: 4 }, (_, i) => (
									<div key={i} className="trow">
										<Skeleton width={30} height={30} />
										<span className="tm grid gap-1.5">
											<Skeleton width="40%" />
											<Skeleton width="70%" />
										</span>
									</div>
								))}
							</div>
						)}

						{all && !list.length && (
							<div className="card">
								<EmptyState
									title={q.trim() ? `No templates match “${q.trim()}”` : 'No templates match'}
									action={
										<div className="flex gap-2">
											<Button size="sm" onClick={clear}>
												Clear filters
											</Button>
											<ButtonLink to="/apps/new" size="sm">
												Start blank
											</ButtonLink>
										</div>
									}
								>
									{all.length
										? 'Clear a filter or search for a workflow, role or category.'
										: 'No templates have been published yet.'}
								</EmptyState>
							</div>
						)}

						{groups.map(([heading, items]) => (
							<div key={heading ?? 'all'}>
								{heading && (
									<div className="tgh">
										<h2>{heading}</h2>
										<span className="num">{items.length}</span>
									</div>
								)}
								<div className={cx('tlist', !heading && 'mt-1')}>
									{items.map((t) => (
										<Row key={t.slug} t={t} q={q} onOpen={() => setOpen(t)} />
									))}
								</div>
							</div>
						))}
					</section>
				</div>
			)}
			<TemplateQuickView template={open} onClose={() => setOpen(null)} />
		</Page>
	);
}
