import { rest } from 'msw';

export const appChatbotHandlers = [
	rest.post('/api/v1/apps/:appId/code-assist/execute/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					message: 'Succesfully executed',
				},
			})
		);
	}),
	rest.post('/api/v1/apps/:appId/code-assist/conversation/', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					conversation_id: '123233',
					assist_message: [
						{
							content: 'response_msg',
							content_meta: {
								type: 'text',
							},
						},
						{
							content: 'response_msg',
							content_meta: {
								type: 'code',
								code_language: 'python',
							},
						},
						{
							content: 'https://google.com',
							content_meta: {
								type: 'url',
							},
						},
					],
					allow_execution: true,
					execution_data: {
						conversation_id: '123233',
						execution: 'mapPolicy',
						role_name: 'Test',
						policy: 'Test Policy',
					},
				},
			})
		);
	}),
];