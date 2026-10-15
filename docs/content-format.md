# Problem content format

A problem is a directory whose name equals its `slug`, containing `problem.toml` and the
files it references. The demo catalogue is `content/demo/` (public, **not secret**, see
ADR-009). Real study content uses the same format in a private repository.

```
lower-bound/
  problem.toml          definition (below)
  statement.md          student-facing statement
  harness.cpp           PRIVATE: reads one test input, calls the student's function, prints the result
  reference.cpp         PRIVATE: correct implementation
  error_models/*.cpp    PRIVATE: one known-buggy implementation per error model
```

## `problem.toml`

| Key | Meaning |
| --- | --- |
| `slug`, `title`, `family` | identifiers; `family` groups problems for adaptation (M6) |
| `statement`, `harness`, `reference` | relative paths (no `..`, must stay inside the directory) |
| `solution_file` | name the student's code is compiled under, next to `harness.cpp` |
| `interface` | the function signature the student implements (shown to students) |
| `[skills]` | `key = "description"`: skills that error models and probes refer to |
| `[probes]` | `key = ["skill", …]`: input properties a test exercises, and the skills whose errors they can expose. A modelling assumption, recorded so it can be questioned. |
| `[curriculum]` | optional links by slug: `prerequisites`, `equivalents`, `transfer`, plus `assumes` (prior knowledge, in words). Every slug must name a problem in the same catalogue, and never the problem itself. |
| `[[tests]]` | `key`, `input` (stdin for the harness), `expected` (author's expected stdout), `probes`, `visibility` (`sample` or `hidden`, default hidden), `student_description` (the only thing students may see about a hidden test), and the design record: `purpose` (why the test exists) and `distinguishes` (the error models it is meant to separate from the reference, checked against the measurement) |
| `[[error_models]]` | `key`, `file`, `skill`, `description` (researcher-facing), `student_hint` (shown only after a supported diagnosis), optional `known_limitation` (a documented, accepted weakness such as a known collision) |

The loader rejects unknown keys, unknown probe/skill/model references, duplicate keys,
unsafe paths (including symlinks that escape the directory), and definitions without a
sample test. `purpose`, `distinguishes` and `known_limitation` are researcher-facing and
never reach students.

## Version

`LoadedProblem.version` is a SHA-256 over `problem.toml` and every referenced file.
Changing any of them produces a new version; files that are not referenced do not count.
All evidence records reference the version they were produced against.

## Validation (`codeadapt-content validate <dir>`)

The validator **executes** the reference and every error model on every test in the
sandbox (each test twice by default), then checks:

* errors (content unusable): a program fails to compile; the reference disagrees with an
  authored `expected`; any program is non-deterministic on a test; an infrastructure
  error; an error model behaves exactly like the reference on every test;
* errors (CE0): a test's declared `distinguishes` differs from the set of models the
  measurement shows it separating from the reference;
* warnings (accepted limits that the diagnosis will surface as abstentions): an error
  model detected by fewer than 2 tests; two error models with identical fingerprints; an
  error model whose detecting tests form fewer than 2 *behaviour groups*, unless it has a
  `known_limitation` (then it is listed as a documented limitation); a test without a
  declared `distinguishes`; a test that separates no model and states no `purpose`.

A *behaviour group* is a set of tests that every modelled program passes together or fails
together. Groups are measured, and relative to the models that exist: adding a model can
split a group.

It prints a tests × programs matrix of observed outcome signatures (`=` means "same as the
reference"), each model's detecting tests, each pair's distinguishing tests and the
behaviour groups, and can write everything as JSON with `--json`.

`codeadapt-content report <dir> --out <dir>` runs the same validation and writes one
Markdown report per problem (matrix, models with group counts, groups, pairs, declared
versus measured intent, errors, warnings, limitations). Reports have no timestamps, so a
regenerated report is byte-identical unless the content or its measurement changed. They
contain hidden tests and model descriptions: for private content, write them to the
private repository. The demo bank's reports are in `docs/content-reports/`.

## Authoring checklist

1. Write the reference and the `expected` value of every test first.
2. Write each error model as the *smallest* realistic change that produces the error.
3. Add tests until every model is detected by ≥ 2 tests in ≥ 2 behaviour groups and every
   pair is separable. Where that is impossible, record why in `known_limitation`.
4. Declare each test's `purpose` and `distinguishes`, and let validation check them.
5. Avoid error models whose behaviour is undefined (out-of-bounds reads, signed overflow):
   their outputs are not reproducible. These belong to the sanitiser channel (M5).
