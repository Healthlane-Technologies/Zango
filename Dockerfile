FROM python:3.10

RUN apt-get update && apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl

WORKDIR /zango
COPY backend/requirements/base.txt /zango/backend/requirements/base.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /zango/backend/requirements/base.txt

COPY . /zango/

RUN --mount=type=cache,target=/root/.cache/pip \
    cd backend && pip install .
