"""L21 reproduction: what policy 1.4 records after a pass (run from backend/ with uv run python)."""
import sys
sys.path.insert(0, ".")
from codeadapt.diagnosis import Outcome
from tests.unit.test_adaptation import POLICY, PROBLEMS, attempt

def show(label, slugs):
    hist = [attempt(s, Outcome.NO_FAILURE_OBSERVED, n=i) for i, s in enumerate(slugs)]
    rec = POLICY.recommend(hist[-1], hist, PROBLEMS)
    print(f"{label}: action={rec.action.value} next={rec.problem_slug} note={rec.rationale.get('note')!r}")
    return rec

show("A first-max-index passed (only attempt)", ["first-max-index"])
show("B pivot-index passed, nothing else in prefix-sums tried", ["pivot-index"])
show("C integer-sqrt passed after the 3 recommendable binary-search problems", ["lower-bound", "count-occurrences", "last-less-than", "integer-sqrt"])
show("D integer-sqrt passed first", ["integer-sqrt"])
