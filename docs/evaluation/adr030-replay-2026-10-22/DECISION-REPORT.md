# ADR-030 replay and PC1.0: decision report (2026-10-22)

Nothing in production changed. ADR-030 exists only in `replay.py`. No dataset was downloaded.

## 1. Replay discrepancy: resolved (an evidence property, not a replay bug)

**What was reported.** "Programs whose candidate result differs between runs: 1
['val1a2/first-true/C_AOR_018']".

**Cause.** The two recorded executions of this mutant genuinely differ. The edit is
`mid = lo + (hi + lo) / 2` in the recursive style, which recurses until the stack overflows on
large inputs.

- **Run 1:** the sanitizer build reported `stack-overflow` on 5 tests. That leaves the time
  limits excluded, so the outcome is `unreliable_evidence`.
- **Run 2:** the sanitizer reported it on only 2 of those tests. The 3 large tests keep a
  reliable `time_limit`, so the outcome is `non_termination_observed`.

The difference is therefore already in the recorded v1.1 and v1.2 results, not only the
candidate's. On both runs the candidate equals v1.2. VAL1-A2 already classifies the program as
`unreliable` (not reproducible), so it is in no scored count.

**What was wrong in the report.** It checked reproducibility for the candidate only, and it
compared recorded results against the first run only.

**Corrections, both in `replay.py`:**

1. Every run of every program is now checked against its own record. The replay reproduced every
   recorded result exactly: 1,366 v1.1 runs and 1,066 v1.2 runs. VAL1-A recorded v1.1 only.
2. Run-to-run differences are reported for all three methods. Each lists the same single program.
   VAL1-A2's other non-reproducible program, last-less-than `C_UOI_036`, differs only in
   signatures, with the same outcome on both runs, so no method result changes.

The replay also confirms that the candidate is identical to v1.2 on every run of every program
it does not change.

## 2. Final case counts (scored incorrect programs)

| Set | v1.2 named / right / wrong | Candidate named / right / wrong | Changed by the candidate |
| --- | --- | --- | --- |
| Held-out (26) | 15 / 15 / 0 | 14 / 14 / 0 | 1 (8a; was right) |
| Calibration (5) | 2 / 1 / 1 | 2 / 1 / 1 | 0 |
| VAL1-A (98) | 10 / 10 / 0 | 10 / 10 / 0 | 0 |
| VAL1-A2 (323) | 50 / 39 / 11 | 30 / 30 / 0 | 20: 18 by 8a, 1 by 8a+8b, 1 by 8b; 9 were right, 11 wrong |

The totals reconcile: 50 − 20 = 30 named; 39 − 9 = 30 right; 11 − 11 = 0 wrong; 15 − 1 = 14 held-out.

## 3. The remaining licensing question

> **May this project download IBM Project CodeNet, a corpus of public submissions to AIZU Online
> Judge and AtCoder, and use it for non-commercial research analysis?**
>
> The proposed use: no source code is redistributed or committed; only anonymised submission ids
> and derived statistics are published.
>
> The problem: IBM publishes no dataset licence. The repository's Apache-2.0 LICENSE does not
> state that it covers the data. The paper only thanks AIZU and AtCoder for making submissions
> public. DeepMind's CodeContests describes CodeNet as Apache 2.0, but that is a third party's
> reading.

This needs a person who can approve data use for your project, such as your supervisor or your
institution's research-data or ethics office. The same question applies to RunBugRun, which is
built from CodeNet.

## 4. Minimum steps to measure candidate counts, once permitted

1. **Record the permission** verbatim (who, date, conditions) next to the VAL1-B institutional
   record.
2. **Allow the download host** in a project cloud environment:
   `codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud`. The current built-in environment
   blocks it.
3. **Download the archive** (about 7.8 GB) to scratch space outside the repository. Extract only
   `metadata/` and `problem_descriptions/`, not the code.
4. **Find the candidates** in `problem_list.csv` and the problem descriptions. CodeNet renumbers
   problem ids, so match on statement text for AIZU ALDS1_4_B and ALDS1_4_D. Report "not present"
   if they are absent; do not substitute.
5. **Count for each candidate** from its metadata CSV: C++ submissions by status, distinct users,
   and rejected submissions whose user later has an accepted one, using `user_id` and `date`.
6. **Update the feasibility report** with the measured counts and a final recommendation. Stop
   at the gate.

Steps 3 to 6 read metadata only, run no diagnosis and commit no third-party code. They take
under an hour once the host is allowed.
