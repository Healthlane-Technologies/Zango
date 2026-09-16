/**
 * Platform-level Build with AI configuration.
 *
 * Two agents are configured separately because they do very different work:
 * the analyst reads and asks questions in short turns; the builder writes
 * dozens of files across a long run. Running both on the same model and
 * budget is usually the wrong default.
 *
 * Stored values override the environment, so an operator can change the model
 * or rotate the key without a redeploy.
 */
import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import Toast from '../../../../components/Notifications/Toast';
import useApi from '../../../../hooks/useApi';

const BASE = '/api/v1/platform/agent-mode';

const MODELS = [
	{ value: '', label: 'SDK default' },
	{ value: 'claude-opus-5', label: 'Claude Opus 5 — most capable' },
	{ value: 'claude-sonnet-5', label: 'Claude Sonnet 5 — faster, cheaper' },
	{ value: 'claude-haiku-4-5', label: 'Claude Haiku 4.5 — cheapest' },
];
const EFFORTS = [
	{ value: '', label: 'Default' },
	{ value: 'low', label: 'Low' },
	{ value: 'medium', label: 'Medium' },
	{ value: 'high', label: 'High' },
	{ value: 'xhigh', label: 'Extra high' },
	{ value: 'max', label: 'Max' },
];

function notify(type, title, description) {
	toast.custom(
		(t) => <Toast type={type} toastRef={t} title={title} description={description} />,
		{ duration: 5000, position: 'bottom-left' }
	);
}

function Field({ label, hint, children }) {
	return (
		<label className="flex flex-col gap-[4px]">
			<span className="text-[11.5px] font-medium text-[#0B0D14]">{label}</span>
			{children}
			{hint ? <span className="text-[10.5px] text-[#8389A3]">{hint}</span> : null}
		</label>
	);
}

const inputCls =
	'rounded-[6px] border border-[#E3E6EF] px-[9px] py-[6px] text-[12.5px] text-[#0B0D14] focus:border-[#5961E5] focus:outline-none';

