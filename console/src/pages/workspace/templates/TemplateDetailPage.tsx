import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { useApps } from '@/api/apps';
import { useTemplate, useTemplates, type TemplateDetail } from '@/api/templates';
import {
	AppIcon,
	Badge,
	Button,
	ButtonLink,
	EmptyState,
	ErrorState,
	Icon,
	Page,
	Skeleton,
	cx,
	initials,
	toast,
	type IconName,
} from '@/ui';
import { categoryStyle, formatUpdated } from './catalog';
import { AgentsTag, BetaBadge, LiveFrame, PreviewDialog, PreviewThumb, TemplateIcon } from './parts';
import { primaryEntity, specModel, typeLabel, type SpecModel } from './specModel';
import './gallery.css';

const FICONS: IconName[] = ['pulse', 'users', 'check', 'flow', 'file', 'zap', 'shield', 'logs'];
const ROLE_COLORS = ['#4F46E5', '#0F766E', '#B45309', '#A21CAF', '#1D4ED8', '#BE185D', '#15803D'];
const TONE: Record<string, string> = {
	gray: '#98A2B3',
	blue: '#2E90FA',
	green: '#12B76A',
	amber: '#F79009',
	red: '#F04438',
	purple: '#7A5AF8',
	teal: '#15B79E',
	indigo: '#6172F3',
	pink: '#EE46BC',
};
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;
const PACKAGE_NAMES: Record<string, string> = { crm: 'CRM', appbuilder: 'App builder', crud: 'CRUD' };
const VERSION_TONE = { published: 'green', deprecated: 'gray', draft: 'amber' } as const;

/** One section of the page: a block with a heading, linked from the sticky section nav. */
interface Section {
	id: string;
	label: string;
	title: string;
	sub?: string;
	body: ReactNode;
}

/** The section in view: the last one whose heading has scrolled under the nav. */
function useScrollSpy(ids: string[]) {
	const [current, setCurrent] = useState(ids[0]);
	useEffect(() => {
		const els = ids.map((id) => document.getElementById(`s-${id}`)).filter(Boolean) as HTMLElement[];
		if (!els.length) return;
		const visible = new Map<string, boolean>();
		const io = new IntersectionObserver(
			(entries) => {
				for (const e of entries) visible.set(e.target.id.slice(2), e.isIntersecting);
				const first = ids.find((id) => visible.get(id));
				if (first) setCurrent(first);
			},
			{ rootMargin: '-70px 0px -55% 0px' },
		);
		els.forEach((el) => io.observe(el));
		return () => io.disconnect();
	}, [ids.join('|')]); // eslint-disable-line react-hooks/exhaustive-deps
	return [current, setCurrent] as const;
}

