# PC1 public-corpus audit: frozen protocol

**Version 1.0, frozen 2026-10-23, before any real data was examined.** File hashes are in
`MANIFEST.sha256`. Any change after this point is an amendment (section 11). The owner
approved writing this protocol and its scripts. The owner has not approved running them on real
data. Neither phase below may start until the permission gate in section 3 is open.

Nothing in PC1 changes production diagnosis, the evidence ledger, BKT, the recommendation
policy, the problem bank or anything students see.

## 1. Purpose and research questions

Every CodeAdapt accuracy number to date comes from synthetic mutants or from cases written by
the error models' author. PC1 asks whether real rejected programs, written by people other than
the model author, give a different picture. The corpus is IBM Project CodeNet.

PC1 has two phases with separate questions.

**Phase F: feasibility and data quality** (metadata only, scripted here).

- **RQ-F1.** Does CodeNet contain AIZU ALDS1_4_B "Binary Search" (or the pre-registered fallback
  ALDS1_4_D "Allocation")? Can it be identified from its statement, without assuming it exists?
- **RQ-F2.** How many C++ users have an eligible rejected submission followed by their own
  accepted submission? Is the metadata clean enough to count them reliably?

**Phase E: diagnosis evaluation** (specified in section 8, not implemented, needs a separate
owner approval).

- **RQ-E1.** Of rejected programs that fail our frozen test suite, how many does method v1.3
  name (coverage)? How does this compare with v1.1 and v1.2?
- **RQ-E2.** When v1.3 names an error, how often does the name agree with a proxy label taken
  from the same user's accepted fix?
- **RQ-E3.** How often does a rejected program pass our suite (a suite gap)? How often is the
  evidence abstained on or unreliable, and for what reasons?

## 2. Phases and what each may read

| | Phase F (feasibility) | Phase E (diagnosis evaluation) |
| --- | --- | --- |
| Reads | `metadata/*.csv`, `problem_descriptions/*.html` | Additionally, the source files of the paired submissions only |
| Never reads | Any source code | Source code of unpaired submissions or other problems |
| Runs | Counting, pairing, reconciliation (`scripts/pc1.py`) | Compile and test in the sandbox, diagnosis methods v1.1, v1.2, v1.3 |
| Gate level | `metadata` | `code` (needs `source_code_analysis` in the permission scope) |
| Output | Counts and bands | Coverage, proxy agreement, abstention reasons |
| Status | Scripts written and tested on synthetic fixtures | Specified here only; not built |

Feasibility counts are not evidence about diagnosis quality. A large number of pairs says
nothing about whether CodeAdapt would name their errors correctly.

## 3. Permission gate

No download, extraction or processing of CodeNet happens until the owner records a permission
record that the gate accepts. `scripts/pc1.py gate` checks it. Every real-data command checks
it again before opening any data file, and exits with code 3 if it fails. Evidence and fields
are specified in `permission.md`. In short:

- The record must state an **explicit approval** from the owner's supervisor, institutional
  research-data office, institutional ethics office, or IBM as dataset owner.
- **The repository's Apache-2.0 LICENSE is not permission.** Its scope over the data is
  unstated. A third party's description, such as the CodeContests README calling CodeNet
  Apache 2.0, is not permission either. The gate rejects either as a `basis`.
- The scope must cover downloading the full archive. IBM offers no metadata-only download: the
  7.8 GB archive contains all source code. The scope must also cover storing it outside the
  repository and analysing metadata. Phase E also needs source-code analysis. Redistributing
  code must be false.
- Only the owner writes the record (`recorded_by: owner`). Claude never creates or edits it.
  It holds no names or email addresses. The written approval itself stays in the owner's
  records, referenced by `evidence_reference`.

## 4. Data handling

- Real data lives outside the repository. The scripts refuse a real-data directory or output
  directory inside it. Nothing from CodeNet is committed except counts and derived statistics,
  and only if `publish_derived_statistics` is true. Submission ids are committed only if
  `publish_submission_ids` is true. Source code is never committed or redistributed.
- Synthetic fixtures live in `fixtures/` and carry the marker file
  `SYNTHETIC-FIXTURE-NOT-REAL-DATA`. The scripts accept fixtures only with
  `--synthetic-fixtures`. They refuse a marked directory in real mode, and refuse a
  `--synthetic-fixtures` run outside `fixtures/`. Identification files record their source
  (`synthetic` or `real`). Feasibility refuses a mismatch.
