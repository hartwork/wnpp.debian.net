# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import re

import pkg_resources
from django.urls import re_path
from django.views.static import serve

FAVICON_FILES = [
    'android-chrome-36x36.png',
    'android-chrome-48x48.png',
    'android-chrome-72x72.png',
    'android-chrome-96x96.png',
    'apple-touch-icon-114x114.png',
    'apple-touch-icon-120x120.png',
    'apple-touch-icon-57x57.png',
    'apple-touch-icon-60x60.png',
    'apple-touch-icon-72x72.png',
    'apple-touch-icon-76x76.png',
    'apple-touch-icon-precomposed.png',
    'apple-touch-icon.png',
    'browserconfig.xml',
    'favicon-16x16.png',
    'favicon-32x32.png',
    'favicon-96x96.png',
    'favicon.ico',
    'manifest.json',
    'mstile-150x150.png',
    'mstile-310x150.png',
    'mstile-70x70.png',
]

_FAVICON_FILES_PATTERN = '|'.join(re.escape(filename) for filename in FAVICON_FILES)


def favicon_urlpatterns(name='favicon'):
    return [
        re_path('^(?P<path>%s)$' % _FAVICON_FILES_PATTERN,
                serve,
                kwargs={
                    'document_root': pkg_resources.resource_filename('wnpp_debian_net',
                                                                     'static/favicon'),
                },
                name=name),
    ]
