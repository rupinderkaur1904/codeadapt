# Proposal: failing-case feedback as the main student experience

**Status: proposal for later owner review. Not implemented. Nothing students see changes.**
Written 2026-10-23 at the owner's request, separately from PC1. No ADR number has been
assigned.

## 1. Why

After ADR-027 and ADR-030, a named error (with a hint) is now the exception. Under method v1.3
it is given for:

- 30 of 323 incorrect VAL1-A2 mutants (9%);
- 10 of 98 VAL1-A mutants;
- 14 of 26 held-out cases.

These are all synthetic or author-written, not real-student rates. Most incorrect submissions
therefore get the failing-cases view. Today that view says "Your code fails some cases. Compare
what these cases have in common." It lists the failing hidden tests only by their one-line
description, and shows input, expected and actual output for sample tests only
(`backend/src/codeadapt/api/feedback.py`).

The product's most common message is therefore its least developed one. This proposal makes
the failing cases the main experience and treats a named hint as an occasional addition. That
is consistent with the owner's goal that no feedback be stronger than its evidence.

## 2. Options

| Option | What the student sees on a failed attempt | Cost | Risk |
| --- | --- | --- | --- |
| **A. Reorder and reword** | Failing cases first, grouped by their `student_description` category (empty input, target below all values, duplicates at a boundary, and so on). A named hint, when there is one, follows as "one possible cause". | Small: view and wording only | Low; still little information for hidden cases |
| **B. A + one revealed counterexample (recommended)** | As A. After the second failed attempt on the same problem version, the smallest failing hidden case is shown with its input, the expected output and the student's own output. | Medium: reveal rule, event record, UI | Students may special-case the revealed input. Mitigated in section 3. |
| **C. B + predict first** | As B, but the student first predicts their program's output on the revealed case before seeing it | Larger: new interaction and storage | Slower; unvalidated benefit |

## 3. What B would need (for a later ADR, not now)

- **Reveal rule.** A deterministic choice of which case is revealed: the smallest input, ties
  broken by test order. At most one reveal per attempt, and only after the second failed
  attempt. Each reveal is recorded as an event.
- **Evidence after a reveal.** A revealed test can be passed by special-casing. Later attempts
  would treat a revealed test's pass as weaker evidence: excluded from the ledger's success
  observations and flagged in the researcher view. That is a methodology change and needs its
  own ADR and regression tests.
- **No change** to:
  - diagnosis methods;
  - error models;
  - BKT parameters or the learner model;
  - recommendation policy 1.4;
  - which problems are recommendable.
- **Content.** Each problem's hidden tests need a short, student-safe category label. Most
  already have a `student_description`.

## 4. What would decide it

- The owner's view on the trade-off between revealing hidden inputs and the risk of
  special-casing.
- PC1 Phase E, if run, would show how often real rejected programs fail only one or two cases.
  That bears on whether one revealed case is enough.
- Any real-student use needs the existing ethics conditions first. No learning-effect claim can
  be made without a study.

## 5. Not part of this proposal

- Any implementation.
- Any change to CE1.2/CE1.3, BKT, the ledger or deployment.
- Any claim that failing-case feedback improves learning.
