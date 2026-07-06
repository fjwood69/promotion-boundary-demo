"""Output C — one of three check_health versions the agent produced."""
import http_client


def check_health(url):
    return http_client.get(url)      # one attempt, no retry
