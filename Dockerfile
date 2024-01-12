FROM python:3.10
RUN  apt-get update
RUN  apt-get install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl
COPY . /zelthy/
WORKDIR /zelthy/
RUN cd backend && pip install .