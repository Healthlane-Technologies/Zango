import { useEffect, useMemo, useState } from 'react';
import { cx } from '@/ui';

/** What the agent is doing, in the words a person would use, by section id. */
const PHRASE: Record<string, string> = {
	app: 'Naming your app',
	program: 'Naming your program',
	roles: 'Setting up roles',
	pages: 'Laying out pages',
	menu: 'Building the menu',
	modules: 'Modelling your records',
	entities: 'Modelling your records',
	choice_sets: 'Collecting choice lists',
	masters: 'Collecting reference lists',
	workflows: 'Adding workflows',
	patient_lifecycle: 'Adding workflows',
	detail_views: 'Designing detail pages',
	detail: 'Designing detail pages',
	documents: 'Setting up documents',
	reports: 'Adding reports',
};
const ROTATE_MS = 2400;

/**
 * Covers the preview while the agent writes the first version of the app: a small app window
 * assembling itself, and a line saying what is happening. Fades out once a real revision lands.
 */
export function GeneratingPreview({
	shown,
	awaiting = false,
	documents,
	sections,
	changedSections,
}: {
	shown: boolean;
	/** The agent is waiting on the user's answers before it writes the first version. */
	awaiting?: boolean;
	documents: number;
	sections: Array<{ id: string; title: string }>;
	/** Section ids the agent has written so far this turn (may be empty). */
	changedSections: string[];
}) {
	const lines = useMemo(() => {
		const out: string[] = [];
		if (documents) out.push(`Reading ${documents} document${documents > 1 ? 's' : ''}`);
		else out.push('Reading your brief');
		const ids = changedSections.length ? changedSections : sections.map((s) => s.id);
		for (const id of ids) {
			const title = sections.find((s) => s.id === id)?.title;
			const phrase = PHRASE[id] ?? (title ? `Working on ${title.toLowerCase()}` : '');
			if (phrase && !out.includes(phrase)) out.push(phrase);
		}
		if (out.length < 3) out.push('Laying out pages', 'Adding workflows');
		out.push('Filling in sample data');
		return out;
	}, [documents, sections, changedSections]);

	const [i, setI] = useState(0);
	useEffect(() => {
		if (!shown) return;
		const t = window.setInterval(() => setI((n) => n + 1), ROTATE_MS);
		return () => window.clearInterval(t);
	}, [shown]);
	// Stay mounted for the fade-out, then go.
	const [present, setPresent] = useState(shown);
	useEffect(() => {
		if (shown) {
			setPresent(true);
			return;
		}
		const t = window.setTimeout(() => setPresent(false), 450);
		return () => window.clearTimeout(t);
	}, [shown]);
	if (!present) return null;
	const line = lines[i % lines.length];

	return (
		<div className={cx('gp', !shown && 'out', awaiting && 'wait')} role="status" aria-live="polite">
			<div className="gp-in">
				<svg className="gp-art" viewBox="0 0 320 200" aria-hidden="true">
					<defs>
						<linearGradient id="gp-sheen" x1="0" x2="1">
							<stop offset="0" stopColor="#fff" stopOpacity="0" />
							<stop offset="0.5" stopColor="#fff" stopOpacity="0.7" />
							<stop offset="1" stopColor="#fff" stopOpacity="0" />
						</linearGradient>
						<clipPath id="gp-clip">
							<rect x="20" y="16" width="280" height="168" rx="12" />
						</clipPath>
					</defs>
					{/* window */}
					<rect className="gp-win" x="20" y="16" width="280" height="168" rx="12" />
					<g clipPath="url(#gp-clip)">
						<rect className="gp-bar" x="20" y="16" width="280" height="22" />
						<circle className="gp-dot" cx="34" cy="27" r="3" />
						<circle className="gp-dot" cx="44" cy="27" r="3" />
						<circle className="gp-dot" cx="54" cy="27" r="3" />
						{/* sidebar */}
						<rect className="gp-side" x="20" y="38" width="66" height="146" />
						<g className="gp-s gp-s1">
							<rect className="gp-logo" x="30" y="48" width="14" height="14" rx="4" />
							<rect className="gp-ln" x="49" y="52" width="28" height="6" rx="3" />
						</g>
						<rect className="gp-s gp-s2 gp-nav on" x="28" y="72" width="50" height="10" rx="5" />
						<rect className="gp-s gp-s3 gp-nav" x="28" y="88" width="42" height="8" rx="4" />
						<rect className="gp-s gp-s4 gp-nav" x="28" y="102" width="46" height="8" rx="4" />
						<rect className="gp-s gp-s5 gp-nav" x="28" y="116" width="38" height="8" rx="4" />
						{/* page */}
						<rect className="gp-s gp-s2 gp-h1" x="98" y="50" width="78" height="10" rx="5" />
						<rect className="gp-s gp-s3 gp-btn" x="250" y="47" width="38" height="15" rx="5" />
						<g className="gp-s gp-s4">
							<rect className="gp-card" x="98" y="72" width="58" height="34" rx="7" />
							<rect className="gp-ln" x="106" y="80" width="26" height="5" rx="2.5" />
							<rect className="gp-num" x="106" y="91" width="18" height="8" rx="3" />
						</g>
						<g className="gp-s gp-s5">
							<rect className="gp-card" x="164" y="72" width="58" height="34" rx="7" />
							<rect className="gp-ln" x="172" y="80" width="30" height="5" rx="2.5" />
							<rect className="gp-num g" x="172" y="91" width="22" height="8" rx="3" />
						</g>
						<g className="gp-s gp-s6">
							<rect className="gp-card" x="230" y="72" width="58" height="34" rx="7" />
							<rect className="gp-ln" x="238" y="80" width="22" height="5" rx="2.5" />
							<rect className="gp-num a" x="238" y="91" width="16" height="8" rx="3" />
						</g>
						<g className="gp-s gp-s6">
							<rect className="gp-card" x="98" y="116" width="190" height="58" rx="7" />
						</g>
						{[0, 1, 2].map((r) => (
							<g key={r} className={`gp-s gp-s${7 + r}`}>
								<rect className="gp-ln" x="108" y={128 + r * 15} width="44" height="5" rx="2.5" />
								<rect className="gp-ln" x="162" y={128 + r * 15} width="58" height="5" rx="2.5" />
								<rect
									className={cx('gp-chip', r === 1 && 'g')}
									x="246"
									y={126.5 + r * 15}
									width="30"
									height="8"
									rx="4"
								/>
							</g>
						))}
						<rect
							className="gp-sheen"
							x="-120"
							y="16"
							width="120"
							height="168"
							fill="url(#gp-sheen)"
						/>
					</g>
					{/* the agent, drawing */}
					<g className="gp-pen">
						<path
							className="gp-spark"
							d="M0 -9 C1.2 -2.5 2.5 -1.2 9 0 C2.5 1.2 1.2 2.5 0 9 C-1.2 2.5 -2.5 1.2 -9 0 C-2.5 -1.2 -1.2 -2.5 0 -9Z"
						/>
					</g>
				</svg>
				{awaiting ? (
					<>
						<b className="gp-title">Your preview starts with your answers</b>
						<span className="gp-line">The agent has a few questions in the chat</span>
						<span className="gp-note">
							Answer them and the first version of your app appears here.
						</span>
					</>
				) : (
					<>
						<b className="gp-title">Generating your app preview</b>
						<span key={line} className="gp-line">
							{line}…
						</span>
						<span className="gp-note">
							The preview appears here as soon as the first version is ready.
						</span>
					</>
				)}
			</div>
		</div>
	);
}

/** The preview already exists and the agent is changing it: a slim bar, nothing in the way. */
export function UpdatingPreview() {
	return (
		<div className="gp-upd" role="status" aria-live="polite">
			<div className="gp-upd-bar" />
			<span className="gp-upd-chip">
				<span className="spin" />
				Updating preview…
			</span>
		</div>
	);
}
