import { faker } from '@faker-js/faker';
import { rest } from 'msw';

const range = (len) => {
	const arr = [];
	for (let i = 0; i < len; i++) {
		arr.push(i);
	}
	return arr;
};

const newPolicy = () => {
	return {
		id: faker.number.int({ min: 1, max: 10 }),
		schema_name: faker.internet.displayName(),
		created_at: faker.date.past(),
		created_by: faker.person.fullName(),
		modified_at: faker.date.past(),
		modified_by: faker.person.fullName(),
		uuid: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Policy ' + faker.number.int({ min: 1, max: 10 }),
		description: faker.lorem.sentences(2),
		tenant_type: 'policy',
		status: faker.helpers.shuffle(['staged', 'deployed']),
		deployed_on: null,
		suspended_on: null,
		deleted_on: null,
		timezone: null,
		language: null,
		date_format: null,
		datetime_format: null,
		logo: null,
		extra_config: null,
	};
};

const newTask = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Task ' + faker.number.int({ min: 1, max: 10 }),
		email: faker.internet.email().toLowerCase(),
		attached_policies: makePolices(faker.number.int({ min: 1, max: 10 })),
		schedule: '* * * * *',
		crontab: {
			minute: '1',
			hour: '2',
			day_of_week: '3',
			day_of_month: '4',
			month_of_year: '5',
		},
		is_superadmin: false,
		last_login: faker.date.past(),
		is_enabled: faker.datatype.boolean(),
		created_at: faker.date.past(),
	};
};

export function makePolices(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newPolicy(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

export function makeData(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newTask(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const appTasksManagementHandlers = [
	rest.get('/api/v1/apps/:appId/tasks/', (req, res, ctx) => {
		const pageIndex = parseInt(req.url.searchParams.get('page')) || 0;
		const pageSize = parseInt(req.url.searchParams.get('page_size')) || 10;
		const searchValue = req.url.searchParams.get('search') || '';
		let slicedData = data.slice(
			pageIndex * pageSize,
			(pageIndex + 1) * pageSize
		);

		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					tasks: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: searchValue ? [] : slicedData,
					},
					dropdown_options: {
						policies: [
							{ id: 1, label: 'Policy 1' },
							{ id: 2, label: 'Policy 2' },
							{ id: 3, label: 'Policy 3' },
							{ id: 4, label: 'Policy 4' },
						],
					},
					message: 'Platform user fetched successfully',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/tasks/', (req, res, ctx) => {
		const action = req.url.searchParams.get('action');
		if (action === 'sync_tasks') {
			return res(
				ctx.delay(1000),
				ctx.status(200),
				ctx.json({
					success: true,
					response: {
						message: 'Tasks synced successfully',
					},
				})
			);
		}

		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					message: 'Platform user fetched successfully',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/tasks/:id', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					message: 'Platform user fetched successfully',
				},
			})
		);
	}),
];
