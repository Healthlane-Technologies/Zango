#!/bin/bash

docker stop zelthy_postgres || true && docker rm zelthy_postgres || true

docker run --name zelthy_postgres -e POSTGRES_DB=zelthy1 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=zelthy3pass \
  -p 127.0.0.1:5432:5432 \
  -d postgres:latest

sleep 3

# Parse flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--tenants)
            tenants="$2"
            shift 2
            ;;
        -p|--platform)
            platform="$2"
            shift 2
            ;;
        -nm | --no_of_models)
            no_of_models="$2"
            shift 2
            ;;
        -nmod | --no_of_modules)
            no_of_modules="$2"
            shift 2
            ;;
        -nmv | --no_of_models_in_view)
            no_of_models_in_view="$2"
            ;;
        -s | --server)
            server="$2"
            shift 2
            ;;
        *)
            echo "Invalid flag: $1"
            exit 1
            ;;
    esac
done


if [ "$platform" == "django" ]; then 
    cd dproject
    project="dproject"
    python generate_models.py --nt "$tenants" --nm "$no_of_models" --nmv="$no_of_models_in_view"
else
    cd examples/firstproject
    project="firstproject"
    python generate_modules.py --nt="$tenants" --nm="$no_of_models" --nmod="$no_of_modules" --nmv="$no_of_models_in_view"
fi

case "$server" in
    "runserver")
        mprof run python manage.py runserver
        ;;
    "gunicorn_async")
        mprof run gunicorn -k uvicorn.workers.UvicornWorker "$project".asgi
        ;;
    "gunicorn_sync")
        mprof run gunicorn --workers=4 "$project".wsgi
        ;;
    "daphne")
        mprof run daphne "$project".asgi:application
        ;;
    *)
        echo "Invalid server option"
        ;;
esac
