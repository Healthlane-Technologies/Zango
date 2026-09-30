import { useState } from 'react';
import {
	AVAILABILITY_REASONS,
	createScaffold,
	MAX_PROMPT_CHARS,
	useAgentAvailability,
	type Scaffold,
} from '@/api/scaffolds';
import { useApiMutation } from '@/api/hooks';
import {
	Button,
	ButtonLink,
	Card,
	CardBody,
	CardHeader,
	Field,
	Icon,
	Page,
	PageHeader,
	Skeleton,
	Textarea,
} from '@/ui';
import { Section, SourceOption, SummaryRow } from './parts';

const PLACEHOLDER =
	'e.g. a way for our clinic staff to book patient appointments and record whether the patient turned up';

// Starting points the backend can take. Only a plain description today; when the template
// list API lands, add { kind: 'template' } here and render the picker under the options.
type StartingPoint = 'brief';
const STARTING_POINTS: Array<{ kind: StartingPoint; title: string; description: string }> = [
	{
		kind: 'brief',
		title: 'Describe it',
		description: 'The agent composes the app from the Zango package catalog',
	},
];

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);

function Unavailable({ reasons }: { reasons: string[] }) {
	return (
		<div
			className="mb-5 flex items-start gap-3 rounded-[10px] border border-[#FCD34D] bg-amber-soft px-4 py-3"
			role="alert"
		>
			<span className="mt-[1px] text-amber-t">
				<Icon name="alert" />
			</span>
			<div className="min-w-0 flex-1">
				<b className="block font-[550] text-amber-t">Build with AI isn't ready on this platform</b>
				<ul className="mt-1 list-disc pl-[18px] text-amber-t">
					{reasons.map((r) => (
						<li key={r}>{AVAILABILITY_REASONS[r] ?? r}</li>
					))}
				</ul>
			</div>
			<ButtonLink to="/settings?tab=agent-mode" size="sm" icon="cog">
				Build with AI settings
			</ButtonLink>
		</div>
	);
}

/** Step one: say what to build. Hands the created scaffold to `onStarted`. */
export function NewAppForm({ onStarted }: { onStarted: (s: Scaffold) => void }) {
	const [source, setSource] = useState<StartingPoint>('brief');
	const [prompt, setPrompt] = useState('');
	const { data: availability, isLoading: checking } = useAgentAvailability();
	const create = useApiMutation({ fn: createScaffold, onSuccess: (s) => onStarted(s) });

	const blocked = !!availability && !availability.available;
	const trimmed = prompt.trim();
	const tooLong = trimmed.length > MAX_PROMPT_CHARS;
	const canStart = !blocked && !checking && !!trimmed && !tooLong && !create.isPending;
	const start = () => canStart && create.mutate(trimmed);

	return (
		<div className="flex min-h-full flex-col">
			<Page>
				<PageHeader
					title="New app"
					description="Describe what you need. The agent names and sets up the app, then agrees requirements with you before it builds anything."
				/>
				{blocked && <Unavailable reasons={availability.reasons} />}
				<div className="grid grid-cols-[minmax(0,1fr)_300px] items-start gap-7">
					<div>
						<Section n={1} title="Starting point" hint="Where the agent begins.">
							<div
								className="grid grid-cols-2 gap-[10px]"
								role="radiogroup"
								aria-label="Starting point"
							>
								{STARTING_POINTS.map((p) => (
									<SourceOption
										key={p.kind}
										selected={source === p.kind}
										title={p.title}
										description={p.description}
										onSelect={() => setSource(p.kind)}
									/>
								))}
							</div>
						</Section>
						<Section
							n={2}
							title="Requirements"
							hint="Plain language, the way you'd explain it to a colleague: who uses it, the steps, what gets recorded."
						>
							<Field
								label="Describe the app"
								error={
									tooLong
										? `Keep it under ${MAX_PROMPT_CHARS.toLocaleString()} characters.`
										: undefined
								}
								hint={`${isMac ? '⌘' : 'Ctrl'} + Enter to start. The agent asks follow-up questions, so a sentence or two is enough.`}
							>
								{(p) => (
									<Textarea
										{...p}
										rows={7}
										autoFocus
										value={prompt}
										placeholder={PLACEHOLDER}
										disabled={blocked || create.isPending}
										onChange={(e) => setPrompt(e.target.value)}
										onKeyDown={(e) => {
											if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
												e.preventDefault();
												start();
											}
										}}
									/>
								)}
							</Field>
						</Section>
					</div>
					<aside className="sticky top-0">
						<Card>
							<CardHeader title="Summary" />
							<CardBody>
								<SummaryRow label="Starting point">Description</SummaryRow>
								<SummaryRow label="App name">
									<span className="font-normal text-t3">Chosen by the agent</span>
								</SummaryRow>
								<SummaryRow label="Analyst model">
									{checking ? <Skeleton width={90} /> : (availability?.config.analyst_model ?? '—')}
								</SummaryRow>
								<SummaryRow label="First step">Requirements chat</SummaryRow>
								<div className="divider my-3" />
								<p className="text-[12px] text-t3">
									Creating the app starts an agent conversation. Nothing is built until you approve
									the plan.
								</p>
							</CardBody>
						</Card>
					</aside>
				</div>
			</Page>
			<div className="sticky bottom-0 mt-auto flex justify-end gap-2 border-t border-border bg-[rgba(255,255,255,.94)] px-8 py-3 backdrop-blur">
				<ButtonLink to="/apps">Cancel</ButtonLink>
				<Button
					variant="primary"
					icon="agent"
					disabled={!canStart}
					loading={create.isPending}
					onClick={start}
				>
					Create app and start agent
				</Button>
			</div>
		</div>
	);
}
