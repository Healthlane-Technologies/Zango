FROM python:3.10
RUN  apt-get update && apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl
WORKDIR /zango
# ref: https://docs.docker.com/build/cache/
COPY backend/requirements/base.txt /backend/requirements/base.txt
RUN pip install -r /backend/requirements/base.txt
COPY . /zango/
RUN cd backend && pip install .
