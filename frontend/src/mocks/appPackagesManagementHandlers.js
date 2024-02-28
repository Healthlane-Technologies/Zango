import { faker } from '@faker-js/faker';
import { rest } from 'msw';

const range = (len) => {
	const arr = [];
	for (let i = 0; i < len; i++) {
		arr.push(i);
	}
	return arr;
};

const newPackage = () => {
	return {
		name: 'Package ' + faker.number.int({ min: 1, max: 10 }),
		versions: ['0.1.0', '0.2.0'],
		status: faker.helpers.shuffle(['Installed', 'Not Installed'])[0],
		installed_version: faker.number.int({ min: 1, max: 10 }),
	};
};

export function makeData(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newPackage(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const appPackagesManagementHandlers = [
	rest.get('/api/v1/apps/:appId/packages/', (req, res, ctx) => {
		const pageIndex = parseInt(req.url.searchParams.get('page')) || 0;
		const pageSize = parseInt(req.url.searchParams.get('page_size')) || 10;
		const action = req.url.searchParams.get('action');

		let slicedData = data.slice(
			pageIndex * pageSize,
			(pageIndex + 1) * pageSize
		);

		if (action === 'config_url') {
			return res(
				ctx.delay(500),
				ctx.status(200),
				ctx.json({
					success: true,
					response: {
						url: 'app0.zelthy.com/communication/configure',
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
					packages: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: slicedData,
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

	rest.post('/api/v1/apps/:appId/packages/', (req, res, ctx) => {
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

	rest.post('/api/v1/apps/:appId/packages/sync/', (req, res, ctx) => {
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
	}),

	rest.put('/api/v1/apps/:appId/packages/:id', (req, res, ctx) => {
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
