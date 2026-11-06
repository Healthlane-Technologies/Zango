import { useEffect, useState } from 'react';
import {
	inUseAgents,
	useActivatePrompt,
	useDeletePrompt,
	usePromoteVersion,
	usePromptList,
	type Prompt,
	type PromptType,
	type PromptVersion,
} from '@/api/ai';
import {
	Badge,
	Button,
	ConfirmModal,
	cx,
	Drawer,
	EmptyState,
	Pagination,
	RowMenu,
	SearchInput,
	SectionTitle,
	Segmented,
	Select,
	SwitchField,
	Table,
	Toolbar,
	useDebounced,
	type Column,
	type Tone,
} from '@/ui';
import { DiffView } from './diff';
import { CreatePromptModal, EditPromptModal, NewVersionModal } from './PromptModals';
import { fmtDate, InUseModal, PromptText, StatStrip } from './parts';

const PAGE_SIZE = 20;

const VERSION_TONE: Record<PromptVersion['status'], Tone> = {
	active: 'green',
	draft: 'amber',
	inactive: 'gray',
};
const VERSION_LABEL: Record<PromptVersion['status'], string> = {
	active: 'Live',
	draft: 'Draft',
	inactive: 'Old',
};

function TypeBadge({ type }: { type: PromptType }) {
	return <Badge tone={type === 'system' ? 'violet' : 'accent'}>{type === 'system' ? 'System' : 'User'}</Badge>;
}

