# Proposal D1: skill evidence when the assessed technique is not verified

**Status.** Design proposal for owner review (owner action 5, 2026-10-25). **Nothing here is
implemented.** Rule C, the skill mappings, the BKT parameters, the content and the
recommendation policy are unchanged.

**Defect it addresses.** D1 in docs/reviews/2026-10-25/expansion-audit.md §5.2: a linear scan
or a banned library call passes every test of a binary-search problem, and rule C then gives
it `correct` observations for skills such as `search_space_boundaries` and
`loop_termination`.

**Correction to the audit's count.** The audit said six of the eight provisional statements
require O(log n) and three ban `std::upper_bound`. The exact counts are:

- **Complexity.** All 25 statements state a complexity bound:
  - O(log n): 11 problems;
  - O(log x): integer-sqrt;
  - O(n log W): min-capacity;
  - O(n) or O(n + q): the 12 problems of the new families.
- **Banned calls.** 14 statements ban named library calls:
  - all 12 binary-search problems;
  - dedup-sorted (`std::unique`);
  - first-max-index (`std::max_element`).

Within the eight provisional problems, six say O(log n), and `std::upper_bound` is named in
six.

## 1. What the functional tests establish, and what they cannot

**What a passing attempt shows.** For each committed test, the program's output matched the
reference within the run limits:

- **Limits:** 2 s CPU per test, 256 MiB of memory, and a capped output.
- **Sanitizer build** (ADR-016): no undefined behaviour was detected on those runs.
- **Repeat:** a failing test is run again to check it is stable.

That is all.

**What the tests cannot establish:**

1. **Correctness beyond the tests.** The audit's random-input checks are design-time
   evidence only. They are not run per attempt.
2. **Which algorithm was used, or its complexity.** One test calls the function once.
3. **Why a program fails.** The L20 search (docs/reviews/2026-10-25/l20-search.md) found
   that most named models in the six searched problems have an output-identical program with
   a different cause. Often that cause belongs to a different skill.
4. **Understanding.** A pass by a banned call and a pass by a careful binary search
   produce the same record.

Rule C reads only (1)-style facts, per skill: every probing test passed. So the `correct`
observation it gives means "no failure on the tests that probe this skill". It does not mean
"used the technique correctly". The learner model and its label already say "estimated under
assumed parameters". The skill name implies more than that.

## 2. Limits of the obvious fixes

### 2.1 Larger tests and tighter time limits

**The obstacle.** Each test runs a fresh process. The harness reads or builds the whole
array (the `L`, `A` and `D` input modes) before calling the function once. So every run
already costs Θ(n), and a linear scan adds only a constant factor to that. Measured in
the audit, a linear scan passes the n = 200 000 tests well within 2 s.

**No single-call test can separate O(n) from O(log n) by time.** The only timing design
that can is a multi-query harness: build the array once, then call the function q times. At
n = q = 200 000, a linear scan does about 4·10¹⁰ steps and binary search about 3.6·10⁶.

**Its costs:**

- **New content.** It changes the harness and the tests of every affected problem. That
  means new content versions, new fingerprints and new evaluations; the existing records
  stay with their versions.
- **Mislabelled outcome.** A slow but correct program would end at the CPU limit. Under
  v1.3, rule 4b reports that as `non_termination_observed`, which is wrong for a program
  that terminates slowly. A new outcome would be needed, and the sandbox cannot tell "slow"
  from "never stops" at the limit.
- **Timing noise.** CPU timing varies between hosts and between runc and gVisor, so the
  margin must be very large (×100 or more). Even then, a time-limit verdict is a reliability
  risk the project has so far avoided.
- **Not every problem.** integer-sqrt has one integer input; a linear root search does at
  most 46 341 steps per call, so only a multi-query design separates it too. min-capacity is
  O(n log W) against O(n·W): it needs a large W, which the tests already bound.

### 2.2 Static checks for banned calls

**What it would be.** A token scan of the source for the names each statement bans, after
stripping comments and string literals. It is cheap and deterministic.

**What it can do.** It can say a banned name **appears**. It cannot say a call **happens**:

- a macro, a function pointer or `using` can hide the name;
- a ban on `std::find` does not stop `std::ranges::find` unless that name is listed too.

**What it cannot do.** It says nothing about a hand-written linear scan, which is the more
likely way to avoid binary search. Detecting that would need an AST-level loop analysis.
That is a heuristic with false positives, such as a linear pre-check before a correct binary
search.

