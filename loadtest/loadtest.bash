#!/bin/bash

source .env.loadtest

# Create the locust.conf file
echo "users = $USERS
spawn-rate = $SPAWN_RATE
run-time = $RUNTIME
headless = $HEADLESS
locustfile = $LOCUSTFILE" > locust.conf

# Generate the loadtest.py file
python add_loadtest.py $PLATFORM $MODULES

# Start the server
docker compose up -d

until curl -f http://app0.zelthy.com:8000/mod0/view1
do
    echo "Waiting for server to start"
    sleep 1
done

echo "Server Started"
echo "Beginning loadtest"

servers=("runserver" "gunicorn_sync" "gunicorn_async" "daphne")
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

for ((i = 0; i < $TENANTS; i++)); do
    nohup locust --config=locust.conf --host="http://app${i}.zelthy.com:8000/" --html "loadtest_results/${cur}/${PLATFORM}/${SERVER}/loadtest_${i}.html" &
done

# Sleep for a while to allow locust processes to start
sleep 10

# Wait for all background processes to finish
wait

