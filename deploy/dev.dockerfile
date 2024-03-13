FROM kczelthy/zelthy3:latest

RUN apt-get install net-tools

ARG UID
ARG GID

# Update the package list, install sudo, create a non-root user, and grant password-less sudo permissions
RUN apt update && \
    apt install -y sudo && \
    groupadd -o -g ${GID} -r zelthy_user && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" zelthy_user && \
    echo 'zelthy_user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set the non-root user as the default user
USER zelthy_user


COPY init.sh /zelthy/
WORKDIR /zelthy/
CMD ["/bin/sh", "init.sh"]
