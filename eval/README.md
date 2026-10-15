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
