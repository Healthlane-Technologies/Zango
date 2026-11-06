import { useMemo, useState } from 'react';
import type { AvailableProvider, ConfigField, ProviderModelInfo } from '@/api/ai';
import { cx, Icon, Input, ProviderLogo, serviceMeta } from '@/ui';
import './ai.css';

// Pieces shared by Platform → Settings → AI accounts and App → AI → Connect.

/** Config fields that go in `config` (default_model is chosen from the model list). */
export const credentialFields = (svc: AvailableProvider | undefined) =>
	(svc?.config_fields ?? []).filter((f) => f.options_from !== 'supported_models');

/** Typed values, then saved values (masked secrets are kept server-side), then defaults. */
export function buildConfig(
	svc: AvailableProvider | undefined,
	values: Record<string, string>,
	saved?: Record<string, unknown>,
) {
	const out: Record<string, unknown> = {};
	for (const f of credentialFields(svc)) {
		const typed = values[f.name]?.trim();
		const kept = saved?.[f.name];
		const v = typed || (kept != null && kept !== '' ? kept : f.default);
		if (v === undefined || v === '') continue;
		out[f.name] = f.type === 'integer' ? Number(v) : v;
	}
	return out;
}

export function missingFields(
	svc: AvailableProvider | undefined,
	values: Record<string, string>,
	saved?: Record<string, unknown>,
) {
	return credentialFields(svc).filter(
		(f) => f.required && !values[f.name]?.trim() && !(saved && saved[f.name]),
	);
}

/** Big logo tiles to choose an AI service. */
export function ServicePicker({
	services,
	value,
	onChange,
}: {
	services: AvailableProvider[];
	value: string;
	onChange: (slug: string) => void;
}) {
	return (
		<div className="zai-svc" role="radiogroup" aria-label="AI service">
			{services.map((s) => {
				const meta = serviceMeta(s.slug);
				const on = value === s.slug;
				return (
					<button
						key={s.slug}
						type="button"
						role="radio"
						aria-checked={on}
						className={cx('zai-svc-t', on && 'on')}
						onClick={() => onChange(s.slug)}
					>
						<ProviderLogo slug={s.slug} size={40} />
						<span className="min-w-0">
							<b>{meta.name || s.display_name}</b>
							<small>{meta.tagline}</small>
						</span>
						<span className="zai-radio" aria-hidden>
							{on && <Icon name="check" />}
						</span>
					</button>
				);
			})}
		</div>
	);
}

/** The service's credential fields. Secrets are masked inputs that never show a saved value. */
export function CredentialFields({
	svc,
	values,
	onChange,
	saved,
}: {
	svc: AvailableProvider;
	values: Record<string, string>;
	onChange: (name: string, value: string, field: ConfigField) => void;
	/** Masked saved config when editing: blank secrets keep the saved key. */
	saved?: Record<string, unknown>;
}) {
	const help = serviceMeta(svc.slug).keyHelp;
	return (
		<div className="zai-cred flex flex-col gap-3.5">
			{credentialFields(svc).map((f) => {
				const savedValue = saved?.[f.name];
				const secret = f.type === 'secret';
				return (
					<label key={f.name} className="field">
						<span>
							{f.label}
							{!f.required && <span className="font-normal text-t4"> · optional</span>}
						</span>
						<div className={cx(secret && 'zai-secret')}>
							{secret && <Icon name="lock" />}
							<Input
								type={secret ? 'password' : f.type === 'integer' ? 'number' : 'text'}
								autoComplete={secret ? 'new-password' : 'off'}
								spellCheck={false}
								className={cx(secret && 'mono')}
								placeholder={
									secret && savedValue
										? `Saved ${String(savedValue)} · type to replace`
										: f.default != null
											? String(f.default)
											: undefined
								}
								value={values[f.name] ?? ''}
								onChange={(e) => onChange(f.name, e.target.value, f)}
							/>
						</div>
						{f.help_text && <span className="hint">{f.help_text}</span>}
					</label>
				);
			})}
			{credentialFields(svc).length === 0 && (
				<p className="text-[12.5px] leading-[1.5] text-t2">
					Nothing to enter: this uses the server's own login. Only for local testing, so it is
					hidden everywhere else.
				</p>
			)}
			{credentialFields(svc).length > 0 && (
			<div className="zai-note">
				<Icon name="shield" />
				<span>
					Stored encrypted and never shown again. Apps use it without seeing it.
					{help && (
						<>
							{' '}
							Get one at{' '}
							<a href={help.href} target="_blank" rel="noreferrer">
								{help.label}
							</a>
							.
						</>
					)}
				</span>
			</div>
			)}
		</div>
	);
}

