# Proposal: VAL1-B, independently authored buggy solutions with blind labels (for owner approval)

**Status: proposed, not started.** Nobody is contacted, recruited or asked for code until
the owner approves this protocol, and, where §3 says so, until the institution's answer
is recorded. This document was written alongside VAL1-A (the lower-bound mutation audit,
`docs/evaluation/val1a-2026-10-21/`). Its thresholds are fixed here, before any data
exists.

## 1. Purpose and the claim it can support

**Question.** On incorrect C++ solutions written by people who have never seen
CodeAdapt's error models, the production method is `fingerprint_consistency` v1.1:

- How often does it name an error model (coverage)?
- When it names one, how often do independent human labellers agree on the error
  (precision)?
- How often do the labellers agree with each other on the error and on the skill?

**Claim allowed if the thresholds in §8 are met.** "On N independently written incorrect
solutions to four binary-search problems, the method diagnosed X with Y% agreement with
blind expert labels (95% CI …); it abstained on the rest."

**Claims not allowed under any result:**
- real-student or novice accuracy (the authors are volunteers writing deliberately buggy
  code, not students under course conditions);
- any learning effect;
- skill mastery;
- validated BKT parameters.

## 2. Materials

The four existing problems are frozen at their current content versions:

| Problem | Content version |
| --- | --- |
| lower-bound | `871602bc2bba` |
| count-occurrences | `d1b043c04574` |
| last-less-than | `3d52811ae14b` |
| first-true | `b69c5efa3b39` |

- **Method:** v1.1 is frozen.
- **What authors see:** each problem's public statement and its 2 sample tests, nothing
  else.
- **What authors never see:** error models, hidden tests, design records, the repository.

## 3. Participants, recruitment and consent

**Authors.** 3 people. They must:
- write C++ comfortably;
- not have read the CodeAdapt repository, its design records or its error models;
- not be the project owner or anyone who designed content.

Classmates, teaching assistants or junior developers are suitable.

**Labellers.** 2 people, separate from the authors where possible, with experience
teaching or reviewing introductory programming.
- The project owner may be a third labeller for adjudication only.
- The owner's labels are not used in the agreement statistics.

**Task for authors.** For each problem, write 5 solutions that compile but are wrong,
each containing a mistake the author believes a learner could plausibly make. That gives
4 problems × 5 solutions × 3 authors = **60 programs**.
- Authors may also submit up to 2 correct solutions per problem in different styles.
  These measure false alarms on correct code.
- Authors write a one-line private note per program describing the intended mistake.
  The note is withheld from labellers and used only as a secondary reference.

**Data recorded.** For each program:
- the source;
- a random author code (A1–A3);
- the problem;
- the private note.

No names, no student records and no grades are recorded. The code is the authors' own
work, donated under a licence stated on the consent form (CC BY 4.0 is suggested). That
allows it to go in the public repository under `eval/independent/`.

**Consent.** A one-page information sheet and consent form covering:
- the purpose;
- that the code may be published;
- the right to withdraw before publication;
- no payment, unless the owner decides otherwise.

**Institutional review (owner decision).**
- If the authors or labellers are students at the owner's institution, or the work is
  part of a course or degree project, the owner should ask the supervisor or ethics
  office whether this counts as human-subjects research.
- It collects no personal data beyond donated code, and it is not a study of the
  participants' learning. It may be exempt or minimal-risk, but **that is the
  institution's call, not ours**.
- The answer is recorded in this document before recruitment starts.

## 4. Label definitions

Labellers see each program's source and the problem statement. They do **not** see:
- any CodeAdapt output or test results;
- the author's note;
- the other labeller's labels.

They may run the program on inputs they choose. For each program, they record:

