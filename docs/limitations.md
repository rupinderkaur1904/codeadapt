# Limitations and future work (as of 2026-10-24)

Each item says what is limited, the evidence for it, and what would address it. Numbers come
from [evaluation/summary.md](evaluation/summary.md).

## Evidence about the diagnostic method

| # | Limitation | Evidence | What would address it |
| --- | --- | --- | --- |
| L1 | No independent test data. Held-out programs were written by the error-model author; mutants were generated and labelled by the same AI system that works on the project. | critical review 2026-10-21; VAL1-A/A2 reports | Programs by other people: VAL1-B (pre-registered, deferred) or real rejected submissions (PC1, blocked) |
| L2 | Near-circularity. Every correctly diagnosed held-out case produced exactly its bug model's output on 500 random inputs (it was effectively that model), and the unmodelled cases were far from every model. | critical review §3 | Cases chosen by someone else; mutation audits (done) |
| L3 | Low coverage. Under v1.3, about 9% of incorrect mutants (30/323) and 14/26 held-out cases get a named error. | adr030-2026-10-23 | Better failing-case feedback (proposal); more discriminating tests per problem |
| L4 | "0 wrong" rests on small denominators (30 named mutants, 14 held-out). | same | Larger, independent samples |
| L5 | One algorithm family (binary search, 4 problems) with shared bug models, so evidence across problems is not independent. | content/demo | New families designed for diagnosis (CE1.2/1.3 paused) |
| L6 | Strict consistency: two bugs, or one bug plus noise, give `unmodelled_behaviour`. | methodology §4 | A noise-aware or compositional method, compared on stored evidence |
| L7 | Complexity is not assessed: a linear scan passes. | methodology §4 | An instrumented harness counting comparisons |
| L8 | count-occurrences can no longer name its only equality model (ADR-030 cost). | adr030-2026-10-23 | A test on which that model prints something other than 0 |

## Learner model and recommendations

| # | Limitation | Evidence | What would address it |
| --- | --- | --- | --- |
| L9 | BKT parameters are assumptions (`bkt-params-assumed-1`); estimates swing widely across plausible values (e.g. 0.52–0.99 after two corrects). | bkt-sensitivity-2026-10-17 | Fitting on real data; until then researcher-only |
| L10 | Skill maps (problem → skill) are unvalidated modelling choices. | ADR-021/023 | Expert review; real-data checks |
| L11 | The recommendation policy is a transparent rule set over a small bank, effectively a fixed sibling lookup; it ignores prerequisites and uncertainty. | critical review; policy 1.4 | More content; a policy evaluated on learner outcomes |
| L12 | No learning effect has been measured; no claim of improved learning is possible. | — | A study with real learners and a suitable design |
| L19 | Rule C gives a `correct` observation to any skill whose every probing test passed, whatever else the program did. A program that prints 0 on every count-occurrences test (abstained on, rule 8a) still earns `problem_specification` = correct from the absent-target tests. Evidence is per test property, not per program understanding. | pinned in `tests/sandbox/test_adaptation_end_to_end.py` (2026-10-24) | An owner decision on whether abstained or largely failing attempts should give positive evidence (an evidence-policy change, not made). Measured on 421 synthetic mutants under v1.3: incorrect programs gave 94 `correct` and 28 `incorrect` observations; options and a recommendation in docs/reviews/2026-10-25/l19-policy-options.md |
| L20 | Some skill attributions are not unique even when the diagnosis is unqualified. min-capacity `strict_day_limit` and `full_day_overflows` (mapped to `equality_handling`) are output-identical on every valid input to programs with a counting or specification error, so a named diagnosis may put an `incorrect` observation on the wrong skill. rotated-min `compares_with_lo` is attributed to its effect (`search_space_boundaries`), not its cause, which no skill describes. **Owner principle (2026-10-25):** where two distinct error causes are observationally indistinguishable on the valid input domain, the system must not claim to distinguish them. **Resolved for min-capacity by ADR-032 (owner option b, 2026-10-25):** both models carry a documented `known_limitation`, so diagnoses are kept but qualified and add no `equality_handling` evidence or BKT update. Attempts stored against the earlier min-capacity content version keep that version's snapshot (ADR-023 D4); none exist outside dev/test databases. rotated-min is not provably non-unique and is unchanged. **Bank expansion (2026-10-25):** each of the 13 new problems was checked against hand-written alternative-cause programs on 400 random inputs (not exhaustive). Three cross-skill equivalences were found and take the same route (`stock-profit/ignores_order`, `container-water/moves_taller`, `dedup-sorted/returns_last_index`); same-skill equivalences are listed in each design record. The other binary-search problems were not searched. | docs/reviews/2026-10-25/skill-mapping-review.md; docs/content-design/expansion-2026-10-25/ | ADR-032 (min-capacity done); a systematic search for exact equivalences in the remaining binary-search problems |
| L21 | In a family with no recommendable problem (every non-binary-search family since the 2026-10-25 expansion), a pass gives recommendation action `none` with the note "every problem in the family has an attempt with no failure observed". There the real reason is that no problem in the family is recommendable, so the note is inaccurate. Supported and ambiguous diagnoses fall back to a retry of the same problem. | ADR-033; policy 1.4 | A policy revision (needs an owner decision), or recommendable problems in those families once the research criteria allow it |
| L22 | The five skill keys of the new families (ADR-033: `index_range`, `accumulator_init`, `tie_resolution`, `update_rule`, `output_contract`) are broad and defined by the author. Evidence pools across problems and families by key, so an `index_range` mistake in a sliding-window problem and one in an array problem count as the same skill; whether students' errors actually transfer that way is untested. Each new problem has 7–8 held-out cases written by the models' author; one (second-largest `after_max_only.cpp`) exposed a wrong design claim and was fixed after it was seen, so it is no longer an independent check. | ADR-033; docs/evaluation/expansion-2026-10-25/ | Independent programs for these families; a skill-map validation before any of them becomes recommendable |

