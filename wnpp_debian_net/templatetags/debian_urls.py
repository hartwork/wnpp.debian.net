# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django import template

register = template.Library()

@register.simple_tag
def wnpp_issue_url(issue_id):
    return f'https://bugs.debian.org/cgi-bin/bugreport.cgi?bug={issue_id}'
