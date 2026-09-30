import type { AnalystQuestion } from '@/api/agentMode';

export interface Answer {
	selected: string[];
	other: string;
}
export type Answers = Record<string, Answer>;

/** Initial answers: whatever the analyst recommended. */
export function seedAnswers(questions: AnalystQuestion[]): Answers {
	return Object.fromEntries(
		questions.map((q) => [q.id, { selected: [...(q.selected ?? [])], other: '' }]),
	);
}

export function isAnswered(questions: AnalystQuestion[], answers: Answers): boolean {
	return questions.every((q) => {
		const a = answers[q.id];
		return !!a && (a.selected.length > 0 || a.other.trim() !== '');
	});
}

/**
 * The message the analyst receives, written as the user would have written it: the agent
 * reads it as an ordinary reply in a resumed session and never sees this UI. Same format as
 * the classic panel's composeAnswer.
 */
export function composeAnswer(questions: AnalystQuestion[], answers: Answers): string {
	return questions
		.map((q) => {
			const a = answers[q.id] ?? { selected: [], other: '' };
			const parts = [...a.selected];
			if (a.other.trim()) parts.push(a.other.trim());
			return `${q.question}\n→ ${parts.length ? parts.join(', ') : 'not sure'}`;
		})
		.join('\n\n');
}

/** Toggle an option. Single choice: tapping the chosen option again clears it. */
export function toggleOption(q: AnalystQuestion, a: Answer, option: string): Answer {
	const on = a.selected.includes(option);
	if (q.type === 'multi')
		return {
			...a,
			selected: on ? a.selected.filter((o) => o !== option) : [...a.selected, option],
		};
	return { ...a, selected: on ? [] : [option] };
}
