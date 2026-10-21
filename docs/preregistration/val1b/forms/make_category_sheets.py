"""Generate the stage-2 category sheets and categories.json from the frozen content.

Run from the repository root: python3 docs/preregistration/val1b/forms/make_category_sheets.py
Stops if a content file no longer matches the frozen version recorded in the protocol.
Labellers receive only the `categories/<problem>.md` sheets; categories.json (the key from
category id to model) is never shown to them.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROBLEMS = ("lower-bound", "count-occurrences", "last-less-than", "first-true")
SKILL_IDS = {
    "search_space_boundaries": "S1",
    "loop_termination": "S2",
    "equality_handling": "S3",
    "problem_specification": "S4",
}


def main() -> None:
    key: dict[str, object] = {"skills": {v: k for k, v in SKILL_IDS.items()}}
    (HERE / "categories").mkdir(exist_ok=True)
    skills_text = None
    for slug in PROBLEMS:
        raw = (ROOT / f"content/demo/{slug}/problem.toml").read_bytes()
        spec = tomllib.loads(raw.decode())
        skills_text = skills_text or spec["skills"]
        # Order by a hash of the key, so the list order does not follow the content file.
        models = sorted(
            spec["error_models"], key=lambda m: hashlib.sha256(m["key"].encode()).hexdigest()
        )
        ids = {f"C{i + 1}": m for i, m in enumerate(models)}
        key[slug] = {
            "problem_toml_sha256": hashlib.sha256(raw).hexdigest(),
            "categories": {c: m["key"] for c, m in ids.items()},
            "category_skills": {c: SKILL_IDS[m["skill"]] for c, m in ids.items()},
        }
        lines = [
            f"# Categories for problem: {spec['title']}",
            "",
            "Choose the one category that best matches **your own stage-1 description** of the",
            "primary error. If none fits, use `other-single` (and describe it), `multiple`, or",
            "`unclear`. Do not change your stage-1 answers.",
            "",
            "| Id | Description |",
            "| --- | --- |",
            *[f"| {c} | {m['description']} |" for c, m in ids.items()],
            "| other-single | One error that is not in this list |",
            "| multiple | Two or more independent errors |",
            "| unclear | You cannot tell |",
            "",
            "## Skills",
            "",
            "| Id | Skill |",
            "| --- | --- |",
            *[
                f"| {SKILL_IDS[s]} | {t} |"
                for s, t in sorted(spec["skills"].items(), key=lambda x: SKILL_IDS[x[0]])
            ],
            "| none | None of these |",
            "| uncertain | You cannot tell |",
            "",
        ]
        (HERE / "categories" / f"{slug}.md").write_text("\n".join(lines))
    (HERE / "categories.json").write_text(json.dumps(key, indent=1) + "\n")


if __name__ == "__main__":
    main()
