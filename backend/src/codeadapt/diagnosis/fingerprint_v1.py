"""Diagnostic method v1: strict fingerprint consistency with abstention.

The decision rules are numbered exactly as in docs/methodology.md §4; keep them in sync.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codeadapt.diagnosis.groups import count_groups, detection_patterns
from codeadapt.diagnosis.models import Diagnosis, DiagnosticInput, Observation, Outcome
from codeadapt.evidence.signature import OutcomeKind

CAVEAT = (
    "The observed behaviour is consistent with this error model; that is not proof of it, "
    "and explanations outside the modelled error space remain possible."
)
SINGLE_BEHAVIOUR = (
    "Every failing test that supports this model exercises the same behaviour (one "
    "behaviour group), so the evidence is one observation repeated. Other errors that "
    "produce the same behaviour cannot be ruled out."
)
NON_TERMINATION = (
    "The program did not finish within the CPU-time limit on these tests. That is "
    "consistent with a loop or recursion that stops making progress and with a program that "
    "is far too slow. Many different errors stop progress on the same inputs, so no error "
    "model is named (ADR-027)."
)


@dataclass(frozen=True)
class FingerprintConsistencyV1:
    name: str = "fingerprint_consistency"
    version: str = "1.2"
    min_support: int = 2
    # Distinct behaviour groups the supporting tests must span (diagnosis/groups.py).
    # 1 keeps v1's decisions and only reports the count; 2 is the C6 candidate rule.
    min_behaviours: int = 1
    max_excluded_fraction: float = 0.34
    # Rule 4b (v1.2, ADR-027): a reliable CPU-time-limit failure is reported as a symptom
    # and never named as an error model. False reproduces v1.1.
    time_limit_is_symptom: bool = True

    def diagnose(self, data: DiagnosticInput) -> Diagnosis:
        rationale: dict[str, Any] = {
            "parameters": {
                "min_support": self.min_support,
                "min_behaviours": self.min_behaviours,
                "max_excluded_fraction": self.max_excluded_fraction,
                "time_limit_is_symptom": self.time_limit_is_symptom,
            }
        }

        def result(outcome: Outcome, rule: int | str, **kw: Any) -> Diagnosis:
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

        timed_out = [
            o.test_key for o in reliable_failing if o.signature.kind is OutcomeKind.TIME_LIMIT
        ]

        contradictions = {
            key: [o.test_key for o in reliable if pred.get(o.test_key) != o.signature]
            for key, pred in data.models.items()
        }
        candidates = tuple(sorted(k for k, bad in contradictions.items() if not bad))
        rationale["contradicting_tests"] = {k: v for k, v in contradictions.items() if v}
        rationale["candidates"] = list(candidates)

        # Rule 4b (ADR-027). Every candidate predicts the time limit it is consistent with, so
        # naming one would rest on a one-bit observation many errors share. The candidates
        # are kept for research only; no consumer reads them.
        if self.time_limit_is_symptom and timed_out:
            rationale["timed_out_tests"] = timed_out
            rationale["other_failing_tests"] = [
                o.test_key for o in reliable_failing if o.test_key not in timed_out
            ]
            rationale["consistent_models"] = rationale.pop("candidates")
            rationale["note"] = NON_TERMINATION
            return result(Outcome.NON_TERMINATION_OBSERVED, "4b")
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
        supporting = [
            o.test_key for o in reliable if prediction[o.test_key] != data.reference[o.test_key]
        ]
        support = len(supporting)
        behaviours = count_groups(supporting, detection_patterns(data.reference, data.models))
        rationale["supporting_tests"] = supporting
        rationale["support_behaviours"] = behaviours
        if support < self.min_support or behaviours < self.min_behaviours:
            return result(Outcome.INSUFFICIENT_EVIDENCE, 7, candidates=candidates, support=support)
        rationale["caveat"] = CAVEAT
        # A supported diagnosis resting on one behaviour is reported as qualified, never as
        # established: consumers (feedback, policy, research views) read this field.
        rationale["evidence_strength"] = "single_behaviour" if behaviours == 1 else "multiple"
        if behaviours == 1:
            rationale["qualification"] = SINGLE_BEHAVIOUR
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


# Named parameter sets. "v1" is the deployed method (1.2 since ADR-027); "v1.1" reproduces
# every result recorded before it; "v2-candidate" is change C6 on top of v1.1, kept for
# evaluation until a decision adopts or rejects it (docs/decisions.md ADR-019).
METHODS: dict[str, FingerprintConsistencyV1] = {
    "v1": FingerprintConsistencyV1(),
    "v1.1": FingerprintConsistencyV1(version="1.1", time_limit_is_symptom=False),
    "v2-candidate": FingerprintConsistencyV1(
        version="2-candidate", min_behaviours=2, time_limit_is_symptom=False
    ),
}
