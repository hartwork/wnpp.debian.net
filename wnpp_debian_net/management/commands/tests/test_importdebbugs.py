# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import datetime
from io import StringIO
from unittest.mock import Mock

from django.test import TestCase
from django.utils.timezone import now

from ....debbugs import IssueProperty
from ....models import DebianWnpp, IssueKind
from ....tests.factories import DebianWnppFactory
from ..importdebbugs import Command


def _create_mock_debbugs_wnpp_client(issue_ids, properties_of_issues):
    return Mock(fetch_ids_of_issues_with_status=Mock(return_value=issue_ids),
                fetch_issues=Mock(return_value=properties_of_issues))


def _create_wnpp_issue_subject(issue_kind: IssueKind, package_name: str, description):
    return f'{issue_kind.value}: {package_name} -- {description}'


class InspectDebbugsCommandTest(TestCase):

    def setUp(self):
        self.command = Command(stdout=StringIO())
        self.magic_description = '61a1fd27a085e090ed6a13309b319ab130eec98d'  # arbitrary
        self.issue_ids = range(3)  # arbitrary
        self.issue_kind = IssueKind.ITP  # arbitrary
        issue_subject = _create_wnpp_issue_subject(
            self.issue_kind,
            'package1',  # arbitrary
            self.magic_description)
        properties_of_issues = {
            issue_id: {
                IssueProperty.DATE.value: now().timestamp(),  # arbitrary
                IssueProperty.LAST_MODIFIED.value: now().timestamp(),  # arbitrary
                IssueProperty.SUBJECT.value: issue_subject,
            }
            for issue_id in self.issue_ids
        }
        self.mock_client = _create_mock_debbugs_wnpp_client(self.issue_ids, properties_of_issues)

    def _invoke_command(self):
        self.command.handle(client=self.mock_client)

    def test_addition(self):
        self.assertEqual(DebianWnpp.objects.filter(description=self.magic_description).count(), 0)
        self._invoke_command()
        self.assertEqual(
            DebianWnpp.objects.filter(description=self.magic_description).count(),
            len(self.issue_ids))

    def test_removal(self):
        issue_that_was_closed_remotely = DebianWnppFactory(ident=len(self.issue_ids) + 1)
        self.assertNotIn(issue_that_was_closed_remotely.ident, self.issue_ids)  # self-test

        self._invoke_command()

        with self.assertRaises(DebianWnpp.DoesNotExist):
            issue_that_was_closed_remotely.refresh_from_db()

    def test_updating(self):
        a_long_time_ago = now() - datetime.timedelta(days=5000)  # arbitrary
        issues = [
            DebianWnppFactory(ident=issue_id,
                              kind=IssueKind.values[i],
                              description='will be updated',
                              cron_stamp=a_long_time_ago)
            for i, issue_id in enumerate(self.issue_ids)
        ]

        self._invoke_command()

        for issue in issues:
            issue.refresh_from_db()
            self.assertEqual(issue.description, self.magic_description)
            self.assertEqual(issue.kind, self.issue_kind.value)
