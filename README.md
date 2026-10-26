# CodeAdapt

CodeAdapt is an evidence-driven, adaptive C++ learning and diagnostic platform. Most
coding platforms only say whether a submission passed. CodeAdapt runs a submission
against diagnostic tests in a sandbox, records what it observed, works out which known
implementation errors the evidence supports (and abstains when it supports none of them),
recommends a targeted follow-up exercise, and then uses the next attempt as new evidence.

```
Submission → Execution evidence → Interpretable diagnosis → Targeted practice → New evidence → Adaptation
```

Observed behaviour is not a student's cognitive state. The system keeps observations,
inferences and learning outcomes separate, and every piece of feedback can be traced back
to the evidence behind it.

## Status

| Milestone | State |
| --- | --- |
| M0 Repository foundation | done |
| M1 Sandboxed execution core | done (dev isolation tier: Docker + runc) |
| M2 Content model + first diagnostic problem | done |
| M3 Backend vertical slice (API, worker, diagnosis v1) | done |
| M4 Student workspace (browser UI) | done |
| M5 Evidence reliability (sanitiser, repeat runs) | done |
| M6 Adaptive follow-up exercises | done |
| M7 Researcher console + synthetic evaluation harness | done |
| CE0 Content-design method, tooling, review resolution | done |
| M8 Auth, gVisor isolation, Postgres, deployment | in progress: auth, gVisor (CI), PostgreSQL (CI) done; not deployed |

There is a working student workspace in the browser, an HTTP API and a sandboxed worker. The full plan is in [docs/roadmap.md](docs/roadmap.md).
**Do not deploy CodeAdapt where students can reach it** until milestone M8 (production
isolation tier) is complete. See [docs/security.md](docs/security.md).

## Documentation

| Document | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | objective, stack, components, workflow, data model, API, risks |
| [docs/security.md](docs/security.md) | threat model, sandbox design, verified guarantees, limitations |
| [docs/methodology.md](docs/methodology.md) | diagnostic method, adaptation policy, evaluation plan |
| [docs/roadmap.md](docs/roadmap.md) | milestones with acceptance criteria |
| [docs/decisions.md](docs/decisions.md) | architecture decision log |
| [docs/content-format.md](docs/content-format.md) | how problems, tests and error models are authored and validated |
| [docs/content-design/](docs/content-design/README.md) | how problems are designed for diagnosis; worked example (lower-bound); content-expansion milestone |
| [docs/evaluation/](docs/evaluation/synthetic-2026-10-15.md) | synthetic evaluation reports (not evidence about real students) |
| [docs/development.md](docs/development.md) | setup, commands, tested environment |
| [docs/release-2026-10-26.md](docs/release-2026-10-26.md) | engineering release report: what is tested, provisional, synthetic and open |
| [docs/status-2026-10-24.md](docs/status-2026-10-24.md) | verified project status: tested, untested, proposed, blocked |
| [docs/evaluation/summary.md](docs/evaluation/summary.md) | one-page labelled results (synthetic and author-written only) |
| [docs/demo.md](docs/demo.md) | demo workflow with observed output |
| [docs/limitations.md](docs/limitations.md) | limitations and future work |
| [docs/research-report-draft.md](docs/research-report-draft.md) | research report draft (evidence-supported claims only) |
| [docs/interview-prep.md](docs/interview-prep.md) | how to explain the design, algorithms, trade-offs and evaluation |
| [PROJECT_AUTOPILOT.md](PROJECT_AUTOPILOT.md) | completion plan and progress log |

## Quick start

With Docker only (development stack, never expose it publicly):

```bash
docker compose up --build        # then open http://localhost:5173
```

To demo the real login page instead of the development role switch, add the demo file. It
creates `demo-student` and `demo-researcher` (passwords in `compose.demo.yaml`; local use only):

```bash
docker compose -f compose.yaml -f compose.demo.yaml up --build
```

For development without compose (Docker, [uv](https://docs.astral.sh/uv/), Node 22):

```bash
docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/
cd backend
uv sync
uv run pytest                      # unit + sandbox tests
uv run codeadapt-run main.cpp --input input.txt
```

Details, including Windows/macOS notes, are in [docs/development.md](docs/development.md).
