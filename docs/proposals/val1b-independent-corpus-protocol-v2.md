# Proposal: VAL1-B protocol, version 2 (for owner approval)

**Status: proposed revision, not started.** Nobody is contacted or recruited, and no code
or labels are collected, until three things are recorded here:

1. the owner approves this version;
2. the owner approves the participant materials in `val1b-materials/`;
3. the institutional determination is recorded in
   `val1b-materials/institutional-review.md`.

The record must be the institution's actual answer. Exemption is not assumed.

Version 1 (`val1b-independent-corpus-protocol.md`, commit 835bc3a) stays unchanged as the
original proposal. This document replaces it only once approved. Everything not listed in
§0 carries over from v1 unchanged:

- the four frozen problems and content versions;
- what authors see and never see;
- data recorded per program;
- `eval/independent/<problem>/` with `data_class = synthetic-independent`;
- the claims that are not allowed under any result.

## 0. What changed from v1, and why

| # | Change | Why (owner request, 2026-10-21) |
| --- | --- | --- |
| 1 | New **stage 1**: independent open-ended labelling. Each labeller describes the primary error in their own words and gives a minimal fix, before seeing any modelled-error category. | Mapping straight onto CodeAdapt's categories lets the taxonomy shape what labellers see. |
| 2 | The v1 taxonomy labelling becomes **stage 2**, done after stage 1 is committed and without editing it. Agreement is reported separately for the two stages. | It separates "do humans agree on the error?" from "do humans agree on which CodeAdapt category it is?" |
| 3 | **Blinding is extended.** Labellers are kept away from CodeAdapt outputs, hidden tests, our execution results, author notes and each other's labels until their labels are committed. CodeAdapt runs only after adjudication is committed. | Owner request. |
| 4 | **Records are immutable.** Raw stage-1 labels, raw stage-2 labels, confidence ratings, disagreements and adjudication each live in separate files with hashes. Adjudication never overwrites a raw label. | Owner request. |
| 5 | **Sample size and thresholds are rechecked** (§7). The primary analysis is now based on agreement, there is a minimum count before precision is a primary endpoint, three-way outcomes (fail / inconclusive / adequate) replace single point thresholds, and 100 incorrect programs are recommended (60 minimum). | The v1 figures assumed about 25 named diagnoses. VAL1-A and the ADR-027 replay suggest far fewer, perhaps 6 to 20 at 60 programs. |
| 6 | **Primary and exploratory metrics are separated** (§6). | Owner request. |
| 7 | **Training no longer primes the taxonomy before stage 1.** Stage-1 practice uses an unrelated problem, and taxonomy practice happens only before stage 2. | In v1, owner-led calibration on held-out programs taught the categories before labelling. |
| 8 | Authors must **not use AI code assistants or generators**, and must attest that they have not read the repository. | Generated bugs would measure an AI's error distribution, and reading the repository would leak the error models. |
| 9 | **Method version pre-registration.** The primary analysis uses the method version deployed at the freeze commit. If ADR-027 is approved by then, v1.2 is primary and v1.1 is secondary. | ADR-027 changes how time-limit evidence is reported. |
| 10 | The **suggested licence changes** from CC BY 4.0 to CC0 1.0 (see `val1b-materials/licence.md`). | CC BY requires attribution, which conflicts with publishing the code anonymously. Creative Commons also does not recommend its licences for software. |
| 11 | Institutional review becomes a **recorded determination** with a template. Recruitment is blocked until it is filled in. | Owner request: do not assume exemption. |

## 1. Purpose and claims

The question is as in v1. On incorrect C++ solutions written by people who have never seen
CodeAdapt's error models:

- How often does the frozen method name an error?
- When it does, do independent humans identify the same error?
- How often do humans agree with each other, first in their own words and then in
  CodeAdapt's categories?

The claim allowed if the primary results are adequate (§8) is: "On N independently written
incorrect solutions to four binary-search problems, two blind labellers agreed on the
primary error in A% of programs (own words) and B% (CodeAdapt categories). The method
named an error on C% and agreed with the agreed human label on D of E (95% CI …). It
abstained or reported a symptom on the rest."

