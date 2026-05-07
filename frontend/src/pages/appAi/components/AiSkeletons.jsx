/**
 * AiSkeletons.jsx
 * Centralized skeleton/loading components for the AI module.
 * Prefer skeletons over spinners to prevent layout shift.
 */

/* ─── Primitive ──────────────────────────────────────────────────── */
function Shimmer({ className = '' }) {
	return (
		<div
			className={`animate-pulse rounded bg-[#E5E7EB] ${className}`}
			style={{ backgroundImage: 'linear-gradient(90deg, #E5E7EB 25%, #F3F4F6 50%, #E5E7EB 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.4s infinite' }}
		/>
	);
}

/* ─── Header card skeleton (shared by all tabs) ──────────────────── */
export function HeaderCardSkeleton() {
	return (
		<div className="rounded-[16px] border border-[#E5E7EB] bg-white p-[24px]">
			<div className="flex items-center justify-between mb-[16px]">
				<div className="flex flex-col gap-[8px]">
					<Shimmer className="h-[22px] w-[180px]" />
					<Shimmer className="h-[14px] w-[300px]" />
				</div>
				<Shimmer className="h-[36px] w-[120px] rounded-[8px]" />
			</div>
			<div className="flex items-center gap-[16px]">
				<Shimmer className="h-[14px] w-[80px]" />
				<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
				<Shimmer className="h-[14px] w-[60px]" />
				<div className="h-[16px] w-[1px] bg-[#E5E7EB]" />
				<Shimmer className="h-[14px] w-[80px]" />
			</div>
		</div>
	);
}

/* ─── Generic list-row skeleton ───────────────────────────────────── */
function ListRowSkeleton({ cols = 5 }) {
	const widths = ['w-[180px]', 'w-[120px]', 'w-[150px]', 'w-[80px]', 'w-[100px]'];
	return (
		<div className="flex items-center gap-[16px] rounded-[12px] border border-[#E5E7EB] bg-white px-[20px] py-[16px]">
			<Shimmer className="h-[36px] w-[36px] rounded-[8px] shrink-0" />
			{Array.from({ length: cols }).map((_, i) => (
				<Shimmer key={i} className={`h-[14px] ${widths[i % widths.length]}`} />
			))}
		</div>
	);
}

/* ─── Provider tab skeleton ───────────────────────────────────────── */
export function ProvidersListSkeleton() {
	return (
		<div className="flex flex-col gap-[24px]">
			<HeaderCardSkeleton />
			<div className="flex flex-col gap-[12px]">
				{[1, 2, 3].map((i) => (
					<div key={i} className="rounded-[16px] border border-[#E5E7EB] bg-white p-[20px]">
						<div className="flex items-center gap-[16px]">
							<Shimmer className="h-[44px] w-[44px] rounded-[10px] shrink-0" />
							<div className="flex flex-col gap-[8px] flex-1">
								<Shimmer className="h-[16px] w-[160px]" />
								<Shimmer className="h-[12px] w-[240px]" />
							</div>
							<Shimmer className="h-[28px] w-[70px] rounded-full" />
							<Shimmer className="h-[32px] w-[90px] rounded-[8px]" />
							<Shimmer className="h-[32px] w-[32px] rounded-[8px]" />
						</div>
					</div>
				))}
			</div>
		</div>
	);
}

/* ─── Agents tab skeleton ─────────────────────────────────────────── */
export function AgentsListSkeleton() {
	return (
		<div className="flex flex-col gap-[24px]">
			<HeaderCardSkeleton />
			{/* Column header ghost */}
			<div className="flex items-center px-[72px] gap-[20px]">
				{['w-[180px]', 'w-[100px]', 'w-[150px]', 'w-[70px]', 'w-[40px]', 'w-[70px]'].map((w, i) => (
					<Shimmer key={i} className={`h-[10px] ${w}`} />
				))}
			</div>
			<div className="flex flex-col gap-[8px]">
				{[1, 2, 3, 4].map((i) => (
					<ListRowSkeleton key={i} cols={6} />
				))}
			</div>
		</div>
	);
}

/* ─── Prompts tab skeleton ────────────────────────────────────────── */
export function PromptsListSkeleton() {
	return (
		<div className="flex flex-col gap-[24px]">
			<HeaderCardSkeleton />
			{/* Search bar ghost */}
			<div className="flex items-center gap-[10px]">
				<Shimmer className="h-[36px] w-[360px] rounded-[8px]" />
				<Shimmer className="h-[36px] w-[60px] rounded-[7px]" />
				<Shimmer className="h-[36px] w-[70px] rounded-[7px]" />
				<Shimmer className="h-[36px] w-[60px] rounded-[7px]" />
			</div>
			<div className="flex flex-col gap-[10px]">
				{[1, 2, 3, 4, 5].map((i) => (
					<div key={i} className="rounded-[12px] border border-[#E5E7EB] bg-white px-[20px] py-[16px]">
						<div className="flex items-center gap-[16px]">
							<Shimmer className="h-[32px] w-[32px] rounded-[8px] shrink-0" />
							<div className="flex flex-col gap-[6px] flex-1">
								<Shimmer className="h-[14px] w-[200px]" />
								<Shimmer className="h-[12px] w-[320px]" />
							</div>
							<Shimmer className="h-[20px] w-[50px] rounded-full" />
							<Shimmer className="h-[20px] w-[40px]" />
							<Shimmer className="h-[20px] w-[80px]" />
							<Shimmer className="h-[30px] w-[100px] rounded-[8px]" />
						</div>
					</div>
				))}
			</div>
		</div>
	);
}

