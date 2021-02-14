# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.http import FileResponse
from django.templatetags.static import static
from django.test import TestCase
from parameterized import parameterized


class StaticFilesTest(TestCase):
    @parameterized.expand([
        ('our own', 'images/feed-icon.png'),
        ('third party', 'admin/css/nav_sidebar.css'),
    ])
    def test_file_served_properly(self, _label, path):
        url = static(path)
        response = self.client.get(url)
        self.assertIsInstance(response, FileResponse)
