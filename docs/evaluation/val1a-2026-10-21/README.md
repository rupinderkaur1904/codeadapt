# VAL1-A results: lower-bound mutation audit (2026-10-21)

**What this is.** Single-edit mutants of three correct lower-bound implementations were
run through the production evidence and diagnosis path. The plan was pre-registered in
[PLAN.md](PLAN.md):

| Commit | Contents | Committed before |
| --- | --- | --- |
| `1948791` | plan and originals | anything was generated |
| `b1aff23` | mutants and labels | anything ran |

**What this is not.**
- The mutants are synthetic and mechanically generated.
- Their concept labels are the plan author's (an AI system's) judgement, not human labels.
- This is **not** independent validation, real-student evidence or evidence about
  learning.

**Frozen.** Method `fingerprint_consistency` v1.1, lower-bound content `871602bc2bba`, g++
14.2.0 under runc, 2 runs per program. No production code, content, skill map, BKT or
policy was changed.

Raw data, regenerable with the scripts in this folder:

| File | Contents |
| --- | --- |
| `results/pipeline.jsonl` | every run's outcome, signatures and exclusions |
| `results/equivalence.json` | native behaviour against the reference on 3040 inputs |
| `results/cases.json` | the per-mutant classification |
| `results/summary.json` | the summary figures |
| `results/tables.md` | every table, including each diagnosis, abstention and exclusion |

## 1. Headline

1. **Pre-registered threshold T1 is triggered.**
   - 17 of 32 diagnoses (53%, 95% CI 36–69%) name a different error from the edit that
     was made, under the strict labels.
   - All 17 are *unqualified*, with 6 or 9 behaviour groups. All would have produced an
     `incorrect` skill observation.
   - Under the lenient labels the count is 11/32 (34%, 95% CI 20–52%). That is still
     above the T1 threshold.
2. **Every wrong diagnosis is a termination diagnosis.**
   - All 17 involve `no_progress_update` (7) or `closed_loop_hi_mid` (10).
   - Each of the 17 mutants hits the time limit on the 10 or 13 tests where a modelled
     loop does, and matches the model elsewhere.
   - Of 22 termination diagnoses, 5 named the edit (23%, CI 10–43%).
   - Of 10 non-termination diagnoses, 10 named the edit (CI 72–100%).
   - **A time limit pattern identifies "this does not terminate on these inputs". It
     does not identify which edit causes it.** The behaviour-group count did not protect
     against this: the wrong diagnoses rested on 6–9 groups.
3. **Coverage looks moderate, but correct-model coverage is low.**
   - Coverage was 32/98 incorrect mutants (33%, CI 24–42%), so T2 is not triggered.
   - Counting only diagnoses that name the edit, coverage is 15/98 (15%, CI 10–24%). This
     is a derived figure, not pre-registered.
4. **Style dependence (derived figures).**
   - Correct-model coverage is 9/34 in the reference style (26%) against 6/64 in the
     other two styles (9%).
   - The pre-registered T3 compares *any-diagnosis* coverage: 41% against 28%. That ratio
     is 0.68, so T3 is not triggered.
   - In style B (closed interval), 12 of its 14 diagnoses were wrong-model.
5. **No suite gap.** No incorrect mutant passed all 17 tests: 0/98, CI 0–4%. T4 is not
   triggered.
6. **Abstention works where nothing is close.** 66 incorrect mutants abstained as
   unmodelled. None was ambiguous or insufficient.

## 2. Counts by category

| Category | A: half-open (reference style) | B: closed + answer | C: recursive | All |
| --- | ---: | ---: | ---: | ---: |
| compile_error | 0 | 0 | 0 | 0 |
| unreliable (sanitizer finding or not reproducible) | 6 | 9 | 20 | 35 |
| equivalent (passes suite and matches the reference on 3040 inputs) | 4 | 6 | 4 | 14 |
| suite_gap (passes suite, differs on random inputs) | 0 | 0 | 0 | 0 |
| incorrect_failing | 34 | 42 | 22 | 98 |
| **mutants** | 44 | 57 | 46 | 147 |

Other checks:
- All three originals gave `no_failure_observed` and matched the reference on every
  random input.
- The native and pipeline classifications agreed for every mutant.
- One mutant, `C_UOI_036` (out-of-bounds read), was not reproducible across the 2 runs.
  It is counted as unreliable.

