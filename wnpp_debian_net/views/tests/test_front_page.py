# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse_lazy
from parameterized import parameterized

from ...models import DebianPopcon, IssueKind
from ...tests.factories import DebianWnppFactory
from ..front_page import _COLUMN_NAMES, _DEFAULT_COLUMNS, _DEFAULT_ISSUE_KINDS


class _FrontPageTestCase(TestCase):
    url = reverse_lazy('front_page')


class RequestValidationTest(TestCase):  # doesn't need _FrontPageTestCase
    @parameterized.expand([
        ('/?col%5B%5D=description%27&desc=%27&sort=project%27&type%5B%5D=RFP%27', ),  # seen live
        ('/?col%5B%5D=description%27', ),
        ('/?sort=project%27', ),
        ('/?type%5B%5D=RFP%27', ),
        ('/?sort=installs&col%5B%5D=description', ),  # misses "&col[]=installs"
        ('/?sort=users', ),  # misses "&col[]=users"
    ])
    def test_bad_request_for_column(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)


class ColumnVisibilityTest(_FrontPageTestCase):
    def test_default(self):
        expected = {
            f'show_{column_name}': column_name in _DEFAULT_COLUMNS
            for column_name in _COLUMN_NAMES
        }

        response = self.client.get(self.url)

        for k, v in expected.items():
            self.assertEqual(response.context_data[k], v)

    def test_all(self):
        expected = {f'show_{column_name}': True for column_name in _COLUMN_NAMES}
        data = {'col[]': _COLUMN_NAMES}

        response = self.client.get(self.url, data)

        for k, v in expected.items():
            self.assertEqual(response.context_data[k], v)


class TextBasedFilterTest(_FrontPageTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        package1 = DebianPopcon(package='package1')
        package1.save()
        package2 = DebianPopcon(package='package2')
        package2.save()
        cls.issue1 = DebianWnppFactory(description='desc1', popcon=package1)
        cls.issue2 = DebianWnppFactory(description='desc2', popcon=package2)
        cls.issue3 = DebianWnppFactory(description='desc3')

    def test_default(self):
        response = self.client.get(self.url)

        object_list = list(response.context_data['object_list'])
        self.assertIn(self.issue1, object_list)
        self.assertIn(self.issue2, object_list)
        self.assertIn(self.issue3, object_list)

    def test_description_filter(self):
        data = {'description': self.issue1.description[1:]}

        response = self.client.get(self.url, data)

        object_list = list(response.context_data['object_list'])
        self.assertIn(self.issue1, object_list)
        self.assertNotIn(self.issue2, object_list)
        self.assertNotIn(self.issue3, object_list)

    def test_project_filter(self):
        data = {'project': self.issue2.popcon_id}

        response = self.client.get(self.url, data)

        object_list = list(response.context_data['object_list'])
        self.assertNotIn(self.issue1, object_list)
        self.assertIn(self.issue2, object_list)
        self.assertNotIn(self.issue3, object_list)


class KindFilterTest(_FrontPageTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.issue_for_kind = {kind.value: DebianWnppFactory(kind=kind.value) for kind in IssueKind}

    def test_all(self):
        data = {'type[]': IssueKind.values}

        response = self.client.get(self.url, data)

        object_list = list(response.context_data['object_list'])
        self.assertEqual(sorted(object_list), sorted(self.issue_for_kind.values()))

    def test_default(self):
        response = self.client.get(self.url)

        object_list = list(response.context_data['object_list'])
        for kind in IssueKind.values:
            assertion = self.assertIn if (kind in _DEFAULT_ISSUE_KINDS) else self.assertNotIn
            issue_to_test = self.issue_for_kind[kind]
            assertion(issue_to_test, object_list)


class OwnerFilterTest(_FrontPageTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.with_owner = DebianWnppFactory(charge_person='owner@example.org')
        cls.without_owner = DebianWnppFactory()

    def test_owner_filter__default(self):
        response = self.client.get(self.url)

        object_list = list(response.context_data['object_list'])
        self.assertIn(self.with_owner, object_list)
        self.assertIn(self.without_owner, object_list)

    def test_owner_filter__with_only(self):
        data = {'owner[]': 'yes'}

        response = self.client.get(self.url, data)

        object_list = list(response.context_data['object_list'])
        self.assertIn(self.with_owner, object_list)
        self.assertNotIn(self.without_owner, object_list)

    def test_owner_filter__without_only(self):
        data = {'owner[]': 'no'}

        response = self.client.get(self.url, data)

        object_list = list(response.context_data['object_list'])
        self.assertNotIn(self.with_owner, object_list)
        self.assertIn(self.without_owner, object_list)

    def test_owner_filter__with_and_without(self):
        data = {'owner[]': ['yes', 'no']}

        response = self.client.get(self.url, data)

        object_list = list(response.context_data['object_list'])
        self.assertIn(self.with_owner, object_list)
        self.assertIn(self.without_owner, object_list)
