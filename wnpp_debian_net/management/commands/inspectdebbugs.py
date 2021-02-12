# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import json
import sys

from django.core.management.base import BaseCommand

from ...debbugs import DebbugsWnppClient


class Command(BaseCommand):
    help = 'Inspect one or more WNPP issues by dumping their metadata to standard output as JSON'

    def add_arguments(self, parser):
        parser.add_argument('issue_ids', nargs='+', metavar='ISSUE', type=int)

    def handle(self, *args, **options):
        client = DebbugsWnppClient()
        client.connect()

        properties_of_issue = client.fetch_issues(options['issue_ids'])

        json.dump(properties_of_issue, sys.stdout, indent='  ', sort_keys=True)
        print()  # for trailing newline
