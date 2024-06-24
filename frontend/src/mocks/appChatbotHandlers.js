import { rest } from 'msw';
let status = 'waiting';
let mockHistoryData = [
	{
		UserID: '2',
		conversation_id: '03e144c3-8639-455b-89e8-e4e0ba74e0ed',
		LastActionTimestamp: 1697692477,
		Status: 'closed',
		AppUUID: '2332323',
		Messages: [
			{
				knowledge_base: 'models',
				content_meta: {
					type: 'text',
				},
				role: 'user',
				content:
					'MOCK DATA 1 Can you help me create Customer model inside customer module? you can use general fields',
				timestamp: 1697692205,
			},
			{
				content_meta: {
					type: 'text',
				},
				role: 'assistant',
				content:
					"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br>",
				timestamp: 1697692216,
			},
			{
				content_meta: {
					type: 'code',
					code_language: 'python',
				},
				role: 'assistant',
				content:
					'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Customer(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    email = models.EmailField()\n    phone_number = models.CharField(max_length=15, blank=True, null=True)\n    address = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
				timestamp: 1697692216,
			},
			{
				knowledge_base: 'models',
				content_meta: {
					type: 'text',
				},
				role: 'user',
				content:
					'Can you help me create Teacher model inside teacher module? you can use general fields',
				timestamp: 1697692467,
			},
			{
				content_meta: {
					type: 'text',
				},
				role: 'assistant',
				content:
					"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br>",
				timestamp: 1697692477,
			},
			{
				content_meta: {
					type: 'code',
					code_language: 'python',
				},
				role: 'assistant',
				content:
					'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Teacher(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    email = models.EmailField()\n    phone_number = models.CharField(max_length=15, blank=True, null=True)\n    subject = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
				timestamp: 1697692477,
			},
		],
	},
	{
		UserID: '2',
		conversation_id: '03e144c3-8639-554a-89e8-e4e0ba74e0ed',
		LastActionTimestamp: 1697692477,
		Status: 'open',
		AppUUID: '2332323',
		Messages: [
			{
				knowledge_base: 'models',
				content_meta: {
					type: 'text',
				},
				role: 'user',
				content:
					'MOCK DATA 2 Can you help me create Customer model inside customer module? you can use general fields 1',
				timestamp: 1697692205,
			},
			{
				content_meta: {
					type: 'text',
				},
				role: 'assistant',
				content:
					"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is 1 <br>",
				timestamp: 1697692216,
			},
			{
				content_meta: {
					type: 'code',
					code_language: 'python',
				},
				role: 'assistant',
				content:
					'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Customer(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    email = models.EmailField()\n    phone_number = models.CharField(max_length=15, blank=True, null=True)\n    address = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
				timestamp: 1697692216,
			},
			{
				content_meta: {
					type: 'url',
					code_language: 'python',
				},
				role: 'assistant',
				content: 'https://www.youtube.com/watch?v=3OX0Uqi8d_U',
				timestamp: 1697692216,
			},
			{
				knowledge_base: 'models',
				content_meta: {
					type: 'text',
				},
				role: 'user',
				content:
					'Can you help me create Teacher model inside teacher module? you can use general fields',
				timestamp: 1697692467,
			},
			{
				content_meta: {
					type: 'text',
				},
				role: 'assistant',
				content:
					"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br>",
				timestamp: 1697692477,
			},
			{
				content_meta: {
					type: 'code',
					code_language: 'python',
				},
				role: 'assistant',
				content:
					'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Teacher(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    email = models.EmailField()\n    phone_number = models.CharField(max_length=15, blank=True, null=True)\n    subject = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
				timestamp: 1697692477,
			},
		],
	},
];

