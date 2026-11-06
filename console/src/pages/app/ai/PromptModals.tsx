import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
	aiKeys,
	createPrompt,
	templateVars,
	useCreateVersion,
	useUpdatePrompt,
	type Prompt,
	type PromptType,
} from '@/api/ai';
import { Badge, Button, Field, Input, Modal, Segmented, Select, Textarea, toast } from '@/ui';
import { DiffView } from './diff';
import { PromptText } from './parts';

const NAME_RE = /^[a-z0-9-]+$/;

function VarChips({ content }: { content: string }) {
	const vars = templateVars(content);
	if (!vars.length) return null;
	return (
		<div className="flex flex-wrap items-center gap-1 text-[12px] text-t3">
			Variables:
			{vars.map((v) => (
				<Badge key={v} tone="violet">
					{`{{${v}}}`}
				</Badge>
			))}
		</div>
	);
}

/** New prompt; version 1 is live straight away. */
export function CreatePromptModal({
	appId,
	fixedType,
	onClose,
	onCreated,
}: {
	appId: string;
	/** From an agent's picker: the type is decided by the slot. */
	fixedType?: PromptType;
	onClose: () => void;
	onCreated?: (name: string) => void;
}) {
	const qc = useQueryClient();
	const [name, setName] = useState('');
	const [type, setType] = useState<PromptType>(fixedType ?? 'system');
	const [description, setDescription] = useState('');
	const [content, setContent] = useState('');
	const [note, setNote] = useState('');
	const [saving, setSaving] = useState(false);

	const nameError = name && !NAME_RE.test(name) ? 'Lowercase letters, numbers and hyphens only' : undefined;
	const valid = !!name && !nameError && !!content.trim();

	const save = async () => {
		setSaving(true);
		try {
			await createPrompt(appId, {
				name,
				description,
				type,
				content,
				change_description: note.trim() || 'Initial version',
			});
			await qc.invalidateQueries({ queryKey: aiKeys.prompts(appId) });
			toast.success(`${name} created as v1`);
			onCreated?.(name);
			onClose();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : String(err));
		} finally {
			setSaving(false);
		}
	};

	return (
		<Modal
			open
			large
			onOpenChange={(o) => !o && onClose()}
			title={fixedType ? `New ${fixedType} prompt` : 'New prompt'}
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button variant="primary" disabled={!valid} loading={saving} onClick={save}>
						Create prompt
					</Button>
				</>
			}
		>
			<div className="grid gap-3">
				<div className="grid grid-cols-[1fr_160px] gap-3">
					<Field label="Name" error={nameError} hint="Agents link prompts by this name.">
						{(p) => (
							<Input
								{...p}
								className="mono"
								autoFocus
								value={name}
								placeholder="e.g. triage-system"
								onChange={(e) => setName(e.target.value)}
							/>
						)}
					</Field>
					<Field label="Type">
						{(p) => (
							<Select
								{...p}
								value={type}
								disabled={!!fixedType}
								onChange={(e) => setType(e.target.value as PromptType)}
							>
								<option value="system">System</option>
								<option value="user">User</option>
							</Select>
						)}
					</Field>
				</div>
				<Field label="Description">
					{(p) => (
						<Input
							{...p}
							value={description}
							placeholder="Optional"
							onChange={(e) => setDescription(e.target.value)}
						/>
					)}
				</Field>
				<Field label="Content" hint="Use {{variable_name}} for values filled in at run time.">
					{(p) => (
						<Textarea
							{...p}
							className="mono"
							rows={10}
							value={content}
							onChange={(e) => setContent(e.target.value)}
						/>
					)}
				</Field>
				<VarChips content={content} />
				<Field label="Version note">
					{(p) => (
						<Input
							{...p}
							value={note}
							placeholder="Initial version"
							onChange={(e) => setNote(e.target.value)}
						/>
					)}
				</Field>
			</div>
		</Modal>
	);
}

