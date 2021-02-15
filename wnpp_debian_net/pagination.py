# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later
#
# 7dda3eab17f495d5b972fc8c67e69d47c12aedb4347116d1443778b05e7839c4

from typing import Optional

_DEFAULT_MAX_ITEM_COUNT = 11
_DEFAULT_ENDING_ITEM_COUNT = 2

ELLIPSIS = None


def iterate_page_items(total_page_count: int,
                       current_page_number: int,
                       max_item_count: Optional[int] = None,
                       ending_item_count: Optional[int] = None):
    """
    Calculates where to put ellipses (omission markers) in a
    sequence of page items to keep the number of page items
    at no more than ``max_items`` items.

    >>> iterate_page_items(100, 94, 10, 2)
    [1, 2, None, 93, 94, 95, 96, None, 99, 100]
    """
    if not 1 <= current_page_number <= total_page_count:
        raise ValueError(f'Page {current_page_number} is not within range 1 to {total_page_count}')

    if max_item_count is None:
        max_item_count = _DEFAULT_MAX_ITEM_COUNT

    if ending_item_count is None:
        ending_item_count = _DEFAULT_ENDING_ITEM_COUNT

    # The formula is: item ending count items plus 1 for the ellipsis,
    #                 that times 2 for both sides,
    #                 plus 1 for the item with the current page
    min_expected_max_item_count = (ending_item_count + 1) * 2 + 1
    if max_item_count < min_expected_max_item_count:
        raise ValueError(f'Max item count {max_item_count} needs to be'
                         f' at least {min_expected_max_item_count}'
                         f' (given ending item count {ending_item_count})')

    if total_page_count <= max_item_count:
        yield from range(1, total_page_count + 1)
        return

    number_of_items_surrounding_current = (max_item_count - 2 * (ending_item_count + 1) - 1)
    assert number_of_items_surrounding_current >= 0
    items_before_current = number_of_items_surrounding_current // 2
    items_after_current = number_of_items_surrounding_current - items_before_current
    middle_first_page = current_page_number - items_before_current
    middle_last_page = current_page_number + items_after_current

    head_trouble = middle_first_page <= ending_item_count + 1 + 1
    tail_trouble = middle_last_page >= total_page_count - ending_item_count - 1

    if head_trouble:
        yield from range(1, max_item_count - (ending_item_count + 1) + 1)
        yield ELLIPSIS
        yield from range(total_page_count - (ending_item_count - 1), total_page_count + 1)
    elif tail_trouble:
        yield from range(1, ending_item_count + 1)
        yield ELLIPSIS
        yield from range(total_page_count - max_item_count + ending_item_count + 1 + 1,
                         total_page_count + 1)
    else:
        yield from range(1, ending_item_count + 1)
        yield ELLIPSIS
        yield from range(middle_first_page, middle_last_page + 1)
        yield ELLIPSIS
        yield from range(total_page_count - (ending_item_count - 1), total_page_count + 1)
