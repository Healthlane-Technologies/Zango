import {
	Suspense,
	lazy,
	useEffect,
	useRef,
	useState,
	type CSSProperties,
	type ReactNode,
} from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import type { TemplateSummary } from '@/api/templates';
import { Badge, Icon, cx } from '@/ui';
import { categoryStyle, highlight, templateIcon } from './catalog';
import './templates.css';
import './gallery.css';

/** The coloured category tile (prototype `vic`). */
export function TemplateIcon({
	template,
	size = 32,
}: {
	template: Pick<TemplateSummary, 'icon' | 'category'>;
	size?: number;
}) {
	const { bg, fg } = categoryStyle(template.category);
	return (
		<span
			className="vic"
			style={{ background: bg, color: fg, width: size, height: size, borderRadius: size / 4 }}
		>
			<Icon name={templateIcon(template)} size={Math.round(size / 2)} />
		</span>
	);
}

export function BetaBadge() {
	return (
		<Badge tone="violet" className="tb">
			Beta
		</Badge>
	);
}

/** `text` with the search words wrapped in <mark>. */
export function Highlighted({ text, q }: { text: string; q: string }) {
	return (
		<>
			{highlight(text, q).map(([part, hit], i) =>
				hit ? <mark key={i}>{part}</mark> : <span key={i}>{part}</span>,
			)}
		</>
	);
}

export function AgentsTag({ count }: { count: number }) {
	if (!count) return null;
	return (
		<span className="tag-ai" title={`${count} AI agent${count > 1 ? 's' : ''} recommended`}>
			<Icon name="bot" size={13} />
			{count}
		</span>
	);
}

// ---- gallery cards (mockup gcard / gfeat) ----------------------------------------------------

const LivePreview = lazy(() => import('./LivePreview'));

/** The tinted header of a card: the template's tile and its first workflows as a flow. */
export function CardVisual({ template }: { template: TemplateSummary }) {
	const { bg, fg } = categoryStyle(template.category);
	const steps = (template.catalogue.workflows ?? []).map((w) => w.name);
	return (
		<div className="gvis" style={{ '--vb': bg, '--vf': fg } as CSSProperties}>
			<span className="gv-ic">
				<Icon name={templateIcon(template)} size={17} />
			</span>
			<div className="gv-flow">
				{steps.slice(0, 3).map((s) => (
					<span key={s} className="gv-n">
						<i />
						{s}
					</span>
				))}
				{steps.length > 3 && <span className="gv-more">+{steps.length - 3}</span>}
			</div>
		</div>
	);
}

function AppsUsing({ n }: { n: number }) {
	return <span>{n ? `${n} ${n === 1 ? 'app' : 'apps'}` : 'New'}</span>;
}

export function TemplateCard({
	template: t,
	q = '',
	onOpen,
}: {
	template: TemplateSummary;
	q?: string;
	onOpen: () => void;
}) {
	return (
		<button type="button" className="gcard" onClick={onOpen}>
			<CardVisual template={t} />
			<div className="gc-b">
				<b>
					<Highlighted text={t.name} q={q} />
					{t.is_beta && <BetaBadge />}
				</b>
				<p>{t.one_liner || t.catalogue.description}</p>
				<div className="gc-f">
					<AgentsTag count={t.catalogue.recommended_agents?.length ?? 0} />
					<AppsUsing n={t.apps_using} />
					<span className="mono ml-auto">v{t.version}</span>
				</div>
			</div>
		</button>
	);
}

/** Mounts its children once the element scrolls near the viewport. */
function WhenVisible({ children, className }: { children: ReactNode; className?: string }) {
	const ref = useRef<HTMLDivElement>(null);
	const [seen, setSeen] = useState(false);
	useEffect(() => {
		const el = ref.current;
		if (!el || seen) return;
		const io = new IntersectionObserver(
			(entries) => entries.some((e) => e.isIntersecting) && setSeen(true),
			{ rootMargin: '200px' },
		);
		io.observe(el);
		return () => io.disconnect();
	}, [seen]);
	return (
		<div ref={ref} className={className}>
			{seen ? children : null}
		</div>
	);
}

/** A scaled-down, non-interactive view of the template's running preview. */
export function PreviewThumb({
	template,
	yaml,
	className,
}: {
	template: Pick<TemplateSummary, 'slug' | 'version_uuid'>;
	yaml?: string;
	className?: string;
}) {
	return (
		<WhenVisible className={cx('mini-thumb', className)}>
			<div className="scale">
				<Suspense fallback={null}>
					<LivePreview slug={template.slug} versionUuid={template.version_uuid} yaml={yaml} />
				</Suspense>
			</div>
		</WhenVisible>
	);
}

/** The template's running preview at full size and interactive, mounted when scrolled to. */
export function LiveFrame({
	template,
	yaml,
	className,
}: {
	template: Pick<TemplateSummary, 'slug' | 'version_uuid'>;
	yaml?: string;
	className?: string;
}) {
	return (
		<WhenVisible className={cx('lframe', className)}>
			<Suspense fallback={null}>
				<LivePreview slug={template.slug} versionUuid={template.version_uuid} yaml={yaml} />
			</Suspense>
		</WhenVisible>
	);
}

export function FeaturedCard({ template: t, onOpen }: { template: TemplateSummary; onOpen: () => void }) {
	return (
		<button type="button" className="gfeat" onClick={onOpen}>
			<div className="gf-shot">
				<PreviewThumb template={t} />
			</div>
			<div className="gc-b">
				<div className="gf-h">
					<TemplateIcon template={t} size={32} />
					<div className="min-w-0">
						<b>{t.name}</b>
						<small>{t.category}</small>
					</div>
				</div>
				<p>{t.one_liner || t.catalogue.description}</p>
				<div className="gc-f">
					<AgentsTag count={t.catalogue.recommended_agents?.length ?? 0} />
					<span className="ml-auto">
						<AppsUsing n={t.apps_using} />
					</span>
				</div>
			</div>
		</button>
	);
}

/** The template's app, full size and interactive: switch roles, click through, try it. */
export function PreviewDialog({
	template,
	yaml,
	open,
	onOpenChange,
}: {
	template: Pick<TemplateSummary, 'slug' | 'version_uuid' | 'name' | 'icon' | 'category'>;
	yaml?: string;
	open: boolean;
	onOpenChange: (open: boolean) => void;
}) {
	return (
		<Dialog.Root open={open} onOpenChange={onOpenChange}>
			<Dialog.Portal>
				<Dialog.Overlay className="scrim" />
				<Dialog.Content className="pvdlg" aria-describedby={undefined}>
					<div className="pvdlg-h">
						<TemplateIcon template={template} size={28} />
						<Dialog.Title asChild>
							<h3>{template.name}</h3>
						</Dialog.Title>
						<span className="pvdlg-k">Live preview with demo data</span>
						<Dialog.Close className="ib ml-auto" aria-label="Close">
							<Icon name="x" />
						</Dialog.Close>
					</div>
					<div className="pvdlg-b">
						<Suspense fallback={null}>
							<LivePreview slug={template.slug} versionUuid={template.version_uuid} yaml={yaml} />
						</Suspense>
					</div>
				</Dialog.Content>
			</Dialog.Portal>
		</Dialog.Root>
	);
}
