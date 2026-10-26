"""L20 alternative-cause search for the four original binary-search problems (review evidence).

Investigation only (owner request D, 2026-10-26): nothing here changes content or rules.
The method, driver and output format are those of docs/reviews/2026-10-25/l20-search/
search.py; only the problems, their domains and the alternative programs are new.

Usage (from the repository root, needs g++):
    python3 docs/reviews/2026-10-26/l20-search-original/search.py [slug ...]

For every alternative program in l20-search-original/<slug>/ it reports:

1. which error models give the same output on every committed test (natively). Such a model
   is the one v1.3 would consider; whether it would be *named* also depends on the rules in
   fingerprint_v1.py (no time limit, not constant, >= 2 behaviour groups, no
   known_limitation);
2. how many inputs of an exhaustive small domain and of a seeded random domain give a
   different output from that model. 0 on both is an observed equivalence on those domains;
   it is evidence, not a proof that the two programs agree on every valid input.

Native builds with libstdc++ assertions approximate the sandbox. They are not the
authoritative measurement; the sandbox fingerprints in docs/content-reports/ are.
"""

import itertools
import os
import random
import re
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DRIVER = ROOT / "docs" / "reviews" / "2026-10-25" / "l20-search" / "driver.cpp"
CONTENT = ROOT / "content" / "demo"
SLUGS = ["lower-bound", "count-occurrences", "last-less-than", "first-true"]
RANDOM_N = 3000
SEED = 20261026


def line(a, t=None):
    s = f"L {len(a)} {' '.join(map(str, a))}".rstrip()
    return s if t is None else f"{s} {t}"


def exhaustive(slug):
    """Every valid input of a small domain: short arrays over small values."""
    out = []
    if slug in ("lower-bound", "count-occurrences", "last-less-than"):
        # every non-decreasing array of length 0-6 over {0..3}, every target -1..4
        for n in range(0, 7):
            for a in itertools.combinations_with_replacement(range(4), n):
                out += [line(a, t) for t in range(-1, 5)]
    elif slug == "first-true":
        # every valid flags array of length 0-12 (k zeros, then ones)
        for n in range(0, 13):
            out += [line([0] * k + [1] * (n - k)) for k in range(n + 1)]
    return out


def randomised(slug):
    rng = random.Random(SEED)
    out = []
    for _ in range(RANDOM_N):
        if slug in ("lower-bound", "count-occurrences", "last-less-than"):
            a = sorted(rng.randint(-30, 30) for _ in range(rng.randint(0, 40)))
            out.append(line(a, rng.randint(-35, 35)))
        elif slug == "first-true":
            n = rng.randint(0, 200)
            k = rng.randint(0, n)
            out.append(line([0] * k + [1] * (n - k)))
    return out


def expand(inp):
    """Committed test input in harness format -> literal one-line form."""
    tok = inp.split()
    if not tok or tok[0] not in "LADP":
        return " ".join(tok)
    mode, n = tok[0], int(tok[1])
    if mode == "L":
        return " ".join(tok)
    if mode == "P":  # first-true: k zeros followed by n - k ones
        k = int(tok[2])
        return line([0] * k + [1] * (n - k))
    if mode == "A":
        start, step = int(tok[2]), int(tok[3])
        a, rest = [start + i * step for i in range(n)], tok[4:]
    else:
        a, rest = [int(tok[2])] * n, tok[3:]
    return line(a, *rest) if rest else line(a)


def kind_and_name(slug):
    h = (CONTENT / slug / "harness.cpp").read_text()
    m = re.search(r"^int (\w+)\((.*)\);", h, re.M)
    args = m.group(2)
    kind = "VT" if "," in args else ("V" if "vector" in args else "X")
    return kind, m.group(1)


def build(slug, src, workdir):
    kind, fn = kind_and_name(slug)
    out = os.path.join(workdir, Path(src).stem + "_" + str(abs(hash(str(src)))))
    cmd = ["g++", "-O2", "-std=c++20", "-D_GLIBCXX_ASSERTIONS", f"-DKIND_{kind}", f"-DFN={fn}",
           "-o", out, str(DRIVER), str(src)]
    subprocess.run(cmd, check=True)
    return out


def run(binary, inputs):
    r = subprocess.run([binary], input="\n".join(inputs) + "\n", capture_output=True,
                       text=True, check=True)
    return r.stdout.split("\n")[: len(inputs)]


