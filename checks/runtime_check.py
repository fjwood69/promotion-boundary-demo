"""RUNTIME check (the product identity) — verifies what the code *does*.

Execute the artifact against an injected fault and observe the behaviour. Here:
inject a transient failure on every attempt, run `check_health`, and count how
many times the outbound call was actually made. Two or more attempts = it
retried; one = it did not. The check never inspects the source — it observes
execution, so it does not care *how* the retry is (or isn't) expressed.

DEMO MECHANISM NOTE — HONEST LABEL. This demo counts attempts with an
*in-process* monkeypatch (zero dependencies, runs anywhere with just Python).
That is fine to *demonstrate the idea*, but it is the WEAK isolation tier: an
adversarial artifact could reach around the patch (an un-mocked client) or forge
the counter. The production gate does NOT do this — it observes egress at the
*sandbox boundary* (`--network=none` + host-side flow counting), outside the
artifact's reach. See moriapp.dev/pbgf.
"""
import importlib

import http_client

DUMMY_URL = "https://svc.internal/health"


def check(artifact_module, on_attempt=None):
    """Return (verdict, reason). verdict in {'PASS','FAIL','ERROR'}.

    on_attempt(n, url): optional callback invoked on each observed outbound
    attempt — lets a caller narrate the execution live (see demo.py --step).
    """
    attempts = {"n": 0}
    original_get = http_client.get

    def failing_get(url):
        attempts["n"] += 1
        if on_attempt is not None:
            on_attempt(attempts["n"], url)
        raise http_client.TransientError("injected transient failure")

    http_client.get = failing_get
    try:
        mod = importlib.import_module(f"artifacts.{artifact_module}")
        importlib.reload(mod)
        try:
            mod.check_health(DUMMY_URL)
        except Exception:
            pass                      # the injected failure is expected to propagate
    finally:
        http_client.get = original_get

    n = attempts["n"]
    if n == 0:
        return "ERROR", "the artifact never made the outbound call"
    if n >= 2:
        return "PASS", f"retried — {n} attempts observed under injected failure"
    return "FAIL", f"did not retry — {n} attempt observed under injected failure"
