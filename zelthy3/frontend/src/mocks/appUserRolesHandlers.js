import { rest } from 'msw';
import moment from 'moment';
import { faker } from '@faker-js/faker';

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

const newUser = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		created_at: faker.date.past(),
		created_by: '',
		modified_at: faker.date.past(),
		modified_by: '',
		name: faker.person.fullName(),
		config: null,
		is_active: faker.datatype.boolean(),
		is_default: faker.datatype.boolean(),
		policies: [],
		policy_groups: [],
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

export const appUserRolesHandlers = [
	rest.get(
		'/api/v1/apps/02248bb4-e120-48fa-bb64-a1c6ee032cb5/roles/',
		(req, res, ctx) => {
			const pageIndex = parseInt(req.url.searchParams.get('pageIndex')) || 0;
			const pageSize = parseInt(req.url.searchParams.get('pageSize')) || 10;
			let slicedData = data.slice(
				pageIndex * pageSize,
				(pageIndex + 1) * pageSize
			);

			console.log(
				'slicedData',
				typeof pageIndex,
				typeof pageSize,
				pageIndex,
				pageSize,
				slicedData
			);
			return res(
				ctx.delay(500),
				ctx.status(200),
				ctx.json({
					success: true,
					response: {
						roles: {
							total_records: totalData,
							total_pages: Math.ceil(data.length / pageSize),
							next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
							previous: null,
							records: slicedData,
						},
						include_dropdown_options: {
							apps: [],
						},
						message: 'Platform user fetched successfully',
					},
				})
			);
		}
	),
];
