# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

import base64
from enum import Enum
from typing import Optional

from pysimplesoap.client import SoapClient
from pysimplesoap.simplexml import SimpleXMLElement


class IssueProperty(Enum):
    AFFECTS = 'affects'
    ARCHIVED = 'archived'
    BLOCKEDBY = 'blockedby'
    BLOCKS = 'blocks'
    BUG_NUM = 'bug_num'
    DATE = 'date'
    DONE = 'done'
    FIXED = 'fixed'
    FIXED_DATE = 'fixed_date'
    FIXED_VERSIONS = 'fixed_versions'
    FORWARDED = 'forwarded'
    FOUND = 'found'
    FOUND_DATE = 'found_date'
    FOUND_VERSIONS = 'found_versions'
    ID = 'id'
    KEYWORDS = 'keywords'
    LAST_MODIFIED = 'last_modified'
    LOCATION = 'location'
    LOG_MODIFIED = 'log_modified'
    MERGEDWITH = 'mergedwith'
    MSGID = 'msgid'
    ORIGINATOR = 'originator'
    OUTLOOK = 'outlook'
    OWNER = 'owner'
    PACKAGE = 'package'
    PENDING = 'pending'
    SEVERITY = 'severity'
    SOURCE = 'source'
    SUBJECT = 'subject'
    SUMMARY = 'summary'
    TAGS = 'tags'
    UNARCHIVED = 'unarchived'


class DebbugsWnppClient:

    def __init__(self):
        self._client = None

    def connect(self):
        self._client = SoapClient(location='https://bugs.debian.org/cgi-bin/soap.cgi')

    @staticmethod
    def _to_soap_kwargs(*iter):
        return {f'arg{i}': v for i, v in enumerate(iter)}

    @staticmethod
    def _decode_base64_as_needed(candidate: Optional[str]) -> Optional[str]:
        # Some bugs have base64 encoded titles or contact info
        # e.g. 842114 (https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=842114)
        if candidate is None:
            return None

        try:
            return base64.decodebytes(candidate.encode('ascii')).decode()
        except (ValueError, UnicodeEncodeError):
            return candidate

    def fetch_ids_of_open_issues(self) -> list[int]:
        result: SimpleXMLElement = self._client.get_bugs(
            **self._to_soap_kwargs('package', 'wnpp', 'status', 'open'))
        return [
            int(item_element.firstChild.nodeValue)
            for item_element
            in result._element.getElementsByTagName('item')
        ]

    def fetch_issues(self, issue_ids: list[int]) -> dict[int, dict[str, str]]:
        properties_of_issue: dict[int, dict[str, str]] = {}

        soap_result: SimpleXMLElement = self._client.get_status(**self._to_soap_kwargs(*issue_ids))

        map_element = soap_result._element.getElementsByTagName('s-gensym3')[0]
        for item_element in map_element.childNodes:
            key_element = item_element.childNodes[0]
            value_element = item_element.childNodes[1]

            issue_id = int(key_element.firstChild.nodeValue)
            issue_properties = {node.tagName: self._decode_base64_as_needed(node.firstChild.nodeValue)
                                for node in value_element.childNodes
                                if node.firstChild is not None}

            properties_of_issue[issue_id] = issue_properties

        return properties_of_issue
