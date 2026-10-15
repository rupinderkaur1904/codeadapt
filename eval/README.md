# Held-out synthetic evaluation set

Submissions whose bug is known by construction, used by `codeadapt-eval`
(docs/methodology.md §6.1). Data class: `synthetic` (ADR-008). Nothing here is student data.

Each `heldout/<problem-slug>/cases.toml` lists cases:

```toml
problem = "lower-bound"

[[cases]]
file = "upper_bound_closed.cpp"
truth = "upper_bound_confusion"   # an error-model key, "correct", or "unmodelled"
note = "Closed-interval loop using <=."
```

Write new cases in a different style from the error model they target, and before running
the method on them. Run from `backend/`:

```
uv run codeadapt-eval --json report.json --markdown report.md
```

## Calibration cases

`calibration/<problem-slug>/cases.toml` has the same format. Calibration cases are written
*after* a design analysis, to probe what it predicted (for lower-bound: the collision of
`hi_init_last_index` with a clamped result, and alternatives to `stops_at_first_match`).
Because they informed design decisions, their results are reported separately and never
pooled with held-out results:

```
uv run codeadapt-eval --cases ../eval/calibration --case-set calibration
```

`--method v1` (default, deployed) or `--method v2-candidate` (behaviour-group support rule,
ADR-019) chooses the diagnostic parameter set.
