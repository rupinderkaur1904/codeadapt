"""Run held-out programs of every non-binary-search problem through a running dev API and worker.

For each problem: the first correct, the first modelled and the first unmodelled held-out case
(synthetic, author-written). Prints what the pipeline recorded and checks it against the case's
label: correct -> no failure observed; modelled -> that model named; unmodelled -> abstention.
Then reads the researcher's learner-model view for the dev student. Engineering check only: it
shows the pipeline handles the grown bank, not how well diagnosis works on real code.

Needs the API and worker running in dev mode (docs/demo.md). Standard library only.
Usage: python3 docs/demo/bank_check.py [--api http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import time
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEW_FAMILIES = {"arrays", "two-pointers", "sliding-window", "prefix-sums"}


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


def submit(api: str, slug: str, source: str, timeout: float) -> tuple[dict, dict]:  # type: ignore[type-arg]
    sub = call(api, "/api/v1/submissions", "student", {"problem_slug": slug, "source": source})
    deadline = time.monotonic() + timeout
    while True:
        view = call(api, f"/api/v1/submissions/{sub['id']}", "student")  # type: ignore[index]
        if view["status"] in ("completed", "failed") or time.monotonic() > deadline:  # type: ignore[index]
            break
        time.sleep(2)
    trace = call(api, f"/api/v1/research/submissions/{sub['id']}/trace", "researcher")  # type: ignore[index]
    return view, trace  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument(
        "--slugs", nargs="*", help="check these problems instead of every non-binary-search one"
    )
    args = parser.parse_args()
    problems = call(args.api, "/api/v1/problems", "student")
    print(f"problems listed: {len(problems)}")  # type: ignore[arg-type]
    failures = 0
    for p in problems:  # type: ignore[union-attr]
        if (p["slug"] not in args.slugs) if args.slugs else (p["family"] not in NEW_FAMILIES):
            continue
        cases = tomllib.loads((ROOT / "eval/heldout" / p["slug"] / "cases.toml").read_text())
        picks = {}
        for c in cases["cases"]:
            kind = c["truth"] if c["truth"] in ("correct", "unmodelled") else "modelled"
            picks.setdefault(kind, c)
        for kind in ("correct", "modelled", "unmodelled"):
            case = picks[kind]
            source = (ROOT / "eval/heldout" / p["slug"] / case["file"]).read_text()
            view, trace = submit(args.api, p["slug"], source, args.timeout)
            d = trace.get("diagnosis") or {}
            rec = trace.get("recommendation") or {}
            outcome, model = d.get("outcome"), d.get("selected_model")
            if kind == "correct":
                ok = outcome == "no_failure_observed"
            elif kind == "modelled":
                ok = outcome == "hypothesis_supported" and model == case["truth"]
            else:
                ok = outcome not in ("hypothesis_supported", "no_failure_observed")
            failures += not ok
            print(
                f"{'ok ' if ok else 'BAD'} {p['slug']:22} {kind:10} {case['file']:28} "
                f"status={view['status']} outcome={outcome} model={model} "
                f"action={rec.get('action')} next={rec.get('problem_slug')}"
            )
    lm = call(args.api, "/api/v1/research/learner-model?username=dev-student", "researcher")
    estimate = lm["estimate"]  # type: ignore[index]
    print(f"learner model: {lm['attempts']} attempts; {estimate['label']}")  # type: ignore[index]
    for s in estimate["skills"]:
        print(f"skill {s['skill']:24} counted={s['counted']} problems={s['distinct_problems']} "
              f"state={s['state']} p_known={s['p_known']}")
    print(f"label mismatches: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
