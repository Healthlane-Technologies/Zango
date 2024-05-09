import { faker } from '@faker-js/faker';
import { rest } from 'msw';

const range = (len) => {
	const arr = [];
	for (let i = 0; i < len; i++) {
		arr.push(i);
	}
	return arr;
};

const newPermission = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Permission Name ' + faker.number.int({ min: 1, max: 10 }),
		description:
			'Permission Description ' + faker.number.int({ min: 1, max: 10 }),
		type: faker.helpers.shuffle([
			'DataModel',
			'UserAccess',
			'View',
			'Custom',
		])[0],
		is_superadmin: false,
		last_login: faker.date.past(),
		status: faker.helpers.shuffle(['active', 'inactive'])[0],
		created_at: faker.date.past(),
	};
};

export function makeData(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newPermission(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const appPermissionsManagementHandlers = [
	rest.get('/api/v1/apps/:appId/permissions/', (req, res, ctx) => {
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
					permissions: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: slicedData,
					},
					dropdown_options: {
						apps: [],
					},
					message: 'Success',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/permissions/', (req, res, ctx) => {
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

	rest.put('/api/v1/apps/:appId/permissions/:id', (req, res, ctx) => {
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
