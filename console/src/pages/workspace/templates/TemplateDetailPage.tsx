import { Link, useParams } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { useTemplate } from '@/api/templates';
import {
	Badge,
	ButtonLink,
	Card,
	CardBody,
	CardHeader,
	EmptyState,
	ErrorState,
	Icon,
	KeyValues,
	Page,
	Skeleton,
} from '@/ui';
import { formatUpdated } from './catalog';
import { BetaBadge, TemplateIcon } from './parts';

function camel(s: string) {
	return s
		.replace(/[^A-Za-z0-9 ]/g, ' ')
		.split(/\s+/)
		.filter(Boolean)
		.map((w) => w[0].toUpperCase() + w.slice(1))
		.join('');
}

const VERSION_TONE = { published: 'green', deprecated: 'gray', draft: 'amber' } as const;

/** One template's page (prototype vTemplate). */
export function TemplateDetailPage() {
	const { slug } = useParams();
	const { data: t, isLoading, error, refetch } = useTemplate(slug);

	const back = (
		<Link
			to="/templates"
			className="back"
			style={{ margin: '-8px 0 12px -8px', width: 'fit-content' }}
		>
			<Icon name="back" />
			Templates
		</Link>
	);

	if (error) {
		const missing = error instanceof ApiError && error.status === 404;
		return (
			<Page>
				{back}
				<div className="card">
					{missing ? (
						<EmptyState title="Template not found">
							It may have been archived or renamed.
						</EmptyState>
					) : (
						<ErrorState error={error} onRetry={() => refetch()} />
					)}
				</div>
			</Page>
		);
	}
	if (isLoading || !t) {
		return (
			<Page>
				{back}
				<div className="flex items-center gap-3">
					<Skeleton width={44} height={44} />
					<div className="grid gap-2">
						<Skeleton width={240} height={18} />
						<Skeleton width={180} />
					</div>
				</div>
			</Page>
		);
	}

	const c = t.catalogue;
	const workflows = c.workflows ?? [];
	const roles = c.roles ?? [];
	const objects = c.data_objects ?? [];
	const packages = c.packages ?? [];
	const agents = c.recommended_agents ?? [];
	const compliance = c.compliance ?? [];

	return (
		<Page>
			{back}
			<div className="ph" style={{ alignItems: 'center' }}>
				<TemplateIcon template={t} size={44} />
				<div className="min-w-0">
					<h1>
						{t.name} {t.is_beta && <BetaBadge />}
					</h1>
					<p>
						{t.category} · <span className="mono">v{t.version}</span> · updated{' '}
						{formatUpdated(t.published_at)}
					</p>
				</div>
				<div className="r">
					<ButtonLink to={`/apps/new?template=${t.slug}`} variant="primary">
						Use template
					</ButtonLink>
				</div>
			</div>

			<div className="tdg">
				<div className="flex min-w-0 flex-col gap-4">
					<Card>
						<CardHeader title="About" />
						<CardBody>
							<p className="max-w-[68ch] text-t2">{c.description || t.one_liner}</p>
							{!!c.gives_you?.length && (
								<ul className="tp-c mt-4">
									{c.gives_you.map((x) => (
										<li key={x}>
											<Icon name="check" weight={2.4} />
											{x}
										</li>
									))}
								</ul>
							)}
						</CardBody>
					</Card>

					{!!workflows.length && (
						<Card>
							<CardHeader title="Workflows" count={workflows.length} />
							<CardBody className="py-1.5">
								<ol className="steps-ol">
									{workflows.map((w, i) => (
										<li key={w.name}>
											<span className="n">{i + 1}</span>
											<span className="min-w-0">
												<b>{w.name}</b>
												{w.description && <small>{w.description}</small>}
											</span>
										</li>
									))}
								</ol>
							</CardBody>
						</Card>
					)}

					<div className="tdg2">
						<Card>
							<CardHeader title="Roles" count={roles.length} />
							{roles.length ? (
								<div className="act-list">
									{roles.map((r) => (
										<div key={r.name} className="ai items-center">
											<Icon name="users" />
											<div className="min-w-0">
												<b>{r.name}</b>
												{r.description && <small>{r.description}</small>}
											</div>
										</div>
									))}
								</div>
							) : (
								<CardBody className="text-t3">Roles are agreed in the requirements chat.</CardBody>
							)}
						</Card>
						<Card>
							<CardHeader title="Data model" count={objects.length} />
							<CardBody>
								{objects.length ? (
									<div className="pkgs">
										{objects.map((o) => (
											<span key={o} className="pkg">
												{camel(o)}
											</span>
										))}
									</div>
								) : (
									<span className="text-t3">Defined by the requirements.</span>
								)}
							</CardBody>
						</Card>
					</div>

					{!!packages.length && (
						<div className="card tbl-wrap">
							<CardHeader title="Packages" count={packages.length} />
							<table className="t">
								<tbody>
									{packages.map((p) => (
										<tr key={p.name}>
											<td className="mono w-[210px] text-t1">zango-{p.name}</td>
											<td className="whitespace-normal text-t3">{p.description}</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					)}
				</div>

				<div className="flex min-w-0 flex-col gap-4">
					<Card>
						<CardHeader title="Details" />
						<CardBody>
							<KeyValues
								items={[
									['Version', <span className="mono">v{t.version}</span>],
									['Category', t.category || '—'],
									['Apps using it', <span className="num">{t.apps_using}</span>],
									['Integrations', c.integrations?.length ? c.integrations.join(', ') : '—'],
									['Spec format', t.spec_format === 'yaml' ? 'YAML' : 'Markdown'],
								]}
							/>
						</CardBody>
					</Card>

					<Card>
						<CardHeader title="Recommended AI agents" />
						{agents.length ? (
							<div className="act-list">
								{agents.map((a) => (
									<div key={a.id ?? a.name} className="ai items-center">
										<Icon name="bot" />
										<div className="min-w-0 flex-1">
											<b>{a.name}</b>
											{(a.hitl || a.description) && <small>{a.hitl || a.description}</small>}
										</div>
									</div>
								))}
							</div>
						) : (
							<CardBody className="text-t3">
								None recommended. Add agents from the catalog after creating the app.
							</CardBody>
						)}
					</Card>

					{!!compliance.length && (
						<Card>
							<CardHeader title="Compliance built in" />
							<div className="act-list">
								{compliance.map((x) => (
									<div key={x} className="ai items-center">
										<span className="text-green">
											<Icon name="check" weight={2.4} />
										</span>
										<span className="text-t1">{x}</span>
									</div>
								))}
							</div>
						</Card>
					)}

					<Card>
						<CardHeader title="Version history" />
						{t.versions?.length ? (
							<div className="act-list">
								{t.versions.map((v) => (
									<div key={v.version} className="ai">
										<span className="mono w-[52px] shrink-0 text-t1">v{v.version}</span>
										<div className="min-w-0 flex-1">
											<b className="font-normal">{v.changelog || 'No notes.'}</b>
											<small>{formatUpdated(v.published_at)}</small>
										</div>
										{v.status !== 'published' && (
											<Badge tone={VERSION_TONE[v.status] ?? 'gray'}>{v.status}</Badge>
										)}
									</div>
								))}
							</div>
						) : (
							<CardBody className="text-t3">No published versions.</CardBody>
						)}
					</Card>
				</div>
			</div>
		</Page>
	);
}
