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
| `[[tests]]` | `key`, `input` (stdin for the harness), `expected` (author's expected stdout), `probes`, `visibility` (`sample` or `hidden`, default hidden), `student_description` (the only thing students may see about a hidden test) |
| `[[error_models]]` | `key`, `file`, `skill`, `description` (researcher-facing), `student_hint` (shown only after a supported diagnosis) |

The loader rejects unknown keys, unknown probe/skill references, duplicate keys, unsafe
paths (including symlinks that escape the directory), and definitions without a sample test.

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
* warnings (accepted limits that the diagnosis will surface as abstentions): an error
  model detected by fewer than 2 tests; two error models with identical fingerprints.

It prints a tests × programs matrix of observed outcome signatures (`=` means "same as the
reference"), each model's detecting tests and each pair's distinguishing tests, and can
write everything as JSON with `--json`.

## Authoring checklist

1. Write the reference and the `expected` value of every test first.
2. Write each error model as the *smallest* realistic change that produces the error.
3. Add tests until every model is detected by ≥ 2 tests and every pair is separable.
4. Avoid error models whose behaviour is undefined (out-of-bounds reads, signed overflow):
   their outputs are not reproducible. These belong to the sanitiser channel (M5).
