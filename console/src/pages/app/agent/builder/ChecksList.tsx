import type { SpecIssue } from '@/api/agentMode';
import { cx, EmptyState, Icon } from '@/ui';
import type { BuilderSection } from './sections';

export interface CheckRow {
	issue: SpecIssue;
	section?: BuilderSection;
	where: string;
	line?: number;
}

/** "Section › path", without repeating a segment the section title already says. */
function crumbs(r: CheckRow): string {
	const parts = [r.section?.title, ...r.where.split(' › ')].filter((p): p is string => !!p);
	return parts.filter((p, i) => i === 0 || p !== parts[i - 1]).join(' › ');
}

/** Issues grouped by level (errors first), then by section in builder order. */
export function ChecksList({
	rows,
	onJump,
}: {
	rows: CheckRow[];
	onJump: (row: CheckRow) => void;
}) {
	if (!rows.length) {
		return (
			<div className="card">
				<EmptyState title="No problems found">Every check on this spec passes.</EmptyState>
			</div>
		);
	}
	const levels: Array<['error' | 'warning', string]> = [
		['error', 'Must fix before approving'],
		['warning', 'Worth a look'],
	];
	return (
		<div className="grid gap-4">
			{levels.map(([level, heading]) => {
				const group = rows.filter((r) => r.issue.level === level);
				if (!group.length) return null;
				return (
					<div key={level}>
						<div className="bv-chk-h">
							{heading}
							<span className="ct">{group.length}</span>
						</div>
						<div className="card">
							{group.map((r, i) => (
								<button
									key={i}
									type="button"
									className={cx('bv-chk', level === 'error' ? 'err' : 'wrn')}
									onClick={() => onJump(r)}
								>
									<Icon name="alert" size={14} />
									<span className="min-w-0 flex-1">
										<span className="block text-t1">{r.issue.message}</span>
										<span className="block truncate text-[12px] text-t3">
											{crumbs(r) || 'Whole spec'}
											{r.line ? ` · line ${r.line}` : ''}
										</span>
									</span>
									<Icon name="ext" size={13} className="text-t4" />
								</button>
							))}
						</div>
					</div>
				);
			})}
		</div>
	);
}
