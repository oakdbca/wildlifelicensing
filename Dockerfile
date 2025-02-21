# syntax = docker/dockerfile:1.2

FROM ubuntu:24.04 AS builder_base_wildlifelicensing

LABEL maintainer="asi@dbca.wa.gov.au"
LABEL org.opencontainers.image.source="https://github.com/dbca-wa/wildlifelicensing"

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Australia/Perth \
    PRODUCTION_EMAIL=False \
    SECRET_KEY="ThisisNotRealKey" \
    NOTIFICATION_EMAIL="asi@dbca.wa.gov.au" \
    NON_PROD_EMAIL="asi@dbca.wa.gov.au" \
    EMAIL_INSTANCE="UAT" \
    OSCAR_SHOP_NAME="Parks & Wildlife" \
    BPAY_ALLOWED=False

FROM builder_base_wildlifelicensing AS apt_packages_wildlifelicensing

# Use Australian Mirrors
RUN sed 's/archive.ubuntu.com/au.archive.ubuntu.com/g' /etc/apt/sources.list > /etc/apt/sourcesau.list && \
    mv /etc/apt/sourcesau.list /etc/apt/sources.list

RUN --mount=type=cache,target=/var/cache/apt apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
    binutils \
    ca-certificates \
    cron  \
    gcc  \
    gdal-bin \
    git \
    gunicorn \
    gunicorn \
    htop \
    imagemagick \
    libmagic-dev \
    libpq-dev \
    libproj-dev \
    libreoffice \
    mtr \
    patch \
    postgresql-client \
    python3-dev \
    python3-gevent \
    python3-pip \
    python3-setuptools \
    python3-venv \
    rsyslog \
    software-properties-common \
    ssh \
    sudo \
    tzdata \
    vim \
    wget && \
    rm -rf /var/lib/apt/lists/* && \
    update-ca-certificates

FROM apt_packages_wildlifelicensing AS configure_wildlifelicensing

COPY startup.sh /

RUN chmod 755 /startup.sh && \
    chmod +s /startup.sh && \
    groupadd -g 5000 oim && \
    useradd -g 5000 -u 5000 oim -s /bin/bash -d /app && \
    usermod -a -G sudo oim && \
    echo "oim  ALL=(ALL)  NOPASSWD: /startup.sh" > /etc/sudoers.d/oim && \
    mkdir /app && \
    chown -R oim.oim /app && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh && \
    chmod 755 /tmp/default_script_installer.sh && \
    /tmp/default_script_installer.sh && \
    rm -rf /tmp/*

FROM configure_wildlifelicensing AS python_dependencies_wildlifelicensing

WORKDIR /app
USER oim
ENV VIRTUAL_ENV_PATH=/app/venv
ENV PATH=$VIRTUAL_ENV_PATH/bin:$PATH

COPY --chown=oim:oim requirements.txt gunicorn.ini.py manage.py python-cron ./
COPY --chown=oim:oim .git ./.git
COPY --chown=oim:oim wildlifelicensing ./wildlifelicensing

RUN python3.12 -m venv $VIRTUAL_ENV_PATH
RUN $VIRTUAL_ENV_PATH/bin/pip3 install --upgrade pip && \
    $VIRTUAL_ENV_PATH/bin/pip3 install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*

FROM python_dependencies_wildlifelicensing AS collectstatic_wildlifelicensing

RUN touch /app/.env
RUN $VIRTUAL_ENV_PATH/bin/python manage.py collectstatic --noinput

FROM collectstatic_wildlifelicensing AS launch_wildlifelicensing

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
