FROM zelthy3:latest

RUN pip install gunicorn
COPY ${PROJECT_NAME}/workspaces/ /zelthy/temp_workspace/
COPY init.sh /zelthy/
COPY config/gunicorn.conf.py /zelthy/temp_config/
WORKDIR /zelthy/
CMD ["/bin/sh", "init.sh"]