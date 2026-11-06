import { useState, type ReactNode } from 'react';
import { money, useInvocation, type InvocationDetail } from '@/api/ai';
import {
	Badge,
	CodeBlock,
	cx,
	Drawer,
	ErrorState,
	KeyValues,
	SectionTitle,
	Skeleton,
	Tabs,
} from '@/ui';
import { fmtInt, fmtMs, RunStatus } from './parts';

type Tab = 'conversation' | 'prompt' | 'cost' | 'meta';

type Block = Record<string, unknown>;
type Msg = { role?: string; content?: unknown; tool_calls?: unknown[]; tool_call_id?: string };

const json = (v: unknown) => JSON.stringify(v, null, 2);
const blocks = (content: unknown): Block[] =>
	Array.isArray(content) ? (content as Block[]) : [];

/** A user message that only carries tool results (Anthropic) isn't a real turn. */
const isRealUserTurn = (m: Msg) =>
	m.role === 'user' &&
	(typeof m.content === 'string' || blocks(m.content).some((b) => b.type !== 'tool_result'));

function textOf(content: unknown): string {
	if (typeof content === 'string') return content;
	return blocks(content)
		.filter((b) => b.type === 'text')
		.map((b) => String(b.text ?? ''))
		.join('\n');
}

function Bubble({ who, tone, children }: { who: string; tone: string; children: ReactNode }) {
	return (
		<div className="flex gap-2.5">
			<span
				className={cx(
					'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold',
					tone,
				)}
			>
				{who[0]}
			</span>
			<div className="min-w-0 flex-1">
				<div className="mb-0.5 text-[11.5px] font-medium text-t3">{who}</div>
				{children}
			</div>
		</div>
	);
}

const Pre = ({ children }: { children: string }) => (
	<pre className="mono whitespace-pre-wrap rounded-lg border border-border bg-bg p-2.5 text-[12px] leading-[1.55] text-t1">
		{children}
	</pre>
);

/** Renders one logged message: text, tool calls (Anthropic or OpenAI shape) and tool results. */
function Message({ m }: { m: Msg }) {
	if (m.role === 'tool')
		return (
			<Bubble who="Tool result" tone="bg-amber-soft text-amber-t">
				<Pre>{typeof m.content === 'string' ? m.content : json(m.content)}</Pre>
			</Bubble>
		);
	const text = textOf(m.content);
	const toolUses = blocks(m.content).filter((b) => b.type === 'tool_use');
	const toolResults = blocks(m.content).filter((b) => b.type === 'tool_result');
	const files = blocks(m.content).filter((b) => b.type === 'image' || b.type === 'document' || b.type === 'image_url');
	const oaCalls = (m.tool_calls ?? []) as Array<{ function?: { name?: string; arguments?: string } }>;
	const isUser = m.role === 'user';
	return (
		<Bubble
			who={isUser ? (toolResults.length && !text ? 'Tool results' : 'User') : 'Assistant'}
			tone={isUser ? 'bg-accent-soft text-accent-t' : 'bg-violet-soft text-violet-t'}
		>
			<div className="grid gap-1.5">
				{text && <Pre>{text}</Pre>}
				{files.length > 0 && <span className="text-[12px] text-t3">{files.length} file(s) attached</span>}
				{toolUses.map((b, i) => (
					<ToolCard key={i} name={String(b.name)} input={b.input} />
				))}
				{oaCalls.map((c, i) => (
					<ToolCard key={`o${i}`} name={c.function?.name ?? 'tool'} input={c.function?.arguments} />
				))}
				{toolResults.map((b, i) => (
					<div key={`r${i}`}>
						<div className="text-[11.5px] text-t3">↩ result</div>
						<Pre>{typeof b.content === 'string' ? b.content : json(b.content)}</Pre>
					</div>
				))}
			</div>
		</Bubble>
	);
}

function ToolCard({ name, input, note }: { name: string; input: unknown; note?: string }) {
	let shown = input;
	if (typeof input === 'string') {
		try {
			shown = JSON.parse(input);
		} catch {
			/* keep the raw string */
		}
	}
	return (
		<div className="rounded-lg border border-amber/60 bg-amber-soft/40 p-2">
			<div className="mb-1 flex items-center gap-2 text-[12px]">
				<Badge tone="amber">tool call</Badge>
				<b className="mono">{name}</b>
				{note && <span className="text-t3">{note}</span>}
			</div>
			<Pre>{typeof shown === 'string' ? shown : json(shown)}</Pre>
		</div>
	);
}