export function PromptsTab({ appId }: { appId: string }) {
	const [q, setQ] = useState('');
	const search = useDebounced(q, 300);
	const [type, setType] = useState<'' | PromptType>('');
	const [includeInactive, setIncludeInactive] = useState(false);
	const [page, setPage] = useState(1);
	useEffect(() => setPage(1), [search, type, includeInactive]);

	const list = usePromptList(appId, { page, pageSize: PAGE_SIZE, search, type, includeInactive });
	const activate = useActivatePrompt(appId);
	const remove = useDeletePrompt(appId);

	const [openId, setOpenId] = useState<number | null>(null);
	const [modal, setModal] = useState<
		{ kind: 'create' } | { kind: 'edit' | 'version' | 'delete'; prompt: Prompt } | null
	>(null);
	const [blocked, setBlocked] = useState<Array<{ id: number; name: string }> | null>(null);

	const rows = list.data?.prompts.records;
	const stats = list.data?.stats;
	const open = rows?.find((p) => p.id === openId);

	const columns: Column<Prompt>[] = [
		{
			key: 'n',
			header: 'Prompt',
			cell: (p) => (
				<div className="nm">
					<div className="min-w-0">
						<span className="flex items-center gap-2">
							<b className="mono">{p.name}</b>
							<TypeBadge type={p.type} />
							{!p.is_active && <Badge tone="gray">Deactivated</Badge>}
						</span>
						{p.description && <small className="max-w-[380px] truncate">{p.description}</small>}
					</div>
				</div>
			),
		},
		{
			key: 'l',
			header: 'Live',
			cell: (p) =>
				p.active_version_number ? (
					<span className="mono">v{p.active_version_number}</span>
				) : (
					<span className="text-amber-t">None</span>
				),
		},
		{ key: 'v', header: 'Versions', cell: (p) => <span className="num">{p.total_versions}</span> },
		{
			key: 'u',
			header: 'Used by',
			cell: (p) =>
				p.used_by_agents.length ? (
					<span title={p.used_by_agents.map((a) => a.name).join(', ')}>
						{p.used_by_agents.length} agent{p.used_by_agents.length > 1 ? 's' : ''}
					</span>
				) : (
					<span className="text-t4">—</span>
				),
		},
		{ key: 'm', header: 'Changed', cell: (p) => <span className="text-t3">{fmtDate(p.modified_at)}</span> },
		{
			key: 'a',
			header: '',
			align: 'right',
			cell: (p) => (
				<RowMenu
					label={`Actions for ${p.name}`}
					items={
						p.is_active
							? [
									{ label: 'New version', icon: 'plus', onSelect: () => setModal({ kind: 'version', prompt: p }) },
									{ label: 'Edit details', icon: 'pen', onSelect: () => setModal({ kind: 'edit', prompt: p }) },
									null,
									{
										label: p.total_versions ? 'Deactivate' : 'Delete',
										icon: 'x',
										danger: true,
										onSelect: () => setModal({ kind: 'delete', prompt: p }),
									},
								]
							: [{ label: 'Activate', icon: 'check', onSelect: () => activate.mutate({ id: p.id }) }]
					}
				/>
			),
		},
	];

	return (
		<>
			<StatStrip
				items={[
					['Prompts', stats?.total_prompts],
					['With a live version', stats?.active_versions],
					['Versions', stats?.total_versions],
				]}
			/>
			<Toolbar>
				<SearchInput value={q} onChange={setQ} placeholder="Search prompts" />
				<Segmented
					label="Filter by type"
					value={type}
					onChange={setType}
					options={[
						{ value: '', label: 'All' },
						{ value: 'system', label: 'System' },
						{ value: 'user', label: 'User' },
					]}
				/>
				<SwitchField checked={includeInactive} onChange={setIncludeInactive} label="Show deactivated" />
				<Button variant="primary" icon="plus" className="ml-auto" onClick={() => setModal({ kind: 'create' })}>
					New prompt
				</Button>
			</Toolbar>
			<Table
				columns={columns}
				rows={rows}
				rowKey={(p) => p.id}
				loading={list.isLoading}
				error={list.error}
				onRetry={() => list.refetch()}
				onRowClick={(p) => setOpenId(p.id)}
				footer={
					list.data && list.data.prompts.total_pages > 1 ? (
						<Pagination
							page={page}
							pageSize={PAGE_SIZE}
							totalRecords={list.data.prompts.total_records}
							totalPages={list.data.prompts.total_pages}
							onPage={setPage}
							noun="prompts"
							busy={list.isFetching}
						/>
					) : undefined
				}
				empty={
					search || type ? (
						<EmptyState title="No prompts match">Try another search or filter.</EmptyState>
					) : (
						<EmptyState
							title="No prompts yet"
							action={
								<Button variant="primary" icon="plus" onClick={() => setModal({ kind: 'create' })}>
									New prompt
								</Button>
							}
						>
							Versioned prompt templates for agents. Change which version is live without a
							deploy.
						</EmptyState>
					)
				}
			/>

			{open && (
				<PromptDrawer
					appId={appId}
					prompt={open}
					onClose={() => setOpenId(null)}
					onNewVersion={() => setModal({ kind: 'version', prompt: open })}
					onEdit={() => setModal({ kind: 'edit', prompt: open })}
					onActivate={() => activate.mutate({ id: open.id })}
				/>
			)}

			{modal?.kind === 'create' && <CreatePromptModal appId={appId} onClose={() => setModal(null)} />}
			{modal?.kind === 'edit' && (
				<EditPromptModal appId={appId} prompt={modal.prompt} onClose={() => setModal(null)} />
			)}
			{modal?.kind === 'version' && (
				<NewVersionModal appId={appId} prompt={modal.prompt} onClose={() => setModal(null)} />
			)}
			<ConfirmModal
				open={modal?.kind === 'delete'}
				onOpenChange={(o) => !o && setModal(null)}
				title={modal?.kind === 'delete' && modal.prompt.total_versions ? 'Deactivate prompt' : 'Delete prompt'}
				confirmLabel={modal?.kind === 'delete' && modal.prompt.total_versions ? 'Deactivate' : 'Delete'}
				danger
				loading={remove.isPending}
				onConfirm={() =>
					modal?.kind === 'delete' &&
					remove.mutate(
						{ id: modal.prompt.id },
						{
							onSettled: () => setModal(null),
							onError: (err) => setBlocked(inUseAgents(err)),
						},
					)
				}
			>
				<p className="text-t2">
					{modal?.kind === 'delete' && modal.prompt.total_versions
						? 'It leaves the agent pickers. Its versions are kept, and you can activate it again later.'
						: 'It has no versions, so it will be removed for good.'}
				</p>
			</ConfirmModal>
			<InUseModal what="This prompt" agents={blocked} onClose={() => setBlocked(null)} />
		</>
	);
}

