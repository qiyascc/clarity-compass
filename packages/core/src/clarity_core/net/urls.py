from urllib.parse import SplitResult, urlsplit, urlunsplit

ALLOWED_SCHEMES = frozenset({"http", "https"})
DEFAULT_PORTS = {"http": 80, "https": 443}


class InvalidUrlError(ValueError):
    pass


def normalize_url(raw: str) -> str:
    candidate = raw.strip()
    if not candidate:
        raise InvalidUrlError("empty url")
    if "://" not in candidate and ":" not in candidate.split("/", 1)[0]:
        candidate = f"https://{candidate}"

    parts = urlsplit(candidate)
    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise InvalidUrlError(f"unsupported scheme: {parts.scheme or '<none>'}")
    if parts.username or parts.password:
        raise InvalidUrlError("credentials in url are not allowed")
    if not parts.hostname:
        raise InvalidUrlError("missing host")

    try:
        port = parts.port
    except ValueError as exc:
        raise InvalidUrlError("invalid port") from exc

    host = _encode_host(parts.hostname)
    netloc = host if port in (None, DEFAULT_PORTS[scheme]) else f"{host}:{port}"
    return urlunsplit(SplitResult(scheme, netloc, parts.path or "/", parts.query, ""))


def site_key(url: str) -> str:
    host = urlsplit(url).hostname or ""
    return host.removeprefix("www.")


def same_site(a: str, b: str) -> bool:
    return site_key(a) == site_key(b)


def _encode_host(hostname: str) -> str:
    host = hostname.lower().rstrip(".")
    if ":" in host:
        return f"[{host}]"
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise InvalidUrlError(f"invalid host: {hostname}") from exc
