# Base Production Project Image for Zango
# Creates a complete project structure at build time for ECS deployment

FROM kczelthy/zango:latest

# Create non-root user
RUN apt update && \
    groupadd -o -g 2048 -r zango_user && \
    adduser --uid 2048 --gid 2048 --disabled-password --gecos "" zango_user && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /zango

# Create the base project structure at build time
# Using --skip-db-setup flag to skip database operations and user/tenant creation
RUN zango start-project zango_project --skip-db-setup

# Copy necessary files
COPY --chown=zango_user:zango_user init.sh /zango/
COPY --chown=zango_user:zango_user start_flower.sh /zango/
COPY --chown=zango_user:zango_user config/gunicorn.conf.py /zango/config/

# Remove .envs - this will be created at runtime
RUN rm -f /zango/.env

# Set proper permissions
RUN chmod +x /zango/init.sh /zango/start_flower.sh
RUN chown -R zango_user:zango_user /zango

# Switch to non-root user
USER zango_user


# Default command - same as current prod.dockerfile
ENTRYPOINT ["/bin/bash", "/zango/init.sh"]
