# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.db import models
from django.db.models import CASCADE, DO_NOTHING, ForeignKey, OneToOneField, TextChoices
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class IssueKind(TextChoices):
    ITA = "ITA", _("ITA (Intent to adopt)")
    ITP = "ITP", _("ITP (Intent to package)")
    O_ = "O", _("O (Orphaned)")
    RFA = "RFA", _("RFA (Request for adoption)")
    RFH = "RFH", _("RFH (Request for help)")
    RFP = "RFP", _("RFP (request for packaging)")


class EventKind(TextChoices):
    MODIFIED = "MOD", _("modified")
    OPENED = "OPEN", _("opened")
    CLOSED = "CLOSE", _("closed")


class DebianLogIndex(models.Model):
    log_id = models.AutoField(primary_key=True)
    ident = models.IntegerField(blank=True, null=True)
    kind = models.CharField(
        max_length=3, choices=IssueKind.choices, blank=True, null=True, db_column="type"
    )
    project = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    log_stamp = models.DateTimeField(blank=True, null=True)
    event = models.CharField(max_length=5, choices=EventKind.choices)
    event_stamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "debian_log_index"


class DebianLogMods(models.Model):
    log = OneToOneField(
        DebianLogIndex,
        on_delete=CASCADE,
        primary_key=True,
        related_name="kind_change",
        related_query_name="kind_change",
    )
    old_kind = models.CharField(
        max_length=3, choices=IssueKind.choices, blank=True, null=True, db_column="before_type"
    )
    new_kind = models.CharField(
        max_length=3, choices=IssueKind.choices, blank=True, null=True, db_column="after_type"
    )

    class Meta:
        db_table = "debian_log_mods"


class DebianPopcon(models.Model):
    package = models.CharField(primary_key=True, max_length=255)
    inst = models.IntegerField(blank=True, null=True)
    vote = models.IntegerField(blank=True, null=True)
    old = models.IntegerField(blank=True, null=True)
    recent = models.IntegerField(blank=True, null=True)
    nofiles = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "debian_popcon"


class DebianWnpp(models.Model):
    ident = models.IntegerField(primary_key=True)
    open_person = models.CharField(max_length=255, blank=True, null=True)
    open_stamp = models.DateTimeField(blank=True, null=True)
    mod_stamp = models.DateTimeField(blank=True, null=True)
    kind = models.CharField(max_length=3, choices=IssueKind.choices, db_column="type")
    # Original was: project = models.CharField(max_length=255, blank=True, null=True)
    popcon = ForeignKey(DebianPopcon, on_delete=DO_NOTHING, null=True, db_column="project")
    description = models.CharField(max_length=255, blank=True, null=True)
    charge_person = models.CharField(max_length=255, blank=True, null=True)
    cron_stamp = models.DateTimeField()
    has_smaller_sibling = models.BooleanField(default=False)

    class Meta:
        db_table = "debian_wnpp"

    def age_days(self, until=None) -> int:
        if until is None:
            until = now()
        return (until - self.open_stamp).days

    def dust_days(self, until=None) -> int:
        if until is None:
            until = now()
        return (until - self.mod_stamp).days

    def has_existing_package(self):
        return IssueKind(self.kind) not in (IssueKind.ITP, IssueKind.RFP)

    def __lt__(self, other):
        return self.ident < other.ident
