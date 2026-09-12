from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """
    Resolves the real visitor IP. The backend runs behind HuggingFace Spaces'
    reverse proxy, so request.client.host would otherwise be the proxy's IP
    for every visitor. Falls back to the direct connection IP locally, where
    there's no proxy setting the header.

    Takes the LAST entry in X-Forwarded-For, not the first. HF doesn't
    document how their proxy populates this header, so we can't assume it's
    a single trusted hop that overwrites the header outright — if a client
    sends their own X-Forwarded-For and the proxy appends to it rather than
    replacing it, the first entry is attacker-controlled and the rate limit
    becomes trivially bypassable (a new fake IP on every request). The last
    entry is always the one the proxy closest to us actually observed and
    added, so it's the only value in the chain we can trust regardless of
    how many hops came before it.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_ip)
