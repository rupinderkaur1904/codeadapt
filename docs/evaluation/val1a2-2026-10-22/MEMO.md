# VAL1-A2 decision memo (2026-10-22)

**Scope.** This memo covers the synthetic mutants only: 487 single-edit mutants of three problems,
scored against behavioural labels, plus the VAL1-A lower-bound replay. It is not real-student
evidence or independent validation, and it says nothing about learning. Full results are in
`README.md` and `results/tables.md`.

## Does the VAL1-A failure pattern generalise?

| Part of the pattern | Generalises? | Evidence |
| --- | --- | --- |
| Low coverage | **Yes** | Named coverage is 10–21% on each problem, 15% pooled, and 14% across all four problems. Most incorrect programs get `unmodelled_behaviour` (59%) or the time-limit symptom (26%). |
| Wrong names concentrated in one kind of uninformative evidence | **Yes, in a new form** | ADR-027 removed the time-limit source. Under v1.2 the wrong names (11/50, 22%, CI 13–35%) come from a different uninformative fingerprint: `upper_uses_strict` on count-occurrences prints 0 on every test, so any program that prints 0 everywhere is named as it (10 cases). One more wrong name arose because the sanitizer excluded exactly the tests that would have told the programs apart. All 11 are unqualified and cross-skill: each would have produced an `incorrect` observation on the wrong skill. |
| Crash or memory-limit signatures (ADR-027 Q3) | **No** | No named diagnosis rests on them (0/50). Crashing mutants almost always become sanitizer exclusions instead. |
| Dependence on the reference's style | **No** | Style A 17% vs styles B+C 15%. The recursive style does lose many programs to `unreliable`, through stack-overflow exclusions. |
| Suite gaps | **No** | No incorrect mutant passed a suite. |

## What the evidence supports

1. **The method is precise when a model's fingerprint is informative.** Last-less-than had 0/17 wrong
   names, and first-true 1/10. Every mutant that behaves exactly like a terminating error model was
   named as that model (39/39).
2. **The remaining precision problem is located, not diffuse.** It sits in the fingerprints the method
   matches against: one constant-output model, and evidence thinned by exclusions. It is not in the
   matching rule; in every wrong case, the evidence really was identical to the named model's.
3. **v1.2 is safer than v1.1 on these problems too, but only partly.** Wrong names fell from 19 to 11
   and coverage from 29% to 15%. ADR-027 alone does not bring precision to an acceptable level.
4. **Coverage is low enough that most incorrect programs get no specific diagnosis.** Any human-data
   study should expect few named diagnoses per program collected. This matches VAL1-B's reason for a
   60–100 program target.

## What remains unknown

- **Whether real programs look like these mutants.** Real errors may be multi-edit, partly correct,
  or wrong in ways no operator produces. Coverage and precision on real code could be higher or
  lower.
- **Whether behavioural labels reflect misconceptions.** A label says what a program does, not why
  the student wrote it.
- **Labels and pipeline use different builds** (`-O1` vs `-O2`). Only one mutant was affected here,
  but programs with undefined behaviour can depend on build flags.
- **Generalisation beyond one algorithm family.** All four problems are binary-search variants.
- **The right fix.** Two candidates follow from the mechanism, and both are production or content
  changes that need your approval; neither has been made:
  - **(a)** never name, or name only as qualified, a model whose fingerprint is constant, or whose
    fingerprint is matched only on the tests left after exclusions;
  - **(b)** give count-occurrences tests or models that separate "prints 0" from the off-by-one
    misconception.

## Recommendation at this gate

Nothing here authorises a production change, content change, CE1.2/CE1.3 or bank expansion, and
nothing has been changed.

1. **Treat G1 and G2 as confirmed across all four problems.** Keep diagnoses researcher-facing.
2. **Consider an ADR-028 proposal for candidate (a).** It would be a narrow, testable rule: no
   unqualified name from a constant fingerprint or from exclusion-thinned evidence. It would need its
   own approval, regression tests, and a replay on held-out, calibration, VAL1-A and VAL1-A2, as
   ADR-027 had.
3. **Use real programs next, not more synthetic ones.** You have chosen public datasets over
   collecting student code. That fits, because the main unknown is now how real programs compare
   with these mutants. A separate roadmap covers this.
