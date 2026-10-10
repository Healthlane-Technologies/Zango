# Bootstrap Templates

These are the exact file templates to create when bootstrapping a Zango environment in the developer's current working directory.

> **Two setup modes are supported.** Docker mode uses the full Docker Compose stack. Venv mode runs Django locally and uses Docker only for Postgres and Redis. Choose the right section below based on the mode (references/setup.md §1).

---

## Docker Mode Files

### File: `deploy/.env` (Docker mode)

```env
COMPOSE_PROJECT_NAME=zango-a1b2
PLATFORM_USERNAME=platform_admin@zango.dev
PLATFORM_USER_PASSWORD=Zango@123
PROJECT_NAME=zango_project
POSTGRES_USER=zango_admin
POSTGRES_PASSWORD=zangopass
POSTGRES_DB=zango
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
PLATFORM_DOMAIN_URL=localhost
CSRF_TRUSTED_ORIGINS=http://localhost:3000
FIELD_ENCRYPTION_KEY=<generate-fernet-key>
```

**`FIELD_ENCRYPTION_KEY`** is required for app secrets encryption. Generate a random Fernet key at bootstrap time and store it here:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Never change this key after creation — existing encrypted secrets will become unreadable.

Ask the user if they want to customize any of these values before writing. Use these as sensible defaults. `COMPOSE_PROJECT_NAME` controls the Docker Compose project name (container prefix) — generate a unique default like `zango-<random-4-chars>` so containers aren't always prefixed with "deploy-".

### File: `deploy/Dockerfile`

```dockerfile
FROM kczelthy/zango:latest

RUN apt-get update && apt-get install -y net-tools sudo && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ARG HOST_UID=1000
ARG HOST_GID=1000

RUN groupadd -o -g $HOST_GID -r zango_user && \
    adduser --uid $HOST_UID --gid $HOST_GID --disabled-password --gecos "" zango_user && \
    echo 'zango_user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

USER zango_user

COPY init.sh /zango/
WORKDIR /zango/
CMD ["/bin/sh", "init.sh"]
```

### File: `deploy/init.sh`

```bash
#!/bin/bash

set -a
source /zango/.env
set +a

if [ -z "$PLATFORM_DOMAIN_URL" ]; then
    PLATFORM_DOMAIN_URL="localhost"
fi

cd "$PROJECT_NAME" 2>/dev/null

if [ -d "$PROJECT_NAME" ]; then
    echo "Restarting existing project..."
    if [ "${UPDATE_APPS_ON_STARTUP:-true}" = "true" ]; then
        echo "Updating apps..."
        SINGLE_BEAT_REDIS_SERVER=redis://${REDIS_HOST}:${REDIS_PORT}/1 single-beat zango update-apps
    fi
else
    cd /zango
    zango start-project $PROJECT_NAME \
        --db_name="$POSTGRES_DB" \
        --db_user="$POSTGRES_USER" \
        --db_password="$POSTGRES_PASSWORD" \
        --db_host="$POSTGRES_HOST" \
        --db_port="$POSTGRES_PORT" \
        --platform_username="$PLATFORM_USERNAME" \
        --platform_user_password="$PLATFORM_USER_PASSWORD" \
        --redis_host="$REDIS_HOST" \
        --redis_port="$REDIS_PORT" \
        --platform_domain_url="$PLATFORM_DOMAIN_URL"
    cd "$PROJECT_NAME"
fi

python manage.py runserver 0.0.0.0:8000
```

### File: `deploy/docker_compose.yml`

```yaml
name: ${COMPOSE_PROJECT_NAME}

services:
  postgres:
    image: postgres:15
    env_file:
      - .env
    environment:
      POSTGRES_HOST_AUTH_METHOD: md5  # ensures pg_hba.conf allows host connections from containers and local tools
    ports:
      - "127.0.0.1:5432:5432"  # host port — connect via TablePlus/psql at localhost:5432
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} -p ${POSTGRES_PORT}",
        ]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - dev_db:/var/lib/postgresql/data

  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - HOST_UID=${HOST_UID}
        - HOST_GID=${HOST_GID}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    env_file:
      - .env
    environment:
      ENV: dev
    volumes:
      - .:/zango/
    healthcheck:
      test: ["CMD-SHELL", "netstat -ltn | grep -q 8000"]
      timeout: 5s
      retries: 3

  celery:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - HOST_UID=${HOST_UID}
        - HOST_GID=${HOST_GID}
    command: /bin/sh -c "cd ${PROJECT_NAME} && celery -A ${PROJECT_NAME} worker -l info"
    volumes:
      - .:/zango/
    env_file:
      - .env
    depends_on:
      app:
        condition: service_healthy
      redis:
        condition: service_healthy

  redis:
    image: redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - HOST_UID=${HOST_UID}
        - HOST_GID=${HOST_GID}
    command: /bin/sh -c "cd ${PROJECT_NAME} && single-beat celery -A ${PROJECT_NAME} beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
    volumes:
      - .:/zango/
    env_file:
      - .env
    depends_on:
      app:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  dev_db:
```