### 2.3 Summary of the limits

No available check verifies "used binary search". The only evidence the system can obtain
cheaply and reliably points the other way: "a banned name appears in the source".

## 3. Proposal (narrow)

**P-D1a. Withhold skill evidence from attempts with a detected banned name.** Recommended.

| Aspect | Proposal |
| --- | --- |
| **Scope** | Only the 14 problems whose statements ban named calls. Only names listed in that problem's statement, plus their `std::ranges::` forms. The list goes in `problem.toml` (`banned_names`), so the statement and the check cannot drift. |
| **Detection** | Token match after removing comments and string or character literals. It runs in the worker before execution. It is recorded in the trace as `technique_check = {banned_names_found: [...]}`. |
| **Execution and diagnosis** | Unchanged. The program still runs, and the student still sees test results and any diagnosis. |
| **Evidence** | The attempt gives **no skill observations**: no rule C `correct` and no `incorrect`. Its trace says why. |
| **Counting (LM1)** | **Decision for you.** Option 1, recommended: the attempt consumes the counted opportunity, like an abstaining attempt with reliable execution and delivered feedback (the rule you confirmed on 2026-10-17). This stops a banned-call pass from being followed by a counted re-attempt that was influenced by it. Option 2: it does not consume the opportunity. |
| **Student-facing** | **Decision for you,** because it changes what students see. One added sentence: "The statement asks you not to call X. Your tests still ran, but this attempt does not count as practice of the technique." Without it, the evidence change is silent. |
| **Versioning** | A new version of the evidence rules. Earlier attempts keep the observations they were given. The ledger is rebuilt from stored attempts, so a replay under the new rule must be selectable, not applied silently to old records (see §4). |

**P-D1b. Label rule C evidence on unverified-technique problems.** Optional; display only.

- In the researcher learner-model view, mark `correct` observations from problems whose
  technique is not verified: "technique not verified".
- No change to the estimate.
- This makes the gap visible without removing evidence.

**Not proposed.**

- Withholding rule C from **all** passes on binary-search problems. It would remove almost
  every positive observation for `search_space_boundaries` and `loop_termination`. The
  learner model would then see only negative evidence, a bias in the other direction.
- Multi-query performance tests. This is a separate content project with the costs in
  §2.1. It is worth doing only if complexity becomes an assessed outcome.

## 4. Effect

**On rule C.** Rule C is unchanged for every attempt without a detected banned name. With
P-D1a, an attempt with one gives nothing, so rule C is not reached. L19 option B (pending)
is independent of this.

**On existing observations.**

- **Records.** No stored record is rewritten. Submissions, traces and recommendations are
  append-only.
- **The ledger.** It is derived from stored attempts. The new rule would apply by evidence
  policy version:
  - attempts recorded under the current rules keep their attribution;
  - a researcher replay can show the current rules against the new ones, case by case.
- **Data affected.** Only dev and test databases hold attempts. There is no student data.

**On recommendations.**

- **Unchanged.** The recommendation policy reads the diagnosis outcome, not the ledger. A
  banned-call pass is still `no_failure_observed`. It leads to `new_problem` on the three
  recommendable problems, or to `none` elsewhere (L21 wording).
- **Option.** You could also have it lead to `retry` with the added sentence. That would be
  a policy change (1.5), with a golden-fixture regeneration and diff review.

**On research claims.** Even with P-D1a, a `correct` observation still means "no failure on
the probing tests", not "used the technique". The limitation stays in docs/limitations.md
(L23 below).

## 5. Acceptance criteria if approved

- Unit tests:
  - names inside comments and strings are ignored;
  - each banned name and its `std::ranges::` form is detected;
  - an attempt with a detected name gives no observation;
  - one without a detected name gives exactly the observations it gives today.
- A replay of every stored dev/test attempt and of the held-out cases under the current and
  the new rules: only attempts with detected names change.
- The policy golden fixture is unchanged, unless you choose the `retry` option.
- New content versions only where `banned_names` is added. That changes the 14 versions, so
  it needs your approval as a content change. Alternatively the list can live outside the
  content hash, in the policy. That keeps content versions, but the list can drift from the
  statement text.

## 6. Proposed limitation entry

**L23.** Complexity bounds and the technique a problem assesses are not verified. A `correct`
observation means no failure on the probing tests, not use of the intended technique.
