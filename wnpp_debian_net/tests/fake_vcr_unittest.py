# Copyright (C) 2026 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import inspect
import os.path
import unittest
from unittest.mock import patch

import yaml
from pysimplesoap.transport import TransportBase


def _create_http_responder_from(cassette_filename: str) -> type[TransportBase]:
    with open(cassette_filename) as f:
        cassette_doc = yaml.safe_load(f)

    first_http_request = cassette_doc["interactions"][0]["request"]
    expected_http_request_body: str = first_http_request["body"].encode("utf-8")
    expected_http_request_method: str = first_http_request["method"]
    expected_http_request_uri: str = first_http_request["uri"]

    first_http_response = cassette_doc["interactions"][0]["response"]
    http_response_body: bytes = first_http_response["body"]["string"].encode("utf-8")

    class DummyHttpClient(TransportBase):
        def __init__(self, **_kwargs): ...

        def request(self, location, http_method, body, **_kwargs):
            if location != expected_http_request_uri:
                raise AssertionError(f"{location=} != {expected_http_request_uri=}")

            if http_method != expected_http_request_method:
                raise AssertionError(f"{http_method=} != {expected_http_request_method=}")

            if body != expected_http_request_body:
                raise AssertionError(f"{body=} != {expected_http_request_body=}")

            return {}, http_response_body

    return DummyHttpClient


class FakeVcrTestCase(unittest.TestCase):
    """
    Replaces ``vcr.unittest.VcrTestCase`` in a way where
    it only supports PySimpleSOAP (version 1.16.2 at the time)
    and a single successful HTTP request... to allow getting rid of
    the vcrpy dependency.
    """

    def setUp(self):
        super().setUp()

        cassette_filename = os.path.join(
            self._get_cassette_library_dir(), self._get_cassette_name()
        )

        # This effectively wraps the execution of each test method by `with patcher:`
        patcher = patch(
            "pysimplesoap.transport.Http", _create_http_responder_from(cassette_filename)
        )
        patcher.__enter__()
        self.addCleanup(patcher.__exit__, None, None, None)

    def _get_cassette_library_dir(self):
        testdir = os.path.dirname(inspect.getfile(self.__class__))
        return os.path.join(testdir, "cassettes")

    def _get_cassette_name(self):
        return f"{self.__class__.__name__}.{self._testMethodName}.yaml"
