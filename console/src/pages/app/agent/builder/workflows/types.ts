// Workflows drawn as swimlanes. Two sources share this shape: lifecycles derived from the
// journey here in the console (`source: 'lifecycle'`), and user journeys the agent writes
// while drafting (`source: 'agent'`, on the spec payload as `workflows`).

export type {
	WfFlow,
	WfLane,
	WfNode,
	WfNodeKind,
	WfProcess,
	Workflows,
} from '@/api/agentMode';
