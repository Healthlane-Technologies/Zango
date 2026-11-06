import { useMemo, useState, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
	aiKeys,
	createAgent,
	money,
	testAgent,
	updateAgent,
	useAgent,
	useClearSession,
	usePromptOptions,
	useProviders,
	useSession,
	useSessions,
	useTools,
	type Agent,
	type AgentInput,
	type AgentTestResult,
	type OutputSchema,
	type PromptType,
} from '@/api/ai';
import {
	Button,
	CodeBlock,
	cx,
	Drawer,
	EmptyState,
	ErrorState,
	Field,
	FieldGroup,
	Input,
	KeyValues,
	SectionTitle,
	Segmented,
	Select,
	Skeleton,
	SwitchField,
	Tabs,
	Textarea,
	toast,
} from '@/ui';
import { CreatePromptModal } from './PromptModals';
import { EnabledBadge, fmtDate, PromptText, SafetyBadge, serviceLabel } from './parts';

type Tab = 'settings' | 'test' | 'sessions' | 'usage';

const NAME_RE = /^[a-z0-9-]+$/;

const EMPTY: AgentInput = {
	name: '',
	description: '',
	provider_id: 0,
	model: '',
	system_prompt_name: '',
	user_prompt_name: '',
	temperature: 0.7,
	max_tokens: 4096,
	timeout_seconds: 30,
	output_schema: 'Text',
	output_json_schema: null,
	tools: [],
	short_term_memory: false,
	short_term_memory_max_messages: 20,
};

const toInput = (a: Agent): AgentInput => ({
	name: a.name,
	description: a.description,
	provider_id: a.provider ?? 0,
	model: a.model ?? '',
	system_prompt_name: a.system_prompt_name ?? '',
	user_prompt_name: a.user_prompt_name ?? '',
	temperature: a.temperature,
	max_tokens: a.max_tokens,
	timeout_seconds: a.timeout_seconds,
	output_schema: a.output_schema,
	output_json_schema: a.output_json_schema,
	tools: a.tools,
	short_term_memory: a.short_term_memory,
	short_term_memory_max_messages: a.short_term_memory_max_messages,
});

/** How app code calls this agent; mirrors what the classic panel shows. */
export function usageSnippet(a: {
	name: string;
	user_prompt_name: string | null;
	system_prompt_name: string | null;
	short_term_memory: boolean;
}) {
	const sys = a.system_prompt_name ? '\n    system_variables={...},  # optional' : '';
	const lines = ['from zango.ai import get_agent', '', `agent = get_agent("${a.name || 'agent-name'}")`];
	if (a.short_term_memory) {
		lines.push(
			`r = agent.run(variables={"message": "Hello!"}${sys ? ',' : ''}${sys})`,
			'session_id = r.session_id',
			'r = agent.run(variables={...}, session_id=session_id)',
		);
	} else if (a.user_prompt_name) {
		lines.push(`r = agent.run(variables={...}${sys ? ',' : ''}${sys})`);
	} else {
		lines.push(`r = agent.run(input="Your message here"${sys ? ',' : ''}${sys})`);
	}
	lines.push('r.content  # r.parsed_content for JSON output');
	return lines.join('\n');
}

