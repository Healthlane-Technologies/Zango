// A template's app, running: its preview page (App Studio, or the template's own builder in
// preview mode) loaded with the template's spec and demo data. Loaded lazily — the preview
// page is large, and the gallery and detail pages render without it.

import { useTemplateBuilder } from '@/api/agentMode';
import { useTemplate } from '@/api/templates';
import { Skeleton } from '@/ui';
import { EmbeddedBuilder } from '../../app/agent/builder/EmbeddedBuilder';

const noop = () => {};

export default function LivePreview({
	slug,
	versionUuid,
	yaml,
}: {
	slug: string;
	versionUuid: string;
	/** The spec to show; defaults to the template's example, else its starter. */
	yaml?: string;
}) {
	const builder = useTemplateBuilder(slug, versionUuid);
	const detail = useTemplate(yaml === undefined ? slug : undefined);
	const url = builder.data?.preview_url ?? builder.data?.builder_url ?? null;
	const text = yaml ?? (detail.data?.example_yaml || detail.data?.starter_yaml || '');

	if (builder.isLoading || (yaml === undefined && detail.isLoading)) {
		return (
			<div className="lpv-wait">
				<Skeleton width="30%" height={14} />
				<Skeleton height={180} />
			</div>
		);
	}
	if (!url || !text) {
		return <div className="lpv-none">No preview for this template.</div>;
	}
	return (
		<div className="lpv">
			<EmbeddedBuilder url={url} text={text} readOnly preview onChange={noop} />
		</div>
	);
}
