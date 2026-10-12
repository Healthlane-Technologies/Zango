import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTemplates, type TemplateSummary } from '@/api/templates';
import { Button, ButtonLink, ErrorState, Icon, Page, PageHeader, Skeleton, cx } from '@/ui';
import {
	SORTS,
	categoryStyle,
	describeMatches,
	featured,
	filterTemplates,
	hasAgents,
	orderedCategories,
	tokens,
	type Match,
	type SortKey,
} from './catalog';
import { CardVisual, FeaturedCard, TemplateCard } from './parts';
import { TemplateQuickView } from './TemplateQuickView';
import './gallery.css';

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

const SHELF_SIZE = 8;

/** "What do you want to build?" — a description matched against the catalogue. */
function DescribeHero({
	all,
	value,
	onSubmit,
}: {
	all: TemplateSummary[];
	value: string;
	onSubmit: (text: string) => void;
}) {
	const [text, setText] = useState(value);
	useEffect(() => setText(value), [value]);
	// Examples in the catalogue's own words: what the most used templates are also called.
	const examples = useMemo(
		() =>
			featured(all, 4)
				.map((t) => t.catalogue.aka?.[1] ?? t.catalogue.aka?.[0] ?? t.name)
				.filter(Boolean),
		[all],
	);
	return (
		<section className="ghero">
			<div className="gh-in">
				<div className="gh-t">
					<span className="gh-k">
						<Icon name="zap" size={13} />
						Describe it
					</span>
					<h2>What do you want to build?</h2>
					<p>
						Describe the process in a sentence. We find the closest templates, or the agent
						starts your app from the description.
					</p>
				</div>
				<form
					className="gh-box"
					onSubmit={(e) => {
						e.preventDefault();
						onSubmit(text.trim());
					}}
				>
					<textarea
						rows={2}
						value={text}
						placeholder="e.g. Clinics order vaccines with credit limits, distributors fulfil and we track delivery"
						aria-label="Describe what you want to build"
						onChange={(e) => setText(e.target.value)}
						onKeyDown={(e) => {
							if (e.key === 'Enter' && !e.shiftKey) {
								e.preventDefault();
								onSubmit(text.trim());
							}
						}}
					/>
					<Button type="submit" variant="primary" icon="search" disabled={!text.trim()}>
						Find templates
					</Button>
				</form>
				{!!examples.length && (
					<div className="gh-ex">
						<span>Try</span>
						{examples.map((x) => (
							<button key={x} type="button" className="gchip" onClick={() => onSubmit(x)}>
								{x}
							</button>
						))}
					</div>
				)}
			</div>
		</section>
	);
}

function Matches({
	text,
	matches,
	onOpen,
	onClear,
}: {
	text: string;
	matches: Match[];
	onOpen: (t: TemplateSummary) => void;
	onClear: () => void;
}) {
	const navigate = useNavigate();
	const blank = `/apps/new?prompt=${encodeURIComponent(text)}`;
	return (
		<section>
			<div className="gsec-h">
				<h2>Closest templates</h2>
				<span className="muted">for “{text}”</span>
				<Button size="xs" variant="ghost" className="ml-auto" onClick={onClear}>
					Clear
				</Button>
			</div>
			{matches.length ? (
				<div className="gm-grid">
					{matches.map(({ template: t, workflows, roles }) => (
						<div key={t.slug} className="gmc">
							<CardVisual template={t} />
							<div className="gc-b">
								<div className="gf-h">
									<b className="flex-1">{t.name}</b>
								</div>
								<ul className="tp-c gwhy">
									<li>
										<Icon name="check" weight={2.4} />
										{workflows.length ? `Covers ${workflows.join(', ')}` : `${t.category} workflows`}
									</li>
									{!!roles.length && (
										<li>
											<Icon name="check" weight={2.4} />
											For {roles.join(' and ')}
										</li>
									)}
									<li>
										<Icon name="check" weight={2.4} />
										{t.apps_using
											? `Running in ${t.apps_using} ${t.apps_using === 1 ? 'app' : 'apps'}`
											: 'Newly published'}{' '}
										· v{t.version}
									</li>
								</ul>
								<div className="gm-f">
									<Button size="sm" onClick={() => onOpen(t)}>
										Details
									</Button>
									<Button
										size="sm"
										variant="primary"
										onClick={() =>
											navigate(
												`/apps/new?template=${t.slug}&prompt=${encodeURIComponent(text)}`,
											)
										}
									>
										Use template
									</Button>
								</div>
							</div>
						</div>
					))}
				</div>
			) : (
				<div className="card">
					<div className="empty">
						<b>No close match</b>
						Start from your description and the agent composes the app for you.
					</div>
				</div>
			)}
			<div className="gm-blank">
				<Icon name="blank" />
				<span className="flex-1">None of these? The agent can build it from your description.</span>
				<ButtonLink to={blank} size="sm">
					Start from this description
				</ButtonLink>
			</div>
		</section>
	);
}

function CardSkeletons({ n }: { n: number }) {
	return (
		<div className="ggrid">
			{Array.from({ length: n }, (_, i) => (
				<div key={i} className="gcard">
					<Skeleton height={92} />
					<div className="gc-b grid gap-2">
						<Skeleton width="60%" />
						<Skeleton width="90%" />
						<Skeleton width="40%" />
					</div>
				</div>
			))}
		</div>
	);
}

