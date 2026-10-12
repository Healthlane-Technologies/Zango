// What the platform checked on an App Studio build, and what it is waiting on the user for.
// (AgentRun.studio_report and pending_actions, see backend apps/agent_mode/studio_build.py.)
import { useEffect, useState } from 'react';
import {
	checksOf,
	ContinueRefused,
	useContinueRun,
	type CheckLayer,
	type ChecksSummary,
	type PendingAction,
	type StudioReport,
} from '@/api/agentRuns';
import { Badge, Button, ConfirmModal, cx, Drawer, Icon, toast, type Tone } from '@/ui';

/** The checks in the order the build runs them, with what each one proves. */
const LAYERS: Array<[key: string, name: string, proves: string]> = [
	['app_shell', 'App shell', '/app is served by the app module and a fresh frontend build'],
	['audit_holes', 'Plain-language items', 'every item in the spec was implemented'],
	['design_lint', 'Design lint', 'the frontend uses the design system'],
	['api', 'API & access', 'each role can do exactly what the spec allows'],
	['ui', 'UI per role', 'menus, lists, forms and 360 pages work in a browser'],
	['design', 'Design vs goldens', 'screens match the reference design'],
	['scenarios', 'Scenarios', 'each plain-language rule behaves as written'],
];
const LAYER_NAME: Record<string, string> = {
	...Object.fromEntries(LAYERS.map(([k, n]) => [k, n])),
	// Bring-up steps a pending action can block.
	appbuilder: 'Menus and routes',
};
const layerName = (key: string) => LAYER_NAME[key] ?? key.replace(/[_:]/g, ' ');

const STATUS: Record<CheckLayer['status'], [Tone, string]> = {
	pass: ['green', 'Passed'],
	fail: ['red', 'Failed'],
	skip: ['gray', 'Not run'],
};

/** "6/7 passed · 1 not verified": skipped checks are never counted as passed. */
export function checksLine(c: ChecksSummary): string {
	const parts = [`${c.passed}/${c.total} passed`];
	if (c.failed) parts.push(`${c.failed} failed`);
	if (c.not_verified) parts.push(`${c.not_verified} not verified`);
	return parts.join(' · ');
}

/** The compact summary for a build row or status bar. */
export function ChecksChip({
	checks,
	onClick,
}: {
	checks: ChecksSummary | null;
	onClick?: () => void;
}) {
	if (!checks) return null;
	const tone = checks.failed ? 'bad' : checks.not_verified ? 'warn' : 'ok';
	const body = (
		<>
			<Icon name={checks.failed ? 'x' : checks.not_verified ? 'alert' : 'check'} size={11} />
			{checksLine(checks)}
		</>
	);
	return onClick ? (
		<button type="button" className={cx('rc-chip', tone)} onClick={onClick} title="Open the checks">
			{body}
		</button>
	) : (
		<span className={cx('rc-chip', tone)}>{body}</span>
	);
}

function counts(layer: CheckLayer): string {
	const c = layer.counts;
	if (!c) return '';
	const total = (c.pass ?? 0) + (c.fail ?? 0) + (c.skip ?? 0);
	if (total <= 1) return '';
	return [
		`${c.pass ?? 0} passed`,
		c.fail ? `${c.fail} failed` : '',
		c.skip ? `${c.skip} skipped` : '',
	]
		.filter(Boolean)
		.join(' · ');
}

function LayerRow({ id, layer }: { id: string; layer: CheckLayer }) {
	const failures = layer.failures ?? [];
	const [open, setOpen] = useState(false);
	const [tone, label] = STATUS[layer.status] ?? STATUS.skip;
	const proves = LAYERS.find(([k]) => k === id)?.[2];
	return (
		<li className={cx('rc-row', layer.status)}>
			<div className="rc-line">
				<span className={cx('rc-dot', layer.status)}>
					<Icon
						name={layer.status === 'pass' ? 'check' : layer.status === 'fail' ? 'x' : 'dots'}
						size={10}
						weight={3}
					/>
				</span>
				<div className="min-w-0 flex-1">
					<b>{layerName(id)}</b>
					<small>
						{layer.status === 'skip'
							? layer.reason || 'Not run'
							: layer.status === 'fail' && !failures.length
								? layer.reason || proves
								: proves}
					</small>
				</div>
				<span className="rc-ct">{counts(layer)}</span>
				<Badge tone={tone}>{label}</Badge>
				{failures.length > 0 && (
					<button
						type="button"
						className="rc-more"
						aria-expanded={open}
						onClick={() => setOpen((o) => !o)}
					>
						{open ? 'Hide' : `${failures.length} failure${failures.length === 1 ? '' : 's'}`}
					</button>
				)}
			</div>
			{open && (
				<ul className="rc-fails">
					{failures.map((f, i) => (
						<li key={f.id + i}>
							<div className="flex flex-wrap items-baseline gap-x-2">
								<b>{f.title || f.id}</b>
								{f.role && <Badge tone="line">{f.role}</Badge>}
							</div>
							<div className="mono text-[11px] text-t3">
								{f.id}
								{f.spec_path ? ` · ${f.spec_path}` : ''}
							</div>
							{f.detail && <pre className="rc-detail">{f.detail}</pre>}
						</li>
					))}
				</ul>
			)}
		</li>
	);
}

