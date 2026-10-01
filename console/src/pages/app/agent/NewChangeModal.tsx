import { useEffect, useState } from 'react';
import type { NewRoundInput } from '@/api/agentMode';
import type { TemplateReference } from '@/api/templates';
import { Button, Field, Modal, Textarea } from '@/ui';
import { DocumentDrop, DRAFT_GUIDANCE, ReferencePicker } from '../../new/intake';

/**
 * "New change" on an app built from a template: like New app's intake, the agent drafts the
 * change in one pass from a detailed brief and/or documents (the app's current journey is
 * its starting point unless a reference is picked).
 */
export function NewChangeModal({
	open,
	onOpenChange,
	references,
	onSubmit,
}: {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	references: TemplateReference[] | undefined;
	onSubmit: (input: NewRoundInput) => Promise<boolean>;
}) {
	const [prompt, setPrompt] = useState('');
	const [files, setFiles] = useState<File[]>([]);
	const [reference, setReference] = useState('');
	const [busy, setBusy] = useState(false);
	useEffect(() => {
		if (!open) {
			setPrompt('');
			setFiles([]);
			setReference('');
		}
	}, [open]);

	const trimmed = prompt.trim();
	const ready = (!!trimmed || files.length > 0) && !busy;
	const submit = async () => {
		if (!ready) return;
		setBusy(true);
		const ok = await onSubmit({
			prompt: trimmed || undefined,
			reference: reference || undefined,
			documents: files,
		});
		setBusy(false);
		if (ok) onOpenChange(false);
	};

	return (
		<Modal
			open={open}
			onOpenChange={onOpenChange}
			large
			title="New change"
			subtitle="The agent drafts the change in one pass and flags what it had to infer."
			footer={
				<>
					<Button onClick={() => onOpenChange(false)} disabled={busy}>
						Cancel
					</Button>
					<Button variant="primary" icon="agent" disabled={!ready} loading={busy} onClick={submit}>
						Start the draft
					</Button>
				</>
			}
		>
			<div className="grid gap-4">
				<Field label="What should change?" hint={DRAFT_GUIDANCE}>
					{(p) => (
						<Textarea
							{...p}
							rows={7}
							autoFocus
							value={prompt}
							disabled={busy}
							placeholder="e.g. add a second program for a new indication, with its own eligibility and a buy-4-get-2 scheme"
							onChange={(e) => setPrompt(e.target.value)}
							onKeyDown={(e) => {
								if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
									e.preventDefault();
									submit();
								}
							}}
						/>
					)}
				</Field>
				<DocumentDrop files={files} onChange={setFiles} disabled={busy} />
				<ReferencePicker
					references={references}
					value={reference}
					onChange={setReference}
					disabled={busy}
				/>
			</div>
		</Modal>
	);
}
