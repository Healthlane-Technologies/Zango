# Base Production Project Image for Zango
# Creates a complete project structure at build time for ECS deployment

FROM zango:latest

# Install production dependencies
RUN apt update && \
    apt install -y \
    net-tools \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir gunicorn==23.0.0

ARG HOST_UID
ARG HOST_GID

# Create non-root user
RUN apt update && \
    apt install -y sudo && \
    groupadd -o -g ${HOST_GID} -r zango_user && \
    adduser --uid $HOST_UID --gid $HOST_GID --disabled-password --gecos "" zango_user && \
    echo 'zango_user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /zango

# Create the base project structure at build time
# Using --skip-db-setup flag to skip database operations and user/tenant creation
RUN zango start-project zango_project --skip-db-setup

# Copy necessary files
COPY init.sh /zango/
COPY start_flower.sh /zango/
COPY config/gunicorn.conf.py /zango/config/

# Remove .env and workspaces - these will be created at runtime
RUN rm -f /zango/zango_project/.env
RUN rm -rf /zango/zango_project/workspaces

# Set proper permissions
RUN chmod +x /zango/init.sh /zango/start_flower.sh && \
    chown -R zango_user:zango_user /zango

# Switch to non-root user
USER zango_user

# Default command - same as current prod.dockerfile
CMD ["/bin/sh", "/zango/init.sh"]
