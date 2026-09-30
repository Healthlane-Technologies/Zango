import type { ReactNode } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { Button } from './Button';
import { cx } from './cx';
import { Icon, type IconName } from './Icon';

interface OverlayProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	title: ReactNode;
	subtitle?: ReactNode;
	footer?: ReactNode;
	children: ReactNode;
}

function CloseButton() {
	return (
		<Dialog.Close className="ib ml-auto" aria-label="Close">
			<Icon name="x" />
		</Dialog.Close>
	);
}

/** Right-hand panel for detail and edit forms. */
export function Drawer({ open, onOpenChange, title, subtitle, footer, children }: OverlayProps) {
	return (
		<Dialog.Root open={open} onOpenChange={onOpenChange}>
			<Dialog.Portal>
				<Dialog.Overlay className="scrim" />
				<Dialog.Content className="drawer" aria-describedby={undefined}>
					<div className="dh">
						<div className="min-w-0">
							<Dialog.Title asChild>
								<h3>{title}</h3>
							</Dialog.Title>
							{subtitle && <small className="text-t3">{subtitle}</small>}
						</div>
						<CloseButton />
					</div>
					<div className="db">{children}</div>
					{footer && <div className="df">{footer}</div>}
				</Dialog.Content>
			</Dialog.Portal>
		</Dialog.Root>
	);
}

export function Modal({
	open,
	onOpenChange,
	title,
	subtitle,
	footer,
	children,
	large,
}: OverlayProps & { large?: boolean }) {
	return (
		<Dialog.Root open={open} onOpenChange={onOpenChange}>
			<Dialog.Portal>
				<Dialog.Overlay className="scrim" />
				<Dialog.Content className={cx('modal', large && 'lg')} aria-describedby={undefined}>
					<div className="mh">
						<div className="min-w-0">
							<Dialog.Title asChild>
								<h3>{title}</h3>
							</Dialog.Title>
							{subtitle && <small>{subtitle}</small>}
						</div>
						<CloseButton />
					</div>
					<div className="mb">{children}</div>
					{footer && <div className="mf">{footer}</div>}
				</Dialog.Content>
			</Dialog.Portal>
		</Dialog.Root>
	);
}

export interface MenuItem {
	label: ReactNode;
	icon?: IconName;
	onSelect: () => void;
	danger?: boolean;
	disabled?: boolean;
}

/** Dropdown menu; pass `null` in `items` for a separator. */
export function Menu({
	trigger,
	items,
	align = 'end',
}: {
	trigger: ReactNode;
	items: Array<MenuItem | null>;
	align?: 'start' | 'end';
}) {
	return (
		<DropdownMenu.Root modal={false}>
			<DropdownMenu.Trigger asChild>{trigger}</DropdownMenu.Trigger>
			<DropdownMenu.Portal>
				{/* React bubbles events through portals, so stop clicks reaching a clickable row behind the menu. */}
				<DropdownMenu.Content
					className="menu"
					align={align}
					sideOffset={4}
					onClick={(e) => e.stopPropagation()}
				>
					{items.map((it, i) =>
						it === null ? (
							<DropdownMenu.Separator key={i} />
						) : (
							<DropdownMenu.Item
								key={i}
								className={cx(it.danger && 'danger')}
								disabled={it.disabled}
								onSelect={it.onSelect}
							>
								{it.icon && <Icon name={it.icon} />}
								{it.label}
							</DropdownMenu.Item>
						),
					)}
				</DropdownMenu.Content>
			</DropdownMenu.Portal>
		</DropdownMenu.Root>
	);
}

/** The `⋯` button used for row actions. Stops the click reaching a clickable row. */
export function RowMenu({
	items,
	label = 'Actions',
}: {
	items: Array<MenuItem | null>;
	label?: string;
}) {
	return (
		<Menu
			items={items}
			trigger={
				<button
					type="button"
					className="ib"
					aria-label={label}
					onClick={(e) => e.stopPropagation()}
				>
					<Icon name="dots" weight={2.4} />
				</button>
			}
		/>
	);
}

/** Confirmation dialog for a single consequential action. */
export function ConfirmModal({
	open,
	onOpenChange,
	title,
	children,
	confirmLabel,
	danger,
	loading,
	onConfirm,
}: {
	open: boolean;
	onOpenChange: (o: boolean) => void;
	title: ReactNode;
	children: ReactNode;
	confirmLabel: string;
	danger?: boolean;
	loading?: boolean;
	onConfirm: () => void;
}) {
	return (
		<Modal
			open={open}
			onOpenChange={onOpenChange}
			title={title}
			footer={
				<>
					<Button onClick={() => onOpenChange(false)}>Cancel</Button>
					<Button variant={danger ? 'danger' : 'primary'} loading={loading} onClick={onConfirm}>
						{confirmLabel}
					</Button>
				</>
			}
		>
			{children}
		</Modal>
	);
}
