FROM kczelthy/zelthy3:0.1.0

RUN pip install gunicorn
WORKDIR /zelthy/
CMD ["/bin/sh", "init.sh"]