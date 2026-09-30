// CodeMirror 6, read-only for now (F3 makes it editable). Imported only via YamlView's
// React.lazy, so CodeMirror lands in its own chunk.

import { useEffect, useRef } from 'react';
import { Compartment, EditorState, RangeSetBuilder } from '@codemirror/state';
import { Decoration, EditorView, lineNumbers, type DecorationSet } from '@codemirror/view';
import { defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { yaml } from '@codemirror/lang-yaml';

export interface LineMarks {
	changed: number[];
	errors: number[];
	warnings: number[];
}

export interface YamlEditorProps {
	text: string;
	marks: LineMarks;
	/** Scroll to and select this 1-based line; `nonce` re-triggers the same line. */
	jump?: { line: number; nonce: number } | null;
}

const theme = EditorView.theme({
	'&': { fontSize: '12px', height: '100%', background: 'var(--panel)' },
	'.cm-scroller': { fontFamily: 'var(--mono)', lineHeight: '1.6' },
	'.cm-gutters': { background: 'var(--bg)', border: 'none', color: 'var(--t4)' },
	'.cm-line.cm-chg': { background: 'var(--accent-soft)' },
	'.cm-line.cm-err': { background: 'var(--red-soft)', boxShadow: 'inset 3px 0 0 var(--red)' },
	'.cm-line.cm-wrn': { background: 'var(--amber-soft)', boxShadow: 'inset 3px 0 0 var(--amber)' },
	'.cm-line.cm-jump': { outline: '1px solid var(--accent)' },
	'&.cm-focused': { outline: 'none' },
});

function decorations(state: EditorState, marks: LineMarks, jumpLine?: number): DecorationSet {
	const byLine = new Map<number, string[]>();
	const add = (line: number, cls: string) => {
		if (line < 1 || line > state.doc.lines) return;
		byLine.set(line, [...(byLine.get(line) ?? []), cls]);
	};
	marks.changed.forEach((l) => add(l, 'cm-chg'));
	marks.warnings.forEach((l) => add(l, 'cm-wrn'));
	marks.errors.forEach((l) => add(l, 'cm-err'));
	if (jumpLine) add(jumpLine, 'cm-jump');
	const builder = new RangeSetBuilder<Decoration>();
	[...byLine.keys()]
		.sort((a, b) => a - b)
		.forEach((l) => {
			const line = state.doc.line(l);
			builder.add(line.from, line.from, Decoration.line({ class: byLine.get(l)!.join(' ') }));
		});
	return builder.finish();
}

export default function YamlEditor({ text, marks, jump }: YamlEditorProps) {
	const host = useRef<HTMLDivElement>(null);
	const view = useRef<EditorView | null>(null);
	const decoSlot = useRef(new Compartment());

	useEffect(() => {
		if (!host.current) return;
		const state = EditorState.create({
			doc: text,
			extensions: [
				lineNumbers(),
				yaml(),
				syntaxHighlighting(defaultHighlightStyle),
				EditorState.readOnly.of(true),
				EditorView.editable.of(false),
				theme,
				decoSlot.current.of(EditorView.decorations.of(Decoration.none)),
			],
		});
		view.current = new EditorView({ state, parent: host.current });
		return () => {
			view.current?.destroy();
			view.current = null;
		};
		// The editor is created once; text and marks are pushed in below.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	useEffect(() => {
		const v = view.current;
		if (!v) return;
		if (v.state.doc.toString() !== text)
			v.dispatch({ changes: { from: 0, to: v.state.doc.length, insert: text } });
		v.dispatch({
			effects: decoSlot.current.reconfigure(
				EditorView.decorations.of(decorations(v.state, marks, jump?.line)),
			),
		});
	}, [text, marks, jump]);

	useEffect(() => {
		const v = view.current;
		if (!v || !jump || jump.line < 1 || jump.line > v.state.doc.lines) return;
		const line = v.state.doc.line(jump.line);
		v.dispatch({ effects: EditorView.scrollIntoView(line.from, { y: 'center' }) });
	}, [jump]);

	return <div ref={host} className="bv-yaml" data-testid="yaml-editor" />;
}
