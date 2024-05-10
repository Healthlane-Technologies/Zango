FROM zcore:latest

RUN apt-get install net-tools
RUN apt install ffmpeg -y

ARG UID
ARG GID

# Update the package list, install sudo, create a non-root user, and grant password-less sudo permissions
RUN apt update && \
    apt install -y sudo && \
    groupadd -o -g ${GID} -r zcore_user && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" zcore_user && \
    echo 'zcore_user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set the non-root user as the default user
USER zcore_user


COPY init.sh /zcore/
WORKDIR /zcore/
CMD ["/bin/sh", "init.sh"]
