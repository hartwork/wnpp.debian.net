# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from typing import Optional

from django import template
from django.utils import safestring
from django.utils.html import format_html
from django.utils.text import Truncator

register = template.Library()


def _truncate(value: str, length: int) -> str:
    if length is None:
        return value
    return Truncator(value).chars(length)


def _parse_contact(contact: str) -> tuple[Optional[str], str]:
    split_up = contact.rsplit(' ', maxsplit=1)

    if len(split_up) == 1:
        mailto = contact
        display = contact
    elif len(split_up) == 2:
        display, angled_address = split_up
        display = display.strip('"').replace('<', '').replace('>', '')
        mailto = angled_address.replace('<', '').replace('>', '')
    else:
        mailto = None
        display = contact

    return mailto, display


@register.simple_tag
def contact_link_for(contact: Optional[str], truncatechars: int = None) -> safestring:
    if not contact:
        mailto, display = None, 'nobody'
    else:
        mailto, display = _parse_contact(contact)
        display = _truncate(display, truncatechars)

    if mailto is None:
        return format_html('<i>{}</i>', display)
    else:
        return format_html('<a href="mailto:{}">{}</a>', mailto, display)