The claims not allowed are as in v1, with two additions:

- real-student or novice accuracy;
- any learning effect;
- skill mastery;
- validated BKT parameters;
- generalisation beyond binary search (new);
- any claim about how students would react to the feedback (new).

## 2. Participants

The roles are authors (who write buggy programs) and labellers (who identify errors).
Inclusion and exclusion criteria are in `val1b-materials/recruitment.md`.

- **Target:** 5 authors, giving 100 incorrect programs. **Minimum:** 3 authors, giving 60
  programs, accepted with the reduced resolution stated in §7.
- **Labellers:** 2 people who are not authors, plus the owner as adjudicator only.
- **The owner's labels are never used in agreement statistics or in the primary precision
  analysis.** The owner has read the error models, so their labels are not blind to the
  taxonomy. This is why the primary precision analysis uses the subset where the labellers
  agree, not the adjudicated labels.

## 3. Author task

As in v1:

- per problem, 5 programs that compile but are wrong, each with one mistake the author
  believes a learner could plausibly make;
- optionally up to 2 correct programs in different styles;
- a private one-line note per program.

Two additions:

- **No AI assistants.** Authors may not use an AI code assistant or generator for these
  programs.
- **Attestation.** Each author attests on the consent form that they have not read the
  CodeAdapt repository, its design records or its error models.

## 4. Labelling procedure

### Stage 0: practice

- Each labeller labels 3 practice programs for an **unrelated** problem, using the stage-1
  form only. These programs are supplied with the materials and are not binary search.
- Before stage 1, nobody discusses CodeAdapt's categories with the labellers.
- The practice items are excluded from all results.

### Stage 1: independent open-ended labels

**What labellers see:** the problem statement, its 2 public sample tests, and the program
source.

**What they may do:** compile and run the program on inputs they choose. Their own runs
are allowed; our runs, hidden tests and CodeAdapt outputs are not shown to them.

**What they record per program** (form in `val1b-materials/labelling-forms.md`):

1. **Correctness:** `correct`, `incorrect`, or `unsure`.
2. **Primary error, in the labeller's own words:**
   - the line number(s) of the faulty statement;
   - what is wrong;
   - what the code should do instead.
3. **Minimal fix:** the smallest edit the labeller believes makes the program correct,
   written as a replacement for the faulty line(s).
4. **Other errors,** if any, also in the labeller's own words.
5. **Confidence:** 1 to 3.

**Freeze.** When a labeller has finished every program, their stage-1 file is committed
with its SHA-256 recorded in `eval/independent/labels/MANIFEST.md`. The owner receives the
files and commits them. Claude never sees labeller identities, which are coded L1 and L2.
Labellers do not see each other's files at any point before adjudication.

### Stage 2: taxonomy mapping

This stage starts only after **both** labellers' stage-1 files are committed. Each
labeller receives:

- the problem's plain-language list of modelled errors (from each design record §2, never
  model keys or code);
- the four skill descriptions;
- their **own** stage-1 labels, read-only.

**What they record per program:**

1. **Category:** one modelled error, `other-single`, `multiple`, or `unclear`.
2. **Skill:** one of the four, `none of these`, or `uncertain`.
3. **Mapping confidence:** 1 to 3.
4. **Change note:** an optional note if, on reflection, their stage-1 judgement now looks
   wrong. The stage-1 label itself is not edited.

**Freeze:** the stage-2 files are committed with hashes, as in stage 1.

### Stage 3: adjudication

- This stage starts after both stage-2 files are committed. The owner adjudicates the
  programs where the labellers' stage-2 categories differ, and the programs where either
  marked `unclear` or `multiple`.
- The owner sees both labellers' stage-1 and stage-2 labels and the author note.
- The owner does **not** see CodeAdapt output, because CodeAdapt has not been run yet.
- Adjudication goes in its own file, one row per program, with:
  - the adjudicated category;
  - the reason;
  - whether the author note was consulted.

  It is committed with a hash.
