# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

FROM python:3.9-alpine

RUN apk add --update \
        bash \
        diffutils \
        gcc \
        mariadb-client \
        mariadb-connector-c-dev \
        musl-dev \
        shadow

RUN useradd --create-home --uid 1001 --non-unique wnpp-debian-net
USER wnpp-debian-net
ENV PATH=/home/wnpp-debian-net/.local/bin/:${PATH}
COPY --chown=wnpp-debian-net:wnpp-debian-net requirements.txt  /home/wnpp-debian-net/

WORKDIR /home/wnpp-debian-net/
RUN pip3 install --user --ignore-installed --disable-pip-version-check pip setuptools wheel \
        && \
    hash pip3 \
        && \
    pip3 install --user -r requirements.txt \
        && \
    pip3 check \
        && \
    bash -c "diff -u0 <(pip freeze | sort -f) <(sed -e '/^#/d' -e '/^$/d' requirements.txt | sort -f)"

COPY docker/entrypoint.sh ./
ENTRYPOINT ["./entrypoint.sh"]
CMD []

COPY --chown=wnpp-debian-net:wnpp-debian-net .coveragerc crontab manage.py  ./
COPY --chown=wnpp-debian-net:wnpp-debian-net wnpp_debian_net/               ./wnpp_debian_net/

USER root
RUN apk upgrade --update
# Enable testing repository for nothing but package "supercronic".
# It's done down here so that we get as little as possible from testing.
RUN echo http://dl-cdn.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories \
        && \
    apk add --update supercronic
USER wnpp-debian-net
