import { useState } from 'react';
import {
	useCreateTheme,
	useThemes,
	useUpdateTheme,
	type Theme,
	type ThemeConfig,
} from '@/api/themes';
import { Badge, Button, Card, Drawer, EmptyState, ErrorState, Field, Input, Skeleton } from '@/ui';
import { ColorField, Swatch } from './parts';

const COLOR_KEYS = [
	'primary',
	'secondary',
	'background',
	'gray',
	'success',
	'warning',
	'error',
	'info',
] as const;
const BUTTON_KEYS = [
	['background', 'Background'],
	['color', 'Text'],
	['border_color', 'Border'],
] as const;

// Defaults from the classic AddThemeForm.
const DEFAULT_CONFIG: ThemeConfig = {
	color: {
		primary: '#5048ED',
		secondary: '#E1D6AE',
		background: '#ffffff',
		gray: '#717680',
		success: '#52c41a',
		warning: '#faad14',
		error: '#AA4A44',
		info: '#1890ff',
	},
	button: { color: '#ffffff', background: '#5048ED', border_color: '#C7CED3', border_radius: '10' },
	typography: {
		font_family:
			"-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
		font_size_base: '14px',
		line_height: 1.5715,
	},
};

/** Fill gaps so older themes (fewer colour keys) edit cleanly. */
function withDefaults(c: Partial<ThemeConfig> | undefined): ThemeConfig {
	return {
		color: { ...DEFAULT_CONFIG.color, ...(c?.color ?? {}) },
		button: { ...DEFAULT_CONFIG.button, ...(c?.button ?? {}) },
		typography: { ...DEFAULT_CONFIG.typography, ...(c?.typography ?? {}) },
	};
}

const label = (k: string) => k.charAt(0).toUpperCase() + k.slice(1);

function ThemeDrawer({
	appId,
	theme,
	open,
	onClose,
}: {
	appId: string;
	theme: Theme | null;
	open: boolean;
	onClose: () => void;
}) {
	const create = useCreateTheme(appId);
	const update = useUpdateTheme(appId);
	const [name, setName] = useState(theme?.name ?? '');
	const [config, setConfig] = useState<ThemeConfig>(withDefaults(theme?.config));
	const [touched, setTouched] = useState(false);
	const pending = create.isPending || update.isPending;
	const nameError = touched && !name.trim() ? 'Required' : undefined;

	const setColor = (group: 'color' | 'button', k: string, v: string) =>
		setConfig({ ...config, [group]: { ...config[group], [k]: v } });
	const setType = (k: keyof ThemeConfig['typography'], v: string) =>
		setConfig({ ...config, typography: { ...config.typography, [k]: v } });

	const submit = () => {
		setTouched(true);
		if (!name.trim()) return;
		const body = {
			...config,
			typography: {
				...config.typography,
				line_height: Number(config.typography.line_height) || 1.5,
			},
		};
		if (theme)
			update.mutate({ id: theme.id, name: name.trim(), config: body }, { onSuccess: onClose });
		else create.mutate({ name: name.trim(), config: body }, { onSuccess: onClose });
	};

	return (
		<Drawer
			open={open}
			onOpenChange={(o) => !o && onClose()}
			title={theme ? `Edit ${theme.name}` : 'New theme'}
			subtitle="Colours and typography used by the app's generated screens."
			footer={
				<>
					<Button onClick={onClose}>Cancel</Button>
					<Button variant="primary" loading={pending} onClick={submit}>
						{theme ? 'Save theme' : 'Create theme'}
					</Button>
				</>
			}
		>
			<div className="grid gap-5">
				<Field label="Name" error={nameError}>
					{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} autoFocus />}
				</Field>
				<section>
					<h4 className="mb-2 text-[12.5px]">Colours</h4>
					<div className="grid grid-cols-2 gap-3">
						{COLOR_KEYS.map((k) => (
							<ColorField
								key={k}
								label={label(k)}
								value={config.color[k] ?? ''}
								onChange={(v) => setColor('color', k, v)}
							/>
						))}
					</div>
				</section>
				<section>
					<h4 className="mb-2 text-[12.5px]">Buttons</h4>
					<div className="grid grid-cols-2 gap-3">
						{BUTTON_KEYS.map(([k, l]) => (
							<ColorField
								key={k}
								label={l}
								value={config.button[k] ?? ''}
								onChange={(v) => setColor('button', k, v)}
							/>
						))}
						<Field label="Corner radius (px)">
							{(p) => (
								<Input
									{...p}
									type="number"
									min={0}
									value={config.button.border_radius ?? ''}
									onChange={(e) =>
										setConfig({
											...config,
											button: { ...config.button, border_radius: e.target.value },
										})
									}
								/>
							)}
						</Field>
					</div>
				</section>
				<section className="grid gap-3">
					<h4 className="text-[12.5px]">Typography</h4>
					<Field label="Font family">
						{(p) => (
							<Input
								{...p}
								value={config.typography.font_family ?? ''}
								onChange={(e) => setType('font_family', e.target.value)}
							/>
						)}
					</Field>
					<div className="grid grid-cols-2 gap-3">
						<Field label="Base size">
							{(p) => (
								<Input
									{...p}
									value={config.typography.font_size_base ?? ''}
									onChange={(e) => setType('font_size_base', e.target.value)}
								/>
							)}
						</Field>
						<Field label="Line height">
							{(p) => (
								<Input
									{...p}
									type="number"
									step="0.05"
									value={String(config.typography.line_height ?? '')}
									onChange={(e) => setType('line_height', e.target.value)}
								/>
							)}
						</Field>
					</div>
				</section>
				<ThemePreview config={config} />
			</div>
		</Drawer>
	);
}

