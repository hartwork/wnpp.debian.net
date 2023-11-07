#! /usr/bin/env bash
# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

PS4='# '
set -e
set -u
set -x

wait-for-it --service "${WDN_POSTGRES_HOST}:${WDN_POSTGRES_PORT}"

if [[ $# -gt 0 ]]; then
    if [[ $1 = test ]]; then
        coverage run -a ./manage.py test "${@:2}"
        coverage run -a ./manage.py validate_templates -v3 \
                --ignore-app django_extensions \
                --ignore-app django.contrib.admin \
                --ignore-app django.contrib.auth
        coverage report
        exit 0
    else
        exec "$@"
    fi
fi

./manage.py migrate

gunicorn_args=(
    --name=wnpp-debian-net
    --bind=0.0.0.0:51080
    --workers="$(( $(nproc --ignore=1) + 1 ))"  # i.e. always >=2
    --timeout 5
    --access-logfile=-
    --access-logformat '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    --logger-class=gunicorn_color.Logger
    wnpp_debian_net.wsgi
)
exec gunicorn "${gunicorn_args[@]}"