## Platform

| # | Limitation | Evidence | What would address it |
| --- | --- | --- | --- |
| L13 | Not deployed; the production tier (gVisor on a separate runner VM) is set up and tested in CI only for one shard, and there is no host. | docs/deployment.md; roadmap M8 | Owner's hosting choice; full suite under runsc on the host |
| L14 | Lost-output cause unknown; the end-of-output marker turns it into an infrastructure error. | ADR-024; 0 in about 37,700 probe runs | Root cause if it recurs |
| L15 | The lease heartbeat (2026-10-24) keeps a live worker's claim, but a worker whose event loop stalls for a whole lease (600 s) can lose it mid-run; the job can then run on two workers (both diagnoses kept). | ADR-031 | A fencing token checked in the diagnosis insert |
| L16 | The sandbox tests are slow (about 20–30 min locally), so they are sharded in CI. | CI config | Batch execution (changes per-test isolation, so it needs a decision) |

## Data and permissions

| # | Limitation | Evidence | What would address it |
| --- | --- | --- | --- |
| L17 | CodeNet: the licence is reported (CDLA-Permissive-2.0) but not shipped in the archive; IBM gives no warranty about upstream rights; ids are pseudonymous. The PC1 gate is closed. | pc1/STATUS.md; CORRECTIONS.md | Owner decision on amendment A1, first-hand evidence, optional maintainer reply |
| L18 | Public-corpus authors are not CodeAdapt's target students; a rejected→accepted pair is not a misconception label. | PC1 protocol §9 | State this in any claim |

## Future work, in order of value for the research question

1. Independent programs (PC1 if unblocked, otherwise VAL1-B), evaluated with the pre-registered
   protocols.
2. Failing-case feedback as the main experience (proposal), since that is what most students see.
3. Evidence that the new families' skill keys (ADR-033, added 2026-10-25 with 13 non-recommendable
   problems) describe errors that recur across problems.
4. Only after real data: fitting BKT parameters, and validating skill maps.
