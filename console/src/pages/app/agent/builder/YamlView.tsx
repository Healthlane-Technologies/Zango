import { lazy, Suspense } from 'react';
import { Skeleton } from '@/ui';
import type { YamlEditorProps } from './YamlEditor';

const YamlEditor = lazy(() => import('./YamlEditor'));

/** The spec as YAML (editable when allowed). CodeMirror loads on first open of this tab. */
export function YamlView(props: YamlEditorProps) {
	return (
		<Suspense fallback={<Skeleton height={320} />}>
			<YamlEditor {...props} />
		</Suspense>
	);
}
