# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from ...models import DebianLogIndex
from ...views.rss_feed import DEFAULT_MAX_ENTRIES, NewsDataSet, WnppNewsFeedView
from ._common import ReportingMixin


class Command(ReportingMixin, BaseCommand):
    help = 'Delete log entries that are not needed to serve any of the RSS feeds'

    @staticmethod
    def _get_ids_of_log_entries_used_by_rss_feed(spare_count) -> set[str]:
        ids_of_log_entries_to_keep: set[str] = set()
        for dataset in NewsDataSet:
            feed_view = WnppNewsFeedView(data_set=dataset.value, max_entries=spare_count)
            ids_of_log_entries_to_keep |= set(feed_view.items().values_list('log_id', flat=True))
        return ids_of_log_entries_to_keep

    def _truncate_change_log(self, spare_count):
        starting_at = now()

        with transaction.atomic():
            ids_of_log_entries_to_keep = self._get_ids_of_log_entries_used_by_rss_feed(spare_count)
            _, deletion_details = (DebianLogIndex.objects.exclude(
                log_id__in=ids_of_log_entries_to_keep).filter(event_stamp__lt=starting_at,
                                                              log_stamp__lt=starting_at).delete())

        count_deleted = deletion_details.get(DebianLogIndex._meta.label, 0)
        if count_deleted:
            self._success(f'Deleted {count_deleted} log entries')
        else:
            self._notice('No log entries to delete')

    def add_arguments(self, parser):
        parser.add_argument('--spare',
                            dest='spare_count',
                            metavar='COUNT',
                            type=int,
                            default=DEFAULT_MAX_ENTRIES)

    def handle(self, *args, **options):
        self._truncate_change_log(options['spare_count'])
