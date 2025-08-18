FROM python:3.10-bookworm
RUN  apt-get update && apt-get install -y libxml2-dev \
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
    cabextract xfonts-utils && \
    mkdir -p /usr/share/fonts/truetype/msttcore && \
    cd /usr/share/fonts/truetype/msttcore && \
    wget https://downloads.sourceforge.net/corefonts/arial32.exe && \
    cabextract -F '*.ttf' arial32.exe && \
    fc-cache -fv && \
    rm arial32.exe \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.0g-2ubuntu4_amd64.deb && \
    dpkg -i libssl1.1_1.1.0g-2ubuntu4_amd64.deb && \
    rm libssl1.1_1.1.0g-2ubuntu4_amd64.deb

# Download and install wkhtmltopdf from an alternative source
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb && \
    apt-get install -f -y && \
    rm wkhtmltox_0.12.6-1.buster_amd64.deb
    

WORKDIR /zango
# ref: https://docs.docker.com/build/cache/
RUN pip install --upgrade 'sentry-sdk[django]'
COPY backend/requirements/base.txt /backend/requirements/base.txt
RUN pip install -r /backend/requirements/base.txt
COPY backend /zango/backend
RUN cd backend && pip install .
RUN rm -rf /zango/backend
