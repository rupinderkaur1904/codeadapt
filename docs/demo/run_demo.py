"""Submit four lower-bound programs to a running dev API and print what each audience sees.

Needs the API and worker running in dev mode (docs/demo.md). Standard library only.
Usage: python3 docs/demo/run_demo.py [--api http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELDOUT = ROOT / "eval/heldout/lower-bound"
# (label, author-written held-out program, what the author intended it to contain)
PROGRAMS = [
    ("correct", "correct_iterative.cpp", "correct"),
    ("modelled bug", "upper_bound_closed.cpp", "upper_bound_confusion"),
    ("two bugs at once", "double_bug.cpp", "unmodelled"),
    ("loop that never ends", "size_t_stuck_left.cpp", "no_progress_update"),
]


def call(api: str, path: str, role: str, body: dict[str, object] | None = None) -> object:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        api + path,
        data=data,
        method="POST" if body is not None else "GET",
        headers={"X-Dev-Role": role, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read() or b"null")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    for label, name, intended in PROGRAMS:
        source = (HELDOUT / name).read_text()
        accepted = call(args.api, "/api/v1/submissions", "student",
                        {"problem_slug": "lower-bound", "source": source})
        sub_id = accepted["id"]  # type: ignore[index]
        deadline = time.monotonic() + args.timeout
        while True:
            view = call(args.api, f"/api/v1/submissions/{sub_id}", "student")
            if view["status"] in ("completed", "failed") or time.monotonic() > deadline:  # type: ignore[index]
                break
            time.sleep(2)
        trace = call(args.api, f"/api/v1/research/submissions/{sub_id}/trace", "researcher")
        diagnosis = trace.get("diagnosis") or {}  # type: ignore[union-attr]
        feedback = view.get("feedback") or {}  # type: ignore[union-attr]
        print(f"== {label} ({name}; author's intent: {intended})")
        print(f"   job status:       {view['status']}")  # type: ignore[index]
        print(f"   outcome:          {diagnosis.get('outcome')}")
        print(f"   selected model:   {diagnosis.get('selected_model')}")
        print(f"   student feedback: {feedback.get('kind')}: {feedback.get('message')}")
        if feedback.get("hint"):
            print(f"   student hint:     {feedback['hint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
