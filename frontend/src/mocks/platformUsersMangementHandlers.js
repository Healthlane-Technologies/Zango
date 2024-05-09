import { faker } from '@faker-js/faker';
import { rest } from 'msw';

const range = (len) => {
	const arr = [];
	for (let i = 0; i < len; i++) {
		arr.push(i);
	}
	return arr;
};

const newApp = () => {
	return {
		id: faker.number.int({ min: 1, max: 10 }),
		schema_name: faker.internet.displayName(),
		created_at: faker.date.past(),
		created_by: faker.person.fullName(),
		modified_at: faker.date.past(),
		modified_by: faker.person.fullName(),
		uuid: faker.number.int({ min: 1, max: 10 }),
		name: 'App ' + faker.number.int({ min: 1, max: 10 }),
		description: faker.lorem.sentences(2),
		tenant_type: 'app',
		is_active: faker.datatype.boolean(),
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

const newUser = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		name: faker.person.fullName(),
		email: faker.internet.email().toLowerCase(),
		apps: makeApps(faker.number.int({ min: 1, max: 10 })),
		is_superadmin: false,
		last_login: faker.date.past(),
		is_active: faker.datatype.boolean(),
		created_at: faker.date.past(),
	};
};

export function makeApps(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newApp(),
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
				...newUser(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const platformUsersMangementHandlers = [
	rest.get('/api/v1/auth/platform-users/', (req, res, ctx) => {
		const pageIndex = parseInt(req.url.searchParams.get('page')) || 0;
		const pageSize = parseInt(req.url.searchParams.get('page_size')) || 10;
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
					platform_users: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: slicedData,
					},
					dropdown_options: {
						apps: [
							{
								id: 1,
								label: 'Apps 1',
							},
							{
								id: 2,
								label: 'Apps 2',
							},
							{
								id: 3,
								label: 'Apps 3',
							},
							{
								id: 4,
								label: 'Apps 4',
							},
							{
								id: 5,
								label: 'Apps 5',
							},
							{
								id: 6,
								label: 'Apps 6',
							},
						],
					},
					message: 'Success',
				},
			})
		);
	}),

	rest.post('/api/v1/auth/platform-users/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					message: 'Success',
				},
			})
		);
	}),

	rest.put('/api/v1/auth/platform-users/:id', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					message: 'Success',
				},
			})
		);
	}),
];
