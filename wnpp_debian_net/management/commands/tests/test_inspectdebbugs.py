# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import json
from io import StringIO

from vcr_unittest import VCRTestCase

from ....tests.test_debbugs import EXPECTED_PROPERTIES_OF_ISSUE, ISSUE_IDS_OF_INTEREST
from ..inspectdebbugs import Command


class InspectDebbugsCommandTest(VCRTestCase):
    def test(self):
        stdout = StringIO()
        command = Command(stdout=stdout)

        command.handle(issue_ids=ISSUE_IDS_OF_INTEREST)

        # NOTE: Dictionaries can only have string keys in JSON
        actual_properties_of_issues = {int(k): v for k, v in json.loads(stdout.getvalue()).items()}
        self.assertEqual(actual_properties_of_issues, EXPECTED_PROPERTIES_OF_ISSUE)
