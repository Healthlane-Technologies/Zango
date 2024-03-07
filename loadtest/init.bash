#!/bin/bash

if [ "$PLATFORM" == "django" ]; then 
    cd django_project
    project="django_project"
    python generate_models.py --nt "$TENANTS" --nm "$MODELS" --nmv="$MODELS_IN_VIEWS"
else
    if [ -d zelthy_project ]; then
        echo "restarting existing project"
    else
        zelthy3 start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST" --redis_port="$REDIS_PORT"
        cp generate_modules.py zelthy_project
    fi
    cd zelthy_project
    if [ "$GENERATE_MODULES" == "true" ]; then
        python generate_modules.py --nt="$TENANTS" --nm="$MODELS" --nmod="$MODULES" --nmv="$MODELS_IN_VIEWS"
    fi
fi

case "$SERVER" in
    "runserver")
        python manage.py runserver 0.0.0.0:8000
        ;;
    "gunicorn_async")
        gunicorn -k uvicorn.workers.UvicornWorker "$PROJECT_NAME".asgi
        ;;
    "gunicorn_sync")
        gunicorn --workers=4 --bind 0.0.0.0:8000 "$PROJECT_NAME".wsgi
        ;;
    "daphne")
        daphne "$PROJECT_NAME".asgi:application
        ;;
    *)
        echo "Invalid server option"
        ;;
esac