/** The template gallery (mockup vTemplates). Filters live in the URL so they survive a reload. */
export function TemplatesPage() {
	const { data: all, isLoading, error, refetch } = useTemplates();
	const [params, setParams] = useSearchParams();
	const [q, setQ] = useState(params.get('q') ?? '');
	const category = params.get('category') ?? '';
	const sort = (params.get('sort') as SortKey) in SORTS ? (params.get('sort') as SortKey) : 'used';
	const withAgents = params.get('agents') === '1';
	const ask = params.get('ask') ?? '';
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

	const templates = useMemo(() => all ?? [], [all]);
	const list = useMemo(
		() => filterTemplates(templates, { q, category, sort, withAgents, used: false }),
		[templates, q, category, sort, withAgents],
	);
	const cats = useMemo(() => orderedCategories(templates), [templates]);
	const feat = useMemo(() => featured(templates), [templates]);
	const matches = useMemo(() => (ask ? describeMatches(templates, ask) : []), [templates, ask]);
	const anyAgents = templates.some(hasAgents);
	const browse = !category && !tokens(q).length && !withAgents;
	const clear = () => {
		setQ('');
		setParams({}, { replace: true });
	};

	let body;
	if (isLoading) {
		body = <CardSkeletons n={8} />;
	} else if (browse) {
		body = (
			<>
				{!!feat.length && (
					<section>
						<div className="gsec-h">
							<h2>Featured</h2>
							<span className="muted">The most used templates, running live with demo data</span>
						</div>
						<div className="gfeat-g">
							{feat.map((t) => (
								<FeaturedCard key={t.slug} template={t} onOpen={() => setOpen(t)} />
							))}
						</div>
					</section>
				)}
				{cats.map(([name, count]) => {
					const items = templates
						.filter((t) => t.category === name)
						.sort(SORTS[sort][1])
						.slice(0, SHELF_SIZE);
					return (
						<section key={name} className="gshelf">
							<div className="gsec-h">
								<span className="sw" style={{ background: categoryStyle(name).fg }} />
								<h2>{name}</h2>
								<span className="muted num">{count}</span>
								{count > 4 && (
									<button
										type="button"
										className="link ml-auto text-[12.5px]"
										onClick={() => setParam('category', name)}
									>
										See all
									</button>
								)}
							</div>
							<div className="grow">
								{items.map((t) => (
									<TemplateCard key={t.slug} template={t} onOpen={() => setOpen(t)} />
								))}
							</div>
						</section>
					);
				})}
			</>
		);
	} else if (list.length) {
		body = (
			<section>
				<div className="gsec-h">
					<h2>{tokens(q).length ? `Results for “${q.trim()}”` : category || 'All templates'}</h2>
					<span className="muted num">{list.length}</span>
				</div>
				<div className="ggrid">
					{list.map((t) => (
						<TemplateCard key={t.slug} template={t} q={q} onOpen={() => setOpen(t)} />
					))}
				</div>
			</section>
		);
	} else {
		body = (
			<div className="card">
				<div className="empty">
					<b>{q.trim() ? `No templates match “${q.trim()}”` : 'No templates match'}</b>
					{templates.length
						? 'Clear a filter, or describe the app above and we suggest the closest fit.'
						: 'No templates have been published yet.'}
					<div className="mt-3 flex justify-center gap-2">
						<Button size="sm" onClick={clear}>
							Clear filters
						</Button>
						<ButtonLink to="/apps/new" size="sm">
							Start blank
						</ButtonLink>
					</div>
				</div>
			</div>
		);
	}

	return (
		<Page wide>
			<div className="gpage">
				<PageHeader
					title="Templates"
					description={
						all
							? `${all.length} validated starting points. The agent tailors any of them to your requirements.`
							: 'Validated starting points the agent tailors to your requirements.'
					}
					actions={
						<ButtonLink to="/apps/new" icon="blank">
							Start blank
						</ButtonLink>
					}
				/>
				{error ? (
					<div className="card">
						<ErrorState error={error} onRetry={() => refetch()} />
					</div>
				) : (
					<>
						<DescribeHero all={templates} value={ask} onSubmit={(text) => setParam('ask', text)} />
						{ask && !isLoading && (
							<Matches
								text={ask}
								matches={matches}
								onOpen={setOpen}
								onClear={() => setParam('ask', '')}
							/>
						)}
						<div className="gbar">
							<div className="gtabs" role="tablist" aria-label="Template categories">
								<button
									type="button"
									role="tab"
									aria-selected={!category}
									className={cx(!category && 'on')}
									onClick={() => setParam('category', '')}
								>
									All<span className="num">{templates.length}</span>
								</button>
								{cats.map(([name, count]) => (
									<button
										key={name}
										type="button"
										role="tab"
										aria-selected={category === name}
										className={cx(category === name && 'on')}
										onClick={() => setParam('category', category === name ? '' : name)}
									>
										{name}
										<span className="num">{count}</span>
									</button>
								))}
							</div>
							<div className="gbar-r">
								{anyAgents && (
									<button
										type="button"
										className={cx('gtog', withAgents && 'on')}
										aria-pressed={withAgents}
										onClick={() => setParam('agents', withAgents ? '' : '1')}
									>
										<Icon name="bot" size={14} />
										With AI agents
									</button>
								)}
								<label className="tsearch">
									<Icon name="search" />
									<input
										ref={searchRef}
										value={q}
										onChange={(e) => setQ(e.target.value)}
										placeholder="Search"
										aria-label="Search templates"
										autoComplete="off"
									/>
									<kbd>/</kbd>
								</label>
								<select
									className="select w-[150px]"
									aria-label="Sort"
									value={sort}
									onChange={(e) =>
										setParam('sort', e.target.value === 'used' ? '' : e.target.value)
									}
								>
									{(Object.keys(SORTS) as SortKey[]).map((k) => (
										<option key={k} value={k}>
											{SORTS[k][0]}
										</option>
									))}
								</select>
							</div>
						</div>
						{body}
					</>
				)}
			</div>
			<TemplateQuickView template={open} onClose={() => setOpen(null)} />
		</Page>
	);
}
