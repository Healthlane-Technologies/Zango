import { Suspense, type ReactNode } from 'react';
import { useRequirementSpec, useTemplateBuilder, type Requirement } from '@/api/agentMode';
import { ErrorState, Skeleton } from '@/ui';
import { builderOverrides, type BuilderProps } from './registry';
import { TemplateBuilderPanel } from './TemplateBuilderPanel';

function Loading() {
	return (
		<div className="grid gap-3">
			<Skeleton width="45%" height={18} />
			<Skeleton height={48} />
			<Skeleton height={220} />
		</div>
	);
}

/**
 * The Requirements tab for a template requirement: loads the template version's builder
 * definition and the spec, then renders the template's own builder if it ships one, else
 * the generic schema-driven panel. `fallback` renders a spec the builder can't show
 * (a Markdown-format template).
 */
export function TemplateBuilderHost({
	appId,
	requirement,
	fallback,
	editable,
	onController,
	jump,
	commit,
	sheet,
}: {
	appId: string;
	requirement: Requirement;
	fallback: () => ReactNode;
	editable?: boolean;
	onController?: BuilderProps['onController'];
	jump?: BuilderProps['jump'];
	commit?: BuilderProps['commit'];
	sheet?: BuilderProps['sheet'];
}) {
	const template = requirement.template!;
	const builder = useTemplateBuilder(template.slug, template.version_uuid);
	const spec = useRequirementSpec(appId, requirement.uuid, {
		draft: requirement.draft_revision,
		version: requirement.spec_version,
		status: requirement.status,
	});

	const error = builder.error ?? spec.error;
	if (error) {
		return (
			<div className="card">
				<ErrorState
					error={error}
					onRetry={() => (builder.error ? builder.refetch() : spec.refetch())}
				/>
			</div>
		);
	}
	if (!builder.data || !spec.data) return <Loading />;
	if (builder.data.spec_format !== 'yaml' || spec.data.format !== 'yaml') return <>{fallback()}</>;

	const Override = builderOverrides[template.slug];
	const props = {
		appId,
		requirement,
		builder: builder.data,
		spec: spec.data,
		changed: spec.data.changed_paths ?? [],
		editable,
		onController,
		jump,
		commit,
		sheet,
	};
	if (Override) {
		return (
			<Suspense fallback={<Loading />}>
				<Override {...props} />
			</Suspense>
		);
	}
	return <TemplateBuilderPanel {...props} />;
}
