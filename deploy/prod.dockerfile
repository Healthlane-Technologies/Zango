FROM kczelthy/zelthy3:latest

RUN pip install gunicorn
WORKDIR /zelthy/
CMD ["/bin/sh", "init.sh"]