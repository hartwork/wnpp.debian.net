# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def url_with_query(url, **data) -> str:
    """
    Applies substitutions/additions to the query part of the given URL
    """
    scheme, network_location, path, query, _fragment = urlsplit(url)
    query_pairs = parse_qsl(query)

    for query_key, query_value in data.items():
        rightmost_index = max((i for i, pair in enumerate(query_pairs) if pair[0] == query_key),
                                   default=None)
        new_pair = (query_key, str(query_value))
        if rightmost_index is None:
            query_pairs.append(new_pair)
        else:
            query_pairs[rightmost_index] = new_pair

    new_query = urlencode(query_pairs, doseq=True)
    return urlunsplit((scheme, network_location, path, new_query, None))