for ((i = 0; i < 20; i++))
do
    nohup locust --config=locust.conf --host="http://app${i}.zelthy.com:8000/" --html "loadtest_results/async_gunicorn/loadtest_${i}.html" &
done