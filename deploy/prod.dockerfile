FROM kczelthy/zango:0.3.0rc1

RUN apt update
RUN pip install gunicorn
RUN apt-get install -y net-tools
RUN apt install ffmpeg -y

ARG UID
ARG GID

# Update the package list, install sudo, create a non-root user, and grant password-less sudo permissions
RUN apt update && \
    apt install -y sudo && \
    groupadd -o -g ${GID} -r zango_user && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" zango_user && \
    echo 'zango_user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set the non-root user as the default user
USER zango_user

COPY init.sh /zango/
WORKDIR /zango/
CMD ["/bin/sh", "init.sh"]