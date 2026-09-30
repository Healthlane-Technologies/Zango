import { useMemo, useState } from 'react';

import { useCodebase, type DataModel } from '@/api/code';

import { formatDateTime, timeAgo } from '@/format/time';

import {
	Badge,
	Card,
	CardHeader,
	Drawer,
	EmptyState,
	ErrorState,
	Icon,
	KeyValues,
	SearchInput,
	Segmented,
	Skeleton,
	Table,
	Toolbar,
} from '@/ui';

import { StatTile } from './parts';

type View = 'modules' | 'models' | 'routes';

interface ModelRow extends DataModel {
	module: string;
}

function ModelDrawer({ model, onClose }: { model: ModelRow | null; onClose: () => void }) {
	return (
		<Drawer
			open={!!model}
			onOpenChange={(o) => !o && onClose()}
			title={model?.name ?? ''}
			subtitle={model ? `${model.module} · ${model.meta.db_table ?? ''}` : undefined}
		>
			{model && (
				<div className="grid gap-5">
					<section>
						<h4 className="mb-2 text-[12.5px]">Fields · {model.fields.length}</h4>
						<div className="card tbl-wrap">
							<table className="t">
								<thead>
									<tr>
										<th>Name</th>
										<th>Type</th>
										<th>Null</th>
									</tr>
								</thead>
								<tbody>
									{model.fields.map((f) => (
										<tr key={f.name}>
											<td className="mono text-t1">{f.name}</td>
											<td>{f.type}</td>
											<td>{f.attributes.null ? 'Yes' : 'No'}</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</section>
					{model.relationships.length > 0 && (
						<section>
							<h4 className="mb-2 text-[12.5px]">Relationships · {model.relationships.length}</h4>
							<div className="card tbl-wrap">
								<table className="t">
									<thead>
										<tr>
											<th>Name</th>
											<th>Type</th>
											<th>Related model</th>
										</tr>
									</thead>
									<tbody>
										{model.relationships.map((r) => (
											<tr key={r.name}>
												<td className="mono text-t1">{r.name}</td>
												<td>{r.type}</td>
												<td>{r.related_model}</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						</section>
					)}
				</div>
			)}
		</Drawer>
	);
}

/** Read-only view of the app's code parsed from its workspace: modules, data models, routes. */
export function CodeSettings({ appId }: { appId: string }) {
	const { data, isLoading, error, refetch } = useCodebase(appId);
	const [view, setView] = useState<View>('modules');
	const [q, setQ] = useState('');
	const [openModel, setOpenModel] = useState<ModelRow | null>(null);

	const models = useMemo<ModelRow[]>(() => {
		// A module lists models it imports too; show each model once, under the first module that has it.
		const seen = new Set<string>();
		return (data?.modules ?? []).flatMap((m) =>
			m.models
				.filter((x) => !seen.has(x.name) && seen.add(x.name))
				.map((x) => ({ ...x, module: m.name })),
		);
	}, [data]);

	const needle = q.trim().toLowerCase();
	const match = (...s: Array<string | null | undefined>) =>
		!needle || s.some((x) => x?.toLowerCase().includes(needle));

	if (error) {
		// The endpoint 500s with an ENOENT message when the app's workspace isn't on this server.
		const noWorkspace = /No such file or directory/.test(error.message);
		return (
			<div className="card">
				{noWorkspace ? (
					<EmptyState title="No workspace on this server">
						This app's code isn't checked out here, so its modules and routes can't be read.
					</EmptyState>
				) : (
					<ErrorState error={error} onRetry={() => refetch()} />
				)}
			</div>
		);
	}

	return (
		<div className="grid gap-4">
			<div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
				<StatTile label="Modules" value={data?.total_modules ?? '—'} loading={isLoading} />
				<StatTile label="Data models" value={models.length} loading={isLoading} />
				<StatTile label="Routes" value={data?.total_routes ?? '—'} loading={isLoading} />
				<StatTile label="Packages" value={data?.total_packages ?? '—'} loading={isLoading} />
			</div>
			<Card>
				<CardHeader title="Workspace" />
				<div className="card-b">
					{data ? (
						<KeyValues
							items={[
								['App', <span className="mono">{data.app_name}</span>],
								['Version', <span className="mono">{data.version}</span>],
								[
									'Last modified',
									data.last_modified ? (
										<span title={formatDateTime(data.last_modified)}>
											{timeAgo(data.last_modified)}
										</span>
									) : null,
								],
								[
									'Package routes',
									data.package_routes.length ? (
										<span className="flex flex-wrap gap-1">
											{data.package_routes.map((r) => (
												<Badge key={r.package} tone="line">
													{r.package}
												</Badge>
											))}
										</span>
									) : null,
								],
							]}
						/>
					) : (
						<div className="grid gap-3">
							<Skeleton width="40%" />
							<Skeleton width="60%" />
						</div>
					)}
				</div>
			</Card>

			<Toolbar>
				<Segmented
					label="View"
					value={view}
					onChange={setView}
					options={[
						{ value: 'modules', label: 'Modules' },
						{ value: 'models', label: 'Data models' },
						{ value: 'routes', label: 'Routes' },
					]}
				/>
				<SearchInput
					value={q}
					onChange={setQ}
					placeholder={`Search ${view === 'models' ? 'data models' : view}`}
				/>
				<a
					className="btn btn-g btn-sm ml-auto"
					href={`/platform/apps/${appId}/code/#codeexecution`}
				>
					<Icon name="ext" />
					Code execution in classic view
				</a>
			</Toolbar>

			{view === 'modules' && (
				<Table
					loading={isLoading}
					rows={data?.modules.filter((m) => match(m.name, m.path))}
					rowKey={(m) => m.path}
					empty={<EmptyState title="No modules" />}
					columns={[
						{
							key: 'n',
							header: 'Module',
							cell: (m) => (
								<div className="nm">
									<div>
										<b>{m.name}</b>
										<small className="mono">{m.path}</small>
									</div>
								</div>
							),
						},
						{
							key: 'm',
							header: 'Models',
							cell: (m) => <span className="num">{m.models_count}</span>,
						},
						{
							key: 'v',
							header: 'Views',
							cell: (m) => <span className="num">{m.views_count}</span>,
						},
						{
							key: 't',
							header: 'Templates',
							cell: (m) => <span className="num">{m.templates_count}</span>,
						},
						{
							key: 'f',
							header: 'Has',
							cell: (m) => (
								<span className="flex gap-1">
									{m.has_urls && <Badge tone="line">urls</Badge>}
									{m.has_policies && <Badge tone="line">policies</Badge>}
								</span>
							),
						},
					]}
				/>
			)}
			{view === 'models' && (
				<Table
					loading={isLoading}
					rows={models.filter((m) => match(m.name, m.module, m.meta.db_table))}
					rowKey={(m) => `${m.module}.${m.name}`}
					onRowClick={setOpenModel}
					empty={<EmptyState title="No data models" />}
					columns={[
						{
							key: 'n',
							header: 'Model',
							cell: (m) => <b className="font-[550] text-t1">{m.name}</b>,
						},
						{ key: 'mod', header: 'Module', cell: (m) => m.module },
						{
							key: 'f',
							header: 'Fields',
							cell: (m) => <span className="num">{m.fields.length}</span>,
						},
						{
							key: 'r',
							header: 'Relations',
							cell: (m) => <span className="num">{m.relationships.length}</span>,
						},
						{
							key: 't',
							header: 'Table',
							cell: (m) => <span className="mono">{m.meta.db_table ?? '—'}</span>,
						},
					]}
				/>
			)}
			{view === 'routes' && (
				<Table
					loading={isLoading}
					rows={data?.route_tree.filter((r) => match(r.full_url, r.module, r.name))}
					rowKey={(r) => `${r.full_module_path}:${r.pattern}`}
					empty={<EmptyState title="No routes" />}
					columns={[
						{
							key: 'u',
							header: 'URL',
							cell: (r) => <span className="mono text-t1">{r.full_url}</span>,
						},
						{ key: 'm', header: 'Module', cell: (r) => <span className="mono">{r.module}</span> },
						{ key: 'n', header: 'Name', cell: (r) => r.name ?? <span className="text-t4">—</span> },
					]}
				/>
			)}
			<ModelDrawer model={openModel} onClose={() => setOpenModel(null)} />
		</div>
	);
}