/** The run's checks: a verdict, one row per check, and the way into the full report. */
export function ChecksReport({ report }: { report: StudioReport }) {
	const [full, setFull] = useState(false);
	const layers = report.layers ?? {};
	const known = LAYERS.map(([k]) => k).filter((k) => layers[k]);
	const extra = Object.keys(layers).filter((k) => !LAYERS.some(([l]) => l === k));
	const order = [...known, ...extra];
	const failing = order.filter((k) => layers[k]?.status === 'fail');
	const notVerified = report.not_verified?.length
		? report.not_verified
		: order.filter((k) => layers[k]?.status === 'skip');
	const verdict = report.verdict || report.report?.verdict || '';
	const bad = failing.length > 0 || !report.bring_up_ok || report.frontend === false;
	const ready = !bad && !notVerified.length;
	// A paused or running build has only run some of its checks so far.
	const pending = LAYERS.map(([k]) => k).filter((k) => !layers[k]);
	const partial = pending.length > 0 && !report.html_url && !verdict;

	return (
		<div className="grid gap-3">
			<div className={cx('rc-verdict', bad ? 'bad' : partial ? 'warn' : ready ? 'ok' : 'warn')}>
				<Icon
					name={ready && !partial ? 'check' : 'alert'}
					size={15}
					className="mt-[1px] shrink-0"
				/>
				<div className="min-w-0 flex-1">
					<b>
						{partial && !bad
							? `${known.length} of ${LAYERS.length} checks have run so far`
							: ready
								? 'All checks passed'
								: bad
									? failing.length
										? `${failing.length} check${failing.length === 1 ? '' : 's'} failed`
										: !report.bring_up_ok
											? 'The app could not be brought up'
											: 'Built without a frontend'
									: 'Passed what could be checked'}
						{verdict && <span className="rc-vd">Report verdict: {verdict}</span>}
					</b>
					{failing.length > 0 && <div>Failing: {failing.map(layerName).join(', ')}.</div>}
					{report.frontend === false && (
						<div>
							No frontend was built{report.frontend_reason ? `: ${report.frontend_reason}` : ''}.
						</div>
					)}
					{notVerified.length > 0 && (
						<div>
							Not verified: {notVerified.map(layerName).join(', ')}. These checks did not run, so
							they are neither passed nor failed.
						</div>
					)}
					{partial && <div>Still to run: {pending.map(layerName).join(', ')}.</div>}
					{!!report.rounds && (
						<div>
							The agent fixed failures in {report.rounds} fix round
							{report.rounds === 1 ? '' : 's'}.
						</div>
					)}
				</div>
				{report.html_url && (
					<Button size="xs" icon="file" onClick={() => setFull(true)}>
						Open full report
					</Button>
				)}
			</div>

			<ul className="rc-list">
				{order.map((k) => (
					<LayerRow key={k} id={k} layer={layers[k] as CheckLayer} />
				))}
			</ul>

			{report.html_url && (
				<Drawer
					open={full}
					onOpenChange={setFull}
					wide
					title="Build report"
					subtitle="Generated by the build skill's test layers"
					actions={
						<a className="btn btn-s btn-xs" href={report.html_url} target="_blank" rel="noreferrer">
							<Icon name="ext" size={13} />
							Open in new tab
						</a>
					}
				>
					{/* The report is the skill's own HTML: scripts only, no access to the console. */}
					<iframe
						title="Build report"
						className="rc-frame"
						sandbox="allow-scripts"
						src={report.html_url}
					/>
				</Drawer>
			)}
		</div>
	);
}

