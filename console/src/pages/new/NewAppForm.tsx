import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
	AVAILABILITY_REASONS,
	createScaffold,
	MAX_PROMPT_CHARS,
	useAgentAvailability,
	type Scaffold,
} from '@/api/scaffolds';
import { useApiMutation } from '@/api/hooks';
import { useTemplate, useTemplates } from '@/api/templates';
import {
	Button,
	ButtonLink,
	Card,
	CardBody,
	CardHeader,
	Field,
	Icon,
	Input,
	Page,
	PageHeader,
	Skeleton,
	Textarea,
} from '@/ui';
import { DocumentDrop, DRAFT_GUIDANCE, ReferencePicker } from './intake';
import { Section, SourceOption, SummaryRow } from './parts';
import { TemplateIcon } from '../workspace/templates/parts';
import { TemplatePicker } from './TemplatePicker';

const PLACEHOLDER =
	'e.g. a way for our clinic staff to book patient appointments and record whether the patient turned up';

// Starting points the backend can take: a plain description, or a published template
// (the scaffold then binds the app to it and the analyst runs that template's interview).
type StartingPoint = 'brief' | 'template';
const STARTING_POINTS: Array<{ kind: StartingPoint; title: string; description: string }> = [
	{
		kind: 'template',
		title: 'From a template',
		description: 'Start from a proven program',
	},
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
	const [params] = useSearchParams();
	const preselected = params.get('template');
	const [source, setSource] = useState<StartingPoint>(preselected ? 'template' : 'brief');
	const [templateSlug, setTemplateSlug] = useState<string | null>(preselected);
	// Arrived with a template already chosen: show it as a locked card, not a list to find it in.
	const [changing, setChanging] = useState(false);
	// Deep links from the template pages: a description to start from, an example journey.
	const [prompt, setPrompt] = useState(() => params.get('prompt') ?? '');
	const [files, setFiles] = useState<File[]>([]);
	const [reference, setReference] = useState(() => params.get('reference') ?? '');
	const { data: availability, isLoading: checking } = useAgentAvailability();
	const templates = useTemplates();
	const create = useApiMutation({ fn: createScaffold, onSuccess: (s) => onStarted(s) });

	const template =
		source === 'template' ? (templates.data?.find((t) => t.slug === templateSlug) ?? null) : null;
	// Template mode: the app opens on the template's own preview.
	const direct = template?.launch === 'direct';
	// Any template: the creator only names the app. No brief.
	const fromTemplate = source === 'template' && !!template;
	const [appName, setAppName] = useState('');
	const name = appName.trim();
	// References come with the template's detail, not the catalogue list.
	const detail = useTemplate(template?.slug);
	const references = detail.data?.references;
	// A different template's examples don't apply (the deep-linked one survives first load).
	const shownSlug = useRef<string | undefined>(undefined);
	useEffect(() => {
		if (shownSlug.current && template?.slug !== shownSlug.current) setReference('');
		shownSlug.current = template?.slug;
	}, [template?.slug]);
	// A deep link to a template that isn't published (any more) falls back to the first one.
	useEffect(() => {
		if (source !== 'template' || !templates.data?.length) return;
		if (!templateSlug || !templates.data.some((t) => t.slug === templateSlug)) {
			setTemplateSlug(templates.data[0].slug);
		}
	}, [source, templates.data, templateSlug]);

	const locked = !!preselected && !changing;

	const blocked = !!availability && !availability.available;
	const trimmed = prompt.trim();
	const tooLong = trimmed.length > MAX_PROMPT_CHARS;
	// A template draft needs material to work from: a detailed brief, documents, or both.
	const hasInput = fromTemplate
		? true
		: source === 'template'
			? !!template && (!!trimmed || files.length > 0)
			: !!trimmed;
	// From scratch the app is written in the generic template's spec, so documents
	// (an SOP, an RFP) are welcome there too — alongside a sentence or two.
	const canStart = !blocked && !checking && hasInput && !tooLong && !create.isPending;
	const start = () =>
		canStart &&
		create.mutate(
			fromTemplate && template
				? { template_slug: template.slug, app_name: name || undefined }
				: source === 'template' && template
				? {
						prompt: trimmed || undefined,
						template_slug: template.slug,
						reference: reference || undefined,
						documents: files,
					}
				: { prompt: trimmed, documents: files },
		);

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
							{locked ? (
								<Section n={1} title="Template" hint="You picked this from the gallery.">
									{template ? (
										<div className="tprow on">
											<TemplateIcon template={template} size={28} />
											<span className="mid">
												<b>{template.name}</b>
												<small>{template.one_liner || template.catalogue.description}</small>
											</span>
											<span className="meta">
												<span className="mono">v{template.version}</span>
												<br />
												<button
													type="button"
													className="text-[12px] text-accent underline"
													disabled={create.isPending}
													onClick={() => setChanging(true)}
												>
													Change
												</button>
											</span>
										</div>
									) : templates.error ? (
										<TemplatePicker
											templates={templates.data}
											loading={false}
											error={templates.error}
											onRetry={() => templates.refetch()}
											value={templateSlug}
											onChange={setTemplateSlug}
										/>
									) : (
										<div className="tprow">
											<Skeleton width={28} height={28} />
											<span className="mid grid gap-1.5">
												<Skeleton width="45%" />
												<Skeleton width="75%" />
											</span>
										</div>
									)}
								</Section>
							) : (
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
										disabled={create.isPending}
										onSelect={() => setSource(p.kind)}
									/>
								))}
							</div>
							{source === 'template' && (
								<TemplatePicker
									templates={templates.data}
									loading={templates.isLoading}
									error={templates.error}
									onRetry={() => templates.refetch()}
									value={templateSlug}
									onChange={setTemplateSlug}
									disabled={create.isPending}
								/>
							)}
						</Section>
							)}
						{fromTemplate && template && (
							<Section
								n={2}
								title="Name"
								hint={
									direct
										? "The app opens on the template's preview with demo data. Change anything in the chat (flows, data, screens, the look), then build it."
										: 'The agent starts from the template and agrees the requirements with you in the chat.'
								}
							>
								<Field label="App name (optional)" hint="Leave it empty and the agent suggests a short name.">
									{(p) => (
										<Input
											{...p}
											value={appName}
											placeholder="Chosen by the agent"
											maxLength={120}
											disabled={blocked || create.isPending}
											onChange={(e) => setAppName(e.target.value)}
											onKeyDown={(e) => {
												if (e.key === 'Enter') {
													e.preventDefault();
													start();
												}
											}}
										/>
									)}
								</Field>
								{!!template.catalogue.gives_you?.length && (
									<div className="mt-4">
										<div className="mb-2 text-[12.5px] font-[550] text-t2">What's included</div>
										<ul className="grid gap-[6px] text-[13px] text-t2">
											{template.catalogue.gives_you.map((g) => (
												<li key={g} className="flex items-start gap-2">
													<span className="mt-[2px] text-green-t">
														<Icon name="check" />
													</span>
													{g}
												</li>
											))}
										</ul>
									</div>
								)}
							</Section>
						)}
						{!fromTemplate && (
						<Section
							n={2}
							title="Requirements"
							hint={
								source === 'template'
									? 'The agent drafts the whole journey from this in one pass and flags what it had to infer. Describe the program in detail, upload documents, or both.'
									: "Plain language, the way you'd explain it to a colleague: who uses it, the steps, what gets recorded."
							}
						>
							<Field
								label={source === 'template' ? 'Describe the program' : 'Describe the app'}
								error={
									tooLong
										? `Keep it under ${MAX_PROMPT_CHARS.toLocaleString()} characters.`
										: undefined
								}
								hint={
									source === 'template'
										? `${DRAFT_GUIDANCE} ${isMac ? '⌘' : 'Ctrl'} + Enter to start.`
										: `${isMac ? '⌘' : 'Ctrl'} + Enter to start. The agent asks follow-up questions, so a sentence or two is enough.`
								}
							>
								{(p) => (
									<Textarea
										{...p}
										rows={source === 'template' ? 9 : 7}
										autoFocus={source === 'brief'}
										value={prompt}
										placeholder={
											source === 'template'
												? template?.catalogue.app_prompt_prefill || PLACEHOLDER
												: PLACEHOLDER
										}
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
							{source !== 'template' && (
								<div className="mt-4">
									<DocumentDrop
										files={files}
										onChange={setFiles}
										disabled={blocked || create.isPending}
									/>
								</div>
							)}
							{source === 'template' && (
								<div className="mt-4 grid gap-4">
									<DocumentDrop
										files={files}
										onChange={setFiles}
										disabled={blocked || create.isPending}
									/>
									<ReferencePicker
										references={references}
										value={reference}
										onChange={setReference}
										disabled={create.isPending}
									/>
								</div>
							)}
						</Section>
						)}
					</div>
					<aside className="sticky top-0">
						<Card>
							<CardHeader title="Summary" />
							<CardBody>
								<SummaryRow label="Starting point">
									{source === 'template' ? 'Template' : 'Description'}
								</SummaryRow>
								{source === 'template' && (
									<>
										<SummaryRow label="Template">
											{template ? (
												<>
													{template.name} <span className="mono text-t3">v{template.version}</span>
												</>
											) : (
												<span className="font-normal text-t3">Pick one</span>
											)}
										</SummaryRow>
										<SummaryRow label="Packages">
											{template ? (template.catalogue.packages?.length ?? 0) : '—'}
										</SummaryRow>
										<SummaryRow label="Workflows included">
											{template ? (template.catalogue.workflows?.length ?? 0) : '—'}
										</SummaryRow>
										{!fromTemplate && <SummaryRow label="Documents">{files.length || '—'}</SummaryRow>}
										{!fromTemplate && !!references?.length && (
											<SummaryRow label="Start from">
												{references.find((r) => r.id === reference)?.title ?? (
													<span className="font-normal text-t3">Agent's choice</span>
												)}
											</SummaryRow>
										)}
									</>
								)}
								<SummaryRow label="App name">
									{fromTemplate ? (
										name || <span className="font-normal text-t3">Chosen by the agent</span>
									) : (
										<span className="font-normal text-t3">Chosen by the agent</span>
									)}
								</SummaryRow>
								<SummaryRow label="Analyst model">
									{checking ? <Skeleton width={90} /> : (availability?.config.analyst_model ?? '—')}
								</SummaryRow>
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
					{direct ? 'Create & open' : 'Create app and start agent'}
				</Button>
			</div>
		</div>
	);
}