- `extract` takes only `Project_CodeNet/metadata/` and `Project_CodeNet/problem_descriptions/`.
  It refuses links, absolute paths and `..`. It can read the archive as a stream
  (`curl … | pc1.py extract --archive -`), so the 7.8 GB file need not be stored. It reports the
  archive's SHA-256 and size.
- Every output is written atomically and with sorted keys. Re-running with the same inputs
  produces byte-identical files. Outputs record the SHA-256 of each metadata file they read.

## 5. Target problem and identification

**Order (pre-registered):**

1. ALDS1_4_B "Binary Search". Given n integers S in ascending order (n ≤ 100000) and q distinct
   integers T (q ≤ 50000), print the number of integers in T that are also in S.
2. ALDS1_4_D "Allocation". Only if ALDS1_4_B is absent, ambiguous or below the minimum band.
   Given n package weights in order and k trucks, each taking consecutive packages up to a
   common maximum load P, print the minimum P.

No other problem is substituted. If neither qualifies, PC1 stops and reports.

**Identification.** CodeNet anonymises problem ids (`p00000` style), so presence is not
assumed.

1. **Shortlist (automatic).** List every problem in `problem_list.csv` with `dataset = AIZU`
   that either has the frozen name (case-insensitive: "binary search", "allocation") or whose
   description contains at least 3 of the frozen phrases in `scripts/pc1.py` (`CANDIDATES`). The
   phrases are a recall aid, not a definition.
2. **Status.** A shortlist of 0 is `not_present`, 1 is `single_match`, and more is `ambiguous`.
   Nothing is chosen automatically.
3. **Confirmation (human).** The owner or supervisor reads each shortlisted description against
   the task statement above. They then record the chosen id with `pc1.py confirm`, which accepts
   only a shortlisted id. Confirmation happens before any per-problem submission file is read.
   If no shortlisted statement matches the task, the candidate is `not_present`.

## 6. Inclusion, exclusion and pairing (Phase F)

All rules apply to the confirmed problem's `metadata/<id>.csv` only. They are implemented in
`scripts/pc1.py` and tested on `fixtures/synthetic-basic`.

### 6.1 Rows

- **Schema.** The header must be exactly the 12 documented columns, in any order. Otherwise
  stop (S3).
- **Required fields:** `submission_id`, `problem_id`, `user_id`, `date`, `language`, `status`.
  A row is malformed if any of these holds:
  - a required field is empty;
  - an id does not match its pattern (`s` + 9 digits, `p` + 5 digits, `u` + 9 digits);
  - `problem_id` differs from the file's problem;
  - `date` is not a positive integer (Unix seconds);
  - the row has more cells than the header.

  Malformed rows are counted by reason and excluded.
- **Duplicates.**
  - Rows identical in every field: keep one, count the rest.
  - Rows sharing a `submission_id` with any differing field: exclude all of them and count
    them.

### 6.2 Language

Only rows with mapped `language` = `C++` are included. `original_language` is kept and
reported.

### 6.3 Status classes (exact CodeNet strings)

| Class | Statuses | Use |
| --- | --- | --- |
| accepted | Accepted | Candidate fix |
| eligible rejected | Wrong Answer, Time Limit Exceeded, Runtime Error, Memory Limit Exceeded, Output Limit Exceeded | Candidate rejected program |
| presentation error | WA: Presentation Error | Excluded: a formatting issue, not search logic |
| compile error | Compile Error | Excluded: no behaviour to diagnose |
| judge infrastructure | Judge Not Available, Waiting for Judging, Waiting for Re-judging, Internal Error, Judge System Error | Excluded: the verdict is not about the program |
| unknown | Anything else | Excluded and listed by exact string |

### 6.4 Same-user pairing

CodeNet records an anonymised `user_id` and a submission time in whole seconds (`date`). That
is what makes pairing possible. Pairing is done per user, within the problem and within C++.

1. Order the user's submissions by (`date`, `submission_id`).
2. The **fix** is the user's first accepted submission. Users with none are counted as
   `never_accepted` and give no pair.