function jump(id: string) {
	document.getElementById(`s-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function Kv({ label, children }: { label: string; children: ReactNode }) {
	return (
		<div className="pd-kv">
			<span>{label}</span>
			<b>{children}</b>
		</div>
	);
}

function StatusFlow({ statuses }: { statuses: SpecModel['entities'][number]['statuses'] }) {
	return (
		<div className="wsflow">
			{statuses.map((s, i) => (
				<span key={s.code} style={{ display: 'contents' }}>
					{i > 0 && <em className="sep">›</em>}
					<span className="st">
						<i style={{ background: TONE[s.color] ?? TONE.gray }} />
						{s.label}
					</span>
				</span>
			))}
		</div>
	);
}

function sections(t: TemplateDetail, model: SpecModel | null, fromExample: boolean): Section[] {
	const c = t.catalogue;
	const roles = c.roles?.length
		? c.roles.map((r) => ({ name: r.name, description: r.description ?? '' }))
		: (model?.roles ?? []);
	const out: Section[] = [];

	out.push({
		id: 'overview',
		label: 'Overview',
		title: 'Overview',
		body: (
			<div className="pd-ov">
				<div>
					<h3>What it is for</h3>
					<p className="pd-prose">{c.description || t.one_liner}</p>
				</div>
				{!!c.fits_when?.length && (
					<div>
						<h3>A good fit when</h3>
						<ul className="tp-c">
							{c.fits_when.map((x) => (
								<li key={x}>
									<Icon name="check" weight={2.4} />
									{x}
								</li>
							))}
						</ul>
					</div>
				)}
			</div>
		),
	});

	if (c.workflows?.length) {
		out.push({
			id: 'how',
			label: 'How it works',
			title: 'How it works',
			sub: 'From the moment work arrives to the moment it closes.',
			body: (
				<ol className="pd-how">
					{c.workflows.map((w, i) => (
						<li key={w.name}>
							<span className="ph-n">{i + 1}</span>
							<div className="ph-b">
								<b>{w.name}</b>
								{w.description && <p>{w.description}</p>}
							</div>
						</li>
					))}
				</ol>
			),
		});
	}

	out.push({
		id: 'preview',
		label: 'Preview',
		title: 'See it running',
		sub: 'The template’s app with demo data. Switch roles to see what each person gets.',
		body: <InlinePreview template={t} />,
	});

	if (c.gives_you?.length) {
		out.push({
			id: 'features',
			label: 'Core functionality',
			title: 'Core functionality',
			sub: 'Already built — you describe your program, you don’t rebuild these.',
			body: (
				<div className="pd-feats">
					{c.gives_you.map((x, i) => (
						<div key={x} className="pd-feat">
							<span className="pf-ic">
								<Icon name={FICONS[i % FICONS.length]} />
							</span>
							<b>{x}</b>
						</div>
					))}
				</div>
			),
		});
	}

	if (roles.length) {
		out.push({
			id: 'roles',
			label: 'User roles',
			title: 'User roles',
			sub: 'Each role sees its own queue, menu and permissions.',
			body: (
				<div className="pd-roles">
					{roles.map((r, i) => (
						<div key={r.name} className="pd-role">
							<span className="pr-av" style={{ background: ROLE_COLORS[i % ROLE_COLORS.length] }}>
								{initials(r.name)}
							</span>
							<div className="min-w-0">
								<b>{r.name}</b>
								{r.description && <p>{r.description}</p>}
							</div>
						</div>
					))}
				</div>
			),
		});
	}

	const agents = c.recommended_agents ?? [];
	if (agents.length) {
		out.push({
			id: 'agents',
			label: 'AI agents',
			title: 'AI agents',
			sub: 'Agents work inside the workflow, with a person in the loop.',
			body: (
				<div className="pd-stack">
					{agents.map((a) => (
						<div key={a.id ?? a.name} className="card">
							<div className="card-b">
								<div className="gf-h">
									<span className="pf-ic sm">
										<Icon name="bot" />
									</span>
									<b className="flex-1">{a.name}</b>
									{a.mode && <Badge tone="violet">{a.mode}</Badge>}
								</div>
								{(a.description || a.hitl) && (
									<p className="mt-2 text-t3">{a.description || a.hitl}</p>
								)}
							</div>
						</div>
					))}
				</div>
			),
		});
	}

	const lifecycles = (model?.entities ?? []).filter((e) => e.statuses.length);
	if (lifecycles.length) {
		out.push({
			id: 'workflows',
			label: 'Workflows',
			title: 'Workflows',
			sub: fromExample
				? 'The lifecycles in the template’s example app.'
				: 'The record lifecycles the app starts with. Each one is tailored in the requirements.',
			body: (
				<div className="pd-stack">
					{lifecycles.map((e, i) => {
						const who = [...new Set(e.transitions.flatMap((tr) => tr.roles))];
						return (
							<div key={e.code} className="card pd-wf">
								<div className="card-h">
									<span className="pf-ic sm">
										<Icon name={FICONS[i % FICONS.length]} size={14} />
									</span>
									<h3>{e.name}</h3>
									<span className="r text-[12px] text-t3">
										{e.transitions.length} step{e.transitions.length === 1 ? '' : 's'}
										{who.length ? ` · ${who.join(', ')}` : ''}
									</span>
								</div>
								<div className="card-b">
									<StatusFlow statuses={e.statuses} />
									{!!e.transitions.length && (
										<p className="mt-2 text-[12.5px] text-t3">
											{e.transitions.map((tr) => tr.label).join(' · ')}
										</p>
									)}
								</div>
							</div>
						);
					})}
				</div>
			),
		});
	}

	const objects = c.data_objects ?? [];
	if (model || objects.length) {
		out.push({
			id: 'data',
			label: 'Data & access',
			title: 'Data & access',
			body: model ? <DataAndAccess model={model} roles={roles.map((r) => r.name)} /> : (
				<div className="pd-sec">
					<h3>Data model</h3>
					<div className="pkgs">
						{objects.map((o) => (
							<span key={o} className="rchip">
								{o}
							</span>
						))}
					</div>
					<p className="pd-note">
						Every record keeps an audit trail, owner and created / updated fields. Fields are
						agreed in the requirements; the build generates them as app code.
					</p>
				</div>
			),
		});
	}

	if (c.compliance?.length) {
		out.push({
			id: 'compliance',
			label: 'Compliance',
			title: 'Compliance',
			body: (
				<div className="pd-feats">
					{c.compliance.map((x) => (
						<div key={x} className="pd-feat">
							<span className="pf-ic g">
								<Icon name="shield" />
							</span>
							<b>{x}</b>
						</div>
					))}
				</div>
			),
		});
	}

	if (c.packages?.length || c.integrations?.length) {
		out.push({
			id: 'packages',
			label: 'Packages',
			title: 'Packages & integrations',
			body: (
				<>
					{!!c.packages?.length && (
						<div className="pd-sec">
							<h3>Packages</h3>
							<div className="pd-pk">
								{c.packages.map((p) => (
									<div key={p.name} className="pd-pkc">
										<span className="pf-ic">
											<Icon name="pkg" />
										</span>
										<div className="min-w-0">
											<b>{PACKAGE_NAMES[p.name] ?? p.name[0].toUpperCase() + p.name.slice(1)}</b>
											<span className="mono">zango-{p.name}</span>
											{p.description && <p>{p.description}</p>}
										</div>
									</div>
								))}
							</div>
						</div>
					)}
					{!!c.integrations?.length && (
						<div className="pd-sec">
							<h3>Integrations</h3>
							<div className="card">
								<div className="act-list">
									{c.integrations.map((x) => (
										<div key={x} className="ai items-center">
											<Icon name="zap" />
											<div className="min-w-0 flex-1">
												<b>{x}</b>
												<small>Connected per environment once the app is built</small>
											</div>
										</div>
									))}
								</div>
							</div>
						</div>
					)}
				</>
			),
		});
	}

	out.push({
		id: 'setup',
		label: 'Setup',
		title: 'Getting started',
		body: <Setup template={t} />,
	});
	return out;
}

function DataAndAccess({ model, roles }: { model: SpecModel; roles: string[] }) {
	const primary = primaryEntity(model);
	const names = new Map(model.entities.map((e) => [e.code, e.name]));
	const cols = model.entities.slice(0, 6);
	// The spec's own role names (the catalogue may spell them differently), then any role an
	// entity grants access to that the spec doesn't list.
	const matrixRoles = [
		...new Set([
			...model.roles.map((r) => r.name),
			...(model.roles.length ? [] : roles),
			...model.entities.flatMap((e) => Object.keys(e.access)),
		]),
	];
	const accessFor = (e: SpecModel['entities'][number], role: string) =>
		e.access[role] ??
		Object.entries(e.access).find(([k]) => k.toLowerCase() === role.toLowerCase())?.[1] ??
		'';
	return (
		<>
			<div className="pd-sec">
				<h3>Data model</h3>
				<div className="pd-ents">
					{model.entities.map((e) => {
						const inbound = model.entities.filter((x) => x.links.includes(e.code)).length;
						const shown = e.fields.slice(0, 5);
						return (
							<div key={e.code} className="pd-ent">
								<div className="pe-h">
									<Icon name="logs" size={14} />
									<b>{e.name}</b>
									{e.code === primary && (
										<Badge tone="accent" className="ml-auto">
											Primary
										</Badge>
									)}
								</div>
								<ul>
									{shown.map((f) => (
										<li key={f.key}>
											<span>
												{f.label}
												{f.required && <span className="text-t4"> *</span>}
											</span>
											<span className="mono">{f.to ? `→ ${names.get(f.to) ?? f.to}` : typeLabel(f.type)}</span>
										</li>
									))}
									{e.fields.length > shown.length && (
										<li className="text-t4">+{e.fields.length - shown.length} more fields</li>
									)}
								</ul>
								<div className="pe-r">
									<Icon name="flow" size={12} />
									{e.links.filter((l) => names.has(l)).length
										? `Linked to ${e.links.filter((l) => names.has(l)).map((l) => names.get(l)).join(', ')}`
										: inbound
											? `${inbound} linked record${inbound === 1 ? '' : 's'}`
											: e.module}
								</div>
							</div>
						);
					})}
				</div>
				<p className="pd-note">
					Every record keeps an audit trail, owner and created / updated fields. Add fields in the
					requirements; the build generates them as app code.
				</p>
			</div>
			{!!matrixRoles.length && (
				<div className="pd-sec">
					<h3>Roles and access</h3>
					<div className="card tbl-wrap">
						<table className="t pd-mx">
							<thead>
								<tr>
									<th>Role</th>
									{cols.map((e) => (
										<th key={e.code}>{e.name}</th>
									))}
								</tr>
							</thead>
							<tbody>
								{matrixRoles.map((r) => (
									<tr key={r}>
										<td className="font-medium text-t1">{r}</td>
										{cols.map((e) => {
											const v = accessFor(e, r);
											return (
												<td key={e.code}>
													<span className={cx('mx', v ? `mx-${Math.min(v.length, 4)}` : 'mx-n')}>
														{v || '—'}
													</span>
												</td>
											);
										})}
									</tr>
								))}
							</tbody>
						</table>
						<div className="tfoot">
							C create · R read · U update · D delete · — no access. Rows can be scoped further
							per role (own records, a region).
						</div>
					</div>
				</div>
			)}
		</>
	);
}

const STEPS: Array<[string, string]> = [
	['Describe your requirements', 'Start from this template with a brief, your SOPs or an RFP.'],
	[
		'The agent drafts the app',
		'It tailors the template’s spec in one pass and flags what it had to infer.',
	],
	[
		'Review it in the live preview',
		'Click through the app as each role, answer the open questions, ask for changes in chat.',
	],
	['Commit for build', 'The build agent writes the app from the spec, exactly as previewed.'],
	[
		'Verified and deployed',
		'The platform migrates, sets up roles and menus, runs the checks and reports what passed.',
	],
];

function Setup({ template: t }: { template: TemplateDetail }) {
	const refs = t.references ?? [];
	return (
		<>
			<div className="pd-sec">
				<h3>From template to app</h3>
				<div className="pd-tl">
					{STEPS.map(([title, text], i) => (
						<div key={title} className="tl-s">
							<span className="tl-n">{i + 1}</span>
							<div>
								<b>{title}</b>
								<p>{text}</p>
							</div>
						</div>
					))}
				</div>
			</div>
			{!!refs.length && (
				<div className="pd-sec">
					<h3>Start from an example</h3>
					<div className="pd-refs">
						{refs.map((r) => (
							<div key={r.id} className="pd-ref">
								<b>{r.title}</b>
								{r.summary && <p>{r.summary}</p>}
								{!!r.tags?.length && (
									<div className="pkgs">
										{r.tags.slice(0, 4).map((x) => (
											<span key={x} className="rchip">
												{x}
											</span>
										))}
									</div>
								)}
								<div className="r">
									<ButtonLink
										to={`/apps/new?template=${t.slug}&reference=${encodeURIComponent(r.id)}`}
										size="sm"
									>
										Start from this example
									</ButtonLink>
								</div>
							</div>
						))}
					</div>
				</div>
			)}
		</>
	);
}

function InlinePreview({ template: t }: { template: TemplateDetail }) {
	const [full, setFull] = useState(false);
	return (
		<div className="card overflow-hidden">
			<div className="flex items-center gap-2 border-b border-[var(--border-soft)] px-4 py-2.5 text-[12.5px] text-t3">
				<Icon name="eye" size={14} />
				<span className="flex-1">Running on demo data — nothing here is saved.</span>
				<Button size="xs" onClick={() => setFull(true)}>
					Open full screen
				</Button>
			</div>
			<LiveFrame template={t} className="h-[640px]" />
			<PreviewDialog template={t} open={full} onOpenChange={setFull} />
		</div>
	);
}

/** One template's page (mockup vTemplate): a long page with a sticky section nav. */
export function TemplateDetailPage() {
	const { slug } = useParams();
	const navigate = useNavigate();
	const { data: t, isLoading, error, refetch } = useTemplate(slug);
	const { data: all } = useTemplates();
	const { data: apps } = useApps();
	const [full, setFull] = useState(false);

	const starter = useMemo(() => specModel(t?.starter_yaml), [t?.starter_yaml]);
	const example = useMemo(() => specModel(t?.example_yaml), [t?.example_yaml]);
	// A near-empty starter (the generic template's) says less than its example app.
	const fromExample = !!example && (!starter || starter.entities.length < 2);
	const model = fromExample ? example : starter;
	const secs = useMemo(() => (t ? sections(t, model, fromExample) : []), [t, model, fromExample]);
	const [current, setCurrent] = useScrollSpy(secs.map((s) => s.id));

	const back = (
		<Link to="/templates" className="back">
			<Icon name="back" />
			Templates
		</Link>
	);

	if (error) {
		const missing = error instanceof ApiError && error.status === 404;
		return (
			<Page wide>
				<div className="pd">
					{back}
					<div className="card">
						{missing ? (
							<EmptyState title="Template not found">It may have been archived or renamed.</EmptyState>
						) : (
							<ErrorState error={error} onRetry={() => refetch()} />
						)}
					</div>
				</div>
			</Page>
		);
	}
	if (isLoading || !t) {
		return (
			<Page wide>
				<div className="pd">
					{back}
					<div className="pd-hero" style={{ '--hb': '#F4F4F5' } as CSSProperties}>
						<div className="pd-hl">
							<div className="flex items-center gap-3">
								<Skeleton width={48} height={48} />
								<div className="grid gap-2">
									<Skeleton width={120} />
									<Skeleton width={260} height={22} />
								</div>
							</div>
							<Skeleton width="80%" />
							<Skeleton width={220} height={34} />
						</div>
					</div>
				</div>
			</Page>
		);
	}

	const c = t.catalogue;
	const { bg, fg } = categoryStyle(t.category);
	const roleCount = c.roles?.length || model?.roles.length || 0;
	const workflowCount = c.workflows?.length || model?.entities.filter((e) => e.statuses.length).length || 0;
	const using = (apps ?? []).filter((a) => a.template?.slug === t.slug);
	const related = (all ?? [])
		.filter((x) => x.category === t.category && x.slug !== t.slug)
		.sort((a, b) => b.apps_using - a.apps_using || a.name.localeCompare(b.name))
		.slice(0, 3);
	const use = () => navigate(`/apps/new?template=${t.slug}`);
	const copy = () =>
		navigator.clipboard
			?.writeText(window.location.href)
			.then(() => toast.success('Link copied'))
			.catch(() => toast.error('Could not copy the link'));

	return (
		<Page wide>
			<div className="pd">
				{back}
				<header className="pd-hero" style={{ '--hb': bg, '--hf': fg } as CSSProperties}>
					<div className="pd-hl">
						<div className="pd-id">
							<TemplateIcon template={t} size={48} />
							<div className="min-w-0">
								<div className="pd-cat">
									<span className="sw" style={{ background: fg }} />
									{t.category} · Template
								</div>
								<h1>
									{t.name} {t.is_beta && <BetaBadge />}
								</h1>
							</div>
						</div>
						<p className="pd-tag">{t.one_liner || c.description}</p>
						<div className="pd-badges">
							<AgentsTag count={c.recommended_agents?.length ?? 0} />
							{!!roleCount && <Badge tone="line">{plural(roleCount, 'role')}</Badge>}
							{!!workflowCount && <Badge tone="line">{plural(workflowCount, 'workflow')}</Badge>}
							<Badge tone="line">
								<span className="mono">v{t.version}</span>
							</Badge>
							<Badge tone="line">Updated {formatUpdated(t.published_at)}</Badge>
						</div>
						<div className="pd-cta">
							<Button variant="primary" icon="rocket" onClick={use}>
								Use template
							</Button>
							<Button icon="eye" onClick={() => setFull(true)}>
								Live preview
							</Button>
							<Button variant="ghost" onClick={() => jump('how')}>
								See how it works
							</Button>
							<button type="button" className="ib" aria-label="Copy link" onClick={copy}>
								<Icon name="copy" />
							</button>
						</div>
					</div>
					<button
						type="button"
						className="pd-shot"
						onClick={() => setFull(true)}
						aria-label={`Open the live preview of ${t.name}`}
					>
						<PreviewThumb template={t} />
						<span className="pd-shot-k">
							<Icon name="eye" size={12} />
							Live preview
						</span>
					</button>
				</header>

				<nav className="pd-tabs" aria-label="On this page">
					{secs.map((s) => (
						<button
							key={s.id}
							type="button"
							className={cx(current === s.id && 'on')}
							onClick={() => {
								setCurrent(s.id);
								jump(s.id);
							}}
						>
							{s.label}
						</button>
					))}
				</nav>

				<div className="pd-grid">
					<div className="pd-main">
						{secs.map((s) => (
							<section key={s.id} id={`s-${s.id}`} className="pd-blk">
								<div className="pd-bh">
									<h2>{s.title}</h2>
									{s.sub && <p>{s.sub}</p>}
								</div>
								{s.body}
							</section>
						))}
					</div>

					<aside className="pd-side">
						<div className="card">
							<div className="card-b">
								<Kv label="Version">
									<span className="mono">v{t.version}</span>
								</Kv>
								<Kv label="Category">{t.category || '—'}</Kv>
								<Kv label="Updated">{formatUpdated(t.published_at)}</Kv>
								<Kv label="Apps built on it">
									<span className="num">{t.apps_using}</span>
								</Kv>
								{!!c.integrations?.length && <Kv label="Integrations">{c.integrations.length}</Kv>}
								<Button variant="primary" className="mt-3.5 w-full justify-center" onClick={use}>
									Use template
								</Button>
							</div>
						</div>

						<div className="card">
							<div className="card-h">
								<h3>In your workspace</h3>
							</div>
							{using.length ? (
								<div className="act-list">
									{using.slice(0, 5).map((a) => (
										<Link key={a.uuid} to={`/apps/${a.uuid}`} className="ai">
											<AppIcon name={a.name} size={26} />
											<div className="min-w-0 flex-1">
												<b>{a.name}</b>
												<small>v{a.template?.version}</small>
											</div>
										</Link>
									))}
									{using.length > 5 && (
										<Link to="/apps" className="ai text-[12.5px] text-t3">
											and {using.length - 5} more
										</Link>
									)}
								</div>
							) : (
								<div className="card-b text-[12.5px] text-t3">No apps use this template yet.</div>
							)}
						</div>

						{!!related.length && (
							<div className="card">
								<div className="card-h">
									<h3>Related templates</h3>
								</div>
								<div className="act-list">
									{related.map((x) => (
										<Link key={x.slug} to={`/templates/${x.slug}`} className="ai">
											<TemplateIcon template={x} size={26} />
											<div className="min-w-0 flex-1">
												<b>{x.name}</b>
												<small>
													{x.apps_using
														? `${x.apps_using} ${x.apps_using === 1 ? 'app' : 'apps'}`
														: 'New'}
												</small>
											</div>
										</Link>
									))}
								</div>
							</div>
						)}

						{!!t.versions?.length && (
							<div className="card">
								<div className="card-h">
									<h3>Changelog</h3>
								</div>
								<div className="card-b py-1">
									<div className="pd-tl mini">
										{t.versions.slice(0, 5).map((v, i) => (
											<div key={v.version} className="tl-s">
												<span className={cx('tl-n', i === 0 && 'cur')}>{i === 0 ? '●' : ''}</span>
												<div className="min-w-0">
													<b className="mono">v{v.version}</b>
													<span className="text-t3"> · {formatUpdated(v.published_at)}</span>{' '}
													{i === 0 ? (
														<Badge tone="green">Latest</Badge>
													) : (
														v.status !== 'published' && (
															<Badge tone={VERSION_TONE[v.status] ?? 'gray'}>{v.status}</Badge>
														)
													)}
													{v.changelog && <p>{v.changelog}</p>}
												</div>
											</div>
										))}
									</div>
								</div>
							</div>
						)}
					</aside>
				</div>
			</div>
			<PreviewDialog template={t} open={full} onOpenChange={setFull} />
		</Page>
	);
}
