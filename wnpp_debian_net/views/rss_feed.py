# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import sys
from enum import Enum

from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from ..models import DebianLogIndex, EventKind, IssueKind
from ..templatetags.debian_urls import wnpp_issue_url

DEFAULT_MAX_ENTRIES = 30


class NewsDataSet(Enum):
    ALL = 'all'
    BAD_NEWS = 'bad_news'
    GOOD_NEWS = 'good_news'
    HELP_EXISTING = 'help_existing'
    NEW_PACKAGES = 'new_packages'

    @classmethod
    def _missing_(cls, value):
        return cls.ALL


_FILTER_GOOD_NEWS: Q = (Q(event=EventKind.CLOSED.value)
                        | Q(event__in=(EventKind.MODIFIED.value, EventKind.OPENED.value),
                            kind__in=(IssueKind.ITA.value, IssueKind.ITP.value)))

_DATASETS: dict[NewsDataSet, tuple[str, Q]] = {
    NewsDataSet.ALL: (_('Debian Packaging News'), (Q())),
    NewsDataSet.BAD_NEWS: (_('Bad News on Debian Packages'), ~_FILTER_GOOD_NEWS),
    NewsDataSet.GOOD_NEWS: (_('Good News on Debian Packages'), _FILTER_GOOD_NEWS),
    NewsDataSet.HELP_EXISTING: (_('Existing Debian Packages In Need For Help'),
                                Q(event__in=(EventKind.MODIFIED.value, EventKind.OPENED.value),
                                  kind__in=(IssueKind.O_.value, IssueKind.RFA.value,
                                            IssueKind.RFH.value))),
    NewsDataSet.NEW_PACKAGES: (_('New Debian Packages'),
                               Q(event=EventKind.CLOSED, kind=IssueKind.ITP)),
}


class WnppNewsFeedView(Feed):
    title = _('Debian Packaging News')
    description = _('Debian news feed on packaging bugs')
    ttl = 15  # seconds

    def __init__(self, data_set: str | None = None, max_entries: int | None = None):
        self.__max_entries = max_entries or DEFAULT_MAX_ENTRIES
        self.__data_set = data_set  # overwritten in __call__ below

    @staticmethod
    def _insert_reference_to_xslt_stylesheet_to(response: HttpResponse) -> None:
        rss_xsl_url = static('xsl/rss.xsl')
        stylesheet_line = f'<?xml-stylesheet type="text/xsl" href="{rss_xsl_url}" media="all"?>'
        bytes_lines: bytes = response.content.split(b'\n')
        response.content = b'\n'.join([bytes_lines[0] + stylesheet_line.encode('ascii')]
                                      + bytes_lines[1:])

    def __call__(self, request, *args, **kwargs):
        self.__request: HttpRequest = request
        self.__title_format_kind = self.__request.GET.get('title_format', '0')
        self.__data_set = self.__request.GET.get('data', 'all')

        self.feed_url = self.__request.build_absolute_uri(self.__request.get_full_path())
        self.link = self.feed_url

        response = super().__call__(request, *args, **kwargs)

        if 'test' in sys.argv:
            response.context_data = {
                'object_list': self.items(),
            }

        self._insert_reference_to_xslt_stylesheet_to(response)

        # This will make Chromium and Firefox apply the XML stylesheet
        # Without it, Django serves "application/rss+xml".
        response['Content-Type'] = 'application/xml'

        return response

    def title(self):
        return _DATASETS[NewsDataSet(self.__data_set)][0]

    def _get_querset_filter(self):
        return _DATASETS[NewsDataSet(self.__data_set)][1]

    def items(self):
        return (DebianLogIndex.objects.filter(self._get_querset_filter()).select_related(
            'kind_change').order_by('-event_stamp')[:self.__max_entries])

    def item_author_email(self, item: DebianLogIndex):
        return f'{item.ident}@bugs.debian.org'

    def item_author_name(self, item: DebianLogIndex):
        return f'Debian WNPP issue {item.ident}'

    def item_description(self, item: DebianLogIndex):
        return wnpp_issue_url(item.ident)  # for backwards-compatibility, only

    def item_guid(self, item: DebianLogIndex):
        # NOTE: The HTTP absolute URL is in place for backwards-compatibility, only
        return f'http://wnpp.debian.net/{item.ident}/{item.event_stamp.timestamp():.0f}'

    def item_link(self, item):
        return wnpp_issue_url(item.ident)

    def item_pubdate(self, item: DebianLogIndex):
        return item.event_stamp

    def item_title(self, item: DebianLogIndex):
        event_display = {
            EventKind.MODIFIED.value: _('Modified'),
            EventKind.OPENED.value: _('Opened'),
            EventKind.CLOSED.value: _('Closed'),
        }[item.event]

        if item.event == EventKind.MODIFIED.value and hasattr(item, 'kind_change'):
            kind_display = f'{item.kind_change.old_kind} -> {item.kind_change.new_kind}'
        else:
            kind_display = item.kind

        if self.__title_format_kind != '1':
            return f'{event_display} [{kind_display}] {item.project} -- {item.description}'
        else:  # i.e. explicit format '0' or anything invalid
            if item.event == EventKind.CLOSED.value:
                return f'CLOSED : {item.project} -- {item.description}'
            else:
                return f'#{item.ident} {kind_display}: {item.project} -- {item.description}'
