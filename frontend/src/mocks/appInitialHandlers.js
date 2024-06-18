import { faker } from '@faker-js/faker';
import { rest } from 'msw';

export const appInitialHandlers = [
	rest.get('/api/v1/auth/app-initalization-details/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					app_data: {
						user_logged_in: {
							name: faker.person.fullName(),
							email: faker.internet.email(),
							apps: [],
							is_superadmin: true,
							last_login: null,
							created_at: '2023-10-16T06:47:37.847652Z',
						},
						is_codeassist_enabled: true,
					},
				},
			})
		);
	}),
];
