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
	const year = faker.number.int({ min: 2022, max: 2025 });
	const mins = faker.number.int({ min: 1, max: 59 });

	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		key: faker.helpers.arrayElement([
			'GITHUB_TOKEN',
			'GOOGLE_CLIENT_ID',
			'DATABASE_URL',
			'AWS_ACCESS_KEY_ID',
			'AWS_SECRET_ACCESS_KEY',
		]),
		description: faker.lorem.paragraph(),
		is_active: faker.datatype.boolean(),
		created_at: `${faker.number.int({
			min: 1,
			max: 14,
		})} April ${year} 01:${mins} PM`,
		modified_at: `${faker.number.int({
			min: 1,
			max: 14,
		})} April ${year + 1} 01:${mins} PM`,
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

export const appSecretsHandlers = [
	rest.get('/api/v1/apps/:appId/secrets/', (req, res, ctx) => {
		const secretId = req.url.searchParams.get('secret_id');
		const action = req.url.searchParams.get('action');

		if (action === 'get_secret_value' && secretId) {
			return res(
				ctx.delay(500),
				ctx.status(200),
				ctx.json({
					success: true,
					response: {
						secret_value: `mock_secret_value_${secretId}`,
						message: 'Secret value fetched successfully',
					},
				})
			);
		}

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
					secrets: {
						total_records: 3,
						total_pages: 1,
						next: null,
						previous: null,
						records: [
							{
								id: 3,
								key: 'Key3',
								active: true,
								created_at: '25 Apr 2025 09:45 AM',
								modified_at: '25 Apr 2025 10:13 AM',
							},
							{
								id: 2,
								key: 'Key1',
								active: false,
								created_at: '24 Apr 2025 07:48 PM',
								modified_at: '24 Apr 2025 07:48 PM',
							},
							{
								id: 1,
								key: 'Something',
								active: false,
								created_at: '24 Apr 2025 07:38 PM',
								modified_at: '24 Apr 2025 07:43 PM',
							},
						],
					},
					message: 'All secrets fetched successfully',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/secrets/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(400),
			ctx.json({
				success: false,
				response: {
					message:
						'No Space, First Character Caps, No Special Character except _',
				},
			})
		);
	}),

	rest.put('/api/v1/apps/:appId/secrets/:id', (req, res, ctx) => {
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
