FROM python:3.10
RUN  apt-get update
RUN  apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl
COPY backend/requirements/base.txt /
RUN pip install -r base.txt
COPY . /zcore/
WORKDIR /zcore/
RUN cd backend && pip install .