const k = (n?: number | null) =>
	!n ? null : n >= 1_000_000 ? `${+(n / 1_000_000).toFixed(1)}M` : `${Math.round(n / 1000)}K`;

/** The model to suggest as default: the service's recommended one, else its first listed. */
export function suggestedModel(svc: AvailableProvider | undefined, usable: ProviderModelInfo[]) {
	const known = (svc?.supported_models ?? []).filter((m) => usable.some((u) => u.id === m.id));
	return (known.find((m) => m.recommended) ?? known[0] ?? usable[0])?.id ?? '';
}

/** A service with nothing to type (it uses the server's own login). */
export const keyless = (svc: AvailableProvider | undefined) => !!svc && credentialFields(svc).length === 0;

/** Tick the models apps may use and star the default. */
export function ModelPicker({
	models,
	selected,
	onSelected,
	defaultModel,
	onDefault,
	single,
}: {
	models: ProviderModelInfo[];
	selected: string[];
	onSelected?: (ids: string[]) => void;
	defaultModel: string;
	onDefault: (id: string) => void;
	/** Choose one model only (no ticking). */
	single?: boolean;
}) {
	const [q, setQ] = useState('');
	const shown = useMemo(() => {
		const t = q.trim().toLowerCase();
		return t
			? models.filter((m) => m.id.toLowerCase().includes(t) || m.name?.toLowerCase().includes(t))
			: models;
	}, [models, q]);
	const toggle = (id: string) => {
		if (!onSelected) return;
		const on = selected.includes(id);
		if (on && selected.length === 1) return; // keep at least one
		const next = on ? selected.filter((x) => x !== id) : [...selected, id];
		onSelected(next);
		if (on && id === defaultModel) onDefault(next[0]);
	};
	return (
		<div className="flex flex-col gap-2">
			{models.length > 8 && (
				<Input placeholder="Filter models" value={q} onChange={(e) => setQ(e.target.value)} />
			)}
			<div className="zai-models">
				{shown.map((m) => {
					const on = single || selected.includes(m.id);
					const isDefault = m.id === defaultModel;
					return (
						<div key={m.id} className={cx('zai-model', on && 'on', isDefault && 'def')}>
							{!single && (
								<input
									type="checkbox"
									aria-label={`Allow ${m.name || m.id}`}
									checked={on}
									onChange={() => toggle(m.id)}
								/>
							)}
							<button
								type="button"
								className="zai-model-b"
								onClick={() => (single || on ? onDefault(m.id) : toggle(m.id))}
							>
								<span className="min-w-0">
									<b>{m.name && m.name !== m.id ? m.name : m.id}</b>
									<small className="mono">{m.id}</small>
								</span>
								<span className="zai-chips">
									{k(m.context_window) && <i>{k(m.context_window)} context</i>}
									{m.supports_vision && <i>Vision</i>}
									{m.supports_tools && <i>Tools</i>}
								</span>
							</button>
							<button
								type="button"
								className={cx('zai-star', isDefault && 'on')}
								aria-label={isDefault ? 'Default model' : `Make ${m.id} the default`}
								title={isDefault ? 'Default model' : 'Make default'}
								disabled={!on}
								onClick={() => onDefault(m.id)}
							>
								{isDefault ? 'Default' : 'Set default'}
							</button>
						</div>
					);
				})}
				{!shown.length && <div className="px-3 py-4 text-center text-t3">No models match.</div>}
			</div>
		</div>
	);
}

/** Numbered steps across the top of a wizard. */
export function Steps({ steps, at }: { steps: string[]; at: number }) {
	return (
		<ol className="zai-steps">
			{steps.map((s, i) => (
				<li key={s} className={cx(i < at && 'done', i === at && 'on')}>
					<span>{i < at ? <Icon name="check" /> : i + 1}</span>
					{s}
				</li>
			))}
		</ol>
	);
}
