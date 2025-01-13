# Contribution Guide for Zango

## Table of Contents

1. [How to Contribute](#how-to-contribute)
   - [Reporting Issues](#reporting-issues)
   - [Contributing to Zango](#contributing-to-zango)
2. [Contributing to Zango backend](#contributing-to-zango-backend)
3. [Contributing to Zango frontend](#contributing-to-zango-frontend)
4. [Contributing to documentation](#contributing-to-documentation)
5. [Community](#community)

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please create an issue in our [issue tracker](https://github.com/Healthlane-Technologies/Zango/issues). When reporting an issue, please include as much detail as possible, including steps to reproduce the problem, your environment, and any relevant log output.

## Contributing to Zango

This section describes the general practices for contributing to zango, you can check the next sections which describe how to contribute to [frontend](#contributing-to-zango-frontend), [backend](#contributing-to-zango-backend) and [documentation](#contributing-to-documentation)

### Getting Started

1. [Fork the Repository](https://help.github.com/en/github/getting-started-with-github/fork-a-repo): Fork the [Zango repository](https://github.com/Healthlane-Technologies/Zango) to your GitHub account.
2. [Clone the Repository](https://help.github.com/en/desktop/contributing-to-projects/creating-a-pull-request): Clone your forked repository to your local machine.
3. Set Up Environment: Follow the setup instructions in [Setup.md](https://github.com/Healthlane-Technologies/Zango/blob/main/Setup.md) to configure your development environment.

### Development Workflow

1. Create a Branch: Create a new branch for your changes.

```bash
    git checkout -b feature/your-feature-name
```

2. Implement Changes: Make your changes, ensuring to follow the coding standards and best practices.
3. Install pre-commit: In the root directory of this repo run `pre-commit install`.This will ensure that pre-commit automatically runs the configured hooks (such as code formatters, linters, and other checks) on your files before each commit, helping to maintain code quality and consistency.
4. Commit Changes: Commit your changes with a meaningful commit message.

```bash
    git add .
    git commit -m "Add feature <feature_name>"
```

### Submitting Changes

1. Push to GitHub: Push your changes to your forked repository.

```bash
    git push origin feature/your-feature-name
```

2. [Create a Pull Request](https://opensource.com/article/19/7/create-pull-request-github): Open a pull request from your branch to the main branch of the original repository. Provide a clear description of your changes and link any related issues.

### Code Review

1. Respond to Feedback: Be prepared to make changes based on feedback from code reviewers.
2. Update PR: Push any updates to your branch to reflect the feedback received.

## Contributing to Zango backend

### Steps to contribute to Zango backend

1. Clone the zango repository
2. Create a new virtual environment inside a fresh directory (this virtual env will be used to setup a zango project using local copy of zango [similar to django.](https://docs.djangoproject.com/en/dev/intro/contributing/#getting-a-copy-of-django-s-development-version))
3. Activate your virtual env and run the below command to install local copy of zango:

```bash
    pip install -e path/to/your/zango_repo/backend
```

4. Perform the steps to setup a new project as described in the docs [here.](https://www.zango.dev/docs/core/getting-started/installing-zango/python-venv)
5. Start your project and launch a new app.
6. Now whatever changes you will do to your local zango it will be reflected in your project.

**Running Migrations:** You can run all the Zango migrations using the command `python manage.py migrate_schemas`, this is for the zango
core migrations only, you can create and run app specific migrations as described [here](https://www.zango.dev/docs/core/ddms/migrating-ddms).

**Static Files:** To add static files that you have added to Zango, you can use the command `python manage.py collectstatic`.

## Contributing to Zango frontend

### with mock server

1. Go to the frontend directory of the repository and install the dependencies

```bash
    cd frontend
    yarn install
```

2. Start the application with mock service worker

```bash
    yarn mock
```

### with live data

#### Prerequisite

Before running this application, ensure that your Zango backend is up and running.

#### Default Port Configuration

By default, the application uses Zango's default running port `(localhost:8000)`. If you wish to use a different port, you can easily configure this in your package.json file under the proxy key.

1. Go to the frontend directory of the repository and install the dependencies

```bash
    cd frontend
    yarn install
```

2. Start the application with dev server

```bash
    yarn dev
```

### Generating and Using frontend build in Zango

To test your frontend app with the Zango framework, follow these steps:

Run the build command:

```bash
    yarn build
```

This command generates the build and places it inside the `backend/src/zango/assets/app_panel/js` directory of Zango.

The generated build will include the latest timestamp in its filename (`build.<timestamp>.min.js`). By default, the most recent build will be served. If you need to use a different build, you can update the filename in the `backend/src/zango/apps/shared/tenancy/templates/app_panel.html` file.

4. Collecting Static Build for Your Project

Before testing the build, collect the static files for your project. Ensure your project is already created and your environment is activated.

Change directory to your project:

```bash
    cd <project_name>
```

Collect the static build:

```bash
    python manage.py collectstatic
```

## Contributing to Documentation

We use docusaurus for maintaining Zango's documentation

1. Go to the docs directory of the repository and install the dependencies

```bash
    cd zango/docs
    yarn install
```

2. Start the application

```bash
    yarn start
```

## Community

If you face any issues or need any help you can use our [discord](https://discord.com/invite/WHvVjU23e7) to connect with other contributors.
