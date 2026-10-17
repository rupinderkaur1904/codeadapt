# Timeout classification under load (2026-10-17)

Raw measurement behind docs/component-interfaces.md §3.1. Run from `backend/`:
`uv run python ../docs/evaluation/sandbox-timeouts-2026-10-17/tle_probe.py RUNS LOAD`,
where LOAD is the number of busy-loop processes started on the host first.

Environment: the development container (4 vCPUs, runc, image `codeadapt-sandbox:gcc14.2-1`).
Tuples are (status, timed_out, signal).

```text
{"load_procs": 0, "runs": 24, "reference": {"counts": {"('ok', False, None)": 24}, "wall_ms_min_med_max": [241, 292, 315]}, "no_progress_update": {"counts": {"('time_limit', False, 24)": 24}, "wall_ms_min_med_max": [2275, 2317, 2409]}}
{"load_procs": 8, "runs": 24, "reference": {"counts": {"('ok', False, None)": 24}, "wall_ms_min_med_max": [341, 459, 554]}, "no_progress_update": {"counts": {"('time_limit', True, 9)": 24}, "wall_ms_min_med_max": [3174, 3253, 3379]}}
{"load_procs": 16, "runs": 24, "reference": {"counts": {"('ok', False, None)": 24}, "wall_ms_min_med_max": [352, 500, 669]}, "no_progress_update": {"counts": {"('time_limit', True, 9)": 24}, "wall_ms_min_med_max": [3223, 3329, 3407]}}
```

Signal 24 is SIGXCPU (the CPU-time limit); signal 9 with `timed_out` is the wall deadline
followed by `docker kill`. CPU load did not reproduce the CI event in which a trivial run
was recorded as a time limit.