const fmtBytes = (n: number | null) =>
	n == null ? '' : n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`;

function Conversation({ inv }: { inv: InvocationDetail }) {
	const [showMemory, setShowMemory] = useState(false);
	const msgs = (inv.request_messages ?? []).filter((m): m is Msg => !!m && typeof m === 'object');
	let lastUser = -1;
	msgs.forEach((m, i) => {
		if (isRealUserTurn(m)) lastUser = i;
	});
	const history = lastUser > 0 ? msgs.slice(0, lastUser) : [];
	const current = lastUser >= 0 ? msgs.slice(lastUser) : msgs;

	return (
		<div className="grid gap-4">
			{inv.request_system && (
				<div>
					<SectionTitle>System prompt</SectionTitle>
					<CodeBlock maxHeight={200}>{inv.request_system}</CodeBlock>
				</div>
			)}
			{inv.files.length > 0 && (
				<div>
					<SectionTitle>Files ({inv.files.length})</SectionTitle>
					<div className="overflow-hidden rounded-lg border border-border">
						{inv.files.map((f) => {
							const href = f.url ?? f.source_url;
							return (
								<div key={f.id} className="flex items-center gap-3 border-b border-border-soft px-3 py-2 text-[12.5px] last:border-b-0">
									{href ? (
										<a className="mono truncate text-accent" href={href} target="_blank" rel="noreferrer">
											{f.filename ?? 'file'}
										</a>
									) : (
										<span className="mono truncate">{f.filename ?? 'file'}</span>
									)}
									{f.media_type && <Badge tone="line">{f.media_type}</Badge>}
									<span className="text-t3">{fmtBytes(f.size_bytes)}</span>
									<span className="text-t3">{f.source_kind === 'url' ? 'Linked, not copied' : 'Copied'}</span>
									{f.sha256 && (
										<span className="mono ml-auto text-[11px] text-t4" title={f.sha256}>
											sha {f.sha256.slice(0, 12)}…
										</span>
									)}
								</div>
							);
						})}
					</div>
				</div>
			)}
			{history.length > 0 && (
				<div className="rounded-lg border border-violet/40 bg-violet-soft/30 p-3">
					<button type="button" className="text-[12.5px] font-medium text-violet-t" onClick={() => setShowMemory((x) => !x)}>
						{showMemory ? 'Hide' : 'Show'} memory: {history.length} earlier message{history.length > 1 ? 's' : ''} sent as context
					</button>
					{showMemory && (
						<div className="mt-3 grid gap-3">
							{history.map((m, i) => (
								<Message key={i} m={m} />
							))}
						</div>
					)}
				</div>
			)}
			<div className="grid gap-3">
				{current.map((m, i) => (
					<Message key={i} m={m} />
				))}
			</div>
			<div>
				<SectionTitle
					action={
						inv.stop_reason && (
							<Badge tone={inv.stop_reason === 'tool_use' ? 'amber' : 'line'}>
								{inv.stop_reason === 'tool_use' ? 'asked for a tool' : inv.stop_reason}
							</Badge>
						)
					}
				>
					Model answer
				</SectionTitle>
				<div className="grid gap-1.5">
					{(inv.response_tool_calls ?? []).map((c) => (
						<ToolCard key={c.id} name={c.name} input={c.input} note="result goes into the next round" />
					))}
					{inv.response_content ? (
						<Pre>{inv.response_content}</Pre>
					) : (
						!inv.response_tool_calls?.length && <p className="text-t3">No text in the answer.</p>
					)}
					{inv.error_message && (
						<div className="rounded-lg border border-red bg-red-soft px-3 py-2 text-[12.5px] text-red-t">
							<b>{inv.error_type ?? 'Error'}: </b>
							{inv.error_message}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}

export function RunDrawer({ appId, id, onClose }: { appId: string; id: number; onClose: () => void }) {
	const { data: inv, isLoading, error, refetch } = useInvocation(appId, id);
	const [tab, setTab] = useState<Tab>('conversation');

	return (
		<Drawer
			open
			wide
			onOpenChange={(o) => !o && onClose()}
			title={
				<span>
					Call #{id}
					{inv?.agent_name && <span className="mono text-t3"> · {inv.agent_name}</span>}
				</span>
			}
			subtitle={
				inv && (
					<span className="inline-flex items-center gap-2">
						<RunStatus status={inv.status} />
						{inv.model} · {fmtMs(inv.latency_ms)} · {money(inv.cost_usd, 4)}
						{inv.round_number ? ` · round ${inv.round_number}` : ''}
					</span>
				)
			}
		>
			<Tabs
				className="-mx-5 -mt-5 mb-5"
				value={tab}
				onChange={setTab}
				items={[
					{ value: 'conversation', label: 'Conversation' },
					{ value: 'prompt', label: 'Prompt' },
					{ value: 'cost', label: 'Cost' },
					{ value: 'meta', label: 'Details' },
				]}
			/>
			{isLoading && <Skeleton height={240} />}
			{error && <ErrorState error={error} onRetry={() => refetch()} />}
			{inv && tab === 'conversation' && <Conversation inv={inv} />}
			{inv && tab === 'prompt' && (
				<>
					<KeyValues
						items={[
							[
								'System prompt',
								inv.system_prompt_name && (
									<span className="mono">
										{inv.system_prompt_name} v{inv.system_prompt_version}
									</span>
								),
							],
							[
								'User prompt',
								inv.user_prompt_name && (
									<span className="mono">
										{inv.user_prompt_name} v{inv.user_prompt_version}
									</span>
								),
							],
						]}
					/>
					<SectionTitle>System prompt as sent</SectionTitle>
					<CodeBlock maxHeight={260}>{inv.rendered_system_prompt || inv.request_system || '—'}</CodeBlock>
					<SectionTitle>Variables passed in</SectionTitle>
					<CodeBlock maxHeight={260}>{json(inv.context_snapshot ?? {})}</CodeBlock>
					{inv.request_tools && inv.request_tools.length > 0 && (
						<>
							<SectionTitle>Tools offered</SectionTitle>
							<div className="flex flex-wrap gap-1">
								{inv.request_tools.map((t) => (
									<Badge key={t.name} tone="line">
										<span className="mono">{t.name}</span>
									</Badge>
								))}
							</div>
						</>
					)}
				</>
			)}
			{inv && tab === 'cost' && (
				<KeyValues
					items={[
						['Input tokens', fmtInt(inv.input_tokens)],
						['Output tokens', fmtInt(inv.output_tokens)],
						['Cache write tokens', fmtInt(inv.cache_creation_tokens)],
						['Cache read tokens', fmtInt(inv.cache_read_tokens)],
						['Cost', money(inv.cost_usd, 6)],
						['Time', fmtMs(inv.latency_ms)],
						['Time to first token', fmtMs(inv.time_to_first_token_ms)],
						['Stop reason', inv.stop_reason],
					]}
				/>
			)}
			{inv && tab === 'meta' && (
				<>
					<KeyValues
						items={[
							['Triggered by', inv.triggered_by],
							['User', inv.user_id_ref],
							['Celery task', inv.celery_task_id && <span className="mono">{inv.celery_task_id}</span>],
							['Agent', inv.agent_name && <span className="mono">{inv.agent_name}</span>],
							['Provider', `${inv.provider_name} (${inv.provider_slug})`],
							['Model', <span className="mono">{inv.model}</span>],
							['Run', inv.run_id && <span className="mono">{inv.run_id}</span>],
							['Session', inv.session_id && <span className="mono">{inv.session_id}</span>],
							['Status', <RunStatus status={inv.status} />],
							['Error type', inv.error_type],
							['When', new Date(inv.created_at).toLocaleString()],
						]}
					/>
					<SectionTitle>Request settings</SectionTitle>
					<CodeBlock>{json(inv.request_params ?? {})}</CodeBlock>
					{inv.error_message && (
						<>
							<SectionTitle>Error</SectionTitle>
							<CodeBlock>{inv.error_message}</CodeBlock>
						</>
					)}
				</>
			)}
		</Drawer>
	);
}
