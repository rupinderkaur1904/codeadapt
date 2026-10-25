import dataclasses

from codeadapt.content import load_problem
from codeadapt.content.fingerprint import (
    REFERENCE,
    FingerprintSet,
    ProgramFingerprint,
    TestFingerprint,
)
from codeadapt.content.models import ProblemSpec
from codeadapt.content.report import render_report
from codeadapt.content.validate import ValidationReport, validate_fingerprints
from codeadapt.evidence import OutcomeKind, Signature
from codeadapt.execution.models import (
    BuildProfile,
    CompileResult,
    CompileStatus,
    EnvironmentInfo,
)
from tests.paths import DEMO_CONTENT

LOADED = load_problem(DEMO_CONTENT / "lower-bound")
# The real spec without its design declarations: each test below declares what its own
# synthetic fingerprints measure (see `declared`), or deliberately does not. The shape is
# pinned to 15 tests and 5 models so the synthetic patterns below do not depend on how much
# content the demo problem grows.
SPEC: ProblemSpec = LOADED.spec.model_copy(
    update={
        "tests": tuple(
            t.model_copy(update={"distinguishes": None, "purpose": None})
            for t in LOADED.spec.tests[:15]
        ),
        "error_models": tuple(
            m.model_copy(update={"known_limitation": None}) for m in LOADED.spec.error_models[:5]
        ),
    }
)
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
    return ProgramFingerprint(
        label=label, compile=compile_result(), tests=tests, sanitizer_checked=True
    )


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
    """Model i fails tests 2i and 2i+1; model i+1 (cyclically) also fails test 2i+1.

    So every model is detected by three tests in three distinct behaviour groups, and the
    last five tests detect nothing.
    """
    keys = [t.key for t in SPEC.tests]
    n = len(SPEC.error_models)
    bad: dict[int, set[str]] = {i: set() for i in range(n)}
    for i in range(n):
        bad[i] |= {keys[2 * i], keys[2 * i + 1]}
        bad[(i + 1) % n].add(keys[2 * i + 1])
    return {
        m.key: program(m.key, {k: (out("-7"), out("-7")) for k in bad[i]})
        for i, m in enumerate(SPEC.error_models)
    }


def declared(fps: FingerprintSet, spec: ProblemSpec = SPEC) -> ProblemSpec:
    """`spec` with every test declaring exactly what `fps` measures, and a purpose."""
    ref = {k: t.signature for k, t in fps.reference.tests.items()}
    tests = tuple(
        t.model_copy(
            update={
                "purpose": "synthetic",
                "distinguishes": tuple(
                    k
                    for k, fp in fps.models.items()
                    if fp.compiled and fp.tests[t.key].signature != ref[t.key]
                ),
            }
        )
        for t in spec.tests
    )
    return spec.model_copy(update={"tests": tests})


def check(fps: FingerprintSet) -> ValidationReport:
    return validate_fingerprints(declared(fps), fps)


def test_well_formed_fingerprints_validate() -> None:
    report = check(fingerprints(distinct_models()))
    assert report.ok, report.errors
    assert not report.warnings
    assert not report.limitations
    assert all(len(m.detecting_tests) == 3 for m in report.models)
    assert all(m.behaviour_groups == 3 for m in report.models)
    assert {len(p.distinguishing_tests) for p in report.pairs} == {4, 6}
    # 5 single-model groups, 5 two-model groups, and one group detecting nothing.
    assert len(report.groups) == 11
    assert report.groups[-1].detected_models == ()


def test_reference_must_match_authored_expectations() -> None:
    first = SPEC.tests[0].key
    ref = program(REFERENCE, {first: (out("999"), out("999"))})
    report = check(fingerprints(distinct_models(), ref))
    assert any("reference disagrees" in e and first in e for e in report.errors)


def test_undetectable_model_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = program(key)
    report = check(fingerprints(models))
    assert any("cannot detect it" in e and key in e for e in report.errors)


def test_weakly_detected_model_warns() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = program(key, {SPEC.tests[0].key: (out("-1"), out("-1"))})
    report = check(fingerprints(models))
    assert report.ok
    assert any("only 1 test" in w and key in w for w in report.warnings)


def test_identical_models_warn_as_ambiguous() -> None:
    models = distinct_models()
    a, b = SPEC.error_models[0].key, SPEC.error_models[1].key
    models[b] = program(b, {k: v.runs for k, v in models[a].tests.items()})
    report = check(fingerprints(models))
    assert any("identical fingerprints" in w for w in report.warnings)
    pair = next(p for p in report.pairs if {p.a, p.b} == {a, b})
    assert pair.distinguishing_tests == ()


