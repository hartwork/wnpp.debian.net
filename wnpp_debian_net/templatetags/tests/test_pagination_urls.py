# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from django.test import RequestFactory
from parameterized import parameterized

from ..pagination_urls import url_for_page


class UrlForPageTest(TestCase):
    @parameterized.expand(
        [
            ("/hello", "/hello?page=3"),
            ("/hello?other=1", "/hello?other=1&page=3"),
            ("/hello?page=5", "/hello?page=3"),
        ]
    )
    def test_url_for_page(self, current_url, expected_url):
        page_number = 3  # arbitrary
        context = {
            "request": RequestFactory().get(current_url),
        }

        actual_url = url_for_page(context, page_number)

        self.assertEqual(actual_url, expected_url)
