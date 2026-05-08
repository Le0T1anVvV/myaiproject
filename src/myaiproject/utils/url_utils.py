"""URL validation, normalization, and domain utilities."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


def normalize_url(url: str, base: str | None = None) -> str:
    """Normalize a URL: ensure scheme, remove fragments, lower netloc."""
    if base and not urlparse(url).netloc:
        url = urljoin(base, url)
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = urlparse(f"https://{url}")
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return f"{parsed.scheme}://{netloc}{path}"


def is_same_domain(url: str, base_domain: str) -> bool:
    """Check if *url* belongs to the same domain as *base_domain*."""
    return extract_domain(url) == base_domain.lower()


def extract_domain(url: str) -> str:
    """Extract the lowercase domain from a URL."""
    netloc = urlparse(url).netloc
    return netloc.lower()


def is_valid_url(url: str) -> bool:
    """Return True if *url* has both a scheme and a netloc."""
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)
