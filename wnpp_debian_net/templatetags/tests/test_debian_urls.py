# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from ..debian_urls import wnpp_issue_url


class DebianUrlsTest(TestCase):
    def test_wnpp_issue_url(self):
        self.assertEqual(
            wnpp_issue_url(748374), "https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=748374"
        )
