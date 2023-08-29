#!/bin/bash

upper_bound=4
arg1=""
arg2=""

# Parse flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--tenants)
            upper_bound="$2"
            shift 2
            ;;
        -p|--platform)
            arg1="$2"
            shift 2
            ;;
        -s|--server)
            arg2="$2"
            shift 2
            ;;
        *)
            echo "Invalid flag: $1"
            exit 1
            ;;
    esac
done


for ((i = 0; i < upper_bound; i++)); do
    nohup locust --config=locust.conf --host="http://app${i}.zelthy.com:8000/" --html "loadtest_results/{$1}/{$2}/loadtest_${i}.html" &
done