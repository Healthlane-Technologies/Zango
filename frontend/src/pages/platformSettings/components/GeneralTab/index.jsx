/**
 * Platform-wide defaults applied when an app is launched.
 *
 * Deliberately creation-time only: each new app is stamped with these values
 * and owns them from then on. Changing a default here cannot move an existing
 * app's dates, timezone or theme out from under its users.
 */
import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import Toast from '../../../../components/Notifications/Toast';
import useApi from '../../../../hooks/useApi';

const BASE = '/api/v1/platform/general';

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

const inputCls =
	'rounded-[6px] border border-[#E3E6EF] px-[9px] py-[6px] text-[12.5px] text-[#0B0D14] focus:border-[#5961E5] focus:outline-none';

function Field({ label, hint, children }) {
	return (
		<label className="flex flex-col gap-[4px]">
			<span className="text-[11.5px] font-medium text-[#0B0D14]">{label}</span>
			{children}
			{hint ? <span className="text-[10.5px] text-[#8389A3]">{hint}</span> : null}
		</label>
	);
}

function Select({ value, onChange, options }) {
	return (
		<select className={inputCls} value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
			{options.map((o) => (
				<option key={o.value} value={o.value}>
					{o.label}
				</option>
			))}
		</select>
	);
}

function Toggle({ checked, onChange, label, hint }) {
	return (
		<label className="flex cursor-pointer items-start gap-[9px]">
			<input
				type="checkbox"
				checked={!!checked}
				onChange={(e) => onChange(e.target.checked)}
				className="mt-[2px] h-[15px] w-[15px] accent-[#5961E5]"
			/>
			<span>
				<span className="block text-[12.5px] font-medium text-[#0B0D14]">{label}</span>
				{hint ? <span className="block text-[10.5px] text-[#8389A3]">{hint}</span> : null}
			</span>
		</label>
	);
}

function Card({ title, subtitle, children }) {
	return (
		<section className="rounded-[10px] border border-[#E3E6EF] bg-white p-[18px]">
			<div className="mb-[14px]">
				<h3 className="text-[13px] font-semibold text-[#0B0D14]">{title}</h3>
				{subtitle ? (
					<p className="mt-[2px] text-[11.5px] leading-[16px] text-[#5A607A]">{subtitle}</p>
				) : null}
			</div>
			{children}
		</section>
	);
}

const THEME_SWATCHES = [
	['color.primary', 'Primary'],
	['color.secondary', 'Secondary'],
	['color.background', 'Background'],
	['button.background', 'Button'],
];

