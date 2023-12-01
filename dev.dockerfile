FROM zelthy3:latest

COPY init.sh /zelthy/
WORKDIR /zelthy/
CMD ["/bin/sh", "init.sh"]

