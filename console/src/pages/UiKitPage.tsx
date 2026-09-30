import { useState } from 'react';
import {
	AppIcon,
	Avatar,
	Badge,
	Button,
	Card,
	CardBody,
	CardHeader,
	Drawer,
	EmptyState,
	Field,
	Input,
	Modal,
	Page,
	PageHeader,
	RowMenu,
	SearchInput,
	Segmented,
	Select,
	Skeleton,
	Table,
	Tabs,
	Textarea,
	Toolbar,
	toast,
	type Tone,
} from '@/ui';

const TONES: Tone[] = ['green', 'amber', 'violet', 'accent', 'gray', 'line', 'red'];
const ROWS = [
	{ id: 1, name: 'zango-workflow', version: '2.4.1' },
	{ id: 2, name: 'zango-crud', version: '1.9.0' },
];

/** Unlisted reference page (/console/_ui) showing every primitive. */
export function UiKitPage() {
	const [seg, setSeg] = useState<'a' | 'b' | 'c'>('a');
	const [tab, setTab] = useState<'one' | 'two'>('one');
	const [q, setQ] = useState('');
	const [drawer, setDrawer] = useState(false);
	const [modal, setModal] = useState(false);

	return (
		<Page>
			<PageHeader
				title="UI kit"
				description="Primitives from design/prototype.html."
				actions={
					<>
						<Button icon="plus" variant="primary">
							Primary
						</Button>
						<Button>Secondary</Button>
					</>
				}
			/>
			<div className="grid gap-4">
				<Card>
					<CardHeader title="Buttons" />
					<CardBody className="flex flex-wrap items-center gap-2">
						<Button variant="primary">Primary</Button>
						<Button>Secondary</Button>
						<Button variant="ghost">Ghost</Button>
						<Button variant="danger">Danger</Button>
						<Button size="sm" icon="ext">
							Small
						</Button>
						<Button size="xs">Extra small</Button>
						<Button loading>Saving</Button>
						<Button disabled>Disabled</Button>
					</CardBody>
				</Card>
				<Card>
					<CardHeader title="Badges, avatars" />
					<CardBody className="flex flex-wrap items-center gap-2">
						{TONES.map((t) => (
							<Badge key={t} tone={t} dot>
								{t}
							</Badge>
						))}
						<Badge tone="amber" busy>
							Building
						</Badge>
						<Avatar name="Anshuman C" />
						<Avatar name="Ravi M" small />
						<AppIcon name="Oncology PAP" />
						<AppIcon name="Vaccine Ordering" size={40} />
					</CardBody>
				</Card>
				<Card>
					<Tabs
						value={tab}
						onChange={setTab}
						items={[
							{ value: 'one', label: 'Users', count: 12 },
							{ value: 'two', label: 'Roles', count: 3 },
						]}
					/>
					<CardBody>
						<Toolbar>
							<SearchInput value={q} onChange={setQ} placeholder="Search" />
							<Segmented
								label="Demo"
								value={seg}
								onChange={setSeg}
								options={[
									{ value: 'a', label: 'All' },
									{ value: 'b', label: 'Live' },
									{ value: 'c', label: 'In progress' },
								]}
							/>
						</Toolbar>
						<div className="grid max-w-md gap-3">
							<Field label="App name" hint="You can change this later.">
								{(p) => <Input {...p} defaultValue="Oncology PAP" />}
							</Field>
							<Field label="Region" error="Pick a region">
								{(p) => (
									<Select {...p}>
										<option>India (Mumbai)</option>
									</Select>
								)}
							</Field>
							<Field label="Description">{(p) => <Textarea {...p} rows={3} />}</Field>
						</div>
					</CardBody>
				</Card>
				<Table
					columns={[
						{
							key: 'name',
							header: 'Package',
							cell: (r) => <span className="mono text-t1">{r.name}</span>,
						},
						{ key: 'v', header: 'Version', cell: (r) => r.version },
						{
							key: 'a',
							header: '',
							align: 'right',
							cell: () => (
								<RowMenu
									items={[
										{ label: 'Configure', icon: 'cog', onSelect: () => toast.success('Configure') },
										null,
										{
											label: 'Uninstall',
											icon: 'x',
											danger: true,
											onSelect: () => toast.error('Uninstall failed'),
										},
									]}
								/>
							),
						},
					]}
					rows={ROWS}
					rowKey={(r) => r.id}
					footer={<span>2 packages</span>}
				/>
				<Table
					columns={[{ key: 'x', header: 'Loading', cell: () => null }]}
					rows={undefined}
					rowKey={() => 0}
					loading
				/>
				<Card>
					<EmptyState title="No deployments yet" action={<Button size="sm">Open agent</Button>}>
						The first build appears here.
					</EmptyState>
				</Card>
				<Card>
					<CardHeader title="Overlays" />
					<CardBody className="flex flex-wrap gap-2">
						<Button onClick={() => setDrawer(true)}>Open drawer</Button>
						<Button onClick={() => setModal(true)}>Open modal</Button>
						<Button onClick={() => toast.success('Saved')}>Success toast</Button>
						<Button onClick={() => toast.error('Could not save')}>Error toast</Button>
						<Skeleton width={120} />
					</CardBody>
				</Card>
			</div>
			<Drawer
				open={drawer}
				onOpenChange={setDrawer}
				title="Invite user"
				subtitle="They get an email with a sign-in link."
				footer={
					<>
						<Button onClick={() => setDrawer(false)}>Cancel</Button>
						<Button variant="primary">Invite</Button>
					</>
				}
			>
				<Field label="Email">{(p) => <Input {...p} type="email" />}</Field>
			</Drawer>
			<Modal
				open={modal}
				onOpenChange={setModal}
				title="Delete app"
				subtitle="This removes the tenant and its data."
				footer={
					<>
						<Button onClick={() => setModal(false)}>Cancel</Button>
						<Button variant="danger">Delete</Button>
					</>
				}
			>
				Type the app name to confirm.
			</Modal>
		</Page>
	);
}
