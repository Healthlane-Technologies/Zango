# Using Docker to Create Zango Projects

This guide outlines the steps to create and develop Zango projects without the need for local installations.

# Installing Zango with Docker

## Prerequisites

To begin using Zango through Docker installation, ensure that Docker and Docker Compose are installed on your machine. If not, follow the installation instructions for [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

## Steps

1. Clone the Zango repository:

   ```bash
   git clone https://github.com/Healthlane-Technologies/zango.git
   cd zango
   ```

2. Run the following command from the root folder of the project:

   ```bash
   python setup_project.py <directory>
   ```

   You can use the `--build_core` option to build the Zango library

3. This creates a project named `zango_project` in the `zproject` folder in the specified directory.

4. Customize the project creation using optional arguments:

   ```bash
   python setup_project.py --project_name my_project --project_dir /path/to/my_project --build_core --platform_username user@example.com --platform_user_password secret --skip_build_project
   ```

   - `--project_name`: Modifies the name of the project (Default: `zango_project`).
   - `--project_dir`: Specifies the directory for project creation (Default: `zproject`).
   - `--build_core`: Builds the Zango library (Default: `False`).
   - `--platform_username`: The user email of the platform user (Default: `platform_admin@zango.dev`).
   - `--platform_user_password`: The password for the platform user (Default: `Zango@123`).

5. Docker is started as a non root user, run the below commands to export the host HOST_UID and HOST_GID

```bash
export HOST_UID=$(id -u)
export HOST_GID=$(id -g)
```

6. Run `docker compose up` in the project directory to start the project

# Rebuilding Core

If you modify somehting in the core of the project, to rebuild it run the following command from the root of the zango project

```bash
python setup_project.py --project_dir <project_dir> --rebuild_core
```

# Syncing Static Files And Running Migrations

You can sync static files by running `python manage.py collectstatic` from the project directory in the `<project>-app-1` container. Make sure to sync the static files before deploying

You can run migrations by running `python manage.py ws_makemigrations <project_name>` and `python manage.py ws_migrate <project_name` from the project directory in the container

# Deploy

The necessary docker compose, nginx and gunicorn files to deploy your project are created in the project directory you can use it to deploy your apps easily

## Steps

- Replace `${PROJECT_NAME}` with your project name in the following files
  - `config/nginx.conf`
  - `prod.dockerfile`
- Change the `CORS_ORIGIN_WHITELIST` and `CSRF_TRUSTED_ORIGINS` in the project settings to appropriate domain configured
- Start the production server by running the two commands
  ```bash
  docker compose -f docker-compose.prod.yml build
  docker compose -f docker-compose.prod.yml up
  ```
- You can access your server at `http://<domain>:1443` (By default the domain is localhost)
-
