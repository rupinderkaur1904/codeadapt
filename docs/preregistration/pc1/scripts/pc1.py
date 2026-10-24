"""PC1 public-corpus feasibility checks (protocol: ../protocol.md, frozen 1.0).

Standard-library only, kept outside the package so it is frozen with the protocol. It reads
CodeNet *metadata* and *problem descriptions* only: never source code, never the network, and
never runs a diagnosis. Every command that touches real data first passes the permission gate
(protocol section 3). Synthetic fixtures (directory marked SYNTHETIC-FIXTURE-NOT-REAL-DATA)
skip the gate and can never be mixed with real data.

    python pc1.py gate [--permission FILE] [--level metadata|code]
    python pc1.py extract --archive TAR|- --data-dir DIR
    python pc1.py identify --data-dir DIR --out DIR [--synthetic-fixtures]
    python pc1.py confirm --identification FILE --candidate KEY --problem pNNNNN --role ROLE
    python pc1.py feasibility --data-dir DIR --identification FILE --out DIR [--synthetic-fixtures]

Exit codes: 0 ok, 2 usage, 3 permission gate closed, 4 stop condition (report written).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import statistics
import sys
import tarfile
import tempfile
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

PROTOCOL_VERSION = "1.0"
HERE = Path(__file__).resolve().parent
PC1_DIR = HERE.parent
REPO_ROOT = PC1_DIR.parents[2]
DEFAULT_PERMISSION = PC1_DIR / "permission" / "record.json"
FIXTURE_MARKER = "SYNTHETIC-FIXTURE-NOT-REAL-DATA"
FIXTURES_ROOT = PC1_DIR / "fixtures"
CODENET = "Project_CodeNet"
EXTRACT_PREFIXES = (f"{CODENET}/metadata/", f"{CODENET}/problem_descriptions/")

EXIT_OK, EXIT_USAGE, EXIT_GATE, EXIT_STOP = 0, 2, 3, 4

# ------------------------------------------------------------------ frozen definitions
PROBLEM_COLUMNS = frozenset(
    {"id", "name", "dataset", "time_limit", "memory_limit", "rating", "tags", "complexity"}
)
SUBMISSION_COLUMNS = frozenset(
    {
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
    }
)
REQUIRED_FIELDS = ("submission_id", "problem_id", "user_id", "date", "language", "status")
ID_PATTERNS = {
    "submission_id": re.compile(r"s\d{9}"),
    "problem_id": re.compile(r"p\d{5}"),
    "user_id": re.compile(r"u\d{9}"),
}
LANGUAGE = "C++"
ACCEPTED = "Accepted"
ELIGIBLE_REJECTED = frozenset(
    {
        "Wrong Answer",
        "Time Limit Exceeded",
        "Runtime Error",
        "Memory Limit Exceeded",
        "Output Limit Exceeded",
    }
)
PRESENTATION = frozenset({"WA: Presentation Error"})
COMPILE = frozenset({"Compile Error"})
INFRA = frozenset(
    {
        "Judge Not Available",
        "Waiting for Judging",
        "Waiting for Re-judging",
        "Internal Error",
        "Judge System Error",
    }
)
LONG_GAP_SECONDS = 30 * 24 * 3600

# Section 5: candidates, in pre-registered order. Shortlisting is automatic; confirmation is
# a human reading of the shortlisted statement against `task` (identification.json).
CANDIDATES: dict[str, dict[str, Any]] = {
    "ALDS1_4_B": {
        "names": ["binary search"],
        "phrases": ["sorted", "ascending", "sequence of n integers", "q integers", "number of"],
        "task": (
            "Given n integers S in ascending order (n <= 100000) and q distinct integers T "
            "(q <= 50000), print C, the number of integers in T that are also in S."
        ),
    },
    "ALDS1_4_D": {
        "names": ["allocation"],
        "phrases": ["packages", "trucks", "maximum load", "consecutive", "minimum"],
        "task": (
            "Given n package weights in order and k trucks that each carry consecutive "
            "packages up to a common maximum load P, print the minimum P."
        ),
    },
}
MIN_PHRASES = 3

# Section 7: stop conditions and feasibility bands.
MAX_MALFORMED_SHARE = 0.01
MAX_CONFLICT_SHARE = 0.01
MAX_UNKNOWN_STATUS_SHARE = 0.01
PAIRS_TARGET = 100
PAIRS_MINIMUM = 60

# Section 3: the permission gate.
ALLOWED_ROLES = frozenset(
    {
        "supervisor",
        "institutional research-data office",
        "institutional ethics office",
        "dataset owner (IBM)",
    }
)
# Amendment A1: a published dataset licence as a second, metadata-only basis.
EXPLICIT_APPROVAL = "explicit approval"
PUBLISHED_LICENCE = "published dataset licence"
LICENCE_ID = "CDLA-Permissive-2.0"
LICENCE_TEXT = PC1_DIR / "permission/licences/CDLA-Permissive-2.0.txt"
LICENCE_LEVELS = frozenset({"metadata"})
SELF_IMPOSED_CONDITIONS = (
    "aggregate_outputs_only",
    "no_reidentification",
    "no_linkage_with_other_sources",
    "no_source_code_access",
    "no_redistribution",
    "data_outside_repository",
)
REQUIRED_SCOPE = {
    "metadata": ("download_full_archive", "store_outside_repository", "metadata_analysis"),
    "code": (
        "download_full_archive",
        "store_outside_repository",
        "metadata_analysis",
        "source_code_analysis",
    ),
}


class GateClosedError(Exception):
    """The permission prerequisite is not satisfied; nothing was read."""


class StopConditionError(Exception):
    """A pre-registered stop condition fired (protocol section 7)."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# ------------------------------------------------------------------ permission gate