1. **Correctness:** `correct` or `incorrect`.
2. **Primary error.** Exactly one of:
   - one of the modelled errors of that problem, shown to labellers as **plain-language
     descriptions**, never as model keys or code (the descriptions come from each
     problem's design record §2);
   - `other-single`: one error, not in the list. The labeller writes a short description.
   - `multiple`: two or more independent errors.
   - `unclear`.
3. **Skill.** One of the four skill descriptions (`problem.toml` `[skills]` text), or
   `none of these`, with `uncertain` allowed.
4. **Confidence:** 1 to 3.

**Training.** Before labelling the study set, labellers label 8 calibration programs
taken from the existing held-out set, and discuss disagreements with the owner. Those 8
are excluded from all results.

## 5. Procedure

1. **Pre-registration.** This protocol, the frozen versions and the analysis script are
   committed before any program is collected.
2. **Collection.** Authors submit by a shared folder or email to the owner. Claude never
   receives contact details.
3. **Freeze before running.** All programs are committed (`eval/independent/<problem>/`,
   `data_class = synthetic-independent`) **before** CodeAdapt runs on them. Labels are
   committed **before** CodeAdapt output is shared with labellers.
4. **Evaluation.** `codeadapt-eval`, 2 runs per program, produces outcomes.
5. **Adjudication.** Where the two labellers disagree on the primary error, the owner
   adjudicates. Both the raw and the adjudicated labels are kept.

## 6. Metrics

Each metric is reported per problem and pooled, as counts with Wilson 95% intervals.

**Labeller agreement:** Cohen's κ, with raw agreement, between the two labellers on:
- correctness;
- primary error;
- skill.

**Coverage:** diagnosed / programs labelled `incorrect` by adjudication.

**Precision:** diagnoses whose model matches the adjudicated primary error / diagnoses.
Reported:
- with qualified and unqualified diagnoses separately;
- with false positives broken down by adjudicated label: `other-single`, `multiple`, or a
  different modelled error.

**Abstention by outcome**, plus the adjudicated label of each abstained program. This
shows how many modelled errors the method missed.

**Correct code:** `no_failure_observed` / correct programs.

**Suite gap:** programs labelled incorrect that pass every test.

**Skill attribution:** agreement between the diagnosed model's skill and the adjudicated
skill, for unqualified diagnoses. This is what would become an `incorrect` skill
observation.

**Comparison with VAL1-A:** coverage and precision on independent code against the
mutation audit.

## 7. Size and what it can resolve

60 incorrect programs is a small sample.

- If the method diagnoses about 25 of them, precision is estimated within roughly ±15
  points.
- 0 wrong diagnoses out of 25 gives a 95% upper bound of about 13%.
- κ on 60 items has a standard error of about 0.07–0.1.

This is enough to detect a method that is clearly unreliable. It is **not** enough to
certify a precise accuracy figure. If the results are borderline, the next step is more
data (VAL1-C or the RD1 real-data study), not a stronger claim.

## 8. Pre-registered stop thresholds

| ID | Condition | Consequence |
| --- | --- | --- |
| S1 | Labeller κ on primary error < 0.6 | The error categories are not reliably identifiable by humans. Accuracy against those labels is not interpretable, so report agreement only. Revise the category definitions before any further diagnostic claim. |
| S2 | Labeller κ on skill < 0.6 | The four-skill taxonomy is not reliably identifiable. Skill-level learner modelling (BKT) stays dormant, and skill evidence is redesigned around error patterns. |
| S3 | Precision < 80%, or its 95% upper bound < 90% with ≥ 3 wrong unqualified diagnoses | Diagnoses are not precise enough to show students as named errors. Tighten the support and qualification rules, or show test-level feedback only, before any student use. |
| S4 | Coverage < 20% | The model library covers few real-looking errors. Content expansion in the current form is not justified. Consider other designs, such as human-reviewed candidate generation or test-feedback-first. |
| S5 | Any correct program diagnosed with an error | A blocking defect. Investigate before anything else. |
| Pass | κ ≥ 0.6 on both, precision ≥ 80% with upper bound ≥ 90%, coverage ≥ 20%, no S5 | Supports the limited claim in §1. It still does **not** establish novice accuracy or learning. RD1 (real data) is the next step. Content expansion becomes an owner decision. |

## 9. Cost and timeline (estimate)

- **Authors:** about 2–3 hours each.
- **Labellers:** about 3–4 hours each, including training.
- **Owner:** recruitment, consent, adjudication of disagreements, and possibly an ethics
  query.
- **Claude:** pre-registration, the analysis script, evaluation and report (about 1–2
  days of work after the data arrives).

## 10. Decisions needed from the owner

1. Approve this protocol, or amend the thresholds, the sample size or the label scheme.
2. Find the authors and labellers, and decide on any compensation.
3. Ask the institution whether review is needed, and record the answer here.
4. Approve publishing the donated code in the public repository, or keep it in the
   private study repository (ADR-009).