function PromptDrawer({
	appId,
	prompt,
	onClose,
	onNewVersion,
	onEdit,
	onActivate,
}: {
	appId: string;
	prompt: Prompt;
	onClose: () => void;
	onNewVersion: () => void;
	onEdit: () => void;
	onActivate: () => void;
}) {
	const promote = usePromoteVersion(appId);
	const [promoting, setPromoting] = useState<PromptVersion | null>(null);
	const latest = prompt.versions[0]?.version_number ?? 0;
	const [base, setBase] = useState(prompt.active_version_number ?? 0);
	const [other, setOther] = useState(latest);
	const vBase = prompt.versions.find((v) => v.version_number === base);
	const vOther = prompt.versions.find((v) => v.version_number === other);
	const live = prompt.active_version;

	return (
		<Drawer
			open
			wide
			onOpenChange={(o) => !o && onClose()}
			title={<span className="mono">{prompt.name}</span>}
			subtitle={
				<span className="inline-flex items-center gap-2">
					<TypeBadge type={prompt.type} />
					{prompt.description || `${prompt.total_versions} versions`}
				</span>
			}
			actions={
				prompt.is_active ? (
					<>
						<Button size="sm" onClick={onEdit}>
							Edit details
						</Button>
						<Button size="sm" variant="primary" icon="plus" onClick={onNewVersion}>
							New version
						</Button>
					</>
				) : (
					<Button size="sm" variant="primary" onClick={onActivate}>
						Activate
					</Button>
				)
			}
		>
			{!prompt.is_active && (
				<p className="mb-4 rounded-lg border border-border bg-subtle px-3 py-2 text-[12.5px] text-t2">
					Deactivated: hidden from agent pickers and read-only until activated again.
				</p>
			)}
			<SectionTitle>{live ? `Live text · v${live.version_number}` : 'Live text'}</SectionTitle>
			{live ? (
				<>
					<PromptText content={live.content} />
					{live.variables.length > 0 && (
						<div className="mt-2 flex flex-wrap gap-1">
							{live.variables.map((v) => (
								<Badge key={v} tone="violet">{`{{${v}}}`}</Badge>
							))}
						</div>
					)}
				</>
			) : (
				<p className="text-amber-t">No live version. Make one live from the history below.</p>
			)}

			{prompt.used_by_agents.length > 0 && (
				<>
					<SectionTitle>Used by</SectionTitle>
					<div className="flex flex-wrap gap-1">
						{prompt.used_by_agents.map((a) => (
							<Badge key={a.id} tone="line">
								<span className="mono">{a.name}</span>
							</Badge>
						))}
					</div>
				</>
			)}

			<SectionTitle>Version history</SectionTitle>
			<div className="overflow-hidden rounded-lg border border-border">
				{prompt.versions.map((v) => (
					<div
						key={v.id}
						className={cx(
							'flex items-start gap-3 border-b border-border-soft px-3 py-2.5 last:border-b-0',
							v.status === 'active' && 'bg-green-soft/40',
						)}
					>
						<span className="mono w-8 pt-0.5 text-[12.5px] font-semibold text-t1">v{v.version_number}</span>
						<div className="min-w-0 flex-1">
							<div className="flex items-center gap-2">
								<Badge tone={VERSION_TONE[v.status]} dot={v.status === 'active'}>
									{VERSION_LABEL[v.status]}
								</Badge>
								{v.version_number === latest && v.status !== 'active' && (
									<span className="text-[11px] text-t3">latest</span>
								)}
							</div>
							<div className="mt-0.5 text-[12.5px] text-t2">{v.change_description || '—'}</div>
							<div className="text-[11.5px] text-t3">
								{fmtDate(v.created_at)}
								{v.created_by ? ` · ${v.created_by}` : ''}
							</div>
						</div>
						{prompt.is_active && v.status !== 'active' && (
							<Button size="xs" onClick={() => setPromoting(v)}>
								Make live
							</Button>
						)}
					</div>
				))}
			</div>

			{prompt.versions.length >= 2 && (
				<>
					<SectionTitle>Compare versions</SectionTitle>
					<div className="mb-2 flex items-center gap-2">
						{[
							[base, setBase, 'From'] as const,
							[other, setOther, 'To'] as const,
						].map(([val, setVal, label]) => (
							<Select
								key={label}
								aria-label={label}
								className="w-auto"
								value={val}
								onChange={(e) => setVal(Number(e.target.value))}
							>
								{prompt.versions.map((v) => (
									<option key={v.id} value={v.version_number}>
										{label} v{v.version_number}
										{v.status === 'active' ? ' (live)' : ''}
									</option>
								))}
							</Select>
						))}
					</div>
					{vBase && vOther && vBase.id !== vOther.id ? (
						<DiffView before={vBase.content} after={vOther.content} />
					) : (
						<p className="text-[12.5px] text-t3">Pick two different versions.</p>
					)}
				</>
			)}

			<ConfirmModal
				open={promoting != null}
				onOpenChange={(o) => !o && setPromoting(null)}
				title={`Make v${promoting?.version_number} live`}
				confirmLabel="Make live"
				loading={promote.isPending}
				onConfirm={() =>
					promoting &&
					promote.mutate(
						{ promptId: prompt.id, versionId: promoting.id },
						{ onSettled: () => setPromoting(null) },
					)
				}
			>
				<p className="text-t2">
					Every agent using <b className="mono">{prompt.name}</b> switches to this text on its next
					run. No deploy needed.
				</p>
			</ConfirmModal>
		</Drawer>
	);
}
