import { useId, useRef, useState, type DragEvent } from 'react';
import type { TemplateReference } from '@/api/templates';
import { Icon, cx } from '@/ui';
import './intake.css';

// What a template draft is made from: a detailed brief, documents (SOPs, RFPs, protocols…),
// and optionally a reference journey to start from. Shared by New app and New change.

export const MAX_FILES = 10;
export const MAX_TOTAL_BYTES = 25 * 1024 * 1024;
export const ACCEPTED = [
	'pdf', 'docx', 'xlsx', 'csv', 'txt', 'md', 'html', 'htm', 'png', 'jpg', 'jpeg', 'gif', 'webp',
] as const;
export const IMAGE_EXTS = ['png', 'jpg', 'jpeg', 'gif', 'webp'];

export const DRAFT_GUIDANCE =
	'Who uses it, the programs, eligibility, documents, dispensing and schemes, consent, reports — or just upload your SOP or RFP.';

export const extOf = (name: string) => name.split('.').pop()?.toLowerCase() ?? '';

export function formatBytes(n: number): string {
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
	return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

/** Add `incoming` to `current`, returning the accepted list and why anything was refused. */
export function addFiles(current: File[], incoming: File[]): { files: File[]; errors: string[] } {
	const files = [...current];
	const errors: string[] = [];
	for (const file of incoming) {
		if (!ACCEPTED.includes(extOf(file.name) as (typeof ACCEPTED)[number])) {
			errors.push(`${file.name}: only ${ACCEPTED.join(', ').toUpperCase()} files are supported.`);
			continue;
		}
		if (files.some((f) => f.name === file.name && f.size === file.size)) continue;
		if (files.length >= MAX_FILES) {
			errors.push(`At most ${MAX_FILES} documents.`);
			break;
		}
		const total = files.reduce((n, f) => n + f.size, 0) + file.size;
		if (total > MAX_TOTAL_BYTES) {
			errors.push(
				`${file.name}: documents can add up to ${formatBytes(MAX_TOTAL_BYTES)} in total.`,
			);
			continue;
		}
		files.push(file);
	}
	return { files, errors };
}

/** Drop zone + file list. Refused files are explained inline; nothing is uploaded until submit. */
export function DocumentDrop({
	files,
	onChange,
	disabled,
}: {
	files: File[];
	onChange: (files: File[]) => void;
	disabled?: boolean;
}) {
	const input = useRef<HTMLInputElement>(null);
	const [over, setOver] = useState(false);
	const [errors, setErrors] = useState<string[]>([]);
	const add = (list: FileList | null) => {
		if (!list?.length) return;
		const result = addFiles(files, Array.from(list));
		setErrors(result.errors);
		onChange(result.files);
	};
	const onDrop = (e: DragEvent) => {
		e.preventDefault();
		setOver(false);
		if (!disabled) add(e.dataTransfer.files);
	};
	const total = files.reduce((n, f) => n + f.size, 0);

	return (
		<div className="grid gap-2">
			<div
				className={cx('docdrop', over && 'over', disabled && 'disabled')}
				onDragOver={(e) => {
					e.preventDefault();
					if (!disabled) setOver(true);
				}}
				onDragLeave={() => setOver(false)}
				onDrop={onDrop}
				role="button"
				tabIndex={disabled ? -1 : 0}
				aria-label="Add documents"
				onClick={() => !disabled && input.current?.click()}
				onKeyDown={(e) => {
					if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
						e.preventDefault();
						input.current?.click();
					}
				}}
			>
				<Icon name="clip" />
				<span>
					<b>Drop SOPs, RFPs, process documents or screenshots</b>, or click to choose
					<small>
						{ACCEPTED.map((a) => a.toUpperCase()).join(', ')} · up to {MAX_FILES} files,{' '}
						{formatBytes(MAX_TOTAL_BYTES)} in total
					</small>
				</span>
				<input
					ref={input}
					type="file"
					multiple
					hidden
					accept={ACCEPTED.map((a) => `.${a}`).join(',')}
					onChange={(e) => {
						add(e.target.files);
						e.target.value = '';
					}}
				/>
			</div>
			{errors.length > 0 && (
				<ul className="docdrop-err" role="alert">
					{errors.map((e) => (
						<li key={e}>{e}</li>
					))}
				</ul>
			)}
			{files.length > 0 && (
				<ul className="docs" aria-label="Documents to upload">
					{files.map((f) => (
						<li key={`${f.name}-${f.size}`}>
							<span className="docext">{extOf(f.name).toUpperCase()}</span>
							<span className="min-w-0 flex-1 truncate">{f.name}</span>
							<span className="text-t4">{formatBytes(f.size)}</span>
							<button
								type="button"
								className="ib"
								aria-label={`Remove ${f.name}`}
								disabled={disabled}
								onClick={() => onChange(files.filter((x) => x !== f))}
							>
								<Icon name="x" />
							</button>
						</li>
					))}
					<li className="docs-total">
						{files.length} document{files.length > 1 ? 's' : ''} · {formatBytes(total)}
					</li>
				</ul>
			)}
		</div>
	);
}

/** "Start from": a template reference journey, or let the agent pick the closest one. */
export function ReferencePicker({
	references,
	value,
	onChange,
	disabled,
}: {
	references: TemplateReference[] | undefined;
	value: string;
	onChange: (v: string) => void;
	disabled?: boolean;
}) {
	const id = useId();
	if (!references?.length) return null;
	const picked = references.find((r) => r.id === value);
	return (
		<div className="field">
			<label htmlFor={id}>Start from</label>
			<select
				id={id}
				className="select"
				value={value}
				disabled={disabled}
				onChange={(e) => onChange(e.target.value)}
			>
				<option value="">Let the agent choose</option>
				{references.map((r) => (
					<option key={r.id} value={r.id}>
						{r.title}
					</option>
				))}
			</select>
			<span className="hint">
				{picked?.summary ||
					'The agent starts from the closest reference journey and adapts it to your material.'}
			</span>
		</div>
	);
}
