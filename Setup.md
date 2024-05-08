# Installing ZCore: Manual Process

To get started with ZCore, you will need to install it using the Python package manager, pip.

Please ensure you have Python and pip installed on your system. If you haven't installed them yet, you can find Python installation instructions [here](https://www.python.org/downloads/) and pip installation instructions [here](https://pip.pypa.io/en/stable/installation/).

Once Python and pip are installed, you can create virtual environment in which zcore will be installed.

Now you are ready to create and activate the virtual environment by running the following command in your terminal or command prompt

```shell
python3 -m venv <virtual_environment_name>
source <virtual_environment_name>/bin/activate
```

install the ZCore Open Source Platform by running the following command in your terminal or command prompt

```shell
git clone https://github.com/Healthlane-Technologies/zcore.git
cd backend
pip install -e .
```

This command will download and install the latest version of ZCore Framework along with its dependencies.

## zcore: The ZCore CLI

**zcore** is the command-line interface (CLI) tool provided by ZCore, designed to facilitate the management of projects and applications within the ZCore platform. This powerful tool streamlines various tasks such as project creation, database migrations, and much more. Here's a brief overview of ZCore and how to use it:

### Key Features and Usage

- **Project Management:**
  Use zcore to create new projects, manage existing projects, and configure project settings.

- **Database Migrations:**
  Perform database migrations seamlessly to keep your application's data schema up-to-date.

- **Application Development:**
  Simplify app development by utilizing zcore's commands for app creation, configuration, and deployment.

- **Extensive Command Options:**
  Run `zcore --help` to view a comprehensive list of available commands and their descriptions.

- **Command Specific Help:**
  For detailed information about a specific command, run `zcore [command] --help`.

To get started with **zcore cli**, open your terminal and run the following commands:

- To see a list of all available commands and their descriptions:

  ```
  zcore --help
  ```

- To get detailed information about a specific command (replace `[command]` with the desired command):
  ```
  zcore [command] --help
  ```

**zcore** is an invaluable tool for efficiently managing your ZCore projects and applications through the command line, enhancing your development and administrative capabilities.

### Prerequisites for Setting Up a Project

Before you embark on setting up your project with ZCore, there are certain prerequisites that need to be met. One of the crucial prerequisites is the setup of a PostgreSQL database. Here's a brief guide on what needs to be done:

### PostgreSQL Database Setup

Run the below command in your terminal to create a postgres container

```bash
docker run -d \
   --name <db_name> \
   -p 5432:5432 \
   -e POSTGRES_USER=<username>\
   -e POSTGRES_PASSWORD=<password> \
   -e POSTGRES_DB=<db_name> \
   -v db:/var/lib/postgresql/data \
   postgres:latest
```

ex:

```bash
docker run -d \
   --name zcore_postgres_db \
   -p 5432:5432 \
   -e POSTGRES_USER=zcore_admin \
   -e POSTGRES_PASSWORD=zcorepass \
   -e POSTGRES_DB=zcore_db \
   -v db:/var/lib/postgresql/data \
   postgres:latest
```

### Redis Setup

Run the below command in your terminal to create a redis container

```bash
docker run --name <name> -d -p 6379:6379 redis
```

ex:

```bash
docker run --name zcore_redis -d -p 6379:6379 redis
```

## Setting Up the Project

Setting up your project with ZCore is a straightforward process. Follow these steps to create your project's root folder, initialize the project, and configure the necessary settings:

#### 1. Choose a Directory:

Navigate to the directory where you want to create your project's root folder. You can use your preferred file explorer or the command line to create and navigate to this directory.

#### 2. Install ZCore and Start a New Project:

After installing ZCore, you can use the `zcore start-project` command to initiate the creation of a new project. Replace `"MyFirstProject"` with your preferred project name.

```bash
zcore start-project "MyFirstProject"
```

#### 3. Provide Database Credentials:

During the project setup, you'll be prompted to provide your PostgreSQL database credentials. These credentials include:

- **Database Name**
- **Database Username**
- **Database Password**
- **Database Host**
- **Database Port** (default is usually 5432)

If the provided credentials are incorrect or if there are issues with the database connection, the setup process will throw errors and cancel the project creation. This is because ZCore will create schemas and perform migrations during the project's creation.

#### 4. Migrate Schemas and Create Public Tenant:

Upon successful database connection, the setup process will automatically migrate schemas and create a public tenant. This ensures that your project is ready to go with the necessary database structure.

#### 5. Configure Default Platform User:

Next, you'll be asked to provide details for the default platform user. This user serves as the first administrator and will have access to App Panel, where you can begin creating apps. You'll need to provide the following information:

- **Platform User Email Address**
- **Password**
- **Password Confirmation**

Once you've entered these details, the setup process will create the default platform user for your project.

#### 6. Project Folder Structure and Boilerplate Code:

With all the necessary configurations in place, the setup process will proceed to create your project's folder structure and populate it with boilerplate code. You're now ready to start developing your healthcare apps within the ZCore platform.

##### Project Structure

```plaintext
project_name/                  # Project root directory
├── manage.py                  # Django command-line utility for administrative tasks
└── project_name/              # Django project package
    ├── __init__.py
    ├── asgi.py                # ASGI config for the project
    ├── settings.py            # Project settings (database, static files, etc.)
    ├── urls_public.py         # Public URL patterns
    ├── urls_tenant.py         # Tenant-specific URL pattern
    ├── urls.py                # Project-level URL patterns
    └── wsgi.py                # WSGI config for the project
```

Follow this guide, and you'll be well on your way to creating powerful and efficient healthcare applications using ZCore.

## Running the Development Server

Now that you've set up your project using ZCore, the next step is to start the development server. This server allows you to access App Panel, where you can begin creating your healthcare apps. Follow these steps to run the development server:

#### 1. Navigate to Your Project Folder:

Open your terminal or command prompt and navigate to the directory where you created your project's root folder. You can use the `cd` (change directory) command to move to the project directory. For example:

```bash
cd path/to/your/project
```

Replace `path/to/your/project` with the actual path to your project folder.

#### 2. Start the Development Server:

Once you're inside the project folder, you can start the development server using the following command:

```bash
python manage.py runserver
```

This command will initiate the development server, and you'll see output indicating that the server is running. By default, the server will be available at `http://localhost:8000/`.

Running the development server is a crucial step in your project setup, as it provides you with a local environment for app development and testing.

Perform the below steps from the root directory of the project

### Starting the celery worker

```
celery -A <project_name> worker -l INFO
```

### Starting Celery beat

```
celery -A <project_name> beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Creating task and syncing it

- Navigate to the module or package where you need to create the task and create `tasks.py`

  ```
  workspace
     App_Name
        module_name
           tasks.py    --> Task File
  ```

- Add the task with `@shared_task` decorator

  ```
  from celery import shared_task

  @shared_task
  def download_task(request_data):

       print("request_data: ", request_data)
       pat = Patient.objects.create(
           name="Download oc"
       )
  ```

- Navigate to App Panel and under Tasks Table sync the tasks
- Executing task programmatically

  ```

  from zcore.core.tasks import zcore_task_executor
  zcore_task_executor.delay(request.tenant.name, "<task_name>", *args, **kwargs)

  task_name can be taken from App Panel -> Tasks table
  ```

  Example

  ```

  from zcore.core.tasks import zcore_task_executor
  zcore_task_executor.delay(request.tenant.name, ""patient.tasks.export_table", {"test": "test_kwarg"})

  task_name can be taken from App Panel -> Tasks table
  ```