def _iso_date(value: object) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def check_permission(path: Path, level: str = "metadata") -> list[str]:
    """Return the reasons the gate is closed; an empty list means open."""
    if level not in REQUIRED_SCOPE:
        return [f"unknown level {level!r}"]
    if not path.is_file():
        return [f"no permission record at {path}"]
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"permission record is not valid JSON: {exc}"]
    if not isinstance(record, dict):
        return ["permission record must be a JSON object"]
    problems: list[str] = []
    if record.get("status") != "granted":
        problems.append("status must be 'granted' (the template says 'TEMPLATE')")
    if record.get("dataset") != "IBM Project CodeNet 1.0.0":
        problems.append("dataset must be 'IBM Project CodeNet 1.0.0'")
    if record.get("recorded_by") != "owner":
        problems.append("recorded_by must be 'owner' (Claude never writes this record)")
    version, basis = record.get("record_version"), record.get("basis")
    if version == 1 and basis == EXPLICIT_APPROVAL:
        problems.extend(_check_approval(record))
    elif version == 2 and basis == PUBLISHED_LICENCE:
        problems.extend(_check_licence(record, level))
    else:
        problems.append(
            f"basis must be {EXPLICIT_APPROVAL!r} (record_version 1) or {PUBLISHED_LICENCE!r} "
            "(record_version 2, amendment A1); a repository licence or a third-party "
            "description is not permission"
        )
    scope = record.get("scope")
    if not isinstance(scope, dict):
        problems.append("scope must be an object")
    else:
        problems.extend(
            f"scope.{key} must be true for level {level!r}"
            for key in REQUIRED_SCOPE[level]
            if scope.get(key) is not True
        )
        if scope.get("redistribute_code") is not False:
            problems.append("scope.redistribute_code must be false: PC1 never redistributes code")
    return problems


def _check_approval(record: dict[str, Any]) -> list[str]:
    """Record version 1: an explicit approval from one of ALLOWED_ROLES (section 3)."""
    problems: list[str] = []
    if record.get("granted_by_role") not in ALLOWED_ROLES:
        problems.append(f"granted_by_role must be one of {sorted(ALLOWED_ROLES)}")
    decided, recorded = _iso_date(record.get("decision_date")), _iso_date(record.get("recorded_on"))
    if decided is None or recorded is None:
        problems.append("decision_date and recorded_on must be ISO dates (YYYY-MM-DD)")
    elif decided > recorded:
        problems.append("decision_date is after recorded_on")
    reference = record.get("evidence_reference")
    if not isinstance(reference, str) or len(reference.strip()) < 8:
        problems.append("evidence_reference must say where the written approval is kept")
    elif "@" in reference:
        problems.append("evidence_reference must not contain an email address")
    conditions = record.get("conditions_verbatim")
    if not isinstance(conditions, str) or not conditions.strip():
        problems.append("conditions_verbatim must quote the approval's conditions ('none' if none)")
    return problems