export function AgentDrawer({
	appId,
	agentId,
	onClose,
	onCreated,
}: {
	appId: string;
	agentId: number | null;
	onClose: () => void;
	onCreated: (id: number) => void;
}) {
	const { data: agent, isLoading, error, refetch } = useAgent(appId, agentId);
	const [tab, setTab] = useState<Tab>('settings');

	if (agentId != null && !agent) {
		return (
			<Drawer open onOpenChange={(o) => !o && onClose()} title="Agent" wide>
				{isLoading ? (
					<div className="grid gap-3">
						{[0, 1, 2, 3].map((i) => (
							<Skeleton key={i} height={36} />
						))}
					</div>
				) : (
					error && <ErrorState error={error} onRetry={() => refetch()} />
				)}
			</Drawer>
		);
	}

	if (!agent) return <AgentForm appId={appId} onClose={onClose} onSaved={onCreated} />;

	const tabs = [
		{ value: 'settings' as const, label: 'Settings' },
		{ value: 'test' as const, label: 'Test' },
		...(agent.short_term_memory
			? [{ value: 'sessions' as const, label: 'Sessions', count: agent.session_count }]
			: []),
		{ value: 'usage' as const, label: 'Usage' },
	];

	return tab === 'settings' ? (
		<AgentForm
			key={agent.id}
			appId={appId}
			agent={agent}
			onClose={onClose}
			onSaved={() => undefined}
			header={<Tabs className="-mx-5 -mt-5 mb-5" items={tabs} value={tab} onChange={setTab} />}
		/>
	) : (
		<Drawer
			open
			wide
			onOpenChange={(o) => !o && onClose()}
			title={<span className="mono">{agent.name}</span>}
			subtitle={<AgentSubtitle agent={agent} />}
		>
			<Tabs className="-mx-5 -mt-5 mb-5" items={tabs} value={tab} onChange={setTab} />
			{tab === 'test' && <AgentTest appId={appId} agent={agent} />}
			{tab === 'sessions' && <Sessions appId={appId} agent={agent} />}
			{tab === 'usage' && <Usage agent={agent} />}
		</Drawer>
	);
}

function AgentSubtitle({ agent }: { agent: Agent }) {
	return (
		<span className="inline-flex items-center gap-2">
			<EnabledBadge enabled={agent.is_enabled} />
			{agent.provider_name
				? `${agent.provider_name} · ${agent.model}`
				: 'No provider — pick one in Settings'}
		</span>
	);
}

/* ---------- settings form ---------- */

