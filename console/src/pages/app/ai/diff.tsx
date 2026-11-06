import { cx } from '@/ui';

type Op = { kind: 'same' | 'add' | 'del'; text: string };

/** Longest-common-subsequence diff over tokens. */
function lcsDiff(a: string[], b: string[]): Op[] {
	const n = a.length;
	const m = b.length;
	const dp: Uint32Array[] = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
	for (let i = n - 1; i >= 0; i--)
		for (let j = m - 1; j >= 0; j--)
			dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
	const out: Op[] = [];
	const push = (kind: Op['kind'], text: string) => {
		const last = out[out.length - 1];
		if (last?.kind === kind) last.text += text;
		else out.push({ kind, text });
	};
	let i = 0;
	let j = 0;
	while (i < n && j < m) {
		if (a[i] === b[j]) {
			push('same', a[i]);
			i++;
			j++;
		} else if (dp[i + 1][j] >= dp[i][j + 1]) push('del', a[i++]);
		else push('add', b[j++]);
	}
	while (i < n) push('del', a[i++]);
	while (j < m) push('add', b[j++]);
	return out;
}

/** Word-level for normal prompts; line-level when either side is long, to keep the table small. */
export function diffText(before: string, after: string): Op[] {
	const long = before.length > 3000 || after.length > 3000;
	const split = (s: string) => (long ? s.split(/(?<=\n)/) : s.split(/(\s+)/).filter(Boolean));
	return lcsDiff(split(before), split(after));
}

export function DiffView({
	before,
	after,
	maxHeight = 320,
}: {
	before: string;
	after: string;
	maxHeight?: number;
}) {
	const ops = diffText(before, after);
	const count = (k: Op['kind']) => ops.filter((o) => o.kind === k && o.text.trim()).length;
	const added = count('add');
	const removed = count('del');
	return (
		<div>
			<div className="mb-1.5 text-[12px] text-t3">
				{added || removed ? (
					<>
						<span className="text-green-t">+{added}</span> <span className="text-red-t">−{removed}</span>{' '}
						changed spans
					</>
				) : (
					'No changes'
				)}
			</div>
			<pre
				className="mono overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-bg p-3 text-[12px] leading-[1.6] text-t1"
				style={{ maxHeight }}
			>
				{ops.map((o, i) => (
					<span
						key={i}
						className={cx(
							o.kind === 'add' && 'bg-green-soft text-green-t',
							o.kind === 'del' && 'bg-red-soft text-red-t line-through',
						)}
					>
						{o.text}
					</span>
				))}
			</pre>
		</div>
	);
}
