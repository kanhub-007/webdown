"""Domain service for URL normalization (shared host-extraction logic).

Used by both the SQLite page-error repository and the in-memory test fake
to ensure consistent host matching for cross-job resume queries.
"""

from urllib.parse import urlparse


def normalize_host(url: str) -> str:
    """Return the hostname of a URL, ignoring a leading 'www.'.

    Args:
        url: A full URL string (e.g. 'https://www.example.com/page').

    Returns:
        The normalized hostname (e.g. 'example.com'), or '' if parsing fails.

    >>> normalize_host('https://www.example.com/page')
    'example.com'
    >>> normalize_host('https://example.com')
    'example.com'
    """
    host = urlparse(url).hostname or ""
    return host[4:] if host.startswith("www.") else host
