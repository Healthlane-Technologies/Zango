## Development Environment

### Git Setup

To set up Git for your application directory, use the following command:

```shell
zango git-setup <app_dir>
```

**Options:**
- `--git_repo_url TEXT`    : The URL of the repository [required]
- `--dev_branch TEXT`      : The Git branch for development [required]
- `--staging_branch TEXT`  : The Git branch for staging [required]
- `--prod_branch TEXT`     : The Git branch for production [required]
- `--initialize`           : Initialize the repository (use this to initialize the repo in the development environment)

Make sure to maintain the `version` in `settings.json`.

### Exporting Fixtures

To define a model as a config model, use the following code:

```python
class MyModel(DynamicModelBase):
    ...

    class DynamicModelMeta:
        is_config_model = True
```

To export fixtures, use the following command:

```shell
python manage.py export_fixture
```

**Options:**
- `--workspace`         : The workspace name to be used.
- `--app`               : Export fixtures for the app.
- `--package`           : Export fixtures for the package.
- `--framework`         : Export fixtures for the framework.
- `--release_version`   : Export fixture for the given version.

**Note:** `--app`, `--package`, and `--framework` are mutually exclusive options.

This will save the fixture under the `release/<version>/fixtures/` folder inside the workspace directory.

## Production/Staging Environment

### Launching and Running

- Launch an app from the App Panel.
- Run `git-setup` for that app.
- From the project directory, run:

  ```shell
  docker compose -f docker-compose.prod.yml restart
  ```

## Releasing a Particular App

To update and release a particular app, use the following command:

```shell
zango update-apps
```

Options:
- `--app_name TEXT`    : App Name(s) (optional)

Note: If no app names are specified, the command will update and release all apps by default.

You can specify multiple app names by repeating the ```--app_name``` option.

Examples
To update and release a single app named my_app:

```shell
zango update-apps --app_name my_app
```

To update and release multiple apps named app1 and app2:

```shell
zango update-apps --app_name app1 --app_name app2
```

This command will perform following operations if an app has newer version available:
- Updates the codebase
- Runs migration
- Sync Static files
- Sync Policies
- Execute Fixtures