function AgentForm({
	appId,
	agent,
	onClose,
	onSaved,
	header,
}: {
	appId: string;
	agent?: Agent;
	onClose: () => void;
	onSaved: (id: number) => void;
	header?: ReactNode;
}) {
	const qc = useQueryClient();
	const providers = useProviders(appId);
	const tools = useTools(appId, { search: '', section: '', safety: '', isActive: 'true' });

	const [v, setV] = useState<AgentInput>(() => (agent ? toInput(agent) : EMPTY));
	const [schemaText, setSchemaText] = useState(() =>
		agent?.output_json_schema ? JSON.stringify(agent.output_json_schema, null, 2) : '',
	);
	const [saving, setSaving] = useState(false);
	const set = <K extends keyof AgentInput>(k: K, val: AgentInput[K]) =>
		setV((cur) => ({ ...cur, [k]: val }));

	const enabledProviders = (providers.data ?? []).filter(
		(p) => p.is_enabled || p.id === v.provider_id,
	);
	const provider = providers.data?.find((p) => p.id === v.provider_id);
	const modelOptions = useMemo(() => {
		const ids = (provider?.enabled_models ?? []).filter((m) => m.is_enabled).map((m) => m.model_id);
		if (provider?.default_model && !ids.includes(provider.default_model))
			ids.unshift(provider.default_model);
		if (v.model && !ids.includes(v.model)) ids.unshift(v.model);
		return ids;
	}, [provider, v.model]);

	const schema = useMemo((): { value: Record<string, unknown> | null; error?: string } => {
		if (v.output_schema !== 'JSON') return { value: null };
		if (!schemaText.trim()) return { value: null, error: 'A JSON schema is required for JSON output' };
		try {
			const parsed: unknown = JSON.parse(schemaText);
			if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed))
				return { value: null, error: 'Must be a JSON object' };
			if (!('type' in parsed)) return { value: null, error: 'The schema needs a "type" field' };
			return { value: parsed as Record<string, unknown> };
		} catch {
			return { value: null, error: 'Invalid JSON' };
		}
	}, [v.output_schema, schemaText]);

	const errors = {
		name: !v.name
			? 'Required'
			: !NAME_RE.test(v.name)
				? 'Lowercase letters, numbers and hyphens only'
				: undefined,
		provider: !v.provider_id ? 'Pick a provider' : undefined,
		model: !v.model ? 'Pick a model' : undefined,
		temperature: v.temperature < 0 || v.temperature > 2 ? 'Between 0 and 2' : undefined,
		max_tokens: v.max_tokens < 1 || v.max_tokens > 128000 ? 'Between 1 and 128,000' : undefined,
		timeout: v.timeout_seconds < 1 ? 'At least 1 second' : undefined,
		memory:
			v.short_term_memory_max_messages < 1 || v.short_term_memory_max_messages > 200
				? 'Between 1 and 200'
				: undefined,
	};
	const valid = !Object.values(errors).some(Boolean) && !schema.error;

	const save = async () => {
		setSaving(true);
		const body: AgentInput = { ...v, output_json_schema: schema.value };
		try {
			if (agent) {
				await updateAgent(appId, agent.id, body);
				toast.success(`${v.name} saved`);
				onSaved(agent.id);
			} else {
				const r = await createAgent(appId, body);
				toast.success(`${v.name} created`);
				onSaved(r.agent_id);
			}
			await qc.invalidateQueries({ queryKey: aiKeys.agents(appId) });
			await qc.invalidateQueries({ queryKey: aiKeys.prompts(appId) });
		} catch (err) {
			toast.error(err instanceof Error ? err.message : String(err));
		} finally {
			setSaving(false);
		}
	};

	const dirty = !agent || JSON.stringify({ ...v, output_json_schema: schema.value }) !== JSON.stringify(toInput(agent));

	return (
		<Drawer
			open
			wide
			onOpenChange={(o) => !o && onClose()}
			title={agent ? <span className="mono">{agent.name}</span> : 'New agent'}
			subtitle={agent ? <AgentSubtitle agent={agent} /> : 'App code runs it with get_agent("name").run(...)'}
			footer={
				<>
					<Button onClick={onClose}>{agent ? 'Close' : 'Cancel'}</Button>
					<Button
						variant="primary"
						disabled={!valid || !dirty}
						loading={saving}
						onClick={save}
					>
						{agent ? 'Save' : 'Create agent'}
					</Button>
				</>
			}
		>
			{header}
			<SectionTitle>Identity</SectionTitle>
			<div className="grid gap-3">
				<Field
					label="Name"
					error={v.name ? errors.name : undefined}
					hint={
						<>
							Used in code: <span className="mono">get_agent("{v.name || 'name'}")</span>
						</>
					}
				>
					{(p) => (
						<Input
							{...p}
							className="mono"
							value={v.name}
							placeholder="e.g. triage-request"
							onChange={(e) => set('name', e.target.value)}
						/>
					)}
				</Field>
				<Field label="Description">
					{(p) => (
						<Textarea
							{...p}
							rows={2}
							value={v.description}
							placeholder="What this agent does and when it runs"
							onChange={(e) => set('description', e.target.value)}
						/>
					)}
				</Field>
			</div>

			<SectionTitle>Model</SectionTitle>
			{providers.data && !enabledProviders.length ? (
				<p className="rounded-lg border border-amber bg-amber-soft px-3 py-2 text-[12.5px] text-amber-t">
					No enabled providers. Add one on the Providers tab first.
				</p>
			) : (
				<div className="grid grid-cols-2 gap-3">
					<Field label="Provider" error={agent ? errors.provider : undefined}>
						{(p) => (
							<Select
								{...p}
								value={v.provider_id || ''}
								onChange={(e) => {
									const id = Number(e.target.value);
									const next = providers.data?.find((x) => x.id === id);
									setV((cur) => ({ ...cur, provider_id: id, model: next?.default_model ?? '' }));
								}}
							>
								<option value="">Choose a provider</option>
								{enabledProviders.map((x) => (
									<option key={x.id} value={x.id}>
										{x.name} · {serviceLabel(x.provider_slug)}
										{!x.is_enabled ? ' (disabled)' : ''}
									</option>
								))}
							</Select>
						)}
					</Field>
					<Field label="Model" error={agent && v.provider_id ? errors.model : undefined}>
						{(p) => (
							<Select
								{...p}
								className="mono"
								disabled={!v.provider_id}
								value={v.model}
								onChange={(e) => set('model', e.target.value)}
							>
								{!v.model && <option value="">Choose a model</option>}
								{modelOptions.map((m) => (
									<option key={m} value={m}>
										{m}
										{m === provider?.default_model ? ' (provider default)' : ''}
									</option>
								))}
							</Select>
						)}
					</Field>
				</div>
			)}
			<div className="mt-3 grid grid-cols-3 gap-3">
				<Field label="Temperature" hint="0 = consistent, 2 = creative" error={errors.temperature}>
					{(p) => (
						<Input
							{...p}
							type="number"
							step={0.1}
							min={0}
							max={2}
							value={v.temperature}
							onChange={(e) => set('temperature', Number(e.target.value))}
						/>
					)}
				</Field>
				<Field label="Max tokens" hint="Longest answer" error={errors.max_tokens}>
					{(p) => (
						<Input
							{...p}
							type="number"
							min={1}
							value={v.max_tokens}
							onChange={(e) => set('max_tokens', Number(e.target.value))}
						/>
					)}
				</Field>
				<Field label="Timeout (s)" hint="Per call" error={errors.timeout}>
					{(p) => (
						<Input
							{...p}
							type="number"
							min={1}
							value={v.timeout_seconds}
							onChange={(e) => set('timeout_seconds', Number(e.target.value))}
						/>
					)}
				</Field>
			</div>

			<SectionTitle>Prompts</SectionTitle>
			<div className="grid gap-4">
				<PromptPicker
					appId={appId}
					type="system"
					value={v.system_prompt_name}
					onChange={(n) => set('system_prompt_name', n)}
				/>
				<PromptPicker
					appId={appId}
					type="user"
					value={v.user_prompt_name}
					onChange={(n) => set('user_prompt_name', n)}
				/>
			</div>

			<SectionTitle>Output</SectionTitle>
			<Segmented<OutputSchema>
				label="Output format"
				value={v.output_schema}
				onChange={(o) => set('output_schema', o)}
				options={[
					{ value: 'Text', label: 'Text' },
					{ value: 'Markdown', label: 'Markdown' },
					{ value: 'JSON', label: 'JSON' },
				]}
			/>
			{v.output_schema === 'JSON' && (
				<div className="mt-3">
					<Field
						label="JSON schema"
						error={schemaText.trim() ? schema.error : undefined}
						hint="The model's answer is constrained to this schema; code reads it as r.parsed_content."
					>
						{(p) => (
							<Textarea
								{...p}
								className="mono"
								rows={8}
								spellCheck={false}
								value={schemaText}
								placeholder={'{\n  "type": "object",\n  "properties": { "category": { "type": "string" } },\n  "required": ["category"]\n}'}
								onChange={(e) => setSchemaText(e.target.value)}
							/>
						)}
					</Field>
				</div>
			)}

			<SectionTitle
				action={<span className="text-[12px] text-t3">{v.tools.length} selected</span>}
			>
				Tools
			</SectionTitle>
			{tools.isLoading ? (
				<Skeleton height={60} />
			) : tools.data?.tools.records.length ? (
				<div className="max-h-[240px] overflow-auto rounded-lg border border-border">
					{tools.data.tools.records.map((t) => {
						const on = v.tools.includes(t.name);
						return (
							<label
								key={t.id}
								className={cx(
									'flex cursor-pointer items-start gap-3 border-b border-border-soft px-3 py-2 last:border-b-0 hover:bg-hover',
									on && 'bg-accent-soft',
								)}
							>
								<input
									type="checkbox"
									className="mt-1"
									checked={on}
									onChange={(e) =>
										set(
											'tools',
											e.target.checked ? [...v.tools, t.name] : v.tools.filter((x) => x !== t.name),
										)
									}
								/>
								<span className="min-w-0 flex-1">
									<span className="flex items-center gap-2">
										<b className="mono text-[12.5px]">{t.name}</b>
										<SafetyBadge safety={t.safety} />
										<span className="ml-auto text-[11.5px] text-t3">{t.section}</span>
									</span>
									<span className="block truncate text-[12px] text-t3">{t.description}</span>
								</span>
							</label>
						);
					})}
				</div>
			) : (
				<p className="text-[12.5px] text-t3">
					No tools registered. Define functions with <span className="mono">@tool</span> in the
					app's <span className="mono">tools.py</span>, then sync them on the Tools tab.
				</p>
			)}
			{v.tools.some((n) => !tools.data?.tools.records.some((t) => t.name === n)) && tools.data && (
				<p className="mt-2 text-[12px] text-amber-t">
					Not found in the active tools:{' '}
					<span className="mono">
						{v.tools.filter((n) => !tools.data?.tools.records.some((t) => t.name === n)).join(', ')}
					</span>
				</p>
			)}

			<SectionTitle>Memory</SectionTitle>
			<SwitchField
				checked={v.short_term_memory}
				onChange={(on) => set('short_term_memory', on)}
				label="Conversation history"
				hint="Calls that pass the same session_id get the last few exchanges as context."
			/>
			{v.short_term_memory && (
				<div className="mt-3 max-w-[220px]">
					<Field label="Window (pairs)" hint="Max 200" error={errors.memory}>
						{(p) => (
							<Input
								{...p}
								type="number"
								min={1}
								max={200}
								value={v.short_term_memory_max_messages}
								onChange={(e) => set('short_term_memory_max_messages', Number(e.target.value))}
							/>
						)}
					</Field>
				</div>
			)}

			<SectionTitle>Use in code</SectionTitle>
			<CodeBlock>{usageSnippet(v)}</CodeBlock>
		</Drawer>
	);
}

