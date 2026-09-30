import { useSearchParams } from 'react-router-dom';
import { useAppId } from '@/api/hooks';
import type { AuditModelType } from '@/api/logs';
import { Page, PageHeader, Segmented } from '@/ui';
import { AccessLogs } from './logs/AccessLogs';
import { AuditLogs } from './logs/AuditLogs';

type Source = 'audit' | 'data' | 'framework' | 'access';

// Audit sources map to the auditlog endpoint's `model_type`; "All changes" omits it, so the
// server merges and paginates both groups. Access logs are a separate endpoint with other columns.
const AUDIT_MODEL: Record<Exclude<Source, 'access'>, AuditModelType> = {
	audit: undefined,
	data: 'dynamic_models',
	framework: 'core_models',
};

const SOURCES: Array<{ value: Source; label: string }> = [
	{ value: 'audit', label: 'All changes' },
	{ value: 'data', label: 'App data' },
	{ value: 'framework', label: 'Framework' },
	{ value: 'access', label: 'Sign-ins' },
];

const isSource = (s: string | null): s is Source => SOURCES.some((o) => o.value === s);

export function LogsPage() {
	const appId = useAppId();
	const [params, setParams] = useSearchParams();
	const raw = params.get('source');
	const source: Source = isSource(raw) ? raw : 'audit';

	return (
		<Page wide>
			<PageHeader
				title="Logs"
				description="Audit trail of every change to app and framework records, and sign-in attempts. Audit entries are immutable."
				actions={
					<a className="btn btn-s" href={`/platform/apps/${appId}/logs#runtime`}>
						Runtime logs
					</a>
				}
			/>
			<div className="mb-3">
				<Segmented
					label="Log source"
					value={source}
					onChange={(v) => setParams(v === 'audit' ? {} : { source: v }, { replace: true })}
					options={SOURCES}
				/>
			</div>
			{source === 'access' ? (
				<AccessLogs key={`${appId}-access`} appId={appId} />
			) : (
				<AuditLogs key={`${appId}-${source}`} appId={appId} modelType={AUDIT_MODEL[source]} />
			)}
		</Page>
	);
}
