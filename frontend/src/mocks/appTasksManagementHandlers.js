import { faker } from '@faker-js/faker';
import { rest } from 'msw';

const range = (len) => {
	const arr = [];
	for (let i = 0; i < len; i++) {
		arr.push(i);
	}
	return arr;
};

const newPolicy = () => {
	return {
		id: faker.number.int({ min: 1, max: 10 }),
		schema_name: faker.internet.displayName(),
		created_at: faker.date.past(),
		created_by: faker.person.fullName(),
		modified_at: faker.date.past(),
		modified_by: faker.person.fullName(),
		uuid: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Policy ' + faker.number.int({ min: 1, max: 10 }),
		description: faker.lorem.sentences(2),
		tenant_type: 'policy',
		status: faker.helpers.shuffle(['staged', 'deployed']),
		deployed_on: null,
		suspended_on: null,
		deleted_on: null,
		timezone: null,
		language: null,
		date_format: null,
		datetime_format: null,
		logo: null,
		extra_config: null,
	};
};

const newTask = () => {
	return {
		id: faker.number.int({ min: 1000, max: 9999 }),
		name: 'Task ' + faker.number.int({ min: 1, max: 10 }),
		email: faker.internet.email().toLowerCase(),
		attached_policies: makePolices(faker.number.int({ min: 1, max: 10 })),
		schedule: '* * * * *',
		crontab: {
			minute: '1',
			hour: '2',
			day_of_week: '3',
			day_of_month: '4',
			month_of_year: '5',
		},
		is_superadmin: false,
		last_login: faker.date.past(),
		is_enabled: faker.datatype.boolean(),
		created_at: faker.date.past(),
		docstring: '\n    This is a docstring\n    ',
		code: '@shared_task()\ndef test():\n    """\n    This is a docstring\n    """\n    print("test")\n    return "test"\n',
	};
};