function PromptPicker({
	appId,
	type,
	value,
	onChange,
}: {
	appId: string;
	type: PromptType;
	value: string;
	onChange: (name: string) => void;
}) {
	const { data } = usePromptOptions(appId, type);
	const [preview, setPreview] = useState(false);
	const [creating, setCreating] = useState(false);
	const selected = data?.find((p) => p.name === value);
	const label = type === 'system' ? 'System prompt' : 'User prompt';
	const hint =
		type === 'system'
			? 'Sets the role and rules. Sent as the system message on every call.'
			: 'Template for the message. {{variables}} are filled from agent.run(variables={...}).';

	return (
		<FieldGroup label={label} hint={hint}>
			<div className="flex gap-2">
				<Select
					aria-label={label}
					className="mono flex-1"
					value={value}
					onChange={(e) => onChange(e.target.value)}
				>
					<option value="">None</option>
					{value && !selected && data && <option value={value}>{value} (not found)</option>}
					{data?.map((p) => (
						<option key={p.id} value={p.name}>
							{p.name}
							{p.active_version_number ? ` · v${p.active_version_number}` : ' · no live version'}
						</option>
					))}
				</Select>
				{selected?.active_version && (
					<Button size="sm" onClick={() => setPreview((x) => !x)}>
						{preview ? 'Hide' : 'Preview'}
					</Button>
				)}
				<Button size="sm" icon="plus" onClick={() => setCreating(true)}>
					New
				</Button>
			</div>
			{preview && selected?.active_version && (
				<div className="mt-2">
					<PromptText content={selected.active_version.content} maxHeight={200} />
				</div>
			)}
			{creating && (
				<CreatePromptModal
					appId={appId}
					fixedType={type}
					onClose={() => setCreating(false)}
					onCreated={(name) => onChange(name)}
				/>
			)}
		</FieldGroup>
	);
}

