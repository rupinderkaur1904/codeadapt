# ADR-027 preview: replay of proposed rule 4b on recorded VAL1-A data

This is **not** the approved re-run required by ADR-027 §8. `replay.py` applies the
proposed rule to the v1.1 observations recorded in `../val1a-2026-10-21/results/`. It
re-executes nothing and changes no production code. Its output is `val1a-replay.json`,
with a summary and one row per program.

The results are summarised in `docs/proposals/adr-027-non-termination-evidence.md` §7:

- named diagnoses fall from 32/98 to 10/98;
- wrong names fall from 17/32 to 0/10, with an upper 95% bound of 28%;
- 30 programs become `non_termination_observed`.

The labels are Claude's a-priori labels from VAL1-A, not human labels, and the mutants are
synthetic.
