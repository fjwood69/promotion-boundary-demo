"""STATIC check (Tier-2, AST) — verifies what the code *looks like*.

A plausible, reasonable heuristic for "this module retries the call": the source
contains a loop (`for`/`while`) AND the outbound `http_client.get(...)` call is
wrapped in a `try/except`. That is the structure of a retry.

It is genuinely useful — it catches the naive single-attempt violation (no loop
at all). But it matches *structure*, and structure is not behaviour. Output B has
both — a loop, and a `try/except` around the call — yet never retries: the
`try/except` lives in a helper that *swallows* the failure and returns a truthy
status, so the loop returns on its first iteration. Catching that statically
needs whole-program dataflow (does the helper swallow? does the loop return on
iteration 1?) — the enumeration treadmill the PBGF paper (moriapp.dev/pbgf,
Part 6) documents. Running the code catches it in one step.
"""
import ast


def _calls_http_get(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get":
            return True
    return False


def _has_loop(tree):
    return any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))


def _has_error_handled_call(tree):
    """A try/except somewhere in the module wrapping the outbound get() call."""
    return any(isinstance(n, ast.Try) and _calls_http_get(n) for n in ast.walk(tree))


def check(path):
    """Return (verdict, reason). verdict in {'PASS','FAIL'}."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    if _has_loop(tree) and _has_error_handled_call(tree):
        return "PASS", "looks like a retry — a loop, and the call wrapped in try/except"
    return "FAIL", "doesn't look like a retry — no loop, or the call isn't error-handled"
