# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from ..models import DebianLogIndex, EventType, IssueType
from ..templatetags.debian_urls import wnpp_issue_url

_MAX_ENTRIES = 30


class WnppNewsFeedView(Feed):
    title = _('Debian Packaging News')
    description = _('Debian news feed on packaging bugs')
    ttl = 15  # seconds

    def __call__(self, request, *args, **kwargs):
        self.__request: HttpRequest = request
        self.__title_format_type = self.__request.GET.get('title_format', '0')
        self.__data_set = self.__request.GET.get('data', 'all')

        self.feed_url = self.__request.build_absolute_uri(self.__request.get_full_path())
        self.link = self.feed_url

        return super().__call__(request, *args, **kwargs)

    def title(self):
        _TITLE_DATASET_ALL = _('Debian Packaging News')
        return {
            'all': _TITLE_DATASET_ALL,
            'bad_news': _('Bad News on Debian Packages'),
            'good_news': _('Good News on Debian Packages'),
            'help_existing': _('Existing Debian Packages In Need For Help'),
            'new_packages': _('New Debian Packages'),
        }.get(self.__data_set, _TITLE_DATASET_ALL)

    def _get_querset_filter(self):
        _FILTER_DATASET_ALL = Q()
        _FILTER_GOOD_NEWS = (Q(event=EventType.CLOSED)
                             | Q(event__in=(EventType.MODIFIED.value, EventType.OPENED.value),
                                 type__in=(IssueType.ITA.value, IssueType.ITP.value)))
        _QA_FILTER_FOR_DATASET = {
            'all': _FILTER_DATASET_ALL,
            'bad_news': ~_FILTER_GOOD_NEWS,
            'good_news': _FILTER_GOOD_NEWS,
            'help_existing': Q(event__in=(EventType.MODIFIED.value, EventType.OPENED.value),
                               type__in=(
                               IssueType.O.value, IssueType.RFA.value, IssueType.RFH.value)),
            'new_packages': Q(event=EventType.CLOSED, type=IssueType.ITP),
        }
        return _QA_FILTER_FOR_DATASET.get(self.__data_set, _FILTER_DATASET_ALL)

    def items(self):
        return (DebianLogIndex.objects
                    .filter(self._get_querset_filter())
                    .select_related('type_change')
                    .order_by('-event_stamp')[:_MAX_ENTRIES])

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
            EventType.MODIFIED.value: _('Modified'),
            EventType.OPENED.value: _('Opened'),
            EventType.CLOSED.value: _('Closed'),
        }[item.event]

        if item.event == EventType.MODIFIED.value and hasattr(item, 'type_change'):
            type_display = f'{item.type_change.before_type} -> {item.type_change.after_type}'
        else:
            type_display = item.type

        if self.__title_format_type != '1':
            return f'{event_display} [{type_display}] {item.project} -- {item.description}'
        else:  # i.e. explicit format '0' or anything invalid
            if item.event == EventType.CLOSED.value:
                return f'CLOSED : {item.project} -- {item.description}'
            else:
                return f'#{item.ident} {type_display}: {item.project} -- {item.description}'
