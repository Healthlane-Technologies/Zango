ARG ZANGO_IMAGE_NAME=kczelthy/zango
ARG ZANGO_IMAGE_TAG=latest

FROM ${ZANGO_IMAGE_NAME}:${ZANGO_IMAGE_TAG}

RUN apt update
RUN pip install gunicorn
RUN apt-get install -y net-tools
RUN apt install ffmpeg -y

ARG HOST_UID
ARG HOST_GID

# Update the package list, install sudo, create a non-root user, and grant password-less sudo permissions
RUN apt update && \
    apt install -y sudo && \
    groupadd -o -g ${HOST_GID} -r zango_user && \
    adduser --uid $HOST_UID --gid $HOST_GID --disabled-password --gecos "" zango_user && \
    echo 'zango_user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set the non-root user as the default user
USER zango_user

COPY init.sh /zango/
COPY start_flower.sh /zango/
WORKDIR /zango/
CMD ["/bin/sh", "init.sh"]
