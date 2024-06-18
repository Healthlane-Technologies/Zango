import { rest } from 'msw';

export const appThemeConfigurationHandlers = [
	rest.get('/api/v1/apps/:appId/themes/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					themes: [
						{
							id: 2,
							created_at: '2023-09-08T12:10:59.572025Z',
							created_by: '',
							modified_at: '2023-09-08T12:10:59.572047Z',
							modified_by: '',
							name: 'Test Theme2',
							config: {
								color: {
									primary: '#5048ED',
									secondary: '#ffffff',
									background: '#ffffff',
								},
								typography: {
									font_family: 'Advent Pro',
								},
								button: {
									border_radius: 4,
									color: '#ffffff',
									border_color: '#C7CED3',
									background: '#5048ED',
								},
							},
							is_active: true,
							tenant: 20,
						},
						{
							id: 3,
							created_at: '2023-09-08T12:10:59.572025Z',
							created_by: '',
							modified_at: '2023-09-08T12:10:59.572047Z',
							modified_by: '',
							name: 'Test Theme2',
							config: {
								color: {
									primary: '#FF8085',
									secondary: '#ffffff',
									background: '#ffffff',
								},
								typography: {
									font_family: 'Alegreya Sans SC',
								},
								button: {
									border_radius: 4,
									color: '#ffffff',
									border_color: '#C7CED3',
									background: '#FF8085',
								},
							},
							is_active: false,
							tenant: 20,
						},
					],
					dropdown_options: {},
					message: 'Success',
				},
			})
		);
	}),

	rest.post('/api/v1/apps/:appId/themes/', (req, res, ctx) => {
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

	rest.put('/api/v1/apps/:appId/themes/:id', (req, res, ctx) => {
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
