"""A stand-in HTTP client for the demo.

The demo never reaches a real network. The runtime check (checks/runtime_check.py)
patches `get` to inject a transient failure and count attempts. Calling this
un-patched just raises the stub error — there is nothing to connect to.
"""


class TransientError(Exception):
    """A retryable transient failure — the 503 / dropped-connection case."""


def get(url):
    raise TransientError(f"no network in the demo stub: {url}")
