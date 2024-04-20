# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

FROM python:3.12-alpine

RUN echo '@edge-community https://dl-cdn.alpinelinux.org/alpine/edge/community' >> /etc/apk/repositories \
        && \
    apk add --update \
        bash \
        diffutils \
        g++ \
        gcc \
        musl-dev \
        postgresql-client \
        postgresql-dev \
        shadow \
        supercronic@edge-community

SHELL ["/bin/bash", "-c"]
RUN useradd --create-home --uid 1001 --non-unique wnpp-debian-net
USER wnpp-debian-net
ENV PATH=/home/wnpp-debian-net/.local/bin/:${PATH}
COPY --chown=wnpp-debian-net:wnpp-debian-net requirements*.txt  /home/wnpp-debian-net/

WORKDIR /home/wnpp-debian-net/
RUN pip3 install --user --ignore-installed --disable-pip-version-check pip setuptools wheel \
        && \
    hash pip3 \
        && \
    pip3 install --user --require-hashes -r requirements.txt \
        && \
    pip3 check \
        && \
    diff -u0 \
            <(sed -e '/--hash=/d' -e 's/ \\$//' -e '/^#/d' -e '/^$/d' requirements-*.txt | sort -f) \
            <(pip3 freeze | sed -e '/^setuptools==/d' -e '/^wheel==/d' | sort -f)

COPY docker/entrypoint.sh ./
ENTRYPOINT ["./entrypoint.sh"]
CMD []

COPY --chown=wnpp-debian-net:wnpp-debian-net .coveragerc crontab manage.py  ./
COPY --chown=wnpp-debian-net:wnpp-debian-net wnpp_debian_net/               ./wnpp_debian_net/

USER root
RUN apk upgrade --update
USER wnpp-debian-net
