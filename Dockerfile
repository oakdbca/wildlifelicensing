# syntax = docker/dockerfile:1.4

ARG UBUNTU_IMAGE=ubuntu:24.04

# --- Builder: install OS build deps, create venv, install python deps ---
FROM ${UBUNTU_IMAGE} AS builder

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

# Use Australian mirrors for apt
RUN sed -i 's|archive.ubuntu.com|au.archive.ubuntu.com|g' /etc/apt/sources.list || true

# Install build-time packages. Keep this stage self-contained.
RUN --mount=type=cache,target=/var/cache/apt apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
    build-essential \
    ca-certificates \
    curl \
    git \
    gcc \
    gdal-bin \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    python3.12-venv \
    python3-pip \
    python3-dev \
    patch \
    tzdata \
    wget && \
    rm -rf /var/lib/apt/lists/*

# Create app user early so files can be chown'd during copy
RUN groupadd -g 5000 oim && useradd -g 5000 -u 5000 -s /bin/bash -d /app oim && mkdir -p /app && chown oim:oim /app

WORKDIR /app
USER oim

# Copy only what's needed for pip install (keep .git out)
COPY --chown=oim:oim requirements.txt gunicorn.ini.py manage.py python-cron ./
COPY --chown=oim:oim wildlifelicensing ./wildlifelicensing
COPY --chown=oim:oim startup.sh /

# Create venv and install python deps as the unprivileged user
ENV VIRTUAL_ENV=/app/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH
RUN python3.12 -m venv $VIRTUAL_ENV && \
    $VIRTUAL_ENV/bin/pip install --upgrade pip setuptools wheel && \
    $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

# Collect static (still in builder stage)
RUN touch /app/.env
RUN $VIRTUAL_ENV/bin/python manage.py collectstatic --noinput

# --- Runtime: minimal image with only runtime deps and application artifacts ---
FROM ${UBUNTU_IMAGE} AS runtime

ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set runtime environment defaults (can be overridden at container start)
ENV PRODUCTION_EMAIL=False \
    SECRET_KEY="ThisisNotRealKey" \
    NOTIFICATION_EMAIL="asi@dbca.wa.gov.au" \
    NON_PROD_EMAIL="asi@dbca.wa.gov.au" \
    EMAIL_INSTANCE="UAT" \
    OSCAR_SHOP_NAME="Parks & Wildlife" \
    BPAY_ALLOWED=False

# Install only minimal runtime packages required by wheels in venv
# Upgrade packages to pick up distro security fixes (note: this increases image size)
RUN apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y \
    ca-certificates \
    tzdata \
    wget \
    python3.12 \
    python3.12-venv \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install standard utility scripts (installs /bin/scheduler.py, etc.)
RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh && \
    chmod 755 /tmp/default_script_installer.sh && \
    /tmp/default_script_installer.sh && \
    rm -rf /tmp/*

# Create non-root user to run the app
RUN groupadd -g 5000 oim && useradd -g 5000 -u 5000 -s /bin/bash -d /app oim && mkdir -p /app && chown oim:oim /app

USER oim
WORKDIR /app

# Copy only runtime artifacts from builder
COPY --from=builder --chown=oim:oim /app/venv /app/venv
COPY --from=builder --chown=oim:oim /app/wildlifelicensing /app/wildlifelicensing
COPY --from=builder --chown=oim:oim /app/gunicorn.ini.py /app/gunicorn.ini.py
COPY --from=builder --chown=oim:oim /app/manage.py /app/manage.py
COPY --from=builder --chown=oim:oim /app/.env /app/.env
COPY --from=builder --chown=oim:oim /app/staticfiles_wl /app/staticfiles_wl

# Copy startup script and ensure executable
COPY --from=builder --chown=oim:oim /startup.sh /startup.sh
RUN chmod 0755 /startup.sh || true

ENV PATH=/app/venv/bin:$PATH

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget","-q","-O","-","http://localhost:8080/"]

CMD ["/bin/bash","/startup.sh"]
