"""Check that a problem's executed fingerprints make it diagnosable.

Pure function over a `FingerprintSet`: no I/O, so every rule is unit-tested.

Errors make the content unusable. Warnings describe limits of the test suite that the
diagnostic method will surface as abstentions (e.g. two error models it cannot separate).
"""

from __future__ import annotations

from itertools import combinations

from pydantic import BaseModel, ConfigDict

from codeadapt.content.fingerprint import FingerprintSet, ProgramFingerprint
from codeadapt.content.models import ProblemSpec
from codeadapt.evidence.signature import OutcomeKind, Signature

# Mirrors the diagnosis default (methodology §4, rule 7): a model explaining fewer failing
# tests than this can never be diagnosed, only reported as insufficient evidence.
DEFAULT_MIN_SUPPORT = 2


class ModelSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    skill: str
    # Tests on which the model's behaviour differs from the reference.
    detecting_tests: tuple[str, ...]


class PairSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: str
    distinguishing_tests: tuple[str, ...]


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem_slug: str
    problem_version: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    models: tuple[ModelSummary, ...]
    pairs: tuple[PairSummary, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _program_errors(fp: ProgramFingerprint) -> list[str]:
    who = "reference" if fp.label.startswith("__") else f"error model {fp.label!r}"
    if not fp.compiled:
        first = fp.compile.diagnostics.strip().splitlines()[:3]
        return [f"{who} does not compile ({fp.compile.status.value}): {' | '.join(first)}"]
    errors = []
    for key, test in fp.tests.items():
        if not test.deterministic:
            runs = ", ".join(str(s) for s in test.runs)
            errors.append(f"{who} is non-deterministic on test {key!r}: {runs}")
        elif any(s.kind is OutcomeKind.INFRASTRUCTURE_ERROR for s in test.runs):
            errors.append(f"{who}: infrastructure error on test {key!r}")
    return errors


def _signatures(fp: ProgramFingerprint) -> dict[str, Signature | None]:
    return {key: t.signature for key, t in fp.tests.items()}


def validate_fingerprints(
    spec: ProblemSpec, fps: FingerprintSet, *, min_support: int = DEFAULT_MIN_SUPPORT
) -> ValidationReport:
    errors = _program_errors(fps.reference)
    warnings: list[str] = []
    for fp in fps.models.values():
        errors += _program_errors(fp)

    ref = _signatures(fps.reference)
    for test in spec.tests:
        observed = ref.get(test.key)
        expected = Signature(kind=OutcomeKind.OUTPUT, detail=test.expected.strip())
        if fps.reference.compiled and observed is not None and observed != expected:
            errors.append(
                f"reference disagrees with the authored expectation on test {test.key!r}: "
                f"got {observed}, expected {expected}"
            )

    summaries: list[ModelSummary] = []
    usable: dict[str, dict[str, Signature | None]] = {}
    for model in spec.error_models:
        fp = fps.models[model.key]
        if not fp.compiled:
            continue
        sigs = _signatures(fp)
        usable[model.key] = sigs
        detecting = tuple(t.key for t in spec.tests if sigs[t.key] != ref.get(t.key))
        summaries.append(ModelSummary(key=model.key, skill=model.skill, detecting_tests=detecting))
        if not detecting:
            errors.append(
                f"error model {model.key!r} behaves exactly like the reference on every test; "
                "the suite cannot detect it"
            )
        elif len(detecting) < min_support:
            warnings.append(
                f"error model {model.key!r} is detected by only {len(detecting)} test(s) "
                f"(< {min_support}); it can never be diagnosed with sufficient support"
            )

    pairs: list[PairSummary] = []
    for a, b in combinations(sorted(usable), 2):
        diff = tuple(t.key for t in spec.tests if usable[a][t.key] != usable[b][t.key])
        pairs.append(PairSummary(a=a, b=b, distinguishing_tests=diff))
        if not diff:
            warnings.append(
                f"error models {a!r} and {b!r} have identical fingerprints; "
                "submissions matching them will be reported as ambiguous"
            )

    return ValidationReport(
        problem_slug=spec.slug,
        problem_version=fps.problem_version,
        errors=tuple(errors),
        warnings=tuple(warnings),
        models=tuple(summaries),
        pairs=tuple(pairs),
    )
