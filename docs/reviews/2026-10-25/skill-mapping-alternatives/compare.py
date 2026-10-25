"""Compare alternative-cause programs with an error model, natively (review evidence only).

Usage (from the repository root, needs g++):
    python3 docs/reviews/2026-10-25/skill-mapping-alternatives/compare.py \
        <problem-slug> <error-model-key> <alternative.cpp>...

For each alternative it prints the tests on which its output differs from the error model's,
the number of differing outputs on 400 seeded random valid inputs, and the tests it fails.
Native runs approximate the sandbox; they are not the authoritative measurement.
"""

import random
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

slug, model_key, *alts = sys.argv[1:]
problem = Path("content/demo") / slug
spec = tomllib.loads((problem / "problem.toml").read_text())


def build(src: Path) -> str:
    out = tempfile.mktemp()
    cmd = ["g++", "-O2", "-std=c++20", "-o", out, str(problem / "harness.cpp"), str(src)]
    subprocess.run(cmd, check=True)
    return out


def run(binary: str, stdin: str) -> str:
    try:
        r = subprocess.run([binary], input=stdin, capture_output=True, text=True, timeout=3)
    except subprocess.TimeoutExpired:
        return "TLE"
    return r.stdout.strip() if r.returncode == 0 else f"RE{r.returncode}"


def random_inputs() -> list[str]:
    rng = random.Random(1)
    inputs = []
    for _ in range(400):
        n = rng.randint(1, 12)
        if slug == "rotated-min":
            values = sorted(rng.sample(range(-50, 50), n))
            k = rng.randrange(n)
            inputs.append("L %d %s" % (n, " ".join(map(str, values[k:] + values[:k]))))
        elif slug == "min-capacity":
            weights = [rng.randint(1, 20) for _ in range(n)]
            inputs.append("L %d %s %d" % (n, " ".join(map(str, weights)), rng.randint(1, n)))
        else:
            sys.exit(f"no random generator for {slug}")
    return inputs


model = build(problem / "error_models" / f"{model_key}.cpp")
reference = build(problem / "reference.cpp")
rand = random_inputs()
for alt in alts:
    b = build(Path(alt))
    differ = [t["key"] for t in spec["tests"] if run(b, t["input"]) != run(model, t["input"])]
    rdiff = sum(run(b, i) != run(model, i) for i in rand)
    fails = [t["key"] for t in spec["tests"] if run(b, t["input"]) != run(reference, t["input"])]
    print(f"{Path(alt).name} vs {model_key}")
    print(f"  tests with different output: {differ}")
    print(f"  random inputs with different output: {rdiff}/400")
    print(f"  tests failed: {len(fails)}/{len(spec['tests'])}")
