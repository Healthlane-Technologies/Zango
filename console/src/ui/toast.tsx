import { useSyncExternalStore } from 'react';
import { cx } from './cx';
import { Icon } from './Icon';

interface ToastItem {
	id: number;
	message: string;
	kind: 'success' | 'error';
}

const DURATION_MS = 2800;
let items: ToastItem[] = [];
let nextId = 1;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

function push(message: string, kind: ToastItem['kind']) {
	const id = nextId++;
	items = [...items, { id, message, kind }];
	emit();
	setTimeout(() => {
		items = items.filter((t) => t.id !== id);
		emit();
	}, DURATION_MS);
}

export const toast = {
	success: (message: string) => push(message, 'success'),
	error: (message: string) => push(message, 'error'),
};

function subscribe(l: () => void) {
	listeners.add(l);
	return () => listeners.delete(l);
}

export function Toaster() {
	const list = useSyncExternalStore(subscribe, () => items);
	return (
		<div className="toasts" role="status" aria-live="polite">
			{list.map((t) => (
				<div key={t.id} className={cx('toast', t.kind === 'error' && 'error')}>
					<Icon name={t.kind === 'error' ? 'alert' : 'check'} weight={2.4} />
					<span>{t.message}</span>
				</div>
			))}
		</div>
	);
}
