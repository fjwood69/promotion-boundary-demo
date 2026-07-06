#!/usr/bin/env python3
"""Promotion-Boundary Demo (Deliverable Zero): the stake in the ground.

One rule ("retry the readiness probe on transient failure"), three versions of
the code, two checks. The point, made runnable:

    the same version PASSES a check that reads the code and FAILS the moment
    that code is executed.

One check reads what the code looks like. The other runs it and watches what it
does. Full framework, every null, every receipt: https://moriapp.dev/pbgf

Usage:
    python3 demo.py            # guided step-through (default) — pauses in a terminal
    python3 demo.py --table    # just the summary verdict table (quick / CI)
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from checks import static_check, runtime_check  # noqa: E402

# (module, label) — labels are deliberately neutral: you should NOT be able to
# tell which one actually retries from its name. The checks reveal that.
ARTEFACTS = [
    ("output_a", "Output A"),
    ("output_b", "Output B"),
    ("output_c", "Output C"),
]

TREE = [
    ("AGENTS.md",               "the rule the agent must follow"),
    ("artifacts/output_a.py",   "Output A ─┐"),
    ("artifacts/output_b.py",   "Output B ─┤ three versions of check_health —"),
    ("artifacts/output_c.py",   "Output C ─┘ which one actually retries?"),
    ("checks/static_check.py",  "reads the code — does it LOOK like a retry?"),
    ("checks/runtime_check.py", "runs the code  — does it ACTUALLY retry?"),
]


_MARK = {"PASS": "✓", "FAIL": "✗", "ERROR": "⚠"}


def _v(verdict):
    """Decorate a verdict with its symbol, e.g. 'PASS ✓' / 'FAIL ✗'."""
    return f"{verdict} {_MARK.get(verdict, '')}".rstrip()


def _source_of(name):
    # show the whole artefact from its first def onward (skip the module docstring
    # + import) — so Output B's swallowing helper is visible, not just check_health.
    lines = (HERE / "artifacts" / f"{name}.py").read_text(encoding="utf-8").splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("def ")), 0)
    return "\n".join(lines[start:]).rstrip("\n")


def _pause(pause, prompt="        [enter] to continue → "):
    if pause and sys.stdin.isatty():
        try:
            input(prompt)
            print()
        except EOFError:
            pass


def _agents_rule():
    """The convention text — read from AGENTS.md (single source of truth), de-marked."""
    txt = (HERE / "AGENTS.md").read_text(encoding="utf-8")
    if "## Convention" in txt:
        txt = txt[txt.index("## Convention"):]
    if "\n> " in txt:
        txt = txt[:txt.index("\n> ")]           # drop the trailing note (shown at the end)
    lines = [ln.replace("**", "").replace("`", "").lstrip("# ").rstrip()
             for ln in txt.splitlines()]
    return "\n".join(lines).strip()


def _header(title):
    print("  " + "═" * 66)
    print(f"  {title}")
    print("  " + "═" * 66)
    print()


# ── step-through (default) ──────────────────────────────────────────────────
def walk(pause=False):
    print()
    print("  Promotion-Boundary Demo")
    print()
    print("  ┃ Demonstrating a mechanism, not a gate. This demo runs the check in-process")
    print("  ┃ for zero-dependency teaching. The real enforcement gate runs the code in an")
    print("  ┃ isolated sandbox at the merge boundary and counts network egress from")
    print("  ┃ outside the container — the code can't tamper with the verdict because it")
    print("  ┃ doesn't share the process. Why that matters: https://moriapp.dev/pbgf")
    print()

    _header("THE SCENARIO — what we need the agent to do")
    print("  You ask a coding agent to add a readiness probe: a small function that")
    print("  GETs a service's /health endpoint to confirm it is alive. Networks blip,")
    print('  so a probe that gives up on the first hiccup flaps the service as "down"')
    print("  constantly. It has to survive a transient failure — and whether it does")
    print("  is a rule someone has to write down and enforce.")
    print()
    _pause(pause)

    _header("THE SETUP — the rule the agent is given")
    print("  Team rules live in AGENTS.md — the file every coding agent reads before")
    print("  it works. Here is this repo's rule, as written:")
    print()
    for line in _agents_rule().splitlines():
        print(("      " + line) if line else "")
    print()
    print("  The agent gave you three versions of check_health — Output A, B and C.")
    print("  From the outside you can't tell which one actually retries. Two checks try:")
    print()
    print("    •  the STATIC check READS the code — it parses the text and looks for a")
    print("       retry written into it (a loop that re-tries the call). It never runs")
    print("       anything.")
    print("    •  the RUNTIME check RUNS the code — it actually executes check_health()")
    print("       with the network rigged to fail every time, and counts how many times")
    print("       the code tries the call. Tried once then gave up → it didn't retry.")
    print("       Tried again after the failure → it did.")
    print()
    for path, note in TREE:
        print(f"      {path:26}{note}")
    print()
    _pause(pause)

    _header("THE OUTCOME — two checks judge each version")

    results = {}
    for i, (name, label) in enumerate(ARTEFACTS, 1):
        print("  " + "━" * 66)
        print(f"  {i}/3   {label}")
        print("  " + "━" * 66)
        print()

        print("  ┌─ what the agent wrote")
        for line in _source_of(name).splitlines():
            print("  │   " + line)

        s, s_reason = static_check.check(str(HERE / "artifacts" / f"{name}.py"))
        print("\n  ├─ STATIC check — reads the source; does it LOOK like a retry?")
        print(f"  │   {s_reason}")
        print(f"  │   → {_v(s)}")

        print("\n  ├─ RUNTIME check — runs it; does it ACTUALLY retry?")
        print("  │   injecting a transient failure on each attempt, calling check_health()…")

        def on_attempt(n, url):
            print(f"  │     → attempt {n}: outbound call made … 503 injected")

        r, r_reason = runtime_check.check(name, on_attempt=on_attempt)
        print(f"  │   {r_reason}")
        print(f"  │   → {_v(r)}")

        print("  │")
        if s == "PASS" and r == "FAIL":
            print(f"  └─ ▶  {label} LOOKS like a retry, so the static check approved it —")
            print("        but run it, and it gives up after one attempt. Looks compliant; isn't.")
        elif s == "PASS" and r == "PASS":
            print(f"  └─ ▶  {label} looks like a retry — and running it, it really does. Compliant.")
        else:
            print(f"  └─ ▶  {label} doesn't even look like a retry, and doesn't act like one.")
        results[name] = (s, r)
        print()
        _pause(pause, "        [enter] for the next version → ")

    print("  " + "═" * 66)
    print("  The static check judged what the code LOOKS LIKE. The runtime check")
    print("  judged what it DOES. On Output B, they disagreed — same file.")
    print()
    print("  This is NOT 'static analysis is useless' — it caught Output C. It's")
    print("  looks-like vs does: a static check matches structure, and structure can be")
    print("  faked. Output B has the retry structure — a loop, error-handling — but hides")
    print("  the missing retry in a helper the parser can't follow. A smarter linter might")
    print("  catch this one shortcut; the agent just takes another wrapper or dispatch, and")
    print("  running the code ends that structural treadmill. (Evasions that detect the test")
    print("  itself — keyed on input or environment — need the product's per-trial input and")
    print("  environment variation; this demo runs one fixed fault, so it does not catch them.)")
    print()
    print("  Output B is exactly what a coding agent under pressure produces: it looks")
    print("  compliant and isn't. This is why mori enforces at the CI merge boundary with")
    print("  runtime-state-assertions — running the artifact against injected faults — not")
    print("  static AST checks in the editor.")
    print("  The full framework — every null, every receipt: https://moriapp.dev/pbgf")
    print()
    print("  ── other ways to run this ─────────────────────────────────────────")
    print("     make table   just the three verdicts, no narration")
    print("     make demo    this guided walk  (runs straight through when piped / in CI)")
    print()
    return 0 if results.get("output_b") == ("PASS", "FAIL") else 1


# ── terse table (--table) ───────────────────────────────────────────────────
def table():
    print()
    print("  Promotion-Boundary Demo")
    print()
    print(f"  {'':10}{'static':18}{'runtime':18}")
    print(f"  {'':10}{'(reads the code)':18}{'(runs the code)':18}")
    print("  " + "─" * 50)
    rows = {}
    for name, label in ARTEFACTS:
        s, _ = static_check.check(str(HERE / "artifacts" / f"{name}.py"))
        r, _2 = runtime_check.check(name)
        rows[name] = (s, r)
        flag = "◄ caught only by running it" if (s == "PASS" and r == "FAIL") else ""
        print(f"  {label:10}{_v(s):18}{_v(r):10}{flag}")
    print("  " + "─" * 50)
    print("  Static checks what the code LOOKS LIKE; runtime checks what it DOES.")
    print("  moriapp.dev/pbgf")
    print()
    return 0 if rows.get("output_b") == ("PASS", "FAIL") else 1


def main():
    ap = argparse.ArgumentParser(description="Promotion-Boundary Demo (Deliverable Zero)")
    ap.add_argument("--table", action="store_true", help="just the summary verdict table")
    args = ap.parse_args()
    if args.table:
        return table()
    # guided step-through is the default; it pauses only in an interactive terminal.
    return walk(pause=True)


if __name__ == "__main__":
    raise SystemExit(main())
