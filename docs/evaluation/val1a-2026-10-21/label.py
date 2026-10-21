"""VAL1-A: a-priori concept labels for the generated mutants (PLAN.md §4).

Written after generation and BEFORE any mutant was run. The labels are the plan author's
judgement (an AI system working on this project), not human labels.

* `strict`: the label under the literal rules of PLAN.md §4, extended only to edits whose
  resulting code is the same statement as a listed edit (for example `lo = (mid - 1) + 1`
  is `lo = mid`). This is the primary, pre-registered label.
* `lenient`: a sensitivity label for edits that are debatable. It applies when a model's
  described error, read more broadly than §4 (for example "`lo = mid` instead of
  `mid + 1`" in a closed loop), fits the edit. Both are reported; the strict one is
  primary.

Run from the repository root:  python3 docs/evaluation/val1a-2026-10-21/label.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "eval/mutation/lower-bound/manifest.json"
OUT = ROOT / "eval/mutation/lower-bound/labels.json"

STRICT = {
    # Style A (half-open, the reference style)
    "A_UOI_004": ("hi_init_last_index", "hi = n - 1 with a half-open loop"),
    "A_ROR_007": ("closed_loop_hi_mid", "lo <= hi with hi = mid"),
    "A_UOI_012": ("closed_loop_hi_mid", "lo < hi + 1 is lo <= hi, with hi = mid"),
    "A_ROR_027": ("upper_bound_confusion", "a[mid] <= target sends equal elements right"),
    "A_DEL_038": ("no_progress_update", "lo = mid"),
    "A_ICR_037": ("no_progress_update", "lo = mid + 0 is lo = mid"),
    "A_UOI_034": ("no_progress_update", "lo = (mid - 1) + 1 is lo = mid"),
    "A_UOI_041": ("hi_skips_candidate", "hi = mid - 1 in a half-open loop"),
    "A_UOI_044": ("returns_wrong_pointer", "returns lower_bound - 1"),
    # Style B (closed with an answer variable)
    "B_ROR_035": ("upper_bound_confusion", "a[mid] > target sends equal elements right"),
    "B_UOI_057": ("returns_wrong_pointer", "returns ans - 1"),
    # Style C (recursive, half-open)
    "C_ROR_005": ("closed_loop_hi_mid", "base case lo > hi with hi = mid"),
    "C_UOI_008": ("closed_loop_hi_mid", "lo >= hi + 1 is lo > hi, with hi = mid"),
    "C_ROR_025": ("upper_bound_confusion", "a[mid] <= target sends equal elements right"),
    "C_DEL_038": ("no_progress_update", "recurse with lo = mid"),
    "C_ICR_035": ("no_progress_update", "mid + 0 is mid"),
    "C_UOI_032": ("no_progress_update", "(mid - 1) + 1 is mid"),
    "C_UOI_042": ("hi_skips_candidate", "recurse with hi = mid - 1 in a half-open range"),
    "C_UOI_012": ("returns_wrong_pointer", "base case returns lo - 1"),
    "C_UOI_046": ("hi_init_last_index", "initial call with hi = n - 1"),
}

# Debatable edits: the alternative label under a broader reading of the model description.
LENIENT = {
    "B_DEL_047": ("closed_loop_hi_mid", "closed loop with hi = mid: E7's described code shape"),
    "B_ICR_046": ("closed_loop_hi_mid", "hi = mid - 0 is hi = mid in a closed loop"),
    "B_UOI_042": ("closed_loop_hi_mid", "hi = (mid + 1) - 1 is hi = mid in a closed loop"),
    "B_DEL_054": ("no_progress_update", "lo = mid instead of mid + 1 (closed loop)"),
    "B_ICR_053": ("no_progress_update", "lo = mid + 0 (closed loop)"),
    "B_UOI_050": ("no_progress_update", "lo = (mid - 1) + 1 (closed loop)"),
    "B_UOI_040": ("returns_wrong_pointer", "records mid - 1 as the answer (returns n when absent above)"),
    "B_UOI_010": ("hi_init_last_index", "answer starts at n - 1, so n is unreachable (E2's behaviour, not its code)"),
}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    ids = {e["id"] for e in manifest if "excluded" not in e}
    unknown = (set(STRICT) | set(LENIENT)) - ids
    if unknown:
        raise SystemExit(f"labels for unknown mutants: {sorted(unknown)}")
    labels = {}
    for mid in sorted(ids):
        strict, s_reason = STRICT.get(mid, ("none", ""))
        lenient, l_reason = LENIENT.get(mid, (strict, s_reason))
        labels[mid] = {
            "strict": strict,
            "lenient": lenient,
            "reason": l_reason if mid in LENIENT else s_reason,
            "debatable": mid in LENIENT,
        }
    OUT.write_text(json.dumps(labels, indent=1, sort_keys=True) + "\n")
    n_lib = sum(v["strict"] != "none" for v in labels.values())
    print(f"{len(labels)} labelled; {n_lib} with a library label (strict); {len(LENIENT)} debatable")


if __name__ == "__main__":
    main()
