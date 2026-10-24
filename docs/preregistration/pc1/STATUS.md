# PC1 status (not frozen; updated as things change)

The frozen files (`protocol.md` 1.0, `README.md`, `permission.md`, the scripts and fixtures) are
unchanged and still match `MANIFEST.sha256`. Some of their statements describe the state when
they were frozen and are no longer true. This file records the current state.

**As of 2026-10-24 (after A1 and A1b were approved and applied):**

| Item | State | Evidence |
| --- | --- | --- |
| Permission gate | **Closed.** The only record is withdrawn. | `pc1.py gate` exit 3 at both levels; `permission/CORRECTIONS.md` |
| Archive download | Done once, outside the repository (D1) | `DEVIATIONS.md` |
| Extraction and identification | Done (D2); ALDS1_4_B ↔ p02268 identified from statement text, **not confirmed** | `DEVIATIONS.md` |
| Counting, pairing (Phase F) | **Not run** | — |
| Source code | Never read | — |
| README "no CodeNet data has been downloaded", protocol section 12 "no permission record exists" | Out of date (frozen text); superseded by this file | — |

## Why PC1 is blocked

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

Fill in `permission/record-licence.template.json` with your own first-hand reading of the
CodeNet paper's licence sentence: the exact quote, where it is, and the date you read it. Then
save it as `permission/record.json` with `status: granted`. Until then, the gate stays closed.
The tripwire test `test_committed_record_is_not_an_open_gate` is updated in the same commit
that adds a truthful record.