function Select({ value, onChange, options }) {
	return (
		<select className={inputCls} value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
			{options.map((o) => (
				<option key={o.value} value={o.value}>{o.label}</option>
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

function Card({ title, subtitle, badge, children }) {
	return (
		<section className="rounded-[10px] border border-[#E3E6EF] bg-white p-[18px]">
			<div className="mb-[14px] flex items-start justify-between gap-[12px]">
				<div>
					<h3 className="text-[13px] font-semibold text-[#0B0D14]">{title}</h3>
					{subtitle ? (
						<p className="mt-[2px] text-[11.5px] leading-[16px] text-[#5A607A]">{subtitle}</p>
					) : null}
				</div>
				{badge}
			</div>
			{children}
		</section>
	);
}

export default function BuildWithAITab() {
	const triggerApi = useApi();
	const [data, setData] = useState(null);
	const [form, setForm] = useState({});
	const [apiKey, setApiKey] = useState('');
	const [busy, setBusy] = useState(false);
	const [dirty, setDirty] = useState(false);
	const [loaded, setLoaded] = useState(false);
	const [loadError, setLoadError] = useState('');

	const load = useCallback(async () => {
		const { response, success } = await triggerApi({
			url: `${BASE}/settings/`, type: 'GET', loader: false, showErrorModal: false,
		});
		if (!success || !response) {
			setLoadError(response?.message || 'Could not load settings.');
			setLoaded(true);
			return;
		}
		{
			setLoadError('');
			setData(response);
			setForm(response.settings || {
				is_enabled: response.resolved?.enabled ?? false,
				ensure_packages: response.resolved?.ensure_packages ?? true,
				allow_frontend_build: response.resolved?.allow_frontend_build ?? false,
				default_model: response.resolved?.model || '',
				default_effort: response.resolved?.effort || '',
				max_run_seconds: response.resolved?.max_run_seconds ?? 1800,
				max_budget_usd: response.resolved?.max_budget_usd ?? '',
				max_turns: response.resolved?.max_turns ?? '',
				analyst_model: response.resolved?.analyst_model || '',
				analyst_effort: response.resolved?.analyst_effort || '',
				analyst_budget_usd: response.resolved?.analyst_budget_usd ?? '',
				analyst_max_turns: response.resolved?.analyst_max_turns ?? '',
				monthly_budget_usd: '',
			});
			setDirty(false);
		}
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

	const save = async () => {
		setBusy(true);
		const payload = { ...form };
		if (apiKey.trim()) payload.api_key = apiKey.trim();
		const { success, response } = await triggerApi({
			url: `${BASE}/settings/`, type: 'POST', loader: false,
			payload, showErrorModal: false,
		});
		setBusy(false);
		if (success) {
			setApiKey('');
			setDirty(false);
			setData(response);
			notify(
				'success',
				'Saved',
				'Applies to the next run. Runs already in progress keep their settings.'
			);
		} else {
			notify('error', 'Could not save', response?.message);
		}
	};

	const validate = async () => {
		setBusy(true);
		const { success, response } = await triggerApi({
			url: `${BASE}/settings/validate/`, type: 'POST', loader: false,
			payload: {}, showErrorModal: false,
		});
		setBusy(false);
		if (success && response?.valid) notify('success', 'Key works', response.message);
		else notify('error', 'Key check failed', response?.message || 'Unknown error');
		load();
	};

	if (!loaded) {
		return (
			<p className="text-[12.5px] text-[#5A607A]">Loading settings…</p>
		);
	}
	if (loadError || !data) {
		return (
			<div className="rounded-[10px] border border-[#F3C6C6] bg-[#FDECEC] px-[16px] py-[12px]">
				<p className="text-[12.5px] font-semibold text-[#B42318]">
					Could not load Build with AI settings
				</p>
				<p className="mt-[2px] text-[11.5px] text-[#B42318]">
					{loadError || 'The server returned no data.'}
				</p>
				<button
					type="button"
					onClick={load}
					className="mt-[8px] rounded-[6px] border border-[#F3C6C6] px-[12px] py-[5px] text-[12px] font-medium text-[#B42318] hover:bg-[#FBDCDC]"
				>
					Retry
				</button>
			</div>
		);
	}
	const env = data.environment || {};
	const keyKnown = data.has_api_key || env.env_api_key_present;

	return (
		<div className="flex flex-col gap-[16px] pb-[4px]">
			{/* Primary action, mirrored at the foot of the form. Repeated here
			    so it is reachable without scrolling past four cards. */}
			<div className="flex items-center justify-end gap-[10px]">
				{dirty ? (
					<span className="text-[11px] text-[#B45309]">Unsaved changes</span>
				) : null}
				<button
					type="button"
					onClick={save}
					disabled={busy}
					className="rounded-[6px] bg-[#5961E5] px-[16px] py-[7px] text-[12.5px] font-medium text-white hover:bg-[#4B52CC] disabled:opacity-40"
				>
					{busy ? 'Saving…' : 'Save settings'}
				</button>
			</div>

			{/* Credential */}
			<Card
				title="Anthropic API key"
				subtitle="Used by both agents. Stored encrypted; never shown again once saved. A rotated key applies to the next run, not one already in progress."
				badge={
					<span
						className="rounded-full px-[9px] py-[3px] text-[10px] font-semibold uppercase tracking-[0.05em]"
						style={
							keyKnown
								? { backgroundColor: '#E9F8F1', color: '#0B7A57' }
								: { backgroundColor: '#FDECEC', color: '#B42318' }
						}
					>
						{data.has_api_key ? 'Configured' : env.env_api_key_present ? 'From environment' : 'Not set'}
					</span>
				}
			>
				<div className="flex flex-col gap-[10px]">
					<Field
						label={data.has_api_key ? 'Replace key' : 'API key'}
						hint={
							data.has_api_key
								? `Currently ${data.masked_config?.api_key || 'set'}. Leave blank to keep it.`
								: env.env_api_key_present
								? 'An environment key is in use. Saving one here overrides it.'
								: 'Starts with sk-ant-'
						}
					>
						<input
							type="password"
							autoComplete="new-password"
							className={inputCls}
							placeholder="sk-ant-…"
							value={apiKey}
							onChange={(e) => setApiKey(e.target.value)}
						/>
					</Field>
					<div className="flex items-center gap-[10px]">
						<button
							type="button"
							onClick={validate}
							disabled={busy || !keyKnown}
							className="rounded-[6px] border border-[#E3E6EF] px-[12px] py-[6px] text-[12px] font-medium text-[#0B0D14] hover:bg-[#F0F2F7] disabled:opacity-40"
						>
							Test key
						</button>
						{data.is_validated ? (
							<span className="text-[11px] text-[#0B7A57]">
								Verified{data.last_validated_at ? ` · ${new Date(data.last_validated_at).toLocaleString()}` : ''}
							</span>
						) : null}
					</div>
				</div>
			</Card>

			{/* Requirement agent */}
			<Card
				title="Requirement agent"
				subtitle="Phase 1 — interviews the user and writes the specification. Read-only; short turns."
			>
				<div className="grid grid-cols-2 gap-[12px]">
					<Field label="Model" hint="Falls back to the build agent's model.">
						<Select value={form.analyst_model} onChange={(v) => set('analyst_model', v)} options={MODELS} />
					</Field>
					<Field label="Effort">
						<Select value={form.analyst_effort} onChange={(v) => set('analyst_effort', v)} options={EFFORTS} />
					</Field>
					<Field label="Budget per conversation (USD)" hint="Hard ceiling. Default 2.">
						<input type="number" step="0.5" min="0" className={inputCls}
							value={form.analyst_budget_usd ?? ''} onChange={(e) => set('analyst_budget_usd', e.target.value)} />
					</Field>
					<Field label="Max turns" hint="Default 40.">
						<input type="number" min="1" className={inputCls}
							value={form.analyst_max_turns ?? ''} onChange={(e) => set('analyst_max_turns', e.target.value)} />
					</Field>
				</div>
			</Card>

			{/* Build agent */}
			<Card
				title="Build agent"
				subtitle="Phase 2 — implements the approved specification into the app's workspace."
			>
				<div className="grid grid-cols-2 gap-[12px]">
					<Field label="Model" hint="Writes code; capability matters most here.">
						<Select value={form.default_model} onChange={(v) => set('default_model', v)} options={MODELS} />
					</Field>
					<Field label="Effort">
						<Select value={form.default_effort} onChange={(v) => set('default_effort', v)} options={EFFORTS} />
					</Field>
					<Field label="Budget per build (USD)" hint="Hard ceiling; the run stops when reached.">
						<input type="number" step="1" min="0" className={inputCls}
							value={form.max_budget_usd ?? ''} onChange={(e) => set('max_budget_usd', e.target.value)} />
					</Field>
					<Field label="Max turns" hint="Blank for no limit.">
						<input type="number" min="1" className={inputCls}
							value={form.max_turns ?? ''} onChange={(e) => set('max_turns', e.target.value)} />
					</Field>
					<Field label="Time limit (seconds)" hint="Default 1800.">
						<input type="number" min="60" className={inputCls}
							value={form.max_run_seconds ?? ''} onChange={(e) => set('max_run_seconds', e.target.value)} />
					</Field>
					<Field label="Monthly budget (USD)" hint="Advisory; not yet enforced.">
						<input type="number" step="10" min="0" className={inputCls}
							value={form.monthly_budget_usd ?? ''} onChange={(e) => set('monthly_budget_usd', e.target.value)} />
					</Field>
				</div>
			</Card>

			{/* Behaviour */}
			<Card title="Behaviour">
				<div className="flex flex-col gap-[12px]">
					<Toggle
						checked={form.is_enabled}
						onChange={(v) => set('is_enabled', v)}
						label="Enable Build with AI"
						hint="When off, the feature reports unavailable and no run can start."
					/>
					<Toggle
						checked={form.ensure_packages}
						onChange={(v) => set('ensure_packages', v)}
						label="Install required packages before each build"
						hint="appbuilder, crud and workflow. Without them the agent hand-rolls Django views."
					/>
					<Toggle
						checked={form.allow_frontend_build}
						onChange={(v) => set('allow_frontend_build', v)}
						label="Allow custom React builds"
						hint={
							env.node_available
								? 'Permits npm install / build. npm runs package scripts, i.e. code from the registry.'
								: 'Node is not installed on the server, so this has no effect until it is.'
						}
					/>
				</div>
			</Card>

			<div className="flex items-center justify-between rounded-[10px] border border-[#E3E6EF] bg-white px-[18px] py-[12px]">
				<span className="text-[11.5px] text-[#5A607A]">
					{data.source === 'platform_settings'
						? 'These settings override the environment.'
						: 'Currently using environment values. Saving stores them here instead.'}
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
