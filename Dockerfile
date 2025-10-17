# syntax=docker/dockerfile:1
FROM python:3.10-bookworm

# Declare architecture argument
ARG TARGETARCH

# Install dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    net-tools \
    ffmpeg \
    software-properties-common \
    fontconfig \
    libxrender1 \
    libxext6 \
    wget \
    xfonts-base \
    xfonts-75dpi \
    fonts-lato \
    fonts-noto-core \
    fonts-roboto \
    fonts-open-sans \
    cabextract \
    xfonts-utils && \
    mkdir -p /usr/share/fonts/truetype/msttcore && \
    cd /usr/share/fonts/truetype/msttcore && \
    wget https://downloads.sourceforge.net/corefonts/arial32.exe && \
    cabextract -F '*.ttf' arial32.exe && \
    fc-cache -fv && \
    rm arial32.exe && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install libssl1.1 dynamically based on architecture
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        wget http://ports.ubuntu.com/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_arm64.deb; \
    else \
        wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb; \
    fi && \
    dpkg -i libssl1.1_1.1.0g-2ubuntu4_*.deb && \
    rm libssl1.1_1.1.0g-2ubuntu4_*.deb


# Install wkhtmltopdf dynamically based on architecture
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_arm64.deb; \
    else \
        wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb; \
    fi && \
    dpkg -i wkhtmltox_0.12.6-1.buster_*.deb && \
    apt-get install -f -y && \
    rm wkhtmltox_0.12.6-1.buster_*.deb

WORKDIR /zango

# Install Python dependencies
RUN pip install --upgrade 'sentry-sdk[django]'
COPY backend/requirements/base.txt /backend/requirements/base.txt
RUN pip install -r /backend/requirements/base.txt

# Copy backend and install
COPY backend /zango/backend
RUN cd backend && pip install . && cd .. && rm -rf backend
