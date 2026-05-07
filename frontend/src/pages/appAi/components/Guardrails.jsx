import { useEffect } from 'react';

const FEATURES = [
	{
		icon: (
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
				<path d="M10 2L4 5.5V10C4 13.52 6.56 16.76 10 17.6C13.44 16.76 16 13.52 16 10V5.5L10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
				<path d="M7.5 10L9.5 12L12.5 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
			</svg>
		),
		title: 'Policy Enforcement',
		description: 'Define rules on what agents can and cannot do — block categories, cap costs, restrict domains.',
		color: 'text-[#346BD4]',
		bg: 'bg-[#EFF6FF]',
		border: 'border-[#BFDBFE]',
		iconBg: 'bg-[#DBEAFE]',
	},
	{
		icon: (
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
				<rect x="3" y="3" width="14" height="14" rx="3" stroke="currentColor" strokeWidth="1.5"/>
				<path d="M7 10H13M7 7H13M7 13H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
			</svg>
		),
		title: 'PII Detection & Masking',
		description: 'Automatically detect and redact personally identifiable information before it reaches the LLM.',
		color: 'text-[#7C3AED]',
		bg: 'bg-[#F5F3FF]',
		border: 'border-[#DDD6FE]',
		iconBg: 'bg-[#EDE9FE]',
	},
	{
		icon: (
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
				<path d="M10 3C6.134 3 3 6.134 3 10C3 13.866 6.134 17 10 17C13.866 17 17 13.866 17 10C17 6.134 13.866 3 10 3Z" stroke="currentColor" strokeWidth="1.5"/>
				<path d="M10 7V10L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
			</svg>
		),
		title: 'Prompt Injection Protection',
		description: 'Detect and neutralise adversarial inputs designed to hijack agent behaviour.',
		color: 'text-[#D97706]',
		bg: 'bg-[#FFFBEB]',
		border: 'border-[#FDE68A]',
		iconBg: 'bg-[#FEF3C7]',
	},
	{
		icon: (
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
				<path d="M4 4H16V13H11L8 16V13H4V4Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
				<path d="M7 8H13M7 11H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
			</svg>
		),
		title: 'Output Moderation',
		description: 'Run every LLM response through content classifiers before it reaches users.',
		color: 'text-[#10B981]',
		bg: 'bg-[#ECFDF5]',
		border: 'border-[#A7F3D0]',
		iconBg: 'bg-[#D1FAE5]',
	},
	{
		icon: (
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
				<path d="M3 5C3 4.448 3.448 4 4 4H16C16.552 4 17 4.448 17 5V9C17 12.866 13.866 16 10 16C6.134 16 3 12.866 3 9V5Z" stroke="currentColor" strokeWidth="1.5"/>
				<path d="M7 9L9 11L13 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
			</svg>
		),
		title: 'Compliance & Audit Controls',
		description: 'Enforce regulatory requirements with per-tenant policies and full audit trails.',
		color: 'text-[#EF4444]',
		bg: 'bg-[#FFF5F5]',
		border: 'border-[#FECACA]',
		iconBg: 'bg-[#FEE2E2]',
	},
	{
		icon: (
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
				<path d="M10 2L11.8 7.2H17.2L12.7 10.4L14.5 15.6L10 12.4L5.5 15.6L7.3 10.4L2.8 7.2H8.2L10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
			</svg>
		),
		title: 'Safety Scoring',
		description: 'Assign risk scores to every invocation and block requests that exceed safety thresholds.',
		color: 'text-[#0284C7]',
		bg: 'bg-[#F0F9FF]',
		border: 'border-[#BAE6FD]',
		iconBg: 'bg-[#E0F2FE]',
	},
];

export default function Guardrails({ onReady }) {
	useEffect(() => {
		if (onReady) onReady();
	}, []);

	return (
		<div className="flex flex-col items-center gap-[36px] py-[56px] max-w-[820px] mx-auto">

			{/* Hero */}
			<div className="relative w-full overflow-hidden rounded-[20px] border border-[#E5E7EB] bg-white px-[48px] py-[48px] flex flex-col items-center text-center gap-[20px]">
				{/* Decorative gradients */}
				<div className="pointer-events-none absolute -top-[100px] -right-[100px] h-[320px] w-[320px] rounded-full opacity-[0.07]"
					style={{ background: 'radial-gradient(circle, #5048ED 0%, transparent 70%)' }} />
				<div className="pointer-events-none absolute -bottom-[60px] -left-[60px] h-[240px] w-[240px] rounded-full opacity-[0.05]"
					style={{ background: 'radial-gradient(circle, #346BD4 0%, transparent 70%)' }} />

				{/* Icon with pulse ring */}
				<div className="relative">
					<div className="flex h-[64px] w-[64px] items-center justify-center rounded-[16px] bg-gradient-to-br from-[#5048ED] to-[#346BD4] shadow-lg">
						<svg width="32" height="32" viewBox="0 0 28 28" fill="none">
							<path d="M14 3L5 7.5V13C5 18.08 8.84 22.84 14 24C19.16 22.84 23 18.08 23 13V7.5L14 3Z" fill="white" fillOpacity="0.2" stroke="white" strokeWidth="1.6" strokeLinejoin="round"/>
							<path d="M10 14L12.5 16.5L18 11" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
						</svg>
					</div>
					<span className="absolute inset-0 rounded-[16px] ring-[3px] ring-[#5048ED] ring-opacity-25 animate-ping" style={{ animationDuration: '2.5s' }} />
				</div>

				{/* Coming soon badge */}
				<span className="inline-flex items-center gap-[6px] rounded-full border border-[#DDD6FE] bg-[#F5F3FF] px-[14px] py-[5px]">
					<span className="h-[6px] w-[6px] rounded-full bg-[#5048ED] animate-pulse" />
					<span className="font-lato text-[12px] font-semibold text-[#5048ED] tracking-[0.3px]">Coming Soon</span>
				</span>

				<div>
					<h2 className="font-source-sans-pro text-[28px] font-bold text-[#111827] leading-[36px]">Guardrails for AI Agents</h2>
					<p className="mt-[10px] font-lato text-[15px] leading-[24px] text-[#6B7280] max-w-[520px]">
						Enterprise-grade safety, compliance, and policy controls that sit between your agents and the world — ensuring every LLM interaction is secure and trustworthy.
					</p>
				</div>
			</div>

			{/* Feature grid */}
			<div className="w-full">
				<p className="mb-[16px] font-lato text-[13px] font-semibold text-[#9CA3AF] uppercase tracking-[0.6px]">What&apos;s coming</p>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[14px]">
					{FEATURES.map((f) => (
						<div
							key={f.title}
							className={`rounded-[14px] border ${f.border} ${f.bg} p-[20px] flex flex-col gap-[12px]`}
						>
							<div className={`flex h-[40px] w-[40px] items-center justify-center rounded-[10px] ${f.iconBg} ${f.color}`}>
								{f.icon}
							</div>
							<div>
								<h4 className={`font-source-sans-pro text-[14px] font-semibold ${f.color}`}>{f.title}</h4>
								<p className="mt-[4px] font-lato text-[12px] leading-[18px] text-[#6B7280]">{f.description}</p>
							</div>
						</div>
					))}
				</div>
			</div>
		</div>
	);
}
