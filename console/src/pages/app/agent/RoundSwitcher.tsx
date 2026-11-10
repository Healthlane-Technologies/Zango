import { cx, Menu, type MenuItem } from '@/ui';
import { REQUIREMENT_STATUS, roundLabel, stageOf, stamp, type Round } from './rounds';

const STAGE_TEXT = { approved: 'Approved', build: 'Building', built: 'Built' } as const;

/** Where a round stands, in a word: its review state until approved, then its build state. */
function stateOf(r: Round): { text: string; tone: 'amber' | 'green' | 'accent' | 'gray' | 'red' } {
	const detail = r.detail;
	const { stage, failed } = stageOf(detail);
	if (failed) return { text: 'Build failed', tone: 'red' };
	if (stage === 'requirements') {
		const [tone, text] = REQUIREMENT_STATUS[detail?.status ?? r.summary.status];
		return { text, tone: tone as 'amber' | 'green' | 'accent' | 'gray' };
	}
	return { text: STAGE_TEXT[stage], tone: stage === 'built' ? 'green' : 'accent' };
}

/** Pick which round (the initial build or a change) the panel shows: newest first, each with what it does. */
export function RoundSwitcher({
	rounds,
	viewed,
	onPick,
}: {
	rounds: Round[];
	viewed: Round;
	onPick: (uuid: string) => void;
}) {
	const items: MenuItem[] = [...rounds].reverse().map((r) => {
		const state = stateOf(r);
		const current = r.summary.uuid === viewed.summary.uuid;
		return {
			onSelect: () => onPick(r.summary.uuid),
			label: (
				<span className={cx('rs-item', current && 'on')}>
					<span className="rs-top">
						<b>{roundLabel(r.index)}</b>
						<span className={cx('rs-state', state.tone)}>
							<i />
							{state.text}
						</span>
						{r.index === rounds.length - 1 && <span className="rs-latest">Latest</span>}
					</span>
					<span className="rs-title">{r.summary.title || 'Untitled'}</span>
					<span className="rs-when">{stamp(r.summary.created_at)}</span>
				</span>
			),
		};
	});
	const state = stateOf(viewed);
	return (
		<Menu
			align="end"
			items={items}
			trigger={
				<button type="button" className="rs-btn" aria-label="Switch between your changes">
					<span className={cx('rs-dot', state.tone)} />
					<span className="rs-name">{roundLabel(viewed.index)}</span>
					{viewed.index > 0 && viewed.summary.title && (
						<span className="rs-label" title={viewed.summary.title}>
							{viewed.summary.title}
						</span>
					)}
					<span className="rs-caret" />
				</button>
			}
		/>
	);
}
