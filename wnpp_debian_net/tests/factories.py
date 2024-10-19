# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.utils.timezone import now
from factory import LazyFunction, Sequence
from factory.django import DjangoModelFactory

from ..models import DebianLogIndex, DebianLogMods, DebianPopcon, DebianWnpp, IssueKind


class DebianLogIndexFactory(DjangoModelFactory):
    class Meta:
        model = DebianLogIndex

    event_stamp = LazyFunction(now)
    log_stamp = LazyFunction(now)


class DebianLogModsFactory(DjangoModelFactory):
    class Meta:
        model = DebianLogMods


class DebianPopconFactory(DjangoModelFactory):
    class Meta:
        model = DebianPopcon


class DebianWnppFactory(DjangoModelFactory):
    class Meta:
        model = DebianWnpp

    ident = Sequence(int)
    cron_stamp = LazyFunction(now)
    mod_stamp = LazyFunction(now)
    open_stamp = LazyFunction(now)
    kind = IssueKind.RFA.value  # anything that matches the default filters
