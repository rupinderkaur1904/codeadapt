# Skill-mapping review: min-capacity and rotated-min (2026-10-25)

**Status.** This is review evidence for the owner. **No mapping, rule, policy or content file was changed.** The two mappings were flagged in the design records on 2026-10-24.

## What a mapping does

Each error model names one skill (`problem.toml`, `[[error_models]] skill`). The evidence ledger
(`backend/src/codeadapt/adaptation/ledger.py`; ADR-019 C5 and ADR-023 D2) acts on that skill as
follows:

- **Unqualified diagnosis.** If v1.3 names a model, the diagnosis is unqualified (two or more
  behaviour groups) and the model is not a documented collision (`known_limitation`), then the
  attempt gives **one `incorrect` observation on that model's skill**. That observation feeds
  the researcher-only BKT learner model.
- **Qualified diagnosis or abstention.** It gives no `incorrect` observation.

So a mapping matters only when its model is named unqualified. It is a modelling assumption,
and the design records already say so.

The question here is narrower. Does the observed behaviour single out the mapped skill? Or
could a program with a different underlying cause produce exactly the same behaviour?

## 1. min-capacity: `strict_day_limit` and `full_day_overflows`, mapped to `equality_handling`

**Rationale in the design record (§1).** Both errors choose `<` where `<=` is needed at an
exact boundary:

- a day loaded exactly to capacity;
- a schedule needing exactly `days` days.

The skill's text is "equal elements land on the correct side". The design record already says
this stretches the skill.

**Fingerprint strength.** Measured in the sandbox
([content report](../../content-reports/min-capacity.md)):

| Model | Failing tests | Behaviour groups | Qualified? |
| --- | --- | --- | --- |
| `strict_day_limit` | 14 | 6 | No |
| `full_day_overflows` | 12 | 5 | No |

So when v1.3 names either model, the attempt gives an `incorrect` observation on
`equality_handling`.

**Alternative causes.** Each alternative is a full program written to have a different cause.
All are in `skill-mapping-alternatives/`.

| Alternative program | Different cause | Plausible skill | Tests with a different output | Random inputs with a different output |
| --- | --- | --- | --- | --- |
| `overcount_days.cpp` | Day counter starts at 2: a counting error | problem_specification / initialisation | 0 of 19 | 0 of 400 |
| `days_as_breaks.cpp` | Reads "days" as the number of breaks, allowing only `days - 1` days | problem_specification | 0 of 19 | 0 of 400 |
| `cap_minus_one.cpp` | Treats the usable capacity as `cap - 1` | problem_specification | 0 of 19 | 0 of 400 |

The first two are compared with `strict_day_limit`, the third with `full_day_overflows`.

**These are exact equivalences.** Over integers, three pairs of conditions are identical:

- `needed < days` and `needed + 1 <= days`;
- `needed < days` and `needed <= days - 1`;
- `load + x >= cap` and `load + x > cap - 1`.

So **no test can ever separate these programs from the models**. Adding tests cannot fix it.

**Finding.** The evidence **does not support a unique attribution** to `equality_handling`.

- What the behaviour establishes is that the program treats the exact boundary as infeasible.
- Three different misunderstandings produce that same behaviour:
  - a comparison operator;
  - a day count;
  - a reading of the specification.
- Under the current policy, all three put an `incorrect` observation on `equality_handling`.

**Consequence today.** Nothing reaches students.

- min-capacity is `recommendable = false`.
- BKT is researcher-only.
- There is no real-learner data.

The mis-attribution would matter only when real attempts feed the learner model, or when
estimates are reported.

## 2. rotated-min: `compares_with_lo`, mapped to `search_space_boundaries`

**Rationale in the design record (§1).**

- **Effect.** The bound update discards the half that holds the minimum. That matches the skill
  text: "updating the bounds ... so every candidate answer stays reachable".
- **Cause.** The program compares with the wrong reference element, `a[lo]` instead of `a[hi]`.
  None of the four skills describes that cause.
- **Why not the other skills.** `equality_handling` cannot be observed here: the values are
  distinct, and `mid < hi`. `loop_termination` and `problem_specification` do not describe this
  error at all.

**Fingerprint strength.** The model fails 7 tests in 2 behaviour groups, so it is unqualified.
It fails exactly the inputs where the current range is already sorted:

- every unrotated test;
- `min_middle_even`, `negatives` and `large_half`, where `lo` lands on the minimum.

**Alternative causes.**

| Alternative program | Different cause | Tests with a different output | Random inputs with a different output | What v1.3 would do |
| --- | --- | --- | --- | --- |
| `drop_from_first.cpp` | Assumes the array is rotated: searches for the first element below `a[0]` | 3 of 18 (`min_middle_even`, `negatives`, `large_half`) | 74 of 400 | Abstain as unmodelled |

