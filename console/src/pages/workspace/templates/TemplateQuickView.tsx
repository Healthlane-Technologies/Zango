import { useNavigate } from 'react-router-dom';
import type { TemplateSummary } from '@/api/templates';
import { Button, Icon, Modal } from '@/ui';
import { formatUpdated } from './catalog';
import { BetaBadge, TemplateIcon } from './parts';

/** Quick look at a template from the gallery (prototype tplModalHTML). */
export function TemplateQuickView({
	template,
	onClose,
}: {
	template: TemplateSummary | null;
	onClose: () => void;
}) {
	const navigate = useNavigate();
	if (!template) return null;
	const c = template.catalogue;
	const agents = c.recommended_agents ?? [];
	const compliance = c.compliance ?? [];
	return (
		<Modal
			open
			large
			onOpenChange={(o) => !o && onClose()}
			title={
				<span className="flex items-center gap-3">
					<TemplateIcon template={template} size={40} />
					<span className="min-w-0">
						<span className="block">
							{template.name} {template.is_beta && <BetaBadge />}
						</span>
						<small className="block text-[12px] font-normal text-t3">
							{template.category}, <span className="mono">v{template.version}</span>, updated{' '}
							{formatUpdated(template.published_at)}
						</small>
					</span>
				</span>
			}
			footer={
				<>
					<Button onClick={() => navigate(`/templates/${template.slug}`)}>View full details</Button>
					<Button variant="primary" onClick={() => navigate(`/apps/new?template=${template.slug}`)}>
						Use template
					</Button>
				</>
			}
		>
			<div className="-m-5 grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] gap-7 p-5">
				<div>
					<p className="tp-d">{c.description || template.one_liner}</p>
					{!!c.workflows?.length && (
						<div className="tp-s">
							<h4>How it runs</h4>
							<ol className="tflow">
								{c.workflows.map((w) => (
									<li key={w.name}>
										{w.name}
										{w.description && <small>{w.description}</small>}
									</li>
								))}
							</ol>
						</div>
					)}
					{!!c.roles?.length && (
						<div className="tp-s">
							<h4>Who uses it</h4>
							<div className="pkgs">
								{c.roles.map((r) => (
									<span key={r.name} className="rchip" title={r.description}>
										{r.name}
									</span>
								))}
							</div>
						</div>
					)}
				</div>
				<div>
					{!!agents.length && (
						<div className="tp-s">
							<h4>AI agents included</h4>
							{agents.map((a) => (
								<div key={a.id ?? a.name} className="tp-ag">
									<Icon name="bot" />
									<span className="min-w-0 flex-1">
										<b>{a.name}</b>
										{(a.hitl || a.description) && <small>{a.hitl || a.description}</small>}
									</span>
								</div>
							))}
						</div>
					)}
					{!!compliance.length && (
						<div className="tp-s">
							<h4>Compliance built in</h4>
							<ul className="tp-c">
								{compliance.map((x) => (
									<li key={x}>
										<Icon name="check" weight={2.4} />
										{x}
									</li>
								))}
							</ul>
						</div>
					)}
					{!agents.length && !compliance.length && !!c.gives_you?.length && (
						<div className="tp-s">
							<h4>Already built</h4>
							<ul className="tp-c">
								{c.gives_you.map((x) => (
									<li key={x}>
										<Icon name="check" weight={2.4} />
										{x}
									</li>
								))}
							</ul>
						</div>
					)}
				</div>
			</div>
		</Modal>
	);
}
