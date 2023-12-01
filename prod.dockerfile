FROM zelthy3:latest

RUN pip install gunicorn
COPY ${PROJECT_NAME} /zelthy/${PROJECT_NAME}
COPY init.sh /zelthy/
COPY config/gunicorn.conf.py /zelthy/${PROJECT_NAME}
WORKDIR /zelthy/
CMD ["/bin/sh", "init.sh"]