The last column is inferred from the content report's matrix, not run in the sandbox.
`compares_with_lo` contradicts this alternative on those 3 tests. `returns_pivot` contradicts
it on the rotated tests.

A rewrite of the same cause, `a[lo] <= a[mid]`, was output-identical, as expected. No
output-identical program with a *different* cause was found. Only one such alternative was
tried, so this is not proof that none exists.

**Finding.** The behaviour **does** separate this model from the one alternative cause that was
tried. That separation is safe: the alternative would be abstained on, not misnamed.

The residual uncertainty is about the taxonomy, not the fingerprint.

- `search_space_boundaries` describes what the program does to the range.
- It does not describe the misunderstanding: which element the rotation invariant should be
  checked against.
- So the observation is attributed to the effect, not the cause. Among the four skills, this is
  the least-bad fit.

## Options

The choices for min-capacity, from least to most change:

| Option | What changes | Consequence |
| --- | --- | --- |
| **(a) Keep and document** (current) | Nothing | Possible mis-attribution stays. Documented here and in `docs/limitations.md` (L20). |
| **(b) No failure evidence for provably non-unique attributions** | The two models are treated like documented collisions: a qualified hint, no `incorrect` observation | Needs a new field or reason. `known_limitation` currently means "single behaviour group", which `test_demo_content` enforces. Changes `problem.toml`, giving a new content version. Changes evidence attribution (policy) and the wording of a hint students see. **Owner decision.** |
| **(c) Remap to `problem_specification`** | The skill field | Moves the mis-attribution rather than removing it. Not recommended. |
| **(d) New skill** ("boundary condition of a feasibility check") | Taxonomy | Still does not separate the counting and specification readings. Not recommended on this evidence. |

For rotated-min, keeping the mapping with this documentation is recommended. Option (d) would
fit the cause better, but it is a taxonomy change, and one problem is too little evidence for
it.

**Recommendation.**

- **Now.** Keep both mappings unchanged and record the limitation as L20.
- **Before real-learner use.** Before any real-learner evidence from min-capacity reaches the
  learner model, decide on (b). I would choose (b): an attribution that no test can separate
  from other causes should not count against a specific skill.
- **Urgency.** This decision is not needed for the demonstrable prototype, because no real
  learner data exists and min-capacity is not recommendable.

**Not checked.**

- Whether similar exact equivalences exist in the other ten problems. Off-by-one models are the
  likely candidates. The critical review (2026-10-21) found the same kind of
  output-indistinguishable alternatives for the original four problems.
- Whether the alternatives are as common as the modelled errors in real code. That is unknown
  without real data.

**Reproduce** (from the repository root, needs g++):

```
python3 docs/reviews/2026-10-25/skill-mapping-alternatives/compare.py min-capacity strict_day_limit \
  docs/reviews/2026-10-25/skill-mapping-alternatives/overcount_days.cpp \
  docs/reviews/2026-10-25/skill-mapping-alternatives/days_as_breaks.cpp
python3 docs/reviews/2026-10-25/skill-mapping-alternatives/compare.py min-capacity full_day_overflows \
  docs/reviews/2026-10-25/skill-mapping-alternatives/cap_minus_one.cpp
python3 docs/reviews/2026-10-25/skill-mapping-alternatives/compare.py rotated-min compares_with_lo \
  docs/reviews/2026-10-25/skill-mapping-alternatives/drop_from_first.cpp
```

These are native runs, which approximate the sandbox. The alternative programs were written by
the same author as the models. They are review evidence, not held-out cases.

## Owner principle and the current gap (2026-10-25)

The owner's principle: where two distinct error causes are observationally indistinguishable on
the valid input domain, **the system must not claim to distinguish them**. Against that, the
current min-capacity behaviour is as follows.

- **Researcher trace: consistent.** Every named diagnosis carries the caveat "consistent with
  this error model; that is not proof of it, and explanations outside the modelled error space
  remain possible".
- **Student hints: mostly consistent.** Both hints ask about behaviour:
  - `strict_day_limit`: "Is a capacity that needs exactly the allowed number of days good
    enough?"
  - `full_day_overflows`: "Can a day be loaded exactly up to the capacity? Check the comparison
    in your feasibility check."

  The second sentence points at the comparison. The `cap - 1` alternative also lives in that
  comparison, so it is not contradicted.
- **Skill evidence: not consistent.** A named diagnosis records `incorrect` on
  `equality_handling`, and that attributes the error to one of several indistinguishable causes.
  Closing this gap is option (b) above, an evidence-policy change that needs the owner's
  decision.

Nothing was changed.
