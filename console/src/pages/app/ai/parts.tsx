import type { ReactNode } from 'react';
import type { Provider, ToolSafety, InvocationStatus } from '@/api/ai';
import { Badge, Button, Modal, type Tone } from '@/ui';

// Shared pieces for the AI page's tabs.

export const SERVICE_LABEL: Record<string, string> = {
	anthropic: 'Anthropic',
	openai: 'OpenAI',
	azure_openai: 'Azure OpenAI',
	bedrock: 'AWS Bedrock',
};

export const serviceLabel = (slug: string | null | undefined) =>
	slug ? (SERVICE_LABEL[slug] ?? slug) : '—';

/** A row of small metric tiles above a tab's table. */
export function StatStrip({ items }: { items: Array<[string, ReactNode, Tone?]> }) {
	return (
		<div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
			{items.map(([label, value, tone]) => (
				<div key={label} className="card px-4 py-3">
					<div className="text-[12px] text-t3">{label}</div>
					<div
						className={
							'num mt-1 text-[20px] font-semibold tracking-tight ' +
							(tone === 'red' ? 'text-red' : 'text-t1')
						}
					>
						{value ?? <span className="sk" style={{ width: 40, height: 20 }} />}
					</div>
				</div>
			))}
		</div>
	);
}

export function ProviderStatus({ p }: { p: Provider }) {
	if (!p.is_enabled)
		return (
			<Badge tone="gray" dot>
				Disabled
			</Badge>
		);
	if (p.is_placeholder)
		return (
			<Badge tone="amber" dot>
				Waiting for a key
			</Badge>
		);
	if (p.source === 'platform' && !p.connected)
		return (
			<span title={p.connection_problem}>
				<Badge tone="red" dot>
					Platform account unavailable
				</Badge>
			</span>
		);
	if (p.validation_error)
		return (
			<Badge tone="red" dot>
				Key check failed
			</Badge>
		);
	if (!p.is_validated)
		return (
			<Badge tone="amber" dot>
				Not checked
			</Badge>
		);
	return (
		<Badge tone="green" dot>
			Active
		</Badge>
	);
}

export function EnabledBadge({ enabled }: { enabled: boolean }) {
	return (
		<Badge tone={enabled ? 'green' : 'gray'} dot>
			{enabled ? 'Enabled' : 'Disabled'}
		</Badge>
	);
}

const SAFETY: Record<ToolSafety, [string, Tone]> = {
	read_only: ['Read only', 'green'],
	write: ['Write', 'amber'],
	external: ['External', 'red'],
};

export function SafetyBadge({ safety }: { safety: ToolSafety }) {
	const [label, tone] = SAFETY[safety] ?? [safety, 'gray'];
	return <Badge tone={tone}>{label}</Badge>;
}

const STATUS: Record<InvocationStatus, [string, Tone]> = {
	success: ['Success', 'green'],
	error: ['Error', 'red'],
	timeout: ['Timeout', 'amber'],
	rate_limited: ['Rate limited', 'amber'],
	budget_exceeded: ['Over budget', 'red'],
};

export function RunStatus({ status }: { status: InvocationStatus }) {
	const [label, tone] = STATUS[status] ?? [status, 'gray'];
	return (
		<Badge tone={tone} dot>
			{label}
		</Badge>
	);
}

/** A 409 from provider disable/delete or prompt delete: which agents are in the way. */
export function InUseModal({
	what,
	agents,
	onClose,
}: {
	what: string;
	agents: Array<{ id: number; name: string }> | null;
	onClose: () => void;
}) {
	return (
		<Modal
			open={agents != null}
			onOpenChange={(o) => !o && onClose()}
			title={`${what} is in use`}
			footer={
				<Button variant="primary" onClick={onClose}>
					Got it
				</Button>
			}
		>
			<p className="mb-3 text-t2">
				{agents?.length === 1 ? 'This enabled agent uses it' : 'These enabled agents use it'}.
				Point them somewhere else or disable them first.
			</p>
			<ul className="grid gap-1">
				{agents?.map((a) => (
					<li key={a.id} className="mono text-[12.5px]">
						{a.name}
					</li>
				))}
			</ul>
		</Modal>
	);
}

/** `{{var}}` slots highlighted inside prompt text. */
export function PromptText({ content, maxHeight = 320 }: { content: string; maxHeight?: number }) {
	const parts = content.split(/(\{\{\w+\}\})/g);
	return (
		<pre
			className="mono overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-bg p-3 text-[12px] leading-[1.6] text-t1"
			style={{ maxHeight }}
		>
			{parts.map((p, i) =>
				/^\{\{\w+\}\}$/.test(p) ? (
					<span key={i} className="rounded bg-violet-soft px-0.5 text-violet">
						{p}
					</span>
				) : (
					p
				),
			)}
		</pre>
	);
}

export const fmtDate = (iso: string | null | undefined) =>
	iso
		? new Date(iso).toLocaleString(undefined, {
				month: 'short',
				day: 'numeric',
				hour: '2-digit',
				minute: '2-digit',
			})
		: '—';

export const fmtMs = (ms: number | null | undefined) =>
	ms == null ? '—' : ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`;

export const fmtInt = (n: number | null | undefined) => (n == null ? '—' : n.toLocaleString());
