# Using Docker to Create Zelthy Projects

This guide outlines the steps to create and develop Zelthy projects without the need for local installations.

# Develop

## Prerequisites

Make sure you have Docker and Docker Compose installed on your machine. If not, you can follow the installation instructions for [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

## Steps

1. Clone the Zelthy3 repository:

    ```bash
    git clone https://github.com/zelthy/zelthy3.git
    cd zelthy3
    ```

2. Run the following command from the root folder of the project:

    ```bash
    python zel_setup.py --build_core
    ```

    Use the `--build_core` option to build the Zelthy library for the first time. Subsequent projects can omit this step.

3. This creates a project named `zelthy_project` in the `zproject` folder in the same directory.

4. Customize the project creation using optional arguments:

    ```bash
    python zel_setup.py --project_name my_project --project_dir /path/to/my_project --server runserver --build_core --platform_username user@example.com --platform_user_password secret --skip_build_project
    ```

    - `--project_name`: Modifies the name of the project (Default: `zelthy_project`).
    - `--project_dir`: Specifies the directory for project creation (Default: `zproject`).
    - `--build_core`: Builds the Zelthy library (Default: `False`).
    - `--platform_username`: The user email of the platform user (Default: `zelthy@mail.com`).
    - `--platform_user_password`: The password for the platform user (Default: `Zelthy@123`).
    - `--skip_build_project`: Skips building the project (Default: `False`).
    - `--start`: Starts the project as soon as it is created (Default: `False`)

5. To install any Zelthy package, add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to the `.env` file created in the `project_dir` and restart the containers.

6. Subsequently, you can use `docker compose up` from the `project_dir` to start the project.


# Rebuilding Core

If you modify somehting in the core of the project, to rebuild it run the following command from the root of the zelthy3 project

```bash
python zel_setup.py --project_dir <project_dir> --rebuild_core
```

you can then run `docker compose up` from the project directory to start the project

# Syncing Static Files

You can sync static files by running `python manage.py collectstatic` from the project directory in the `<project>-app-1` container. Make sure to sync the static files before deploying

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