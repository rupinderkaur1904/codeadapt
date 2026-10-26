# Policy 1.4 vs 1.5 on synthetic histories (2026-10-26)

**Status.** Evaluation for ADR-038, prepared for the owner's review. **Synthetic histories only.**
These numbers show which problem each policy version picks for fixed, author-made attempt
histories. They do not show that any pick helps a learner, and a more varied set of picks is not
evidence of better recommendations.

## 1. What changed and what did not

| | Policy 1.4 | Policy 1.5 |
| --- | --- | --- |
| Eligible problems | the `recommendable` problems of the attempt's family | same flag (now 22 of 25 problems, held 5 unchanged) |
| Target skill after a named diagnosis | the model's skill | unchanged |
| Target skills after an ambiguous diagnosis | the candidates' skills | unchanged |
| Follow-up criterion | probing tests of the target skills must pass | unchanged |
| Ranking after a named diagnosis | not recent, then **most tests probing the skill** | §2 |
| Ranking after an ambiguous diagnosis | most candidate skills modelled, not recent, most probing tests | most candidate skills modelled, then §2 |
| No failure, abstention, non-termination, compile or run error | unchanged rules | unchanged |
| Diagnosis, evidence ledger, skill observations, BKT | not touched | not touched |

1.4 stays implemented: `PolicyV1(version="1.4")`, or `CODEADAPT_POLICY_VERSION=1.4` for the
worker. Every stored recommendation keeps the version that made it.

## 2. The 1.5 ranking

**Information used** (all already stored by the system): the problem specs (skills, tests and
their `probes`, error models, `positive_only_skills`, family, `recommendable`), the learner's
last 3 attempts, and the learner's skill observations from the evidence ledger (rule C,
unchanged). **Not used:** BKT estimates (researcher-only, assumed parameters), difficulty (the
system has no measure of it), and any count of tests as a preference.

**Algorithm.** For each eligible problem in the family:
1. Count the tests that probe the target skills. **Fewer than 2 → not a candidate** (the same
   minimum a diagnosis needs to name a model). This count is only a threshold.
2. Rank the candidates by, in order:
   1. after an ambiguous diagnosis only: the most candidate skills with an error model there (as
      in 1.4, so the follow-up can still tell the candidates apart);
   2. not among the last 3 attempts;
   3. the most target skills that can also receive **negative** evidence there (declared in the
      problem and not in its `positive_only_skills`);
   4. the **fewest observations this learner already has of the target skills from that
      problem** (the problem that would add the least-duplicated evidence);
   5. the largest **share** of the problem's tests that probe the target skills;
   6. the slug, so the result is fully deterministic.
3. No candidate → a retry of the same problem (as 1.4 when a family has nothing else).

The whole ranking, with every criterion value, is stored in the recommendation's rationale and
shown on the researcher trace page ("Recommendation rationale and ranking").

**Missing evidence.** A learner with no observations has 0 for every problem, so criterion 4 is
a tie and the next criteria decide. Fewer observations means *less evidence from that problem*.
It is never read as a weaker skill or lower mastery.

**Test-count bias.** 1.4 preferred the problem with the most probing tests, so the larger new
problems took almost every pick once enabled (review §2). In 1.5 the count is only the
threshold in step 1, and the tie-break is a share, not a count. Regression test:
`test_policy_1_5.py::test_test_count_alone_no_longer_decides`.

**Note on "least-evidenced".** The target skill is still the diagnosed one (changing it would
change the diagnostic rules, which this task excluded). "Least evidence" therefore chooses
*where* to look for new evidence of that skill, not *which* skill to target. After a pass, the
existing 1.4 no-failure rule already picks the problem whose skills have least ledger evidence;
it is unchanged.

### Examples (from `backend/`, the policy on the current catalogue)

**Example 1: lower-bound, named `stops_at_first_match` (equality_handling).**

| Candidate | Recent | Negative evidence possible | Prior obs. | Probing tests | Share |
| --- | --- | --- | --- | --- | --- |
| **count-occurrences** | no | 1 | 0 | 9 | 0.600 |
| last-occurrence | no | 0 | 0 | 12 | 0.632 |
| upper-bound | no | 0 | 0 | 10 | 0.526 |
| last-less-than | no | 0 | 0 | 7 | 0.467 |
| lower-bound | yes | 1 | 1 | 8 | 0.471 |

1.4 picks last-occurrence (most probing tests), where equality_handling is declared
positive-only. 1.5 picks count-occurrences, the only non-recent candidate where the follow-up
can record an incorrect equality_handling observation. This is also the demo path.

**Example 2: lower-bound, named `hi_init_last_index` (search_space_boundaries), no history.**
1.4 picks exact-search (14 probing tests; the skill is positive-only there). 1.5 picks
first-true. first-true and upper-bound both allow negative evidence and have no prior
observations, and first-true has the larger share (0.684 against 0.526).

