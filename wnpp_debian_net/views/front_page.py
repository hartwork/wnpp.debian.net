# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from typing import Union, Tuple, Dict, Any

from django.core.paginator import Paginator, Page
from django.db.models import Q, QuerySet, F
from django.views.generic import ListView

from ..models import DebianWnpp
from ..pagination import iterate_page_items
from ..templatetags.sorting_urls import parse_sort_param

_QUERY_FIELD_FOR_COLUMN_NAME = {
    'dust': 'mod_stamp',
    'age': 'open_stamp',
    'type': 'type',
    'project': 'popcon_id',
    'description': 'description',
    'users': 'popcon__vote',
    'installs': 'popcon__inst',
    'owner': 'charge_person',
    'reporter': 'open_person',
}

_COLUMN_NAMES = _QUERY_FIELD_FOR_COLUMN_NAME.keys()

_DEFAULT_COLUMNS = [
    'dust',
    'type',
    'project',
    'description',
    'installs',
]

assert all((column in _COLUMN_NAMES) for column in _DEFAULT_COLUMNS)

_ISSUE_TYPES = [
    'ita',
    'itp',
    'o',
    'rfa',
    'rfh',
    'rfp',
]

_DEFAULT_ISSUE_TYPES = [
    'o',
    'rfa',
    'rfh',
    'rfp',
]

assert all((type_ in _ISSUE_TYPES) for type_ in _DEFAULT_ISSUE_TYPES)


class FrontPageView(ListView):
    model = DebianWnpp
    paginate_by = 50

    #override
    def setup(self, request, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        super().setup(request, *args, **kwargs)
        self._col = self.request.GET.getlist('col[]', _DEFAULT_COLUMNS)
        self._description_filter = self.request.GET.get('description', '')
        self._owners = self.request.GET.getlist('owner[]', ['yes', 'no'])
        self._project_filter = self.request.GET.get('project', '')
        self._sort = self.request.GET.get('sort', 'project')
        self._types = {t.lower() for t in self.request.GET.getlist('type[]', _DEFAULT_ISSUE_TYPES)}

    #override
    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()

        if 'installs' in self._col or 'users' in self._col:
            qs = qs.select_related('popcon')

        fields = [_QUERY_FIELD_FOR_COLUMN_NAME[col] for col in sorted(set(self._col))]
        qs = qs.only(*fields)

        if self._description_filter:
            qs = qs.filter(description__icontains=self._description_filter)

        if self._owners:
            without_owner_filter = Q(charge_person__isnull=True) | Q(charge_person='')
            if 'yes' not in self._owners:
                qs = qs.exclude(~without_owner_filter)
            if 'no' not in self._owners:
                qs = qs.exclude(without_owner_filter)

        if self._project_filter:
            # NOTE: Django doesn't let us do "popcon_id__icontains=[..]"
            #       since it's used as a foreign key
            qs = (qs
                  .annotate(package_name=F('popcon_id'))
                  .filter(package_name__icontains=self._project_filter))

        if self._types:
            qs = qs.filter(type__in=self._types)

        return qs

    #override
    def get_ordering(self) -> Union[str, Tuple[str, ...]]:
        """Return the field or fields to use for ordering the queryset."""
        external_column, internal_direction_prefix = parse_sort_param(self._sort)
        fallback_field_name = _QUERY_FIELD_FOR_COLUMN_NAME['project']
        return internal_direction_prefix + _QUERY_FIELD_FOR_COLUMN_NAME.get(external_column,
                                                                            fallback_field_name)

    #override
    def get_context_data(self, *, object_list=None, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(object_list=object_list, **kwargs)

        context.update({
            'description_filter': self._description_filter,
            'project_filter': self._project_filter,
            'sort': self._sort,
            'with_owner': 'yes' in self._owners,
            'without_owner': 'no' in self._owners,
        })

        for issue_type in _ISSUE_TYPES:
            context[f'show_{issue_type}'] = issue_type in self._types

        for column_name in _COLUMN_NAMES:
            context[f'show_{column_name}'] = column_name in self._col

        paginator: Paginator = context['paginator']
        page_obj: Page = context['page_obj']
        context['page_items'] = list(iterate_page_items(total_page_count=paginator.num_pages,
                                                        current_page_number=page_obj.number))

        return context
