#! /usr/bin/env bash
# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

PS4='# '
set -e
set -u
set -x

wait-for-it --service "${WDN_MYSQL_HOST}:${WDN_MYSQL_PORT}"

if [[ $# -gt 0 ]]; then
    if [[ $1 = test ]]; then
        ./manage.py test "${@:2}"
        exit 0
    else
        exec "$@"
    fi
fi

./manage.py migrate

gunicorn_args=(
    --name=wnpp-debian-net
    --bind=0.0.0.0:52080
    --workers="$(nproc --ignore=1)"
    --timeout 5
    --access-logfile=-
    --access-logformat '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    --logger-class=gunicorn_color.Logger
    wnpp_debian_net.wsgi
)
exec gunicorn "${gunicorn_args[@]}"
