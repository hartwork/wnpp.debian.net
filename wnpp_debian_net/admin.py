# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.contrib import admin

from .models import DebianLogIndex, DebianLogMods, DebianPopcon, DebianWnpp


@admin.register(DebianLogIndex)
class DebianLogIndexAdmin(admin.ModelAdmin):
    pass


@admin.register(DebianLogMods)
class DebianLogModsAdmin(admin.ModelAdmin):
    pass


@admin.register(DebianPopcon)
class DebianPopconAdmin(admin.ModelAdmin):
    pass


@admin.register(DebianWnpp)
class DebianWnppAdmin(admin.ModelAdmin):
    readonly_fields = (
        # Quick workaround so that Django doesn't try offering ALL of popcon as a select value
        'popcon', )
