"""Run the held-out set through the same evidence and diagnosis code as the worker.

No database is touched: results go only into the returned report.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict

from codeadapt.content.catalogue import Catalogue
from codeadapt.content.fingerprint import FingerprintSet, fingerprint_problem
from codeadapt.content.loader import LoadedProblem
from codeadapt.content.validate import validate_fingerprints
from codeadapt.diagnosis import DiagnosticInput, DiagnosticMethod, Outcome
from codeadapt.evaluation.heldout import CORRECT, UNMODELLED, HeldoutCase
from codeadapt.evaluation.metrics import LIMITATIONS, CaseResult, Metrics, compute
from codeadapt.evidence.collect import collect_evidence
from codeadapt.evidence.signature import Signature
from codeadapt.execution.backend import SandboxBackend


class CaseRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    file: str
    truth: str
    outcome: str
    selected_model: str | None
    candidates: tuple[str, ...]
    classification: str
    reproducible: bool


class ProblemReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem: str
    version: str
    metrics: Metrics
    identical_model_pairs: tuple[tuple[str, str], ...]
    detecting_tests: dict[str, int]
    cases: tuple[CaseRow, ...]


class EvaluationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_class: str = "synthetic"
    # "heldout" (reported results) or "calibration" (used while designing; never pooled).
    case_set: str = "heldout"
    method: str
    method_version: str
    runs_per_case: int
    environment: dict[str, Any]
    overall: Metrics
    problems: tuple[ProblemReport, ...]
    limitations: tuple[str, ...] = LIMITATIONS


class InvalidContentError(RuntimeError):
    pass


def _predictions(fps: FingerprintSet, model: str | None) -> dict[str, Signature]:
    program = fps.reference if model is None else fps.models[model]
    out: dict[str, Signature] = {}
    for key, test in program.tests.items():
        if test.signature is None:
            raise InvalidContentError(f"non-deterministic fingerprint {program.label}/{key}")
        out[key] = test.signature
    return out


async def _case(
    sandbox: SandboxBackend,
    problem: LoadedProblem,
    case: HeldoutCase,
    fps: FingerprintSet,
    methods: Sequence[DiagnosticMethod],
    runs: int,
) -> list[CaseResult]:
    """One result per method. Every method diagnoses the *same* collected evidence."""
    reference = _predictions(fps, None)
    models = {k: _predictions(fps, k) for k in fps.models}
    outcomes: list[list[Outcome]] = [[] for _ in methods]
    selected: list[list[str | None]] = [[] for _ in methods]
    candidates: list[tuple[str, ...]] = [() for _ in methods]
    signatures = []
    for _ in range(runs):
        evidence = await collect_evidence(sandbox, problem, case.source, reference)
        observations = evidence.observations()
        data = DiagnosticInput(
            problem_version=problem.version,
            compiled=evidence.ok,
            observations=tuple(observations),
            reference=reference,
            models=models,
        )
        signatures.append(tuple(str(o.signature) for o in observations))
        for i, method in enumerate(methods):
            diagnosis = method.diagnose(data)
            outcomes[i].append(diagnosis.outcome)
            selected[i].append(diagnosis.selected_model)
            candidates[i] = candidates[i] or diagnosis.candidates
    return [
        CaseResult(
            problem=case.problem,
            file=case.file,
            truth=case.truth,
            outcomes=tuple(outcomes[i]),
            selected_models=tuple(selected[i]),
            candidates=candidates[i],
            signatures=tuple(signatures),
        )
        for i in range(len(methods))
    ]


async def evaluate(
    sandbox: SandboxBackend,
    catalogue: Catalogue,
    cases: list[HeldoutCase],
    method: DiagnosticMethod,
    runs: int = 2,
    case_set: str = "heldout",
) -> EvaluationReport:
    (report,) = await evaluate_methods(sandbox, catalogue, cases, [method], runs, case_set)
    return report


async def evaluate_methods(
    sandbox: SandboxBackend,
    catalogue: Catalogue,
    cases: list[HeldoutCase],
    methods: Sequence[DiagnosticMethod],
    runs: int = 2,
    case_set: str = "heldout",
) -> list[EvaluationReport]:
    """One report per method, all computed from the same executions of the same cases."""
    if runs < 1:
        raise ValueError("runs must be >= 1")
    if not methods:
        raise ValueError("at least one method is required")
    environment = await sandbox.environment()
    reports: list[list[ProblemReport]] = [[] for _ in methods]
    all_results: list[list[CaseResult]] = [[] for _ in methods]
    all_models: set[str] = set()
    for slug in sorted({c.problem for c in cases}):
        problem = catalogue.by_slug.get(slug)
        if problem is None:
            raise InvalidContentError(f"held-out cases reference unknown problem {slug!r}")
        model_keys = {m.key for m in problem.spec.error_models}
        problem_cases = [c for c in cases if c.problem == slug]
        unknown = [
            c.file
            for c in problem_cases
            if c.truth not in model_keys and c.truth not in (CORRECT, UNMODELLED)
        ]
        if unknown:
            raise InvalidContentError(f"{slug}: unknown ground truth in {unknown}")
        fps = await fingerprint_problem(sandbox, problem)
        validation = validate_fingerprints(problem.spec, fps)
        if not validation.ok:
            raise InvalidContentError(f"{slug}: content failed validation: {validation.errors}")
        per_case = await asyncio.gather(
            *(_case(sandbox, problem, c, fps, methods, runs) for c in problem_cases)
        )
        all_models |= {f"{slug}:{k}" for k in model_keys}
        for i in range(len(methods)):
            results = [r[i] for r in per_case]
            all_results[i] += results
            reports[i].append(
                ProblemReport(
                    problem=slug,
                    version=problem.version,
                    metrics=compute(results, model_keys),
                    identical_model_pairs=tuple(
                        (p.a, p.b) for p in validation.pairs if not p.distinguishing_tests
                    ),
                    detecting_tests={m.key: len(m.detecting_tests) for m in validation.models},
                    cases=tuple(
                        CaseRow(
                            file=r.file,
                            truth=r.truth,
                            outcome=r.outcome.value,
                            selected_model=r.selected_model,
                            candidates=r.candidates,
                            classification=r.classification,
                            reproducible=r.reproducible,
                        )
                        for r in results
                    ),
                )
            )
    env = {
        "compiler_version": environment.compiler_version,
        "container_runtime": environment.container_runtime,
        "image": environment.image,
        "image_id": environment.image_id,
    }
    out = []
    for i, method in enumerate(methods):
        # Overall metrics: namespace model keys by problem so equal keys do not collide.
        namespaced = [
            r.model_copy(
                update={
                    "truth": r.truth
                    if r.truth in (CORRECT, UNMODELLED)
                    else f"{r.problem}:{r.truth}",
                    "selected_models": tuple(
                        f"{r.problem}:{m}" if m else None for m in r.selected_models
                    ),
                }
            )
            for r in all_results[i]
        ]
        out.append(
            EvaluationReport(
                case_set=case_set,
                method=method.name,
                method_version=method.version,
                runs_per_case=runs,
                environment=env,
                overall=compute(namespaced, all_models),
                problems=tuple(reports[i]),
            )
        )
    return out


def render_markdown(report: EvaluationReport) -> str:
    def metrics_rows(m: Metrics) -> list[str]:
        abst = ", ".join(f"{k}: {v}" for k, v in m.abstentions_by_outcome.items()) or "none"
        return [
            "| Metric | Value |",
            "| --- | --- |",
            f"| Cases (buggy / correct) | {m.cases} ({m.buggy_cases} / {m.correct_cases}) |",
            f"| Coverage (buggy cases diagnosed) | {m.coverage} |",
            f"| Selective accuracy (diagnoses matching truth) | {m.selective_accuracy} |",
            f"| False-positive diagnoses | {m.false_positive_diagnoses} |",
            f"| False negatives (modelled bugs not diagnosed) | {m.false_negatives} |",
            f"| Correct code with no failure observed | {m.correct_code_passed} |",
            f"| Abstentions on buggy cases, by outcome | {abst} |",
            f"| Reproducible across {report.runs_per_case} runs | {m.reproducibility} |",
        ]

    env = report.environment
    lines = [
        "# CodeAdapt synthetic evaluation report",
        "",
        f"Method `{report.method}` v{report.method_version}; case set "
        f"`{report.case_set}`; data class `{report.data_class}`; "
        f"each case run {report.runs_per_case} times; "
        f"{env['compiler_version']} on `{env['container_runtime']}`.",
        "",
        "## Overall",
        "",
        *metrics_rows(report.overall),
        "",
    ]
    for p in report.problems:
        pairs = ", ".join(f"{a}/{b}" for a, b in p.identical_model_pairs) or "none"
        lines += [
            f"## {p.problem} (content {p.version[:12]})",
            "",
            *metrics_rows(p.metrics),
            "",
            f"Error-model pairs the suite cannot separate: {pairs}.",
            "",
            "| Case | Truth | Outcome | Selected model | Result | Reproducible |",
            "| --- | --- | --- | --- | --- | --- |",
            *(
                f"| {c.file} | {c.truth} | {c.outcome} | {c.selected_model or '—'} | "
                f"{c.classification} | {'yes' if c.reproducible else 'no'} |"
                for c in p.cases
            ),
            "",
        ]
    lines += ["## Limitations", "", *(f"* {text}" for text in report.limitations), ""]
    return "\n".join(lines)
