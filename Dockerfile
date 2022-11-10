# Prepare the base environment.
FROM ubuntu:20.04 as builder_base_wls
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Australia/Perth
ENV PRODUCTION_EMAIL=False
ENV SECRET_KEY="ThisisNotRealKey"
ENV NOTIFICATION_EMAIL="jawaid.mushtaq@dbca.wa.gov.au"
ENV NON_PROD_EMAIL='jawaid.mushtaq@dbca.wa.gov.au,walter.genuit@dbca.wa.gov.au'
ENV EMAIL_INSTANCE='UAT'
ENV SITE_PREFIX='wildlifelicencing-uat'
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Parks & Wildlife'
ENV BPAY_ALLOWED=False

# Install Python libs from base environment.
RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y

# RUN apt-get install -yq git mercurial gcc gdal-bin libsasl2-dev libpq-dev \
#   python python-setuptools python-dev python-pip \
#   imagemagick poppler-utils \
#   libldap2-dev libssl-dev wget build-essential \
#   libmagic-dev binutils libproj-dev gunicorn tzdata \
#   mtr libevent-dev python-gevent \
#   cron rsyslog iproute2
# RUN pip install --upgrade pip
# RUN apt-get install -yq vim

RUN apt-get install --no-install-recommends -y wget git libmagic-dev gcc \
    binutils libproj-dev gdal-bin python3-setuptools python3-pip tzdata cron \
    rsyslog gunicorn libreoffice
RUN apt-get install --no-install-recommends -y libpq-dev patch
RUN apt-get install --no-install-recommends -y postgresql-client mtr htop \
    vim ssh 
RUN apt-get install --no-install-recommends -y python3-gevent \
    software-properties-common imagemagick gunicorn tzdata

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install --no-install-recommends -y python3.7 python3.7-dev
RUN apt-get install --no-install-recommends -y python3.7 python3.7-dev python3.7-distutils

RUN ln -s /usr/bin/python3.7 /usr/bin/python && \
    rm /usr/bin/pip && \
    ln -s /usr/bin/pip3 /usr/bin/pip
RUN python3.7 -m pip install --upgrade pip
RUN apt-get install -yq vim

# Install Python libs from requirements.txt.
FROM builder_base_wls as python_libs_wls
WORKDIR /app
COPY requirements.txt ./
RUN python3.7 -m pip install --no-cache-dir -r requirements.txt \
  # Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
  # Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
  # && sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python2.7/dist-packages/django/contrib/gis/geos/libgeos.py \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*

COPY libgeos.py.patch /app/
RUN patch /usr/local/lib/python3.7/dist-packages/django/contrib/gis/geos/libgeos.py /app/libgeos.py.patch
RUN rm /app/libgeos.py.patch

# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_wls
COPY gunicorn.ini manage_wl.py ./
#COPY timezone /etc/timezone
RUN echo "Australia/Perth" > /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN touch /app/.env
COPY .git ./.git
#COPY ledger ./ledger
COPY wildlifelicensing ./wildlifelicensing
RUN python manage_wl.py collectstatic --noinput

# upgrade postgresql to v11
#RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 11" > /etc/apt/sources.list.d/pgsql.list
#RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main 11" > /etc/apt/sources.list.d/pgsql.list
#RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
#RUN apt update && apt install -y lsb-release postgresql-11 postgresql-client

RUN mkdir /app/tmp/
RUN chmod 777 /app/tmp/

COPY cron /etc/cron.d/dockercron
COPY startup.sh /
# Cron start
RUN service rsyslog start
RUN chmod 0644 /etc/cron.d/dockercron
RUN crontab /etc/cron.d/dockercron
RUN touch /var/log/cron.log
RUN service cron start
RUN chmod 755 /startup.sh
# cron end

# IPYTHONDIR - Will allow shell_plus (in Docker) to remember history between sessions
RUN export IPYTHONDIR=/app/logs/.ipython/

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
#CMD ["gunicorn", "wildlifecompliance.wsgi", "--bind", ":8080", "--config", "gunicorn.ini"]