def test_nondeterminism_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = program(key, {SPEC.tests[3].key: (out("1"), out("2"))})
    report = check(fingerprints(models))
    assert any("non-deterministic" in e for e in report.errors)


def test_compile_failure_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = ProgramFingerprint(label=key, compile=compile_result(ok=False), tests={})
    report = check(fingerprints(models))
    assert any("does not compile" in e and "boom" in e for e in report.errors)
    assert key not in {m.key for m in report.models}


def test_infrastructure_errors_are_errors() -> None:
    infra = Signature(kind=OutcomeKind.INFRASTRUCTURE_ERROR, detail="x")
    ref = program(REFERENCE, {SPEC.tests[0].key: (infra, infra)})
    report = check(fingerprints(distinct_models(), ref))
    assert any("infrastructure error" in e for e in report.errors)


def test_undefined_behaviour_in_a_model_is_an_error() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    models[key] = models[key].model_copy(
        update={"sanitizer_findings": {"empty": "heap-buffer-overflow"}}
    )
    report = check(fingerprints(models))
    assert any("undefined behaviour" in e and "heap-buffer-overflow" in e for e in report.errors)


def test_unchecked_sanitizer_warns() -> None:
    ref = program(REFERENCE).model_copy(update={"sanitizer_checked": False})
    report = check(fingerprints(distinct_models(), ref))
    assert report.ok
    assert any("sanitizer build unavailable" in w for w in report.warnings)


# ------------------------------------------------- declared intent and behaviour groups
def test_declared_distinguishes_must_match_the_measurement() -> None:
    fps = fingerprints(distinct_models())
    spec = declared(fps)
    first = spec.tests[0]
    wrong = spec.model_copy(
        update={
            "tests": (first.model_copy(update={"distinguishes": ()}), *spec.tests[1:]),
        }
    )
    report = validate_fingerprints(wrong, fps)
    assert any(
        f"test {first.key!r} declares distinguishes []" in e and "but measured" in e
        for e in report.errors
    )


def test_undeclared_distinguishes_and_missing_purpose_warn() -> None:
    fps = fingerprints(distinct_models())
    report = validate_fingerprints(SPEC, fps)  # nothing declared
    assert report.ok
    assert sum("does not declare `distinguishes`" in w for w in report.warnings) == len(SPEC.tests)
    # The five tests that separate no model must say why they exist.
    assert sum("states no `purpose`" in w for w in report.warnings) == 5


def test_a_model_resting_on_one_behaviour_group_warns_unless_documented() -> None:
    models = distinct_models()
    key = SPEC.error_models[0].key
    same = (out("-1"), out("-1"))
    # Detected by three tests that no other model separates: three tests, one behaviour.
    models[key] = program(key, {t.key: same for t in SPEC.tests[10:13]})
    fps = fingerprints(models)
    report = check(fps)
    summary = next(m for m in report.models if m.key == key)
    assert (len(summary.detecting_tests), summary.behaviour_groups) == (3, 1)
    assert any("only 1 behaviour group" in w and key in w for w in report.warnings)

    documented = declared(fps).model_copy(
        update={
            "error_models": tuple(
                m.model_copy(update={"known_limitation": "one behaviour; accepted"})
                if m.key == key
                else m
                for m in SPEC.error_models
            )
        }
    )
    report = validate_fingerprints(documented, fps)
    assert not any("behaviour group" in w for w in report.warnings)
    assert any("Documented: one behaviour; accepted" in lim for lim in report.limitations)


def test_report_is_deterministic_and_shows_agreement() -> None:
    fps = fingerprints(distinct_models())
    spec = declared(fps)
    report = validate_fingerprints(spec, fps)
    problem = dataclasses.replace(LOADED, spec=spec)
    text = render_report(problem, fps, report)
    assert text == render_report(problem, fps, report)
    assert "| NO |" not in text
    assert "## Behaviour groups" in text
    assert text.count("| yes |") == len(spec.tests)


def test_inconclusive_measurement_is_an_error() -> None:
    # A model's predicted time limit must be a CPU-limit stop; a wall-clock stop that
    # persisted through re-measurement leaves the content unusable (fail closed).
    stall = Signature(kind=OutcomeKind.INCONCLUSIVE)
    models = distinct_models()
    key = SPEC.error_models[0].key
    first = SPEC.tests[0].key
    models[key] = program(key, {first: (stall, stall)})
    report = validate_fingerprints(SPEC, fingerprints(models))
    assert not report.ok
    assert any("inconclusive run" in e and key in e for e in report.errors)