**Example 3: the same diagnosis, after the learner passed first-true earlier.** The pass gave a
`correct` search_space_boundaries observation from first-true, so first-true now has 1 prior
observation. 1.5 picks **upper-bound** (0 prior); 1.4 still picks exact-search. This is the only
case of the three where the learner's own evidence decides.

**Example 4: a family where 1.5 changes nothing.** stock-profit, named `ignores_order`
(output_contract). All four arrays candidates allow negative evidence and have no prior
observations, so the share decides: longest-run under both versions.

## 3. Histories

| Set | What | Size |
| --- | --- | --- |
| H1 | one attempt on every problem: no failure, compile error, abstention, every named model, every ambiguous pair (the review's set) | 417 |
| H2 | the 286 histories of `tests/unit/policy_cases.py` (golden-fixture set: three original problems, single attempts and pairs) | 286 |
| H3 | 6 attempts each, starting from every unqualified named model of a recommendable binary-search problem and then always attempting the recommended problem. The simulated learner repeats the targeted error wherever that problem has an error model of the skill without a known limitation, and passes otherwise (a crude stand-in, not a model of learning) | 11 (old flags), 28 (new) |

Configurations: `1.4:e2` (policy 1.4 with the flags before this change: the baseline the owner
asked for), `1.4:current` (1.4 with the 22 eligible problems: what enabling alone does) and
`1.5:current`.

## 4. Results

| Measure | 1.4, old flags | 1.4, new flags | 1.5, new flags |
| --- | --- | --- | --- |
| H1 new-problem picks | 290 | 393 | 393 |
| H1 retries because nothing else is eligible | 114 | 24 | 24 |
| H1 "no further problem" | 13 | 0 | 0 |
| H1 distinct problems picked | 3 | 18 | 19 |
| H1 distinct skills targeted | 4 | 12 | 12 |
| H1 original three picked (of binary-search picks) | 290/290 | 8/290 | 79/290 |
| H1 largest single binary-search destination | count-occurrences 44% | exact-search 41% | **first-true 56%** |
| H1 follow-ups to a problem where a target skill is declared positive-only | 75/278 | 174/368 | **6/368** |
| H2 original three picked | 256/256 | 0/262 | 64/262 |
| H2 positive-only targeted follow-ups | 91/244 | 168/244 | 32/244 |
| H3 mean distinct problems visited | 3.00 | 4.46 | 5.71 |
| H3 trajectories reaching ≥3 observations from ≥2 problems | 11/11 | 27/28 | 28/28 |
| Picks a problem already in the history | 0 | 0 | 0 |
| Same result on a second call | yes | yes | yes |
| Time per recommendation | — | 0.11 ms | 0.61 ms |

Across H1 and H2 (703 cases), 319 recommendations differ between 1.4 and 1.5 on the new flags.
Every one is listed in `recommendations-*.json`; trajectories are in `trajectories-*.txt`.

**What this supports.** On these histories, 1.5 (a) removes the preference for larger problems,
(b) nearly removes follow-ups whose target skill can only be recorded as correct (174 → 6 in
H1), and (c) spreads a learner's evidence over more problems. (b) matters for the evidence
ledger: a follow-up that can only ever add `correct` observations cannot show that the error
persists.

**What it does not support.** Nothing here measures learning, difficulty or student
preference. That evidence is spread over more problems is a property of the rule, not proof the
recommendations are better.

## 5. Limitations

- **first-true concentration.** first-true declares no positive-only skills, so it wins
  criterion 3 for every binary-search skill it probes and takes 56% of binary-search picks (H1).
  This replaces one concentration (largest problems) with another (problems with complete
  negative evidence). I found no alternative within the existing data that avoids both without
  using difficulty, which the system does not record.
- **Declared vs effective positive-only.** Criterion 3 uses the declared
  `positive_only_skills`. Some skills are *effectively* positive-only (no error model on that
  problem fails their probing tests; bank-status §3), e.g. loop_termination on upper-bound and
  last-occurrence. 1.5 does not see those.
- **Prior observations are per problem.** Criterion 4 counts this learner's observations of the
  target skills from each candidate problem; it does not rank skills against each other.
- **Synthetic histories, author-written content.** The other families' skill keys are
  author-defined and untested for transfer (L22); the four enabled binary-search siblings keep
  their "Unreviewed" label.
- **No difficulty model.** Neither version knows that, for example, exact-search is easier than
  first-true.

## 6. Reproduce

From `backend/`:

```
PYTHONPATH=. uv run python ../docs/evaluation/policy-1.5-2026-10-26/compare_policies.py 1.4:e2 1.4:current 1.5:current
```

It rewrites `results.txt`, `timing.txt`, `recommendations-*.json` and `trajectories-*.txt` here.
