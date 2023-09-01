FROM python:3.10

RUN pip install pluginbase django-cors-headers channels memory-profiler gunicorn daphne

COPY backend /zelthy/backend
COPY examples/firstproject /zelthy/examples/firstproject
COPY dproject /zelthy/dproject
COPY init.bash /zelthy/

WORKDIR /zelthy/
RUN cd backend && pip install .

CMD ["sh", "-c", "sleep 10 && /bin/bash init.bash"]