"""Audit of the 8 provisional binary-search problems: reference vs brute-force oracle on random
inputs, model-vs-model identity on random inputs, and how often each model differs from the
reference. Native g++ build; design-time check only."""
import bisect, os, random, subprocess, sys, tempfile, tomllib, math
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../content/demo")
rng = random.Random(20261025)

def sorted_arr(n, lo=-50, hi=50, strict=False):
    if strict:
        return sorted(rng.sample(range(lo, hi + n), n))
    return sorted(rng.randint(lo, hi) for _ in range(n))

def rot(a):
    k = rng.randrange(len(a)); return a[k:] + a[:k]

def gen(slug):
    n = rng.randint(1, 12)
    if slug == "integer-sqrt":
        x = rng.choice([rng.randint(0, 200), rng.randint(0, 2**31 - 1), rng.randint(46000**2, 2**31 - 1)])
        return f"{x}\n", math.isqrt(x)
    if slug in ("upper-bound", "last-occurrence"):
        a = sorted_arr(n, -5, 5); t = rng.randint(-7, 7)
        inp = f"L {n} {' '.join(map(str, a))} {t}\n"
        if slug == "upper-bound": return inp, bisect.bisect_right(a, t)
        i = bisect.bisect_right(a, t) - 1
        return inp, i if i >= 0 and a[i] == t else -1
    if slug == "exact-search":
        a = sorted_arr(n, -20, 20, strict=True); t = rng.choice(a + [rng.randint(-25, 45)])
        return f"L {n} {' '.join(map(str, a))} {t}\n", a.index(t) if t in a else -1
    if slug == "min-capacity":
        w = [rng.randint(1, 10) for _ in range(n)]; d = rng.randint(1, n)
        def ok(c):
            days, cur = 1, 0
            for x in w:
                if cur + x > c: days += 1; cur = 0
                cur += x
            return days <= d
        c = max(w)
        while not ok(c): c += 1
        return f"L {n} {' '.join(map(str, w))} {d}\n", c
    if slug == "rotated-min":
        a = rot(sorted_arr(n, -30, 30, strict=True))
        return f"L {n} {' '.join(map(str, a))}\n", a.index(min(a))
    if slug == "rotated-search":
        a = rot(sorted_arr(n, -30, 30, strict=True)); t = rng.choice(a + [rng.randint(-35, 45)])
        return f"L {n} {' '.join(map(str, a))} {t}\n", a.index(t) if t in a else -1
    if slug == "peak-index":
        p = rng.randrange(n)
        left = sorted(rng.sample(range(0, 100), p + 1))
        right = sorted(rng.sample(range(0, left[-1]), min(n - p - 1, left[-1])), reverse=True)
        a = left + right
        return f"L {len(a)} {' '.join(map(str, a))}\n", p
    raise SystemExit(slug)

def build(d, name, src):
    out = os.path.join(d, name)
    r = subprocess.run(["g++", "-O2", "-std=c++20", "-o", out, f"{ROOT}/{slug}/harness.cpp", src], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"{name}: {r.stderr[:500]}")
    return out

def run(b, inp):
    try:
        r = subprocess.run([b], input=inp, capture_output=True, text=True, timeout=3)
        return r.stdout.strip() if r.returncode == 0 else f"RE{r.returncode}"
    except subprocess.TimeoutExpired:
        return "TLE"

slug = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 600
p = tomllib.load(open(f"{ROOT}/{slug}/problem.toml", "rb"))
models = [m["key"] for m in p["error_models"]]
d = tempfile.mkdtemp()
srcs = {"reference": f"{ROOT}/{slug}/reference.cpp", **{m: f"{ROOT}/{slug}/error_models/{m}.cpp" for m in models}}
extra = sys.argv[3:]  # optional extra programs (paths) to compare with the reference
srcs.update({os.path.basename(x)[:-4]: x for x in extra})
with ThreadPoolExecutor(8) as ex:
    bins = dict(zip(srcs, ex.map(lambda kv: build(d, *kv), srcs.items())))
cases = [gen(slug) for _ in range(N)]
names = list(bins)
with ThreadPoolExecutor(8) as ex:
    outs = {n: list(ex.map(lambda c: run(bins[n], c[0]), cases)) for n in names}
bad = [(c[0].strip()[:80], outs["reference"][i], c[1]) for i, c in enumerate(cases) if outs["reference"][i] != str(c[1])]
print(f"== {slug}: {N} random inputs; reference disagrees with brute force on {len(bad)}")
for b in bad[:5]: print("   ", b)
ref = outs["reference"]
for m in names[1:]:
    diff = sum(o != r for o, r in zip(outs[m], ref))
    kinds = sorted({o[:3] for o in outs[m] if o.startswith(("RE", "TLE"))})
    print(f"   {m:28} differs from reference on {diff}/{N} {kinds or ''}")
for i, a in enumerate(names[1:]):
    for b in names[2 + i:]:
        if outs[a] == outs[b]:
            print(f"!! {a} and {b} identical on every random input")
