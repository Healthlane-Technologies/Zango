import type { ReactNode } from 'react';
import { Button } from './Button';

/**
 * Floating bar for a settings form, shown only while there are unsaved changes.
 * Pass `submit` when it sits inside a <form> whose onSubmit saves.
 */
export function SaveBar({
	dirty,
	saving,
	onSave,
	onDiscard,
	note,
	label = 'Save changes',
	submit,
}: {
	dirty: boolean;
	saving: boolean;
	onSave?: () => void;
	onDiscard?: () => void;
	note?: ReactNode;
	label?: string;
	submit?: boolean;
}) {
	if (!dirty && !saving) return null;
	return (
		<div className="sticky bottom-4 z-10 mt-6 flex items-center gap-3 rounded-[10px] border border-border bg-panel px-4 py-2.5 shadow-pop fi">
			<span className="min-w-0">
				<span className="text-t1">You have unsaved changes</span>
				{note && <span className="block text-[12px] text-t3">{note}</span>}
			</span>
			<div className="ml-auto flex gap-2">
				{onDiscard && (
					<Button size="sm" disabled={saving} onClick={onDiscard}>
						Discard
					</Button>
				)}
				<Button
					size="sm"
					variant="primary"
					type={submit ? 'submit' : 'button'}
					loading={saving}
					onClick={submit ? undefined : onSave}
				>
					{label}
				</Button>
			</div>
		</div>
	);
}
