# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import datetime
import gzip
import os
import re
from itertools import islice
from typing import Any

import requests
from django.core.management.base import BaseCommand

from wnpp_debian_net.management.commands._common import ReportingMixin
from wnpp_debian_net.models import DebianPopcon

_BINARY_PACKAGES_POPCON_URL = "https://popcon.debian.org/by_inst.gz"
_SOURCE_PACKAGES_POPCON_URL = "https://popcon.debian.org/source/by_inst.gz"

_BATCH_SIZE = 500
_DEFAULT_MAXIMUM_STALE_DELTA = datetime.timedelta(hours=12)


class Command(ReportingMixin, BaseCommand):
    help = "Import remote popcon stats into the local database"

    def _download_url_to_disk(self, url, filename):
        self._notice(f"Downloading {url} to file {filename}...")
        r = requests.get(url, allow_redirects=True)
        with open(filename, "wb") as f:
            f.write(r.content)

    def _import_from_file_into_database(self, filename):
        self._notice(f"Importing popcon stats from file {filename}...")
        with gzip.open(filename, "r") as f:
            # NOTE: Corrupted data like b'texl\xb1\xdbv\xd2\xc7atex-extra' has been observed
            #       in practice
            content = f.read().decode("utf-8", errors="backslashreplace")

        extractor = re.compile(
            r"^[0-9]+\s+(?P<name>[^ ]+)\s+(?P<inst>[0-9]+)\s+(?P<vote>[0-9]+)\s+(?P<old>[0-9]+)\s+(?P<recent>[0-9]+)\s+(?P<nofiles>[0-9]+)"
        )

        entries_to_classify: dict[str, dict[str, Any]] = {}

        for line in content.split("\n"):
            match = extractor.search(line.rstrip())
            if match is None:
                continue

            stats = match.groupdict()

            package_name = stats["name"]
            if package_name == "Total":
                continue
            del stats["name"]

            entries_to_classify[package_name] = stats

        self._notice(f"Processing {len(entries_to_classify)} entries...")

        existing_packages: set[str] = set(
            DebianPopcon.objects.order_by("package").values_list("package", flat=True)
        )

        # Collecting existing entries to update
        entries_to_update: list[DebianPopcon] = []
        for entry in DebianPopcon.objects.iterator(chunk_size=_BATCH_SIZE):
            if entry.package not in entries_to_classify:
                continue

            changed = False
            for field_name, new_value in entries_to_classify[entry.package].items():
                old_value = getattr(entry, field_name)
                new_value = max(int(new_value), old_value or 0)
                if new_value != old_value:
                    changed = True
                    setattr(entry, field_name, new_value)
            if changed:
                entries_to_update.append(entry)

        # Update existing entries
        if entries_to_update:
            count_entries_left_to_update = len(entries_to_update)
            self._notice(f"Updating {count_entries_left_to_update} stale existing entries...")
            all_fields_but_primary_keys = [
                f.name for f in DebianPopcon._meta.fields if not f.primary_key
            ]
            it = iter(entries_to_update)
            while True:
                entries = list(islice(it, 0, _BATCH_SIZE))
                if not entries:
                    break

                self._notice(
                    f"Updating next {min(_BATCH_SIZE, count_entries_left_to_update)} entries(s) of {count_entries_left_to_update} left to update..."
                )
                count_entries_left_to_update -= _BATCH_SIZE

                DebianPopcon.objects.bulk_update(entries, fields=all_fields_but_primary_keys)
                del entries
            del entries_to_update
        else:
            self._notice("No stale entries to update.")

        # Add missing entries
        new_packages = set(entries_to_classify.keys()) - existing_packages
        del existing_packages
        if new_packages:
            count_entries_left_to_add = len(new_packages)
            self._notice(f"Adding {count_entries_left_to_add} new entries...")
            entries_to_create: list[DebianPopcon] = [
                DebianPopcon(package=package_name, **entries_to_classify[package_name])
                for package_name in new_packages
            ]
            del entries_to_classify

            it = iter(entries_to_create)
            while True:
                entries = list(islice(it, 0, _BATCH_SIZE))
                if not entries:
                    break

                self._notice(
                    f"Adding next {min(_BATCH_SIZE, count_entries_left_to_add)} entries(s) of {count_entries_left_to_add} left to add..."
                )
                count_entries_left_to_add -= _BATCH_SIZE

                DebianPopcon.objects.bulk_create(entries)
        else:
            self._notice("No new entries to add.")

    def _import_popcon_stats(self, maximum_stale_delta, download_cache_dir):
        for url, category in (
            (_SOURCE_PACKAGES_POPCON_URL, "source"),
            (_BINARY_PACKAGES_POPCON_URL, "binary"),
        ):
            filename = os.path.join(download_cache_dir, f"popcon_{category}_by_inst.gz")
            if os.path.exists(filename):
                stats = os.stat(filename)
                last_modified_delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(
                    stats.st_mtime
                )
                if last_modified_delta < maximum_stale_delta:
                    come_back_in = maximum_stale_delta - last_modified_delta
                    come_back_at = datetime.datetime.now() + come_back_in
                    self._notice(
                        f"Nothing to do for {come_back_in} (hh:mm:ss) more (until {come_back_at})."
                    )
                    return
                os.remove(filename)
            else:
                os.makedirs(os.path.dirname(filename), exist_ok=True)

            self._download_url_to_disk(url, filename)
            self._import_from_file_into_database(filename)

    def handle(self, *args, **options):
        maximum_stale_delta = options.get("maximum_stale_delta", _DEFAULT_MAXIMUM_STALE_DELTA)
        download_cache_dir = options.get(
            "download_cache_dir", os.path.expanduser("~/.local/cache")
        )
        self._import_popcon_stats(maximum_stale_delta, download_cache_dir)