### Bootstrap Commands (Docker mode)

After creating all files in `deploy/`:

```bash
# Make init.sh executable
chmod +x deploy/init.sh

# Export host user IDs for file permission alignment
export HOST_UID=$(id -u)
export HOST_GID=$(id -g)

# Build and start all services
docker compose -f deploy/docker_compose.yml up -d --build

# Wait for health checks, then verify
# Poll until the platform responds
curl -s -o /dev/null -w "%{http_code}" -L http://localhost:8000/platform
```

### Verification (Docker mode)

After startup, the platform should be accessible at:
- **URL**: `http://localhost:8000/platform`
- **Username**: Value of PLATFORM_USERNAME from .env
- **Password**: Value of PLATFORM_USER_PASSWORD from .env

### Local DB Access — TablePlus / psql (Docker mode)

The postgres container already binds port `5432` to the host. Connect from TablePlus or any local client using:

| Field    | Value |
|----------|-------|
| Host     | `localhost` (NOT `postgres` — that name is only valid inside Docker) |
| Port     | `5432` |
| User     | Value of `POSTGRES_USER` from `.env` (default: `zango_admin`) |
| Password | Value of `POSTGRES_PASSWORD` from `.env` (default: `zangopass`) |
| Database | Value of `POSTGRES_DB` from `.env` (default: `zango`) |

> If port 5432 is already occupied on your machine, change the host-side mapping in `docker_compose.yml` (e.g. `"5433:5432"`) and connect TablePlus on port `5433`.

### Stopping and Restarting (Docker mode)

```bash
# Stop
docker compose -f deploy/docker_compose.yml down

# Restart (data persists in dev_db volume)
export HOST_UID=$(id -u) HOST_GID=$(id -g)
docker compose -f deploy/docker_compose.yml up -d

# Full reset (destroys data)
docker compose -f deploy/docker_compose.yml down -v
```

### Running Management Commands Inside the Container (Docker mode)

```bash
# General pattern
docker compose -f deploy/docker_compose.yml exec app bash -c "cd <PROJECT_NAME> && python manage.py <command>"

# Run migrations for an app
docker compose -f deploy/docker_compose.yml exec app bash -c "cd <PROJECT_NAME> && python manage.py ws_migrate <app_name>"

# Sync static files
docker compose -f deploy/docker_compose.yml exec app bash -c "cd <PROJECT_NAME> && python manage.py sync_static <app_name> && python manage.py collectstatic --noinput"

# Update apps (sync policies, tasks, etc.)
docker compose -f deploy/docker_compose.yml exec app bash -c "cd <PROJECT_NAME> && SINGLE_BEAT_REDIS_SERVER=redis://redis:6379/1 single-beat zango update-apps --app_name <app_name>"
```

---

## Venv Mode

The Django app runs locally in a virtualenv. Only Postgres and Redis run in Docker — there is no app container.

### Step-by-Step

1. **Gather configuration** - Same defaults as Docker mode. *(Requires Python 3.10+ and Docker locally.)*

2. **Venv setup** - Ask for an existing venv path or a new one (default: `./venv`):
   - New: `python3 -m venv <venv_path> && <venv_path>/bin/pip install zango`
   - Existing: verify with `<venv_path>/bin/zango --version`

3. **Save config** - Write `.claude/zango-config.json` (use absolute path for venv):
   ```json
   { "setup_mode": "venv", "venv_path": "/absolute/path/to/venv" }
   ```

4. **Create DB-only files** - Use the templates below (`docker_compose_db.yml` and `.env` venv variant).

5. **Start DB services:**
   ```bash
   docker compose -f deploy/docker_compose_db.yml up -d
   ```

6. **Bootstrap project** - Run from project root (see Bootstrap Commands section below for the full `zango start-project` invocation).

