import { EmptyState, Icon, Page, PageHeader } from '@/ui';

/** Stand-in for a screen that hasn't been built yet. Links to the same screen in the classic panel. */
export function Placeholder({
	title,
	description,
	classicHref,
}: {
	title: string;
	description?: string;
	classicHref?: string;
}) {
	return (
		<Page>
			<PageHeader title={title} description={description} />
			<div className="card">
				<EmptyState
					title="Not built yet"
					action={
						classicHref && (
							<a className="btn btn-s btn-sm" href={classicHref}>
								<Icon name="ext" />
								Open in classic view
							</a>
						)
					}
				>
					This screen is coming to the new console.
				</EmptyState>
			</div>
		</Page>
	);
}
