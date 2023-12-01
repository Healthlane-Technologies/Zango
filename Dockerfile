FROM python:3.10

COPY . /zelthy/
WORKDIR /zelthy/
RUN cd backend && pip install .
RUN pip install django_smtp_ssl