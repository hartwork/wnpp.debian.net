# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import re

from django.conf import settings
from django.contrib.staticfiles.views import serve
from django.urls import re_path


def staticfiles_urlpatterns(prefix=None, name='static'):
    '''
    Fork of django.contrib.staticfiles.urls.staticfiles_urlpatterns
    that supports DEBUG=False, directory listings, and registering
    a name for the view.
    '''
    if prefix is None:
        prefix = settings.STATIC_URL
    return [
        re_path('^%s(?P<path>.*)$' % re.escape(prefix.lstrip('/')),
                serve,
                kwargs={
                    'insecure': not settings.DEBUG,
                    'show_indexes': settings.DEBUG,
                },
                name=name),
    ]
