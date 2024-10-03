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
		id: faker.number.int(1000),
		schema_name: faker.internet.displayName(),
		created_at: faker.date.past(),
		created_by: faker.person.fullName(),
		modified_at: faker.date.past(),
		modified_by: faker.person.fullName(),
		uuid: faker.number.int({ min: 1000, max: 9999 }),
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

const newRole = () => {
	return {
		id: faker.number.int(1000),
		schema_name: faker.internet.displayName(),
		created_at: faker.date.past(),
		created_by: faker.person.fullName(),
		modified_at: faker.date.past(),
		modified_by: faker.person.fullName(),
		uuid: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Role ' + faker.number.int({ min: 1, max: 10 }),
		description: faker.lorem.sentences(2),
		tenant_type: 'role',
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

const newPolicy = () => {
	return {
		id: faker.number.int(1000),
		schema_name: faker.internet.displayName(),
		created_at: faker.date.past(),
		created_by: faker.person.fullName(),
		modified_at: faker.date.past(),
		modified_by: faker.person.fullName(),
		uuid: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Policy ' + faker.number.int({ min: 1, max: 10 }),
		description: faker.lorem.sentences(2),
		tenant_type: 'policy',
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
		mobile: faker.phone.number('##########'),
		email: faker.internet.email().toLowerCase(),
		roles: makeRoles(faker.number.int({ min: 1, max: 4 })),
		policies: makePolicies(faker.number.int({ min: 1, max: 5 })),
		is_superadmin: false,
		last_login: faker.date.past(),
		is_active: faker.datatype.boolean(),
		created_at: faker.date.past(),
		login_at: faker.date.past(),
		change_password_at: faker.date.past(),
	};
};

export function makeRoles(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newRole(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

export function makePolicies(...lens) {
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
				...newUser(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const appUsersManagementHandlers = [
	rest.get('/api/v1/apps/:appId/users/', (req, res, ctx) => {
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
					users: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: searchValue ? [] : slicedData,
					},
					pn_country_code:'+213',
					dropdown_options: {
						roles: [
							{
								id: 1,
								label: 'Role 1',
							},
							{
								id: 2,
								label: 'Role 2',
							},
							{
								id: 3,
								label: 'Role 3',
							},
							{
								id: 4,
								label: 'Role 4',
							},
						],
					},
					message: 'Success',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/users/', (req, res, ctx) => {
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

	rest.put('/api/v1/apps/:appId/users/:id', (req, res, ctx) => {
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
