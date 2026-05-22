import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import useApi from '../../../hooks/useApi';

function StatusBadge({ status }) {
	const styles = {
		success: 'text-[#10B981]',
		error: 'text-[#EF4444]',
		timeout: 'text-[#F59E0B]',
		rate_limited: 'text-[#D97706]',
		budget_exceeded: 'text-[#EF4444]',
	};
	return (
		<span className={`flex items-center gap-[4px] font-lato text-[12px] font-medium ${styles[status] || 'text-[#6B7280]'}`}>
			<span className={`inline-block h-[6px] w-[6px] rounded-full ${status === 'success' ? 'bg-[#10B981]' : status === 'error' ? 'bg-[#EF4444]' : 'bg-[#F59E0B]'}`} />
			{status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
		</span>
	);
}

function StatCard({ icon, label, value, color }) {
	return (
		<div className="flex items-center gap-[8px]">
			<span className="text-[16px]">{icon}</span>
			<span className="font-lato text-[13px] text-[#6B7280]">{label}</span>
			<span className={`font-lato text-[14px] font-bold ${color || 'text-[#111827]'}`}>{value}</span>
		</div>
	);
}

function JsonBlock({ data, maxHeight = '200px' }) {
	if (!data) return <span className="font-lato text-[13px] text-[#9CA3AF]">-</span>;
	const formatted = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
	return (
		<div className={`rounded-[6px] bg-[#1F2937] p-[12px] overflow-auto`} style={{ maxHeight }}>
			<pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-[20px] text-[#D1D5DB]">{formatted}</pre>
		</div>
	);
}

/* ─── Collapsible panel showing memory context messages injected before the current turn ─── */
function MemoryHistoryPanel({ messages, renderContent }) {
	const [expanded, setExpanded] = useState(false);
	const exchangeCount = Math.ceil(messages.length / 2);
	return (
		<div className="rounded-[8px] border border-[#E5E7EB] overflow-hidden">
			<button
				onClick={() => setExpanded(e => !e)}
				className="w-full flex items-center gap-[8px] px-[12px] py-[8px] bg-[#F9FAFB] hover:bg-[#F3F4F6] text-left"
			>
				<svg width="9" height="9" viewBox="0 0 10 10" className={`transition-transform text-[#7C3AED] shrink-0 ${expanded ? 'rotate-90' : ''}`}>
					<path d="M3 1L7 5L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
				</svg>
				<svg width="11" height="11" viewBox="0 0 12 12" fill="none" className="text-[#7C3AED] shrink-0">
					<path d="M6 1C3.24 1 1 3.24 1 6s2.24 5 5 5 5-2.24 5-5S8.76 1 6 1zm0 2a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0 7.1a3.6 3.6 0 01-3-1.62c.015-1 2-1.55 3-1.55s2.985.55 3 1.55A3.6 3.6 0 016 10.1z" fill="currentColor"/>
				</svg>
				<span className="font-lato text-[11px] font-semibold text-[#7C3AED]">Session memory context</span>
				<span className="font-lato text-[11px] text-[#9CA3AF]">
					({exchangeCount} prior exchange{exchangeCount !== 1 ? 's' : ''} injected from memory)
				</span>
			</button>
			{expanded && (
				<div className="divide-y divide-[#F3F4F6]">
					{messages.map((m, i) => (
						<div key={i} className="flex items-start gap-[8px] px-[12px] py-[8px] bg-white">
							<span className={`mt-[1px] shrink-0 rounded-full px-[6px] py-[1px] font-mono text-[10px] font-bold ${
								m.role === 'user' ? 'bg-[#EFF6FF] text-[#2563EB]' :
								m.role === 'assistant' ? 'bg-[#F0FDF4] text-[#16A34A]' :
								'bg-[#F5F3FF] text-[#7C3AED]'
							}`}>
								{m.role === 'user' ? 'U' : m.role === 'assistant' ? 'A' : 'T'}
							</span>
							<pre className="whitespace-pre-wrap break-words font-lato text-[12px] leading-[18px] text-[#6B7280]">
								{renderContent(m.content)}
							</pre>
						</div>
					))}
				</div>
			)}
		</div>
	);
}

/* ─── Detail Tabs ─── */
function InvocationDetail({ invocation }) {
	const [activeTab, setActiveTab] = useState('request');

	if (!invocation) return null;

	const tabs = [
		{ id: 'request', label: 'Request / Response' },
		{ id: 'prompt', label: 'Prompt' },
		{ id: 'cost', label: 'Cost Breakdown' },
		{ id: 'metadata', label: 'Metadata' },
	];

	const promptInfo = invocation.prompt_info || {};
	const costInfo = invocation.cost_breakdown || {};

	return (
		<div>
			{/* Tab bar */}
			<div className="mb-[16px] flex gap-[24px] border-b border-[#E5E7EB]">
				{tabs.map((tab) => (
					<button
						key={tab.id}
						onClick={() => setActiveTab(tab.id)}
						className={`pb-[10px] font-lato text-[13px] font-medium border-b-[2px] transition-colors ${
							activeTab === tab.id
								? 'border-[#346BD4] text-[#346BD4]'
								: 'border-transparent text-[#6B7280] hover:text-[#111827]'
						}`}
					>
						{tab.label}
					</button>
				))}
			</div>

			{/* Request / Response — conversation timeline */}
			{activeTab === 'request' && (() => {
				// Parse messages to build a conversation timeline
				let messages = [];
				try {
					messages = typeof invocation.request_messages === 'string'
						? JSON.parse(invocation.request_messages)
						: (invocation.request_messages || []);
				} catch (e) {}

				// Build tool result lookup: tool_call_id -> content
				// OpenAI format: role="tool" messages with tool_call_id
				// Anthropic format: role="user" messages with content blocks of type="tool_result" and tool_use_id
				const toolResults = {};
				messages.forEach(m => {
					if (m.role === 'tool' && m.tool_call_id) {
						toolResults[m.tool_call_id] = m.content;
					} else if (m.role === 'user' && Array.isArray(m.content)) {
						m.content.forEach(b => {
							if (b.type === 'tool_result' && b.tool_use_id) {
								const resultContent = Array.isArray(b.content)
									? b.content.filter(c => c.type === 'text').map(c => c.text).join(' ')
									: b.content;
								toolResults[b.tool_use_id] = resultContent;
							}
						});
					}
				});

				// Collect tool calls made by LLM (from assistant messages in history + current response)
				// OpenAI format: assistant message has tool_calls array
				// Anthropic format: assistant message has content array with blocks of type="tool_use"
				const historyToolCalls = [];
				messages.forEach(m => {
					if (m.role === 'assistant') {
						if (m.tool_calls) {
							m.tool_calls.forEach(tc => historyToolCalls.push(tc));
						} else if (Array.isArray(m.content)) {
							m.content.forEach(b => {
								if (b.type === 'tool_use') {
									historyToolCalls.push({ id: b.id, name: b.name, input: b.input });
								}
							});
						}
					}
				});
				const currentToolCalls = invocation.response_tool_calls || [];

				// Separate memory history from the current turn's input.
				// For memory-enabled runs, request_messages = [...historyMessages, currentUserMsg].
				// The current user input is the last user-role message; everything before it is
				// prior session context loaded from memory.
				//
				// Anthropic tool-result messages also use role="user" with content blocks of
				// type "tool_result" — these are NOT the user's actual input and must be skipped
				// when finding the real current user message.
				const isToolResultMsg = (m) =>
					m.role === 'user' &&
					Array.isArray(m.content) &&
					m.content.length > 0 &&
					m.content.every(b => b.type === 'tool_result');

				const userMsgIndices = messages.reduce(
					(acc, m, i) => (m.role === 'user' && !isToolResultMsg(m)) ? [...acc, i] : acc,
					[]
				);
				const currentUserMsgIdx = userMsgIndices[userMsgIndices.length - 1] ?? -1;
				const currentUserMsg = currentUserMsgIdx >= 0 ? messages[currentUserMsgIdx] : null;
				// History = all messages before the current user message (memory context)
				const memoryHistoryMessages = currentUserMsgIdx > 0 ? messages.slice(0, currentUserMsgIdx) : [];
				const hasMemoryHistory = memoryHistoryMessages.length > 0;

				const hasFileBlocks = currentUserMsg && Array.isArray(currentUserMsg.content) &&
					currentUserMsg.content.some(b => b.type === 'image_url' || b.type === 'document');

				// Helper to render message text content
				const renderContent = (content) => {
					if (Array.isArray(content)) {
						// tool_result blocks are internal Anthropic protocol — show a neutral label
						if (content.every(b => b.type === 'tool_result')) {
							return '(tool result)';
						}
						const text = content.filter(b => b.type === 'text').map(b => b.text).join(' ');
						return text || '(file attachment)';
					}
					return content || '(empty)';
				};

				return (
					<div className="flex flex-col gap-[12px]">

						{/* System prompt */}
						{invocation.request_system && (
							<div className="rounded-[8px] border border-[#FCD34D] bg-[#1F2937] overflow-hidden">
								<div className="flex items-center gap-[8px] border-b border-[#374151] px-[12px] py-[8px]">
									<span className="text-[12px]">⚙️</span>
									<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#FCD34D]">System Prompt</span>
								</div>
								<div className="px-[12px] py-[10px] max-h-[160px] overflow-auto">
									<pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-[18px] text-[#D1D5DB]">{invocation.request_system}</pre>
								</div>
							</div>
						)}

						{/* Files attached */}
						{invocation.request_files && invocation.request_files.length > 0 && (
							<div className="flex items-center gap-[8px] rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB] px-[12px] py-[10px]">
								<span className="text-[14px]">📎</span>
								{invocation.request_files.map((f, i) => (
									<span key={i} className="flex items-center gap-[6px]">
										<span className="font-lato text-[12px] font-medium text-[#111827]">{f.filename?.split('/').pop() || 'file'}</span>
										<span className="rounded-full bg-[#EFF6FF] px-[6px] py-[1px] font-lato text-[10px] text-[#2563EB]">{f.media_type}</span>
										{f.size_bytes != null && (
											<span className="font-lato text-[11px] text-[#9CA3AF]">
												{f.size_bytes >= 1048576 ? `${(f.size_bytes / 1048576).toFixed(1)}MB`
													: f.size_bytes >= 1024 ? `${(f.size_bytes / 1024).toFixed(1)}KB`
													: `${f.size_bytes}B`}
											</span>
										)}
									</span>
								))}
								{hasFileBlocks && !invocation.request_files.length && (
									<span className="font-lato text-[12px] text-[#6B7280]">File included in message</span>
								)}
							</div>
						)}

						{/* Memory history context — collapsible, shows prior exchanges loaded from memory */}
						{hasMemoryHistory && (
							<MemoryHistoryPanel messages={memoryHistoryMessages} renderContent={renderContent} />
						)}

						{/* Conversation timeline — current turn only */}
						<div className="flex flex-col gap-[8px]">

							{/* Current turn's user input */}
							{currentUserMsg && (
								<div className="flex gap-[10px]">
									<div className="flex flex-col items-center">
										<div className="flex h-[28px] w-[28px] items-center justify-center rounded-full bg-[#346BD4] text-[11px] text-white font-bold">U</div>
										<div className="mt-[4px] w-[1px] flex-1 bg-[#E5E7EB]" />
									</div>
									<div className="flex-1 pb-[8px]">
										<span className="mb-[4px] block font-lato text-[11px] font-semibold text-[#374151]">
											User
											{hasMemoryHistory && <span className="ml-[6px] font-normal text-[#9CA3AF]">· this turn</span>}
										</span>
										<div className="rounded-[6px] bg-[#EFF6FF] border border-[#BFDBFE] px-[12px] py-[8px]">
											{Array.isArray(currentUserMsg.content)
												? <pre className="whitespace-pre-wrap break-words font-lato text-[12px] text-[#1E3A5F]">
													{currentUserMsg.content.filter(b => b.type === 'text').map(b => b.text).join(' ') || '(file attachment)'}
												  </pre>
												: <pre className="whitespace-pre-wrap break-words font-lato text-[12px] text-[#1E3A5F]">{currentUserMsg.content || '(empty)'}</pre>
											}
										</div>
									</div>
								</div>
							)}

							{/* Tool calls from history (already executed in prior rounds) */}
							{historyToolCalls.map((tc, i) => {
								const tcId = tc.id || tc.function?.name;
								const name = tc.function?.name || tc.name;
								let args = {};
								try { args = typeof tc.function?.arguments === 'string' ? JSON.parse(tc.function.arguments) : (tc.input || {}); } catch(e) {}
								const result = toolResults[tc.id];
								let parsedResult = null;
								try { parsedResult = result ? JSON.parse(result) : null; } catch(e) { parsedResult = result; }

								return (
									<div key={i} className="flex gap-[10px]">
										<div className="flex flex-col items-center">
											<div className="flex h-[28px] w-[28px] items-center justify-center rounded-full bg-[#7C3AED] text-[11px] text-white font-bold">T</div>
											<div className="mt-[4px] w-[1px] flex-1 bg-[#E5E7EB]" />
										</div>
										<div className="flex-1 pb-[8px]">
											<span className="mb-[4px] block font-lato text-[11px] font-semibold text-[#374151]">Tool Call</span>
											<div className="rounded-[6px] border border-[#DDD6FE] bg-[#F5F3FF] px-[12px] py-[8px]">
												<div className="flex items-center gap-[8px] mb-[6px]">
													<span className="font-mono text-[12px] font-bold text-[#7C3AED]">{name}</span>
												</div>
												<div className="grid grid-cols-2 gap-[8px]">
													<div>
														<span className="mb-[2px] block font-lato text-[10px] font-bold uppercase tracking-[0.5px] text-[#7C3AED]">Input</span>
														<JsonBlock data={args} maxHeight="80px" />
													</div>
													{result && (
														<div>
															<span className="mb-[2px] block font-lato text-[10px] font-bold uppercase tracking-[0.5px] text-[#6B7280]">Result</span>
															<JsonBlock data={parsedResult || result} maxHeight="80px" />
														</div>
													)}
												</div>
											</div>
										</div>
									</div>
								);
							})}

							{/* Current round output */}
							<div className="flex gap-[10px]">
								<div className="flex flex-col items-center">
									<div className="flex h-[28px] w-[28px] items-center justify-center rounded-full bg-[#059669] text-[11px] text-white font-bold">A</div>
								</div>
								<div className="flex-1">
									<span className="mb-[4px] block font-lato text-[11px] font-semibold text-[#374151]">
										LLM Response
										{invocation.stop_reason && (
											<span className={`ml-[8px] rounded-full px-[6px] py-[1px] font-lato text-[10px] font-semibold ${
												invocation.stop_reason === 'tool_use' ? 'bg-[#F5F3FF] text-[#7C3AED]' :
												invocation.stop_reason === 'end_turn' ? 'bg-[#F0FDF4] text-[#16A34A]' :
												'bg-[#F3F4F6] text-[#6B7280]'
											}`}>
												{invocation.stop_reason === 'tool_use' ? '🔧 called tool' :
												 invocation.stop_reason === 'end_turn' ? '✓ finished' :
												 invocation.stop_reason}
											</span>
										)}
									</span>

									{/* Tool calls this round made */}
									{currentToolCalls.length > 0 && (
										<div className="mb-[8px] flex flex-col gap-[6px]">
											{currentToolCalls.map((tc, i) => (
												<div key={i} className="rounded-[6px] border border-[#DDD6FE] bg-[#F5F3FF] px-[12px] py-[8px]">
													<div className="flex items-center gap-[6px] mb-[4px]">
														<span className="text-[11px]">🔧</span>
														<span className="font-mono text-[12px] font-bold text-[#7C3AED]">{tc.name}</span>
														<span className="font-lato text-[10px] text-[#9CA3AF]">→ pending result in next round</span>
													</div>
													<JsonBlock data={tc.input} maxHeight="60px" />
												</div>
											))}
										</div>
									)}

									{/* Final text response */}
									{invocation.response_content ? (
										<div className="rounded-[6px] bg-[#F0FDF4] border border-[#BBF7D0] px-[12px] py-[8px] max-h-[300px] overflow-auto">
											<pre className="whitespace-pre-wrap break-words font-lato text-[12px] leading-[20px] text-[#111827]">{invocation.response_content}</pre>
										</div>
									) : currentToolCalls.length === 0 && (
										<div className="rounded-[6px] bg-[#F9FAFB] border border-[#E5E7EB] px-[12px] py-[8px]">
											<span className="font-lato text-[12px] text-[#9CA3AF] italic">No text response — see tool call above</span>
										</div>
									)}
								</div>
							</div>
						</div>
					</div>
				);
			})()}

			{/* Prompt */}
			{activeTab === 'prompt' && (
				<div className="flex flex-col gap-[16px]">
					<div className="grid grid-cols-2 gap-[16px]">
						<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">System Prompt</span>
							<p className="mt-[4px] font-lato text-[14px] font-semibold text-[#111827]">
								{promptInfo.system_prompt_name || '-'}
								{promptInfo.system_prompt_version && <span className="ml-[6px] font-normal text-[#6B7280]">v{promptInfo.system_prompt_version}</span>}
							</p>
						</div>
						<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[16px]">
							<span className="font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">User Prompt</span>
							<p className="mt-[4px] font-lato text-[14px] font-semibold text-[#111827]">
								{promptInfo.user_prompt_name || '-'}
								{promptInfo.user_prompt_version && <span className="ml-[6px] font-normal text-[#6B7280]">v{promptInfo.user_prompt_version}</span>}
							</p>
						</div>
					</div>
					{promptInfo.rendered_system_prompt && (
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Rendered System Prompt</span>
							<div className="rounded-[6px] bg-[#FEF3C7] border border-[#FCD34D] p-[12px] max-h-[300px] overflow-auto">
								<pre className="whitespace-pre-wrap break-words font-lato text-[13px] leading-[22px] text-[#92400E]">{promptInfo.rendered_system_prompt}</pre>
							</div>
						</div>
					)}
					{invocation.context_snapshot && (
						<div>
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Context Snapshot (variables passed at runtime)</span>
							<JsonBlock data={invocation.context_snapshot} />
						</div>
					)}
				</div>
			)}

			{/* Cost Breakdown */}
			{activeTab === 'cost' && (
				<div>
					<div className="rounded-[8px] border border-[#E5E7EB] overflow-hidden">
						<table className="w-full">
							<thead className="bg-[#F9FAFB]">
								<tr>
									<th className="px-[16px] py-[10px] text-left font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Metric</th>
									<th className="px-[16px] py-[10px] text-right font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Value</th>
								</tr>
							</thead>
							<tbody>
								{[
									['Stop Reason', costInfo.stop_reason || '-'],
									['Input Tokens', (costInfo.input_tokens || 0).toLocaleString()],
									['Output Tokens', (costInfo.output_tokens || 0).toLocaleString()],
									['Cache Creation Tokens', (costInfo.cache_creation_tokens || 0).toLocaleString()],
									['Cache Read Tokens', (costInfo.cache_read_tokens || 0).toLocaleString()],
									['Total Cost', `$${costInfo.cost_usd || '0'}`],
									['Latency', costInfo.latency_ms ? `${costInfo.latency_ms}ms` : '-'],
								].map(([label, val]) => (
									<tr key={label} className="border-t border-[#E5E7EB]">
										<td className="px-[16px] py-[10px] font-lato text-[13px] text-[#374151]">{label}</td>
										<td className="px-[16px] py-[10px] text-right font-mono font-lato text-[13px] text-[#111827]">{val}</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>
			)}

			{/* Metadata */}
			{activeTab === 'metadata' && (
				<div className="grid grid-cols-2 gap-[12px]">
					{[
						['Triggered By', invocation.triggered_by],
						['User ID', invocation.user_id_ref || '-'],
						['Celery Task ID', invocation.celery_task_id || '-'],
						['Agent', invocation.agent_name || '-'],
						['Provider', `${invocation.provider_name} (${invocation.provider_slug})`],
						['Model', invocation.model],
						['Status', invocation.status],
						['Error Type', invocation.error_type || '-'],
						['Created', new Date(invocation.created_at).toLocaleString()],
						['Time to First Token', invocation.time_to_first_token_ms ? `${invocation.time_to_first_token_ms}ms` : '-'],
					].map(([label, val]) => (
						<div key={label} className="flex">
							<span className="w-[140px] shrink-0 font-lato text-[13px] text-[#6B7280]">{label}</span>
							<span className="font-lato text-[13px] text-[#111827]">{val}</span>
						</div>
					))}
					{invocation.request_params && (
						<div className="col-span-2">
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Request Params</span>
							<JsonBlock data={invocation.request_params} maxHeight="120px" />
						</div>
					)}
					{invocation.error_message && (
						<div className="col-span-2">
							<span className="mb-[6px] block font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">Error Message</span>
							<div className="rounded-[6px] bg-[#FEF2F2] border border-[#FECACA] p-[12px]">
								<pre className="whitespace-pre-wrap font-mono text-[12px] text-[#991B1B]">{invocation.error_message}</pre>
							</div>
						</div>
					)}
				</div>
			)}
		</div>
	);
}

/* ─── Single invocation row (used inside a run group or standalone) ─── */
function InvocationRow({ inv, onExpand, isExpanded, detail, loadingDetail, indent }) {
	const hasMemory = !!inv.session_id;
	return (
		<div className={`border-b border-[#E5E7EB] bg-white ${indent ? 'bg-[#FAFBFC]' : ''}`}>
			<div className="flex items-center px-[16px] py-[12px] cursor-pointer hover:bg-[#F3F4F6]" onClick={onExpand}>
				<button className={`text-[#6B7280] ${indent ? 'ml-[20px] mr-[8px]' : 'mr-[12px]'}`}>
					<svg width="10" height="10" viewBox="0 0 10 10" className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
						<path d="M3 1L7 5L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
					</svg>
				</button>
				<span className="mr-[16px] w-[120px] font-mono font-lato text-[12px] text-[#6B7280] truncate">
					{indent
						? <span className="text-[#9CA3AF]">r{inv.round_number ?? '?'}</span>
						: `inv_${String(inv.id).padStart(4, '0')}`
					}
				</span>
				<span className="mr-[16px] w-[120px] font-lato text-[12px] text-[#374151]">
					{new Date(inv.created_at).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', month: 'short', day: 'numeric' })}
				</span>
				<span className="mr-[16px] w-[220px] flex items-center gap-[6px]">
					<span className="font-lato text-[13px] font-medium text-[#111827] truncate">{inv.agent_name || '-'}</span>
					{hasMemory && (
						<span title="Memory-enabled session" className="shrink-0 inline-flex items-center gap-[3px] rounded-[4px] bg-[#EDE9FE] px-[4px] py-[1px]">
							<svg width="8" height="8" viewBox="0 0 12 12" fill="none">
								<path d="M6 1C3.24 1 1 3.24 1 6s2.24 5 5 5 5-2.24 5-5S8.76 1 6 1zm0 2a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0 7.1a3.6 3.6 0 01-3-1.62c.015-1 2-1.55 3-1.55s2.985.55 3 1.55A3.6 3.6 0 016 10.1z" fill="#7C3AED"/>
							</svg>
							<span className="font-lato text-[9px] font-semibold text-[#6D28D9]">mem</span>
						</span>
					)}
				</span>
				<span className="mr-[16px] w-[160px]">
					<span className="block font-lato text-[12px] text-[#111827]">{inv.provider_name}</span>
					<span className="block font-mono font-lato text-[11px] text-[#6B7280]">{inv.model}</span>
				</span>
				<span className="mr-[16px] w-[100px] font-mono font-lato text-[12px] text-[#374151]">
					{(inv.input_tokens || 0).toLocaleString()} / {(inv.output_tokens || 0).toLocaleString()}
				</span>
				<span className="mr-[16px] w-[70px] font-lato text-[12px] text-[#374151]">
					${parseFloat(inv.cost_usd || 0).toFixed(4)}
				</span>
				<span className="mr-[16px] w-[60px] font-lato text-[12px] text-[#346BD4]">
					{inv.latency_ms ? `${(inv.latency_ms / 1000).toFixed(1)}s` : '-'}
				</span>
				<span className="mr-[16px] w-[70px] font-lato text-[11px] text-[#6B7280] capitalize">
					{inv.triggered_by}
				</span>
				<span className="w-[80px]"><StatusBadge status={inv.status} /></span>
			</div>

			{isExpanded && (
				<div className="border-t border-[#E5E7EB] px-[24px] py-[16px] bg-[#F8FAFC]">
					{loadingDetail ? (
						<div className="flex items-center justify-center py-[32px]">
							<span className="inline-block h-[20px] w-[20px] animate-spin rounded-full border-[2px] border-[#346BD4] border-t-transparent" />
							<span className="ml-[8px] font-lato text-[13px] text-[#6B7280]">Loading details...</span>
						</div>
					) : (
						<InvocationDetail invocation={detail} />
					)}
				</div>
			)}
		</div>
	);
}

/* ─── Session group: top-level grouping for memory agents ─── */
function SessionGroup({ session_id, runs, onExpand, expandedId, detailData, loadingDetail, fetchDetail }) {
	const [groupExpanded, setGroupExpanded] = useState(false);

	// Aggregate across all rounds in all runs
	const allRounds = runs.flatMap(r => r.type === 'run' ? r.rounds : (r.inv ? [r.inv] : []));
	const firstRound = allRounds[0];
	const last = allRounds[allRounds.length - 1];
	const totalCost = allRounds.reduce((s, r) => s + parseFloat(r.cost_usd || 0), 0);
	const totalTokensIn = allRounds.reduce((s, r) => s + (r.input_tokens || 0), 0);
	const totalTokensOut = allRounds.reduce((s, r) => s + (r.output_tokens || 0), 0);
	const hasError = allRounds.some(r => r.status !== 'success');
	const overallStatus = hasError ? 'error' : (last?.status || 'success');
	const totalRounds = allRounds.length;

	const isUuid = /^[0-9a-f-]{32,36}$/i.test(session_id);
	const sessionLabel = isUuid
		? session_id.replace(/-/g, '').slice(0, 12)
		: session_id.length > 16 ? session_id.slice(0, 16) + '…' : session_id;
	const sessionStartId = firstRound ? `Session #${firstRound.id}` : null;

	return (
		<div className="border-b border-[#E5E7EB]">
			{/* Session header — distinct purple-tinted row with a left accent bar */}
			<div
				className="flex items-center cursor-pointer hover:bg-[#F5F3FF] bg-[#FAFAFF] border-l-[3px] border-l-[#7C3AED]"
				onClick={() => setGroupExpanded(g => !g)}
			>
				{/* Chevron */}
				<div className="flex items-center pl-[13px] pr-[12px] py-[10px]">
					<svg width="10" height="10" viewBox="0 0 10 10" className={`transition-transform text-[#7C3AED] ${groupExpanded ? 'rotate-90' : ''}`}>
						<path d="M3 1L7 5L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
					</svg>
				</div>

				{/* Session identity — matches RunGroup first-column width */}
				<div className="mr-[16px] flex flex-col gap-[3px] overflow-hidden" style={{ width: '120px' }}>
					<span
						className="inline-flex w-fit items-center gap-[4px] rounded-[6px] bg-[#7C3AED] px-[7px] py-[2px] font-mono text-[11px] font-semibold text-white truncate shadow-sm"
						title={session_id}
					>
						<svg width="8" height="8" viewBox="0 0 12 12" fill="none" className="shrink-0 opacity-80">
							<path d="M2 2h3v3H2zm5 0h3v3H7zm0 5h3v3H7zm-5 0h3v3H2z" fill="currentColor"/>
						</svg>
						{sessionLabel}
					</span>
					<span className="font-mono text-[10px] text-[#9CA3AF]">{sessionStartId}</span>
				</div>

				{/* Timestamp */}
				<span className="mr-[16px] w-[120px] font-lato text-[12px] text-[#374151]">
					{firstRound ? new Date(firstRound.created_at).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', month: 'short', day: 'numeric' }) : '-'}
				</span>

				{/* Agent */}
				<span className="mr-[16px] w-[220px] flex items-center gap-[6px]">
					<span className="font-lato text-[13px] font-medium text-[#111827] truncate">{firstRound?.agent_name || '-'}</span>
					<span className="shrink-0 inline-flex items-center gap-[3px] rounded-[4px] bg-[#EDE9FE] px-[4px] py-[1px]">
						<svg width="8" height="8" viewBox="0 0 12 12" fill="none">
							<path d="M6 1C3.24 1 1 3.24 1 6s2.24 5 5 5 5-2.24 5-5S8.76 1 6 1zm0 2a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0 7.1a3.6 3.6 0 01-3-1.62c.015-1 2-1.55 3-1.55s2.985.55 3 1.55A3.6 3.6 0 016 10.1z" fill="#7C3AED"/>
						</svg>
						<span className="font-lato text-[9px] font-semibold text-[#6D28D9]">memory</span>
					</span>
				</span>

				{/* Provider / Model */}
				<span className="mr-[16px] w-[160px]">
					<span className="block font-lato text-[12px] text-[#111827]">{firstRound?.provider_name}</span>
					<span className="block font-mono font-lato text-[11px] text-[#6B7280]">{firstRound?.model}</span>
				</span>

				{/* Tokens */}
				<span className="mr-[16px] w-[100px] font-mono font-lato text-[12px] text-[#374151]">
					{totalTokensIn.toLocaleString()} / {totalTokensOut.toLocaleString()}
				</span>

				{/* Cost */}
				<span className="mr-[16px] w-[70px] font-lato text-[12px] text-[#374151]">
					${totalCost.toFixed(4)}
				</span>

				{/* Latency — not meaningful at session level */}
				<span className="mr-[16px] w-[60px] font-lato text-[12px] text-[#9CA3AF]">—</span>

				{/* Trigger */}
				<span className="mr-[16px] w-[70px] font-lato text-[11px] text-[#6B7280] capitalize">
					{firstRound?.triggered_by}
				</span>

				{/* Status + counts */}
				<span className="w-[80px] flex items-center gap-[4px] flex-wrap">
					<StatusBadge status={overallStatus} />
					<span className="rounded-full bg-[#EDE9FE] px-[5px] py-[1px] font-lato text-[10px] font-semibold text-[#7C3AED] whitespace-nowrap">
						{runs.length}R · {totalRounds}rnd
					</span>
				</span>
			</div>

			{/* Expanded: show each run nested under the session */}
			{groupExpanded && (
				<div className="border-t border-[#E5E7EB] bg-[#F9F8FF]">
					{runs.map((run) =>
						run.type === 'run' ? (
							<RunGroup
								key={run.run_id}
								rounds={run.rounds}
								runLabel={run.run_label}
								expandedId={expandedId}
								onExpand={onExpand}
								detailData={detailData}
								loadingDetail={loadingDetail}
								fetchDetail={fetchDetail}
								indented
							/>
						) : (
							<InvocationRow
								key={run.inv.id}
								inv={run.inv}
								indent
								isExpanded={expandedId === run.inv.id}
								onExpand={() => { onExpand(run.inv.id); fetchDetail(run.inv.id); }}
								detail={detailData[run.inv.id]}
								loadingDetail={loadingDetail && expandedId === run.inv.id}
							/>
						)
					)}
				</div>
			)}
		</div>
	);
}

/* ─── Run group: one header row that expands to show all rounds ─── */
function RunGroup({ rounds, runLabel, onExpand, expandedId, detailData, loadingDetail, fetchDetail, indented }) {
	const [groupExpanded, setGroupExpanded] = useState(false);
	// Summary from all rounds
	const first = rounds[0];
	const last = rounds[rounds.length - 1];
	const totalCost = rounds.reduce((s, r) => s + parseFloat(r.cost_usd || 0), 0);
	const totalTokensIn = rounds.reduce((s, r) => s + (r.input_tokens || 0), 0);
	const totalTokensOut = rounds.reduce((s, r) => s + (r.output_tokens || 0), 0);
	const totalLatency = rounds.reduce((s, r) => s + (r.latency_ms || 0), 0);
	const hasError = rounds.some(r => r.status !== 'success');
	const overallStatus = hasError ? 'error' : last.status;
	const roundCount = rounds.length;

	return (
		<div className={`border-b border-[#E5E7EB] ${indented ? 'border-l-2 border-l-[#7C3AED]' : ''}`}>
			{/* Group header */}
			<div
				className={`flex items-center px-[16px] py-[12px] cursor-pointer ${indented ? 'hover:bg-[#F0EBFF] bg-[#FAF9FF]' : 'hover:bg-[#F9FAFB] bg-white'}`}
				onClick={() => setGroupExpanded(g => !g)}
			>
				<button className="mr-[12px] text-[#6B7280]">
					<svg width="10" height="10" viewBox="0 0 10 10" className={`transition-transform ${groupExpanded ? 'rotate-90' : ''}`}>
						<path d="M3 1L7 5L3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
					</svg>
				</button>
				<span className="mr-[16px] w-[120px] font-mono text-[12px] font-medium text-[#374151]">
					{runLabel || `Run #${first.id}`}
				</span>
				<span className="mr-[16px] w-[120px] font-lato text-[12px] text-[#374151]">
					{new Date(first.created_at).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', month: 'short', day: 'numeric' })}
				</span>
				<span className="mr-[16px] w-[220px] font-lato text-[13px] font-medium text-[#111827] truncate">
					{first.agent_name || '-'}
				</span>
				<span className="mr-[16px] w-[160px]">
					<span className="block font-lato text-[12px] text-[#111827]">{first.provider_name}</span>
					<span className="block font-mono font-lato text-[11px] text-[#6B7280]">{first.model}</span>
				</span>
				<span className="mr-[16px] w-[100px] font-mono font-lato text-[12px] text-[#374151]">
					{totalTokensIn.toLocaleString()} / {totalTokensOut.toLocaleString()}
				</span>
				<span className="mr-[16px] w-[70px] font-lato text-[12px] text-[#374151]">
					${totalCost.toFixed(4)}
				</span>
				<span className="mr-[16px] w-[60px] font-lato text-[12px] text-[#346BD4]">
					{totalLatency ? `${(totalLatency / 1000).toFixed(1)}s` : '-'}
				</span>
				<span className="mr-[16px] w-[70px] font-lato text-[11px] text-[#6B7280] capitalize">
					{first.triggered_by}
				</span>
				<span className="w-[80px] flex items-center gap-[4px]">
					<StatusBadge status={overallStatus} />
					{roundCount > 1 && (
						<span className="rounded-full bg-[#EFF6FF] px-[5px] py-[1px] font-lato text-[10px] font-semibold text-[#2563EB] whitespace-nowrap">
							{roundCount} rnd
						</span>
					)}
				</span>
			</div>

			{/* Expanded: show each round as an indented row */}
			{groupExpanded && (
				<div className="border-t border-[#E5E7EB] bg-[#F9FAFB]">
					{rounds.map((inv) => (
						<InvocationRow
							key={inv.id}
							inv={inv}
							indent
							isExpanded={expandedId === inv.id}
							onExpand={() => { onExpand(inv.id); fetchDetail(inv.id); }}
							detail={detailData[inv.id]}
							loadingDetail={loadingDetail && expandedId === inv.id}
						/>
					))}
				</div>
			)}
		</div>
	);
}

/* ─── Filter chip used in the active-filter bar ─── */
function FilterChip({ label, onRemove }) {
	return (
		<span className="inline-flex items-center gap-[4px] rounded-full bg-[#EFF6FF] border border-[#BFDBFE] px-[8px] py-[3px] font-lato text-[12px] text-[#1D4ED8]">
			{label}
			<button onClick={onRemove} className="ml-[2px] text-[#60A5FA] hover:text-[#1D4ED8]">
				<svg width="10" height="10" viewBox="0 0 10 10">
					<path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
				</svg>
			</button>
		</span>
	);
}

/* ─── Searchable agent filter dropdown (handles paginated agents API) ─── */
function SearchableAgentFilter({ appId, triggerApi, value, valueName, onChange }) {
	const [open, setOpen] = useState(false);
	const [search, setSearch] = useState('');
	const [results, setResults] = useState([]);
	const [loading, setLoading] = useState(false);
	const containerRef = useRef(null);
	const inputRef = useRef(null);
	const isActive = !!value;

	// Fetch agents with debounce whenever dropdown is open or search changes
	useEffect(() => {
		if (!open) return;
		const t = setTimeout(async () => {
			setLoading(true);
			const params = new URLSearchParams({ page: '1', page_size: '20' });
			if (search) params.set('search', search);
			const { response, success } = await triggerApi({
				url: `/api/v1/apps/${appId}/ai/agents/?${params}`,
				type: 'GET',
				loader: false,
			});
			if (success && response) {
				const data = response.agents || {};
				setResults(Array.isArray(data.records) ? data.records : (Array.isArray(data) ? data : []));
			}
			setLoading(false);
		}, 250);
		return () => clearTimeout(t);
	}, [open, search, appId]);

	// Close on outside click
	useEffect(() => {
		const handler = (e) => {
			if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
		};
		document.addEventListener('mousedown', handler);
		return () => document.removeEventListener('mousedown', handler);
	}, []);

	const handleOpen = () => {
		setSearch('');
		setOpen(true);
		setTimeout(() => inputRef.current?.focus(), 0);
	};

	const handleSelect = (agent) => {
		onChange(String(agent.id), agent.name);
		setOpen(false);
	};

	const handleClear = (e) => {
		e.stopPropagation();
		onChange('', '');
	};

	return (
		<div className="relative" ref={containerRef}>
			{/* Trigger button — matches FilterSelect appearance */}
			<button
				type="button"
				onClick={open ? () => setOpen(false) : handleOpen}
				className={`h-[34px] flex items-center gap-[6px] rounded-[6px] border pl-[8px] pr-[6px] font-lato text-[13px] outline-none cursor-pointer transition-colors ${
					isActive
						? 'border-[#346BD4] bg-[#EFF6FF] text-[#1D4ED8] font-medium'
						: 'border-[#DDE2E5] bg-white text-[#374151] hover:border-[#346BD4]'
				}`}
			>
				<span className="max-w-[140px] truncate">
					{isActive ? valueName || 'Agent' : 'All Agents'}
				</span>
				{isActive ? (
					<span
						onClick={handleClear}
						className="ml-[2px] flex items-center text-[#60A5FA] hover:text-[#1D4ED8]"
					>
						<svg width="10" height="10" viewBox="0 0 10 10">
							<path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
						</svg>
					</span>
				) : (
					<svg width="10" height="10" viewBox="0 0 10 10" className="text-[#9CA3AF]">
						<path d="M2 3l3 4 3-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
					</svg>
				)}
			</button>

			{/* Dropdown */}
			{open && (
				<div className="absolute top-[38px] left-0 z-50 w-[220px] rounded-[8px] border border-[#E5E7EB] bg-white shadow-lg overflow-hidden">
					{/* Search input */}
					<div className="flex items-center gap-[6px] border-b border-[#E5E7EB] px-[10px] py-[7px]">
						<svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="flex-shrink-0 text-[#9CA3AF]">
							<circle cx="5" cy="5" r="3.5" stroke="currentColor" strokeWidth="1.3"/>
							<path d="M8 8l2.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
						</svg>
						<input
							ref={inputRef}
							value={search}
							onChange={(e) => setSearch(e.target.value)}
							placeholder="Search agents…"
							className="flex-1 min-w-0 font-lato text-[13px] text-[#111827] outline-none placeholder-[#9CA3AF]"
						/>
						{loading && (
							<svg className="animate-spin flex-shrink-0 text-[#346BD4]" width="11" height="11" viewBox="0 0 11 11" fill="none">
								<path d="M5.5 1.5A4 4 0 1 0 9.5 5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
							</svg>
						)}
					</div>

					{/* Results */}
					<div className="max-h-[200px] overflow-y-auto">
						{/* "All Agents" option */}
						<button
							type="button"
							onClick={() => { onChange('', ''); setOpen(false); }}
							className={`w-full text-left px-[10px] py-[7px] font-lato text-[13px] hover:bg-[#F3F4F6] transition-colors ${!value ? 'text-[#346BD4] font-medium bg-[#EFF6FF]' : 'text-[#374151]'}`}
						>
							All Agents
						</button>
						{results.map((agent) => (
							<button
								key={agent.id}
								type="button"
								onClick={() => handleSelect(agent)}
								className={`w-full text-left px-[10px] py-[7px] font-lato text-[13px] hover:bg-[#F3F4F6] transition-colors truncate ${String(agent.id) === value ? 'text-[#346BD4] font-medium bg-[#EFF6FF]' : 'text-[#374151]'}`}
							>
								{agent.name}
							</button>
						))}
						{!loading && results.length === 0 && (
							<p className="px-[10px] py-[12px] font-lato text-[12px] text-[#9CA3AF] text-center">No agents found</p>
						)}
					</div>
				</div>
			)}
		</div>
	);
}

/* ─── Select with a label pill (replaces bare <select>) ─── */
function FilterSelect({ label, value, onChange, options, accentColor }) {
	const accent = accentColor || '#346BD4';
	const isActive = !!value;
	return (
		<div className="relative">
			<select
				value={value}
				onChange={onChange}
				className={`h-[34px] rounded-[6px] border pl-[8px] pr-[24px] font-lato text-[13px] outline-none appearance-none cursor-pointer transition-colors ${
					isActive
						? 'border-[#346BD4] bg-[#EFF6FF] text-[#1D4ED8] font-medium'
						: 'border-[#DDE2E5] bg-white text-[#374151] hover:border-[#346BD4]'
				}`}
				style={isActive ? { borderColor: accent, backgroundColor: `${accent}18`, color: accent } : {}}
			>
				{options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
			</select>
			{/* caret */}
			<svg width="10" height="10" viewBox="0 0 10 10" className="pointer-events-none absolute right-[7px] top-1/2 -translate-y-1/2 text-[#9CA3AF]">
				<path d="M2 3l3 4 3-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
			</svg>
		</div>
	);
}

/* ─── Pagination bar ─── */
function PaginationBar({ page, totalPages, totalRecords, onPrev, onNext, onGoTo }) {
	const pageNumbers = [];
	const delta = 2;
	for (let i = Math.max(1, page - delta); i <= Math.min(totalPages, page + delta); i++) {
		pageNumbers.push(i);
	}
	const showLeftEllipsis = pageNumbers[0] > 2;
	const showRightEllipsis = pageNumbers[pageNumbers.length - 1] < totalPages - 1;

	return (
		<div className="flex items-center justify-between px-[16px] py-[14px] border-t border-[#E5E7EB] bg-[#F9FAFB] rounded-b-[8px]">
			<span className="font-lato text-[12px] text-[#6B7280]">
				{totalRecords != null ? `${totalRecords.toLocaleString()} invocation${totalRecords !== 1 ? 's' : ''}` : ''}
			</span>
			<div className="flex items-center gap-[4px]">
				<button
					onClick={onPrev}
					disabled={page === 1}
					className="flex items-center gap-[4px] rounded-[6px] border border-[#DDE2E5] px-[10px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
				>
					<svg width="12" height="12" viewBox="0 0 10 10"><path d="M7 1L3 5l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/></svg>
					Prev
				</button>

				{pageNumbers[0] > 1 && (
					<>
						<button onClick={() => onGoTo(1)} className="rounded-[6px] border border-[#DDE2E5] px-[8px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white">1</button>
						{showLeftEllipsis && <span className="px-[4px] font-lato text-[12px] text-[#9CA3AF]">…</span>}
					</>
				)}

				{pageNumbers.map(n => (
					<button
						key={n}
						onClick={() => onGoTo(n)}
						className={`rounded-[6px] border px-[8px] py-[5px] font-lato text-[12px] transition-colors ${
							n === page
								? 'border-[#346BD4] bg-[#346BD4] text-white font-semibold'
								: 'border-[#DDE2E5] text-[#374151] hover:bg-white'
						}`}
					>
						{n}
					</button>
				))}

				{pageNumbers[pageNumbers.length - 1] < totalPages && (
					<>
						{showRightEllipsis && <span className="px-[4px] font-lato text-[12px] text-[#9CA3AF]">…</span>}
						<button onClick={() => onGoTo(totalPages)} className="rounded-[6px] border border-[#DDE2E5] px-[8px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white">{totalPages}</button>
					</>
				)}

				<button
					onClick={onNext}
					disabled={page === totalPages}
					className="flex items-center gap-[4px] rounded-[6px] border border-[#DDE2E5] px-[10px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
				>
					Next
					<svg width="12" height="12" viewBox="0 0 10 10"><path d="M3 1l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/></svg>
				</button>
			</div>
			<span className="font-lato text-[12px] text-[#6B7280]">Page {page} of {totalPages}</span>
		</div>
	);
}

/* ─── Relative time helper ─── */
function useRelativeTime(timestamp) {
	const [label, setLabel] = useState('');
	useEffect(() => {
		if (!timestamp) { setLabel(''); return; }
		const update = () => {
			const diff = Date.now() - timestamp;
			if (diff < 60000) setLabel('just now');
			else if (diff < 3600000) setLabel(`${Math.floor(diff / 60000)} min ago`);
			else setLabel(`${Math.floor(diff / 3600000)} hr ago`);
		};
		update();
		const id = setInterval(update, 30000);
		return () => clearInterval(id);
	}, [timestamp]);
	return label;
}

/* ─── Main Component ─── */
export default function InvocationLogs({ onReady, refreshSignal, onFetchComplete, lastFetchedAt }) {
	const { appId } = useParams();
	const triggerApi = useApi();

	const [invocations, setInvocations] = useState([]);
	const [totalRecords, setTotalRecords] = useState(0);
	const [initialLoading, setInitialLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [stats, setStats] = useState({});
	const [providers, setProviders] = useState([]);
	const [expandedId, setExpandedId] = useState(null);
	const [detailData, setDetailData] = useState({});
	const [loadingDetail, setLoadingDetail] = useState(false);
	const [page, setPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const readyCalledRef = useRef(false);
	const updatedLabel = useRelativeTime(lastFetchedAt);

	// Filters
	const [filterAgent, setFilterAgent] = useState('');
	const [filterAgentName, setFilterAgentName] = useState('');
	const [filterProvider, setFilterProvider] = useState('');
	const [filterStatus, setFilterStatus] = useState('');
	const [filterTriggeredBy, setFilterTriggeredBy] = useState('');
	const [filterMemory, setFilterMemory] = useState(''); // 'yes' | 'no' | ''
	const [filterDateStart, setFilterDateStart] = useState('');
	const [filterDateEnd, setFilterDateEnd] = useState('');

	const fetchStats = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/invocations/stats/`, type: 'GET', loader: false });
		if (success && response) setStats(response);
	}, [appId, triggerApi]);

	const fetchInvocations = useCallback(async ({ background = false } = {}) => {
		if (!background) {
			// only set initialLoading on the very first load (handled by the appId effect below)
		} else {
			setRefreshing(true);
		}
		const params = new URLSearchParams({ page: String(page) });
		if (filterAgent) params.set('agent_id', filterAgent);
		if (filterProvider) params.set('provider_id', filterProvider);
		if (filterStatus) params.set('status', filterStatus);
		if (filterTriggeredBy) params.set('triggered_by', filterTriggeredBy);
		if (filterMemory) params.set('has_session', filterMemory);
		if (filterDateStart) params.set('start_date', filterDateStart);
		if (filterDateEnd) params.set('end_date', filterDateEnd);

		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/invocations/?${params}`, type: 'GET', loader: false });
		if (success && response) {
			const data = response.invocations || {};
			const records = data.records || [];
			setInvocations(records);
			setTotalPages(data.total_pages || 1);
			setTotalRecords(data.total_records || 0);
			onFetchComplete?.();
		}
		if (background) setRefreshing(false);
	}, [appId, triggerApi, page, filterAgent, filterProvider, filterStatus, filterTriggeredBy, filterMemory, filterDateStart, filterDateEnd, onFetchComplete]);

	// Manual refresh — updates both invocations list AND stats
	const handleRefresh = useCallback(async () => {
		setRefreshing(true);
		await Promise.all([fetchStats(), fetchInvocations({ background: true })]);
		setRefreshing(false);
	}, [fetchStats, fetchInvocations]);

	const fetchDetail = async (id) => {
		if (detailData[id]) return;
		setLoadingDetail(true);
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/invocations/${id}/`, type: 'GET', loader: false });
		setLoadingDetail(false);
		if (success && response?.invocation) {
			setDetailData((prev) => ({ ...prev, [id]: response.invocation }));
		}
	};

	const fetchDropdowns = useCallback(async () => {
		const { response, success } = await triggerApi({ url: `/api/v1/apps/${appId}/ai/providers/`, type: 'GET', loader: false });
		if (success) setProviders(response?.providers?.records || response?.providers || []);
	}, [appId, triggerApi]);

	useEffect(() => {
		setInitialLoading(true);
		Promise.all([fetchStats(), fetchDropdowns(), fetchInvocations()]).finally(() => {
			setInitialLoading(false);
			if (!readyCalledRef.current && onReady) {
				readyCalledRef.current = true;
				onReady();
			}
		});
	}, [appId]);
	useEffect(() => { fetchInvocations(); }, [fetchInvocations]);

	// Background re-fetch on tab activation — only invocations list, not stats
	const isFirstRefreshSignal = useRef(true);
	useEffect(() => {
		if (isFirstRefreshSignal.current) { isFirstRefreshSignal.current = false; return; }
		if (!refreshSignal) return;
		fetchInvocations({ background: true });
	}, [refreshSignal]);

	const handleExpand = (id) => {
		if (expandedId === id) { setExpandedId(null); return; }
		setExpandedId(id);
	};

	const clearFilter = (setter) => { setter(''); setPage(1); };

	// Backend returns pre-grouped records: type 'session' | 'run' | 'standalone'
	const groupedRows = invocations;

	// Active filter labels for the chip bar
	const activeFilters = [];
	const providerObj = providers.find(p => String(p.id) === String(filterProvider));
	if (filterAgent) activeFilters.push({ label: `Agent: ${filterAgentName || filterAgent}`, clear: () => { setFilterAgent(''); setFilterAgentName(''); setPage(1); } });
	if (providerObj) activeFilters.push({ label: `Provider: ${providerObj.name}`, clear: () => clearFilter(setFilterProvider) });
	if (filterStatus) activeFilters.push({ label: `Status: ${filterStatus.replace('_', ' ')}`, clear: () => clearFilter(setFilterStatus) });
	if (filterTriggeredBy) activeFilters.push({ label: `Trigger: ${filterTriggeredBy}`, clear: () => clearFilter(setFilterTriggeredBy) });
	if (filterMemory === 'yes') activeFilters.push({ label: 'Memory: enabled', clear: () => clearFilter(setFilterMemory) });
	if (filterMemory === 'no') activeFilters.push({ label: 'Memory: disabled', clear: () => clearFilter(setFilterMemory) });
	if (filterDateStart && filterDateEnd) activeFilters.push({ label: `Date: ${filterDateStart} → ${filterDateEnd}`, clear: () => { setFilterDateStart(''); setFilterDateEnd(''); setPage(1); } });
	else if (filterDateStart) activeFilters.push({ label: `From: ${filterDateStart}`, clear: () => { setFilterDateStart(''); setPage(1); } });
	else if (filterDateEnd) activeFilters.push({ label: `Until: ${filterDateEnd}`, clear: () => { setFilterDateEnd(''); setPage(1); } });

	const hasFilters = activeFilters.length > 0 || !!filterDateStart || !!filterDateEnd;

	return (
		<div className="flex flex-col gap-[20px] pb-[32px]">
			{/* Header */}
			<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
				<div className="flex items-start justify-between gap-[16px]">
					<div>
						<h2 className="font-source-sans-pro text-[18px] font-semibold text-[#111827]">Invocation Logs</h2>
						<p className="mb-[16px] font-lato text-[14px] text-[#6B7280]">
							Complete audit trail of every agent run — LLM calls, resolved prompts, cost breakdown
						</p>
					</div>
					<div className="flex items-center gap-[8px] flex-shrink-0 mt-[2px]">
						{refreshing ? (
							<span className="font-lato text-[12px] text-[#6B7280]">Refreshing…</span>
						) : updatedLabel ? (
							<span className="font-lato text-[12px] text-[#9CA3AF]">Updated {updatedLabel}</span>
						) : null}
						<button
							onClick={handleRefresh}
							disabled={refreshing}
							className="flex items-center gap-[5px] rounded-[6px] border border-[#DDE2E5] px-[10px] py-[5px] font-lato text-[12px] text-[#374151] hover:bg-[#F9FAFB] disabled:opacity-50 transition-colors"
						>
							<svg
								width="12" height="12" viewBox="0 0 12 12" fill="none"
								className={refreshing ? 'animate-spin' : ''}
							>
								<path d="M10.5 6A4.5 4.5 0 1 1 8.5 2.1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
								<path d="M8.5 1v2.5H11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
							</svg>
							Refresh
						</button>
					</div>
				</div>
				<div className="flex flex-wrap items-center gap-[20px]">
					<StatCard icon="🏃" label="Total Runs" value={stats.total_runs ?? '-'} />
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<StatCard icon="📅" label="Today" value={stats.today ?? '-'} />
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<StatCard icon="⚠" label="Errors (24h)" value={stats.errors_24h ?? '-'} color={stats.errors_24h > 0 ? 'text-[#EF4444]' : 'text-[#111827]'} />
					<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
					<StatCard icon="💰" label="Cost Today" value={stats.cost_today != null ? `$${parseFloat(stats.cost_today).toFixed(2)}` : '-'} />
				</div>
			</div>

			{/* Filter bar */}
			<div className="rounded-[8px] border border-[#E5E7EB] bg-white p-[12px] flex flex-wrap items-center gap-[8px]">
				<span className="font-lato text-[12px] font-semibold text-[#6C747D] mr-[4px]">Filter:</span>

				<SearchableAgentFilter
					appId={appId}
					triggerApi={triggerApi}
					value={filterAgent}
					valueName={filterAgentName}
					onChange={(id, name) => { setFilterAgent(id); setFilterAgentName(name || ''); setPage(1); }}
				/>
				<FilterSelect
					label="Provider"
					value={filterProvider}
					onChange={(e) => { setFilterProvider(e.target.value); setPage(1); }}
					options={[{ value: '', label: 'All Providers' }, ...providers.map(p => ({ value: String(p.id), label: p.name }))]}
				/>
				<FilterSelect
					label="Status"
					value={filterStatus}
					onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
					options={[
						{ value: '', label: 'All Status' },
						{ value: 'success', label: '✓ Success' },
						{ value: 'error', label: '✕ Error' },
						{ value: 'timeout', label: '⏱ Timeout' },
						{ value: 'rate_limited', label: '⚡ Rate Limited' },
						{ value: 'budget_exceeded', label: '💸 Budget Exceeded' },
					]}
				/>
				<FilterSelect
					label="Trigger"
					value={filterTriggeredBy}
					onChange={(e) => { setFilterTriggeredBy(e.target.value); setPage(1); }}
					options={[
						{ value: '', label: 'All Triggers' },
						{ value: 'user', label: '👤 User' },
						{ value: 'celery', label: '⚙ Celery' },
						{ value: 'cron', label: '🕐 Cron' },
						{ value: 'system', label: '🔧 System' },
					]}
				/>
				<FilterSelect
					label="Memory"
					value={filterMemory}
					onChange={(e) => { setFilterMemory(e.target.value); setPage(1); }}
					accentColor="#7C3AED"
					options={[
						{ value: '', label: 'Memory: Any' },
						{ value: 'yes', label: '🧠 Memory On' },
						{ value: 'no', label: 'No Memory' },
					]}
				/>

				{/* Date range inputs */}
				<div className="flex items-center gap-[4px]">
					<span className="font-lato text-[12px] text-[#6C747D]">From</span>
					<input
						type="date"
						value={filterDateStart}
						max={filterDateEnd || undefined}
						onChange={(e) => { setFilterDateStart(e.target.value); setPage(1); }}
						className={`h-[34px] rounded-[6px] border px-[8px] font-lato text-[13px] outline-none cursor-pointer transition-colors ${filterDateStart ? 'border-[#346BD4] bg-[#EFF6FF] text-[#1D4ED8]' : 'border-[#DDE2E5] bg-white text-[#374151] hover:border-[#346BD4]'}`}
					/>
					<span className="font-lato text-[12px] text-[#6C747D]">To</span>
					<input
						type="date"
						value={filterDateEnd}
						min={filterDateStart || undefined}
						onChange={(e) => { setFilterDateEnd(e.target.value); setPage(1); }}
						className={`h-[34px] rounded-[6px] border px-[8px] font-lato text-[13px] outline-none cursor-pointer transition-colors ${filterDateEnd ? 'border-[#346BD4] bg-[#EFF6FF] text-[#1D4ED8]' : 'border-[#DDE2E5] bg-white text-[#374151] hover:border-[#346BD4]'}`}
					/>
				</div>

				{/* Predefined date shortcuts */}
				<div className="flex items-center gap-[4px]">
					{[
						{ label: 'Today', days: 0 },
						{ label: '7d', days: 7 },
						{ label: '30d', days: 30 },
					].map(({ label, days }) => {
						const today = new Date();
						const end = today.toISOString().slice(0, 10);
						const start = days === 0 ? end : new Date(today.setDate(today.getDate() - days)).toISOString().slice(0, 10);
						const isActive = filterDateStart === start && filterDateEnd === end;
						return (
							<button
								key={label}
								onClick={() => { setFilterDateStart(start); setFilterDateEnd(end); setPage(1); }}
								className={`h-[34px] rounded-[6px] border px-[10px] font-lato text-[12px] transition-colors ${isActive ? 'border-[#346BD4] bg-[#346BD4] text-white' : 'border-[#DDE2E5] bg-white text-[#374151] hover:border-[#346BD4]'}`}
							>
								{label}
							</button>
						);
					})}
				</div>

				{hasFilters && (
					<button
						onClick={() => { setFilterAgent(''); setFilterAgentName(''); setFilterProvider(''); setFilterStatus(''); setFilterTriggeredBy(''); setFilterMemory(''); setFilterDateStart(''); setFilterDateEnd(''); setPage(1); }}
						className="ml-auto font-lato text-[12px] text-[#6B7280] hover:text-[#EF4444] underline"
					>
						Clear all
					</button>
				)}
			</div>

			{/* Active filter chips */}
			{hasFilters && (
				<div className="flex flex-wrap items-center gap-[6px] -mt-[10px]">
					{activeFilters.map((f, i) => (
						<FilterChip key={i} label={f.label} onRemove={f.clear} />
					))}
				</div>
			)}

			{/* Table + pagination as one card */}
			<div className="rounded-[8px] border border-[#E5E7EB] bg-white overflow-hidden">
				{/* Table header */}
				<div className="flex items-center px-[16px] py-[10px] bg-[#F9FAFB] border-b border-[#E5E7EB] font-lato text-[11px] font-bold uppercase tracking-[0.6px] text-[#6C747D]">
					<span className="mr-[12px] w-[10px]" />
					<span className="mr-[16px] w-[120px]">ID</span>
					<span className="mr-[16px] w-[120px]">Timestamp</span>
					<span className="mr-[16px] w-[220px]">Agent</span>
					<span className="mr-[16px] w-[160px]">Provider / Model</span>
					<span className="mr-[16px] w-[100px]">Tokens</span>
					<span className="mr-[16px] w-[70px]">Cost</span>
					<span className="mr-[16px] w-[60px]">Latency</span>
					<span className="mr-[16px] w-[70px]">Trigger</span>
					<span className="w-[80px]">Status</span>
				</div>

				{!initialLoading && invocations.length === 0 ? (
					<div className="px-[24px] py-[48px] text-center">
						<p className="font-lato text-[14px] text-[#9CA3AF]">No invocations found.</p>
					</div>
				) : (
					groupedRows.map((group) =>
						group.type === 'session' ? (
							<SessionGroup
								key={group.session_id}
								session_id={group.session_id}
								runs={group.runs}
								expandedId={expandedId}
								onExpand={handleExpand}
								detailData={detailData}
								loadingDetail={loadingDetail}
								fetchDetail={fetchDetail}
							/>
						) : group.type === 'run' ? (
							<RunGroup
								key={group.run_id}
								rounds={group.rounds}
								runLabel={group.run_label}
								expandedId={expandedId}
								onExpand={handleExpand}
								detailData={detailData}
								loadingDetail={loadingDetail}
								fetchDetail={fetchDetail}
							/>
						) : (
							<InvocationRow
								key={group.inv.id}
								inv={group.inv}
								isExpanded={expandedId === group.inv.id}
								onExpand={() => { handleExpand(group.inv.id); fetchDetail(group.inv.id); }}
								detail={detailData[group.inv.id]}
								loadingDetail={loadingDetail && expandedId === group.inv.id}
							/>
						)
					)
				)}

				{/* Pagination — always inside the card so it's visible without scrolling */}
				<PaginationBar
					page={page}
					totalPages={totalPages}
					totalRecords={totalRecords}
					onPrev={() => setPage(p => Math.max(1, p - 1))}
					onNext={() => setPage(p => Math.min(totalPages, p + 1))}
					onGoTo={setPage}
				/>
			</div>
		</div>
	);
}
