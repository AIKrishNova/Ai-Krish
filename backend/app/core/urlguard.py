"""SSRF guard for configurable provider URLs. Pure stdlib."""
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    pass


def _ip_is_public(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
                or addr.is_reserved or addr.is_unspecified)


def validate_provider_url(url: str, allowed_suffixes: list[str], *, allow_http_localhost: bool = False, resolve: bool = True) -> str:
    """Return the normalized URL or raise UnsafeURLError.

    Rules: https only (http only for localhost when explicitly allowed for dev), no userinfo,
    host must match an allowed suffix, and every resolved address must be public.
    DNS can change between validation and connection (rebinding); an egress firewall is the
    defense in depth documented in docs/security.md.
    """
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if not host:
        raise UnsafeURLError("URL has no host")
    if p.scheme not in {"http", "https"}:
        raise UnsafeURLError("Unsupported URL scheme")
    if p.username or p.password:
        raise UnsafeURLError("Credentials in URL are not allowed")
    is_local = host in {"localhost", "127.0.0.1", "::1"}
    if is_local:
        if not allow_http_localhost:
            raise UnsafeURLError("Local addresses are not allowed")
        return url.rstrip("/")
    if p.scheme != "https":
        raise UnsafeURLError("Only https is allowed")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise UnsafeURLError("IP-literal hosts are not allowed")
    if not any(host == s.lstrip(".") or host.endswith("." + s.lstrip(".")) for s in allowed_suffixes):
        raise UnsafeURLError("Host is not in the allowed provider host list")
    if resolve:
        try:
            infos = socket.getaddrinfo(host, p.port or 443, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise UnsafeURLError(f"Host did not resolve: {exc}") from exc
        for info in infos:
            if not _ip_is_public(info[4][0]):
                raise UnsafeURLError("Host resolves to a non-public address")
    return url.rstrip("/")