def _check_licence(record: dict[str, Any], level: str) -> list[str]:
    """Record version 2 (A1): the dataset provider's published licence, metadata level only."""
    problems: list[str] = []
    if level not in LICENCE_LEVELS:
        problems.append(f"a {PUBLISHED_LICENCE!r} record opens only the metadata level (A1)")
    if record.get("licence_id") != LICENCE_ID:
        problems.append(f"licence_id must be {LICENCE_ID!r}")
    if record.get("licence_text_sha256") != sha256_file(LICENCE_TEXT):
        problems.append(
            "licence_text_sha256 must match permission/licences/CDLA-Permissive-2.0.txt"
        )
    recorded = _iso_date(record.get("recorded_on"))
    if recorded is None:
        problems.append("recorded_on must be an ISO date (YYYY-MM-DD)")
    evidence = record.get("licence_evidence")
    if not isinstance(evidence, list) or not evidence:
        problems.append("licence_evidence must list at least one source")
        evidence = []
    provider_first_hand = False
    for i, item in enumerate(evidence):
        if not isinstance(item, dict):
            problems.append(f"licence_evidence[{i}] must be an object")
            continue
        for key in ("source", "locator", "quote"):
            value = item.get(key)
            if not isinstance(value, str) or len(value.strip()) < 8:
                problems.append(f"licence_evidence[{i}].{key} must be filled in")
        if item.get("publisher") not in ("dataset provider", "third party"):
            problems.append(
                f"licence_evidence[{i}].publisher must be 'dataset provider' or 'third party'"
            )
        if item.get("seen") not in ("first-hand", "secondary"):
            problems.append(f"licence_evidence[{i}].seen must be 'first-hand' or 'secondary'")
        accessed = _iso_date(item.get("accessed_on"))
        if accessed is None or (recorded is not None and accessed > recorded):
            problems.append(
                f"licence_evidence[{i}].accessed_on must be an ISO date, not after recorded_on"
            )
        if "@" in json.dumps(item):
            problems.append(f"licence_evidence[{i}] must not contain an email address")
        quote = item.get("quote")
        if (
            item.get("publisher") == "dataset provider"
            and item.get("seen") == "first-hand"
            and isinstance(quote, str)
            and ("CDLA" in quote or "Community Data License" in quote)
        ):
            provider_first_hand = True
    if not provider_first_hand:
        problems.append(
            "licence_evidence needs a statement by the dataset provider, read first-hand by the "
            "owner, quoting the licence; third-party or secondary sources alone are not enough"
        )
    for key in ("unverified", "known_risks"):
        value = record.get(key)
        if not isinstance(value, str) or len(value.strip()) < 8:
            problems.append(f"{key} must say what was not verified or what remains uncertain")
    conditions = record.get("self_imposed_conditions")
    if not isinstance(conditions, dict):
        problems.append("self_imposed_conditions must be an object")
    else:
        problems.extend(
            f"self_imposed_conditions.{key} must be true"
            for key in SELF_IMPOSED_CONDITIONS
            if conditions.get(key) is not True
        )
    scope = record.get("scope")
    if isinstance(scope, dict):
        for key in ("source_code_analysis", "publish_submission_ids"):
            if scope.get(key) is not False:
                problems.append(
                    f"scope.{key} must be false under a {PUBLISHED_LICENCE!r} record (A1)"
                )
    return problems


def require_gate(path: Path, level: str = "metadata") -> None:
    problems = check_permission(path, level)
    if problems:
        raise GateClosedError("; ".join(problems))


