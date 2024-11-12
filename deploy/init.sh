#!/bin/sh

should_update_on_startup() {
    if [ -z "$UPDATE_APPS_ON_STARTUP" ]; then
        UPDATE_APPS_ON_STARTUP="true"
    fi

    case "$(echo "$UPDATE_APPS_ON_STARTUP" | tr '[:upper:]' '[:lower:]')" in
        true|1)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

if [ -z "$PLATFORM_DOMAIN_URL" ]; then
    PLATFORM_DOMAIN_URL="localhost"
fi

if [ "$ENV" = "dev" ]; then 
    cd "$PROJECT_NAME"
    if [ -d "$PROJECT_NAME" ]; then
        echo "restarting existing project"
        if should_update_on_startup; then
            echo "Updating apps..."
            zango update-apps
        fi
    else
        zango start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST" --redis_port="$REDIS_PORT" --platform_domain_url="$PLATFORM_DOMAIN_URL"
        cd "$PROJECT_NAME"
    fi
    python manage.py runserver 0.0.0.0:8000
else
    if [ -d "$PROJECT_NAME" ]; then
        echo "restarting existing project"
        cd "$PROJECT_NAME"
        if should_update_on_startup; then
            echo "Updating apps..."
            zango update-apps
        fi
    else
        zango start-project $PROJECT_NAME --db_name="$POSTGRES_DB" --db_user="$POSTGRES_USER" --db_password="$POSTGRES_PASSWORD" --db_host="$POSTGRES_HOST" --db_port="$POSTGRES_PORT" --platform_username="$PLATFORM_USERNAME" --platform_user_password="$PLATFORM_USER_PASSWORD" --redis_host="$REDIS_HOST" --redis_port="$REDIS_PORT" --platform_domain_url="$PLATFORM_DOMAIN_URL"
        cd "$PROJECT_NAME"
    fi
    cp /zango/config/gunicorn.conf.py .
    python manage.py collectstatic --noinput
    python manage.py migrate_schemas
    gunicorn -c gunicorn.conf.py "$PROJECT_NAME".wsgi
fi
