import { useState } from 'react';

import { useApiMutation } from '@/api/hooks';

import {
	taskKeys,
	updateTask,
	useTask,
	type AppTask,
	type Crontab,
	type TaskRun,
} from '@/api/tasks';

import {
	Badge,
	Button,
	Checkbox,
	CodeBlock,
	Drawer,
	EmptyState,
	ErrorState,
	Field,
	Input,
	SectionTitle,
	Skeleton,
	Tabs,
	Textarea,
	type Tone,
} from '@/ui';

type Tab = 'settings' | 'code' | 'history';

const CRON_FIELDS: Array<[keyof Crontab, string]> = [
	['minute', 'Minute'],
	['hour', 'Hour'],
	['day_of_month', 'Day of month'],
	['month_of_year', 'Month'],
	['day_of_week', 'Day of week'],
];
const EVERY_MINUTE: Crontab = {
	minute: '*',
	hour: '*',
	day_of_week: '*',
	day_of_month: '*',
	month_of_year: '*',
};

/** Celery result states. */
const RUN_TONE: Record<string, Tone> = {
	SUCCESS: 'green',
	FAILURE: 'red',
	RETRY: 'amber',
	STARTED: 'accent',
	PENDING: 'gray',
	REVOKED: 'gray',
};

function parseKwargs(text: string): Record<string, unknown> | string {
	try {
		const v: unknown = JSON.parse(text || '{}');
		return v && typeof v === 'object' && !Array.isArray(v)
			? (v as Record<string, unknown>)
			: 'Must be a JSON object';
	} catch {
		return 'Invalid JSON';
	}
}

export function TaskDrawer({
	appId,
	task,
	onClose,
}: {
	appId: string;
	task: AppTask;
	onClose: () => void;
}) {
	const [tab, setTab] = useState<Tab>('settings');
	const [enabled, setEnabled] = useState(task.is_enabled);
	const [cron, setCron] = useState<Crontab>(task.crontab ?? EVERY_MINUTE);
	const [kwargsText, setKwargsText] = useState(JSON.stringify(task.kwargs ?? {}, null, 2));

	const kwargs = parseKwargs(kwargsText);
	const cronError = CRON_FIELDS.some(([k]) => !cron[k].trim());

	const save = useApiMutation({
		fn: () =>
			updateTask(appId, task.id, {
				is_enabled: enabled,
				crontab: cron,
				kwargs: kwargs as Record<string, unknown>,
			}),
		invalidate: [taskKeys.all(appId)],
		success: 'Task updated',
		onSuccess: onClose,
	});

	return (
		<Drawer
			open
			onOpenChange={(o) => !o && onClose()}
			title={<span className="mono text-[14px]">{task.name}</span>}
			subtitle={`Task ${task.id}`}
			footer={
				tab === 'settings' ? (
					<>
						<Button onClick={onClose}>Cancel</Button>
						<Button
							variant="primary"
							disabled={typeof kwargs === 'string' || cronError}
							loading={save.isPending}
							onClick={() => save.mutate()}
						>
							Save
						</Button>
					</>
				) : undefined
			}
		>
			<Tabs
				className="-mx-5 -mt-5 mb-5"
				value={tab}
				onChange={setTab}
				items={[
					{ value: 'settings', label: 'Settings' },
					{ value: 'code', label: 'Code' },
					{ value: 'history', label: 'Run history' },
				]}
			/>

			{tab === 'settings' && (
				<>
					<Checkbox
						label="Enabled"
						hint="Disabled tasks keep their schedule but don't run."
						checked={enabled}
						onChange={(e) => setEnabled(e.target.checked)}
					/>

					<SectionTitle
						action={
							<span className="mono text-t3">
								{CRON_FIELDS.map(([k]) => cron[k] || '?').join(' ')}
							</span>
						}
					>
						Schedule
					</SectionTitle>
					<div className="grid grid-cols-5 gap-2">
						{CRON_FIELDS.map(([key, label]) => (
							<Field
								key={key}
								label={<span className="text-[11.5px] font-medium text-t3">{label}</span>}
							>
								{(p) => (
									<Input
										{...p}
										className="mono"
										value={cron[key]}
										aria-invalid={!cron[key].trim() || undefined}
										onChange={(e) => setCron((c) => ({ ...c, [key]: e.target.value }))}
									/>
								)}
							</Field>
						))}
					</div>
					<p className="mt-2 text-[12px] text-t3">
						Cron syntax: <span className="mono">*</span> for every,{' '}
						<span className="mono">*/15</span> for every 15, <span className="mono">1-5</span> for a
						range.
					</p>

					<SectionTitle>Keyword arguments</SectionTitle>
					<Field
						label="kwargs (JSON)"
						error={typeof kwargs === 'string' ? kwargs : undefined}
						hint="Passed to the task function on every run."
					>
						{(p) => (
							<Textarea
								{...p}
								className="mono"
								rows={6}
								spellCheck={false}
								value={kwargsText}
								onChange={(e) => setKwargsText(e.target.value)}
							/>
						)}
					</Field>

					<SectionTitle>Policies</SectionTitle>
					{task.attached_policies.length ? (
						<div className="flex flex-wrap gap-1">
							{task.attached_policies.map((p) => (
								<Badge key={p.id} tone="line">
									{p.name}
								</Badge>
							))}
						</div>
					) : (
						<p className="text-t3">No policies attached.</p>
					)}
				</>
			)}

			{tab === 'code' &&
				(task.code ? (
					<CodeBlock maxHeight={560}>{task.code}</CodeBlock>
				) : (
					<EmptyState title="Source unavailable">The task's module couldn't be loaded.</EmptyState>
				))}

			{tab === 'history' && <RunHistory appId={appId} taskId={task.id} />}
		</Drawer>
	);
}

function RunHistory({ appId, taskId }: { appId: string; taskId: number }) {
	const { data, isLoading, error, refetch } = useTask(appId, taskId);
	const [openRun, setOpenRun] = useState<number | null>(null);

	if (isLoading) {
		return (
			<div className="grid gap-3">
				{[0, 1, 2].map((i) => (
					<Skeleton key={i} height={40} />
				))}
			</div>
		);
	}
	if (error) return <ErrorState error={error} onRetry={() => refetch()} />;
	const runs = data?.run_history ?? [];
	if (!runs.length)
		return (
			<EmptyState title="No runs yet">Runs appear here once the task has executed.</EmptyState>
		);

	return (
		<div className="overflow-hidden rounded-lg border border-border">
			{runs.map((run, i) => (
				<RunRow
					key={i}
					run={run}
					open={openRun === i}
					onToggle={() => setOpenRun(openRun === i ? null : i)}
				/>
			))}
		</div>
	);
}

function RunRow({ run, open, onToggle }: { run: TaskRun; open: boolean; onToggle: () => void }) {
	const detail = run.traceback || run.result;
	return (
		<div className="border-b border-border-soft last:border-0">
			<button
				type="button"
				className="flex w-full items-center gap-3 px-3 py-2.5 hover:bg-hover"
				onClick={onToggle}
				disabled={!detail}
			>
				<Badge tone={RUN_TONE[run.status] ?? 'gray'} dot>
					{run.status}
				</Badge>
				{/* The API's date_started mirrors date_done, so only the finish time is shown. */}
				<span className="mono text-t2">{run.date_done}</span>
				{run.worker && <span className="ml-auto truncate text-[12px] text-t4">{run.worker}</span>}
			</button>
			{open && detail && (
				<div className="px-3 pb-3">
					<CodeBlock>{detail}</CodeBlock>
				</div>
			)}
		</div>
	);
}
