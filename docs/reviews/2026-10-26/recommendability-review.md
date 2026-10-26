# Which problems may be recommended: review of the 22 non-recommendable problems (2026-10-26)

**Status.** Review only, prepared for the owner's decision. No flag, rule, mapping or content
version has changed. The owner asked (2026-10-26 08:24–08:26) that recommendations draw on
every problem "according to the evidence", not only on the three recommendable ones. My
review below is a recommendation; it is not the owner's acceptance of any problem.

**Inputs.** content/demo/*/problem.toml, the design records in docs/content-design/, the bank
status matrix (bank-status/README.md), and two preview scripts in
[recommendability/](recommendability/). The scripts run policy 1.4 unchanged on the
one-attempt synthetic histories of the earlier regression checks (417 cases: every problem's
no-failure case, every named model and every ambiguous model pair), once with the current
flags and once with flags switched on in memory. **Synthetic histories only.** The previews show
which problem the rule would pick; they say nothing about whether a pick helps a student.

## 1. How a problem is chosen today

Policy 1.4 (`backend/src/codeadapt/adaptation/policy_v1.py`) chooses only among the
`recommendable` problems of the **same family** as the attempt:

| After | Rule | Ranking |
| --- | --- | --- |
| A named diagnosis | `_densest` | not recently attempted, then **most tests probing the target skill** |
| An ambiguous diagnosis | `_discriminating` | most candidate skills with an error model, then not recent, then most probing tests |
| No failure | least evidence | not yet passed, not recent, least ledger evidence for its skills |
| Abstention, non-termination, compile or run error | retry | the same problem |

Only lower-bound, count-occurrences and last-less-than are recommendable (CE1 decision E2:
new problems stay out until a separate policy decision). The other 9 binary-search problems
and all 13 problems of the other four families are not. Consequences:
- In binary search, every follow-up is one of three problems.
- In the other families nothing is recommendable, so a supported or ambiguous diagnosis
  falls back to a retry, and a pass gives "no further problem to recommend" (L21).

## 2. Main finding: switching flags on is not the same as choosing by evidence

Switching a problem on makes it a candidate; the ranking above then decides. Because the
ranking counts probing tests, and the newer problems have more tests (16–21 against 15–17),
**the newly enabled problems take almost every pick and the three original problems almost
none.** Binary-search follow-ups by case type (`recommendability/named.out`):

| Flags | After a named diagnosis (74) | After an ambiguous one (204) | After a pass (12) |
| --- | --- | --- | --- |
| Today | count-occurrences 32, lower-bound 22, last-less-than 20 | count-occurrences 86, lower-bound 70, last-less-than 48 | count-occurrences 11, last-less-than 1 |
| All 25 on | rotated-search 23, rotated-min 20, integer-sqrt 17, last-occurrence 10, others 4 | rotated-search 67, rotated-min 46, exact-search 34, integer-sqrt 25, others 32 | exact-search 8, rotated-search 4 |
| Option B below | first-true 38, exact-search 21, last-occurrence 10, upper-bound 5 | exact-search 89, first-true 54, last-occurrence 37, upper-bound 20, count-occurrences 4 | exact-search 8, count-occurrences 4 |

So with every flag on, a student whose lower-bound attempt is diagnosed `stops_at_first_match`
would be sent to last-occurrence instead of count-occurrences. A student with a supported
`loop_termination` diagnosis would usually go to integer-sqrt or rotated-min. The
two rotated problems are arguably the hardest in the family, and rotated-min has an open mapping flag.
The policy has no notion of difficulty.

I also previewed ranking by the *share* of tests that probe the skill instead of the count. It
changes almost nothing, because the rotated problems have high shares too. A rule that really
chooses "according to the evidence" (for example: prefer the problem where the target skill
has the least evidence for this learner, or where it is not positive-only) is a policy
revision, not a flag change. It needs its own design and owner decision.

**Positive-only targets.** Some follow-ups target a skill that the chosen problem can only ever
record as `correct` (declared or effective positive-only, bank-status §3). This already happens
today (for example, a `search_space_boundaries` follow-up on count-occurrences). Enabling more
problems does not create the issue but moves it (for example, `equality_handling` follow-ups to
last-occurrence, min-capacity, rotated-search or integer-sqrt, where that skill is positive-only).
The follow-up criterion is still evaluable there (probing tests must pass), but the learner
model can only gain positive evidence from it.

## 3. Per-problem review

Columns: the owner's earlier review status; the alternative-cause search done; the mapping flags
still open; the skills the problem's tests probe (and how many tests); which of those skills it
can never give negative evidence for; and my recommendation.

### Binary search (9)

| Problem | Review status | Alternative-cause search | Open flags | Probing tests per skill | Positive-only | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| first-true | Owner-accepted content and held-out (CE1.1); excluded only by E2 | Exhaustive + random (2026-10-26) | none (`returns_any_true` abstains: documented) | loop_termination 9, problem_specification 10, search_space_boundaries 13 | — | **Enable.** |
| upper-bound | Unreviewed (provisional) | Exhaustive + random (2026-10-25, rechecked) | none | equality_handling 10, loop_termination 8, problem_specification 9, search_space_boundaries 10 | equality_handling; loop_termination (effective) | **Enable**, the closest sibling of lower-bound. |
| last-occurrence | Unreviewed | Exhaustive + random | none | equality_handling 12, loop_termination 7, problem_specification 7, search_space_boundaries 8 | equality_handling, search_space_boundaries; loop_termination (effective) | **Enable**, aware that its main skill, equality_handling, is positive-only there. |
| exact-search | Unreviewed | Exhaustive + random | none | loop_termination 8, problem_specification 7, search_space_boundaries 14 | search_space_boundaries | **Enable.** |
| integer-sqrt | Unreviewed | Exhaustive + random | none | equality_handling 7, loop_termination 16, problem_specification 10, search_space_boundaries 4 | equality_handling | **Hold.** No large tests (overflow is part of its contract), and 16 of 19 tests probe loop_termination, so it would absorb loop_termination follow-ups. |
| min-capacity | Unreviewed | Exact equivalence argument (ADR-032) | two equality models non-unique (documented) | equality_handling 10, loop_termination 7, problem_specification 2, search_space_boundaries 9 | equality_handling; loop_termination (effective) | **Hold.** A transfer problem (search on the answer), and only 2 tests probe problem_specification. |
| peak-index | Unreviewed | Exhaustive + random | none | loop_termination 8, problem_specification 9, search_space_boundaries 16 | — | **Hold.** Not a sorted-array search; a different idea under the same skill keys. |
| rotated-search | Unreviewed | Exhaustive + random | none | equality_handling 8, loop_termination 12, problem_specification 20 | equality_handling | **Hold.** 20 of 21 tests probe problem_specification, so it would take most of those follow-ups; the hardest problem in the family. |
| rotated-min | Unreviewed | Skill-mapping review only, **no exhaustive search** | `compares_with_lo` attributed to its effect, not its cause | loop_termination 7, problem_specification 13, search_space_boundaries 18 | loop_termination (effective) | **Hold** until the search and the flag are resolved. |

### Other families (13)

All 13 were built on 2026-10-25 and are content-validated. None is owner-reviewed for research
use. Their skill keys are author-defined and untested for transfer (L22), and their
alternative-cause checks used 400 random inputs, not exhaustive search. Three carry a
documented `known_limitation` (container-water `moves_taller`, dedup-sorted
`returns_last_index`, stock-profit `ignores_order`). pivot-index has an open mapping judgement
(ADR-034), and plus-one has another (`adds_at_front` mapped to loop_bounds).

The policy chooses within a family, so enabling these affects only their own families. Today
those families give no follow-up at all (L21). Enabling them gives a next problem after a pass
and a skill-targeted follow-up after a diagnosis.

| Family | Problems | Recommendation |
| --- | --- | --- |
| arrays | first-max-index, longest-run, plus-one, second-largest, stock-profit | **Enable as a group**, with the L22 caveat stated, or keep all off. A partial set gives little. |
| two-pointers | closest-pair-sum, container-water, dedup-sorted | Same. |
| sliding-window | distinct-in-windows, longest-sum-at-most, max-window-sum | Same. |
| prefix-sums | pivot-index, range-sum-queries | Same; pivot-index's mapping judgement remains open. |

## 4. Options for the owner

| Option | What changes | Effect in binary search | Effect elsewhere |
| --- | --- | --- | --- |
| **A. All 22 on** (your literal request) | `recommendable` removed or true everywhere | Picks move to rotated-search, rotated-min and integer-sqrt (§2) | Follow-ups exist in every family |
| **B. Reviewed subset on** (my recommendation) | first-true, upper-bound, last-occurrence, exact-search, and the 13 other-family problems | Picks spread over the four siblings; the originals are rarely picked | Same as A |
| **C. B now, and a ranking revision later** | B, then a separately designed rule that prefers the skill with least learner evidence | As B until the revision | Same as A |
| **D. No change now** | none | Unchanged | Unchanged |

Whichever option is chosen, the change would be:
- the `recommendable` flags in problem.toml, which gives new content versions for the problems
  changed (earlier versions and their records stay);
- policy version 1.5 recording the changed candidate set (the rules themselves unchanged under
  A and B), with an ADR;
- the 442-history recommendation regression rerun before and after, with every changed choice
  listed;
- the golden policy fixture kept as recorded and its test updated to apply exactly the listed
  changes, as was done for ADR-037;
- the "Unreviewed" label: under B the four enabled siblings would no longer be unreviewed for
  recommendation, but their held-out sets would still be author-written. I would keep the
  label until you say otherwise.

## 5. Time and demo risk

- **Time:** about 2–3 hours for B: flags, version bump, ADR, regression rerun and comparison,
  test updates, and a full CI run (about 25 minutes). A is about the same. A ranking revision (C)
  is a separate design task of several hours, plus your review.
- **Demo risk:** the five-minute script changes under A or B. The `stops_at_first_match` case
  on lower-bound would recommend last-occurrence instead of count-occurrences, and step 4 of the
  script (count-occurrences as the follow-up) would need a new program and a new rehearsal. The
  qualified `uses_le` case would also go to last-occurrence. If the demo is very close, D (or
  making the change after the demo) is the safe choice.
- **Claims:** whichever option, the recommendations remain a rule-based baseline. Nothing here
  shows that a follow-up helps learning.
