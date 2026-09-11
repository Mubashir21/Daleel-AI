from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """
    Resolves the real visitor IP. The backend runs behind HuggingFace Spaces'
    reverse proxy, so request.client.host would otherwise be the proxy's IP
    for every visitor. Falls back to the direct connection IP locally, where
    there's no proxy setting the header.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_ip)
