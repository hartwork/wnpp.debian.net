# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from io import StringIO

from django.test import TestCase

from ....models import DebianLogIndex, EventKind, IssueKind
from ....tests.factories import DebianLogIndexFactory
from ....views.rss_feed import NewsDataSet, WnppNewsFeedView
from ..truncatechangelog import Command


class ChangeLogTruncationTest(TestCase):
    FEED_MAX_ENTRIES = 2

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.entries = []
        for _ in range(cls.FEED_MAX_ENTRIES + 1):
            for issue_kind in IssueKind.values:
                for event_kind in EventKind.values:
                    entry = DebianLogIndexFactory(event=event_kind, kind=issue_kind)
                    cls.entries.append(entry)

        # Self-test: All feeds should be over(!)-satisfied
        for dataset in NewsDataSet:
            feed_view = WnppNewsFeedView(data_set=dataset.value, max_entries=cls.FEED_MAX_ENTRIES)
            print(dataset, feed_view.items().count(), cls.FEED_MAX_ENTRIES)
            assert feed_view.items().count() >= cls.FEED_MAX_ENTRIES

    def test_truncate(self):
        Command(stdout=StringIO()).handle(spare_count=self.FEED_MAX_ENTRIES)

        count_original_entries_left = DebianLogIndex.objects.filter(
            log_id__in=[e.log_id for e in self.entries]).count()
        count_original_entries_deleted = len(self.entries) - count_original_entries_left

        self.assertGreaterEqual(count_original_entries_left, self.FEED_MAX_ENTRIES)
        self.assertGreater(count_original_entries_deleted, 0)
