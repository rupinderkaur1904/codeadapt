# VAL1-B pre-registration package

**Status: complete for owner review; recruitment blocked.** Nobody has been contacted. No
program, label, name, contact detail or consent form exists in this repository, and none
may be added to it or sent to Claude. Recruitment may start only after every item under
"Owner actions" is done, including the institution's recorded determination.

| Path | What it is |
| --- | --- |
| `protocol.md` | Protocol 2.1: version 2 as approved on 2026-10-21, with amendments A1–A6 |
| `analysis/analyse.py` | The pre-registered analysis (primary P1–P6, decision rules S0–S5, exploratory) |
| `analysis/dummy.py` | Invented test data in four scenarios; never study data |
| `backend/tests/unit/test_val1b_analysis.py` | Runs the analysis on the dummy data in CI, including "unevaluable precision is never a pass" |
| `forms/README.md`, `forms/templates/` | Stage-1, stage-2 and adjudication forms; every study file format |
| `forms/categories/<problem>.md` | What labellers see at stage 2 (neutral ids, plain-language descriptions) |
| `forms/categories.json`, `forms/make_category_sheets.py` | The id-to-model key (never shown to labellers) and its generator, with each frozen `problem.toml` hash |
| `practice/` | Stage-0 practice problem, three programs and a plain-words key; unrelated to binary search |
| `materials/` | Information sheet, consent form (CC0 only on explicit opt-in; private by default), recruitment criteria, licence note |
| `institutional-review.md` | Questions for the supervisor or ethics office, a ready-to-send message, and the blank determination record |

Frozen with this package: content versions `lower-bound 871602bc2bba`,
`count-occurrences d1b043c04574`, `last-less-than 3d52811ae14b`, `first-true b69c5efa3b39`;
primary method `fingerprint_consistency` 1.2 (ADR-027), secondary 1.1. `MANIFEST.sha256`
lists the SHA-256 of every file here at the freeze commit.

## Owner actions (in order)

1. **Fill the placeholders** in `materials/` (name, role, institution, supervisor, contact,
   collection period, withdrawal deadline, key-deletion date, payment) or replace the drafts
   with the institution's own templates.
2. **Send the institutional-review request** (`institutional-review.md` §4, with the
   listed attachments) and **record the answer verbatim** in §2. If it sets conditions,
   the protocol or materials are revised and you re-approve them.
3. **Decide compensation** (none, or amount and form, within any institutional rule).
4. **Confirm the adjudicator**: you, or (better) a second person who has not seen the error
   models.
5. **Set up private storage outside the repository** for names, contacts, signed forms and
   the code key, and name the private study repository (ADR-009) for material whose
   contributor does not opt in to CC0.
6. **Confirm the student-facing time-limit wording** now deployed by ADR-027 (the text in
   ADR-027 D4), and decide ADR-027 Q2 (a research-view note that `loop_termination` has no
   remaining negative evidence source from time limits) and Q3 (a separate audit of
   memory-limit and crash signatures).
7. **Give an explicit go-ahead to recruit** once items 1–5 are done. Until then nobody is
   approached.
