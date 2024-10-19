# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import gzip
import os
from datetime import timedelta
from http import HTTPStatus
from io import StringIO
from tempfile import TemporaryDirectory

import responses
from django.test import TestCase
from pkg_resources import resource_filename

from wnpp_debian_net.models import DebianPopcon
from wnpp_debian_net.tests.factories import DebianPopconFactory

from .. import tests
from ..importpopcon import _BINARY_PACKAGES_POPCON_URL, _SOURCE_PACKAGES_POPCON_URL, Command


class ImportPopconCommandTest(TestCase):
    def _setup(self):  # not using .setUp because of using @responses.activate below
        self._add_response(_BINARY_PACKAGES_POPCON_URL, "by_inst_binary_head_13_tail_4.txt")
        self._add_response(_SOURCE_PACKAGES_POPCON_URL, "by_inst_source_head_15_tail_4.txt")
        expected_binary_packages = ["dpkg", "tar", "zxing-cpp", "zynaddsubfx-dbg"]
        expected_source_packages = ["libreoffice", "libxcb", "zip4j", "zpspell"]
        self.expected_packages = expected_binary_packages + expected_source_packages
        self.expected_values = [
            {
                "package": "dpkg",
                "inst": 204964,
                "vote": 188471,
                "old": 1590,
                "recent": 14877,
                "nofiles": 26,
            },
            {
                "package": "libreoffice",
                "inst": 2939399,
                "vote": 849591,
                "old": 1354049,
                "recent": 439808,
                "nofiles": 295951,
            },
        ]

    def _get_actual_values_from_database(self):
        return list(
            DebianPopcon.objects.filter(
                package__in=[
                    "dpkg",  # i.e. one binary package ..
                    "libreoffice",  # .. and one source package, each
                ]
            )
            .order_by("package")
            .values()
        )

    def _add_response(self, url, body_basename):
        filename = resource_filename(
            tests.__name__, os.path.join("popcon_test_data", body_basename)
        )
        with open(filename, "rb") as f:
            body = gzip.compress(f.read())
        responses.add(responses.GET, url, body=body, status=HTTPStatus.OK)

    @responses.activate
    def test_addition(self):
        self._setup()

        with TemporaryDirectory() as tempdir:
            Command(stdout=StringIO()).handle(download_cache_dir=tempdir)

        self.assertEqual(
            DebianPopcon.objects.filter(package__in=self.expected_packages).count(),
            len(self.expected_packages),
        )
        self.assertEqual(self._get_actual_values_from_database(), self.expected_values)

    @responses.activate
    def test_updating(self):
        self._setup()
        for package in self.expected_packages:
            DebianPopconFactory(package=package)
        self.assertNotEqual(self._get_actual_values_from_database(), self.expected_values)

        with TemporaryDirectory() as tempdir:
            Command(stdout=StringIO()).handle(download_cache_dir=tempdir)

        self.assertEqual(self._get_actual_values_from_database(), self.expected_values)

    @responses.activate
    def test_stale_time_respected(self):
        self._setup()

        with TemporaryDirectory() as tempdir:
            for _label, maximum_stale_delta, expect_nothing_to_do in (
                ("enforce update + fill cache", timedelta(), False),
                ("hit default stale check", None, True),
                ("enforce update despite full cache", timedelta(), False),
            ):
                stdout = StringIO()
                kwargs = {
                    "download_cache_dir": tempdir,
                }
                if maximum_stale_delta is not None:
                    kwargs["maximum_stale_delta"] = maximum_stale_delta

                Command(stdout=stdout).handle(**kwargs)

                assertion = self.assertIn if expect_nothing_to_do else self.assertNotIn
                assertion("Nothing to do", stdout.getvalue())
