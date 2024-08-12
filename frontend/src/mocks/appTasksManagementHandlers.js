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
				"success":true,
				"response":{
				   "tasks":{
					  "total_records":2,
					  "total_pages":1,
					  "next":null,
					  "previous":null,
					  "records":[
						 {
							"id":2,
							"attached_policies":[
							   
							],
							"crontab":{
							   "minute":"*",
							   "hour":"*",
							   "day_of_week":"*",
							   "day_of_month":"*",
							   "month_of_year":"*"
							},
							"schedule":"* * * * *",
							"docstring":"\n    This is a docstring\n    ",
							"code":"@shared_task()\ndef test():\n    \"\"\"\n    This is a docstring\n    \"\"\"\n    print(\"test\")\n    return \"test\"\n",
							"run_history":[
							   
							],
							"created_at":"2024-08-12T07:22:14.716445Z",
							"created_by":"",
							"modified_at":"2024-08-12T07:45:32.839697Z",
							"modified_by":"",
							"name":"accounts.tasks.test",
							"is_enabled":true,
							"is_deleted":false,
							"args":"[\"CRMApp2\", \"accounts.tasks.test\"]",
							"kwargs":{
							   
							},
							"interval":null,
							"master_task":52
						 },
						 {
							"id":1,
							"attached_policies":[
							   
							],
							"crontab":{
							   "minute":"*",
							   "hour":"*",
							   "day_of_week":"*",
							   "day_of_month":"*",
							   "month_of_year":"*"
							},
							"schedule":"* * * * *",
							"docstring":null,
							"code":"@shared_task\ndef export_table(request_data, export_job_id):\n    import io\n    import xlsxwriter\n\n    from django.http import HttpRequest\n    from django.db import connection\n\n    from zango.apps.dynamic_models.workspace.base import Workspace\n    from zango.apps.appauth.models import AppUserModel, UserRoleModel\n\n    from ....packages.frame.downloads.models import ExportJob\n\n    request = HttpRequest()\n    request.path = request_data[\"path\"]\n    request.tenant = connection.tenant\n    request.method = \"GET\"\n    request.GET = request_data[\"params\"]\n    request.user = (\n        AppUserModel.objects.get(id=request_data.get(\"user_id\"))\n        if request_data.get(\"user_id\")\n        else None\n    )\n\n    ws = Workspace(request.tenant, as_systemuser=True)\n    ws.ready()\n    view, resolve = ws.match_view(request)\n\n    if not view:\n        return\n\n    view_class = view.view_class\n\n    view_instancte = view_class()\n    view_instancte.request = request\n\n    # table_class = view_class.table\n    table_obj = view_instancte.get_table_obj()\n    table_obj.user_role = UserRoleModel.objects.get(id=request_data.get(\"user_role_id\"))\n\n    data = get_table_data(request, table_obj)\n    table_metadata = table_obj.get_table_metadata()\n\n    col_dict = {}\n    for col in table_metadata[\"columns\"]:\n        col_dict[col[\"name\"]] = col.get(\"display_name\", col[\"name\"])\n\n    output = io.BytesIO()\n    workbook = xlsxwriter.Workbook(output)\n    worksheet = workbook.add_worksheet()\n    header = col_dict.values()\n    for col_num, value in enumerate(header):\n        worksheet.write(0, col_num, value)\n\n    row = 1\n    for d in data:\n        for column_num, col in enumerate(col_dict.keys()):\n            val = d[col]\n            row_val = clean_row_value(val)\n            worksheet.write(row, column_num, row_val)\n            column_num += 1\n        row += 1\n\n    workbook.close()\n    output.seek(0)\n\n    export_job_obj = ExportJob.objects.get(id=export_job_id)\n    export_job_obj.file.save(\"export.xlsx\", output)\n    export_job_obj.status = \"completed\"\n    export_job_obj.save()\n",
							"run_history":[
							   
							],
							"created_at":"2024-08-02T04:18:58.988607Z",
							"created_by":"",
							"modified_at":"2024-08-02T04:18:59.030134Z",
							"modified_by":"",
							"name":"packages.crud.downloads.tasks.export_table",
							"is_enabled":false,
							"is_deleted":false,
							"args":"[\"CRMApp2\", \"packages.crud.downloads.tasks.export_table\"]",
							"kwargs":{
							   
							},
							"interval":null,
							"master_task":46
						 }
					  ]
				   },
				   "message":"All app tasks fetched successfully"
				}
			 })

			// ctx.json({
			// 	success: true,
			// 	response: {
			// 		tasks: {
			// 			total_records: totalData,
			// 			total_pages: Math.ceil(data.length / pageSize),
			// 			next: 'http://localhost:8000/api/v1/auth/platform-users/?page=2',
			// 			previous: null,
			// 			records: searchValue ? [] : slicedData,
			// 		},
			// 		dropdown_options: {
			// 			policies: [
			// 				{ id: 1, label: 'Policy 1' },
			// 				{ id: 2, label: 'Policy 2' },
			// 				{ id: 3, label: 'Policy 3' },
			// 				{ id: 4, label: 'Policy 4' },
			// 			],
			// 		},
			// 		message: 'Success',
			// 	},
			// })
			 
		);
	}),


	// export const appTasksHistoryManagementHandlers = [
		rest.get('/api/v1/apps/:appId/tasks/:taskId', (req, res, ctx) => {
			// const pageIndex = parseInt(req.url.searchParams.get('page')) || 0;
			// const pageSize = parseInt(req.url.searchParams.get('page_size')) || 10;
			// // const searchValue = req.url.searchParams.get('search') || '';
			// let slicedData = data.slice(
			// 	pageIndex * pageSize,
			// 	(pageIndex + 1) * pageSize
			// );
	
			return res(
				ctx.delay(500),
				ctx.status(200),
				ctx.json({
					"success": true,
					"response": {
					  "task": {
						"id": 2,
						"attached_policies": [],
						"crontab": {
						  "minute": "*",
						  "hour": "*",
						  "day_of_week": "*",
						  "day_of_month": "*",
						  "month_of_year": "*"
						},
						"schedule": "* * * * *",
						"docstring": "",
						"code": "",
						"run_history": [
							{
							  "date_created": "2024-08-12T07:30:00.043275Z",
							  "date_done": "2024-08-12T07:30:00.043294Z",
							  "result": "\"Task completed successfully\"",
							  "traceback": null
							},
							{
							  "date_created": "2024-08-12T07:29:00.039694Z",
							  "date_done": "2024-08-12T07:29:00.039726Z",
							  "result": "\"Data processed\"",
							  "traceback": "Traceback (most recent call last):\n  File \"task.py\", line 34, in process_data\n    data = fetch_data()\nKeyError: 'id'"
							},
							{
							  "date_created": "2024-08-12T07:28:00.141579Z",
							  "date_done": "2024-08-12T07:28:00.141628Z",
							  "result": "\"Export failed\"",
							  "traceback": "Traceback (most recent call last):\n  File \"task.py\", line 22, in export_data\n    export_to_csv(data)\nFileNotFoundError: [Errno 2] No such file or directory: 'output.csv'"
							},
							{
							  "date_created": "2024-08-12T07:27:00.141579Z",
							  "date_done": "2024-08-12T07:27:00.141628Z",
							  "result": "\"Email sent\"",
							  "traceback": null
							},
							{
							  "date_created": "2024-08-12T07:26:00.141579Z",
							  "date_done": "2024-08-12T07:26:00.141628Z",
							  "result": "\"Database update failed\"",
							  "traceback": "Traceback (most recent call last):\n  File \"task.py\", line 45, in update_database\n    cursor.execute(query)\npsycopg2.IntegrityError: duplicate key value violates unique constraint \"users_pkey\""
							},
							{
							  "date_created": "2024-08-12T07:25:00.141579Z",
							  "date_done": "2024-08-12T07:25:00.141628Z",
							  "result": "\"Backup completed with warnings\"",
							  "traceback": "Traceback (most recent call last):\n  File \"backup.py\", line 10, in perform_backup\n    raise Warning('Low disk space')\nWarning: Low disk space"
							},
							{
							  "date_created": "2024-08-12T07:24:00.141579Z",
							  "date_done": "2024-08-12T07:24:00.141628Z",
							  "result": "\"Report generation failed\"",
							  "traceback": "Traceback (most recent call last):\n  File \"report.py\", line 59, in generate_report\n    report = create_report(data)\nValueError: Missing required field 'report_name'"
							},
							{
							  "date_created": "2024-08-12T07:23:00.141579Z",
							  "date_done": "2024-08-12T07:23:00.141628Z",
							  "result": "\"Task completed with warnings\"",
							  "traceback": "Traceback (most recent call last):\n  File \"task.py\", line 78, in execute_task\n    validate_input(input_data)\nDeprecationWarning: 'validate_input' is deprecated and will be removed in future versions"
							},
							{
							  "date_created": "2024-08-12T07:22:00.141579Z",
							  "date_done": "2024-08-12T07:22:00.141628Z",
							  "result": "\"Task failed\"",
							  "traceback": "Traceback (most recent call last):\n  File \"task.py\", line 11, in perform_task\n    run_process()\nTypeError: 'NoneType' object is not callable"
							},
							{
							  "date_created": "2024-08-12T07:21:00.141579Z",
							  "date_done": "2024-08-12T07:21:00.141628Z",
							  "result": "\"File upload failed\"",
							  "traceback": "Traceback (most recent call last):\n  File \"upload.py\", line 27, in upload_file\n    response = requests.post(url, files=files)\nrequests.exceptions.ConnectionError: Failed to establish a new connection"
							}
						  ]
						  
						  ,
						"created_at": "2024-08-12T07:22:14.716445Z",
						"created_by": "",
						"modified_at": "2024-08-12T07:30:21.674722Z",
						"modified_by": "",
						"name": "accounts.tasks.test",
						"is_enabled": false,
						"is_deleted": true,
						"args": "[\"CRMApp2\", \"accounts.tasks.test\"]",
						"kwargs": {},
						"interval": null,
						"master_task": 52
					  }
					}
				  }
				  )
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
