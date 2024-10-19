# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import re

from django import template

from ..url_tools import url_with_query

register = template.Library()

INTERNAL_DIRECTION_PREFIX_ASCENDING = ""
INTERNAL_DIRECTION_PREFIX_DESCENDING = "-"

EXTERNAL_DIRECTION_SUFFIX_ASCENDING = "/asc"
EXTERNAL_DIRECTION_SUFFIX_DESCENDING = "/desc"

_OPPOSITE_INTERNAL_PREFIX = {
    INTERNAL_DIRECTION_PREFIX_ASCENDING: INTERNAL_DIRECTION_PREFIX_DESCENDING,
    INTERNAL_DIRECTION_PREFIX_DESCENDING: INTERNAL_DIRECTION_PREFIX_ASCENDING,
}

_EXTERNAL_SUFFIX_FOR = {
    INTERNAL_DIRECTION_PREFIX_ASCENDING: EXTERNAL_DIRECTION_SUFFIX_ASCENDING,
    INTERNAL_DIRECTION_PREFIX_DESCENDING: EXTERNAL_DIRECTION_SUFFIX_DESCENDING,
}


def parse_sort_param(sort_param) -> tuple[str, str]:
    # NOTE: Semicolon (";") is only supported here to keep existing links working.
    #       Some browsers interpret it as a separator of query parameters because of
    #       https://www.w3.org/TR/1999/REC-html401-19991224/appendix/notes.html#h-B.2.2
    #       and some don't; so at least we no longer _produce_ links like that any more.
    split_sort_param = re.split("[;/]", sort_param)
    if len(split_sort_param) == 2 and split_sort_param[1] == "desc":
        order = INTERNAL_DIRECTION_PREFIX_DESCENDING
    else:
        order = INTERNAL_DIRECTION_PREFIX_ASCENDING
    return split_sort_param[0], order


def combine_sort_param(column, internal_direction_prefix):
    return column + _EXTERNAL_SUFFIX_FOR[internal_direction_prefix]


@register.simple_tag(takes_context=True)
def self_url_with_sorting_for(context, future_column):
    """
    Takes the current page URL and adjusts the "sort=[..]" part
    in the query parameters to sort for a specific column.
    If the column is the same as the current one,
    direction is flipped: from ascending to descending and back.
    """
    url = context["request"].get_full_path()
    current_column, internal_direction_prefix = parse_sort_param(context["sort"])

    if future_column == current_column:
        internal_direction_prefix = _OPPOSITE_INTERNAL_PREFIX[internal_direction_prefix]

    future_sort = combine_sort_param(future_column, internal_direction_prefix)

    return url_with_query(url, sort=future_sort, page=1)