function CopyCommand({ command }: { command: string }) {
	const [copied, setCopied] = useState(false);
	useEffect(() => {
		if (!copied) return;
		const id = setTimeout(() => setCopied(false), 1600);
		return () => clearTimeout(id);
	}, [copied]);
	const copy = async () => {
		try {
			await navigator.clipboard.writeText(command);
			setCopied(true);
		} catch {
			toast.error('Could not copy; select the command and copy it');
		}
	};
	return (
		<div className="rc-cmd">
			<code className="mono">{command}</code>
			<Button size="xs" icon={copied ? 'check' : 'copy'} onClick={copy} aria-label="Copy command">
				{copied ? 'Copied' : 'Copy'}
			</Button>
		</div>
	);
}

/**
 * The build paused for something only the user can do. Continue re-checks it on the server;
 * when the fix isn't detected the card stays and says why, per action.
 */
export function ActionNeeded({
	appId,
	runId,
	actions,
	onContinued,
}: {
	appId: string;
	runId: string;
	actions: PendingAction[];
	onContinued: () => void;
}) {
	const go = useContinueRun(appId, runId, onContinued);
	const [reasons, setReasons] = useState<Record<string, string>>({});
	const [refusal, setRefusal] = useState('');
	const [confirmSkip, setConfirmSkip] = useState(false);

	const submit = (skip: boolean) =>
		go.mutate(skip, {
			onSuccess: () => {
				setConfirmSkip(false);
				toast.success(skip ? 'Finishing without those checks' : 'Continuing the build');
			},
			onError: (err) => {
				setConfirmSkip(false);
				if (err instanceof ContinueRefused && err.actions.length) {
					setReasons(
						Object.fromEntries(
							err.actions.map((a) => [a.id, a.still_failing_reason || 'Not detected yet']),
						),
					);
					setRefusal(err.message);
				} else {
					setReasons({});
					toast.error(err.message);
				}
			},
		});

	const blocked = [...new Set(actions.flatMap((a) => a.blocks ?? []))];
	return (
		<section className="rc-act" role="alert" aria-label="Action needed">
			<div className="rc-act-h">
				<Icon name="alert" size={15} />
				<b>Action needed</b>
				<span>
					The build is paused until{' '}
					{actions.length === 1 ? 'this is done' : `these ${actions.length} are done`}. Everything
					that doesn't depend on it has already run.
				</span>
			</div>
			<ol className="rc-act-l">
				{actions.map((a) => (
					<li key={a.id}>
						<b>{a.title}</b>
						{a.detail && <p>{a.detail}</p>}
						{a.command && <CopyCommand command={a.command} />}
						{!!a.blocks?.length && (
							<div className="rc-blocks">
								Blocks:{' '}
								{a.blocks.map((b) => (
									<Badge key={b} tone="line">
										{layerName(b.replace(/^platform:/, ''))}
									</Badge>
								))}
							</div>
						)}
						{reasons[a.id] && (
							<div className="rc-still" role="status">
								<Icon name="x" size={12} weight={2.6} />
								Still not detected: {reasons[a.id]}
							</div>
						)}
					</li>
				))}
			</ol>
			{refusal && !Object.keys(reasons).length && <div className="rc-still">{refusal}</div>}
			<div className="rc-act-f">
				<Button
					size="sm"
					variant="primary"
					icon="check"
					loading={go.isPending && !confirmSkip}
					disabled={go.isPending}
					onClick={() => submit(false)}
				>
					I've done this — continue
				</Button>
				<Button size="sm" disabled={go.isPending} onClick={() => setConfirmSkip(true)}>
					Skip these checks and finish
				</Button>
			</div>
			<ConfirmModal
				open={confirmSkip}
				onOpenChange={setConfirmSkip}
				title="Finish without these checks?"
				confirmLabel="Skip and finish"
				loading={go.isPending}
				onConfirm={() => submit(true)}
			>
				<p className="text-[13px] leading-[1.55] text-t2">
					The build finishes now.{' '}
					{blocked.length
						? `${blocked.map((b) => layerName(b.replace(/^platform:/, ''))).join(', ')} will not run`
						: 'The blocked steps will not run'}{' '}
					and the report will list them as not verified, never as passed. You can build again later
					to run them.
				</p>
			</ConfirmModal>
		</section>
	);
}

export { checksOf };
