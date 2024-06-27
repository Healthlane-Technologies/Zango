FROM python:3.10
RUN  apt-get update
RUN  apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl
COPY backend/requirements/base.txt .
RUN pip install -r base.txt
RUN pip install channels memory-profiler gunicorn daphne
COPY . /zango/
WORKDIR /zango/
# RUN pip install -r backend/requirements/base.txt
RUN cd backend && pip install .