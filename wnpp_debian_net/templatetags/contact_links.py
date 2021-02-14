# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from typing import Optional
from django import template
from django.utils import safestring
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

register = template.Library()

def _truncate(value: str, length: int) -> str:
    if length is None:
        return value
    return Truncator(value).chars(length)


@register.simple_tag
def contact_link_for(contact: Optional[str], truncatechars:int =None) -> safestring:
    if not contact:
        return mark_safe('<i>nobody</i>')

    split_up = contact.rsplit(' ', maxsplit=1)
    if len(split_up) == 1:
        display = _truncate(contact, truncatechars)
        return format_html('<a href="mailto:{}">{}</a>', contact, display)
    elif len(split_up) == 2:
        display, angled_address = split_up
        display = _truncate(display.strip('"').replace('<', '').replace('>', ''),
                            truncatechars)
        address = angled_address.replace('<', '').replace('>', '')
        return format_html('<a href="mailto:{}">{}</a>', address, display)
    else:
        display = _truncate(contact, truncatechars)
        return format_html('<i>{}</i>', display)
