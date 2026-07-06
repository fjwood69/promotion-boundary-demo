"""Output A — one of three check_health versions the agent produced."""
import http_client


def check_health(url):
    last = None
    for _ in range(3):
        try:
            return http_client.get(url)
        except http_client.TransientError as e:
            last = e
            continue          # transient failure -> try again
    raise last                # exhausted all attempts
