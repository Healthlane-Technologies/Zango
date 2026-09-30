import { useState } from 'react';
import type { App } from '@/api/apps';
import { useApiMutation } from '@/api/hooks';
import { installPackage, packageKeys, type Package } from '@/api/packages';
import { Button, Field, Modal, Select } from '@/ui';

interface Props {
	/** Packages offered; the first is preselected unless `initial` is given. */
	packages: Package[];
	initial?: string;
	/** Fixed target app, or a list to choose from (Package catalog). */
	app?: App;
	apps?: App[];
	onClose: () => void;
}

export function InstallPackageModal({ packages, initial, app, apps, onClose }: Props) {
	const [name, setName] = useState(initial ?? packages[0]?.name ?? '');
	const pkg = packages.find((p) => p.name === name);
	const [version, setVersion] = useState(pkg?.versions?.[0] ?? '');
	const [target, setTarget] = useState(app?.uuid ?? apps?.[0]?.uuid ?? '');
	const targetApp = app ?? apps?.find((a) => a.uuid === target);

	const install = useApiMutation({
		fn: () => installPackage(target, name, version),
		invalidate: [packageKeys.all(target)],
		success: (message) => `${message} · ${name} ${version} in ${targetApp?.name ?? 'app'}`,
		onSuccess: onClose,
	});

	const pickPackage = (next: string) => {
		setName(next);
		setVersion(packages.find((p) => p.name === next)?.versions?.[0] ?? '');
	};

	return (
		<Modal
			open
			onOpenChange={(o) => !o && !install.isPending && onClose()}
			title="Install package"
			subtitle={targetApp ? `Into ${targetApp.name}` : undefined}
			footer={
				<>
					<Button onClick={onClose} disabled={install.isPending}>
						Cancel
					</Button>
					<Button
						variant="primary"
						disabled={!name || !version || !target}
						loading={install.isPending}
						onClick={() => install.mutate()}
					>
						{install.isPending ? 'Installing…' : 'Install'}
					</Button>
				</>
			}
		>
			<div className="grid gap-4">
				{apps && !app && (
					<Field label="App">
						{(p) => (
							<Select {...p} value={target} onChange={(e) => setTarget(e.target.value)}>
								{apps.map((a) => (
									<option key={a.uuid} value={a.uuid}>
										{a.name}
									</option>
								))}
							</Select>
						)}
					</Field>
				)}
				<Field label="Package">
					{(p) => (
						<Select
							{...p}
							value={name}
							onChange={(e) => pickPackage(e.target.value)}
							disabled={packages.length < 2}
						>
							{packages.map((x) => (
								<option key={x.name} value={x.name}>
									{x.name}
								</option>
							))}
						</Select>
					)}
				</Field>
				<Field
					label="Version"
					hint={
						pkg?.versions?.length
							? 'Newest first. Only versions compatible with this Zango release are listed.'
							: undefined
					}
				>
					{(p) => (
						<Select
							{...p}
							value={version}
							onChange={(e) => setVersion(e.target.value)}
							disabled={!pkg?.versions?.length}
						>
							{(pkg?.versions ?? []).map((v, i) => (
								<option key={v} value={v}>
									{v}
									{i === 0 ? ' (latest)' : ''}
								</option>
							))}
						</Select>
					)}
				</Field>
				<p className="text-[12px] text-t3">
					Installing runs the package's migrations and re-syncs the app's policies and tasks. It can
					take a minute.
				</p>
			</div>
		</Modal>
	);
}
