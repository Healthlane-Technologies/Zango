FROM zango_test:latest

# RUN pip install channels memory-profiler gunicorn daphne

COPY generate_modules.py /zango/
COPY django_project /zango/django_project
COPY gunicorn.conf.py /zango/
COPY init.bash /zango/

WORKDIR /zango/

CMD ["sh", "-c", "sleep 10 && /bin/bash init.bash"]