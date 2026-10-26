# Bank expansion beyond binary search (2026-10-25)

**Owner instruction (2026-10-25 10:09).** Grow the bank from 12 to 25 problems by adding 13
that cover other array techniques:

- 5 array problems;
- 3 two-pointer problems;
- 3 sliding-window problems;
- 2 prefix-sum problems.

The work goes in batches of 3 or 4, through the full content lifecycle. The research safeguards
stay unchanged:

- the fingerprint rules and thresholds;
- the evidence rules, including rule C (L19 unresolved);
- the BKT parameters;
- recommendation policy 1.4;
- ADR-032 and L20.

Every new problem is `recommendable = false`.

## Skills for the new families (owner decision 2026-10-25 10:21)

> **Migration note (2026-10-26, ADR-034).** `index_range` and `update_rule` are retired. They
> are replaced by:
> - `loop_bounds` and `range_inclusion`;
> - `window_maintenance`, `pointer_movement` and `running_state`.
>
> The current definitions are in `backend/src/codeadapt/content/taxonomy.py`, and the
> model-by-model mapping is in ADR-034 and docs/proposals/l22-skill-taxonomy.md §2.1–2.2.
> Each problem has a new content version. This section and the per-problem design records
> describe the keys as they were when the problems were added. Observations recorded under
> the old keys keep them.

The four existing skills are defined in binary-search terms. Reusing them would pool new
evidence with binary-search evidence and change what those estimates mean. The new families
therefore use their **own** skill keys. The four existing skills, their mappings and their
evidence are untouched.

The owner chose "New skills for new families" on the decision card (2026-10-25 10:21). The
other options were to reuse the four existing skills, or to give no skill evidence.

| Key | Definition (as written in each `problem.toml`) |
| --- | --- |
| `index_range` | Visiting exactly the valid positions: the loop's start and end cover every element once. |
| `accumulator_init` | Initialising (and re-initialising) a running best, minimum, maximum, count or sum to the value the first real element requires. |
| `tie_resolution` | Handling equal values as the specification says: which of several equal candidates wins, and whether duplicates count separately. |
| `update_rule` | Updating every piece of tracked state on each step (running candidates, pointers, window edges) so no candidate is lost. |
| `output_contract` | Returning exactly what the specification asks for: an index or a value, a sentinel when there is no answer. |

**Two changes from the card's wording.**

1. **`tie_resolution` replaces `comparison_ties`.** The design checks showed that returning the
   last of several maxima happens both with `>=` and with a reverse scan using `>`, and the two
   are output-identical. A skill named after the comparison would claim to tell them apart. The
   skill is therefore named after the observable: which equal candidate wins.
2. **`update_rule` replaces `pointer_update`.** Some array problems have no pointers. One example
   is losing the old maximum in second-largest.

**Mapping is a modelling assumption.** As everywhere in the bank, mapping a model to a skill is
an assumption. These skills are linked across the new problems by key, and they are not linked
to the four binary-search skills.

## Process per problem

1. **Design.** Write the contract, a reference solution and the error models. Also write
   *alternative-cause programs*: plausible programs with a different cause, written to look for
   non-unique attributions (L20).
2. **Native design checks.** Run [`native_matrix.py`](native_matrix.py), which needs g++ on the
   host. It checks that:
   - the reference agrees with a Python oracle on every test and on 300–400 random small
     inputs;
   - no two models produce identical output on every test;
   - each model is compared with each alternative on the random inputs. A model that is
     identical to an alternative of a *different skill* on every random input is a non-unique
     attribution: it gets a `known_limitation` (ADR-032 route) or is dropped.
3. **Commit the content.** It passes `codeadapt-content validate` in the sandbox, which is
   authoritative: `distinguishes` equals the measured matrix, and every model has at least 2
   behaviour groups or a documented limitation. Commit it with its design record and content
   report.
4. **Commit the held-out cases separately**, before the method is run on them.
5. **Evaluate.** Run `codeadapt-eval` under v1.1, v1.2 and v1.3, and record the results in
   `docs/evaluation/expansion-2026-10-25/`.

**Reproducing a design check** (from the repository root):

```
python3 docs/content-design/expansion-2026-10-25/native_matrix.py \
    docs/content-design/expansion-2026-10-25/<slug> --content content/demo/<slug> --random 400
```

Each `<slug>/spec.py` holds the test list, the oracle and the random-input generator. Each
`<slug>/alternatives/` holds the alternative-cause programs.

## Recommendation behaviour in a family with no recommendable problem

Policy 1.4 chooses follow-ups only within the index problem's family, from recommendable
problems. Every problem in the new families is non-recommendable, so:

- **A supported or ambiguous diagnosis** falls back to *retry the same problem*, as the policy
  already does when no candidate exists.
- **A pass (`no_failure_observed`)** gives action `none`. Its note says "every problem in the
  family has an attempt with no failure observed". In these families that wording is inaccurate:
  the real reason is that the family has no recommendable problem. Changing the wording would be
  a policy change, so it is recorded as limitation L21 and the policy is left unchanged.

## Completion levels

These are kept separate in [the status table](../../evaluation/expansion-2026-10-25/STATUS.md).
"Research-validated" is **no** for every problem: there are no independent or real-student
programs.
