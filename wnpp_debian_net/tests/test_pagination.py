# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from parameterized import parameterized

from ..pagination import ELLIPSIS, iterate_page_items


class PageItemsTest(TestCase):
    @parameterized.expand([
        ('head start', 100, 1, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 99, 100]),
        ('edge of head', 100, 2, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 99, 100]),
        ('edge of head plus 1', 100, 3, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 99, 100]),
        ('edge of head plus 2', 100, 4, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 99, 100]),
        ('edge of head plus 3', 100, 5, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 99, 100]),
        ('edge of head plus 4', 100, 6, [1, 2, ELLIPSIS, 5, 6, 7, 8, ELLIPSIS, 99, 100]),
        ('tail end', 100, 100, [1, 2, ELLIPSIS, 94, 95, 96, 97, 98, 99, 100]),
        ('edge of tail', 100, 99, [1, 2, ELLIPSIS, 94, 95, 96, 97, 98, 99, 100]),
        ('edge of tail minus 1', 100, 98, [1, 2, ELLIPSIS, 94, 95, 96, 97, 98, 99, 100]),
        ('edge of tail minus 2', 100, 97, [1, 2, ELLIPSIS, 94, 95, 96, 97, 98, 99, 100]),
        ('edge of tail minus 3', 100, 96, [1, 2, ELLIPSIS, 94, 95, 96, 97, 98, 99, 100]),
        ('edge of tail minus 4', 100, 95, [1, 2, ELLIPSIS, 94, 95, 96, 97, 98, 99, 100]),
        ('edge of tail minus 5', 100, 94, [1, 2, ELLIPSIS, 93, 94, 95, 96, ELLIPSIS, 99, 100]),
        ('neither near head nor near tail', 100, 33,
         [1, 2, ELLIPSIS, 32, 33, 34, 35, ELLIPSIS, 99, 100]),
    ])
    def test_ellipsis_locations(self, _, num_pages, current_page_number, expected_page_items):
        actual_page_items = iterate_page_items(total_page_count=num_pages,
                                               current_page_number=current_page_number,
                                               max_item_count=10,
                                               ending_item_count=2)
        self.assertEqual(list(actual_page_items), expected_page_items)

    @parameterized.expand([
        (10, 9, True),
        (10, 10, False),
        (10, 11, False),
    ])
    def test_ellipses_needed(self, total_page_count, max_item_count, ellipses_expected):
        current_page_number = 1  # arbitrary
        page_items = iterate_page_items(total_page_count=total_page_count,
                                        current_page_number=current_page_number,
                                        max_item_count=max_item_count,
                                        ending_item_count=2)
        ellipses_found = ELLIPSIS in page_items
        self.assertEqual(ellipses_found, ellipses_expected)

    def test_defaults(self):
        total_page_count = 555  # arbitrary
        current_page_number = 222  # arbitrary
        actual_page_items = list(iterate_page_items(total_page_count, current_page_number))
        self.assertEqual(actual_page_items,
                         [1, 2, ELLIPSIS, 220, 221, 222, 223, 224, ELLIPSIS, 554, 555])
