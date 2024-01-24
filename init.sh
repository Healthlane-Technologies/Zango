#!/bin/sh

if [ "$ENV" = "dev" ]; then 
    if [ -d "$PROJECT_NAME" ]; then
        echo "restarting existing project"
    else
        zelthy3 start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST"
    fi
    cd "$PROJECT_NAME"
    python manage.py runserver 0.0.0.0:8000
else
    if [ -d "$PROJECT_NAME" ]; then
        echo "restarting existing project"
    else
        zelthy3 start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST"
    fi
    cd "$PROJECT_NAME"
    mv /zelthy/config/gunicorn.conf.py .
    python manage.py collectstatic --noinput
    python manage.py migrate_schemas
    gunicorn -c gunicorn.conf.py "$PROJECT_NAME".wsgi
fi