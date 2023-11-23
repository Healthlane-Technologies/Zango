# Using Docker to Create Zelthy Projects

This guide outlines the steps to create and develop Zelthy projects without the need for local installations.

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
    - `--server`: Specifies the server to be used to run the project (Default: `runserver`).
    - `--build_core`: Builds the Zelthy library (Default: `False`).
    - `--platform_username`: The user email of the platform user (Default: `zelthy@mail.com`).
    - `--platform_user_password`: The password for the platform user (Default: `Zelthy@123`).
    - `--skip_build_project`: Skips building the project (Default: `False`).

5. To install any Zelthy package, add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to the `.env` file created in the `project_dir` and restart the containers.

6. Subsequently, you can use `docker compose up` from the `project_dir` to start the project.

Feel free to adjust the wording and formatting based on your preferences and the specific needs of your users.

