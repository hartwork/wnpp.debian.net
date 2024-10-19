# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later
import re
from re import Match

from django import template
from django.utils import safestring
from django.utils.html import format_html
from django.utils.text import Truncator

register = template.Library()

_CONTACT_MATCHERS = [
    re.compile(r"^(?P<mailto>[^ ]+@[^ ]+) \((?P<display>.+)\)$"),
    re.compile(r'^"?(?P<display>.+?)"? <(?P<mailto>[^ ]+@[^ ]+)>$'),
    re.compile(r"^(?P<display>(?P<mailto>[^ ]+@[^ ]+))$"),
]


class _UnsupportedContactFormat(ValueError):
    pass


def _truncate(value: str, length: int) -> str:
    if length is None:
        return value
    return Truncator(value).chars(length)


def _parse_contact(contact: str) -> tuple[str | None, str]:
    for matcher in _CONTACT_MATCHERS:
        match: Match = matcher.match(contact)
        if match is None:
            continue
        return tuple(match.group(group) for group in ("mailto", "display"))
    raise _UnsupportedContactFormat(contact)


@register.simple_tag
def contact_link_for(contact: str | None, truncatechars: int = None) -> safestring:
    mailto = None
    if not contact:
        display = "nobody"
    else:
        try:
            mailto, display = _parse_contact(contact)
        except _UnsupportedContactFormat:
            display = contact
        display = _truncate(display, truncatechars)

    if mailto is None:
        return format_html("<i>{}</i>", display)
    else:
        return format_html('<a href="mailto:{}">{}</a>', mailto, display)