def header(src, key):
    m = re.search(rf"// {key}: (.*)", Path(src).read_text())
    return m.group(1).strip() if m else "?"


def model_facts(slug):
    """Behaviour groups and documented limitation per model, from the sandbox report."""
    facts = {}
    report = (ROOT / "docs" / "content-reports" / f"{slug}.md").read_text()
    for m in re.finditer(r"^\| `(\w+)` \| (\w+) \| (\d+) \| (\d+) \| (.*?) \|$", report, re.M):
        facts[m.group(1)] = {"skill": m.group(2), "groups": int(m.group(4)),
                             "limitation": m.group(5).strip() != "—"}
    return facts


def search(slug):
    spec = tomllib.loads((CONTENT / slug / "problem.toml").read_text())
    models = [m["key"] for m in spec["error_models"]]
    facts = model_facts(slug)
    alts = sorted((HERE / slug).glob("*.cpp"))
    srcs = {"reference": CONTENT / slug / "reference.cpp"}
    srcs.update({m: CONTENT / slug / "error_models" / f"{m}.cpp" for m in models})
    srcs.update({p.stem: p for p in alts})
    work = tempfile.mkdtemp()
    with ThreadPoolExecutor(8) as ex:
        bins = dict(zip(srcs, ex.map(lambda s: build(slug, s, work), srcs.values())))
    tests = [expand(t["input"]) for t in spec["tests"]]
    domains = {"exhaustive": exhaustive(slug), "random": randomised(slug)}
    with ThreadPoolExecutor(8) as ex:
        on_tests = dict(zip(bins, ex.map(lambda b: run(b, tests), bins.values())))
    print(f"## {slug}: {len(tests)} committed tests; exhaustive domain "
          f"{len(domains['exhaustive'])} inputs; random domain {len(domains['random'])} inputs")
    for m in models:
        f = facts[m]
        tle = any(o == "TLE" for o in on_tests[m])
        constant = len(set(on_tests[m])) == 1
        nameable = not (tle or constant or f["limitation"] or f["groups"] < 2)
        f.update(tle=tle, constant=constant, nameable=nameable)
    ref_dom = {}
    for alt in alts:
        a = alt.stem
        fails = sum(o != r for o, r in zip(on_tests[a], on_tests["reference"]))
        same = [m for m in models if on_tests[m] == on_tests[a]]
        target = header(alt, "compare-with")
        mine = {d: run(bins[a], inputs) for d, inputs in domains.items()}
        wrong = []
        for d, inputs in domains.items():
            if ("reference", d) not in ref_dom:
                ref_dom[("reference", d)] = run(bins["reference"], inputs)
            bad = sum(x != y for x, y in zip(mine[d], ref_dom[("reference", d)]))
            wrong.append(f"{d} {bad}/{len(inputs)}")
        print(f"- {a}  [cause-skill: {header(alt, 'cause-skill')}]")
        print(f"    fails {fails}/{len(tests)} tests; wrong on " + "; ".join(wrong)
              + f"; identical on all tests to: {same or 'none'}")
        for m in dict.fromkeys(same + [target]):
            if m not in models:
                continue
            row = []
            for d, inputs in domains.items():
                key = (m, d)
                if key not in ref_dom:
                    ref_dom[key] = run(bins[m], inputs)
                diff = sum(x != y for x, y in zip(mine[d], ref_dom[key]))
                row.append(f"{d} {diff}/{len(inputs)}")
            f = facts[m]
            status = ("would be named unqualified" if f["nameable"] else
                      "not named unqualified (" + ", ".join(
                          k for k, v in (("time limit", f["tle"]), ("constant", f["constant"]),
                                         ("known_limitation", f["limitation"]),
                                         ("1 behaviour group", f["groups"] < 2)) if v) + ")")
            tdiff = sum(x != y for x, y in zip(on_tests[a], on_tests[m]))
            cause = header(alt, "cause-skill").split()[0]
            cross = "same skill" if cause == f["skill"] else "CROSS-SKILL"
            print(f"    vs {m} [{f['skill']}; {status}; {cross}]: tests {tdiff} differ; "
                  + "; ".join(row) + " differ")
    print()


for s in sys.argv[1:] or SLUGS:
    search(s)
