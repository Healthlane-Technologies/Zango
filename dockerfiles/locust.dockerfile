FROM python:3.10

RUN pip install locust daphne gunicorn memory-profiler

COPY loadtest.py /zelthy/
COPY loadtest_results /zelthy/loadtest_results
COPY loadtest.bash /zelthy/
COPY locust.conf /zelthy/

WORKDIR /zelthy/

CMD ["sh", "-c" ," sleep 30 && /bin/bash loadtest.bash -t 1 -p django -s runserver"]