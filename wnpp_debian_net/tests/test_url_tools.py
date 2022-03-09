# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from parameterized import parameterized

from ..url_tools import url_with_query


class UrlForkeyTest(TestCase):

    @parameterized.expand([
        ('/hello', '/hello?key=3'),
        ('/hello?other=1', '/hello?other=1&key=3'),
        ('/hello?other=1&other=2', '/hello?other=1&other=2&key=3'),
        ('/hello?key=5', '/hello?key=3'),
        ('/hello?key=5&other=1&other=2', '/hello?key=3&other=1&other=2'),
        ('/hello?other=1&key=5&other=2', '/hello?other=1&key=3&other=2'),
        ('/hello?other=1&other=2&key=5', '/hello?other=1&other=2&key=3'),
    ])
    def test_url_with_query(self, current_url, expected_url):
        actual_url = url_with_query(current_url, key=3)
        self.assertEqual(actual_url, expected_url)