/* ---------- test ---------- */

function AgentTest({ appId, agent }: { appId: string; agent: Agent }) {
	const [sys, setSys] = useState<Record<string, string>>({});
	const [vars, setVars] = useState<Record<string, string>>({});
	const [message, setMessage] = useState('');
	const [files, setFiles] = useState<File[]>([]);
	const [running, setRunning] = useState(false);
	const [result, setResult] = useState<AgentTestResult | null>(null);
	const [failure, setFailure] = useState<string | null>(null);
	const qc = useQueryClient();

	const needsMessage = !agent.user_prompt_name;
	const canRun = !running && (!needsMessage || !!message.trim() || files.length > 0);

	const run = async () => {
		setRunning(true);
		setResult(null);
		setFailure(null);
		try {
			const r = await testAgent(appId, agent.id, {
				variables: vars,
				system_variables: sys,
				user_message: needsMessage ? message : '',
				files,
			});
			setResult(r);
		} catch (err) {
			setFailure(err instanceof Error ? err.message : String(err));
		} finally {
			setRunning(false);
			void qc.invalidateQueries({ queryKey: aiKeys.invocations(appId) });
			void qc.invalidateQueries({ queryKey: aiKeys.agents(appId) });
		}
	};

	const varInputs = (names: string[], state: Record<string, string>, setState: typeof setVars) =>
		names.map((n) => (
			<Field key={n} label={<span className="mono">{`{{${n}}}`}</span>}>
				{(p) => (
					<Textarea
						{...p}
						rows={1}
						value={state[n] ?? ''}
						onChange={(e) => setState((s) => ({ ...s, [n]: e.target.value }))}
					/>
				)}
			</Field>
		));

	return (
		<>
			<p className="mb-4 text-[12.5px] text-t3">
				Runs the agent for real with its live prompts, so it costs tokens and shows up in Runs as
				triggered by <span className="mono">system</span>.
			</p>
			{!agent.is_enabled && (
				<p className="mb-4 rounded-lg border border-amber bg-amber-soft px-3 py-2 text-[12.5px] text-amber-t">
					This agent is disabled, so the test will fail. Enable it first.
				</p>
			)}
			<div className="grid gap-3">
				{agent.system_prompt_variables.length > 0 && (
					<>
						<SectionTitle>System prompt variables</SectionTitle>
						{varInputs(agent.system_prompt_variables, sys, setSys)}
					</>
				)}
				{agent.user_prompt_variables.length > 0 && (
					<>
						<SectionTitle>User prompt variables</SectionTitle>
						{varInputs(agent.user_prompt_variables, vars, setVars)}
					</>
				)}
				{needsMessage && (
					<Field label="Message" hint="This agent has no user prompt, so send a message or a file.">
						{(p) => (
							<Textarea
								{...p}
								rows={4}
								value={message}
								placeholder="Type a test message"
								onChange={(e) => setMessage(e.target.value)}
							/>
						)}
					</Field>
				)}
				<Field label="Files (optional)">
					{(p) => (
						<input
							{...p}
							type="file"
							multiple
							className="text-[12.5px]"
							onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
						/>
					)}
				</Field>
			</div>
			<div className="mt-4">
				<Button variant="primary" icon="zap" loading={running} disabled={!canRun} onClick={run}>
					Run test
				</Button>
			</div>

			{failure && (
				<div className="mt-4 rounded-lg border border-red bg-red-soft px-3 py-2 text-[12.5px] text-red-t">
					<b>Test failed. </b>
					{failure}
				</div>
			)}
			{result && (
				<>
					<SectionTitle
						action={
							<span className="num text-[12px] text-t3">
								{result.model} · {result.latency_ms}ms · {result.input_tokens} in /{' '}
								{result.output_tokens} out · {money(result.cost_usd, 6)}
							</span>
						}
					>
						Answer
					</SectionTitle>
					<CodeBlock maxHeight={420}>{result.content || '(empty response)'}</CodeBlock>
					<p className="mt-2 text-[12px] text-t3">
						Tool calls and rounds are in the Runs tab. The answer above is cut at 2,000 characters.
					</p>
				</>
			)}
		</>
	);
}