7. **Start the development server** (in a separate terminal):
   ```bash
   cd <PROJECT_NAME> && <venv_path>/bin/python manage.py runserver 0.0.0.0:8000
   ```

8. **Wait for health** - Poll `http://localhost:8000/platform` until HTTP 200, then share credentials.

---

### Venv Mode Files

### File: `deploy/docker_compose_db.yml` (Venv mode — DB services only)

```yaml
name: ${COMPOSE_PROJECT_NAME}

services:
  postgres:
    image: postgres:15
    env_file:
      - .env
    ports:
      - "5432:5432"
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} -p ${POSTGRES_PORT}",
        ]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - dev_db:/var/lib/postgresql/data

  redis:
    image: redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  dev_db:
```

### File: `deploy/.env` (Venv mode)

The key difference from Docker mode: `POSTGRES_HOST=localhost` and `REDIS_HOST=localhost` because the app runs on the host machine, not inside a container.

```env
COMPOSE_PROJECT_NAME=zango-a1b2
PLATFORM_USERNAME=platform_admin@zango.dev
PLATFORM_USER_PASSWORD=Zango@123
PROJECT_NAME=zango_project
POSTGRES_USER=zango_admin
POSTGRES_PASSWORD=zangopass
POSTGRES_DB=zango
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
PLATFORM_DOMAIN_URL=localhost
CSRF_TRUSTED_ORIGINS=http://localhost:3000
FIELD_ENCRYPTION_KEY=<generate-fernet-key>
```

Generate `FIELD_ENCRYPTION_KEY`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### File: `.claude/zango-config.json`

Create this file in the project root to persist setup mode and venv path for the current session and future sessions:

```json
{
  "setup_mode": "venv",
  "venv_path": "/absolute/path/to/venv"
}
```

Use the absolute path. Expand `~` and relative paths before writing.

### Bootstrap Commands (Venv mode)

```bash
# 1. Start DB services only
docker compose -f deploy/docker_compose_db.yml up -d

# 2. Wait for postgres to be healthy
docker compose -f deploy/docker_compose_db.yml ps

# 3. Bootstrap the Zango project (replace placeholders with values from .env)
<venv_path>/bin/zango start-project <PROJECT_NAME> \
  --db_name="<POSTGRES_DB>" \
  --db_user="<POSTGRES_USER>" \
  --db_password="<POSTGRES_PASSWORD>" \
  --db_host="localhost" \
  --db_port="5432" \
  --platform_username="<PLATFORM_USERNAME>" \
  --platform_user_password="<PLATFORM_USER_PASSWORD>" \
  --redis_host="localhost" \
  --redis_port="6379" \
  --platform_domain_url="localhost"

# 4. Start the development server (run in a separate terminal)
cd <PROJECT_NAME> && <venv_path>/bin/python manage.py runserver 0.0.0.0:8000

# 5. Verify the platform is up
curl -s -o /dev/null -w "%{http_code}" -L http://localhost:8000/platform
```

### Running Management Commands (Venv mode)

Run these from the project root (one directory above `<PROJECT_NAME>/`):

```bash
# Migrations
cd <PROJECT_NAME> && <venv_path>/bin/python manage.py ws_makemigration <app_name>
cd <PROJECT_NAME> && <venv_path>/bin/python manage.py ws_migrate <app_name>

# Sync static files
cd <PROJECT_NAME> && <venv_path>/bin/python manage.py sync_static <app_name>
cd <PROJECT_NAME> && <venv_path>/bin/python manage.py collectstatic --noinput

# Update apps (sync policies, tasks, etc.)
cd <PROJECT_NAME> && <venv_path>/bin/zango update-apps --app_name <app_name>

# Start Celery worker (in a separate terminal)
cd <PROJECT_NAME> && <venv_path>/bin/celery -A <PROJECT_NAME> worker -l info

# Start Celery beat (in a separate terminal)
cd <PROJECT_NAME> && <venv_path>/bin/celery -A <PROJECT_NAME> beat -l info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Stopping and Restarting DB Services (Venv mode)

```bash
# Stop DB containers
docker compose -f deploy/docker_compose_db.yml down

# Restart DB containers (data persists in dev_db volume)
docker compose -f deploy/docker_compose_db.yml up -d

# Full DB reset (destroys all data)
docker compose -f deploy/docker_compose_db.yml down -v
```
