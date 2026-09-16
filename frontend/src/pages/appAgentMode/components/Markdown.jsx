/**
 * Minimal markdown renderer for agent replies.
 *
 * Deliberately not a markdown library: the analyst emits a small, predictable
 * subset (bold, inline code, headings, bullet and numbered lists, the odd
 * fenced block), and pulling in react-markdown + remark + a sanitiser is a
 * lot of dependency for that.
 *
 * Everything is built as React elements — no dangerouslySetInnerHTML — so
 * model output cannot inject markup no matter what it contains.
 */

// Inline: `code`, **bold**, *italic*. Ordered so code wins and its contents
// are never re-parsed as emphasis.
const INLINE = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*\n]+\*)/g;

function renderInline(text, keyPrefix) {
	if (!text) return null;
	return text.split(INLINE).map((part, i) => {
		const key = `${keyPrefix}-i${i}`;
		if (!part) return null;
		if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
			return (
				<code
					key={key}
					className="rounded-[3px] bg-[#EDEFF5] px-[4px] py-[1px] font-mono text-[11.5px] text-[#0B0D14]"
				>
					{part.slice(1, -1)}
				</code>
			);
		}
		if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
			return <strong key={key} className="font-semibold">{part.slice(2, -2)}</strong>;
		}
		if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
			return <em key={key}>{part.slice(1, -1)}</em>;
		}
		return <span key={key}>{part}</span>;
	});
}

const BULLET = /^(\s*)[-*]\s+(.*)$/;
const NUMBERED = /^(\s*)(\d+)[.)]\s+(.*)$/;
const HEADING = /^(#{1,4})\s+(.*)$/;

export default function Markdown({ text, className = '' }) {
	if (!text) return null;

	const lines = String(text).split('\n');
	const blocks = [];
	let list = null;          // { ordered, items: [{ indent, content }] }
	let fence = null;         // string[] while inside ```

	const flushList = () => {
		if (!list) return;
		const Tag = list.ordered ? 'ol' : 'ul';
		blocks.push(
			<Tag
				key={`b${blocks.length}`}
				start={list.ordered ? list.start : undefined}
				className={`my-[6px] flex flex-col gap-[3px] ${
					list.ordered ? 'list-decimal' : 'list-disc'
				} pl-[20px]`}
			>
				{list.items.map((item, i) => (
					<li key={i} style={item.indent ? { marginLeft: item.indent * 12 } : undefined}>
						{renderInline(item.content, `l${blocks.length}-${i}`)}
					</li>
				))}
			</Tag>
		);
		list = null;
	};

	const flushFence = () => {
		if (fence === null) return;
		blocks.push(
			<pre
				key={`b${blocks.length}`}
				className="my-[8px] overflow-x-auto rounded-[6px] bg-[#0F172A] p-[10px] font-mono text-[11px] leading-[16px] text-[#E2E8F0]"
			>
				{fence.join('\n')}
			</pre>
		);
		fence = null;
	};

	lines.forEach((raw, idx) => {
		if (raw.trim().startsWith('```')) {
			if (fence === null) {
				flushList();
				fence = [];
			} else {
				flushFence();
			}
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
			const level = heading[1].length;
			blocks.push(
				<div
					key={`b${blocks.length}`}
					className={`mt-[10px] font-semibold text-[#0B0D14] ${
						level <= 2 ? 'text-[14px]' : 'text-[13px]'
					}`}
				>
					{renderInline(heading[2], `h${idx}`)}
				</div>
			);
			return;
		}

		const numbered = raw.match(NUMBERED);
		if (numbered) {
			const value = parseInt(numbered[2], 10);
			if (!list || !list.ordered) {
				flushList();
				// Resume from the author's own number, so a list broken up by
				// paragraphs or sub-bullets keeps counting instead of
				// restarting at 1.
				list = { ordered: true, items: [], start: value || 1 };
			}
			list.items.push({
				indent: Math.floor(numbered[1].length / 2),
				content: numbered[3],
			});
			return;
		}

		const bullet = raw.match(BULLET);
		if (bullet) {
			if (!list || list.ordered) {
				flushList();
				list = { ordered: false, items: [] };
			}
			list.items.push({
				indent: Math.floor(bullet[1].length / 2),
				content: bullet[2],
			});
			return;
		}

		// A plain line directly under a list item is its continuation.
		if (list && raw.startsWith('  ')) {
			const last = list.items[list.items.length - 1];
			if (last) {
				last.content += ` ${raw.trim()}`;
				return;
			}
		}

		flushList();
		blocks.push(
			<p key={`b${blocks.length}`} className="my-[6px] first:mt-0 last:mb-0">
				{renderInline(raw, `p${idx}`)}
			</p>
		);
	});

	flushList();
	flushFence();

	return <div className={className}>{blocks}</div>;
}
