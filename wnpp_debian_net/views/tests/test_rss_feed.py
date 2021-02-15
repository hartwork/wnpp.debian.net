# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from operator import attrgetter

from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from ...models import DebianLogIndex, EventKind, IssueKind
from ...tests.factories import DebianLogIndexFactory
from ..rss_feed import _MAX_ENTRIES, _DataSet


class WnppNewsFeedTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.entries = []
        cls.entry_for_event_kind_for_issue_kind: dict[str, dict[str, DebianLogIndex]] = {}
        for issue_kind in IssueKind.values:
            for event_kind in EventKind.values:
                entry = DebianLogIndexFactory(event=event_kind, kind=issue_kind)
                cls.entries.append(entry)
                cls.entry_for_event_kind_for_issue_kind.setdefault(issue_kind,
                                                                   {})[event_kind] = entry
        cls.url = reverse('news')

    @staticmethod
    def _most_recent(entries):
        return sorted(entries, key=attrgetter('event_stamp'), reverse=True)[:_MAX_ENTRIES]

    @parameterized.expand([
        ('all', _DataSet.ALL.value),
        ('default', None),
        ('invalid', 'something invalid'),
    ])
    def test_entries(self, _label, dataset):
        data = {}
        if dataset is not None:
            data['data'] = dataset
        expected_object_list = self._most_recent(self.entries)

        response = self.client.get(self.url, data)

        actual_object_list = list(response.context_data['object_list'])
        self.assertEqual(actual_object_list, expected_object_list)

    def test_entries__bad_news(self):
        data = {'data': _DataSet.BAD_NEWS.value}
        good_news = (
            (EventKind.CLOSED.value, IssueKind.ITA.value),
            (EventKind.CLOSED.value, IssueKind.ITP.value),
            (EventKind.CLOSED.value, IssueKind.O_.value),
            (EventKind.CLOSED.value, IssueKind.RFA.value),
            (EventKind.CLOSED.value, IssueKind.RFH.value),
            (EventKind.CLOSED.value, IssueKind.RFP.value),
            (EventKind.MODIFIED.value, IssueKind.ITA.value),
            (EventKind.MODIFIED.value, IssueKind.ITP.value),
            (EventKind.OPENED.value, IssueKind.ITA.value),
            (EventKind.OPENED.value, IssueKind.ITP.value),
        )
        expected_object_list = self._most_recent(entry for entry in self.entries
                                                 if (entry.event, entry.kind) not in good_news)

        response = self.client.get(self.url, data)

        actual_object_list = list(response.context_data['object_list'])
        self.assertEqual(actual_object_list, expected_object_list)

    def test_entries__good_news(self):
        data = {'data': _DataSet.GOOD_NEWS.value}
        good_news = (
            (EventKind.CLOSED, IssueKind.ITA),
            (EventKind.CLOSED, IssueKind.ITP),
            (EventKind.CLOSED, IssueKind.O_),
            (EventKind.CLOSED, IssueKind.RFA),
            (EventKind.CLOSED, IssueKind.RFH),
            (EventKind.CLOSED, IssueKind.RFP),
            (EventKind.MODIFIED, IssueKind.ITA),
            (EventKind.MODIFIED, IssueKind.ITP),
            (EventKind.OPENED, IssueKind.ITA),
            (EventKind.OPENED, IssueKind.ITP),
        )
        expected_object_list = self._most_recent(
            self.entry_for_event_kind_for_issue_kind[issue_kind.value][event_kind.value]
            for event_kind, issue_kind in good_news)

        response = self.client.get(self.url, data)

        actual_object_list = list(response.context_data['object_list'])
        self.assertEqual(actual_object_list, expected_object_list)

    def test_entries__help_existing(self):
        data = {'data': _DataSet.HELP_EXISTING.value}
        help_existing = (
            (EventKind.MODIFIED, IssueKind.O_),
            (EventKind.MODIFIED, IssueKind.RFA),
            (EventKind.MODIFIED, IssueKind.RFH),
            (EventKind.OPENED, IssueKind.O_),
            (EventKind.OPENED, IssueKind.RFA),
            (EventKind.OPENED, IssueKind.RFH),
        )
        expected_object_list = self._most_recent(
            self.entry_for_event_kind_for_issue_kind[issue_kind.value][event_kind.value]
            for event_kind, issue_kind in help_existing)

        response = self.client.get(self.url, data)

        actual_object_list = list(response.context_data['object_list'])
        self.assertEqual(actual_object_list, expected_object_list)

    def test_entries__new_packages(self):
        data = {'data': _DataSet.NEW_PACKAGES.value}
        expected_object_list = [
            self.entry_for_event_kind_for_issue_kind[IssueKind.ITP.value][EventKind.CLOSED.value]
        ]

        response = self.client.get(self.url, data)

        actual_object_list = list(response.context_data['object_list'])
        self.assertEqual(actual_object_list, expected_object_list)
