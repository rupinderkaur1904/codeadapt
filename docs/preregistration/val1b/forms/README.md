# Labelling forms and study file formats

Each labeller gets one spreadsheet or CSV per stage, with one row per program, identified
by a random program code. Labellers never see author codes or author notes.

## Stage 1: own words (before any category list is seen)

| Field | Values |
| --- | --- |
| `program` | program code |
| `correctness` | `correct` / `incorrect` / `unsure` |
| `fault_lines` | line number(s) of the primary faulty statement |
| `what_is_wrong` | free text, one or two sentences |
| `should_be` | free text: what the code should do instead |
| `minimal_fix` | replacement text for `fault_lines` (empty if `correct`) |
| `other_errors` | free text, optional |
| `confidence` | 1 (guess) / 2 (fairly sure) / 3 (sure) |
| `notes` | optional |

The labeller's instructions say:

- Describe the **primary** mistake, meaning the one you would point a learner to first.
- Use your own words. There is no list of right answers.
- You may compile and run the program on inputs you choose.
- Do not look anything up about CodeAdapt.

## Stage 2: categories (after both stage-1 files are committed)

The labeller sees their own stage-1 row, read-only, and the problem's list of category
descriptions in plain language.

| Field | Values |
| --- | --- |
| `program` | program code |
| `category` | one listed category / `other-single` / `multiple` / `unclear` |
| `other_description` | free text if `other-single` |
| `skill` | one of four skill descriptions / `none of these` / `uncertain` |
| `mapping_confidence` | 1 / 2 / 3 |
| `change_note` | optional: if your stage-1 judgement now looks wrong, say why. Do not edit stage 1. |

## Adjudication (owner)

| Field | Values |
| --- | --- |
| `program` | program code |
| `trigger` | `category_differs` / `unclear_or_multiple` / `correctness_differs` |
| `adjudicated_category` | as stage 2 |
| `adjudicated_skill` | as stage 2 |
| `reason` | free text |
| `author_note_consulted` | yes / no |

## Category sheets

`categories/<problem>.md` is what a labeller receives for stage 2: plain-language
descriptions under neutral ids (C1, C2, ...) and skill ids (S1–S4). The order is by a hash
of the model key, not the content file's order. `categories.json`, the key from ids to
model keys and skills with each `problem.toml`'s SHA-256, is never shown to labellers.
Regenerate both with `make_category_sheets.py`; it must reproduce them byte for byte from
the frozen content.

## Study files read by `../analysis/analyse.py`

All are CSV with a header row, one row per program unless stated. Templates (header only)
are in `templates/`.

| File | Columns | Written by |
| --- | --- | --- |
| `programs.csv` | `program, problem, author, declared` (`correct`/`incorrect`, as the author declared) | Owner, at collection |
| `stage1_L1.csv`, `stage1_L2.csv` | as the stage-1 form above; `fault_lines` is a comma-separated list | Labellers |
| `stage2_L1.csv`, `stage2_L2.csv` | as the stage-2 form above, using category and skill ids | Labellers |
| `adjudication.csv` | as the adjudication form above | Owner |
| `fix_validity.csv` | `program, labeller, validity` (`valid`/`invalid`/`does-not-compile`/`none`), one row per program and labeller | Claude, at stage 4 |
| `codeadapt.csv` | `program, method_version, outcome, selected_model, qualified, reproducible`, one row per program and method version; `qualified` is `true` for single-behaviour or documented-collision diagnoses | Claude, at stage 4 |

`author` holds a code (A1–A5) and `program` a random code (P001...). No file holds a name,
email address or any other identifier of a person.