def _inside(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def check_data_dir(data_dir: Path, *, synthetic: bool) -> None:
    """Keep fixtures and real data apart (protocol section 4)."""
    marked = (data_dir / FIXTURE_MARKER).is_file()
    if synthetic:
        if not marked or not _inside(data_dir, FIXTURES_ROOT):
            raise GateClosedError(
                f"--synthetic-fixtures needs a directory under {FIXTURES_ROOT} "
                f"containing {FIXTURE_MARKER}"
            )
        return
    if marked:
        raise GateClosedError(f"{data_dir} is a synthetic fixture; use --synthetic-fixtures")
    if _inside(data_dir, REPO_ROOT):
        raise GateClosedError(f"real data must live outside the repository ({REPO_ROOT})")


# ------------------------------------------------------------------ deterministic output
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_atomic(path: Path, text: str) -> None:
    """Write via a temporary file and rename, so a rerun never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def dump(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


# ------------------------------------------------------------------ extract
class _HashingReader:
    """Pass bytes through to tarfile while hashing them, so a stream needs no copy on disk."""

    def __init__(self, raw: IO[bytes]) -> None:
        self.raw, self.digest, self.size = raw, hashlib.sha256(), 0

    def read(self, n: int = -1) -> bytes:
        data = self.raw.read(n)
        self.digest.update(data)
        self.size += len(data)
        return data

    def drain(self) -> None:
        while self.read(1 << 20):
            pass


def extract(source: Path | IO[bytes], data_dir: Path) -> dict[str, Any]:
    """Extract only metadata/ and problem_descriptions/; never source code.

    `source` is the archive's path or a byte stream (`--archive -`), read once, in order.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter[str]()
    with ExitStack() as stack:
        raw = stack.enter_context(source.open("rb")) if isinstance(source, Path) else source
        reader = _HashingReader(raw)
        tar = stack.enter_context(tarfile.open(fileobj=reader, mode="r|*"))  # type: ignore[call-overload]
        for member in tar:
            name = member.name.removeprefix("./")
            if not name.startswith(EXTRACT_PREFIXES):
                counts["skipped"] += 1
                continue
            if member.isdir():
                counts["directories"] += 1
                continue
            if Path(name).is_absolute() or ".." in Path(name).parts or not member.isfile():
                counts["refused"] += 1
                continue
            target = data_dir / name
            if target.is_file() and target.stat().st_size == member.size:
                counts["already_present"] += 1
                continue
            data = tar.extractfile(member)
            if data is None:
                counts["refused"] += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(f".{target.name}.part")
            with tmp.open("wb") as out:
                while block := data.read(1 << 20):
                    out.write(block)
            os.replace(tmp, target)
            counts["extracted"] += 1
        reader.drain()
    return {
        **dict(sorted(counts.items())),
        "archive_sha256": reader.digest.hexdigest(),
        "archive_bytes": reader.size,
    }


# ------------------------------------------------------------------ identify
def strip_html(text: str) -> str:
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip().lower()


def read_problem_list(root: Path) -> list[dict[str, str]]:
    path = root / CODENET / "metadata" / "problem_list.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = frozenset(reader.fieldnames or ())
        if header != PROBLEM_COLUMNS:
            raise StopConditionError("S3-schema", f"problem_list.csv columns {sorted(header)}")
        return sorted(reader, key=lambda row: row["id"])


def identify(root: Path, *, synthetic: bool = False) -> dict[str, Any]:
    """Shortlist each candidate; never pick or substitute (protocol section 5)."""
    problems = read_problem_list(root)
    descriptions = root / CODENET / "problem_descriptions"
    result: dict[str, Any] = {
        "protocol": PROTOCOL_VERSION,
        "source": "synthetic" if synthetic else "real",
        "candidates": {},
    }
    for key, spec in CANDIDATES.items():
        shortlist = []
        for row in problems:
            if row["dataset"] != "AIZU":
                continue
            name_match = row["name"].strip().lower() in spec["names"]
            page = descriptions / f"{row['id']}.html"
            text = (
                strip_html(page.read_text(encoding="utf-8", errors="replace"))
                if page.is_file()
                else ""
            )
            phrases = sorted(p for p in spec["phrases"] if p in text)
            if name_match or len(phrases) >= MIN_PHRASES:
                shortlist.append(
                    {
                        "problem_id": row["id"],
                        "name": row["name"],
                        "name_match": name_match,
                        "phrases_found": phrases,
                        "has_description": page.is_file(),
                    }
                )
        status = {0: "not_present", 1: "single_match"}.get(len(shortlist), "ambiguous")
        result["candidates"][key] = {
            "status": status,
            "shortlist": shortlist,
            "task_to_confirm": spec["task"],
            "confirmed_problem_id": None,
            "confirmed_by_role": None,
        }
    return result


CONFIRMER_ROLES = {
    "real": frozenset({"owner", "supervisor"}),
    "synthetic": frozenset({"synthetic-fixture"}),
}


def confirm(identification: dict[str, Any], candidate: str, problem_id: str, role: str) -> None:
    """Record the human confirmation that a shortlisted statement is the candidate's task."""
    entry = identification["candidates"].get(candidate)
    if entry is None:
        raise StopConditionError("S4-identification", f"unknown candidate {candidate}")
    if problem_id not in {s["problem_id"] for s in entry["shortlist"]}:
        raise StopConditionError(
            "S4-identification", f"{problem_id} is not on {candidate}'s shortlist"
        )
    if role not in CONFIRMER_ROLES[identification["source"]]:
        raise StopConditionError(
            "S4-identification",
            f"role {role!r} cannot confirm {identification['source']} data; "
            f"use one of {sorted(CONFIRMER_ROLES[identification['source']])}",
        )
    entry["confirmed_problem_id"] = problem_id
    entry["confirmed_by_role"] = role


# ------------------------------------------------------------------ feasibility
@dataclass(frozen=True)
class Submission:
    submission_id: str
    user_id: str
    date: int
    language: str
    original_language: str
    status: str


def _row_problem(row: dict[str, str | None], problem_id: str) -> str | None:
    """Return why a row is malformed, or None."""
    for field in REQUIRED_FIELDS:
        if not (row.get(field) or "").strip():
            return f"missing_{field}"
    for field, pattern in ID_PATTERNS.items():
        if not pattern.fullmatch((row[field] or "").strip()):
            return f"bad_{field}"
    if (row["problem_id"] or "").strip() != problem_id:
        return "problem_id_mismatch"
    date = (row["date"] or "").strip()
    if not date.isdigit() or int(date) <= 0:
        return "bad_date"
    if None in row:  # more cells than header columns
        return "extra_cells"
    return None


def classify(status: str) -> str:
    if status == ACCEPTED:
        return "accepted"
    if status in ELIGIBLE_REJECTED:
        return "eligible_rejected"
    if status in PRESENTATION:
        return "presentation_error"
    if status in COMPILE:
        return "compile_error"
    if status in INFRA:
        return "judge_infrastructure"
    return "unknown_status"


def load_submissions(path: Path, problem_id: str) -> tuple[list[Submission], dict[str, Any]]:
    counts: dict[str, Any] = {"rows_read": 0, "malformed": Counter[str]()}
    rows: dict[str, list[tuple[str, ...]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = frozenset(reader.fieldnames or ())
        if header != SUBMISSION_COLUMNS:
            raise StopConditionError("S3-schema", f"{path.name} columns {sorted(header)}")
        for row in reader:
            counts["rows_read"] += 1
            reason = _row_problem(row, problem_id)
            if reason:
                counts["malformed"][reason] += 1
                continue
            key = tuple((row[c] or "").strip() for c in sorted(SUBMISSION_COLUMNS))
            rows[(row["submission_id"] or "").strip()].append(key)
    columns = sorted(SUBMISSION_COLUMNS)
    exact_dupes = conflicting_rows = conflicting_ids = 0
    submissions = []
    for sid in sorted(rows):
        variants = set(rows[sid])
        if len(variants) > 1:
            conflicting_ids += 1
            conflicting_rows += len(rows[sid])
            continue
        exact_dupes += len(rows[sid]) - 1
        values = dict(zip(columns, rows[sid][0], strict=True))
        submissions.append(
            Submission(
                submission_id=sid,
                user_id=values["user_id"],
                date=int(values["date"]),
                language=values["language"],
                original_language=values["original_language"],
                status=values["status"],
            )
        )
    counts["valid_rows"] = counts["rows_read"] - sum(counts["malformed"].values())
    counts["exact_duplicates_dropped"] = exact_dupes
    counts["conflicting_duplicate_ids"] = conflicting_ids
    counts["conflicting_duplicate_rows_excluded"] = conflicting_rows
    counts["unique_submissions"] = len(submissions)
    counts["malformed"] = dict(sorted(counts["malformed"].items()))
    return submissions, counts


def _quartiles(values: list[int]) -> dict[str, float] | None:
    if not values:
        return None
    if len(values) == 1:
        return {"q1": values[0], "median": values[0], "q3": values[0]}
    q1, median, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"q1": q1, "median": median, "q3": q3}


def pair(submissions: list[Submission]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Same-user pairing on C++ submissions (protocol section 6)."""
    cpp = [s for s in submissions if s.language == LANGUAGE]
    by_class = Counter(classify(s.status) for s in cpp)
    unknown = Counter(s.status for s in cpp if classify(s.status) == "unknown_status")
    by_user: dict[str, list[Submission]] = defaultdict(list)
    for s in cpp:
        by_user[s.user_id].append(s)
    timing = Counter[str]()
    pairs: list[dict[str, Any]] = []
    for user in sorted(by_user):
        history = sorted(by_user[user], key=lambda s: (s.date, s.submission_id))
        accepts = [s for s in history if s.status == ACCEPTED]
        rejected = [s for s in history if s.status in ELIGIBLE_REJECTED]
        if not accepts:
            timing["never_accepted"] += len(rejected)
            continue
        fix = accepts[0]
        before = [s for s in rejected if s.date < fix.date]
        timing["before_first_accept"] += len(before)
        timing["same_second_as_first_accept"] += sum(s.date == fix.date for s in rejected)
        timing["after_first_accept"] += sum(s.date > fix.date for s in rejected)
        if not before:
            continue
        last = before[-1]
        between = [s for s in history if last.date < s.date < fix.date]
        pairs.append(
            {
                "user_id": user,
                "rejected_submission_id": last.submission_id,
                "rejected_status": last.status,
                "accepted_submission_id": fix.submission_id,
                "gap_seconds": fix.date - last.date,
                "rejected_before_accept": len(before),
                "submissions_between": len(between),
                "same_original_language": last.original_language == fix.original_language,
            }
        )
    gaps = [p["gap_seconds"] for p in pairs]
    summary = {
        "cpp_submissions": len(cpp),
        "by_language": dict(sorted(Counter(s.language for s in submissions).items())),
        "cpp_by_original_language": dict(sorted(Counter(s.original_language for s in cpp).items())),
        "cpp_by_class": {
            k: by_class.get(k, 0)
            for k in (
                "accepted",
                "eligible_rejected",
                "presentation_error",
                "compile_error",
                "judge_infrastructure",
                "unknown_status",
            )
        },
        "unknown_statuses": dict(sorted(unknown.items())),
        "eligible_rejected_by_status": dict(
            sorted(Counter(s.status for s in cpp if s.status in ELIGIBLE_REJECTED).items())
        ),
        "eligible_rejected_by_timing": {
            k: timing.get(k, 0)
            for k in (
                "before_first_accept",
                "same_second_as_first_accept",
                "after_first_accept",
                "never_accepted",
            )
        },
        "cpp_users": len(by_user),
        "users_with_accept": sum(any(s.status == ACCEPTED for s in h) for h in by_user.values()),
        "primary_pairs": len(pairs),
        "secondary_pairs": timing.get("before_first_accept", 0),
        "primary_pairs_by_rejected_status": dict(
            sorted(Counter(p["rejected_status"] for p in pairs).items())
        ),
        "gap_seconds_quartiles": _quartiles(gaps),
        "pairs_with_gap_over_30_days": sum(g > LONG_GAP_SECONDS for g in gaps),
        "pairs_with_language_version_change": sum(not p["same_original_language"] for p in pairs),
    }
    return pairs, summary


def reconcile(counts: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    """Count identities that must hold (protocol section 6.5); returns failures."""
    failures = []

    def check(name: str, left: int, right: int) -> None:
        if left != right:
            failures.append(f"{name}: {left} != {right}")

    check(
        "rows_read = malformed + valid",
        counts["rows_read"],
        sum(counts["malformed"].values()) + counts["valid_rows"],
    )
    check(
        "valid = unique + exact duplicates + conflicting rows",
        counts["valid_rows"],
        counts["unique_submissions"]
        + counts["exact_duplicates_dropped"]
        + counts["conflicting_duplicate_rows_excluded"],
    )
    check(
        "unique = sum by language",
        counts["unique_submissions"],
        sum(summary["by_language"].values()),
    )
    check("C++ = sum by class", summary["cpp_submissions"], sum(summary["cpp_by_class"].values()))
    check(
        "eligible rejected = sum by timing",
        summary["cpp_by_class"]["eligible_rejected"],
        sum(summary["eligible_rejected_by_timing"].values()),
    )
    check(
        "secondary pairs = rejected before first accept",
        summary["secondary_pairs"],
        summary["eligible_rejected_by_timing"]["before_first_accept"],
    )
    check(
        "primary pairs = sum by rejected status",
        summary["primary_pairs"],
        sum(summary["primary_pairs_by_rejected_status"].values()),
    )
    if summary["primary_pairs"] > summary["users_with_accept"]:
        failures.append("more primary pairs than users with an accept")
    return failures


def stop_conditions(counts: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    fired = []
    rows = max(counts["rows_read"], 1)
    if sum(counts["malformed"].values()) / rows > MAX_MALFORMED_SHARE:
        fired.append("S5-malformed-rows-over-1%")
    if counts["conflicting_duplicate_rows_excluded"] / rows > MAX_CONFLICT_SHARE:
        fired.append("S5-conflicting-duplicates-over-1%")
    if summary["cpp_by_class"]["unknown_status"] / max(summary["cpp_submissions"], 1) > (
        MAX_UNKNOWN_STATUS_SHARE
    ):
        fired.append("S5-unknown-status-over-1%")
    return fired


def band(primary_pairs: int) -> str:
    if primary_pairs >= PAIRS_TARGET:
        return "feasible"
    if primary_pairs >= PAIRS_MINIMUM:
        return "feasible_below_target"
    return "not_feasible"


def feasibility(
    root: Path, identification: dict[str, Any], *, synthetic: bool = False
) -> dict[str, Any]:
    """Counts for each confirmed candidate, in pre-registered order (section 7)."""
    source = "synthetic" if synthetic else "real"
    if identification.get("source") != source:
        raise StopConditionError(
            "S4-identification",
            f"identification is from {identification.get('source')!r} data, not {source!r}",
        )
    report: dict[str, Any] = {
        "protocol": PROTOCOL_VERSION,
        "source": source,
        "candidates": {},
        "stops": [],
    }
    for key in CANDIDATES:
        entry = identification["candidates"].get(key, {})
        problem_id = entry.get("confirmed_problem_id")
        if not problem_id:
            report["candidates"][key] = {
                "status": entry.get("status", "not_identified"),
                "evaluated": False,
            }
            continue
        listed = {s["problem_id"] for s in entry.get("shortlist", [])}
        if (
            problem_id not in listed
            or entry.get("confirmed_by_role") not in CONFIRMER_ROLES[source]
        ):
            raise StopConditionError(
                "S4-identification",
                f"{key}: confirmed id {problem_id} is not on the shortlist or has no confirmer",
            )
        path = root / CODENET / "metadata" / f"{problem_id}.csv"
        if not path.is_file():
            raise StopConditionError("S4-identification", f"{key}: no metadata file {path.name}")
        submissions, counts = load_submissions(path, problem_id)
        _pairs, summary = pair(submissions)
        failures = reconcile(counts, summary)
        stops = stop_conditions(counts, summary)
        if failures:
            stops.append("S6-reconciliation")
        report["candidates"][key] = {
            "evaluated": True,
            "problem_id": problem_id,
            "input_sha256": sha256_file(path),
            "rows": counts,
            "pairing": summary,
            "reconciliation_failures": failures,
            "stops": stops,
            "band": None if stops else band(summary["primary_pairs"]),
        }
        report["stops"].extend(f"{key}:{s}" for s in stops)
        if stops:
            break
        # Pre-registered order: the fallback is counted only if the first choice falls short.
        if band(summary["primary_pairs"]) != "not_feasible":
            break
    for key in CANDIDATES:
        report["candidates"].setdefault(key, {"status": "not_needed", "evaluated": False})
    report["recommendation"] = _recommend(report)
    return report


def _recommend(report: dict[str, Any]) -> str:
    if report["stops"]:
        return "stop: a stop condition fired; report to the owner, no further step"
    for key, entry in report["candidates"].items():
        if entry.get("evaluated") and entry["band"] != "not_feasible":
            return f"{key} ({entry['band']}): present to the owner for the PC1-E decision"
    return "no candidate reached the minimum: report to the owner; no substitution"


def publication_notice(permission: Path | None) -> dict[str, Any]:
    """A1b: what the permission record says about publishing these counts."""
    if permission is None:
        return {"publish_derived_statistics": None, "notice": "SYNTHETIC FIXTURES - NOT DATA"}
    record = json.loads(permission.read_text(encoding="utf-8"))
    allowed = record.get("scope", {}).get("publish_derived_statistics") is True
    return {
        "publish_derived_statistics": allowed,
        "notice": "may be published under the permission record"
        if allowed
        else "NOT FOR PUBLICATION: the permission record does not allow publishing these counts",
    }


def feasibility_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# PC1 feasibility counts (protocol {report['protocol']})",
        "",
        f"**{report['publication']['notice']}**",
        "",
        "Metadata only. No source code read, no diagnosis run. Counts of submissions, not of",
        "misconceptions.",
        "",
        f"**Recommendation:** {report['recommendation']}",
        "",
    ]
    for key, entry in report["candidates"].items():
        lines.append(f"## {key}")
        if not entry.get("evaluated"):
            lines += ["", f"Not evaluated ({entry.get('status')}).", ""]
            continue
        rows, pairing = entry["rows"], entry["pairing"]
        lines += [
            "",
            f"Problem `{entry['problem_id']}`, input sha256 `{entry['input_sha256']}`, "
            f"band **{entry['band']}**.",
            "",
            "| Count | Value |",
            "| --- | --- |",
            f"| Rows read | {rows['rows_read']} |",
            f"| Malformed rows | {sum(rows['malformed'].values())} |",
            f"| Exact duplicates dropped | {rows['exact_duplicates_dropped']} |",
            f"| Conflicting duplicate rows excluded | "
            f"{rows['conflicting_duplicate_rows_excluded']} |",
            f"| Unique submissions | {rows['unique_submissions']} |",
            f"| C++ submissions | {pairing['cpp_submissions']} |",
            f"| C++ users / with an accept | "
            f"{pairing['cpp_users']} / {pairing['users_with_accept']} |",
            f"| Eligible rejected (C++) | {pairing['cpp_by_class']['eligible_rejected']} |",
            f"| Primary pairs (one per user) | {pairing['primary_pairs']} |",
            f"| Secondary pairs | {pairing['secondary_pairs']} |",
            f"| Pairs with gap over 30 days | {pairing['pairs_with_gap_over_30_days']} |",
            "",
        ]
        if entry["reconciliation_failures"] or entry["stops"]:
            lines += [
                f"Stops: {entry['stops']}; reconciliation: {entry['reconciliation_failures']}",
                "",
            ]
    return "\n".join(lines)


# ------------------------------------------------------------------ CLI
def _open_data(args: argparse.Namespace) -> Path:
    """Gate first, then the fixture/real separation; raises before any data is read."""
    data_dir = Path(args.data_dir)
    if not args.synthetic_fixtures:
        require_gate(Path(args.permission), "metadata")
        if _inside(Path(args.out), REPO_ROOT):
            raise GateClosedError("real-data outputs are written outside the repository first")
    check_data_dir(data_dir, synthetic=args.synthetic_fixtures)
    return data_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pc1", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    gate = sub.add_parser("gate", help="check the permission record; reads no data")
    gate.add_argument("--level", choices=sorted(REQUIRED_SCOPE), default="metadata")
    ext = sub.add_parser("extract", help="extract metadata/ and problem_descriptions/ only")
    ext.add_argument("--archive", required=True, help="path, or - to read a stream (curl ... |)")
    ext.add_argument("--data-dir", required=True)
    ident = sub.add_parser("identify", help="shortlist candidate problems")
    conf = sub.add_parser("confirm", help="record the human confirmation of one candidate")
    conf.add_argument("--identification", required=True)
    conf.add_argument("--candidate", required=True, choices=sorted(CANDIDATES))
    conf.add_argument("--problem", required=True)
    conf.add_argument("--role", required=True)
    feas = sub.add_parser("feasibility", help="count, pair and reconcile")
    feas.add_argument("--identification", required=True)
    for p in (ident, feas):
        p.add_argument("--data-dir", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--synthetic-fixtures", action="store_true")
    for p in (gate, ext, ident, conf, feas):
        p.add_argument("--permission", default=str(DEFAULT_PERMISSION))
    args = parser.parse_args(argv)
    try:
        if args.command == "gate":
            require_gate(Path(args.permission), args.level)
            print(f"gate open for level {args.level!r}")
            return EXIT_OK
        if args.command == "extract":
            data_dir = Path(args.data_dir)
            require_gate(Path(args.permission), "metadata")
            check_data_dir(data_dir, synthetic=False)
            source = sys.stdin.buffer if args.archive == "-" else Path(args.archive)
            print(dump(extract(source, data_dir)), end="")
            return EXIT_OK
        if args.command == "confirm":
            path = Path(args.identification)
            identification = json.loads(path.read_text(encoding="utf-8"))
            confirm(identification, args.candidate, args.problem, args.role)
            write_atomic(path, dump(identification))
            print(f"{args.candidate} confirmed as {args.problem} by {args.role}")
            return EXIT_OK
        root = _open_data(args)
        out = Path(args.out)
        if args.command == "identify":
            result = identify(root, synthetic=args.synthetic_fixtures)
            write_atomic(out / "identification.json", dump(result))
            print(dump({k: v["status"] for k, v in result["candidates"].items()}), end="")
            return EXIT_OK
        identification = json.loads(Path(args.identification).read_text(encoding="utf-8"))
        report = feasibility(root, identification, synthetic=args.synthetic_fixtures)
        report["publication"] = publication_notice(
            None if args.synthetic_fixtures else Path(args.permission)
        )
        write_atomic(out / "feasibility.json", dump(report))
        write_atomic(out / "feasibility.md", feasibility_markdown(report))
        print(report["recommendation"])
        return EXIT_STOP if report["stops"] else EXIT_OK
    except GateClosedError as exc:
        print(f"PC1 permission gate closed; nothing was read.\n  {exc}", file=sys.stderr)
        return EXIT_GATE
    except StopConditionError as exc:
        print(f"PC1 stop condition {exc.code}: {exc.detail}", file=sys.stderr)
        return EXIT_STOP


if __name__ == "__main__":
    sys.exit(main())
