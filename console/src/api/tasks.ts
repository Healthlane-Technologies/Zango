import { useQuery } from '@tanstack/react-query';
import { api } from './client';
import { appKeys } from './apps';
import { fetchAllPages, MAX_PAGE_SIZE, type Paginated } from './policies';

export interface Crontab {
	minute: string;
	hour: string;
	day_of_week: string;
	day_of_month: string;
	month_of_year: string;
}

export interface TaskRun {
	status: string;
	date_started: string;
	date_done: string;
	result: string | null;
	traceback: string | null;
	worker: string | null;
}

// TaskSerializer (api/platform/tasks/v1/serializers.py).
export interface AppTask {
	id: number;
	/** Dotted path, e.g. "patient.tasks.profile_incomplete_trigger". */
	name: string;
	is_enabled: boolean;
	crontab: Crontab | null;
	/** Cron string, e.g. "0 9 * * *"; empty when unscheduled. */
	schedule: string;
	/** Source of the task function; empty if the module couldn't be loaded. */
	code: string;
	kwargs: Record<string, unknown> | null;
	attached_policies: Array<{ id: number; name: string }>;
	/** Only filled by the detail endpoint. */
	run_history: TaskRun[];
	/** Preformatted in the app's timezone. Not ISO. */
	modified_at: string;
}

export const taskKeys = {
	all: (appId: string) => [...appKeys.detail(appId), 'tasks'] as const,
	detail: (appId: string, id: number) => [...taskKeys.all(appId), id] as const,
};

export function useTasks(appId: string) {
	return useQuery({
		queryKey: taskKeys.all(appId),
		queryFn: () =>
			fetchAllPages<AppTask, { tasks: Paginated<AppTask> }>(
				(page) => `/api/v1/apps/${appId}/tasks/?page=${page}&page_size=${MAX_PAGE_SIZE}`,
				(r) => r.tasks,
			).then((r) => r.records),
	});
}

/** Detail endpoint; the only one that includes run history. */
export function useTask(appId: string, id: number | undefined) {
	return useQuery({
		queryKey: taskKeys.detail(appId, id ?? 0),
		queryFn: () => api<{ task: AppTask }>(`/api/v1/apps/${appId}/tasks/${id}/`).then((r) => r.task),
		enabled: id != null,
	});
}

export interface TaskUpdate {
	is_enabled: boolean;
	crontab: Crontab;
	kwargs: Record<string, unknown>;
}

/**
 * Update a task's schedule, enabled flag and kwargs (POST, not PUT). `crontab_exp` and
 * `kwargs` are JSON strings. Attaching policies isn't supported by this endpoint.
 */
export function updateTask(appId: string, id: number, values: TaskUpdate) {
	const fd = new FormData();
	fd.append('crontab_exp', JSON.stringify(values.crontab));
	fd.append('is_enabled', String(values.is_enabled));
	fd.append('kwargs', JSON.stringify(values.kwargs));
	return api<{ message: string }>(`/api/v1/apps/${appId}/tasks/${id}/`, 'POST', fd);
}

/** Re-read tasks declared in the app's code. */
export function syncTasks(appId: string) {
	return api<{ message: string }>(
		`/api/v1/apps/${appId}/tasks/?action=sync_tasks`,
		'POST',
		new FormData(),
	);
}
