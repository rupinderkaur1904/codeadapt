"""Diagnostic method v1: strict fingerprint consistency with abstention.

The decision rules are numbered exactly as in docs/methodology.md §4; keep them in sync.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codeadapt.diagnosis.models import Diagnosis, DiagnosticInput, Observation, Outcome
from codeadapt.evidence.signature import OutcomeKind

CAVEAT = (
    "The observed behaviour is consistent with this error model; that is not proof of it, "
    "and explanations outside the modelled error space remain possible."
)


@dataclass(frozen=True)
class FingerprintConsistencyV1:
    name: str = "fingerprint_consistency"
    version: str = "1"
    min_support: int = 2
    max_excluded_fraction: float = 0.34

    def diagnose(self, data: DiagnosticInput) -> Diagnosis:
        rationale: dict[str, Any] = {
            "parameters": {
                "min_support": self.min_support,
                "max_excluded_fraction": self.max_excluded_fraction,
            }
        }

        def result(outcome: Outcome, rule: int, **kw: Any) -> Diagnosis:
            rationale["rule"] = rule
            return Diagnosis(
                method=self.name,
                method_version=self.version,
                outcome=outcome,
                rationale=rationale,
                **kw,
            )

        # Rule 1
        if not data.compiled:
            return result(Outcome.COMPILE_ERROR, 1)
        # Rule 2
        observations = list(data.observations)
        infra = [
            o.test_key for o in observations if o.signature.kind is OutcomeKind.INFRASTRUCTURE_ERROR
        ]
        if not observations or infra:
            rationale["infrastructure_errors"] = infra
            return result(Outcome.EXECUTION_ERROR, 2)

        unknown = [o.test_key for o in observations if o.test_key not in data.reference]
        if unknown:
            raise ValueError(f"observations for tests without a reference behaviour: {unknown}")

        reliable = [o for o in observations if o.reliable]
        excluded = [o for o in observations if not o.reliable]
        failing = [o for o in observations if o.signature != data.reference[o.test_key]]
        reliable_failing = [o for o in failing if o.reliable]
        rationale["tests"] = [self._row(o, data) for o in observations]
        rationale["excluded"] = {o.test_key: o.excluded_reason for o in excluded}
        rationale["failing_tests"] = [o.test_key for o in failing]

        # Rule 3
        excluded_fraction = len(excluded) / len(observations)
        if excluded_fraction > self.max_excluded_fraction or (failing and not reliable_failing):
            rationale["excluded_fraction"] = round(excluded_fraction, 4)
            return result(Outcome.UNRELIABLE_EVIDENCE, 3)
        # Rule 4
        if not reliable_failing:
            rationale["note"] = (
                f"All {len(reliable)} reliable tests matched the reference. This shows no failure "
                "on the tested cases; it does not prove the implementation correct."
            )
            return result(Outcome.NO_FAILURE_OBSERVED, 4)

        contradictions = {
            key: [o.test_key for o in reliable if pred.get(o.test_key) != o.signature]
            for key, pred in data.models.items()
        }
        candidates = tuple(sorted(k for k, bad in contradictions.items() if not bad))
        rationale["contradicting_tests"] = {k: v for k, v in contradictions.items() if v}
        rationale["candidates"] = list(candidates)

        # Rule 5
        if not candidates:
            rationale["nearest_models"] = sorted(
                ({"model": k, "contradicting": len(v)} for k, v in contradictions.items()),
                key=lambda d: (d["contradicting"], d["model"]),
            )[:3]
            return result(Outcome.UNMODELLED_BEHAVIOUR, 5)
        # Rule 6
        if len(candidates) > 1:
            rationale["distinguishing_tests"] = self._distinguishing(candidates, data)
            return result(Outcome.AMBIGUOUS, 6, candidates=candidates)
        # Rules 7 and 8
        (model,) = candidates
        prediction = data.models[model]
        support = sum(1 for o in reliable if prediction[o.test_key] != data.reference[o.test_key])
        rationale["supporting_tests"] = [
            o.test_key for o in reliable if prediction[o.test_key] != data.reference[o.test_key]
        ]
        if support < self.min_support:
            return result(Outcome.INSUFFICIENT_EVIDENCE, 7, candidates=candidates, support=support)
        rationale["caveat"] = CAVEAT
        return result(
            Outcome.HYPOTHESIS_SUPPORTED,
            8,
            selected_model=model,
            candidates=candidates,
            support=support,
        )

    @staticmethod
    def _row(o: Observation, data: DiagnosticInput) -> dict[str, Any]:
        return {
            "test": o.test_key,
            "observed": str(o.signature),
            "reference": str(data.reference[o.test_key]),
            "reliable": o.reliable,
            "agrees_with": sorted(
                k for k, pred in data.models.items() if pred.get(o.test_key) == o.signature
            ),
        }

    @staticmethod
    def _distinguishing(candidates: tuple[str, ...], data: DiagnosticInput) -> list[str]:
        """Tests (in this suite) where the candidates' predictions differ.

        Empty when the suite cannot separate them; non-empty only if those tests were
        excluded for this submission.
        """
        keys = sorted(data.reference)
        return [k for k in keys if len({str(data.models[c].get(k)) for c in candidates}) > 1]
