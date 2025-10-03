#!/bin/bash

cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 32 | head -n 1 > /app/git_hash

if [ "$ENABLE_CRON" = "True" ];
    then
    echo "Starting Python Cron"
    python /bin/scheduler.py /app/python-cron /app/logs/python-cron.log &
    status=$?
    if [ $status -ne 0 ]; then
        echo "Failed to start cron: $status"
        exit $status
    fi
else
   echo "ENABLE_CRON environment variable not set to True, python cron is not starting."
fi

if [ "$ENABLE_WEB" = "True" ];
    then
    echo "Starting Gunicorn"
    /app/venv/bin/gunicorn  wildlifelicensing.wsgi --bind :8080 --config /app/gunicorn.ini.py
    status=$?
    if [ $status -ne 0 ]; then
    echo "Failed to start gunicorn: $status"
    exit $status
    fi
else
   echo "ENABLE_WEB environment variable not set to True, web server is not starting."
   /bin/bash
fi
