"""Write the PC1 synthetic fixtures (all invented; nothing comes from CodeNet).

    python make_fixtures.py [TARGET]   # default: ../fixtures/synthetic-basic

Problem ids p99001-p99004, user ids u9000*, submission ids s9000* are outside anything the
pc1 tests compare with real data. The output is byte-identical on every run; the unit test
regenerates it and compares it with the committed copy. Expected counts are in
EXPECTED below and in ../fixtures/README.md.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TARGET = HERE.parent / "fixtures" / "synthetic-basic"
MARKER = "SYNTHETIC-FIXTURE-NOT-REAL-DATA"
BASE = 1_600_000_000
DAY = 24 * 3600
COLUMNS = [
    "submission_id",
    "problem_id",
    "user_id",
    "date",
    "language",
    "original_language",
    "filename_ext",
    "status",
    "cpu_time",
    "memory",
    "code_size",
    "accuracy",
]

PROBLEMS = [
    ["p99001", "Binary Search", "AIZU", "1000", "131072", "0", "", ""],
    ["p99002", "Allocation", "AIZU", "1000", "131072", "0", "", ""],
    ["p99003", "Binary Search", "AtCoder", "2000", "1048576", "0", "", ""],
    ["p99004", "Exhaustive Search", "AIZU", "5000", "131072", "0", "", ""],
]
DESCRIPTIONS = {
    "p99001": (
        "<h1>SYNTHETIC FIXTURE: Binary Search</h1><p>A sequence of n integers S is given, "
        "sorted in ascending order, and q integers T. Print the number of integers in T "
        "that also appear in S.</p>"
    ),
    "p99002": (
        "<h1>SYNTHETIC FIXTURE: Allocation</h1><p>Load the packages onto k trucks. Each "
        "truck takes consecutive packages up to the maximum load P. Print the minimum P.</p>"
    ),
    "p99003": "<h1>SYNTHETIC FIXTURE: AtCoder search</h1><p>Not an AIZU problem.</p>",
    "p99004": (
        "<h1>SYNTHETIC FIXTURE: Exhaustive Search</h1><p>A sequence of n integers is given.</p>"
    ),
}

_sid = 900000000


def sub(
    user: str,
    offset: int,
    status: str,
    *,
    language: str = "C++",
    original: str = "C++14",
    problem: str = "p99001",
    sid: str | None = None,
    user_id: str | None = None,
    date: str | None = None,
) -> list[str]:
    global _sid
    if sid is None:
        _sid += 1
        sid = f"s{_sid}"
    ext = "cpp" if language == "C++" else "java"
    return [
        sid,
        problem,
        f"u{user}" if user_id is None else user_id,
        str(BASE + offset) if date is None else date,
        language,
        original,
        ext,
        status,
        "10",
        "1024",
        "500",
        "",
    ]


def binary_search_rows() -> list[list[str]]:
    rows = []
    # Edge users (protocol section 6 rules each exercise).
    rows += [
        sub("900000001", 1000, "Wrong Answer"),
        sub("900000001", 1100, "Wrong Answer"),
        sub("900000001", 1200, "Accepted"),
    ]
    rows.append(list(rows[0]))  # exact duplicate row
    rows.append(sub("900000003", 1000, "Wrong Answer"))  # never accepted
    rows += [
        sub("900000004", 1000, "Time Limit Exceeded"),
        sub("900000004", 1100, "Accepted"),
        sub("900000004", 1200, "Wrong Answer"),
    ]  # rejected after first accept
    rows += [
        sub("900000005", 1000, "Runtime Error"),
        sub("900000005", 1100, "Wrong Answer"),
        sub("900000005", 1100, "Accepted"),
    ]  # same-second tie
    rows += [sub("900000006", 1000, "Compile Error"), sub("900000006", 1100, "Accepted")]
    rows += [sub("900000007", 1000, "WA: Presentation Error"), sub("900000007", 1100, "Accepted")]
    rows += [
        sub("900000008", 1000, "Wrong Answer", language="Java", original="JAVA"),
        sub("900000008", 1100, "Accepted", language="Java", original="JAVA"),
    ]
    rows += [
        sub("900000009", 1000, "Wrong Answer"),
        sub("900000009", 1000 + 31 * DAY, "Accepted", original="C++17"),
    ]
    rows += [sub("900000010", 1000, "Judge Not Available"), sub("900000010", 1100, "Accepted")]
    conflict = sub("900000011", 1000, "Wrong Answer")
    rows += [conflict, [*conflict[:7], "Accepted", *conflict[8:]]]  # conflicting duplicate
    rows.append(sub("900000012", 1000, "Wrong Answer", user_id=""))  # missing user_id
    rows.append(sub("900000013", 1000, "Wrong Answer", date="yesterday"))  # bad date
    rows.append(sub("900000014", 1000, "Wrong Answer", problem="p99002"))  # wrong problem
    # Fillers: 100 users who fail then pass, 100 who pass first time.
    for i in range(100):
        user = f"9000010{i:02d}"
        rows += [
            sub(user, 1_000_000 + i * 100, "Wrong Answer"),
            sub(user, 1_000_000 + i * 100 + 60, "Accepted"),
        ]
    for i in range(100):
        rows.append(sub(f"9000020{i:02d}", 2_000_000 + i * 100, "Accepted"))
    return rows


def allocation_rows() -> list[list[str]]:
    rows = []
    for i in range(5):
        user = f"9000030{i:02d}"
        rows += [
            sub(user, 3_000_000 + i * 100, "Wrong Answer", problem="p99002"),
            sub(user, 3_000_000 + i * 100 + 60, "Accepted", problem="p99002"),
        ]
    return rows


EXPECTED = {
    "rows_read": 326,
    "malformed": {"bad_date": 1, "missing_user_id": 1, "problem_id_mismatch": 1},
    "exact_duplicates_dropped": 1,
    "conflicting_duplicate_rows_excluded": 2,
    "unique_submissions": 320,
    "by_language": {"C++": 318, "Java": 2},
    "cpp_by_class": {
        "accepted": 207,
        "eligible_rejected": 108,
        "presentation_error": 1,
        "compile_error": 1,
        "judge_infrastructure": 1,
        "unknown_status": 0,
    },
    "eligible_rejected_by_timing": {
        "before_first_accept": 105,
        "same_second_as_first_accept": 1,
        "after_first_accept": 1,
        "never_accepted": 1,
    },
    "cpp_users": 208,
    "users_with_accept": 207,
    "primary_pairs": 104,
    "secondary_pairs": 105,
    "primary_pairs_by_rejected_status": {
        "Runtime Error": 1,
        "Time Limit Exceeded": 1,
        "Wrong Answer": 102,
    },
    "pairs_with_gap_over_30_days": 1,
    "pairs_with_language_version_change": 1,
}

IDENTIFICATION_CONFIRMED = {
    "ALDS1_4_B": "p99001",
    "ALDS1_4_D": "p99002",
}


def to_csv(header: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def files() -> dict[str, str]:
    global _sid
    _sid = 900000000
    meta = "Project_CodeNet/metadata"
    out = {
        MARKER: "Every file in this directory is invented for tests. None of it is CodeNet data.\n",
        f"{meta}/problem_list.csv": to_csv(
            ["id", "name", "dataset", "time_limit", "memory_limit", "rating", "tags", "complexity"],
            PROBLEMS,
        ),
        f"{meta}/p99001.csv": to_csv(COLUMNS, binary_search_rows()),
        f"{meta}/p99002.csv": to_csv(COLUMNS, allocation_rows()),
        "expected.json": json.dumps(EXPECTED, indent=2, sort_keys=True) + "\n",
    }
    for problem, text in DESCRIPTIONS.items():
        out[f"Project_CodeNet/problem_descriptions/{problem}.html"] = text + "\n"
    return out


def write(target: Path) -> None:
    for name, text in files().items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    write(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET)