/* ─── Tools tab skeleton ──────────────────────────────────────────── */
export function ToolsListSkeleton() {
	return (
		<div className="flex flex-col gap-[24px]">
			<HeaderCardSkeleton />
			{/* Filter bar ghost */}
			<div className="flex items-center gap-[10px]">
				<Shimmer className="h-[36px] w-[260px] rounded-[6px]" />
				<Shimmer className="h-[36px] w-[130px] rounded-[6px]" />
				<Shimmer className="h-[36px] w-[110px] rounded-[6px]" />
				<Shimmer className="h-[36px] w-[110px] rounded-[6px]" />
			</div>
			<div className="rounded-[8px] border border-[#E5E7EB] bg-white overflow-hidden">
				{/* Table header ghost */}
				<div className="flex items-center gap-[16px] px-[16px] py-[10px] bg-[#F9FAFB] border-b border-[#E5E7EB]">
					{['w-[200px]', 'w-[90px]', 'w-[220px]', 'w-[70px]', 'w-[60px]'].map((w, i) => (
						<Shimmer key={i} className={`h-[10px] ${w}`} />
					))}
				</div>
				{[1, 2, 3, 4, 5].map((i) => (
					<div key={i} className="flex items-center gap-[16px] px-[16px] py-[14px] border-b border-[#F3F4F6]">
						<Shimmer className="h-[12px] w-[12px] rounded shrink-0" />
						<Shimmer className="h-[13px] w-[200px]" />
						<Shimmer className="h-[13px] w-[90px]" />
						<Shimmer className="h-[13px] w-[220px]" />
						<Shimmer className="h-[20px] w-[70px] rounded-full" />
						<Shimmer className="h-[13px] w-[40px]" />
					</div>
				))}
			</div>
		</div>
	);
}

/* ─── Invocation Logs skeleton ────────────────────────────────────── */
export function InvocationLogsSkeleton() {
	return (
		<div className="flex flex-col gap-[24px]">
			{/* Stats row */}
			<div className="grid grid-cols-4 gap-[16px]">
				{[1, 2, 3, 4].map((i) => (
					<div key={i} className="rounded-[12px] border border-[#E5E7EB] bg-white p-[20px] flex flex-col gap-[10px]">
						<Shimmer className="h-[12px] w-[80px]" />
						<Shimmer className="h-[28px] w-[100px]" />
					</div>
				))}
			</div>
			{/* Filter bar */}
			<div className="flex items-center gap-[10px]">
				{[1, 2, 3, 4].map((i) => (
					<Shimmer key={i} className="h-[36px] w-[130px] rounded-[8px]" />
				))}
			</div>
			{/* Table */}
			<div className="rounded-[8px] border border-[#E5E7EB] bg-white overflow-hidden">
				<div className="flex items-center gap-[16px] px-[16px] py-[10px] bg-[#F9FAFB] border-b border-[#E5E7EB]">
					{['w-[120px]', 'w-[120px]', 'w-[160px]', 'w-[120px]', 'w-[100px]'].map((w, i) => (
						<Shimmer key={i} className={`h-[10px] ${w}`} />
					))}
				</div>
				{[1, 2, 3, 4, 5, 6].map((i) => (
					<div key={i} className="flex items-center gap-[16px] px-[16px] py-[14px] border-b border-[#F3F4F6]">
						<Shimmer className="h-[12px] w-[12px] rounded shrink-0" />
						<Shimmer className="h-[13px] w-[120px]" />
						<Shimmer className="h-[13px] w-[120px]" />
						<Shimmer className="h-[13px] w-[160px]" />
						<Shimmer className="h-[20px] w-[80px] rounded-full" />
						<Shimmer className="h-[13px] w-[70px]" />
					</div>
				))}
			</div>
		</div>
	);
}

/* ─── Error state ─────────────────────────────────────────────────── */
export function ErrorState({ message = 'Failed to load data.', onRetry }) {
	return (
		<div className="flex flex-col items-center justify-center rounded-[12px] border border-[#FEE2E2] bg-[#FFF5F5] px-[24px] py-[48px] text-center gap-[12px]">
			<div className="flex h-[44px] w-[44px] items-center justify-center rounded-full bg-[#FEE2E2]">
				<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
					<path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="#EF4444" strokeWidth="1.8" strokeLinecap="round"/>
				</svg>
			</div>
			<p className="font-lato text-[14px] text-[#6B7280]">{message}</p>
			{onRetry && (
				<button
					onClick={onRetry}
					className="rounded-[8px] border border-[#E5E7EB] px-[16px] py-[8px] font-lato text-[13px] text-[#374151] hover:bg-[#F9FAFB] transition-colors"
				>
					Try again
				</button>
			)}
		</div>
	);
}

/* inline shimmer keyframes injected once */
if (typeof document !== 'undefined') {
	const styleId = '__ai-shimmer-style';
	if (!document.getElementById(styleId)) {
		const style = document.createElement('style');
		style.id = styleId;
		style.textContent = `
			@keyframes shimmer {
				0%   { background-position: 200% 0; }
				100% { background-position: -200% 0; }
			}
		`;
		document.head.appendChild(style);
	}
}
