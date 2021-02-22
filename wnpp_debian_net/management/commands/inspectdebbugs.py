# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import json

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

        # NOTE: We're avoiding ``json.dump(.., self.stdout, ..)`` because
        #       ``BaseCommand.stdout`` is duplicating newlines in
        #       ``django.core.management.base.OutputWrapper.write``
        #       and that would not make pretty JSON output
        print(json.dumps(properties_of_issue, indent='  ', sort_keys=True), file=self.stdout)
