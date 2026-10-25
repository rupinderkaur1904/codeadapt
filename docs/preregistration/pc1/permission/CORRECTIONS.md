# Permission record corrections

Written by Claude at the owner's request. `record.json` itself is written only by the owner.

## C1 (2026-10-23, committed 2026-10-24): record 447757a withdrawn

- **What was wrong:** `record.json` as committed in 447757a said `granted_by_role: supervisor`
  and `basis: explicit approval`. The owner is an independent student researcher with no
  supervisor, and nobody approved the work. The record was entered in error, following
  instructions that assumed a supervisor existed.
- **Correction:** in 323f3a9 the owner set `status` to `withdrawn` and added a `withdrawal`
  note saying the record was entered in error. The original fields are kept, and the original
  text stays in git history at 447757a.
- **Verified:** `python3 docs/preregistration/pc1/scripts/pc1.py gate` exits 3 (gate closed) at
  both the `metadata` and the `code` level. This is pinned by the unit test
  `test_withdrawn_record_closes_the_gate`.
- **Effect on work already done:** see `../DEVIATIONS.md` (D1–D3). No submission was counted
  or paired, and no source code was read.
- **What would reopen the gate:** only a new, truthful record that the gate accepts. Under the
  frozen protocol, that means an explicit approval from one of the four listed roles, which the
  owner does not have. A licence-based basis needs amendment A1, which is proposed and not
  approved (`../STATUS.md`).
