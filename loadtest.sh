#!/bin/bash

servers=("runserver" "gunicorn" "gunicorn_async" "daphne")
cur=$(date +"%y_%m_%d")
if [ ! -d "loadtest_results/$cur" ]; then
    mkdir -p "loadtest_results/$cur"
    mkdir -p "loadtest_results/$cur/django"
    mkdir -p "loadtest_results/$cur/zelthy"

    for server in "${servers[@]}"; do
        mkdir -p "loadtest_results/$cur/django/$server"
        mkdir -p "loadtest_results/$cur/zelthy/$server"
    done
fi

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
        -s|--server)
            server="$2"
            shift 2
            ;;
        *)
            echo "Invalid flag: $1"
            exit 1
            ;;
    esac
done

for ((i = 0; i < tenants; i++)); do
    nohup locust --config=locust.conf --host="http://app${i}.zelthy.com:8000/" --html "loadtest_results/${cur}/${platform}/${server}/loadtest_${i}.html" &
done

sleep 80

# docker stop zelthy_postgres
# docker rm zelthy_postgres
