# Lost-output probe results (2026-10-22)

Run `lost-output-probe` #1 on commit 26a148f
(https://github.com/rupinderkaur1904/codeadapt/actions/runs/39721322428): six GitHub-hosted
ubuntu-24.04 runners (3 idle, 3 with one busy loop per core), 1,500 runs per variant,
concurrency 4.

| Runner | production | json-log | no-init | create-start |
| --- | --- | --- | --- | --- |
| cpu-loaded 1 | 1499 ok, 1 inconclusive | 1500 ok | 1500 ok | 1499 ok, 1 inconclusive |
| cpu-loaded 2 | 1500 ok | 1499 ok, 1 inconclusive | 1500 ok | 1500 ok |
| other four | job succeeded; result files the same size (443–468 bytes) as the two above, i.e. no lost-run entries |

Lost output (a run that ended by itself without its end-of-output marker, or with wrong
output): **0** in the 12,000 runs read line by line, and no lost-run entries in the other
24,000. The inconclusive runs are wall-clock stalls (ADR-023), not lost output.
Locally (4 cores, 8 busy loops, concurrency 16): 0 in 1,700 runs.

**Reading.** The event seen on d4c218a and d3919b0 does not reproduce with short synthetic
runs on today's runners, idle or loaded, under any of the four command lines. So this probe
cannot point at the part of the stream path responsible, and the root cause stays unknown.
Possible reasons: the runner image or Docker version changed since 2026-10-17, or the event
needs conditions the probe lacks (compile containers interleaved with runs, long sessions,
many volumes).

**What protects results meanwhile.** ADR-024's marker makes any such run an infrastructure
error that is re-measured and never used as evidence. Every lost run therefore leaves a
record (`detail` "output stream ended without its end-of-output marker"). Counting those
records in large runs (the VAL1-A2 and public-corpus audits) is the cheapest way to see the
event again; no further probe runs are planned unless it recurs.
