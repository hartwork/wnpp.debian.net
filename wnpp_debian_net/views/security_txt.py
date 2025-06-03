# Copyright (c) 2024 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from importlib import resources

from django.urls import re_path
from django.views.static import serve


def security_txt_urlpatterns(name="security_txt"):
    return [
        re_path(
            "^(?:\\.well-known/)?(?P<path>security\\.txt)$",
            serve,
            kwargs={
                "document_root": str(
                    resources.files("wnpp_debian_net").joinpath("static", "well-known")
                ),
            },
            name=name,
        ),
    ]
