FROM kczelthy/zelthy3:latest

RUN pip install channels memory-profiler gunicorn daphne

COPY generate_modules.py /zelthy/
COPY django_project /zelthy/django_project
COPY init.bash /zelthy/

WORKDIR /zelthy/

CMD ["sh", "-c", "sleep 10 && /bin/bash init.bash"]