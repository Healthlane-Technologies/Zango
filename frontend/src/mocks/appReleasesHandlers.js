import { faker } from '@faker-js/faker';
import { rest } from 'msw';

const range = (len) => {
	const arr = [];
	for (let i = 0; i < len; i++) {
		arr.push(i);
	}
	return arr;
};

const eachData = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		version: '1.0.0',
		description: 'description',
		status: 'released',
		last_git_hash: 'n238jekwdmoos',
		created_at: '2024-08-15T18:54:10.413014Z',
	};
};

export function makeData(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...eachData(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const appReleasesHandlers = [
	rest.get('/api/v1/apps/:appId/releases/', (req, res, ctx) => {
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
					releases: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: '.',
						previous: null,
						records: searchValue ? [] : slicedData,
					},
					dropdown_options: {
						version: [
							{
								id: '1.0.0',
								label: '1.0.0',
							},
							{
								id: '1.1.0',
								label: '1.1.0',
							},
						],
						status: [
							{
								id: 'released',
								label: 'Released',
							},
							{
								id: 'failed',
								label: 'Failed',
							},
						],
					},
					message: 'Releases fetched successfully',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/releases/', (req, res, ctx) => {
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

	rest.put('/api/v1/apps/:appId/releases/:id', (req, res, ctx) => {
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
