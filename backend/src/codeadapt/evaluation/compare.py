"""Side-by-side comparison of diagnostic methods run on the same evidence. Pure.

Every number is a raw count over the cases given. Nothing here estimates accuracy on real
students' code: the cases are synthetic and written by the error models' author.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from codeadapt.evaluation.runner import CaseRow, EvaluationReport

# Error models the owner's review singled out (lower-bound E2 and E5); E2's key is shared
# by all three demo problems.
FOCUS_MODELS = ("hi_init_last_index", "stops_at_first_match")


class MethodCounts(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: str
    cases: int
    buggy_cases: int
    correct_diagnoses: int  # buggy case diagnosed with its true model
    incorrect_diagnoses: int  # buggy case diagnosed with another model
    false_alarms: int  # correct program not reported as no-failure-observed
    false_positive_diagnoses: int  # any diagnosis naming a model other than the truth
    abstentions: int  # buggy cases not diagnosed
    abstentions_by_outcome: dict[str, int]
    coverage: str  # diagnosed buggy cases / buggy cases


class CaseChange(BaseModel):
    model_config = ConfigDict(frozen=True)

    problem: str
    file: str
    truth: str
    outcomes: tuple[str, ...]  # "outcome (model)" per method
    classifications: tuple[str, ...]


class Comparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_set: str
    methods: tuple[str, ...]
    counts: tuple[MethodCounts, ...]
    focus: dict[str, tuple[CaseChange, ...]]  # model key -> cases whose truth or pick is it
    changed: tuple[CaseChange, ...]


def _rows(report: EvaluationReport) -> list[tuple[str, CaseRow]]:
    return [(p.problem, c) for p in report.problems for c in p.cases]


def _label(c: CaseRow) -> str:
    return f"{c.outcome} ({c.selected_model})" if c.selected_model else c.outcome


def _counts(report: EvaluationReport) -> MethodCounts:
    rows = [c for _, c in _rows(report)]
    buggy = [c for c in rows if c.truth != "correct"]
    diagnosed = [c for c in buggy if c.outcome == "hypothesis_supported"]
    abstained = [c for c in buggy if c.outcome != "hypothesis_supported"]
    return MethodCounts(
        method=f"{report.method} v{report.method_version}",
        cases=len(rows),
        buggy_cases=len(buggy),
        correct_diagnoses=sum(c.classification == "true_diagnosis" for c in rows),
        incorrect_diagnoses=sum(c.classification == "false_diagnosis" for c in rows),
        false_alarms=sum(c.classification == "false_alarm" for c in rows),
        false_positive_diagnoses=sum(
            c.outcome == "hypothesis_supported" and c.selected_model != c.truth for c in rows
        ),
        abstentions=len(abstained),
        abstentions_by_outcome=dict(sorted(Counter(c.outcome for c in abstained).items())),
        coverage=f"{len(diagnosed)}/{len(buggy)}",
    )


def compare(reports: Sequence[EvaluationReport]) -> Comparison:
    if len(reports) < 2:
        raise ValueError("a comparison needs at least two reports")
    keyed = [{(p, c.file): (p, c) for p, c in _rows(r)} for r in reports]
    if any(k.keys() != keyed[0].keys() for k in keyed):
        raise ValueError("reports must cover the same cases")
    if len({r.case_set for r in reports}) != 1:
        raise ValueError("reports must come from the same case set")

    def change(key: tuple[str, str]) -> CaseChange:
        rows = [k[key][1] for k in keyed]
        return CaseChange(
            problem=key[0],
            file=key[1],
            truth=rows[0].truth,
            outcomes=tuple(_label(c) for c in rows),
            classifications=tuple(c.classification for c in rows),
        )

    keys = sorted(keyed[0])
    changed = [
        change(k)
        for k in keys
        if len({(k_[k][1].outcome, k_[k][1].selected_model) for k_ in keyed}) > 1
    ]
    focus = {
        model: tuple(
            change(k)
            for k in keys
            if any(k_[k][1].truth == model or k_[k][1].selected_model == model for k_ in keyed)
        )
        for model in FOCUS_MODELS
    }
    return Comparison(
        case_set=reports[0].case_set,
        methods=tuple(f"{r.method} v{r.method_version}" for r in reports),
        counts=tuple(_counts(r) for r in reports),
        focus=focus,
        changed=tuple(changed),
    )


def render_comparison(comparison: Comparison) -> str:
    m = comparison.methods
    head = "| | " + " | ".join(f"`{x}`" for x in m) + " |"
    rule = "| --- |" + " --- |" * len(m)

    def row(label: str, values: Sequence[object]) -> str:
        return f"| {label} | " + " | ".join(str(v) for v in values) + " |"

    c = comparison.counts
    lines = [
        f"# Method comparison ({comparison.case_set} cases)",
        "",
        "All methods diagnosed the same collected evidence for each case. Raw counts; the "
        "cases are synthetic and written by the error models' author, so this is not an "
        "accuracy estimate for real students.",
        "",
        head,
        rule,
        row("Cases", [x.cases for x in c]),
        row("Buggy cases", [x.buggy_cases for x in c]),
        row("Coverage (diagnosed buggy cases)", [x.coverage for x in c]),
        row("Correct diagnoses", [x.correct_diagnoses for x in c]),
        row("Incorrect diagnoses (buggy case, wrong model)", [x.incorrect_diagnoses for x in c]),
        row("False alarms on correct programs", [x.false_alarms for x in c]),
        row(
            "False-positive diagnoses (model is not the truth)",
            [x.false_positive_diagnoses for x in c],
        ),
        row("Abstentions on buggy cases", [x.abstentions for x in c]),
        row(
            "Abstentions by outcome",
            [
                ", ".join(f"{k} {v}" for k, v in x.abstentions_by_outcome.items()) or "none"
                for x in c
            ],
        ),
        "",
    ]

    def table(items: Sequence[CaseChange]) -> list[str]:
        if not items:
            return ["None."]
        out = [
            "| Problem | Case | Truth | " + " | ".join(f"`{x}`" for x in m) + " |",
            "| --- | --- | --- |" + " --- |" * len(m),
        ]
        for ch in items:
            cells = [f"{o} → {k}" for o, k in zip(ch.outcomes, ch.classifications, strict=True)]
            out.append(f"| {ch.problem} | {ch.file} | {ch.truth} | " + " | ".join(cells) + " |")
        return out

    for model, items in comparison.focus.items():
        lines += [
            f"## Cases involving `{model}` (as truth or as diagnosis)",
            "",
            *table(items),
            "",
        ]
    lines += ["## Cases whose outcome differs between methods", "", *table(comparison.changed), ""]
    return "\n".join(lines)