**Unreliable mutants.** 23 had heap-buffer-overflow or null-pointer findings, from
out-of-bounds reads. 12 had stack overflow, from infinite recursion in style C.
- **Every termination edit in the recursive style is unreliable, never diagnosed.** This
  includes the 5 recursive mutants labelled `no_progress_update` or
  `closed_loop_hi_mid`.
- That is safe, because unreliable evidence is never diagnosed. It means termination
  errors in recursive code are invisible to the diagnostic engine.

## 3. Pre-registered metrics (all styles; per-style values in `results/tables.md`)

Denominator: the 98 `incorrect_failing` mutants, unless stated.

| Metric | Value |
| --- | --- |
| Coverage (any diagnosis) | 32/98 (33%, CI 24–42%) |
| — unqualified | 30/98 (31%, CI 22–40%) |
| — qualified | 2/98 (2%, CI 1–7%): both `hi_init_last_index`, both correct |
| Abstained: unmodelled | 66/98 (67%, CI 58–76%) |
| Abstained: ambiguous / insufficient | 0 / 0 |
| Concept agreement (strict) | 15/32 diagnoses (47%, CI 31–64%) |
| Cross-pattern diagnoses (strict) | 17/32 (53%, CI 36–69%), all unqualified |
| Cross-pattern diagnoses (lenient) | 11/32 (34%, CI 20–52%) |
| Cross-skill unqualified diagnoses (T1b; the plan counts label `none` as cross-skill) | 17 |
| Library recall on labelled mutants | strict 15/15 labelled `incorrect_failing` (CI 80–100%); 5 more labelled mutants were unreliable (style C). Lenient 21/23: `B_UOI_010` and `B_UOI_040` abstained. |
| Suite gap | 0/98 (CI 0–4%) |
| Mutants with a library label | 20/147 (14%, CI 9–20%): A 9/44, B 2/57, C 9/46 |

| Style | Coverage (any) | Correct-model coverage (derived) | Diagnoses naming the edit |
| --- | --- | --- | --- |
| A (reference style) | 14/34 (41%, CI 26–58%) | 9/34 (26%, CI 15–43%) | 9/14 |
| B (closed + answer) | 14/42 (33%, CI 21–48%) | 2/42 (5%, CI 1–16%) | 2/14 |
| C (recursive) | 4/22 (18%, CI 7–39%) | 4/22 (18%, CI 7–39%) | 4/4 |
| B + C | 18/64 (28%, CI 19–40%) | 6/64 (9%, CI 4–19%) | 6/18 |

## 4. The 17 wrong-model diagnoses

All are termination diagnoses of edits that also fail to terminate.

| Diagnosed as | Edits that produced it |
| --- | --- |
| `no_progress_update` ("`lo = mid` instead of `mid + 1`") | `lo = mid - 1` (A, B); deleting `lo = mid + 1` (A, B); and in the closed style B, `lo = mid`, `lo = mid + 0` and `lo = (mid - 1) + 1`. The last 3 are the lenient label's "same error, other interval", but still not the half-open code the model describes. |
| `closed_loop_hi_mid` ("closed loop with `hi = mid`") | `while ((lo - 1) < hi)` (A); `hi = mid + 1` (A); deleting `hi = mid` (A); in style B, `while ((lo - 1) <= hi)`, `while (lo <= hi + 1)`, `hi = mid + 1`, deleting `hi = mid - 1`, and three spellings of `hi = mid` |

**Reading (judgement, not pre-registered).**
- Every one of these edits does break termination, so at the level of the *skill*
  (`loop_termination`) the attribution is defensible for all 17.
- At the level of the *named error*, which is what the student hint and the
  recommendation rationale describe, it is wrong for all 17 under the strict labels.
- The hint for `closed_loop_hi_mid` would tell a student whose loop never moves `hi` that
  they wrote a closed loop with `hi = mid`.
- Under the plan's definition (label `none` counts as cross-skill), T1b counts 17. Under
  a skill-level reading made after the results, it would count 0. **The pre-registered
  reading is the one reported.** The skill-level reading is offered for the owner's
  judgement.

## 5. Collisions

