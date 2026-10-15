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
| M4 Student workspace (frontend) | next |

There is an HTTP API and a worker, but no browser UI yet. The full plan is in [docs/roadmap.md](docs/roadmap.md).
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
| [docs/development.md](docs/development.md) | setup, commands, tested environment |

## Quick start

Requirements: Docker, [uv](https://docs.astral.sh/uv/), Python 3.12+.

```bash
docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/
cd backend
uv sync
uv run pytest                      # unit + sandbox tests
uv run codeadapt-run main.cpp --input input.txt
```

Details, including Windows/macOS notes, are in [docs/development.md](docs/development.md).