3. Each eligible rejected submission falls into exactly one group:
   - `before_first_accept`: strictly earlier than the fix;
   - `same_second_as_first_accept`: excluded, because the order is unknowable;
   - `after_first_accept`: excluded, because the user had already solved it;
   - `never_accepted`.
4. The **primary pair** is the user's last `before_first_accept` rejection together with the
   fix. There is at most one per user, so users count equally and pairs are independent across
   users. The last rejection is the one closest to the fix, so the edit between them is the
   smallest available.
5. **Secondary pairs** are all `before_first_accept` rejections with the same fix. They are
   counted, never pooled with primary pairs.
6. Each pair records:
   - the gap in seconds (pairs over 30 days are flagged, not excluded);
   - the number of submissions in between;
   - whether `original_language` changed.

### 6.5 Count reconciliation (must hold exactly, else stop S6)

- rows read = malformed + valid
- valid = unique + exact duplicates dropped + conflicting duplicate rows
- unique = sum over languages
- C++ = sum over the six status classes
- eligible rejected = sum over the four timing groups
- secondary pairs = `before_first_accept`
- primary pairs = sum over the rejected status of the primary pair, and ≤ users with an accept

## 7. Phase F outcomes, bands and stop conditions

**Primary outcome:** the number of primary pairs for the confirmed problem.

| Band | Primary pairs | Meaning |
| --- | --- | --- |
| feasible | ≥ 100 | Enough to proceed to the PC1-E decision |
| feasible_below_target | 60–99 | Owner decides; same thresholds as VAL1-B (target 100, minimum 60) |
| not_feasible | < 60 | Count the fallback; if it is also below 60, stop |

The fallback is counted only when the first choice is `not_feasible`, absent or ambiguous.
These bands concern sample size only. Many pairs will drop out in Phase E: suite passes,
library-based solutions, unlabelable fixes.

**Stop conditions.** Each one stops the run, is written to the report, and is not worked
around.

| Code | Condition |
| --- | --- |
| S0 | Permission gate closed (exit 3; nothing read) |
| S1 | Real data or real outputs inside the repository, or fixtures used as real data (exit 3) |
| S3 | Unexpected column set in `problem_list.csv` or a submission file |
| S4 | Candidate not confirmed, confirmed id not on the shortlist, confirmer role wrong, or identification source mismatch |
| S5 | Malformed rows > 1%, conflicting duplicate rows > 1%, or unknown statuses > 1% of C++ rows |
| S6 | Any reconciliation identity fails |

**After Phase F:** the scripts recommend one of three outcomes:

- present the problem to the owner;
- stop;
- report that no candidate reached the minimum.

Then work stops at the gate. Phase F never starts Phase E.

## 8. Phase E: diagnosis evaluation (specified, not implemented)

Phase E starts only with all of the following:

- a permission record at level `code`;
- owner approval of the Phase F report;
- owner approval of the research-only problem adaptation described below.

### 8.1 Frozen before any submission code is read

- A research-only CodeAdapt problem for the confirmed AIZU task, with:
  - a specification;
  - an I/O adapter for the AIZU input format;
  - a test suite;
  - error models with measured fingerprints;
  - a reference solution.

  It is never recommendable and never shown to students.
- The method versions (v1.1, v1.2, v1.3 at a recorded commit) and the sandbox image tag.
- The edit-category rules and the table saying which categories each error model is consistent
  with (8.3).
- The library-use detector: a frozen regular expression for `binary_search`, `lower_bound`,
  `upper_bound`, `equal_range`, `set`/`unordered_set`/`map` lookups, and `count`/`find` on
  containers.

### 8.2 Units and exclusions

The unit is the primary pair. Pairs are excluded and counted in this order:

1. The fix fails our suite. That means our adaptation, not the user, is wrong, and it counts
   toward stop condition E-S1.
2. The rejected program does not compile with our toolchain.
3. The rejected program passes our suite. This is a **suite gap**, reported as RQ-E3, not
   evaluated further.
4. The rejected program uses a library search. This is out of scope for loop-level models: it
   is reported, and diagnosis outcomes are tabulated separately.
5. The evidence is unreliable or not reproducible across two runs.

### 8.3 Outcome definitions

