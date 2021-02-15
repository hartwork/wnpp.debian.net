# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from unittest import TestCase

from parameterized import parameterized

from ...templatetags.contact_links import _parse_contact
from ..contact_links import contact_link_for


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


class ContactLinkForTest(TestCase):
    @parameterized.expand([
        (None, '<i>nobody</i>'),
        ('', '<i>nobody</i>'),
        ('no at sign in sight', '<i>no at sign in sight</i>'),
        ('Some Thing <wellformed@example.org>',
         '<a href="mailto:wellformed@example.org">Some Thing</a>'),
        ('just@example.org', '<a href="mailto:just@example.org">just@example.org</a>'),
    ])
    def test_contact_link_for(self, contact, expected_html):
        actual_html = contact_link_for(contact)
        self.assertEqual(actual_html, expected_html)
