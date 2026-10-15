"""Check that a problem's executed fingerprints make it diagnosable.

Pure function over a `FingerprintSet`: no I/O, so every rule is unit-tested.

Errors make the content unusable. Warnings describe limits of the test suite that the
diagnostic method will surface as abstentions (e.g. two error models it cannot separate).
Limitations are weaknesses the author has documented and accepted (`known_limitation`).

Declared design intent (a test's `distinguishes`) is checked against the measured matrix,
so the design record cannot drift from what the tests actually do.
"""

from __future__ import annotations

from itertools import combinations

from pydantic import BaseModel, ConfigDict

from codeadapt.content.fingerprint import FingerprintSet, ProgramFingerprint
from codeadapt.content.models import ProblemSpec
from codeadapt.diagnosis.groups import count_groups, detection_patterns, group_tests
from codeadapt.evidence.signature import OutcomeKind, Signature

# Mirrors the diagnosis default (methodology §4, rule 7): a model explaining fewer failing
# tests than this can never be diagnosed, only reported as insufficient evidence.
DEFAULT_MIN_SUPPORT = 2
# Distinct behaviour groups a model should be detected by. Below this, every test that
# detects the model shows the same behaviour, and other errors with that behaviour collide.
DEFAULT_MIN_BEHAVIOURS = 2


class ModelSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    skill: str
    # Tests on which the model's behaviour differs from the reference.
    detecting_tests: tuple[str, ...]
    behaviour_groups: int = 0


class PairSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: str
    distinguishing_tests: tuple[str, ...]


class GroupSummary(BaseModel):
    """Tests every modelled program passes together or fails together."""

    model_config = ConfigDict(frozen=True)

    detected_models: tuple[str, ...]  # empty: the tests separate no model
    tests: tuple[str, ...]


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem_slug: str
    problem_version: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    models: tuple[ModelSummary, ...]
    pairs: tuple[PairSummary, ...]
    groups: tuple[GroupSummary, ...] = ()
    limitations: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def _program_errors(fp: ProgramFingerprint) -> list[str]:
    who = "reference" if fp.label.startswith("__") else f"error model {fp.label!r}"
    if not fp.compiled:
        first = fp.compile.diagnostics.strip().splitlines()[:3]
        return [f"{who} does not compile ({fp.compile.status.value}): {' | '.join(first)}"]
    errors = [
        f"{who} has undefined behaviour on test {key!r} (sanitizer: {kind})"
        for key, kind in fp.sanitizer_findings.items()
    ]
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
    spec: ProblemSpec,
    fps: FingerprintSet,
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
    min_behaviours: int = DEFAULT_MIN_BEHAVIOURS,
) -> ValidationReport:
    errors = _program_errors(fps.reference)
    warnings: list[str] = []
    limitations: list[str] = []
    for fp in fps.models.values():
        errors += _program_errors(fp)
    unchecked = [
        fp.label
        for fp in (fps.reference, *fps.models.values())
        if fp.compiled and not fp.sanitizer_checked
    ]
    if unchecked:
        warnings.append(
            f"sanitizer build unavailable; not checked for undefined behaviour: {unchecked}"
        )

    ref = _signatures(fps.reference)
    for test in spec.tests:
        observed = ref.get(test.key)
        expected = Signature(kind=OutcomeKind.OUTPUT, detail=test.expected.strip())
        if fps.reference.compiled and observed is not None and observed != expected:
            errors.append(
                f"reference disagrees with the authored expectation on test {test.key!r}: "
                f"got {observed}, expected {expected}"
            )

    usable: dict[str, dict[str, Signature | None]] = {
        m.key: _signatures(fps.models[m.key])
        for m in spec.error_models
        if fps.models[m.key].compiled
    }
    order = [t.key for t in spec.tests]
    patterns = detection_patterns({k: ref.get(k) for k in order}, usable)
    summaries: list[ModelSummary] = []
    for model in spec.error_models:
        if model.key not in usable:
            continue
        detecting = tuple(k for k in order if model.key in patterns[k])
        groups = count_groups(detecting, patterns)
        summaries.append(
            ModelSummary(
                key=model.key,
                skill=model.skill,
                detecting_tests=detecting,
                behaviour_groups=groups,
            )
        )
        if detecting and groups < min_behaviours:
            text = (
                f"error model {model.key!r} is detected by {len(detecting)} test(s) but only "
                f"{groups} behaviour group(s) (< {min_behaviours}); other errors with that "
                "behaviour would be diagnosed as this model"
            )
            if model.known_limitation:
                limitations.append(f"{text}. Documented: {model.known_limitation}")
            else:
                warnings.append(text)
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

    if usable:
        for test in spec.tests:
            measured = sorted(patterns[test.key])
            if test.distinguishes is None:
                warnings.append(
                    f"test {test.key!r} does not declare `distinguishes` (measured: {measured})"
                )
            elif sorted(test.distinguishes) != measured:
                errors.append(
                    f"test {test.key!r} declares distinguishes {sorted(test.distinguishes)} "
                    f"but measured {measured}"
                )
            if not measured and not test.purpose:
                warnings.append(
                    f"test {test.key!r} separates no error model from the reference and "
                    "states no `purpose`"
                )

    return ValidationReport(
        problem_slug=spec.slug,
        problem_version=fps.problem_version,
        errors=tuple(errors),
        warnings=tuple(warnings),
        models=tuple(summaries),
        pairs=tuple(pairs),
        groups=tuple(
            GroupSummary(detected_models=tuple(sorted(p)), tests=tests)
            for p, tests in group_tests(patterns, order)
        ),
        limitations=tuple(limitations),
    )
