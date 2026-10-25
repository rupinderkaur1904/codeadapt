# Problem bank status (25 problems, 2026-10-25)

Each level is kept separate; a later level is never implied by an earlier one.

| Level | Meaning in this table |
| --- | --- |
| Implemented | Statement, contract, harness, reference, tests and error models committed under `content/demo/<slug>/` |
| Content-validated | `codeadapt-content validate` in the Docker sandbox reports `ok`: declared `distinguishes` equal the measured matrix, every pair of models is separable, every single-group model and every non-unique attribution carries a documented `known_limitation`; content report regenerated |
| Tested through the sandbox | `tests/sandbox/test_demo_content.py` passes for the problem (all problems in one test, runc and gVisor shards in CI) |
| Tested through fingerprint evaluation | Held-out cases committed before the method ran, evaluated under v1.1, v1.2 and v1.3 with `codeadapt-eval` |
| Integrated into the researcher workflow | Listed on `/problems`; a submission runs through API, worker, sandbox, diagnosis, ledger, recommendation and the researcher trace and learner-model views (for the new problems: `docs/demo/bank_check.py`, below) |
| Suitable for recommendations | `recommendable = true`; only the three original CE0 problems. Every other problem is excluded by the CE1 decision E2, applied to the expansion |
| Research-validated | Evaluated on independent or real-student programs. **No problem has this.** |

| # | Problem | Family | Implemented | Content-validated | Tested through the sandbox | Tested through fingerprint evaluation | Integrated into the researcher workflow | Suitable for recommendations | Research-validated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | lower-bound | binary-search | yes | yes | yes | yes (accepted held-out set) | yes | yes | no |
| 2 | count-occurrences | binary-search | yes | yes | yes | yes (accepted held-out set) | yes | yes | no |
| 3 | last-less-than | binary-search | yes | yes | yes | yes (accepted held-out set) | yes | yes | no |
| 4 | first-true | binary-search | yes | yes | yes | yes (accepted held-out set) | yes | no | no |
| 5 | integer-sqrt | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 6 | upper-bound | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 7 | exact-search | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 8 | last-occurrence | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 9 | min-capacity | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 10 | rotated-min | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 11 | rotated-search | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 12 | peak-index | binary-search | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 13 | first-max-index | arrays | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 14 | second-largest | arrays | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 15 | stock-profit | arrays | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 16 | longest-run | arrays | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 17 | plus-one | arrays | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 18 | closest-pair-sum | two-pointers | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 19 | container-water | two-pointers | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 20 | dedup-sorted | two-pointers | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 21 | max-window-sum | sliding-window | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 22 | longest-sum-at-most | sliding-window | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 23 | distinct-in-windows | sliding-window | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 24 | pivot-index | prefix-sums | yes | yes | yes | yes (author-written held-out) | yes | no | no |
| 25 | range-sum-queries | prefix-sums | yes | yes | yes | yes (author-written held-out) | yes | no | no |

## Notes

- **"yes" in the evaluation column means synthetic evidence only.** The cases were written by
  the person who wrote the error models; see [README.md](README.md) and
  [../summary.md](../summary.md). The four original problems (first-true accepted in CE1.1) use
  held-out sets the owner has accepted; the other eight binary-search problems are still
  provisional (owner, 2026-10-25 07:50).
- **Sandbox column.** Verified for all 25 by CI run 112 on `ed35cf7` (`demo-content` shards,
  runc and gVisor, both green).
- **Finer-grained columns** (end-to-end pipeline in CI versus locally, researcher UI versus API)
  are in [the 2026-10-25 audit](../../reviews/2026-10-25/expansion-audit.md#2-status-matrix).
- **Researcher workflow, new problems.** `python3 docs/demo/bank_check.py` against a dev API and
  worker on a fresh SQLite database (2026-10-25): for each of the 13 problems a correct, a
  modelled and an unmodelled held-out program; 39/39 matched their labels (pass, the labelled
  model named, abstention). The three non-unique models gave the qualified student message. In
  the new families every diagnosis recommended a retry of the same problem and every pass gave
  no recommendation (L21). The researcher learner model showed only the five ADR-033 skills,
  each "estimated under assumed parameters"; because each problem's first attempt was the
  correct program, every counted observation was `correct`, which shows the counting rule, not
  anyone's knowledge.
- **Not done.** No problem has independent programs; no skill key of the new families is
  validated (L22); no new problem is recommendable.
