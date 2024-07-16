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
		user: 'Test User',
		username: 'ravi_at_zelthy',
		ip_address: '127.0.0.1',
		attempt_type: 'login',
		attempt_time: '25 April 2024 01:16 PM',
		role: 'patient',
		user_agent: 'Apple Mac Chrome 149.0.1',
		session_expired_at: '25 April 2024 01:16 PM',
		is_login_successful: false,
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

export const appAccessLogsHandlers = [
	rest.get('/api/v1/apps/:appId/access-logs/', (req, res, ctx) => {
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
					access_logs: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: '.',
						previous: null,
						records: searchValue ? [] : slicedData,
					},
					dropdown_options: {
						attempt_type: [
							{
								id: 'login',
								label: 'Login',
							},
							{
								id: 'switch_role',
								label: 'Switched Role',
							},
						],
						role: [
							{
								id: '1',
								label: 'Patient',
							},
							{
								id: '2',
								label: 'Doctor',
							},
						],
						is_login_successful: [
							{
								id: 'successful',
								label: 'Successful',
							},
							{
								id: 'failed',
								label: 'Failed',
							},
						],
					},
					message: 'Access logs fetched successfully',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/access-logs/', (req, res, ctx) => {
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

	rest.put('/api/v1/apps/:appId/access-logs/:id', (req, res, ctx) => {
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
