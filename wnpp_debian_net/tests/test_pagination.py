# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.template.loader import get_template
from django.test import RequestFactory
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


class PaginationTemplateTest(TestCase):
    ending_item_count = 2  # bigger than 1 and as small as possible
    max_item_count = 9  # minimum given ``ending_item_count = 2``
    items_per_page = 2  # bigger than one, as small as possible
    page_count = max_item_count + 2  # allow for up to two ellipses and as small as possible
    url = '/'  # arbitrary

    def setUp(self) -> None:
        self.paginator = Paginator(object_list=range(self.page_count * self.items_per_page),
                                   per_page=self.items_per_page)
        self.template = get_template('pagination.html')

    @staticmethod
    def _extract_page_page_item_classes(soup):
        def without_class_page_item(it):
            return [clazz for clazz in it if clazz != 'page-item']

        return [without_class_page_item(li_tag['class']) for li_tag in soup.find_all('li')]

    @staticmethod
    def _extract_link_text(soup):
        return [a_tag.string for a_tag in soup.find_all('a')]

    @parameterized.expand([
        (1, [
            ('Previous', ['disabled']),
            ('1', ['active']),
            ('2', []),
            ('3', []),
            ('4', []),
            ('5', []),
            ('6', []),
            ('…', ['disabled']),
            ('10', []),
            ('11', []),
            ('Next', []),
        ], '(1 to 2; 22 total)'),
        (6, [
            ('Previous', []),
            ('1', []),
            ('2', []),
            ('…', ['disabled']),
            ('5', []),
            ('6', ['active']),
            ('7', []),
            ('…', ['disabled']),
            ('10', []),
            ('11', []),
            ('Next', []),
        ], '(11 to 12; 22 total)'),
        (11, [
            ('Previous', []),
            ('1', []),
            ('2', []),
            ('…', ['disabled']),
            ('6', []),
            ('7', []),
            ('8', []),
            ('9', []),
            ('10', []),
            ('11', ['active']),
            ('Next', ['disabled']),
        ], '(21 to 22; 22 total)'),
    ])
    def test(self, current_page, expected_display, expected_summary):
        page_items = iterate_page_items(total_page_count=self.page_count,
                                        current_page_number=current_page,
                                        max_item_count=self.max_item_count,
                                        ending_item_count=self.ending_item_count)
        data = {
            'page': current_page,
        }
        context = {
            'page_items': page_items,
            'page_obj': self.paginator.get_page(current_page),
            'request': RequestFactory().get(self.url, data),
        }

        actual_content = self.template.render(context)

        soup = BeautifulSoup(markup=actual_content, features='html.parser')
        actual_display = list(
            zip(self._extract_link_text(soup), self._extract_page_page_item_classes(soup)))
        self.assertEqual(actual_display, expected_display)
        self.assertIn(expected_summary, actual_content)
