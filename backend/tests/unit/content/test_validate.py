from codeadapt.content import load_problem
from codeadapt.content.fingerprint import (
    REFERENCE,
    FingerprintSet,
    ProgramFingerprint,
    TestFingerprint,
)
from codeadapt.content.models import ProblemSpec
from codeadapt.content.validate import validate_fingerprints
from codeadapt.evidence import OutcomeKind, Signature
from codeadapt.execution.models import (
    BuildProfile,
    CompileResult,
    CompileStatus,
    EnvironmentInfo,
)
from tests.paths import DEMO_CONTENT

SPEC: ProblemSpec = load_problem(DEMO_CONTENT / "lower-bound").spec
ENV = EnvironmentInfo(
    backend="fake",
    image="img",
    image_id="sha256:0",
    compiler_version="g++ 14",
    container_runtime="runc",
    engine_version="0",
    host_kernel="0",
)


def compile_result(ok: bool = True) -> CompileResult:
    return CompileResult(
        status=CompileStatus.OK if ok else CompileStatus.ERROR,
        profile=BuildProfile.STANDARD,
        flags=(),
        exit_code=0 if ok else 1,
        diagnostics="" if ok else "main.cpp:1: error: boom",
        diagnostics_truncated=False,
        wall_ms=1,
    )


def out(value: str) -> Signature:
    return Signature(kind=OutcomeKind.OUTPUT, detail=value)


def program(
    label: str, overrides: dict[str, tuple[Signature, ...]] | None = None
) -> ProgramFingerprint:
    overrides = overrides or {}
    tests = {
        t.key: TestFingerprint(runs=overrides.get(t.key, (out(t.expected), out(t.expected))))
        for t in SPEC.tests
    }
    return ProgramFingerprint(label=label, compile=compile_result(), tests=tests)


def fingerprints(
    models: dict[str, ProgramFingerprint], reference: ProgramFingerprint | None = None
) -> FingerprintSet:
    return FingerprintSet(
        problem_slug=SPEC.slug,
        problem_version="v",
        environment=ENV,
        repeats=2,
        reference=reference or program(REFERENCE),
        models=models,
    )


def distinct_models() -> dict[str, ProgramFingerprint]:
    """Each model fails a different, disjoint pair of tests."""
    keys = [t.key for t in SPEC.tests]
    models = {}
    for i, model in enumerate(SPEC.error_models):
        bad = keys[2 * i : 2 * i + 2]
        models[model.key] = program(model.key, {k: (out("-7"), out("-7")) for k in bad})
    return models


def test_well_formed_fingerprints_validate() -> None:
    report = validate_fingerprints(SPEC, fingerprints(distinct_models()))
    assert report.ok, report.errors
    assert not report.warnings
    assert all(len(m.detecting_tests) == 2 for m in report.models)
    assert all(len(p.distinguishing_tests) == 4 for p in report.pairs)


def test_reference_must_match_authored_expectations() -> None:
    first = SPEC.tests[0].key
    ref = program(REFERENCE, {first: (out("999"), out("999"))})
    report = validate_fingerprints(SPEC, fingerprints(distinct_models(), ref))
    assert any("reference disagrees" in e and first in e for e in report.errors)


def test_undetectable_model_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = program(key)
    report = validate_fingerprints(SPEC, fingerprints(models))
    assert any("cannot detect it" in e and key in e for e in report.errors)


def test_weakly_detected_model_warns() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = program(key, {SPEC.tests[0].key: (out("-1"), out("-1"))})
    report = validate_fingerprints(SPEC, fingerprints(models))
    assert report.ok
    assert any("only 1 test" in w and key in w for w in report.warnings)


def test_identical_models_warn_as_ambiguous() -> None:
    models = distinct_models()
    a, b = SPEC.error_models[0].key, SPEC.error_models[1].key
    models[b] = program(b, {k: v.runs for k, v in models[a].tests.items()})
    report = validate_fingerprints(SPEC, fingerprints(models))
    assert any("identical fingerprints" in w for w in report.warnings)
    pair = next(p for p in report.pairs if {p.a, p.b} == {a, b})
    assert pair.distinguishing_tests == ()


def test_nondeterminism_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = program(key, {SPEC.tests[3].key: (out("1"), out("2"))})
    report = validate_fingerprints(SPEC, fingerprints(models))
    assert any("non-deterministic" in e for e in report.errors)


def test_compile_failure_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = ProgramFingerprint(label=key, compile=compile_result(ok=False), tests={})
    report = validate_fingerprints(SPEC, fingerprints(models))
    assert any("does not compile" in e and "boom" in e for e in report.errors)
    assert key not in {m.key for m in report.models}


def test_infrastructure_errors_are_errors() -> None:
    infra = Signature(kind=OutcomeKind.INFRASTRUCTURE_ERROR, detail="x")
    ref = program(REFERENCE, {SPEC.tests[0].key: (infra, infra)})
    report = validate_fingerprints(SPEC, fingerprints(distinct_models(), ref))
    assert any("infrastructure error" in e for e in report.errors)
