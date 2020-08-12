# Copyright (C) 2018 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

FROM gentoo/stage3-amd64

# Configure portage
RUN echo 'FEATURES="${FEATURES} -news"' >> /etc/portage/make.conf
RUN echo 'EMERGE_DEFAULT_OPTS="--tree --jobs 2 --color y"' \
    >> /etc/portage/make.conf
RUN mkdir -m 0755 -p /usr/portage/metadata/
RUN echo 'masters = gentoo' > /usr/portage/metadata/layout.conf
RUN emerge-webrsync --verbose

# Configure PHP and webserver
RUN echo 'dev-lang/php apache2 mysql soap' \
    > /etc/portage/package.use/dev-lang--php
RUN echo 'app-eselect/eselect-php apache2' \
    > /etc/portage/package.use/app-eselect--eselect-php

# Integrate local overlay with PHP 5.6
COPY overlay.conf  /etc/portage/repos.conf/wnpp-debian-net.conf
COPY overlay/      /var/db/repos/wnpp-debian-net/

RUN emerge \
    dev-lang/php:5.6 \
    www-servers/apache
RUN sed 's,DirectoryIndex.*,DirectoryIndex index.php5,' \
    -i /etc/apache2/modules.d/70_mod_php.conf

# Prepare htdocs
COPY \
    images/ \
    \
    browserconfig.xml \
    config_inc.php5 \
    favicon.ico \
    manifest.json \
    php.ini \
    \
    *.png \
    *.php5 \
    \
    /var/www/localhost/htdocs/
RUN rm /var/www/localhost/htdocs/index.html

# Serve
EXPOSE 80
CMD ["apache2", \
    "-D", "FOREGROUND", \
    "-D", "DEFAULT_VHOST", \
    "-D", "PHP", \
    "-d", "/usr/lib64/apache2", \
    "-f", "/etc/apache2/httpd.conf"]
