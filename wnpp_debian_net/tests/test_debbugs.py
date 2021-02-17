# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from vcr_unittest import VCRTestCase

from ..debbugs import DebbugsWnppClient

ISSUE_IDS_OF_INTEREST = [
    748374,  # solo, not merged with any issues
    842114,  # makes use of base64-encoding
    947640,  # merged with 2 other issues
]

EXPECTED_PROPERTIES_OF_ISSUE = {
    748374: {
        'archived': '0',
        'bug_num': '748374',
        'date': '1400257622',
        'id': '748374',
        'last_modified': '1477645744',
        'location': 'db-h',
        'log_modified': '1477645744',
        'msgid': '<6bd7b587bba3ee12d38e668d828c6749.squirrel@fulvetta.riseup.net>',
        'originator': 'xxxxxx@riseup.net',
        'package': 'wnpp',
        'pending': 'pending',
        'severity': 'wishlist',
        'subject': 'RFP: 0bin -- A client-side encrypted pastebin.'
    },
    842114: {
        'archived': '0',
        'bug_num': '842114',
        'date': '1477435322',
        'id': '842114',
        'last_modified': '1533341524',
        'location': 'db-h',
        'log_modified': '1533341524',
        'msgid': '<147743510730.22072.1439888664069428556.reportbug@localhost>',
        'originator': 'XXXXXXX XXXXXXX <xxxxxxxxxxxxxxxxx@gmail.com>',
        'package': 'wnpp',
        'pending': 'pending',
        'severity': 'wishlist',
        'subject': 'RFP: arblib -- Arb is a C library for arbitrary-precision interval arithmetic, using a midpoint-radius representation (\u201cball arithmetic\u201d). It supports real and complex numbers, polynomials, power series, matrices, and evaluation of many transcendental functions. All operations are done with automatic, rigorous error bounds. The code is thread-safe, portable, and extensively tested.'
    },
    947640: {
        'archived': '0',
        'bug_num': '947640',
        'date': '1577559091',
        'id': '947640',
        'last_modified': '1586036707',
        'location': 'db-h',
        'log_modified': '1586036707',
        'mergedwith': '823061 823266',
        'msgid': '<20191228184026.EA1822E757@disroot.org>',
        'originator': 'XXXXXX XXXXXXX <xxxxxxx@disroot.org>',
        'package': 'wnpp',
        'pending': 'pending',
        'severity': 'normal',
        'subject': 'O: fgetty -- very small, efficient, console-only getty and login'
    }
}


class DebbugsWnppClientTest(VCRTestCase):
    def setUp(self):
        super().setUp()
        self.client = DebbugsWnppClient()
        self.client.connect()

    def test_fetch_issues(self):
        properties_of_issue = self.client.fetch_issues(ISSUE_IDS_OF_INTEREST)

        self.assertEqual(properties_of_issue, EXPECTED_PROPERTIES_OF_ISSUE)

    def test_fetch_ids_of_open_issues(self):
        ids_of_open_issues = self.client.fetch_ids_of_open_issues()

        self.assertEqual(len(ids_of_open_issues), 6256)
        self.assertEqual(ids_of_open_issues[0], 119911)
        self.assertEqual(ids_of_open_issues[-1], 982926)