- A disagreement log (`disagreements.csv`) lists every program where the labellers
  differed at stage 1 (faulty statement), stage 2 (category or skill) or on correctness.
  It shows both raw values side by side.

### Stage 4: run CodeAdapt

- This stage starts only after stage 3 is committed.
- `codeadapt-eval` runs with 2 runs per program, on the pre-registered method version(s).
- Fix validity is checked at the same time. Claude applies each labeller's stage-1 minimal
  fix alone to the program, then runs the hidden tests and a randomised comparison with
  the reference, 500 inputs as in the critical review. Each fix is recorded as `valid`,
  `invalid` or `does-not-compile`.
- Labellers never see these results before the report.

## 5. Data and preservation

- **Files are append-only.** Each stage's files are stored as committed, and no later
  stage rewrites an earlier file.
- **Corrections are separate.** A transcription error is fixed in a separate
  `corrections.csv` that names the original value, not in place.
- **Confidence ratings and change notes are kept in the raw files.**
- **Personal data stays outside the repository.** The mapping from labeller and author
  codes to people is held only by the owner. Contact details, signed consent forms and
  that mapping are never committed and never shared with Claude
  (`val1b-materials/institutional-review.md` §3).

## 6. Metrics

All proportions are reported as counts with Wilson 95% intervals. All are reported pooled,
and per problem as descriptive results only.

### Primary (pre-registered; decisions in §8 depend only on these)

| ID | Metric | Definition |
| --- | --- | --- |
| P1 | **Open-ended agreement** | Among programs both labellers called `incorrect`: the fraction where they named the same faulty statement **and** both minimal fixes are `valid`. Statement-only agreement is reported alongside. |
| P2 | **Category agreement (stage 2)** | Cohen's κ and raw agreement between L1 and L2 on the stage-2 category. |
| P3 | **Skill agreement (stage 2)** | Cohen's κ and raw agreement on the skill. |
| P4 | **Named-diagnosis coverage** | `hypothesis_supported` divided by programs that both labellers called `incorrect`. |
| P5 | **Agreed-label precision** | Among unqualified named diagnoses on programs where L1 and L2 gave the **same** stage-2 category: the fraction where the model matches that category. This is a primary endpoint only if at least 12 such diagnoses exist (§7); otherwise it is reported as exploratory. |
| P6 | **False alarms on correct code** | Correct programs (both labellers `correct`, and every hidden test passes) given any named diagnosis or `non_termination_observed`. |

### Exploratory (reported, but no decision rests on them)

- Precision against **adjudicated** labels, which are not blind to the taxonomy.
- Qualified diagnoses: precision and count.
- Agreement with the **author's note**, a third, non-blind label source.
- `non_termination_observed` (if ADR-027 is adopted): how often both labellers' stage-1
  descriptions say the program does not finish on some inputs, and how often their fixes
  touch the loop update or condition.
- Abstentions by outcome, with the agreed or adjudicated label of each abstained program.
  This shows which human-identified errors the library misses.
- **Gap between P1 and P2.** A much higher open-ended than category agreement points at
  the taxonomy rather than the programs.
- Labeller confidence against agreement. Stage-2 change notes.
- Suite gap: programs labelled incorrect that pass every hidden test.
- Secondary method version: v1.1 if v1.2 is primary, and the difference between the two.
- Comparison with VAL1-A coverage and wrong-name rate.
- All per-problem breakdowns.

## 7. Sample size: what each size can resolve

These figures were computed with the same Wilson formula the reports use.

**Named diagnoses are the bottleneck.**

| Expected coverage | 60 programs | 100 programs |
| --- | --- | --- |
| About 10% (ADR-027 replay of VAL1-A under v1.2) | about 6 named diagnoses | about 10 |
| About 20% | 12 | 20 |
| About 33% (VAL1-A under v1.1, inflated by wrong termination names) | about 20 | 33 |

Only the subset of these where the labellers agree feeds P5.

**Precision resolution:**

- with 12 diagnoses all correct, the 95% lower bound is 76%;
- with 11 of 12 correct, it is 65%;
- with 6 of 6 correct, it is 61%.

