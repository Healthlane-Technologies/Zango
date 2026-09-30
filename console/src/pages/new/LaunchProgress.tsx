import { useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { appKeys } from '@/api/apps';
import { handOffScaffold, scaffoldKeys, useScaffold, type Scaffold } from '@/api/scaffolds';
import {
	Button,
	ButtonLink,
	Card,
	ErrorState,
	Icon,
	Page,
	PageHeader,
	Skeleton,
	TemplateBadge,
	toast,
} from '@/ui';
import { Step, type StepState } from './parts';

// The app is already built when the hand-off runs, so a transient failure is worth
// retrying — but a persistent one has to stop and say so.
const MAX_HANDOFF_ATTEMPTS = 4;

const agentPath = (appUuid: string) => `/apps/${appUuid}/agent`;

function steps(
	s: Scaffold,
	handingOff: boolean,
	stuck: boolean,
): Array<[StepState, string, string?]> {
	const failed = s.status === 'failed';
	const naming: StepState = s.app_name ? 'done' : failed ? 'failed' : 'running';
	const creating: StepState =
		s.app_state === 'failed' || (failed && s.app_name)
			? 'failed'
			: s.app_state === 'ready'
				? 'done'
				: s.app_name
					? 'running'
					: 'pending';
	const opening: StepState = s.requirement_uuid
		? 'done'
		: creating !== 'done'
			? 'pending'
			: stuck && !handingOff
				? 'failed'
				: 'running';
	return [
		[naming, 'Choosing a name', s.app_name || undefined],
		[creating, s.app_label ? `Creating ${s.app_label}` : 'Creating the app'],
		[opening, 'Opening the requirements conversation'],
	];
}

/** Step two: follow the scaffold until the app exists, then hand over to its Agent tab. */
export function LaunchProgress({ uuid, onStartOver }: { uuid: string; onStartOver: () => void }) {
	const navigate = useNavigate();
	const qc = useQueryClient();
	const [failures, setFailures] = useState(0);
	const failuresRef = useRef(0);
	const stuck = failures >= MAX_HANDOFF_ATTEMPTS;
	const { data: scaffold, error, refetch, dataUpdatedAt } = useScaffold(uuid, { paused: stuck });

	// A POST, and polling would otherwise fire it again while the first is in flight.
	const inFlight = useRef(false);
	const handOff = useMutation({
		mutationFn: handOffScaffold,
		onSettled: () => {
			inFlight.current = false;
		},
		onSuccess: (s) => {
			qc.setQueryData(scaffoldKeys.detail(uuid), s);
		},
		onError: (err: Error) => {
			// One toast per run of failures, not one per poll.
			if (failuresRef.current === 0)
				toast.error(`Couldn't open the conversation: ${err.message}. Retrying…`);
			failuresRef.current += 1;
			setFailures(failuresRef.current);
		},
	});

	const appUuid = scaffold?.app_uuid;
	// Surface the new tenant in the Apps list and sidebar count as soon as it exists.
	useEffect(() => {
		if (appUuid) qc.invalidateQueries({ queryKey: appKeys.all });
	}, [appUuid, qc]);

	useEffect(() => {
		if (!scaffold) return;
		if (scaffold.requirement_uuid && scaffold.app_uuid) {
			qc.invalidateQueries({ queryKey: appKeys.all });
			navigate(agentPath(scaffold.app_uuid), { replace: true });
			return;
		}
		if (
			scaffold.app_state === 'ready' &&
			scaffold.status !== 'failed' &&
			!stuck &&
			!inFlight.current
		) {
			inFlight.current = true;
			handOff.mutate(scaffold.uuid);
		}
		// Once per poll, like the classic panel: a failed hand-off is retried on the next poll,
		// not immediately. "Try again" resets the budget, which resumes polling.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [dataUpdatedAt]);

	if (error && !scaffold) {
		return (
			<Page>
				<PageHeader title="New app" />
				<div className="card">
					<ErrorState error={error} onRetry={() => refetch()} />
					<div className="-mt-6 flex justify-center pb-8">
						<Button size="sm" onClick={onStartOver}>
							Start over
						</Button>
					</div>
				</div>
			</Page>
		);
	}

	const failed = !!scaffold && (scaffold.status === 'failed' || scaffold.app_state === 'failed');
	const title = !scaffold
		? 'Setting up your app'
		: failed
			? 'The app couldn’t be set up'
			: scaffold.app_state === 'ready'
				? `${scaffold.app_label || 'Your app'} is ready`
				: `Setting up ${scaffold.app_label || 'your app'}`;

	return (
		<Page>
			<PageHeader
				title={title}
				description={
					failed
						? 'Nothing was left half-built, so you can try again.'
						: stuck
							? 'Your app is safe; only opening the conversation failed.'
							: 'This takes a minute. You can leave this page; the app keeps building.'
				}
			/>
			<Card className="max-w-[720px]">
				<div className="card-b">
					<div className="mb-4 flex gap-3">
						<span className="grid h-7 w-7 shrink-0 place-items-center rounded-[7px] bg-accent-soft text-accent-t">
							<Icon name="file" />
						</span>
						<div className="min-w-0">
							{scaffold?.template && (
								<div className="mb-2">
									<div className="text-[12px] text-t3">Template</div>
									<TemplateBadge template={scaffold.template} />
								</div>
							)}
							<div className="text-[12px] text-t3">Your brief</div>
							{scaffold ? (
								<p className="whitespace-pre-wrap text-t1">{scaffold.prompt}</p>
							) : (
								<Skeleton width="70%" height={14} style={{ marginTop: 4 }} />
							)}
						</div>
					</div>
					<ul className="border-t border-border-soft pt-2" aria-live="polite">
						{scaffold
							? steps(scaffold, handOff.isPending, stuck).map(([state, label, detail]) => (
									<Step
										key={label.startsWith('Creating') ? 'creating' : label}
										state={state}
										label={label}
										detail={detail}
									/>
								))
							: [0, 1, 2].map((i) => (
									<li key={i} className="py-[6px]">
										<Skeleton width={160 + i * 30} />
									</li>
								))}
					</ul>
					{scaffold?.app_description && !failed && (
						<p className="mt-3 border-t border-border-soft pt-3 text-t3">
							{scaffold.app_description}
						</p>
					)}
					{(failed || stuck) && (
						<div
							className="mt-3 rounded-[7px] bg-red-soft px-3 py-2 text-[12.5px] text-red-t"
							role="alert"
						>
							{failed
								? scaffold?.error_message ||
									'The app could not be created. Check the platform logs, then try again.'
								: `${scaffold?.app_label || 'Your app'} was created, but the conversation couldn’t be opened. Try again, or open the app and start from its Agent tab.`}
						</div>
					)}
				</div>
				{(failed || (stuck && appUuid)) && (
					<div className="flex justify-end gap-2 border-t border-border px-4 py-3">
						{failed ? (
							<Button variant="primary" onClick={onStartOver}>
								Start over
							</Button>
						) : (
							<>
								<ButtonLink to={agentPath(appUuid!)}>Open the app</ButtonLink>
								<Button
									variant="primary"
									onClick={() => {
										failuresRef.current = 0;
										setFailures(0);
									}}
								>
									Try again
								</Button>
							</>
						)}
					</div>
				)}
			</Card>
		</Page>
	);
}
