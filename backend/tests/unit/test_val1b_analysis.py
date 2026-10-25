"""The VAL1-B pre-registered analysis script, on invented dummy data only.

docs/preregistration/val1b/analysis/ is standard-library Python kept outside the package so
it can be frozen with the protocol; these tests run it in CI.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ANALYSIS = Path(__file__).resolve().parents[3] / "docs/preregistration/val1b/analysis"


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"val1b_{name}", ANALYSIS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyse = load("analyse")
dummy = load("dummy")
CATEGORIES = json.loads((ANALYSIS.parent / "forms/categories.json").read_text())


@pytest.mark.parametrize(
    ("scenario", "overall"),
    [
        ("pass", "pass"),
        ("few_named", "below:S4"),
        ("disagree", "below:S0,S1,S2"),
        ("false_alarm", "blocking_defect"),
    ],
)
def test_scenarios(tmp_path: Path, scenario: str, overall: str) -> None:
    dummy.generate(tmp_path, scenario)
    results = analyse.analyse(tmp_path, CATEGORIES, "1.2")
    assert results["versions"]["1.2"]["overall"] == overall
    assert results["primary_method_version"] == "1.2"


def test_unevaluable_precision_is_never_a_pass() -> None:
    adequate = dict.fromkeys(("S0", "S1", "S2", "S4", "S5"), "adequate")
    assert analyse.overall({**adequate, "S3": "adequate"}) == "pass"
    assert analyse.overall({**adequate, "S3": "not_evaluable"}) == (
        "not_established:precision_not_evaluable"
    )
    assert analyse.overall({**adequate, "S3": "inconclusive"}) == "inconclusive"


def test_few_named_diagnoses_mark_precision_not_evaluable(tmp_path: Path) -> None:
    dummy.generate(tmp_path, "few_named")
    p5 = analyse.analyse(tmp_path, CATEGORIES, "1.2")["versions"]["1.2"]["P5_agreed_precision"]
    assert p5["n"] < analyse.MIN_PRECISION_N
    assert not p5["evaluable"]


def test_statistics() -> None:
    lo, hi = analyse.wilson(12, 12)
    assert round(lo, 3) == 0.757 and hi == 1.0
    # Two raters, 4 items, one disagreement: po = 0.75, pe = 0.5.
    assert analyse.kappa([("a", "a"), ("b", "b"), ("a", "b"), ("b", "b")]) == pytest.approx(0.5)
    pairs = [("a", "a")] * 30 + [("b", "b")] * 30 + [("a", "b")] * 5
    assert analyse.kappa_ci(pairs) == analyse.kappa_ci(pairs)  # fixed seed


def test_three_way_kappa_decision() -> None:
    assert analyse.decide_kappa(0.7, (0.55, 0.85)) == "adequate"
    assert analyse.decide_kappa(0.4, (0.25, 0.55)) == "below"
    assert analyse.decide_kappa(0.6, (0.35, 0.8)) == "inconclusive"