Below about 12, no result can show adequate precision. So P5 is primary only when n ≥ 12.

**Kappa resolution:** at κ ≈ 0.64 with about 6 categories, the 95% half-width is about
±0.19 at n = 40, ±0.16 at n = 60 and ±0.12 at n = 100. A point estimate near 0.6 cannot
separate "adequate" from "poor" at n = 60. This is why §8 uses three-way outcomes.

**Recommendation.** Aim for 100 incorrect programs (5 authors). Accept 60 only knowing
two things:

- P5 will probably not be evaluable;
- the study then mainly answers whether humans agree on these errors, and how often the
  method names one.

That is still useful, but it is a narrower result. The owner decides the size.

## 8. Pre-registered decision rules (replacing v1 §8)

"Upper" and "lower" mean the bounds of the 95% interval. Each primary result is classed as
**below**, **inconclusive** or **adequate**. Inconclusive is reported as inconclusive, not
rounded up or down.

| ID | Below if | Adequate if | Consequence if below |
| --- | --- | --- | --- |
| S0 (P1) | upper < 60% | point ≥ 75% and lower ≥ 60% | Humans do not reliably identify the same error in these programs, even in their own words. No accuracy claim against human labels is interpretable. Report agreement only. |
| S1 (P2) | κ upper < 0.6 | κ ≥ 0.6 and lower ≥ 0.4 | CodeAdapt's categories are not reliably identifiable, even if S0 is adequate. Revise the categories before any diagnostic claim. |
| S2 (P3) | κ upper < 0.6 | κ ≥ 0.6 and lower ≥ 0.4 | The four-skill taxonomy is not reliably identifiable. Skill-level modelling (BKT) stays dormant, and skill evidence is redesigned around error patterns. |
| S3 (P5, n ≥ 12) | precision upper < 90% | lower ≥ 70% | Named diagnoses are not precise enough to show students. Show test-level feedback only, or tighten the rules, before any student use. |
| S4 (P4) | coverage upper < 20% | lower ≥ 20% | The library covers few independently written errors. Content expansion in its current form is not justified. |
| S5 (P6) | any false alarm | none | A blocking defect. Investigate before anything else. |

**Pass** means S0, S1, S2 and S4 are adequate, S3 is adequate or not evaluable (stated as
such), and there is no S5. Even then, a pass supports only the limited claim in §1. It does
not establish novice accuracy or learning. The next step would be RD1 (real data), and
content expansion becomes an owner decision.

**Any inconclusive primary result** means the report states the interval, and the next
step is more data (VAL1-C), not a stronger claim.

## 9. Pre-registration order

These items are committed **before** recruitment:

- this protocol (once approved);
- the frozen content versions and the method version(s);
- the analysis script, run on a dummy label set to prove it works;
- the labelling forms;
- the practice items.

The order after that is fixed:

1. programs are collected and committed;
2. stage 1 is committed;
3. stage 2 is committed;
4. adjudication is committed;
5. CodeAdapt runs;
6. the report is written.

## 10. Cost and timeline (estimate)

| Who | Effort |
| --- | --- |
| Authors | 2 to 3 hours each |
| Labellers | 4 to 6 hours each for 100 programs, longer than v1 because stage 1 asks for a description and a fix (3 to 4 hours for 60) |
| Owner | Recruitment, consent, the institutional query, collecting and committing files, adjudication |
| Claude | Forms, the analysis script and dummy-data test before recruitment; fix validation, evaluation and the report after the data arrives (1 to 2 days) |

## 11. Decisions needed from the owner

1. Approve v2, or amend it, including the sample size target (100) and minimum (60).
2. Approve or amend the participant materials, including the licence (CC0 suggested) and
   compensation.
3. Send the institutional-review questions and record the answer verbatim.
4. Confirm that the owner will adjudicate. A second, taxonomy-blind adjudicator would be
   better if one is available.
5. Decide whether VAL1-B waits for the ADR-027 decision. Recommended: yes, so that the
   primary method version is fixed before pre-registration.
