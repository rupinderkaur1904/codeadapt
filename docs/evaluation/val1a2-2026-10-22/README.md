# VAL1-A2 results: mutation audit of count-occurrences, last-less-than and first-true

**Status:** complete and stopped at the gate. The plan is `PLAN.md`, frozen in 794caea. Mutants and
behavioural labels were committed before any pipeline run (64b6d12, edbb8f6). The decision memo is
`MEMO.md`. Generated tables are in `results/tables.md`, and the numbers behind them in
`results/summary.json`.

**What this is.** It covers 487 synthetic single-edit mutants of three correct styles of three
problems. Each was run twice through the production evidence pipeline and diagnosed with method 1.2
(primary) and 1.1 (secondary). Each is scored against a behavioural label computed natively. The
results are not real-student evidence, not independent validation, and say nothing about learning.
Claude, an AI system working on this project, wrote the plan, the mutants' generator and these
reports.

## How to reproduce

```sh
python3 docs/evaluation/val1a2-2026-10-22/generate.py         # mutants + manifests (deterministic)
python3 docs/evaluation/val1a2-2026-10-22/label.py            # behavioural labels (native, -O1)
cd backend
uv run python ../docs/evaluation/val1a2-2026-10-22/run_audit.py 1   # pipeline, run 1 (Docker)
uv run python ../docs/evaluation/val1a2-2026-10-22/run_audit.py 2   # pipeline, run 2
cd ..
python3 docs/evaluation/val1a2-2026-10-22/native_symptoms.py  # native crash/TLE cross-check
cd backend && uv run python ../docs/evaluation/val1a2-2026-10-22/analyse.py
```

| Item | Value |
| --- | --- |
| Environment | g++ 14.2.0 under runc, image `codeadapt-sandbox:gcc14.2-1` |
| Content versions | as frozen; X2 was checked on both passes |
| Raw records | `results/<problem>.jsonl` (run 1) and `results/<problem>.run2.jsonl` (run 2): every observation and exclusion |
| Integrity | `MANIFEST.sha256` |

Pipeline time was 75 minutes per pass, against a planned estimate of 9–10 hours for both.

## Deviations from the plan

1. **The two runs were executed as two passes** (run 1 for every program, then run 2) rather than
   back to back. This changes only the order: each program still has 2 runs, compared as in §6.
2. **Behavioural labels are computed at `-O1 -std=c++17`** (§5). The pipeline builds at
   `-O2 -std=c++20`. A program whose behaviour depends on undefined behaviour can therefore differ.
   The analysis checks every labelled-reference and labelled-model mutant against its pipeline
   evidence (added after the plan). One differs: count-occurrences `A_SDL_046`. At `-O2` the
   compiler removes its side-effect-free endless loop, and the program prints 0 everywhere; at `-O1`
   it stalls like `no_progress_update`. It is counted as a wrong name, as the rule in §7 says.
3. **The native crash/TLE cross-check** (`native_symptoms.py`) **was run after the pipeline**, so
   that it did not compete with the sandbox for CPU.
4. **Two analyses were added after seeing the data** and are labelled exploratory:
   - whether each wrong name's evidence equals the named model's fingerprint;
   - whether the named model's fingerprint is constant.

No stop condition (X1–X5) was triggered:

- **X1:** all 9 originals gave `no_failure_observed`.
- **X2:** the content was unchanged.
- **X3:** 0 `execution_error`.
- **X4:** v1.1 had already reproduced every lower-bound record (`../adr027-2026-10-21/`).
- **X5:** the run took 2.5 hours.

## Results (pooled over the three problems, method 1.2)

| Metric | Result |
| --- | --- |
| Programs | 487 mutants: 323 incorrect-failing, 51 equivalent, 112 unreliable, 1 compile error, 0 suite gap |
| Reproducibility | 494/496 programs identical across the 2 runs. The 2 that differ were already unreliable |
| **Named coverage** | **50/323 (15%, CI 12–20%)**. Per problem: count-occurrences 21%, last-less-than 15%, first-true 10% |
| `non_termination_observed` | 83/323 (26%) |
| **Wrong name (behavioural)** | **11/50 (22%, CI 13–35%)**. Unqualified 11/40, qualified 0/10 |
| Wrong name per problem | count-occurrences 10/23, last-less-than 0/17, first-true 1/10 |
| Library recall, terminating models | 39/39 mutants that behave exactly like a terminating model were named as that model |
| Library recall, stalling models | 0/37, by design (ADR-027: these get the symptom outcome) |
| Style A vs B+C named coverage | 18/108 (17%) vs 32/215 (15%) |
| Unreliable by style | A 23, B 26, C 63 (recursive: mostly sanitizer stack-overflow exclusions) |
| Named diagnoses resting only on `runtime_error`/`memory_limit` | 0/50 |
| Programs with any reliable `runtime_error`/`memory_limit` | 9 (none incorrect-failing) |
| Programs with an excluded observation | heap-buffer-overflow 144, null-pointer 84, stack-overflow 39 |
| Secondary, method 1.1 on the same evidence | named 94/323 (29%), wrong 19/94 (20%) |
| Four-problem pool (adds the VAL1-A lower-bound replay) | named 60/421 (14%, CI 11–18%), wrong 11/60 (18%, CI 11–30%) |

## Pre-registered readings (§8)

| ID | Triggered? | Basis |
| --- | --- | --- |
| G0 | No | 50 named diagnoses, so precision is evaluable |
| **G1** | **Yes** | Wrong-name rate 22%, upper bound 35% |
| **G1b** | **Yes, 11 cases** | Every wrong name is unqualified and cross-skill: 10 in count-occurrences, all naming `upper_uses_strict`; 1 in first-true naming `stops_one_early` |
| **G2** | **Yes** | Named coverage 15% |
| G3 | No | Style A 17% vs B+C 15% |
| G4 | No | Suite gap 0% |
| G5 | No | No wrong name rests only on `runtime_error`/`memory_limit` |

**Exploratory (not pre-registered).** For all 11 wrong names, the reliable evidence is identical to
the named model's fingerprint on every reliable test. The method applied its rule correctly; the
evidence could not tell the programs apart.

- **10 of the 11** name `upper_uses_strict` on count-occurrences. That model's fingerprint is
  "prints 0 on every test", so any program that prints 0 everywhere matches it. Examples are a loop
  that never runs, and the optimised-away stall.
- **The other one** (first-true `B_UOI_031`, reading `flags[mid + 1]`) had its 5 distinguishing
  tests excluded by the sanitizer as out-of-bounds reads. The remaining tests matched
  `stops_one_early`.
