# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.template import Library

from ..url_tools import url_with_query

register = Library()


@register.simple_tag(takes_context=True)
def url_for_page(context, page_number):
    """
    Produces the current request URLs with `[?&]page=<page_number>` applied
    """
    url = context['request'].get_full_path()
    return url_with_query(url, page=page_number)
