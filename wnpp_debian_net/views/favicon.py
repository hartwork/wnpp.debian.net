# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import re
from importlib import resources

from django.urls import re_path
from django.views.static import serve

FAVICON_FILES = [
    "android-chrome-144x144.png",
    "android-chrome-192x192.png",
    "android-chrome-256x256.png",
    "android-chrome-36x36.png",
    "android-chrome-384x384.png",
    "android-chrome-48x48.png",
    "android-chrome-512x512.png",
    "android-chrome-72x72.png",
    "android-chrome-96x96.png",
    "apple-touch-icon-114x114-precomposed.png",
    "apple-touch-icon-114x114.png",
    "apple-touch-icon-120x120-precomposed.png",
    "apple-touch-icon-120x120.png",
    "apple-touch-icon-144x144-precomposed.png",
    "apple-touch-icon-144x144.png",
    "apple-touch-icon-152x152-precomposed.png",
    "apple-touch-icon-152x152.png",
    "apple-touch-icon-180x180-precomposed.png",
    "apple-touch-icon-180x180.png",
    "apple-touch-icon-57x57-precomposed.png",
    "apple-touch-icon-57x57.png",
    "apple-touch-icon-60x60-precomposed.png",
    "apple-touch-icon-60x60.png",
    "apple-touch-icon-72x72-precomposed.png",
    "apple-touch-icon-72x72.png",
    "apple-touch-icon-76x76-precomposed.png",
    "apple-touch-icon-76x76.png",
    "apple-touch-icon-precomposed.png",
    "apple-touch-icon.png",
    "browserconfig.xml",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "favicon-96x96.png",
    "favicon.ico",
    "mstile-144x144.png",
    "mstile-150x150.png",
    "mstile-310x150.png",
    "mstile-310x310.png",
    "mstile-70x70.png",
    "safari-pinned-tab.svg",
    "site.webmanifest",
]

_FAVICON_FILES_PATTERN = "|".join(re.escape(filename) for filename in FAVICON_FILES)


def favicon_urlpatterns(name="favicon"):
    return [
        re_path(
            "^(?P<path>%s)$" % _FAVICON_FILES_PATTERN,
            serve,
            kwargs={
                "document_root": str(
                    resources.files("wnpp_debian_net").joinpath("static", "favicon")
                ),
            },
            name=name,
        ),
    ]
