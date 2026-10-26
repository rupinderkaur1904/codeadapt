Preview scripts for recommendability-review.md. Run from backend/ with
`PYTHONPATH=.:../docs/reviews/2026-10-26/recommendability uv run python ../docs/reviews/2026-10-26/recommendability/<script>`.
They switch `recommendable` on in memory only and run policy 1.4 unchanged (altrule.py also
patches the ranking in memory, preview only). Synthetic one-attempt histories; no accuracy claim.
