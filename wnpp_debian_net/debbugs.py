# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import base64
import time
from collections.abc import Callable
from datetime import timedelta
from enum import Enum
from functools import wraps
from urllib.error import URLError

from django.utils.timezone import now
from pysimplesoap.client import SoapClient
from pysimplesoap.simplexml import SimpleXMLElement


class IssueProperty(Enum):
    AFFECTS = "affects"
    ARCHIVED = "archived"
    BLOCKEDBY = "blockedby"
    BLOCKS = "blocks"
    BUG_NUM = "bug_num"
    DATE = "date"
    DONE = "done"
    FIXED = "fixed"
    FIXED_DATE = "fixed_date"
    FIXED_VERSIONS = "fixed_versions"
    FORWARDED = "forwarded"
    FOUND = "found"
    FOUND_DATE = "found_date"
    FOUND_VERSIONS = "found_versions"
    ID = "id"
    KEYWORDS = "keywords"
    LAST_MODIFIED = "last_modified"
    LOCATION = "location"
    LOG_MODIFIED = "log_modified"
    MERGEDWITH = "mergedwith"
    MSGID = "msgid"
    ORIGINATOR = "originator"
    OUTLOOK = "outlook"
    OWNER = "owner"
    PACKAGE = "package"
    PENDING = "pending"
    SEVERITY = "severity"
    SOURCE = "source"
    SUBJECT = "subject"
    SUMMARY = "summary"
    TAGS = "tags"
    UNARCHIVED = "unarchived"


class IssueStatus(Enum):  # known to be incomplete
    FORWARDED = "forwarded"
    OPEN = "open"


class DebbugsRequestError(Exception):
    pass


def _wrap_exceptions(f):
    """
    Turn low-level/internal exceptions to something that is part of the public interface.
    """

    @wraps(f)
    def wrapped(*args, **wargs):
        try:
            return f(*args, **wargs)
        except URLError as e:
            raise DebbugsRequestError(e)

    return wrapped


def _retry(
    func: Callable, times: int, exception_classes: tuple[Exception], notify: Callable[[str], None]
) -> Callable:
    """
    Decorates ``func`` with retry for up to ``times`` times with exponential back-off
    while ignoring all exception classes in ``exception_classes``.
    Calls out to ``notify`` for notification targeting humans.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        started_at = now()
        for i in range(times):
            try:
                res = func(*args, **kwargs)
            except exception_classes:
                message_prefix = f"Attempt {i + 1} failed, been trying for {now() - started_at}"
                giving_up = i == times - 1
                if giving_up:
                    notify(f"{message_prefix} — giving up")
                    raise
                sleep_duration_seconds = 2**i
                sleep_until = now() + timedelta(seconds=sleep_duration_seconds)
                notify(
                    f"{message_prefix} — sleeping for {sleep_duration_seconds} second(s)"
                    f" until {sleep_until} to try up to {times - i - 1} time(s) more"
                )
                time.sleep(sleep_duration_seconds)
            else:
                if i > 0:
                    notify(f"Attempt {i + 1} succeeded (after trying for {now() - started_at})")
                return res

    return wrapped


class DebbugsRetry:
    def __init__(self, func: Callable, notify: Callable[[str], None]):
        self.__func = func
        self.__notify = notify

    def __call__(self, *args, **kwargs):
        func_with_retry = _retry(
            self.__func, times=8, exception_classes=(DebbugsRequestError,), notify=self.__notify
        )
        return func_with_retry(*args, **kwargs)


class DebbugsWnppClient:
    def __init__(self):
        self._client = None

    def connect(self):
        self._client = SoapClient(location="https://bugs.debian.org/cgi-bin/soap.cgi")

    @staticmethod
    def _to_soap_kwargs(*iter):
        return {f"arg{i}": v for i, v in enumerate(iter)}

    @staticmethod
    def _decode_base64_as_needed(candidate: str | None) -> str | None:
        # Some bugs have base64 encoded titles or contact info
        # e.g. 842114 (https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=842114)
        if candidate is None:
            return None

        try:
            return base64.decodebytes(candidate.encode("ascii")).decode()
        except ValueError, UnicodeEncodeError:
            return candidate

    @_wrap_exceptions
    def fetch_ids_of_issues_with_status(self, status: IssueStatus) -> list[int]:
        result: SimpleXMLElement = self._client.get_bugs(
            **self._to_soap_kwargs("package", "wnpp", "status", status.value)
        )
        return [
            int(item_element.firstChild.nodeValue)
            for item_element in result._element.getElementsByTagName("item")
        ]

    @_wrap_exceptions
    def fetch_issues(self, issue_ids: list[int]) -> dict[int, dict[str, str]]:
        properties_of_issue: dict[int, dict[str, str]] = {}

        soap_result: SimpleXMLElement = self._client.get_status(**self._to_soap_kwargs(*issue_ids))

        map_element = soap_result._element.getElementsByTagName("s-gensym3")[0]
        for item_element in map_element.childNodes:
            key_element = item_element.childNodes[0]
            value_element = item_element.childNodes[1]

            issue_id = int(key_element.firstChild.nodeValue)
            issue_properties = {
                node.tagName: self._decode_base64_as_needed(node.firstChild.nodeValue)
                for node in value_element.childNodes
                if node.firstChild is not None
            }

            properties_of_issue[issue_id] = issue_properties

        return properties_of_issue