**Distinct signature vectors.** The 98 incorrect mutants produce 43 distinct full
signature vectors. 26 vectors are shared by 2 or more mutants; together they cover 81
mutants.

**Same edit across styles.** The same semantic edit in different styles often collides.
That is expected and harmless, for example `<=` in A and C against `>` in B.

**Different edits on one vector.** The harmful collisions are different edits on one
vector:
- 10 left-update edits across A and B share one vector, the `no_progress_update`
  fingerprint.
- 7 right-update and loop edits across A and B share another, the `closed_loop_hi_mid`
  fingerprint.

**By model (diagnosed mutants).**

| Model | Mutants diagnosed | Of which wrong-model |
| --- | ---: | ---: |
| `closed_loop_hi_mid` | 12 | 10 |
| `no_progress_update` | 10 | 7 |
| `returns_wrong_pointer` | 3 | 0 |
| `upper_bound_confusion` | 3 | 0 |
| `hi_skips_candidate` | 2 | 0 |
| `hi_init_last_index` | 2 | 0 |
| `exact_match_sentinel` | 0 | — |
| `stops_at_first_match` | 0 | — |

The last two cannot be reached by a single edit of these originals.

**Near misses that abstained.** Some abstentions came very close to a model:
- `B_UOI_010` (`ans` starts at `n - 1`) mismatches `hi_init_last_index` on 1 test.
- `B_UOI_031` mismatches `hi_skips_candidate` on 2 tests.
- `A_UOI_015` mismatches `closed_loop_hi_mid` on 1 test.

One more input distribution or test change could turn these into diagnoses, right or
wrong.

## 6. Is the generator biased toward the library?

Yes, in both directions, and the result should be read with that in mind:

1. **Style A is the reference the models were derived from.** 20% of its mutants carry a
   library label, against 4% in style B.
2. **The operators are single-token edits.** The library is mostly single edits too, so
   this audit over-represents library-shaped errors relative to real code. Multi-edit and
   conceptual errors, like `exact_match_sentinel` and `stops_at_first_match`, cannot
   appear at all.
3. **On the other side,** generic operators produce many edits no learner would write,
   such as `/ 3` midpoints or `!=` comparisons. These inflate the "unmodelled" share.

So coverage here is neither an upper nor a lower bound on human-written code. The
precision finding (§1, §4) does not depend on this bias: it comes from edits that *are*
plausible, such as a missing or wrong-direction `hi` or `lo` update.

## 7. What this does and does not show

**Shows, on synthetic single edits of one problem:**
- Non-termination diagnoses are not specific to the error. Under v1.1 they are reported
  as unqualified, multi-group diagnoses, and would become skill evidence.
- The behaviour-group rule does not guard against collisions with unmodelled errors that
  share a non-specific signature.
- Non-termination diagnoses (equality, specification, boundary) named the edit in 10 of
  10 cases, but that is a small number.
- Recursive termination errors are always unreliable, so never diagnosed.
- The suite caught every incorrect mutant.

**Does not show:**
- accuracy on human-written code (VAL1-B);
- anything about learners;
- results for the other three problems, although they share the same termination models
  and time-limit signatures, so the same issue is likely (this is an inference, not a
  measurement).

## 8. Recommended next decision (for the owner)

The finding is specific enough to act on without redesigning everything. **Decide how
non-termination evidence is reported and used** before VAL1-B. My recommendation:

1. **Treat time-limit-based diagnoses as qualified, at the "loop does not terminate"
   level.** The student wording would describe non-termination on the named inputs,
   rather than a specific edit. Such diagnoses add no `incorrect` skill observation
   until a test can show the specific edit.
   - This is a change to diagnosis and ledger policy (a v1.2 / ledger 1.3 ADR).
   - It needs the owner's approval, and a re-run of the held-out, calibration and VAL1-A
     sets to report the effect case by case.
   - **Alternative:** keep v1.1 and accept that termination hints name a possibly wrong
     edit. I do not recommend this.
2. **Then approve the VAL1-B protocol** (`docs/proposals/val1b-independent-corpus-protocol.md`),
   so that independent human-written code tests the non-termination diagnoses under
   whichever rule is in force.

CE1.2 and CE1.3 stay paused. Nothing here argues for resuming them. integer-sqrt's stated
aim was richer *termination* evidence, which this audit shows is the weakest part of the
method.
