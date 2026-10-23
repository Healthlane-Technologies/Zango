// The app's preview on its own browser tab, at full width: opened from the preview pane's "Open in
// new tab". It follows the requirement live (each agent edit redraws it), opens where the user was
// (the pane's place, in the URL hash) and is read-only. "Point" in it reaches the chat on the
// Agent page through a BroadcastChannel, so the user can point here and write there.

import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import {
	requirementQuery,
	THINKING_POLL_MS,
	useRequirementSpec,
	useTemplateBuilder,
	type PreviewFocus,
	type RequirementStatus,
} from '@/api/agentMode';
import { Badge, ErrorState, Icon, Skeleton } from '@/ui';
import { EmbeddedBuilder } from './builder/EmbeddedBuilder';
import { PrototypeFrame } from './builder/PrototypeFrame';
import { PREVIEW_CHANNEL } from './previewChannel';
import './builder/builder.css';

// Nobody else tells this tab that the chat sent a message: poll while the requirement is open.
const OPEN_POLL_MS = 4000;

function placeFromHash(): PreviewFocus | null {
	try {
		const raw = decodeURIComponent(window.location.hash.slice(1));
		const place = raw ? (JSON.parse(raw) as PreviewFocus) : null;
		return place && typeof place === 'object' ? place : null;
	} catch {
		return null;
	}
}

const statusLabel: Partial<Record<RequirementStatus, string>> = {
	gathering: 'Live draft',
	ready: 'Ready for review',
	approved: 'Approved version',
	abandoned: 'Abandoned',
};

export function PreviewTabPage() {
	const { appId = '', reqId = '' } = useParams();
	const requirement = useQuery({
		...requirementQuery(appId, reqId),
		refetchInterval: (q) => {
			const r = q.state.data;
			if (!r) return false;
			if (r.is_thinking) return THINKING_POLL_MS;
			return r.status === 'gathering' || r.status === 'ready' ? OPEN_POLL_MS : false;
		},
	});
	const r = requirement.data;
	const builder = useTemplateBuilder(r?.template?.slug, r?.template?.version_uuid);
	const spec = useRequirementSpec(appId, r?.template ? reqId : undefined, {
		draft: r?.draft_revision,
		version: r?.spec_version,
		status: r?.status,
	});
	const goto = useMemo(placeFromHash, []);
	const [sent, setSent] = useState<string | null>(null);
	const channel = useRef<BroadcastChannel | null>(null);
	useEffect(() => {
		if (typeof BroadcastChannel === 'undefined') return;
		channel.current = new BroadcastChannel(PREVIEW_CHANNEL);
		return () => channel.current?.close();
	}, []);
	useEffect(() => {
		document.title = r ? `Preview · ${r.title || 'App'}` : 'Preview';
	}, [r]);

	const onFocus = (focus: PreviewFocus) => {
		if (!focus.pointed) return;
		channel.current?.postMessage({ reqId, focus });
		setSent(focus.pointed.label || 'that part');
	};

	const previewUrl = builder.data?.preview_url ?? builder.data?.builder_url ?? null;
	const error = requirement.error ?? builder.error ?? spec.error;
	const open = r?.status === 'gathering' || r?.status === 'ready';

	return (
		<div className="pvtab">
			<header className="pvtab-h">
				<Icon name="eye" size={14} />
				<b className="min-w-0 truncate">{r?.title || 'Preview'}</b>
				{r && (
					<Badge tone={open ? 'accent' : 'green'} dot busy={r.is_thinking}>
						{r.is_thinking ? 'The agent is changing it…' : (statusLabel[r.status] ?? r.status)}
					</Badge>
				)}
				{spec.data && (
					<span className="mono text-[11.5px] text-t4" title="Spec revision">
						rev {spec.data.draft_revision}
					</span>
				)}
				<span className="ml-auto text-[12px] text-t3">
					{sent ? (
						<>
							Pointed at <b>{sent}</b>. Write what should change in the chat.
						</>
					) : open ? (
						'Read-only. Use Point to show the agent what you mean, then write in the chat.'
					) : (
						'Read-only.'
					)}
				</span>
			</header>
			<main className="pvtab-b">
				{error ? (
					<div className="card m-6">
						<ErrorState error={error as Error} onRetry={() => requirement.refetch()} />
					</div>
				) : r && !r.template ? (
					<div className="card m-6 p-6 text-t3">This requirement has no preview.</div>
				) : r?.preview_mode === 'open' ? (
					<PrototypeFrame
						appId={appId}
						reqId={reqId}
						revision={r.prototype_revision}
						goto={goto?.page ? { screen: goto.page } : null}
						className="pvtab-emb"
					/>
				) : previewUrl && spec.data ? (
					<EmbeddedBuilder
						url={previewUrl}
						text={spec.data.text}
						readOnly
						onChange={() => undefined}
						preview
						onFocus={open ? onFocus : undefined}
						goto={goto}
						className="pvtab-emb"
					/>
				) : (
					<div className="grid gap-3 p-6">
						<Skeleton width="30%" height={18} />
						<Skeleton height={480} />
					</div>
				)}
			</main>
		</div>
	);
}
