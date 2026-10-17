"""Measure how timeouts are reported: genuine loop vs trivial program, idle vs loaded."""
import asyncio, collections, json, subprocess, sys
from pathlib import Path
from codeadapt.content import load_problem
from codeadapt.execution import DockerSandbox
from codeadapt.execution.models import BuildProfile

N = int(sys.argv[1]); LOAD = int(sys.argv[2])
p = load_problem(Path(__file__).resolve().parents[3] / "content/demo/lower-bound")
tests = {t.key: t for t in p.spec.tests}
cases = [("reference", p.reference, "duplicates_middle"),
         ("no_progress_update", p.error_model_sources["no_progress_update"], "single_above")]

async def main():
    hogs = [subprocess.Popen([sys.executable, "-c", "while True: pass"]) for _ in range(LOAD)]
    try:
        sb = DockerSandbox()
        out = {}
        for label, src, key in cases:
            async with sb.job() as job:
                assert (await job.compile(p.program(src), BuildProfile.STANDARD)).status.value == "ok"
                res = await asyncio.gather(*(job.run(tests[key].input.encode()) for _ in range(N)))
            c = collections.Counter((r.status.value, r.timed_out, r.signal) for r in res)
            walls = sorted(r.wall_ms for r in res)
            out[label] = {"counts": {str(k): v for k, v in c.items()},
                          "wall_ms_min_med_max": [walls[0], walls[len(walls)//2], walls[-1]]}
        print(json.dumps({"load_procs": LOAD, "runs": N, **out}))
    finally:
        for h in hogs: h.kill()
asyncio.run(main())
