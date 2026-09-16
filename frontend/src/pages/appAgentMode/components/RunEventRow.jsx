/**
 * One row of the run transcript.
 *
 * Event kinds come from AgentRunEvent.EventKind on the backend. Thinking and
 * tool payloads are collapsed by default — a run emits a lot of both, and the
 * useful signal is the one-line summary the backend already computed.
 */
import { useState } from 'react';
import Markdown from './Markdown';

const KIND_META = {
	sys: { label: 'System', bg: '#F3F4F6', accent: '#6B7280' },
	init: { label: 'Session', bg: '#EEF2FF', accent: '#5048ED' },
	assistant: { label: '', bg: 'transparent', accent: '#111827' },
	thinking: { label: 'Thinking', bg: '#FAFAF9', accent: '#9CA3AF' },
	tool_use: { label: 'Tool', bg: '#F0F9FF', accent: '#0369A1' },
	tool_result: { label: 'Result', bg: '#F8FAFC', accent: '#64748B' },
	skill: { label: 'Skill', bg: '#FEF3C7', accent: '#B45309' },
	user: { label: 'Input', bg: '#F9FAFB', accent: '#6B7280' },
	compact: { label: 'Compacted', bg: '#F3F4F6', accent: '#6B7280' },
	hook_deny: { label: 'Blocked', bg: '#FEF2F2', accent: '#DC2626' },
	post_step: { label: 'Step', bg: '#ECFDF5', accent: '#047857' },
	stdout: { label: 'stdout', bg: '#F8FAFC', accent: '#64748B' },
	stderr: { label: 'stderr', bg: '#FEF2F2', accent: '#B91C1C' },
	result: { label: 'Done', bg: '#ECFDF5', accent: '#047857' },
	error: { label: 'Error', bg: '#FEF2F2', accent: '#DC2626' },
};

const COLLAPSIBLE = new Set(['thinking', 'tool_use', 'tool_result', 'init', 'compact']);

export default function RunEventRow({ event }) {
	const [open, setOpen] = useState(false);
	const meta = KIND_META[event.kind] || KIND_META.sys;
	const collapsible = COLLAPSIBLE.has(event.kind) && event.data;
	const isPlainText = event.kind === 'assistant';

	return (
		<div
			className="flex gap-[10px] border-b border-[#F1F3F5] px-[16px] py-[8px]"
			style={{ backgroundColor: event.is_error ? '#FEF2F2' : 'transparent' }}
		>
			{meta.label ? (
				<span
					className="mt-[2px] h-[18px] shrink-0 rounded-[4px] px-[6px] font-lato text-[10px] font-bold uppercase leading-[18px] tracking-[0.04em]"
					style={{ backgroundColor: meta.bg, color: meta.accent }}
				>
					{meta.label}
				</span>
			) : (
				<span className="w-[2px] shrink-0" />
			)}

			<div className="min-w-0 grow">
				<div
					className={`break-words font-lato text-[13px] leading-[19px] ${
						isPlainText ? 'text-[#111827]' : 'whitespace-pre-wrap text-[#374151]'
					}`}
					style={event.kind === 'thinking' ? { color: '#9CA3AF', fontStyle: 'italic' } : undefined}
				>
					{/* The agent's own prose is markdown; tool output is not. */}
					{isPlainText ? <Markdown text={event.message} /> : event.message}
				</div>

				{collapsible ? (
					<>
						<button
							onClick={() => setOpen((v) => !v)}
							className="mt-[4px] font-lato text-[11px] font-medium text-[#6B7280] hover:text-[#111827]"
						>
							{open ? 'hide details' : 'show details'}
						</button>
						{open ? (
							<pre className="mt-[6px] max-h-[280px] overflow-auto rounded-[6px] bg-[#0F172A] p-[10px] font-mono text-[11px] leading-[16px] text-[#E2E8F0]">
								{JSON.stringify(event.data, null, 2)}
							</pre>
						) : null}
					</>
				) : null}
			</div>

			<span className="shrink-0 font-lato text-[10px] leading-[18px] text-[#9CA3AF]">
				{event.ts ? new Date(event.ts).toLocaleTimeString() : ''}
			</span>
		</div>
	);
}