- **Named:** outcome `hypothesis_supported`, qualified or not.
- **Abstained:** every other outcome, reported by type, with rule 4b, rule 7 and rules 8a/8b
  listed separately.
- **Proxy label:** taken from the token diff between the rejected program and the fix, after
  removing comments and normalising whitespace.
  - A single-hunk edit of at most 6 tokens is classified by the frozen rules into one category:
    - comparison operator;
    - bound initialisation;
    - midpoint computation;
    - bound update;
    - loop condition;
    - return or output expression;
    - I/O only;
    - other.
  - Larger, multi-hunk, I/O-only and "other" edits are **unlabelable**.
- **Agreement:** the edit category is consistent with the named model. **Disagreement:** the
  category is a search-logic category the named model is not consistent with.

### 8.4 Metrics

- **Primary:**
  - v1.3 coverage = named / evaluable failing programs;
  - v1.3 proxy agreement = agree / (agree + disagree), with a Wilson 95% interval.
- **Secondary:**
  - the same metrics for v1.1 and v1.2;
  - abstention reasons;
  - suite-gap rate;
  - library-use rate;
  - unlabelable rate;
  - results on secondary pairs, reported separately.
- **Minimum for rates:** with fewer than 20 labelable named programs, only counts are reported,
  no percentages or intervals.

### 8.5 Phase E stop conditions

| Code | Condition |
| --- | --- |
| E-S1 | More than 20% of fixes fail our suite. The adaptation is wrong; stop and report. |
| E-S2 | Any method, model, test or rule changes after submission code was read. This is a protocol violation: stop, report, and any rerun is a new protocol version. |
| E-S3 | More than 5% of programs are not reproducible across two runs. Report as unreliable; no rates. |

## 9. Limitations of submission outcomes as proxies

- **A verdict is not a misconception.** "Wrong Answer" says the output differed on AIZU's hidden
  tests. It does not say why. A rejected program can contain several errors, or none in the
  search logic: I/O, overflow, or a typo.
- **A fix shows what changed, not why.** Users may:
  - rewrite the whole program;
  - fix several things at once;
  - change approach (to a library call);
  - copy a solution.

  Small-edit labels cover only part of the pairs and favour near-mutant errors, the same bias
  noted for RunBugRun.
- **Selection.** Pairs exist only for users who eventually succeeded. Users who gave up are
  missing, and their errors may differ.
- **Not our students.** AIZU users are mostly self-learners and university students working
  through an algorithms course, largely in Japan. Results are about them, on one problem, not
  about CodeAdapt's target students.
- **Timing.** `date` has one-second resolution. Same-second order is unknowable, so ties are
  excluded. Long gaps may mean the user learned elsewhere in between.
- **Different judges.** AIZU's hidden tests and compilers differ from our suite and toolchain.
  A program rejected by AIZU may pass our suite, and an accepted one may fail it. Both are
  counted, not hidden.
- **Anonymisation.** User ids are anonymised by CodeNet. We do not know whether one person ever
  holds two ids, or how ids map across AIZU and AtCoder. Pairing stays within one problem.
- **One problem.** A result on ALDS1_4_B does not generalise to other problems or skills.

## 10. Claims

**Allowed after Phase F:**

- "CodeNet contains N C++ users on <problem> with a rejected submission followed by their own
  accepted one."
- Data-quality figures.

**Allowed after Phase E:** coverage and proxy agreement "on public AIZU C++ submissions for one
problem, labelled by the user's own later fix".

**Never allowed:**

- calling any PC1 number real-student accuracy, misconception detection, learning gain or
  mastery;
- presenting feasibility counts as diagnostic evidence;
- presenting synthetic-fixture results as anything but tests of the scripts.

## 11. Amendments and deviations

Any change to sections 3–8, to `scripts/pc1.py` or to the frozen constants after version 1.0
is an amendment. Each amendment:

- is numbered (A1, A2, …);
- is dated and justified;
- is approved by the owner before it applies;
- is recorded at the end of this file;
- updates `MANIFEST.sha256`.

A deviation discovered during a run, such as a CodeNet field that differs from its README, is
reported and not silently fixed.

## 12. Done under this protocol so far

- The scripts and synthetic fixtures were written and tested (31 unit tests, run in CI).
- No CodeNet file has been downloaded, extracted or read. No permission record exists.
