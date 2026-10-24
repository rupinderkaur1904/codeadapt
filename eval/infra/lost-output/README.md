# Lost-output probe (ADR-020, ADR-024)

Twice a sandbox run ended normally with its output missing on the host (CI on d4c218a and
d3919b0). ADR-024's end-of-output marker turns such a run into an infrastructure error, so
it can no longer become evidence, but the cause is unknown. This probe measures how often
it happens and which part of the stream path is involved.

`probe.py` runs a tiny deterministic program many times through the production
`DockerSandbox` and through three variants that each change one thing: the log driver
(`json-log`), the init process (`no-init`), and `docker create` + `docker start -a -i`
instead of `docker run -i` (`create-start`). Each lost run is recorded with which stream
lost its marker, both exit statuses and the wall time.

The `lost-output-probe` workflow runs it on GitHub-hosted runners, idle and with one busy
loop per core, three runners each. It is diagnostic only and never gates a merge.

Results are in [results.md](results.md) once measured. Nothing here changes content,
diagnosis, evidence rules or feedback.
