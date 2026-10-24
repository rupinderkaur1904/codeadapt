# PC1 status (not frozen; updated as things change)

The frozen files (`protocol.md` 1.0, `README.md`, `permission.md`, the scripts and fixtures) are
unchanged and still match `MANIFEST.sha256`. Some of their statements describe the state when
they were frozen and are no longer true. This file records the current state.

**As of 2026-10-24, after Phase F:**

| Item | State | Evidence |
| --- | --- | --- |
| Permission gate | **Open at `metadata` only** (record version 2, published-licence basis, A1). Closed at `code`. | `permission/record.json` (dc4c0e1); `pc1.py gate` |
| Archive download | Done once, outside the repository (D1) | `DEVIATIONS.md` |
| Extraction and identification | Re-run under the version 2 record; output identical to the D2 run | — |
| Confirmation | ALDS1_4_B ↔ p02268, confirmed by the owner (`--role owner`) | — |
| Counting, pairing (Phase F) | **Run on 2026-10-24.** No stop condition fired. Counts are **not** in this repository because `publish_derived_statistics` is false. | owner's project files |
| Source code | Never read | — |
| Phase E | **Not started.** Needs a code-level permission basis (A1 cannot give one) and an owner-approved plan. | — |
| README "no CodeNet data has been downloaded", protocol section 12 "no permission record exists" | Out of date (frozen text); superseded by this file | — |

## History: why PC1 was blocked

The owner is an independent researcher. The frozen gate accepts only an explicit approval from
a supervisor, an institutional research-data office, an institutional ethics office, or IBM.
None exists, so under protocol 1.0 the gate cannot honestly open.

## Amendment A1 + A1b: approved by the owner on 2026-10-24 and applied

**Amendment A1:** a second basis, `published dataset licence` (record version 2), for the
`metadata` level only. The dataset is reported to use CDLA-Permissive-2.0 (CodeNet paper
datasheet; Linux Foundation, June 2021). A1 would require:

- a statement by the dataset provider, read first-hand by the owner, quoting the licence;
- the licence text committed with its hash;
- what was not verified, and the known risks;
- six self-imposed conditions: aggregate outputs only, no re-identification, no linkage with
  other sources, no source-code access, no redistribution, data outside the repository.

It never opens the `code` level.

**Known gap that A1 should also close (A1b, proposed 2026-10-24):** nothing reads
`scope.publish_derived_statistics`. The scripts already refuse real-data outputs inside this
repository, but the reports carry no statement of whether they may be published. Only the
README says "commit counts only if" the flag is true. A1b would have `feasibility` copy the
flag into `feasibility.json` and print it at the top of `feasibility.md` ("NOT FOR PUBLICATION"
when false), and it would add tests for both. A1b is now implemented (`publication_notice`).

## Evidence still needed to unblock

1. ~~Owner approval of A1 (and A1b)~~: approved 2026-10-24.
2. The owner's first-hand reading of the provider's licence statement (exact quote and date).
   Search excerpts seen by Claude do not count.
3. Optional and recommended: a reply from the CodeNet maintainers confirming the dataset
   licence (draft question in the A1 proposal).

## Next step (owner)

Phase F is complete and stopped at its gate. The owner decides whether to pursue Phase E. That
would need a code-level permission basis and a separate frozen plan. Nothing runs until then.
