"""The PC1 feasibility scripts, on synthetic fixtures only.

docs/preregistration/pc1/scripts/ is standard-library Python kept outside the package so it
is frozen with the protocol. Nothing here touches CodeNet: the fixtures are invented, and the
real-data paths are exercised only to prove that the permission gate stops them.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PC1 = Path(__file__).resolve().parents[3] / "docs/preregistration/pc1"
FIXTURE = PC1 / "fixtures/synthetic-basic"


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"pc1_{name}", PC1 / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look their module up here
    spec.loader.exec_module(module)
    return module


pc1 = load("pc1")
make_fixtures = load("make_fixtures")
EXPECTED = json.loads((FIXTURE / "expected.json").read_text())


def valid_record(**changes: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "record_version": 1,
        "status": "granted",
        "dataset": "IBM Project CodeNet 1.0.0",
        "granted_by_role": "supervisor",
        "basis": "explicit approval",
        "decision_date": "2026-11-01",
        "recorded_on": "2026-11-02",
        "recorded_by": "owner",
        "evidence_reference": "Supervisor email of 2026-11-01, kept in the owner's records",
        "conditions_verbatim": "Research use only; do not redistribute code.",
        "scope": {
            "download_full_archive": True,
            "store_outside_repository": True,
            "metadata_analysis": True,
            "source_code_analysis": False,
            "publish_derived_statistics": True,
            "publish_submission_ids": False,
            "redistribute_code": False,
        },
    }
    record.update(changes)
    return record


def write_record(tmp_path: Path, record: dict[str, Any]) -> Path:
    path = tmp_path / "record.json"
    path.write_text(json.dumps(record))
    return path


def confirmed(root: Path, *, synthetic: bool = True, **ids: str) -> dict[str, Any]:
    identification: dict[str, Any] = pc1.identify(root, synthetic=synthetic)
    role = "synthetic-fixture" if synthetic else "owner"
    for candidate, problem in ids.items():
        pc1.confirm(identification, candidate, problem, role)
    return identification


def csv_text(header: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows([header, *rows])
    return buffer.getvalue()


def make_root(tmp_path: Path, problems: list[list[str]], metadata: dict[str, str]) -> Path:
    meta = tmp_path / "Project_CodeNet/metadata"
    meta.mkdir(parents=True)
    (meta / "problem_list.csv").write_text(
        csv_text(
            ["id", "name", "dataset", "time_limit", "memory_limit", "rating", "tags", "complexity"],
            problems,
        )
    )
    for problem, text in metadata.items():
        (meta / f"{problem}.csv").write_text(text)
    return tmp_path


def submissions(rows: list[tuple[str, str, int, str]], problem: str = "p99001") -> str:
    return csv_text(
        make_fixtures.COLUMNS,
        [
            [sid, problem, user, str(date), "C++", "C++14", "cpp", status, "", "", "", ""]
            for sid, user, date, status in rows
        ],
    )


# ------------------------------------------------------------------ permission gate
def test_gate_closed_without_a_record(tmp_path: Path) -> None:
    assert pc1.check_permission(tmp_path / "absent.json") == [
        f"no permission record at {tmp_path / 'absent.json'}"
    ]
    assert pc1.main(["gate", "--permission", str(tmp_path / "absent.json")]) == pc1.EXIT_GATE


def test_committed_template_does_not_open_the_gate() -> None:
    problems = pc1.check_permission(PC1 / "permission/record.template.json")
    assert any("status must be 'granted'" in p for p in problems)


def test_gate_opens_only_for_a_complete_explicit_approval(tmp_path: Path) -> None:
    assert pc1.check_permission(write_record(tmp_path, valid_record())) == []
    assert pc1.main(["gate", "--permission", str(tmp_path / "record.json")]) == pc1.EXIT_OK


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"basis": "repository licence"}, "a repository licence"),
        ({"basis": "third-party description"}, "a repository licence"),
        ({"status": "TEMPLATE"}, "status must be 'granted'"),
        ({"granted_by_role": "Claude"}, "granted_by_role"),
        ({"recorded_by": "Claude"}, "recorded_by"),
        ({"evidence_reference": "jane@example.edu said yes"}, "email address"),
        ({"evidence_reference": ""}, "evidence_reference"),
        ({"conditions_verbatim": " "}, "conditions_verbatim"),
        ({"decision_date": "2026-11-03"}, "after recorded_on"),
        ({"decision_date": "soon"}, "ISO dates"),
        ({"dataset": "CodeNet"}, "dataset"),
    ],
)
def test_gate_refuses_incomplete_or_indirect_permission(
    tmp_path: Path, change: dict[str, Any], reason: str
) -> None:
    problems = pc1.check_permission(write_record(tmp_path, valid_record(**change)))
    assert any(reason in p for p in problems), problems


def test_gate_scope_is_checked_per_level(tmp_path: Path) -> None:
    path = write_record(tmp_path, valid_record())
    assert pc1.check_permission(path, "metadata") == []
    assert pc1.check_permission(path, "code") == [
        "scope.source_code_analysis must be true for level 'code'"
    ]
    scope = {**valid_record()["scope"], "redistribute_code": True}
    assert any(
        "redistribute_code" in p
        for p in pc1.check_permission(write_record(tmp_path, valid_record(scope=scope)))
    )


def test_real_data_commands_stop_before_reading_anything(tmp_path: Path) -> None:
    data, out = tmp_path / "data", tmp_path / "out"
    absent = str(tmp_path / "absent.json")
    for argv in (
        ["identify", "--data-dir", str(data), "--out", str(out)],
        ["feasibility", "--data-dir", str(data), "--identification", "x.json", "--out", str(out)],
        ["extract", "--archive", str(tmp_path / "missing.tar.gz"), "--data-dir", str(data)],
    ):
        assert pc1.main([*argv, "--permission", absent]) == pc1.EXIT_GATE
    assert not out.exists()
    assert not data.exists()


def test_fixtures_and_real_data_cannot_be_mixed(tmp_path: Path) -> None:
    record = str(write_record(tmp_path, valid_record()))
    out = str(tmp_path / "out")
    # A fixture directory is refused in real mode, even with permission.
    assert (
        pc1.main(["identify", "--data-dir", str(FIXTURE), "--out", out, "--permission", record])
        == pc1.EXIT_GATE
    )
    # Real data inside the repository is refused.
    inside = PC1 / "scripts"
    assert (
        pc1.main(["identify", "--data-dir", str(inside), "--out", out, "--permission", record])
        == pc1.EXIT_GATE
    )
    # Real-data outputs inside the repository are refused.
    assert (
        pc1.main(
            [
                "identify",
                "--data-dir",
                str(tmp_path),
                "--out",
                str(PC1 / "out"),
                "--permission",
                record,
            ]
        )
        == pc1.EXIT_GATE
    )
    # --synthetic-fixtures is refused outside the fixtures directory.
    (tmp_path / pc1.FIXTURE_MARKER).write_text("fake")
    assert (
        pc1.main(["identify", "--data-dir", str(tmp_path), "--out", out, "--synthetic-fixtures"])
        == pc1.EXIT_GATE
    )
    assert not (tmp_path / "out").exists()


# ------------------------------------------------------------------ fixtures
def test_fixtures_are_regenerated_byte_for_byte(tmp_path: Path) -> None:
    make_fixtures.write(tmp_path)
    generated = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file())
    committed = sorted(p.relative_to(FIXTURE) for p in FIXTURE.rglob("*") if p.is_file())
    assert generated == committed
    for name in generated:
        assert (tmp_path / name).read_bytes() == (FIXTURE / name).read_bytes(), name
    assert (FIXTURE / pc1.FIXTURE_MARKER).is_file()


# ------------------------------------------------------------------ identification
def test_identify_shortlists_aizu_candidates_only() -> None:
    result = pc1.identify(FIXTURE, synthetic=True)
    assert result["source"] == "synthetic"
    b, d = result["candidates"]["ALDS1_4_B"], result["candidates"]["ALDS1_4_D"]
    assert (b["status"], [s["problem_id"] for s in b["shortlist"]]) == ("single_match", ["p99001"])
    assert (d["status"], [s["problem_id"] for s in d["shortlist"]]) == ("single_match", ["p99002"])
    # Nothing is confirmed automatically.
    assert b["confirmed_problem_id"] is None
    assert d["confirmed_problem_id"] is None


def test_identify_reports_absent_and_ambiguous_without_substituting(tmp_path: Path) -> None:
    root = make_root(
        tmp_path,
        [
            ["p00001", "Binary Search", "AIZU", "1", "1", "0", "", ""],
            ["p00002", "Binary Search", "AIZU", "1", "1", "0", "", ""],
            ["p00003", "Allocation", "AtCoder", "1", "1", "0", "", ""],
        ],
        {},
    )
    result = pc1.identify(root)
    assert result["candidates"]["ALDS1_4_B"]["status"] == "ambiguous"
    assert result["candidates"]["ALDS1_4_D"]["status"] == "not_present"
    assert result["candidates"]["ALDS1_4_D"]["shortlist"] == []


def test_confirmation_rules() -> None:
    identification = pc1.identify(FIXTURE, synthetic=True)
    with pytest.raises(pc1.StopConditionError, match="not on ALDS1_4_B's shortlist"):
        pc1.confirm(identification, "ALDS1_4_B", "p99003", "synthetic-fixture")
    with pytest.raises(pc1.StopConditionError, match="cannot confirm synthetic data"):
        pc1.confirm(identification, "ALDS1_4_B", "p99001", "owner")
    real = pc1.identify(FIXTURE, synthetic=False)
    with pytest.raises(pc1.StopConditionError, match="cannot confirm real data"):
        pc1.confirm(real, "ALDS1_4_B", "p99001", "synthetic-fixture")


def test_feasibility_refuses_unconfirmed_or_mismatched_identification() -> None:
    real = confirmed(FIXTURE, synthetic=False, ALDS1_4_B="p99001")
    with pytest.raises(pc1.StopConditionError, match="not 'synthetic'"):
        pc1.feasibility(FIXTURE, real, synthetic=True)
    report = pc1.feasibility(FIXTURE, pc1.identify(FIXTURE, synthetic=True), synthetic=True)
    assert not any(e["evaluated"] for e in report["candidates"].values())
    assert report["recommendation"].startswith("no candidate reached the minimum")


# ------------------------------------------------------------------ counting and pairing
def test_fixture_counts_match_the_hand_computed_expectation() -> None:
    report = pc1.feasibility(FIXTURE, confirmed(FIXTURE, ALDS1_4_B="p99001"), synthetic=True)
    entry = report["candidates"]["ALDS1_4_B"]
    flat = {**entry["rows"], **entry["pairing"]}
    assert {k: flat[k] for k in EXPECTED} == EXPECTED
    assert entry["reconciliation_failures"] == []
    assert entry["stops"] == []
    assert entry["band"] == "feasible"
    # The fallback is not counted when the first choice is feasible.
    assert report["candidates"]["ALDS1_4_D"] == {"status": "not_needed", "evaluated": False}


def test_pairing_rules_on_edge_users() -> None:
    subs, _ = pc1.load_submissions(FIXTURE / "Project_CodeNet/metadata/p99001.csv", "p99001")
    pairs = {p["user_id"]: p for p in pc1.pair(subs)[0]}
    # Last eligible rejection before the first accept.
    assert pairs["u900000001"]["rejected_submission_id"] == "s900000002"
    assert pairs["u900000001"]["rejected_before_accept"] == 2
    # A rejection in the same second as the accept is not paired; the earlier one is.
    assert pairs["u900000005"]["rejected_status"] == "Runtime Error"
    # Never accepted, compile error, presentation error, judge error, other language: no pair.
    for user in ("u900000003", "u900000006", "u900000007", "u900000008", "u900000010"):
        assert user not in pairs
    # A conflicting duplicate removes the submission entirely.
    assert "u900000011" not in pairs
    assert pairs["u900000009"]["gap_seconds"] > pc1.LONG_GAP_SECONDS
    assert not pairs["u900000009"]["same_original_language"]


def test_missing_and_extra_cells_are_malformed(tmp_path: Path) -> None:
    text = submissions([("s000000001", "u000000001", 10, "Accepted")])
    text += "s000000002,p99001,u000000002\n"  # short row: missing fields
    text += "s000000003,p99001,u000000003,10,C++,C++14,cpp,Accepted,,,,,EXTRA\n"
    path = tmp_path / "p99001.csv"
    path.write_text(text)
    subs, counts = pc1.load_submissions(path, "p99001")
    assert counts["malformed"] == {"extra_cells": 1, "missing_date": 1}
    assert [s.submission_id for s in subs] == ["s000000001"]


def test_schema_mismatch_stops(tmp_path: Path) -> None:
    path = tmp_path / "p99001.csv"
    path.write_text("submission_id,problem_id\ns000000001,p99001\n")
    with pytest.raises(pc1.StopConditionError, match="S3-schema"):
        pc1.load_submissions(path, "p99001")


def test_unknown_status_share_is_a_stop_condition(tmp_path: Path) -> None:
    rows = [(f"s{i:09d}", f"u{i:09d}", 10, "Accepted") for i in range(1, 20)]
    rows.append(("s000000099", "u000000099", 10, "Mystery Verdict"))
    root = make_root(
        tmp_path,
        [["p99001", "Binary Search", "AIZU", "1", "1", "0", "", ""]],
        {"p99001": submissions(rows)},
    )
    report = pc1.feasibility(root, confirmed(root, synthetic=False, ALDS1_4_B="p99001"))
    entry = report["candidates"]["ALDS1_4_B"]
    assert entry["stops"] == ["S5-unknown-status-over-1%"]
    assert entry["pairing"]["unknown_statuses"] == {"Mystery Verdict": 1}
    assert entry["band"] is None
    assert report["recommendation"].startswith("stop")


def test_fallback_is_counted_only_when_the_first_choice_falls_short(tmp_path: Path) -> None:
    few = submissions(
        [
            ("s000000001", "u000000001", 10, "Wrong Answer"),
            ("s000000002", "u000000001", 20, "Accepted"),
        ]
    )
    many = submissions(
        [(f"s1{i:08d}", f"u1{i:08d}", 10, "Wrong Answer") for i in range(70)]
        + [(f"s2{i:08d}", f"u1{i:08d}", 20, "Accepted") for i in range(70)],
        problem="p99002",
    )
    root = make_root(
        tmp_path,
        [
            ["p99001", "Binary Search", "AIZU", "1", "1", "0", "", ""],
            ["p99002", "Allocation", "AIZU", "1", "1", "0", "", ""],
        ],
        {"p99001": few, "p99002": many},
    )
    report = pc1.feasibility(
        root, confirmed(root, synthetic=False, ALDS1_4_B="p99001", ALDS1_4_D="p99002")
    )
    assert report["candidates"]["ALDS1_4_B"]["band"] == "not_feasible"
    assert report["candidates"]["ALDS1_4_D"]["band"] == "feasible_below_target"
    assert report["recommendation"].startswith("ALDS1_4_D (feasible_below_target)")


def test_reconciliation_detects_a_broken_identity() -> None:
    subs, counts = pc1.load_submissions(FIXTURE / "Project_CodeNet/metadata/p99001.csv", "p99001")
    _, summary = pc1.pair(subs)
    assert pc1.reconcile(counts, summary) == []
    counts["valid_rows"] += 1
    assert pc1.reconcile(counts, summary)[0].startswith("rows_read = malformed + valid")


# ------------------------------------------------------------------ CLI end to end, reruns
def run_fixture_pipeline(out: Path) -> int:
    fixture = ["--data-dir", str(FIXTURE), "--out", str(out), "--synthetic-fixtures"]
    assert pc1.main(["identify", *fixture]) == pc1.EXIT_OK
    ident = str(out / "identification.json")
    argv = ["confirm", "--identification", ident, "--candidate", "ALDS1_4_B"]
    assert pc1.main([*argv, "--problem", "p99001", "--role", "synthetic-fixture"]) == pc1.EXIT_OK
    return int(pc1.main(["feasibility", *fixture, "--identification", ident]))


def test_cli_pipeline_is_deterministic_and_safe_to_rerun(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    assert run_fixture_pipeline(first) == pc1.EXIT_OK
    assert run_fixture_pipeline(second) == pc1.EXIT_OK
    assert run_fixture_pipeline(second) == pc1.EXIT_OK  # rerun over existing outputs
    for name in ("identification.json", "feasibility.json", "feasibility.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name
    assert sorted(p.name for p in second.iterdir()) == [
        "feasibility.json",
        "feasibility.md",
        "identification.json",
    ]


# ------------------------------------------------------------------ extract
def add(tar: tarfile.TarFile, name: str, data: bytes = b"x", kind: bytes = tarfile.REGTYPE) -> None:
    info = tarfile.TarInfo(name)
    info.type = kind
    info.size = len(data) if kind == tarfile.REGTYPE else 0
    if kind == tarfile.SYMTYPE:
        info.linkname = "/etc/passwd"
    tar.addfile(info, io.BytesIO(data) if kind == tarfile.REGTYPE else None)


def test_extract_takes_metadata_and_descriptions_only(tmp_path: Path) -> None:
    archive = tmp_path / "fake.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        add(tar, "Project_CodeNet/metadata/problem_list.csv", b"id\n")
        add(tar, "Project_CodeNet/problem_descriptions/p00001.html", b"<p>x</p>")
        add(tar, "Project_CodeNet/data/p00001/C++/s000000001.cpp", b"int main(){}")
        add(tar, "Project_CodeNet/metadata/../../escape.txt", b"no")
        add(tar, "Project_CodeNet/metadata/link.csv", kind=tarfile.SYMTYPE)
    record = str(write_record(tmp_path, valid_record()))
    data = tmp_path / "data"
    argv = ["extract", "--archive", str(archive), "--data-dir", str(data), "--permission", record]
    assert pc1.main(argv) == pc1.EXIT_OK
    files = sorted(p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file())
    assert files == [
        "Project_CodeNet/metadata/problem_list.csv",
        "Project_CodeNet/problem_descriptions/p00001.html",
    ]
    assert not (tmp_path / "escape.txt").exists()
    counts = pc1.extract(archive, data)  # rerun
    assert {k: v for k, v in counts.items() if not k.startswith("archive_")} == {
        "already_present": 2,
        "refused": 2,
        "skipped": 1,
    }
    assert counts["archive_bytes"] == archive.stat().st_size
    assert counts["archive_sha256"] == pc1.sha256_file(archive)
    # A stream (curl ... | pc1.py extract --archive -) gives the same result in one pass.
    streamed = tmp_path / "streamed"
    with archive.open("rb") as stream:
        assert pc1.extract(stream, streamed)["archive_sha256"] == counts["archive_sha256"]
    assert sorted(p.name for p in streamed.rglob("*") if p.is_file()) == [
        "p00001.html",
        "problem_list.csv",
    ]
