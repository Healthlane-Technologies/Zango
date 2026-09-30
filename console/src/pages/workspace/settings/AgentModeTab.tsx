import { useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import {
	agentModeSettingsKey,
	saveAgentModeSettings,
	useAgentModeSettings,
	validateAgentModeKey,
	type AgentModeForm,
	type AgentModeSettings,
} from '@/api/agentModeSettings';

import { useApiMutation } from '@/api/hooks';

import { formatDateTime } from '@/format/time';

import {
	Badge,
	Button,
	Card,
	CardBody,
	CardHeader,
	ErrorState,
	Field,
	Input,
	SaveBar,
	Select,
	SwitchField,
	toast,
} from '@/ui';

import { SettingsSkeleton } from './GeneralTab';

// Same choices as the classic panel's Build with AI tab.
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

const str = (v: unknown) => (v === null || v === undefined ? '' : String(v));

function toForm(d: AgentModeSettings): AgentModeForm {
	const s = d.settings;
	const r = d.resolved;
	if (s) {
		return {
			is_enabled: !!s.is_enabled,
			ensure_packages: !!s.ensure_packages,
			allow_frontend_build: !!s.allow_frontend_build,
			default_model: str(s.default_model),
			default_effort: str(s.default_effort),
			max_run_seconds: str(s.max_run_seconds),
			max_budget_usd: str(s.max_budget_usd),
			max_turns: str(s.max_turns),
			analyst_model: str(s.analyst_model),
			analyst_effort: str(s.analyst_effort),
			analyst_budget_usd: str(s.analyst_budget_usd),
			analyst_max_turns: str(s.analyst_max_turns),
			monthly_budget_usd: str(s.monthly_budget_usd),
		};
	}
	// No stored row yet: start from what the environment resolves to.
	return {
		is_enabled: r.enabled,
		ensure_packages: r.ensure_packages ?? true,
		allow_frontend_build: r.allow_frontend_build ?? false,
		default_model: str(r.model),
		default_effort: str(r.effort),
		max_run_seconds: str(r.max_run_seconds ?? 1800),
		max_budget_usd: str(r.max_budget_usd),
		max_turns: str(r.max_turns),
		analyst_model: str(r.analyst_model),
		analyst_effort: str(r.analyst_effort),
		analyst_budget_usd: str(r.analyst_budget_usd),
		analyst_max_turns: str(r.analyst_max_turns),
		monthly_budget_usd: '',
	};
}

function Options({ options }: { options: Array<{ value: string; label: string }> }) {
	return (
		<>
			{options.map((o) => (
				<option key={o.value} value={o.value}>
					{o.label}
				</option>
			))}
		</>
	);
}

function AgentModeSettingsForm({ data }: { data: AgentModeSettings }) {
	const [form, setForm] = useState(() => toForm(data));
	const [apiKey, setApiKey] = useState('');
	const [dirty, setDirty] = useState(false);
	const [testing, setTesting] = useState(false);
	const qc = useQueryClient();
	const set = <K extends keyof AgentModeForm>(key: K, value: AgentModeForm[K]) => {
		setForm((f) => ({ ...f, [key]: value }));
		setDirty(true);
	};
	const num = (key: keyof AgentModeForm) => ({
		value: form[key] as string,
		onChange: (e: React.ChangeEvent<HTMLInputElement>) => set(key, e.target.value),
		type: 'number',
		inputMode: 'decimal' as const,
	});

	const save = useApiMutation({
		fn: () => saveAgentModeSettings(apiKey.trim() ? { ...form, api_key: apiKey.trim() } : form),
		invalidate: [agentModeSettingsKey],
		success: 'Saved. Applies to the next run; runs in progress keep their settings.',
	});

	const test = async () => {
		setTesting(true);
		try {
			const r = await validateAgentModeKey();
			if (r.valid) toast.success(r.message);
			else toast.error(r.message || 'Key check failed');
		} catch (e) {
			toast.error((e as Error).message);
		} finally {
			setTesting(false);
			// A successful check stamps is_validated on the server.
			qc.invalidateQueries({ queryKey: agentModeSettingsKey });
		}
	};

	const env = data.environment;
	const keyKnown = data.has_api_key || env.env_api_key_present;
	const keyState = data.has_api_key ? (
		<Badge tone="green" dot>
			Configured
		</Badge>
	) : env.env_api_key_present ? (
		<Badge tone="accent" dot>
			From environment
		</Badge>
	) : (
		<Badge tone="red" dot>
			Not set
		</Badge>
	);

	return (
		<div className="grid gap-4">
			<Card>
				<CardHeader title="Anthropic API key" actions={keyState} />
				<CardBody className="grid gap-4">
					<p className="-mt-1 text-t3">
						Used by both agents. Stored encrypted and never shown again once saved. A new key
						applies to the next run, not one already in progress.
					</p>
					<Field
						label={data.has_api_key ? 'Replace key' : 'API key'}
						hint={
							data.has_api_key
								? `Saved key: ${data.masked_config.api_key || 'set'}. Leave blank to keep it.`
								: env.env_api_key_present
									? 'A key from the environment is in use. Saving one here overrides it.'
									: 'Starts with sk-ant-'
						}
					>
						{(p) => (
							<Input
								{...p}
								type="password"
								className="mono max-w-[420px]"
								autoComplete="new-password"
								placeholder="sk-ant-…"
								value={apiKey}
								onChange={(e) => {
									setApiKey(e.target.value);
									setDirty(true);
								}}
							/>
						)}
					</Field>
					<div className="flex items-center gap-3">
						<Button
							size="sm"
							icon="check"
							onClick={test}
							loading={testing}
							disabled={!keyKnown || dirty}
						>
							Test key
						</Button>
						{dirty && keyKnown && (
							<span className="text-[12px] text-t3">Save first to test the new settings.</span>
						)}
						{!dirty && data.is_validated && (
							<span className="text-[12px] text-green-t">
								Verified
								{data.last_validated_at ? ` · ${formatDateTime(data.last_validated_at)}` : ''}
							</span>
						)}
					</div>
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Requirements agent" />
				<CardBody>
					<p className="-mt-1 mb-4 text-t3">
						Interviews the user and writes the specification. Read-only, short turns.
					</p>
					<div className="grid gap-4 sm:grid-cols-2">
						<Field label="Model" hint="Falls back to the build agent's model.">
							{(p) => (
								<Select
									{...p}
									value={form.analyst_model}
									onChange={(e) => set('analyst_model', e.target.value)}
								>
									<Options options={MODELS} />
								</Select>
							)}
						</Field>
						<Field label="Effort">
							{(p) => (
								<Select
									{...p}
									value={form.analyst_effort}
									onChange={(e) => set('analyst_effort', e.target.value)}
								>
									<Options options={EFFORTS} />
								</Select>
							)}
						</Field>
						<Field label="Budget per conversation (USD)" hint="Hard ceiling. Default 2.">
							{(p) => <Input {...p} {...num('analyst_budget_usd')} step="0.5" min="0" />}
						</Field>
						<Field label="Max turns" hint="Default 40.">
							{(p) => <Input {...p} {...num('analyst_max_turns')} min="1" />}
						</Field>
					</div>
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Build agent" />
				<CardBody>
					<p className="-mt-1 mb-4 text-t3">
						Implements the approved specification in the app's workspace.
					</p>
					<div className="grid gap-4 sm:grid-cols-2">
						<Field label="Model" hint="Writes code, so capability matters most here.">
							{(p) => (
								<Select
									{...p}
									value={form.default_model}
									onChange={(e) => set('default_model', e.target.value)}
								>
									<Options options={MODELS} />
								</Select>
							)}
						</Field>
						<Field label="Effort">
							{(p) => (
								<Select
									{...p}
									value={form.default_effort}
									onChange={(e) => set('default_effort', e.target.value)}
								>
									<Options options={EFFORTS} />
								</Select>
							)}
						</Field>
						<Field
							label="Budget per build (USD)"
							hint="Hard ceiling; the run stops when it's reached."
						>
							{(p) => <Input {...p} {...num('max_budget_usd')} step="1" min="0" />}
						</Field>
						<Field label="Max turns" hint="Blank for no limit.">
							{(p) => <Input {...p} {...num('max_turns')} min="1" />}
						</Field>
						<Field label="Time limit (seconds)" hint="Default 1800.">
							{(p) => <Input {...p} {...num('max_run_seconds')} min="60" />}
						</Field>
						<Field label="Monthly budget (USD)" hint="Advisory; not enforced yet.">
							{(p) => <Input {...p} {...num('monthly_budget_usd')} step="10" min="0" />}
						</Field>
					</div>
				</CardBody>
			</Card>

			<Card>
				<CardHeader title="Behaviour" />
				<CardBody className="grid gap-4">
					<SwitchField
						checked={form.is_enabled}
						onChange={(v) => set('is_enabled', v)}
						label="Enable Build with AI"
						hint="When off, the feature reports unavailable and no run can start."
					/>
					<SwitchField
						checked={form.ensure_packages}
						onChange={(v) => set('ensure_packages', v)}
						label="Install required packages before each build"
						hint="appbuilder, crud and workflow. Without them the agent hand-writes Django views."
					/>
					<SwitchField
						checked={form.allow_frontend_build}
						onChange={(v) => set('allow_frontend_build', v)}
						label="Allow custom React builds"
						hint={
							env.node_available
								? 'Permits npm install and build. npm runs package scripts, which is code from the registry.'
								: "Node isn't installed on the server, so this has no effect until it is."
						}
					/>
				</CardBody>
			</Card>

			<SaveBar
				note={
					data.source === 'platform_settings'
						? 'These settings override the environment.'
						: 'Using environment values. Saving stores them here instead.'
				}
				dirty={dirty}
				saving={save.isPending}
				onSave={() => save.mutate()}
			/>
		</div>
	);
}

export function AgentModeTab() {
	const { data, isLoading, error, refetch } = useAgentModeSettings();
	if (isLoading) return <SettingsSkeleton />;
	if (error || !data)
		return (
			<div className="card">
				<ErrorState error={error ?? new Error('No settings returned')} onRetry={() => refetch()} />
			</div>
		);
	// Keyed on the stored row so a save (which returns fresh values) resets the form.
	return (
		<AgentModeSettingsForm
			key={`${data.last_validated_at}-${JSON.stringify(data.settings)}`}
			data={data}
		/>
	);
}