/** Name, description and type only; text changes go through a new version. */
export function EditPromptModal({
	appId,
	prompt,
	onClose,
}: {
	appId: string;
	prompt: Prompt;
	onClose: () => void;
}) {
	const update = useUpdatePrompt(appId);
	const [name, setName] = useState(prompt.name);
	const [description, setDescription] = useState(prompt.description);
	const [type, setType] = useState<PromptType>(prompt.type);

	return (
		<Modal
			open
			onOpenChange={(o) => !o && onClose()}
			title={`Edit ${prompt.name}`}
			subtitle="To change the text, create a new version."
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button
						variant="primary"
						disabled={!name.trim()}
						loading={update.isPending}
						onClick={() =>
							update.mutate(
								{ id: prompt.id, name: name.trim(), description, type },
								{ onSuccess: onClose },
							)
						}
					>
						Save
					</Button>
				</>
			}
		>
			<div className="grid gap-3">
				<Field
					label="Name"
					hint={
						prompt.used_by_agents.length
							? 'Linked agents keep working after a rename.'
							: undefined
					}
				>
					{(p) => (
						<Input {...p} className="mono" value={name} onChange={(e) => setName(e.target.value)} />
					)}
				</Field>
				<Field label="Description">
					{(p) => (
						<Input {...p} value={description} onChange={(e) => setDescription(e.target.value)} />
					)}
				</Field>
				<Field label="Type">
					{(p) => (
						<Select {...p} value={type} onChange={(e) => setType(e.target.value as PromptType)}>
							<option value="system">System</option>
							<option value="user">User</option>
						</Select>
					)}
				</Field>
			</div>
		</Modal>
	);
}

type Mode = 'edit' | 'side' | 'diff';

/** New draft version, prefilled with the live text. */
export function NewVersionModal({
	appId,
	prompt,
	onClose,
}: {
	appId: string;
	prompt: Prompt;
	onClose: () => void;
}) {
	const create = useCreateVersion(appId);
	const live = prompt.active_version?.content ?? '';
	const [content, setContent] = useState(live);
	const [note, setNote] = useState('');
	const [mode, setMode] = useState<Mode>('edit');

	const editor = (rows: number) => (
		<Textarea
			aria-label="New version"
			className="mono"
			rows={rows}
			spellCheck={false}
			value={content}
			onChange={(e) => setContent(e.target.value)}
		/>
	);

	return (
		<Modal
			open
			large
			onOpenChange={(o) => !o && onClose()}
			title={`New version of ${prompt.name}`}
			subtitle="Saved as a draft. Make it live from the version history."
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button
						variant="primary"
						disabled={!content.trim() || content === live}
						loading={create.isPending}
						onClick={() =>
							create.mutate(
								{ id: prompt.id, content, change_description: note },
								{ onSuccess: onClose },
							)
						}
					>
						Create draft
					</Button>
				</>
			}
		>
			{prompt.active_version && (
				<div className="mb-3 flex items-center gap-3">
					<Segmented<Mode>
						label="View"
						value={mode}
						onChange={setMode}
						options={[
							{ value: 'edit', label: 'Edit' },
							{ value: 'side', label: 'Side by side' },
							{ value: 'diff', label: 'Changes' },
						]}
					/>
					<span className="text-[12px] text-t3">Starting from v{prompt.active_version.version_number} (live)</span>
				</div>
			)}
			{mode === 'edit' && editor(16)}
			{mode !== 'edit' && (
				<div className="grid grid-cols-2 gap-3">
					{mode === 'side' ? <PromptText content={live} maxHeight={380} /> : editor(16)}
					{mode === 'side' ? (
						editor(16)
					) : (
						<DiffView before={live} after={content} maxHeight={380} />
					)}
				</div>
			)}
			<div className="mt-2">
				<VarChips content={content} />
			</div>
			<div className="mt-3">
				<Field label="What changed?">
					{(p) => (
						<Input
							{...p}
							value={note}
							placeholder="e.g. Added escalation rules"
							onChange={(e) => setNote(e.target.value)}
						/>
					)}
				</Field>
			</div>
		</Modal>
	);
}
