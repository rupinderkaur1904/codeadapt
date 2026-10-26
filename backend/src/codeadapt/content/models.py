"""Problem definitions: the authored side of a diagnostic problem.

The on-disk format (``problem.toml`` + C++ files) is documented in docs/content-format.md.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from codeadapt.content.taxonomy import skill_problems

_KEY = r"^[a-z][a-z0-9_]{0,63}$"
_SLUG = r"^[a-z][a-z0-9-]{0,63}$"
# A library function a statement forbids, as the statement names it (D1).
_BANNED = r"^(std::(ranges::)?)?[A-Za-z_][A-Za-z0-9_]{0,63}$"
_REL_FILE = re.compile(r"^(?!.*\.\.)[A-Za-z0-9_][A-Za-z0-9_./-]{0,127}$")


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Visibility(StrEnum):
    SAMPLE = "sample"  # input and expected output may be shown to students
    HIDDEN = "hidden"  # only `student_description` may be shown


class TestCase(_Strict):
    __test__ = False  # not a pytest class

    key: str = Field(pattern=_KEY)
    input: str
    expected: str  # author's expected stdout; checked against the executed reference
    probes: tuple[str, ...] = Field(min_length=1)
    visibility: Visibility = Visibility.HIDDEN
    student_description: str = Field(min_length=1)
    # Design record (docs/content-design): why the test exists, and the error models it is
    # meant to separate from the reference. Validation checks `distinguishes` against the
    # measured fingerprints, so the declaration cannot drift from reality.
    purpose: str | None = None
    distinguishes: tuple[str, ...] | None = None


class ErrorModelSpec(_Strict):
    key: str = Field(pattern=_KEY)
    file: str
    skill: str
    description: str = Field(min_length=1)  # researcher-facing
    student_hint: str = Field(min_length=1)  # shown only after a supported diagnosis
    # A documented, accepted weakness (e.g. "evidence rests on one behaviour"). Turns the
    # corresponding validation warning into a recorded limitation.
    known_limitation: str | None = None


class Curriculum(_Strict):
    """Links to other problems by slug (docs/content-design §1.6)."""

    assumes: tuple[str, ...] = ()  # prerequisite knowledge, in words
    prerequisites: tuple[str, ...] = ()
    equivalents: tuple[str, ...] = ()
    transfer: tuple[str, ...] = ()


class ProblemSpec(_Strict):
    slug: str = Field(pattern=_SLUG)
    title: str = Field(min_length=1)
    family: str = Field(pattern=_SLUG)
    statement: str
    harness: str
    reference: str
    solution_file: str = Field(pattern=r"^[A-Za-z0-9_]{1,64}\.cpp$")
    interface: str
    skills: dict[str, str] = Field(min_length=1)
    probes: dict[str, tuple[str, ...]] = Field(min_length=1)
    tests: tuple[TestCase, ...] = Field(min_length=1)
    error_models: tuple[ErrorModelSpec, ...] = ()
    curriculum: Curriculum = Curriculum()
    # Whether recommendation policy v1 may choose this problem as a follow-up (CE1 decision
    # E2). A non-recommendable problem stays in the problem list, and its attempts still
    # produce skill evidence; only the policy's candidate set leaves it out.
    recommendable: bool = True
    # Library calls the statement forbids (D1, technique-evidence eligibility). An attempt whose
    # source names one of them gives no skill observations. The list must match the
    # statement's "Do not call ..." sentence (checked by the loader). Detection is a token
    # match; it does not show which algorithm was used, nor its complexity.
    banned_names: tuple[str, ...] = ()
    # Declared skills that no error model can give negative evidence for: no model maps to
    # them, or every model that does carries a `known_limitation`. Rule C can then only ever
    # give them `correct` observations, so each needs a written reason here (ADR-034).
    positive_only_skills: dict[str, str] = {}

    @model_validator(mode="after")
    def _cross_references(self) -> Self:
        problems: list[str] = []
        for name in (
            self.statement,
            self.harness,
            self.reference,
            *(m.file for m in self.error_models),
        ):
            if not _REL_FILE.fullmatch(name):
                problems.append(f"unsafe or invalid relative path {name!r}")
        for key, definition in self.skills.items():
            if not re.fullmatch(_KEY, key):
                problems.append(f"invalid skill key {key!r}")
            problems += skill_problems(key, definition)
        for probe, skills in self.probes.items():
            if not re.fullmatch(_KEY, probe):
                problems.append(f"invalid probe key {probe!r}")
            problems += [
                f"probe {probe!r}: unknown skill {s!r}" for s in skills if s not in self.skills
            ]
        test_keys = [t.key for t in self.tests]
        problems += [
            f"duplicate test key {k!r}" for k in sorted(set(test_keys)) if test_keys.count(k) > 1
        ]
        model_keys = [m.key for m in self.error_models]
        for test in self.tests:
            problems += [
                f"test {test.key!r}: unknown probe {p!r}"
                for p in test.probes
                if p not in self.probes
            ]
            problems += [
                f"test {test.key!r}: distinguishes unknown error model {m!r}"
                for m in test.distinguishes or ()
                if m not in model_keys
            ]
        problems += [
            f"duplicate error model key {k!r}"
            for k in sorted(set(model_keys))
            if model_keys.count(k) > 1
        ]
        for model in self.error_models:
            if model.skill not in self.skills:
                problems.append(f"error model {model.key!r}: unknown skill {model.skill!r}")
        for skill in self.skills:
            models = [m for m in self.error_models if m.skill == skill]
            positive_only = all(m.known_limitation for m in models)  # also when there are none
            if positive_only and not self.positive_only_skills.get(skill, "").strip():
                problems.append(
                    f"skill {skill!r}: no error model can give negative evidence for it "
                    "(none maps to it, or all carry a known_limitation); add a model or a "
                    "reason under positive_only_skills"
                )
            if not positive_only and skill in self.positive_only_skills:
                problems.append(
                    f"positive_only_skills: {skill!r} has a model that gives negative evidence"
                )
        problems += [
            f"positive_only_skills: undeclared skill {k!r}"
            for k in self.positive_only_skills
            if k not in self.skills
        ]
        for name in self.banned_names:
            if not re.fullmatch(_BANNED, name):
                problems.append(f"invalid banned name {name!r}")
        problems += [
            f"duplicate banned name {n!r}"
            for n in sorted(set(self.banned_names))
            if self.banned_names.count(n) > 1
        ]
        c = self.curriculum
        for slug in (*c.prerequisites, *c.equivalents, *c.transfer):
            if not re.fullmatch(_SLUG, slug) or slug == self.slug:
                problems.append(f"curriculum: invalid problem reference {slug!r}")
        if self.solution_file == "harness.cpp":
            problems.append("solution_file must not be named harness.cpp")
        if not any(t.visibility is Visibility.SAMPLE for t in self.tests):
            problems.append("at least one sample test is required")
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def skills_probed_by(self, test: TestCase) -> set[str]:
        return {skill for probe in test.probes for skill in self.probes[probe]}
