# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.db import models
from django.db.models import DO_NOTHING, ForeignKey, CASCADE, OneToOneField, TextChoices
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class IssueType(TextChoices):
    ITA = 'ITA', _('ITA (Intent to adopt)')
    ITP = 'ITP', _('ITP (Intent to package)')
    O = 'O', _('O (Orphaned)')
    RFA = 'RFA', _('RFA (Request for adoption)')
    RFH = 'RFH', _('RFH (Request for help)')
    RFP = 'RFP', _('RFP (request for packaging)')


class EventType(TextChoices):
    MODIFIED = 'MOD', _('modified')
    OPENED = 'OPEN', _('opened')
    CLOSED = 'CLOSE', _('closed')


class DebianLogIndex(models.Model):
    log_id = models.AutoField(primary_key=True)
    ident = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=3, choices=IssueType.choices, blank=True, null=True)
    project = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    log_stamp = models.DateTimeField(blank=True, null=True)
    event = models.CharField(max_length=5, choices=EventType.choices)
    event_stamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'debian_log_index'


class DebianLogMods(models.Model):
    log = OneToOneField(DebianLogIndex, on_delete=CASCADE, primary_key=True,
                        related_name='type_change', related_query_name='type_change')
    before_type = models.CharField(max_length=3, choices=IssueType.choices, blank=True, null=True)
    after_type = models.CharField(max_length=3, choices=IssueType.choices, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'debian_log_mods'


class DebianPopcon(models.Model):
    package = models.CharField(primary_key=True, max_length=255)
    inst = models.IntegerField(blank=True, null=True)
    vote = models.IntegerField(blank=True, null=True)
    old = models.IntegerField(blank=True, null=True)
    recent = models.IntegerField(blank=True, null=True)
    nofiles = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'debian_popcon'


class DebianWnpp(models.Model):
    ident = models.IntegerField(primary_key=True)
    open_person = models.CharField(max_length=255, blank=True, null=True)
    open_stamp = models.DateTimeField(blank=True, null=True)
    mod_stamp = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=3, choices=IssueType.choices)
    # Original was: project = models.CharField(max_length=255, blank=True, null=True)
    popcon = ForeignKey(DebianPopcon, on_delete=DO_NOTHING, null=True, db_column='project')
    description = models.CharField(max_length=255, blank=True, null=True)
    charge_person = models.CharField(max_length=255, blank=True, null=True)
    cron_stamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'debian_wnpp'
