"""Scratch design tool: native matrix, oracle check, random-input separation (design time only).

Usage (from the repository root):
  python3 docs/content-design/expansion-2026-10-25/native_matrix.py \
      docs/content-design/expansion-2026-10-25/<slug> --content content/demo/<slug> [--random N]
Needs g++ (C++20) on the host. --write regenerates problem.toml in the content directory; the
committed `distinguishes` fields are then checked by `codeadapt-content validate` in the sandbox.

spec.py defines:
  HEADER  str, problem.toml up to the tests
  TESTS   list of dict: key, input, probes, desc, purpose[, sample]
  MODELS  str, the [[error_models]] TOML
  check(input) -> str            Python oracle for the expected output
  RANDOM(rng) -> str             a random valid input (for separation checks)
Optional directory alternatives/*.cpp: plausible programs with a *different* cause; each is
compared with every model on the random inputs to detect non-unique attribution (L20).
The sandbox validator stays authoritative for the committed `distinguishes` fields.
"""
import json, os, random, subprocess, sys, tempfile, runpy
from concurrent.futures import ThreadPoolExecutor

d = os.path.abspath(sys.argv[1])
c = os.path.abspath(sys.argv[sys.argv.index("--content") + 1]) if "--content" in sys.argv else d
N = int(sys.argv[sys.argv.index("--random") + 1]) if "--random" in sys.argv else 300
spec = runpy.run_path(os.path.join(d, "spec.py"))
tests = spec["TESTS"]
models = sorted(f[:-4] for f in os.listdir(os.path.join(c, "error_models")) if f.endswith(".cpp"))
alt_dir = os.path.join(d, "alternatives")
alts = sorted(f[:-4] for f in os.listdir(alt_dir) if f.endswith(".cpp")) if os.path.isdir(alt_dir) else []
bdir = tempfile.mkdtemp()


def build(name, src):
    out = os.path.join(bdir, name)
    r = subprocess.run(["g++", "-O2", "-std=c++20", "-Wall", "-o", out, os.path.join(c, "harness.cpp"), src],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"compile {name}: {r.stderr[:2000]}")
    return out


srcs = {"reference": os.path.join(c, "reference.cpp")}
srcs.update({m: os.path.join(c, "error_models", m + ".cpp") for m in models})
srcs.update({a: os.path.join(alt_dir, a + ".cpp") for a in alts})
with ThreadPoolExecutor(8) as ex:
    bins = dict(zip(srcs, ex.map(lambda kv: build(*kv), srcs.items())))


def run(b, inp):
    try:
        r = subprocess.run([b], input=inp, capture_output=True, text=True, timeout=3)
        return " ".join(r.stdout.split()) if r.returncode == 0 else f"RE{r.returncode}"
    except subprocess.TimeoutExpired:
        return "TLE"


def run_all(names, inputs):
    jobs = [(n, i) for n in names for i in range(len(inputs))]
    with ThreadPoolExecutor(8) as ex:
        outs = list(ex.map(lambda j: run(bins[j[0]], inputs[j[1]]), jobs))
    res = {n: [None] * len(inputs) for n in names}
    for (n, i), o in zip(jobs, outs):
        res[n][i] = o
    return res


names = ["reference", *models, *alts]
tin = [t["input"] for t in tests]
tres = run_all(["reference", *models], tin)
ref = tres["reference"]
bad = False
for i, t in enumerate(tests):
    exp = spec["check"](t["input"])
    if ref[i] != str(exp):
        print(f"!! reference disagrees with oracle on {t['key']}: {ref[i]} vs {exp}")
        bad = True
    if ref[i].startswith(("RE", "TLE")):
        print(f"!! reference failed on {t['key']}: {ref[i]}")
        bad = True
w = max(len(t["key"]) for t in tests)
print("test".ljust(w), "ref".rjust(10), " ".join(m[:12].rjust(12) for m in models))
for i, t in enumerate(tests):
    print(t["key"].ljust(w), ref[i][:10].rjust(10),
          " ".join(("·" if tres[m][i] == ref[i] else tres[m][i][:12]).rjust(12) for m in models))
# behaviour groups (ADR-019 approximation): tests with the same pass/fail vector over all models
vec = {i: tuple(tres[m][i] != ref[i] for m in models) for i in range(len(tests))}
groups = {}
for i, v in vec.items():
    groups.setdefault(v, []).append(i)
print()
for m in models:
    fails = [i for i in range(len(tests)) if tres[m][i] != ref[i]]
    g = {vec[i] for i in fails}
    kinds = sorted({tres[m][i][:3] for i in fails if tres[m][i].startswith(("RE", "TLE"))})
    print(f"  {m}: {len(fails)} detecting tests, {len(g)} behaviour groups {kinds or ''}")
# identical signatures between models on the tests (collision on the test set)
for a in models:
    for b in models:
        if a < b and tres[a] == tres[b]:
            print(f"!! {a} and {b} identical on every test (collision)")
            bad = True

rng = random.Random(20261025)
rin = [spec["RANDOM"](rng) for _ in range(N)]
rres = run_all(names, rin)
for i, inp in enumerate(rin):
    exp = str(spec["check"](inp))
    if rres["reference"][i] != exp:
        print(f"!! reference disagrees with oracle on random input: {inp[:80]} -> {rres['reference'][i]} vs {exp}")
        bad = True
        break
print(f"\nrandom inputs: {N}")
for m in models + alts:
    diff = sum(rres[m][i] != rres["reference"][i] for i in range(N))
    print(f"  {m}: differs from reference on {diff}/{N}")
for a in models:
    for b in models + alts:
        if a == b or (b in models and b < a):
            continue
        same = sum(rres[a][i] == rres[b][i] for i in range(N))
        wrong_a = sum(rres[a][i] != rres["reference"][i] for i in range(N))
        both_wrong_same = sum(rres[a][i] == rres[b][i] != rres["reference"][i] for i in range(N))
        if wrong_a and both_wrong_same == wrong_a and same == N:
            print(f"!! {a} == {b} on every random input" + (" (alternative cause: NON-UNIQUE attribution)" if b in alts else " (collision)"))
        elif b in alts:
            print(f"   {a} vs {b}: identical on {same}/{N}")
if "--write" in sys.argv and not bad:
    out = [spec["HEADER"].rstrip() + "\n"]
    for i, t in enumerate(tests):
        dist = sorted(m for m in models if tres[m][i] != ref[i])
        vis = 'visibility = "sample"\n' if t.get("sample") else ""
        out.append(f'''[[tests]]
key = "{t['key']}"
{vis}input = "{t['input']}"
expected = "{ref[i]}"
probes = {json.dumps(t['probes'])}
student_description = "{t['desc']}"
purpose = "{t['purpose']}"
distinguishes = {json.dumps(dist)}
''')
    open(os.path.join(c, "problem.toml"), "w").write("\n".join(out) + "\n" + spec["MODELS"].strip() + "\n")
    print("wrote problem.toml")
elif bad:
    print("NOT written (problems above)")
