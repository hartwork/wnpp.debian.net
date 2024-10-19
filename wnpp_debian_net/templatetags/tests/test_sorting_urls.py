# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase
from urllib.parse import parse_qs, urlparse

from django.test import RequestFactory
from parameterized import parameterized

from ...templatetags.sorting_urls import self_url_with_sorting_for


class SortingUrlsTest(TestCase):
    @parameterized.expand(
        [
            ("/hello", "/hello?sort=col1%2Fasc&page=1"),
            ("/hello?page=3", "/hello?page=1&sort=col1%2Fasc"),
            ("/hello?sort=col1", "/hello?sort=col1%2Fdesc&page=1"),
            ("/hello?sort=col1%2Fasc", "/hello?sort=col1%2Fdesc&page=1"),
            ("/hello?sort=col1%3Basc", "/hello?sort=col1%2Fdesc&page=1"),
            ("/hello?sort=col1%2Fdesc", "/hello?sort=col1%2Fasc&page=1"),
            ("/hello?sort=col1%3Bdesc", "/hello?sort=col1%2Fasc&page=1"),
            ("/hello?sort=col4", "/hello?sort=col1%2Fasc&page=1"),
        ]
    )
    def test_resets_page_to_1(self, current_page_url, expected_url):
        current_sort_value = parse_qs(urlparse(current_page_url).query).get("sort", ["project"])[0]
        context = {
            "sort": current_sort_value,
            "request": RequestFactory().get(current_page_url),
        }

        actual_url = self_url_with_sorting_for(context, future_column="col1")

        self.assertEqual(actual_url, expected_url)
