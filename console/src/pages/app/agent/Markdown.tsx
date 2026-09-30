import type { ReactNode } from 'react';

// Minimal markdown for analyst replies and specs, ported from the classic panel's Markdown.jsx.
// The analyst emits a small subset (bold, italic, inline code, headings, lists, fenced blocks).
// Everything is built as React elements, never innerHTML, so model output can't inject markup.

const INLINE = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*\n]+\*)/g;
const BULLET = /^(\s*)[-*]\s+(.*)$/;
const NUMBERED = /^(\s*)(\d+)[.)]\s+(.*)$/;
const HEADING = /^(#{1,4})\s+(.*)$/;

function inline(text: string, key: string): ReactNode {
	return text.split(INLINE).map((part, i) => {
		const k = `${key}-${i}`;
		if (!part) return null;
		if (part.length > 2 && part.startsWith('`') && part.endsWith('`')) {
			return (
				<code key={k} className="mono rounded-[4px] bg-subtle px-1 py-px text-[11.5px] text-t1">
					{part.slice(1, -1)}
				</code>
			);
		}
		if (part.length > 4 && part.startsWith('**') && part.endsWith('**')) {
			return (
				<b key={k} className="font-semibold text-t1">
					{part.slice(2, -2)}
				</b>
			);
		}
		if (part.length > 2 && part.startsWith('*') && part.endsWith('*'))
			return <em key={k}>{part.slice(1, -1)}</em>;
		return <span key={k}>{part}</span>;
	});
}

interface ListState {
	ordered: boolean;
	start: number;
	items: Array<{ indent: number; content: string }>;
}

export function Markdown({ text, className }: { text: string; className?: string }) {
	if (!text) return null;
	const blocks: ReactNode[] = [];
	let list: ListState | null = null;
	let fence: string[] | null = null;

	const flushList = () => {
		if (!list) return;
		const l = list;
		const Tag = l.ordered ? 'ol' : 'ul';
		blocks.push(
			<Tag
				key={`b${blocks.length}`}
				start={l.ordered ? l.start : undefined}
				className={`my-1.5 flex flex-col gap-[3px] pl-5 ${l.ordered ? 'list-decimal' : 'list-disc'}`}
			>
				{l.items.map((item, i) => (
					<li key={i} style={item.indent ? { marginLeft: item.indent * 12 } : undefined}>
						{inline(item.content, `l${blocks.length}-${i}`)}
					</li>
				))}
			</Tag>,
		);
		list = null;
	};
	const flushFence = () => {
		if (fence === null) return;
		blocks.push(
			<pre
				key={`b${blocks.length}`}
				className="mono my-2 overflow-x-auto rounded-md border border-border bg-bg p-2.5 text-[11.5px] leading-[1.55] text-t1"
			>
				{fence.join('\n')}
			</pre>,
		);
		fence = null;
	};

	String(text)
		.split('\n')
		.forEach((raw, idx) => {
			if (raw.trim().startsWith('```')) {
				if (fence === null) {
					flushList();
					fence = [];
				} else flushFence();
				return;
			}
			if (fence !== null) {
				fence.push(raw);
				return;
			}
			if (!raw.trim()) {
				flushList();
				return;
			}
			const heading = raw.match(HEADING);
			if (heading) {
				flushList();
				blocks.push(
					<div
						key={`b${blocks.length}`}
						className={`mt-3 font-semibold text-t1 first:mt-0 ${heading[1].length <= 2 ? 'text-[14px]' : 'text-[13px]'}`}
					>
						{inline(heading[2], `h${idx}`)}
					</div>,
				);
				return;
			}
			const numbered = raw.match(NUMBERED);
			if (numbered) {
				if (!list || !list.ordered) {
					flushList();
					// Keep the author's own numbering when a list is broken up by paragraphs.
					list = { ordered: true, items: [], start: parseInt(numbered[2], 10) || 1 };
				}
				list.items.push({ indent: Math.floor(numbered[1].length / 2), content: numbered[3] });
				return;
			}
			const bullet = raw.match(BULLET);
			if (bullet) {
				if (!list || list.ordered) {
					flushList();
					list = { ordered: false, items: [], start: 1 };
				}
				list.items.push({ indent: Math.floor(bullet[1].length / 2), content: bullet[2] });
				return;
			}
			// A plain indented line under a list item continues it.
			if (list && raw.startsWith('  ') && list.items.length) {
				list.items[list.items.length - 1].content += ` ${raw.trim()}`;
				return;
			}
			flushList();
			blocks.push(
				<p key={`b${blocks.length}`} className="my-1.5 first:mt-0 last:mb-0">
					{inline(raw, `p${idx}`)}
				</p>,
			);
		});
	flushList();
	flushFence();
	return <div className={className}>{blocks}</div>;
}
