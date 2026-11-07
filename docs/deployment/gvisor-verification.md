# gVisor verification levels (M3.4)

Student C++ must run under gVisor (`runsc`) in any deployment students can reach
(ADR-003, ADR-028, ADR-040). Evidence for that comes from three different places, and they
are **not interchangeable**. A result at one level never stands in for another.

| Level | Where | What it shows | Status (2026-11-07) |
| --- | --- | --- | --- |
| **L1: CI** | GitHub Actions `sandbox-gvisor` (6 shards), pinned gVisor release 20261005 with checksum, `runsc install`, Docker restarted | The full sandbox suite (isolation, limits, classification, end-to-end pipeline) passes under `runsc` on a GitHub-hosted Ubuntu 24.04 VM. The core shard also checks that the production worker refuses runc and unregistered runtimes (ADR-040). | **PASS** on `main` `eff4dc7` (all 18 checks green) |
| **L2: Local or container** | A developer machine or this cloud container | The code paths and refusals work. It says nothing about the host kernel, Docker version or network policy of the deployment host. | Production-worker refusals verified by hand under runc (Milestone 2). gVisor itself was not run here. |
| **L3: Deployment host** | The actual runner VM chosen at Gate A | gVisor is installed, registered and enforced **on the machine that will run student code**, with that VM's kernel, Docker, egress firewall and limits. | **NOT VERIFIED.** No host exists. Blocked on owner Gate A (choice) and Gate B (provisioning). |

Only L3 counts as "gVisor is operational for the pilot".

## L3 procedure (run on the runner VM after Gate B)

Record every command's output in `docs/deployment/host-verification-<date>.md`. Do not
summarise from memory.

1. **Versions.** `uname -a`, `docker version`, `runsc --version`. Use the same pinned
   gVisor release as CI, installed with its checksum verified.
2. **Registration.** `docker info --format '{{json .Runtimes}}'` lists `runsc`.
3. **The worker refuses to run without it.** With `CODEADAPT_SANDBOX_RUNTIME` unset,
   `docker compose -f deploy/compose.runner.yaml run --rm worker` must exit non-zero with
   the `runsc` message. Restore the setting afterwards.
4. **Containers really run under gVisor.**
   `docker run --rm --runtime runsc codeadapt-sandbox:gcc14.2-1 dmesg` prints gVisor's
   own boot messages ("Starting gVisor..."), not the host kernel's.
5. **Sandbox suite on the host.** Run this from a checkout on the runner VM; it needs the
   dev dependencies, which is acceptable for a one-off gate:
   `CODEADAPT_SANDBOX_RUNTIME=runsc CODEADAPT_REQUIRE_SANDBOX=1 uv run pytest tests/sandbox`.
   All tests pass with none skipped.
6. **Egress is blocked.** From the runner VM, a request to any outside host fails, while
   a connection to the database's private address on port 5432 succeeds. Sandbox
   containers already run with `--network none`, and the suite checks that.
7. **End-to-end.** Through the public site, a test account submits the lower-bound
   reference solution and gets "all tests passed". The diagnosis trace's environment
   shows `container_runtime: runsc`.

If any step fails, the pilot does not start (Gate B stays closed).
