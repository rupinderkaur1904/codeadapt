from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_CONTENT = REPO_ROOT / "content" / "demo"
HELDOUT = REPO_ROOT / "eval" / "heldout"

# The demo problems, by slug: every content directory with a problem.toml. The first four are
# the original bank; tests that need a fixed problem name it explicitly.
DEMO_SLUGS = sorted(p.parent.name for p in DEMO_CONTENT.glob("*/problem.toml"))
ORIGINAL_SLUGS = ["count-occurrences", "first-true", "last-less-than", "lower-bound"]
