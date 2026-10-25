# min-capacity held-out re-run after ADR-032 (2026-10-25)

**Why.** ADR-032 added a `known_limitation` to `strict_day_limit` and `full_day_overflows`,
which creates a new min-capacity content version (`63287d72…`; previously `ab9f81a8…`). The
diagnosis methods do not read `known_limitation`, so diagnosis outcomes were expected to be
identical. This re-run checks that on the new version. The earlier record in
`docs/evaluation/ce2-2026-10-24/min-capacity.*` is preserved unchanged.

**Command** (from `backend/`):

```
uv run codeadapt-eval --content ../content/demo --heldout ../eval/heldout \
  --problem min-capacity --runs 2 --compare v1.1 v1.2 v1 \
  --json ../docs/evaluation/adr032-2026-10-25/min-capacity.json \
  --markdown ../docs/evaluation/adr032-2026-10-25/min-capacity.md
```

**Environment.** g++ 14.2.0, `runc`, image `codeadapt-sandbox:gcc14.2-1`, 2 runs per case.

**Result.** `min-capacity.md` is byte-identical to the 2026-10-24 record: every case has the
same outcome and named model under v1.1, v1.2 and v1.3. The regenerated content report
(`docs/content-reports/min-capacity.md`) changes only the content version and the two
limitation notes; fingerprints, behaviour groups and validation results are unchanged.

What changes with ADR-032 is downstream of the diagnosis: feedback wording (qualified), skill
evidence (no `equality_handling` observation from these two models) and the recommendation
rationale (`qualified_hypothesis`). Those are covered by tests, not by this evaluation.

**Synthetic, author-written cases.** 7 cases; not an accuracy estimate for real students.
