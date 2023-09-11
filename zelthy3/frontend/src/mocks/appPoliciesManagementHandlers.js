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

const newPolicy = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Policy Name ' + faker.number.int({ min: 1, max: 10 }),
		description: 'Policy Description ' + faker.number.int({ min: 1, max: 10 }),
		is_superadmin: false,
		configuration: faker.date.past(),
		statement: {
			permissions: [
				{
					name: 'patient',
					type: 'dataModel',
					actions: ['view', 'edit'],
					records: {
						filter: 'object.clinic == currentUser.clinic',
					},
					accessTime: '9:00-17:00',
					attributes: {
						only: ['Field 1', 'Field 2'],
					},
				},
			],
			configurations: {
				expiry: '26/12/23',
			},
		},
	};
};

export function makeData(...lens) {
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

let totalData = 1000;
const data = makeData(totalData);

export const appPoliciesManagementHandlers = [
	rest.get('/api/v1/apps/:appId/policies/', (req, res, ctx) => {
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
					policies: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: slicedData,
					},
					dropdown_options: {
						apps: [],
					},
					message: 'Platform user fetched successfully',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/policies/', (req, res, ctx) => {
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

	rest.put('/api/v1/apps/:appId/policies/:id', (req, res, ctx) => {
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
