# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import datetime
import re
import sys
from functools import partial
from itertools import islice
from signal import SIGINT
from typing import Any

from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import Truncator
from django.utils.timezone import now

from ...debbugs import (DebbugsRequestError, DebbugsRetry, DebbugsWnppClient, IssueProperty,
                        IssueStatus)
from ...models import DebianLogIndex, DebianLogMods, DebianPopcon, DebianWnpp, EventKind
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

    def _fetch_issues(self, issue_ids: list[int]) -> dict[int, dict[str, str]]:
        flat_issue_ids = ', '.join(str(i) for i in issue_ids)
        self._notice(f'Fetching {len(issue_ids)} issue(s): {flat_issue_ids}...')
        properties_of_issue = DebbugsRetry(self._client.fetch_issues,
                                           notify=self._notice)(issue_ids)

        return properties_of_issue

    @staticmethod
    def _create_missing_pocons_for(package_names: list[str]) -> list[DebianPopcon]:
        existing_packages = set(
            DebianPopcon.objects.filter(package__in=package_names).values_list('package',
                                                                               flat=True))
        missing_packages = package_names - existing_packages
        return [DebianPopcon(package=package) for package in missing_packages]

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

            future_local_properties_of_issue, popcons_to_create = self._analyze_remote_properties(
                remote_properties_of_issue)

            for issue_id, properties in future_local_properties_of_issue.items():
                issue = DebianWnpp(**properties)
                issues_to_create.append(issue)
                log_entries_to_create.append(
                    self._create_log_entry_from(issue, EventKind.OPENED, issue.open_stamp))

            if issues_to_create:
                with transaction.atomic():
                    if popcons_to_create:
                        DebianPopcon.objects.bulk_create(popcons_to_create)
                        self._success(f'Created {len(popcons_to_create)} missing popcon entries')

                    DebianLogIndex.objects.bulk_create(log_entries_to_create)
                    self._success(
                        f'Logged upcoming creation of {len(log_entries_to_create)} issue(s)')

                    DebianWnpp.objects.bulk_create(issues_to_create)
                    self._success(f'Created {len(issues_to_create)} new issues')
            else:
                self._notice('No new issues created.')

    def _analyze_remote_properties(self, remote_properties_of_issue):
        future_local_properties_of_issue: dict[int, dict[str, Any]] = {}
        for issue_id, properties in remote_properties_of_issue.items():
            self._notice(f'Processing upcoming issue {issue_id}...')
            try:
                future_local_properties_of_issue[issue_id] = self._to_database_keys(
                    issue_id, properties)
            except _MalformedSubject as e:
                self._error(str(e))
                continue

        # NOTE: PostgreSQL is not forgiving about absent foreign keys,
        #       so we'll need to create any missing DebianPopcon instances
        #       before creating the related DebianWnpp instances.
        involved_package = {
            properties['popcon_id']
            for properties in future_local_properties_of_issue.values()
        }
        popcons_to_create = self._create_missing_pocons_for(involved_package)

        return future_local_properties_of_issue, popcons_to_create

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
            kind_change_log_entries_to_create: list[DebianLogMods] = []
            issues_to_update: list[DebianWnpp] = list(
                stale_issues_qs.order_by('cron_stamp', 'ident')[:_BATCH_SIZE])
            if not issues_to_update:
                break

            self._notice(
                f'Updating next {min(_BATCH_SIZE, count_issues_left_to_update)} stale issue(s) of {count_issues_left_to_update} left to update...'
            )
            count_issues_left_to_update -= _BATCH_SIZE

            issue_ids = [issue.ident for issue in issues_to_update]
            issue_fields_to_bulk_update: set[str] = {
                'cron_stamp',
            }  # will be grown as needed

            # Fetch remote data
            remote_properties_of_issue = self._fetch_issues(issue_ids)

            future_local_properties_of_issue, popcons_to_create = self._analyze_remote_properties(
                remote_properties_of_issue)

            # Turn remote data into database instances (to persist later)
            for i, issue in enumerate(issues_to_update):
                try:
                    database_field_map = future_local_properties_of_issue[issue.ident]
                except KeyError:  # when self._analyze_remote_properties had to drop the issue
                    issue.cron_stamp = now()
                    continue

                fields_about_to_change = self._detect_and_report_diff(issue, database_field_map)

                if fields_about_to_change:
                    issue_fields_to_bulk_update |= fields_about_to_change

                    old_kind_backup = issue.kind
                    for field_name in fields_about_to_change:
                        setattr(issue, field_name, database_field_map[field_name])

                    log_entry = self._create_log_entry_from(issue, EventKind.MODIFIED,
                                                            issue.mod_stamp)
                    log_entries_to_create.append(log_entry)

                    if old_kind_backup != issue.kind:
                        kind_change_log_entries_to_create.append(
                            DebianLogMods(
                                log=log_entry,
                                old_kind=old_kind_backup,
                                new_kind=issue.kind,
                            ))

            with transaction.atomic():
                # Persist log entries
                DebianLogIndex.objects.bulk_create(log_entries_to_create)
                self._success(f'Logged upcoming updates to {len(log_entries_to_create)} issue(s)')

                if popcons_to_create:
                    DebianPopcon.objects.bulk_create(popcons_to_create)
                    self._success(f'Created {len(popcons_to_create)} missing popcon entries')

                # Persist kind change extra log entries
                if kind_change_log_entries_to_create:
                    # NOTE: We need to apply the just-written primary keys or we'll get this error:
                    #       django.db.utils.IntegrityError: null value in column "log_id" of relation "debian_log_mods" violates not-null constraint
                    for kind_change_log_entry in kind_change_log_entries_to_create:
                        kind_change_log_entry.log_id = kind_change_log_entry.log.log_id

                    DebianLogMods.objects.bulk_create(kind_change_log_entries_to_create)
                    self._success(
                        f'Logged upcoming changes in kind of {len(kind_change_log_entries_to_create)} issue(s)'
                    )
                else:
                    self._notice('No changes in kind recognized.')

                # Persist actual issues
                DebianWnpp.objects.bulk_update(issues_to_update,
                                               fields=issue_fields_to_bulk_update)
                self._success(f'Updated {len(issues_to_update)} existing issue(s)')

    @staticmethod
    def _parse_wnpp_issue_subject(subject) -> tuple[str, str, str]:
        match_ = re.match(
            '^(?:[Ss]ubject: )?(?P<kind>[A-Z]{1,3}): ?(?P<package>[^ ]+)(?:(?: --| -| —|:) (?P<description>.*))?$',
            subject)
        if match_ is None:
            raise _MalformedSubject(f'Malformed subject {subject!r}')

        return tuple(match_.group(g) for g in ('kind', 'package', 'description'))

    @staticmethod
    def _from_epoch_seconds(epoch_seconds) -> datetime.datetime:
        dt = datetime.datetime.fromtimestamp(epoch_seconds)
        dt = dt.replace(tzinfo=datetime.UTC)
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
        has_smaller_sibling = any(
            (int(i) < issue_id)
            for i in issue_properties.get(IssueProperty.MERGEDWITH.value, '').split())

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
            'has_smaller_sibling': has_smaller_sibling,
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
        self._client = options.get('client') or DebbugsWnppClient()
        self._client.connect()

        try:
            ids_of_remote_open_issues: set[int] = set()
            for issue_status in (IssueStatus.FORWARDED, IssueStatus.OPEN):
                fetch_ids = partial(self._client.fetch_ids_of_issues_with_status, issue_status)
                issue_ids: list[int] = DebbugsRetry(fetch_ids, notify=self._notice)()
                ids_of_remote_open_issues |= set(issue_ids)

            self._close_all_issues_but(ids_of_remote_open_issues)
            self._add_any_new_issues_from(ids_of_remote_open_issues)
            self._update_stale_existing_issues(ids_of_remote_open_issues)

            self._success('Successfully synced with Debbugs.')
        except DebbugsRequestError as e:
            raise CommandError(f'Import remote WNPP issues from Debbugs: {e}')
        except KeyboardInterrupt:
            sys.exit(128 + SIGINT)
