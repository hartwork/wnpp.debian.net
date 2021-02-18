# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import json
from io import StringIO

from vcr_unittest import VCRTestCase

from ....tests.test_debbugs import EXPECTED_PROPERTIES_OF_ISSUE, ISSUE_IDS_OF_INTEREST
from ..inspectdebbugs import Command


class InspectDebbugsCommandTest(VCRTestCase):
    @staticmethod
    def with_issue_ids_decoded_to_int(properties_of_issues):
        # NOTE: Dictionaries can only have string keys in JSON
        return {int(k): v for k, v in properties_of_issues.items()}

    def test(self):
        stdout = StringIO()
        command = Command(stdout=stdout)

        command.handle(issue_ids=ISSUE_IDS_OF_INTEREST)

        actual_properties_of_issues = self.with_issue_ids_decoded_to_int(
            json.loads(stdout.getvalue()))
        self.assertEqual(actual_properties_of_issues, EXPECTED_PROPERTIES_OF_ISSUE)
