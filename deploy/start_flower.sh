#!/bin/sh

cd ${PROJECT_NAME}
until timeout 5s celery -A ${PROJECT_NAME} inspect ping; do
    >&2 echo "Celery workers not available"
done

echo 'Starting flower'
celery -A ${PROJECT_NAME} flower --port=5555