function ThemePreview({ config }: { config: ThemeConfig }) {
	const b = config.button;
	return (
		<div
			className="rounded-[10px] border border-border p-4"
			style={{ background: config.color.background, fontFamily: config.typography.font_family }}
		>
			<div
				className="text-[11px] font-[550] uppercase tracking-wide"
				style={{ color: config.color.gray }}
			>
				Preview
			</div>
			<div className="mt-1 text-[15px] font-semibold" style={{ color: config.color.primary }}>
				Enrollment ENR-4412
			</div>
			<div className="mt-3 flex gap-2">
				<span
					className="inline-flex h-8 items-center px-3 text-[13px] font-[550]"
					style={{
						background: b.background,
						color: b.color,
						border: `1px solid ${b.border_color}`,
						borderRadius: `${b.border_radius}px`,
					}}
				>
					Approve
				</span>
				{(['success', 'warning', 'error', 'info'] as const).map((k) => (
					<span
						key={k}
						className="inline-flex h-8 items-center rounded-md px-2 text-[12px] font-[550] text-white"
						style={{ background: config.color[k] }}
					>
						{label(k)}
					</span>
				))}
			</div>
		</div>
	);
}

function ThemeCard({
	theme,
	onEdit,
	onActivate,
	activating,
}: {
	theme: Theme;
	onEdit: () => void;
	onActivate: () => void;
	activating: boolean;
}) {
	const c = withDefaults(theme.config);
	return (
		<Card
			className={theme.is_active ? 'ring-2 ring-[var(--ring)]' : undefined}
			style={theme.is_active ? { borderColor: 'var(--accent)' } : undefined}
		>
			<div className="flex items-center gap-2 px-4 pb-2 pt-3.5">
				<b className="truncate font-[550] text-t1">{theme.name}</b>
				{theme.is_active && (
					<Badge tone="accent" dot>
						Active
					</Badge>
				)}
			</div>
			<div className="flex gap-1.5 px-4">
				{COLOR_KEYS.map((k) => (
					<Swatch key={k} color={c.color[k]} title={`${label(k)} ${c.color[k]}`} />
				))}
			</div>
			<div className="truncate px-4 pt-2 text-[12px] text-t3">
				{(c.typography.font_family ?? '').split(',')[0].replace(/'/g, '')}
			</div>
			<div className="mt-3 flex gap-2 border-t border-border-soft px-4 py-2.5">
				<Button size="xs" onClick={onEdit}>
					Edit
				</Button>
				{!theme.is_active && (
					<Button size="xs" variant="ghost" loading={activating} onClick={onActivate}>
						Set active
					</Button>
				)}
			</div>
		</Card>
	);
}

export function ThemeSettings({ appId }: { appId: string }) {
	const { data, isLoading, error, refetch } = useThemes(appId);
	const activate = useUpdateTheme(appId);
	// `undefined` closed, `null` new, a Theme when editing. Keyed remount resets the form.
	const [editing, setEditing] = useState<Theme | null | undefined>(undefined);

	return (
		<>
			<div className="mb-3 flex items-center">
				<p className="text-t3">
					The active theme styles the app's screens. Only one theme is active at a time.
				</p>
				<Button className="ml-auto" variant="primary" icon="plus" onClick={() => setEditing(null)}>
					New theme
				</Button>
			</div>
			{error ? (
				<div className="card">
					<ErrorState error={error} onRetry={() => refetch()} />
				</div>
			) : isLoading ? (
				<div className="grid gap-3 md:grid-cols-3">
					{[0, 1, 2].map((i) => (
						<div key={i} className="card card-b grid gap-3">
							<Skeleton width="50%" />
							<Skeleton height={20} />
						</div>
					))}
				</div>
			) : !data?.length ? (
				<div className="card">
					<EmptyState
						title="No themes yet"
						action={
							<Button size="sm" onClick={() => setEditing(null)}>
								Create a theme
							</Button>
						}
					/>
				</div>
			) : (
				<div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
					{data.map((t) => (
						<ThemeCard
							key={t.id}
							theme={t}
							onEdit={() => setEditing(t)}
							onActivate={() => activate.mutate({ id: t.id, is_active: true })}
							activating={activate.isPending && activate.variables?.id === t.id}
						/>
					))}
				</div>
			)}
			{editing !== undefined && (
				<ThemeDrawer
					key={editing?.id ?? 'new'}
					appId={appId}
					theme={editing}
					open
					onClose={() => setEditing(undefined)}
				/>
			)}
		</>
	);
}
