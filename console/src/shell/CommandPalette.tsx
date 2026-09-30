import { useEffect, useState } from 'react';
import { Command } from 'cmdk';
import * as Dialog from '@radix-ui/react-dialog';
import { useNavigate } from 'react-router-dom';
import { useApps } from '@/api/apps';
import { Icon, type IconName } from '@/ui';
import { appNav, appPath, useCurrentAppId, workspaceNav } from './nav';

interface Entry {
	id: string;
	label: string;
	icon: IconName;
	hint?: string;
	run: () => void;
}

export function useCommandPaletteHotkey(toggle: () => void) {
	useEffect(() => {
		const onKey = (e: KeyboardEvent) => {
			if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
				e.preventDefault();
				toggle();
			}
		};
		document.addEventListener('keydown', onKey);
		return () => document.removeEventListener('keydown', onKey);
	}, [toggle]);
}

export function CommandPalette({
	open,
	onOpenChange,
}: {
	open: boolean;
	onOpenChange: (o: boolean) => void;
}) {
	const navigate = useNavigate();
	const currentApp = useCurrentAppId();
	const { data: apps } = useApps();
	const [query, setQuery] = useState('');

	useEffect(() => {
		if (!open) setQuery('');
	}, [open]);

	const go = (to: string) => () => {
		onOpenChange(false);
		navigate(to);
	};

	const groups: Array<[string, Entry[]]> = [
		['Actions', [{ id: 'new-app', label: 'New app', icon: 'plus', run: go('/apps/new') }]],
		[
			'Apps',
			(apps ?? []).map((a) => ({
				id: `app-${a.uuid}`,
				label: a.name,
				icon: 'apps',
				hint: a.domain_url ?? undefined,
				run: go(appPath(a.uuid)),
			})),
		],
		[
			'Go to',
			[
				...(currentApp
					? appNav
							.flatMap((g) => g.items)
							.map((it) => ({
								id: `app-nav-${it.to}`,
								label: it.label,
								icon: it.icon,
								hint: 'This app',
								run: go(appPath(currentApp, it.to)),
							}))
					: []),
				...workspaceNav
					.flatMap((g) => g.items)
					.map((it) => ({
						id: `nav-${it.to}`,
						label: it.label,
						icon: it.icon,
						run: go(`/${it.to}`),
					})),
			],
		],
	];

	return (
		<Dialog.Root open={open} onOpenChange={onOpenChange}>
			<Dialog.Portal>
				<Dialog.Overlay className="scrim" />
				<Dialog.Content className="palette" aria-describedby={undefined}>
					<Dialog.Title className="sr-only">Search</Dialog.Title>
					<Command label="Search apps or go to a page" loop>
						<div className="pi">
							<Icon name="search" />
							<Command.Input
								value={query}
								onValueChange={setQuery}
								placeholder="Search apps or go to a page"
								autoFocus
							/>
							<kbd>esc</kbd>
						</div>
						<Command.List className="pl">
							<Command.Empty>No results</Command.Empty>
							{groups.map(([heading, entries]) =>
								entries.length ? (
									<Command.Group key={heading} heading={heading}>
										{entries.map((e) => (
											<Command.Item
												key={e.id}
												value={`${e.label} ${e.hint ?? ''} ${e.id}`}
												onSelect={e.run}
											>
												<Icon name={e.icon} />
												{e.label}
												{e.hint && <small className="mono">{e.hint}</small>}
											</Command.Item>
										))}
									</Command.Group>
								) : null,
							)}
						</Command.List>
						<div className="pf">
							<span>↑↓ navigate</span>
							<span>↵ open</span>
							<span>esc close</span>
						</div>
					</Command>
				</Dialog.Content>
			</Dialog.Portal>
		</Dialog.Root>
	);
}
