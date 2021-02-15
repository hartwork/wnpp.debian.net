# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import datetime
import re
from itertools import islice
from typing import Any, Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import Truncator
from django.utils.timezone import now

from ...debbugs import DebbugsWnppClient, IssueProperty
from ...models import DebianLogIndex, DebianLogMods, DebianWnpp, EventKind
from ._common import ReportingMixin

_BATCH_SIZE = 100
_MAXIMUM_STALE_DELTA = datetime.timedelta(hours=2)


class _MalformedSubject(ValueError):
    pass


class Command(ReportingMixin, BaseCommand):
    help = "Import remote WNPP issues from Debbugs' SOAP service into the local database"

    def _close_all_issues_but(self, ids_of_open_wnpp_issues):
        self._notice('[1/3] Closing issues locally that have been closed remotely...')
        log_entries_to_create: list[DebianLogIndex] = []

        for issue in DebianWnpp.objects.exclude(ident__in=ids_of_open_wnpp_issues).iterator():
            self._notice(f'Detected that issue #{issue.ident} has been as closed, remotely')
            log_entries_to_create.append(
                self._create_log_entry_from(issue, EventKind.CLOSED, now()))

        if log_entries_to_create:
            with transaction.atomic():
                DebianLogIndex.objects.bulk_create(log_entries_to_create)
                self._success(f'Logged closing of {len(log_entries_to_create)} issue(s)')

                DebianWnpp.objects.exclude(ident__in=ids_of_open_wnpp_issues).delete()
                self._success(f'Deleted {len(log_entries_to_create)} issue(s)')
        else:
            self._notice('No existing issues deleted.')

    @staticmethod
    def _is_invalid_in_utf8mb3(codepoint: int) -> bool:
        # These ranges were retrieved by feeding all 0x10ffff code points to MySQL in isolation
        return ((0x80 == codepoint) or (0x82 <= codepoint <= 0x8C) or (0x8E == codepoint)
                or (0x91 <= codepoint <= 0x9C) or (0x9E <= codepoint <= 0x9F)
                or (0x100 <= codepoint <= 0x151) or (0x154 <= codepoint <= 0x15F)
                or (0x162 <= codepoint <= 0x177) or (0x179 <= codepoint <= 0x17C)
                or (0x17F <= codepoint <= 0x191) or (0x193 <= codepoint <= 0x2C5)
                or (0x2C7 <= codepoint <= 0x2DB) or (0x2DD <= codepoint <= 0x2012) or
                (0x2015 <= codepoint <= 0x2017) or (0x201B == codepoint) or (0x201F == codepoint)
                or (0x2023 <= codepoint <= 0x2025) or (0x2027 <= codepoint <= 0x202F)
                or (0x2031 <= codepoint <= 0x2038) or (0x203B <= codepoint <= 0x20AB)
                or (0x20AD <= codepoint <= 0x2121) or (0x2123 <= codepoint))

    @classmethod
    def _fit_utf8mb3(cls, text: Optional[str]) -> Optional[str]:
        """
        MySQL needs charset "utf8mb4" to store 4-byte characters.
        For plain "utf8", we have to pull 4-byte characters characters back into 3-byte range.
        """
        if text is None:
            return None
        return ''.join(
            (f'[U+{ord(c):X}]' if cls._is_invalid_in_utf8mb3(ord(c)) else c) for c in text)

    def _fetch_issues(self, issue_ids: list[int]) -> dict[int, dict[str, str]]:
        flat_issue_ids = ', '.join(str(i) for i in issue_ids)
        self._notice(f'Fetching {len(issue_ids)} issue(s): {flat_issue_ids}...')
        properties_of_issue = self._client.fetch_issues(issue_ids)

        # Mass-replace characters that are potential trouble to MySQL's utf8mb3
        for properties in properties_of_issue.values():
            for k, v in properties.items():
                properties[k] = self._fit_utf8mb3(v)

        return properties_of_issue

    def _add_any_new_issues_from(self, ids_of_remote_open_issues):
        ids_of_issues_already_known_locally = set(
            DebianWnpp.objects.values_list('ident', flat=True))
        ids_of_new_issues_to_create = sorted(
            set(ids_of_remote_open_issues) - ids_of_issues_already_known_locally)
        count_issues_left_to_import = len(ids_of_new_issues_to_create)
        self._notice(
            f'[2/3] Starting to import {count_issues_left_to_import} '
            f'(={len(ids_of_remote_open_issues)}-{len(ids_of_issues_already_known_locally)})'
            ' new remote issue(s) locally...')

        it = iter(ids_of_new_issues_to_create)
        while True:
            issue_ids = list(islice(it, 0, _BATCH_SIZE))
            if not issue_ids:
                break

            self._notice(
                f'Importing next {min(_BATCH_SIZE, count_issues_left_to_import)} issue(s) of {count_issues_left_to_import} left to import...'
            )
            count_issues_left_to_import -= _BATCH_SIZE

            log_entries_to_create: list[DebianLogIndex] = []
            issues_to_create: list[DebianWnpp] = []

            remote_properties_of_issue = self._fetch_issues(issue_ids)

            for issue_id, properties in remote_properties_of_issue.items():
                self._notice(f'Processing upcoming issue {issue_id}...')
                try:
                    issue = DebianWnpp(**self._to_database_keys(issue_id, properties))
                except _MalformedSubject as e:
                    self._error(str(e))
                    continue
                issues_to_create.append(issue)
                log_entries_to_create.append(
                    self._create_log_entry_from(issue, EventKind.OPENED, issue.open_stamp))

            if issues_to_create:
                with transaction.atomic():
                    DebianLogIndex.objects.bulk_create(log_entries_to_create)
                    self._success(
                        f'Logged upcoming creation of {len(log_entries_to_create)} issue(s)')

                    DebianWnpp.objects.bulk_create(issues_to_create)
                    self._success(f'Created {len(issues_to_create)} new issues')
            else:
                self._notice('No new issues created.')

    def _update_stale_existing_issues(self, ids_of_remote_open_issues):
        stale_issues_qs = DebianWnpp.objects.filter(ident__in=ids_of_remote_open_issues,
                                                    cron_stamp__lt=now() - _MAXIMUM_STALE_DELTA)
        count_issues_left_to_update = stale_issues_qs.count()

        self._notice(
            f'[3/3] Starting to apply remote changes to {count_issues_left_to_update} stale local issue(s)...'
        )
        if not count_issues_left_to_update:
            self._notice('No stale issues found, none updated.')
            return

        while True:
            log_entries_to_create: list[DebianLogIndex] = []
            issues_to_update: list[DebianWnpp] = list(
                stale_issues_qs.order_by('cron_stamp', 'ident')[:_BATCH_SIZE])
            if not issues_to_update:
                break

            self._notice(
                f'Updating next {min(_BATCH_SIZE, count_issues_left_to_update)} stale issue(s) of {count_issues_left_to_update} left to update...'
            )
            count_issues_left_to_update -= _BATCH_SIZE

            issue_ids = [issue.ident for issue in issues_to_update]
            issue_fields_to_bulk_update: set[str] = set()  # will be grown as needed
            kind_change_log_details: list[tuple[int, str, str]] = []

            # Fetch remote data
            remote_properties_of_issue = self._fetch_issues(issue_ids)

            # Turn remote data into database instances (to persist later)
            for i, issue in enumerate(issues_to_update):
                self._notice(f'Processing existing issue {issue.ident}...')
                properties = remote_properties_of_issue[issue.ident]

                try:
                    database_field_map = self._to_database_keys(issue.ident, properties)
                except _MalformedSubject as e:
                    self.stderr.write(self.style.ERROR(str(e)))
                    continue

                if database_field_map['kind'] != issue.kind:
                    kind_change_log_details.append((i, issue.kind, database_field_map['kind']))

                fields_that_changed = self._detect_and_report_diff(issue, database_field_map)

                if fields_that_changed:
                    issue_fields_to_bulk_update |= fields_that_changed
                    for field_name in fields_that_changed:
                        setattr(issue, field_name, database_field_map[field_name])
                        log_entries_to_create.append(
                            self._create_log_entry_from(issue, EventKind.MODIFIED,
                                                        issue.mod_stamp))

            with transaction.atomic():
                # Persist log entries
                DebianLogIndex.objects.bulk_create(log_entries_to_create)
                self._success(f'Logged upcoming updates to {len(log_entries_to_create)} issue(s)')

                # Persist kind change extra log entries
                if kind_change_log_details:
                    kind_change_log_entries_to_create: list[DebianLogMods] = []
                    for issue_index, old_kind, new_kind in kind_change_log_details:
                        kind_change_log_entries_to_create.append(
                            DebianLogMods(
                                log=issues_to_update[issue_index],
                                old_kind=old_kind,
                                new_kind=new_kind,
                            ))
                    DebianLogMods.objects.bulk_create(kind_change_log_entries_to_create)
                    self._success(
                        f'Logged upcoming changes in kind of {len(kind_change_log_details)} issue(s)'
                    )
                else:
                    self._notice('No changes in kind recognized.')

                # Persist actual issues
                DebianWnpp.objects.bulk_update(issues_to_update,
                                               fields=issue_fields_to_bulk_update)
                self._success(f'Updated {len(issues_to_update)} existing issues')

    @staticmethod
    def _parse_wnpp_issue_subject(subject) -> tuple[str, str, str]:
        match = re.match(
            '^(?:[Ss]ubject: )?(?P<kind>[A-Z]{1,3}): ?(?P<package>[^ ]+)(?:(?: --| -| —|:) (?P<description>.*))?$',
            subject)
        if match is None:
            raise _MalformedSubject(f'Malformed subject {subject!r}')

        return tuple(match.group(g) for g in ('kind', 'package', 'description'))

    @staticmethod
    def _from_epoch_seconds(epoch_seconds) -> datetime.datetime:
        dt = datetime.datetime.fromtimestamp(epoch_seconds)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    @classmethod
    def _to_database_keys(cls, issue_id: int, issue_properties: dict[str, str]) -> dict[str, Any]:
        _MAX_DESCRIPTION_LENGTH = DebianWnpp._meta.get_field('description').max_length

        issue_subject = issue_properties.get(IssueProperty.SUBJECT.value, '')
        issue_kind, package_name, package_description = cls._parse_wnpp_issue_subject(
            issue_subject)

        charge_person = issue_properties.get(IssueProperty.OWNER.value)
        description = Truncator(package_description).chars(_MAX_DESCRIPTION_LENGTH)
        mod_stamp = cls._from_epoch_seconds(
            int(issue_properties[IssueProperty.LAST_MODIFIED.value]))
        open_person = issue_properties.get(IssueProperty.ORIGINATOR.value)
        open_stamp = cls._from_epoch_seconds(int(issue_properties[IssueProperty.DATE.value]))

        return {
            'ident': issue_id,
            'open_person': open_person,
            'open_stamp': open_stamp,
            'mod_stamp': mod_stamp,
            'kind': issue_kind,
            'popcon_id': package_name,
            'description': description,
            'charge_person': charge_person,
            'cron_stamp': now(),
        }

    @staticmethod
    def _shy_quote(o) -> str:
        if isinstance(o, str):
            return repr(o)
        else:
            return str(o)

    def _detect_and_report_diff(self, issue: DebianWnpp, future_issue_data: dict[str,
                                                                                 Any]) -> set[str]:
        # NOTE: We do not want to update the cron_stamp alone, but we do want to update whenever
        #       any field changed.  Should be done using TimeStampedModel instead, later.
        fields_that_changed = set()
        for field_name, new_value in sorted(future_issue_data.items()):
            old_value = getattr(issue, field_name)
            if new_value != old_value:
                fields_that_changed.add(field_name)
                if field_name != 'cron_stamp':
                    self._notice(f'--- {issue.ident}.{field_name} = {self._shy_quote(old_value)}')
                    self._notice(f'+++ {issue.ident}.{field_name} = {self._shy_quote(new_value)}')
        return fields_that_changed

    @classmethod
    def _create_log_entry_from(cls, issue: DebianWnpp, event: EventKind,
                               when: datetime.datetime) -> DebianLogIndex:
        return DebianLogIndex(
            ident=issue.ident,
            kind=issue.kind,
            project=issue.popcon_id,
            description=issue.description,
            log_stamp=now(),
            event=event.value,
            event_stamp=when,
        )

    def handle(self, *args, **options):
        self._client = DebbugsWnppClient()
        self._client.connect()

        ids_of_remote_open_issues = self._client.fetch_ids_of_open_issues()

        self._close_all_issues_but(ids_of_remote_open_issues)
        self._add_any_new_issues_from(ids_of_remote_open_issues)
        self._update_stale_existing_issues(ids_of_remote_open_issues)

        self._success('Successfully synced with Debbugs.')
