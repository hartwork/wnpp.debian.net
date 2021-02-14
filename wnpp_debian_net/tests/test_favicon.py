# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.http import FileResponse
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from wnpp_debian_net.favicon import FAVICON_FILES


class FaviconTest(TestCase):
    @parameterized.expand(FAVICON_FILES)
    def test_file_served_properly(self, path):
        url = reverse('favicon', kwargs={'path': path})
        response = self.client.get(url)
        self.assertIsInstance(response, FileResponse)