/* ---------- sessions ---------- */

function Sessions({ appId, agent }: { appId: string; agent: Agent }) {
	const { data, isLoading, error, refetch } = useSessions(appId, agent.id);
	const clear = useClearSession(appId, agent.id);
	const [open, setOpen] = useState<string | null>(null);
	const detail = useSession(appId, agent.id, open);

	if (isLoading) return <Skeleton height={120} />;
	if (error) return <ErrorState error={error} onRetry={() => refetch()} />;
	if (!data?.length)
		return (
			<EmptyState title="No sessions yet">
				A session starts when code calls <span className="mono">agent.run(..., session_id=...)</span>.
			</EmptyState>
		);

	return (
		<div className="grid gap-2">
			{data.map((s) => (
				<div key={s.id} className="rounded-lg border border-border">
					<div className="flex items-center gap-3 px-3 py-2">
						<button
							type="button"
							className="min-w-0 flex-1 text-left"
							onClick={() => setOpen(open === s.session_id ? null : s.session_id)}
						>
							<div className="mono truncate text-[12.5px] text-t1">{s.session_id}</div>
							<div className="text-[11.5px] text-t3">
								{s.message_count} messages · {s.user_ref || 'no user ref'} · last active{' '}
								{fmtDate(s.last_active_at)}
							</div>
						</button>
						{s.is_active ? (
							<Button
								size="xs"
								loading={clear.isPending && clear.variables?.sessionId === s.session_id}
								onClick={() => clear.mutate({ sessionId: s.session_id })}
							>
								Clear
							</Button>
						) : (
							<span className="text-[12px] text-t3">Cleared</span>
						)}
					</div>
					{open === s.session_id && (
						<div className="border-t border-border px-3 py-2">
							{detail.isLoading ? (
								<Skeleton height={60} />
							) : detail.data?.messages.length ? (
								<div className="grid gap-2">
									{detail.data.messages.map((m) => (
										<div key={m.id} className="text-[12.5px]">
											<span className="mono text-[11px] uppercase text-t3">{m.role}</span>
											<pre className="mono mt-0.5 whitespace-pre-wrap text-t1">
												{typeof m.content === 'string'
													? m.content
													: JSON.stringify(m.content, null, 2)}
											</pre>
										</div>
									))}
								</div>
							) : (
								<p className="text-t3">No messages.</p>
							)}
						</div>
					)}
				</div>
			))}
		</div>
	);
}

/* ---------- usage ---------- */

function Usage({ agent }: { agent: Agent }) {
	const m = agent.metrics;
	return (
		<>
			<div className="grid grid-cols-3 gap-3">
				{[
					['Runs', m?.totalInvocations],
					['Success rate', m ? `${m.successRate}%` : undefined],
					['Avg latency', m?.avgLatency],
					['Total cost', money(m?.totalCost)],
					['Avg tokens in', m?.avgInputTokens],
					['Avg tokens out', m?.avgOutputTokens],
				].map(([label, value]) => (
					<div key={String(label)} className="card px-4 py-3">
						<div className="text-[12px] text-t3">{label}</div>
						<div className="num mt-1 text-[18px] font-semibold text-t1">{value ?? '—'}</div>
					</div>
				))}
			</div>
			<SectionTitle>Details</SectionTitle>
			<KeyValues
				items={[
					['Created', agent.created_at],
					['Last changed', agent.modified_at],
					['Runs in the last 24h', m?.invocations24h],
					['Avg cost per run', money(m?.avgCost, 4)],
				]}
			/>
			<SectionTitle>Use in code</SectionTitle>
			<CodeBlock>{usageSnippet(agent)}</CodeBlock>
		</>
	);
}