function getPath(obj, path) {
	return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

function setPath(obj, path, value) {
	const keys = path.split('.');
	const next = { ...(obj || {}) };
	let cursor = next;
	keys.slice(0, -1).forEach((k) => {
		cursor[k] = { ...(cursor[k] || {}) };
		cursor = cursor[k];
	});
	cursor[keys[keys.length - 1]] = value;
	return next;
}

export default function GeneralTab() {
	const triggerApi = useApi();
	const [options, setOptions] = useState(null);
	const [form, setForm] = useState({});
	const [samples, setSamples] = useState([]);
	const [busy, setBusy] = useState(false);
	const [dirty, setDirty] = useState(false);
	const [loaded, setLoaded] = useState(false);
	const [loadError, setLoadError] = useState('');

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${BASE}/`, type: 'GET', loader: false, showErrorModal: false,
		});
		if (!success || !response) {
			setLoadError(response?.message || 'Could not load settings.');
			setLoaded(true);
			return;
		}
		setLoadError('');
		setOptions(response.options || null);
		setForm({
			auto_domain_enabled: response.auto_domain_enabled,
			base_domain: response.base_domain || '',
			auto_domain_is_primary: response.auto_domain_is_primary,
			default_timezone: response.default_timezone || '',
			default_date_format: response.default_date_format || '',
			default_datetime_format: response.default_datetime_format || '',
			default_language: response.default_language || '',
			default_theme_config: response.default_theme_config || null,
		});
		setDirty(false);
		setLoaded(true);
	}, [triggerApi]);

	useEffect(() => {
		load();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const set = (key, value) => {
		setForm((f) => ({ ...f, [key]: value }));
		setDirty(true);
	};

	const preview = async () => {
		const { success, response } = await triggerApi({
			url: `${BASE}/preview-subdomain/?base_domain=${encodeURIComponent(form.base_domain || '')}`,
			type: 'GET', loader: false, showErrorModal: false,
		});
		if (success && response?.samples) setSamples(response.samples);
		else {
			setSamples([]);
			notify('error', 'Cannot preview', response?.message || 'Enter a valid domain.');
		}
	};

	const save = async () => {
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `${BASE}/`, type: 'POST', loader: false,
			payload: form, showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			setDirty(false);
			setOptions(response?.options || options);
			notify('success', 'Saved', response?.message || 'Applies to apps created from now on.');
		} else {
			notify('error', 'Could not save', response?.message);
		}
	};

	if (!loaded) return <p className="text-[12.5px] text-[#5A607A]">Loading settings…</p>;

	if (loadError) {
		return (
			<div className="rounded-[10px] border border-[#F3C6C6] bg-[#FDECEC] px-[16px] py-[12px]">
				<p className="text-[12.5px] font-semibold text-[#B42318]">
					Could not load general settings
				</p>
				<p className="mt-[2px] text-[11.5px] text-[#B42318]">{loadError}</p>
				<button
					type="button"
					onClick={load}
					className="mt-[8px] rounded-[6px] border border-[#B42318] px-[12px] py-[5px] text-[11.5px] text-[#B42318]"
				>
					Retry
				</button>
			</div>
		);
	}

	const theme = form.default_theme_config || options?.default_theme_config || {};

	return (
		<div className="flex flex-col gap-[14px] pb-[24px]">
			<Card
				title="Automatic domain allocation"
				subtitle="An app with no domain cannot be opened at all — apps are matched by hostname. Turn this on and every new app gets one automatically."
			>
				<div className="flex flex-col gap-[14px]">
					<Toggle
						checked={form.auto_domain_enabled}
						onChange={(v) => set('auto_domain_enabled', v)}
						label="Give every new app a domain"
						hint="Existing apps are not touched."
					/>
					<div className="grid grid-cols-1 gap-[12px] sm:grid-cols-2">
						<Field
							label="Base domain"
							hint="Point a wildcard DNS record (*.your-domain) at this platform, or the generated names will not resolve."
						>
							<input
								className={inputCls}
								value={form.base_domain || ''}
								onChange={(e) => set('base_domain', e.target.value)}
								placeholder="zelthy.com"
							/>
						</Field>
						<div className="flex flex-col justify-end gap-[6px]">
							<button
								type="button"
								onClick={preview}
								className="self-start rounded-[6px] border border-[#E3E6EF] px-[12px] py-[6px] text-[11.5px] text-[#0B0D14] hover:bg-[#F6F7FB]"
							>
								Preview names
							</button>
							{samples.length ? (
								<div className="flex flex-col gap-[2px]">
									{samples.map((s) => (
										<span key={s} className="font-mono text-[11px] text-[#5A607A]">
											{s}
										</span>
									))}
								</div>
							) : null}
						</div>
					</div>
					<Toggle
						checked={form.auto_domain_is_primary}
						onChange={(v) => set('auto_domain_is_primary', v)}
						label="Mark it as the app's primary domain"
						hint="The primary domain is the one the platform links to and builds URLs from."
					/>
				</div>
			</Card>

			<Card
				title="Defaults for new apps"
				subtitle="Each new app is created with these values and owns them from then on. Changing them here never alters an existing app."
			>
				<div className="grid grid-cols-1 gap-[12px] sm:grid-cols-2">
					<Field label="Timezone" hint="Leave blank to let each app choose.">
						<Select
							value={form.default_timezone}
							onChange={(v) => set('default_timezone', v)}
							options={[
								{ value: '', label: 'No default' },
								...(options?.timezones || []).map((tz) => ({ value: tz, label: tz })),
							]}
						/>
					</Field>
					<Field label="Language">
						<Select
							value={form.default_language}
							onChange={(v) => set('default_language', v)}
							options={[
								{ value: '', label: 'No default' },
								...(options?.languages || []).map((l) => ({
									value: l.value,
									label: l.label,
								})),
							]}
						/>
					</Field>
					<Field label="Date format">
						<Select
							value={form.default_date_format}
							onChange={(v) => set('default_date_format', v)}
							options={[
								{ value: '', label: 'No default' },
								...(options?.date_formats || []).map((f) => ({
									value: f.value,
									label: f.example,
								})),
							]}
						/>
					</Field>
					<Field label="Date &amp; time format">
						<Select
							value={form.default_datetime_format}
							onChange={(v) => set('default_datetime_format', v)}
							options={[
								{ value: '', label: 'No default' },
								...(options?.datetime_formats || []).map((f) => ({
									value: f.value,
									label: f.example,
								})),
							]}
						/>
					</Field>
				</div>
			</Card>

			<Card
				title="Default theme"
				subtitle="The palette each new app starts with. Apps can restyle themselves afterwards."
			>
				<div className="flex flex-col gap-[12px]">
					<div className="grid grid-cols-2 gap-[12px] sm:grid-cols-4">
						{THEME_SWATCHES.map(([path, label]) => {
							const value = getPath(theme, path) || '#ffffff';
							return (
								<Field key={path} label={label}>
									<div className="flex items-center gap-[8px]">
										<input
											type="color"
											value={value}
											onChange={(e) =>
												set('default_theme_config', setPath(theme, path, e.target.value))
											}
											className="h-[28px] w-[34px] cursor-pointer rounded-[4px] border border-[#E3E6EF] bg-white p-[2px]"
										/>
										<span className="font-mono text-[11px] text-[#5A607A]">{value}</span>
									</div>
								</Field>
							);
						})}
					</div>
					{form.default_theme_config ? (
						<button
							type="button"
							onClick={() => set('default_theme_config', null)}
							className="self-start text-[11px] text-[#5961E5] hover:underline"
						>
							Reset to the built-in theme
						</button>
					) : (
						<span className="text-[10.5px] text-[#8389A3]">
							Using the built-in theme. Changing a colour above overrides it.
						</span>
					)}
				</div>
			</Card>

			<div className="flex items-center justify-between rounded-[10px] border border-[#E3E6EF] bg-white px-[18px] py-[12px]">
				<span className="text-[11.5px] text-[#5A607A]">
					Applies to apps created from now on.
				</span>
				<div className="flex items-center gap-[8px]">
					{dirty ? <span className="text-[11px] text-[#B45309]">Unsaved changes</span> : null}
					<button
						type="button"
						onClick={save}
						disabled={busy}
						className="rounded-[6px] bg-[#5961E5] px-[16px] py-[7px] text-[12.5px] font-medium text-white hover:bg-[#4B52CC] disabled:opacity-40"
					>
						{busy ? 'Saving…' : 'Save settings'}
					</button>
				</div>
			</div>
		</div>
	);
}
