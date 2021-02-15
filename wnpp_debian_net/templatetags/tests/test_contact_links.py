# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from parameterized import parameterized

from ...templatetags.contact_links import _parse_contact


class ParseContactTest(TestCase):
    @parameterized.expand([
        ('mail@example.org', 'mail@example.org'),
        ('"First Middle Last" <mail@example.org>', 'First Middle Last'),
        ('First Middle Last <mail@example.org>', 'First Middle Last'),
    ])
    def test_parse_contact(self, contact, expected_display):
        actual_mailto, actual_display = _parse_contact(contact)
        self.assertEqual(actual_mailto, 'mail@example.org')
        self.assertEqual(actual_display, expected_display)