export const appChatbotHandlers = [
	rest.post('/api/v1/apps/:appId/code-assist/execute/', (req, res, ctx) => {
		return res(
			ctx.delay(5000),
			ctx.status(200),
			ctx.json({
				success: false,
				response: {
					message: 'Failed to executed',
				},
			})
		);
	}),

	rest.post(
		'/api/v1/apps/:appId/code-assist/conversation/',
		async (req, res, ctx) => {
			const postData = await JSON.parse(req.body['data']);
			if (postData['action'] === 'get_conversations') {
				return res(
					ctx.delay(5000),
					ctx.status(200),
					ctx.json({
						success: true,
						response: { conversations: mockHistoryData },
					})
				);
			} else if (postData['action'] === 'restart_conversation') {
				let conversationId = postData['conversation_id'];
				return res(
					ctx.delay(500),
					ctx.status(500),
					ctx.json({
						success: false,
						response: {
							conversation_id: conversationId,
							message: 'Conversation Restarted Successfully',
						},
					})
				);
			} else if (postData['action'] === 'update_conversation') {
				status = 'waiting';
				setTimeout(() => {
					status = 'completed';
				}, 5000);
				return res(
					ctx.delay(500),
					ctx.status(500),
					ctx.json({
						success: false,
						response: {
							message: 'Conversation updated successfully',
							conversation_id: '95dde125-27ad-4588-b9ff-a5dd35a93a76',
							Messages: [
								{
									role: 'user',
									content:
										'Can you help me create Customer model inside customer module? you can include common contact fields like name, mobile, address',
									content_meta: {
										type: 'text',
									},
									knowledge_base: 'models',
									timestamp: 1697716659,
								},
								{
									content:
										"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br>",
									content_meta: {
										type: 'text',
									},
									timestamp: 1697716670,
									role: 'assistant',
								},
								{
									content:
										'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Customer(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    mobile = models.CharField(max_length=15, blank=True, null=True)\n    address = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
									content_meta: {
										type: 'code',
										code_language: 'python',
									},
									timestamp: 1697716670,
									role: 'assistant',
									allow_execution: true,
									exection_data: {
										execution: 'createModel',
										module: 'customer',
										'models.py':
											'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Customer(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    mobile = models.CharField(max_length=15, blank=True, null=True)\n    address = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
									},
								},
							],
						},
					})
				);
			} else if (postData['action'] === 'create_conversation') {
				status = 'waiting';
				setTimeout(() => {
					status = 'completed';
				}, 10000);
				return res(
					ctx.delay(5000),
					ctx.status(200),
					ctx.json({
						success: true,
						response: {
							message: 'Conversation created successfully',
							conversation_id: 'fcf37de1-8e57-4159-8ce0-8e3b9ae0db62',
						},
					})
				);
			} else if (postData['action'] === 'get_conversation_message') {
				return res(
					ctx.delay(500),
					ctx.status(200),
					ctx.json({
						success: true,

						response: {
							message: 'Conversation created successfully',
							conversation_id: '03e144c3-8639-554a-89e8-e4e0ba74e0ed',
							status: status,
							Messages: [
								{
									role: 'user',
									content:
										'Can you help me create Customer model inside customer module? you can include common contact fields like name, mobile, address',
									content_meta: {
										type: 'text',
									},
									knowledge_base: 'models',
									timestamp: 1697716659,
								},
								{
									content:
										"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br>",
									content_meta: {
										type: 'text',
									},
									timestamp: 1697988683,
									role: 'assistant',
								},
								{
									content:
										'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Teacher(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    mobile = models.CharField(max_length=15, blank=True, null=True)\n    address = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
									content_meta: {
										type: 'code',
										code_language: 'python',
									},
									timestamp: 1697988683,
									role: 'assistant',
								},
							],
							allow_execution: true,
							execution_data: {
								execution: 'createModel',
								module: 'customer',
								'models.py':
									'from django.db import models\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\n\n\nclass Customer(DynamicModelBase):\n    name = models.CharField(max_length=255)\n    mobile = models.CharField(max_length=15, blank=True, null=True)\n    address = models.CharField(max_length=255, blank=True, null=True)\n\n    def __str__(self):\n        return self.name',
							},
						},
					})
				);
			}
		}
	),
];
