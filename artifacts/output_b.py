"""Output B — one of three check_health versions the agent produced."""
import http_client


def _safe_get(url):
    try:
        return http_client.get(url)
    except http_client.TransientError:
        return "unavailable"          # swallows the failure — returns a status instead


def check_health(url):
    for _ in range(3):                # looks like a retry loop...
        result = _safe_get(url)
        if result:
            return result             # ...but _safe_get never signals failure, so this
    return None                       #    returns on attempt 1 and never loops again