export function makePolices(...lens) {
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

export function makeData(...lens) {
	const makeDataLevel = (depth = 0) => {
		const len = lens[depth];
		return range(len).map((d) => {
			return {
				...newTask(),
				subRows: lens[depth + 1] ? makeDataLevel(depth + 1) : undefined,
			};
		});
	};

	return makeDataLevel();
}

let totalData = 1000;
const data = makeData(totalData);

export const appTasksManagementHandlers = [
	rest.get('/api/v1/apps/:appId/tasks/', (req, res, ctx) => {
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
					tasks: {
						total_records: totalData,
						total_pages: Math.ceil(data.length / pageSize),
						next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
						previous: null,
						records: searchValue ? [] : slicedData,
					},
					dropdown_options: {
						policies: [
							{ id: 1, label: 'Policy 1' },
							{ id: 2, label: 'Policy 2' },
							{ id: 3, label: 'Policy 3' },
							{ id: 4, label: 'Policy 4' },
						],
					},
					message: 'Success',
				},
			})
		);
	}),

	rest.get('/api/v1/apps/:appId/tasks/:taskId', (req, res, ctx) => {
		return res(
			ctx.delay(500),
			ctx.status(200),
			ctx.json({
				success: true,
				response: {
					task: {
						id: 2,
						attached_policies: [],
						crontab: {
							minute: '*',
							hour: '*',
							day_of_week: '*',
							day_of_month: '*',
							month_of_year: '*',
						},
						schedule: '* * * * *',
						docstring: '',
						code: '',
						run_history: [
							{
								date_started: '2024-08-12T07:30:00.043275Z',
								date_done: '2024-08-12T07:30:00.043294Z',
								result: '"Task completed successfully"',
								traceback: null,
							},
							{
								date_started: '2024-08-12T07:29:00.039694Z',
								date_done: '2024-08-12T07:29:00.039726Z',
								result: '"Data processed"',
								traceback:
									'Traceback(mostrecentalllast):Filetask.py,line4,inprocess_datadatafetch_dTraceback(mostrecent call last):\n  File "task.py", line 34, in process_data\n    data = fetch_dTraceback (most recent call last):\n  File "task.py", line 34, in process_data\n    data = fetch_dTraceback (most recent call last):\n  File "task.py", line 34, in process_data\n    data = fetch_dTraceback (most recent call last):\n  File "task.py", line 34, in process_data\n    data = fetch_dTraceback (most recent call last):Filetask.py", line 34, in process_data\n    data = fetch_dTraceback (most recent call last):\n  File "task.py", line 34, in process_data\n    data = fetch_dTraceback (most recent call last):\n  File "task.py", line 34, in process_data\n    data = fetch_data()\nKeyError: \'id\'',
							},
							{
								date_started: '2024-08-12T07:28:00.141579Z',
								date_done: '2024-08-12T07:28:00.141628Z',
								result: '"Export failed"',
								traceback:
									'TraceThisisaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocsspropertiesappliedtowraporbreakwordsappropriatelysuchtextcanoverfloworbreaklayoutsinunexpectedsituationsback (most recent call last):\n  File "task.py", line 22, in export_data\n    export_to_csv(data)\nFileNotFoundError: [Errno 2] No such file or directory: \'output.csv\'',
							},
							{
								date_started: '2024-08-12T07:27:00.141579Z',
								date_done: '2024-08-12T07:27:00.141628Z',
								result: '"Email sent"',
								traceback: null,
							},
							{
								date_started: '2024-08-12T07:26:00.141579Z',
								date_done: '2024-08-12T07:26:00.141628Z',
								result: '"Database update failed"',
								traceback:
									'TracThisisaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocsspropertiesappliedtowraporbreakwordsappropriatelysuchtextcanoverfloworbreaklayoutsinunexpectedsituationseback (most recent call last):\n  File "task.py", line 45, in update_database\n    cursor.execute(query)\npsycopg2.IntegrityError: duplicate key value violates unique constraint "users_pkey"',
							},
							{
								date_started: '2024-08-12T07:25:00.141579Z',
								date_done: '2024-08-12T07:25:00.141628Z',
								result: '"Backup completed with warnings"',
								traceback:
									'Traceback (most recent call last):\n  File "backup.py", line 10, in perform_backup\n    raise Warning(\'Low disk space\')\nWarning: Low disk space',
							},
							{
								date_started: '2024-08-12T07:24:00.141579Z',
								date_done: '2024-08-12T07:24:00.141628Z',
								result: '"Report generation failed"',
								traceback:
									'Traceback (most recent call last):\n  FiThisisaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocssproaplaceholderparagraphdesignedtoshowwhattextwithoutspaceslookslikewhenitisrenderedinawebpagewithnocsspropertiesappliedtowraporbreakwordsappropriatelysuchtextcanoverfloworbreaklayoutsinunexpectedsituationsle "report.py", line 59, in generate_report\n    report = create_report(data)\nValueError: Missing required field \'report_name\'',
							},
							{
								date_started: '2024-08-12T07:23:00.141579Z',
								date_done: '2024-08-12T07:23:00.141628Z',
								result: '"Task completed with warnings"',
								traceback:
									'Traceback (most recent call last):\n  File "task.py", line 78, in execute_task\n    validate_input(input_data)\nDeprecationWarning: \'validate_input\' is deprecated and will be removed in future versions',
							},
							{
								date_started: '2024-08-12T07:22:00.141579Z',
								date_done: '2024-08-12T07:22:00.141628Z',
								result: '"Task failed"',
								traceback:
									'Traceback (most recent call last):\n  File "task.py", line 11, in perform_task\n    run_process()\nTypeError: \'NoneType\' object is not callable',
							},
							{
								date_started: '2024-08-12T07:21:00.141579Z',
								date_done: '2024-08-12T07:21:00.141628Z',
								result: '"File upload failed"',
								traceback:
									'Traceback (most recent call last):\n  File "upload.py", line 27, in upload_file\n    response = requests.post(url, files=files)\nrequests.exceptions.ConnectionError: Failed to establish a new connection',
							},
						],

						created_at: '2024-08-12T07:22:14.716445Z',
						created_by: '',
						modified_at: '2024-08-12T07:30:21.674722Z',
						modified_by: '',
						name: 'accounts.tasks.test',
						is_enabled: false,
						is_deleted: true,
						args: '["CRMApp2", "accounts.tasks.test"]',
						kwargs: {},
						interval: null,
						master_task: 52,
					},
				},
			})
		);
	}),
	rest.post('/api/v1/apps/:appId/tasks/', (req, res, ctx) => {
		const action = req.url.searchParams.get('action');
		if (action === 'sync_tasks') {
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
		}

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

	rest.post('/api/v1/apps/:appId/tasks/:id', (req, res, ctx) => {
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
