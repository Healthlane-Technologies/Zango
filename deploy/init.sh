#!/bin/sh

if [ -z "$PLATFORM_DOMAIN_URL" ]; then
    PLATFORM_DOMAIN_URL="localhost"
fi

python << END
import sys
import time

import psycopg2

suggest_unrecoverable_after = 30
start = time.time()

while True:
    try:
        psycopg2.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}",
        )
        break
    except psycopg2.OperationalError as error:
        sys.stderr.write("Waiting for PostgreSQL to become available...\n")

        if time.time() - start > suggest_unrecoverable_after:
            sys.stderr.write("  This is taking longer than expected. The following exception may be indicative of an unrecoverable error: '{}'\n".format(error))

    time.sleep(1)
END

>&2 echo 'PostgreSQL is available'

if [ "$ENV" = "dev" ]; then 
    if [ -d "$PROJECT_NAME" ]; then
        echo "restarting existing project"
    else
        zango start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST" --redis_port="$REDIS_PORT" --platform_domain_url="$PLATFORM_DOMAIN_URL"
    fi
    cd "$PROJECT_NAME"
    python manage.py runserver 0.0.0.0:8000
else
    if [ -d "$PROJECT_NAME" ]; then
        echo "restarting existing project"
    else
        zango start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST" --redis_port="$REDIS_PORT" --platform_domain_url="$PLATFORM_DOMAIN_URL"
    fi
    cd "$PROJECT_NAME"
    cp /zango/config/gunicorn.conf.py .
    python manage.py collectstatic --noinput
    python manage.py migrate_schemas
    gunicorn -c gunicorn.conf.py "$PROJECT_NAME".wsgi
fi