# Labelling forms (draft)

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
