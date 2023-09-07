#!/bin/bash

if [ "$PLATFORM" == "django" ]; then 
    cd dproject
    project="dproject"
    python generate_models.py --nt "$TENANTS" --nm "$MODELS" --nmv="$MODELS_IN_VIEWS" --nv="$NO_OF_VIEWS"
else
    cd examples/firstproject
    project="firstproject"
    python generate_modules.py --nt="$TENANTS" --nm="$MODELS" --nmod="$MODULES" --nmv="$MODELS_IN_VIEWS"
fi

case "$SERVER" in
    "runserver")
        python manage.py runserver 0.0.0.0:8000
        ;;
    "gunicorn_async")
        gunicorn -k uvicorn.workers.UvicornWorker "$project".asgi --bind 0.0.0.0:8000
        ;;
    "gunicorn_sync")
        gunicorn --workers=4 --bind 0.0.0.0:8000 "$project".wsgi
        ;;
    "daphne")
        daphne "$project".asgi:application
        ;;
    *)
        echo "Invalid server option"
        ;;
esac
