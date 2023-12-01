#!/bin/sh

if [ -d "$PROJECT_NAME" ]; then
    echo "restarting existing project"
else
    zelthy3 start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD"
fi
cd "$PROJECT_NAME"
case "$SERVER" in
    "runserver")
        python manage.py runserver 0.0.0.0:8000
        ;;
    "gunicorn_async")
        gunicorn -k uvicorn.workers.UvicornWorker "$PROJECT_NAME".asgi
        ;;
    "gunicorn")
        python manage.py collectstatic --noinput
        python manage.py migrate_schemas
        gunicorn -c gunicorn.conf.py "$PROJECT_NAME".wsgi
        ;;
    "daphne")
        daphne "$project".asgi:application
        ;;
    *)
        echo "Invalid server option"
        ;;
esac