/**
 * Answer the analyst's questions by clicking.
 *
 * The user here is a business person describing their own work, often on a
 * phone between meetings. Asking them to write prose about tender stages is
 * the single thing most likely to end the conversation — so the analyst sends
 * its questions as options with its own recommendation pre-ticked, and this
 * renders them. Agreeing costs one click; the chat box stays available
 * underneath for anything the options do not cover.
 */
import { useEffect, useMemo, useState } from 'react';

/** Initial answers: whatever the analyst recommended. */
function seed(questions) {
	const next = {};
	(questions || []).forEach((q) => {
		next[q.id] = { selected: [...(q.selected || [])], other: '' };
	});
	return next;
}

/**
 * The message the agent receives. Written as the user would have written it,
 * because the agent reads it as an ordinary reply in a resumed session — it
 * never sees this component or its JSON.
 */
export function composeAnswer(questions, answers) {
	const lines = [];
	(questions || []).forEach((q) => {
		const answer = answers[q.id] || { selected: [], other: '' };
		const parts = [...answer.selected];
		if (answer.other.trim()) parts.push(answer.other.trim());
		lines.push(`${q.question}\n→ ${parts.length ? parts.join(', ') : 'not sure'}`);
	});
	return lines.join('\n\n');
}

export function isAnswered(questions, answers) {
	return (questions || []).every((q) => {
		const answer = answers[q.id];
		return Boolean(answer && (answer.selected.length || answer.other.trim()));
	});
}

function Chip({ selected, disabled, children, onClick }) {
	return (
		<button
			type="button"
			disabled={disabled}
			onClick={onClick}
			className={`rounded-full border px-[11px] py-[5px] text-left font-lato text-[12.5px] leading-[18px] transition-colors ${
				selected
					? 'border-[#5048ED] bg-[#EEF2FF] font-semibold text-[#3730A3]'
					: 'border-[#DDE2E5] bg-white text-[#374151] hover:border-[#9CA3AF]'
			} ${disabled ? 'cursor-default opacity-70' : ''}`}
		>
			{children}
		</button>
	);
}

/**
 * Only ever rendered for the turn awaiting an answer. Earlier turns need
 * nothing: `composeAnswer` repeats each question above its answer, so the
 * user's own reply is already a full record of what was asked.
 */
export default function QuestionAnswers({ questions, disabled = false, onChange }) {
	const [answers, setAnswers] = useState(() => seed(questions));

	// Identity of the question set, so answers reset when a new turn arrives
	// but survive every unrelated re-render (polling causes plenty).
	const key = useMemo(
		() => (questions || []).map((q) => q.id).join('|'),
		[questions]
	);

	useEffect(() => {
		const fresh = seed(questions);
		setAnswers(fresh);
		if (onChange) onChange(fresh);
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key]);

	const update = (next) => {
		setAnswers(next);
		if (onChange) onChange(next);
	};

	const toggle = (question, option) => {
		const current = answers[question.id] || { selected: [], other: '' };
		let selected;
		if (question.type === 'multi') {
			selected = current.selected.includes(option)
				? current.selected.filter((o) => o !== option)
				: [...current.selected, option];
		} else {
			// Single choice: tapping the chosen option again clears it, so a
			// pre-ticked default is never a trap.
			selected = current.selected.includes(option) ? [] : [option];
		}
		update({ ...answers, [question.id]: { ...current, selected } });
	};

	const setOther = (question, value) => {
		const current = answers[question.id] || { selected: [], other: '' };
		update({ ...answers, [question.id]: { ...current, other: value } });
	};

	if (!questions?.length) return null;

	return (
		<div className="flex flex-col gap-[12px]">
			{questions.map((q, index) => {
				const answer = answers[q.id] || { selected: [], other: '' };
				return (
					<div key={q.id}>
						<p className="font-lato text-[13px] font-semibold leading-[19px] text-[#111827]">
							{index + 1}. {q.question}
							{q.type === 'multi' ? (
								<span className="ml-[6px] font-normal text-[#9CA3AF]">
									pick any
								</span>
							) : null}
						</p>
						<div className="mt-[6px] flex flex-wrap gap-[6px]">
							{q.options.map((option) => (
								<Chip
									key={option}
									selected={answer.selected.includes(option)}
									disabled={disabled}
									onClick={() => toggle(q, option)}
								>
									{option}
								</Chip>
							))}
						</div>
						{q.allow_other ? (
							<input
								type="text"
								value={answer.other}
								disabled={disabled}
								onChange={(e) => setOther(q, e.target.value)}
								placeholder="Something else…"
								className="mt-[6px] w-full rounded-[6px] border border-[#E5E7EB] px-[9px] py-[5px] font-lato text-[12.5px] focus:border-primary focus:outline-none disabled:bg-[#F8FAFC]"
							/>
						) : null}
					</div>
				);
			})}
		</div>
	);
}
