# PC1 deviations (protocol section 11)

Protocol section 11 says that a deviation discovered during a run is reported and not silently
fixed. This file lists them. The frozen files (`MANIFEST.sha256`) are unchanged.

| Id | Date | What happened | Effect |
| --- | --- | --- | --- |
| D1 | 2026-10-23 | The full archive (8,343,137,473 bytes, SHA-256 `7e96620307f874269a62cc0225f2a5a13d2de2b3c368cf61319c87ec276620fb`) was downloaded, outside the repository, at the owner's request, before any permission record existed. | Nothing was extracted or read until the gate opened. |
| D2 | 2026-10-23 | `extract` (metadata and problem descriptions only: 8,053 files kept, 14,020,249 skipped) and `identify` ran while the gate was open on record 447757a, whose claim of supervisor approval was untrue (see `permission/CORRECTIONS.md`). | The identification output (ALDS1_4_B shortlist of 16; p02268 is the only statement matching section 5) exists outside the repository. The candidate was **not** confirmed. No count, pairing or source-code read happened. |
| D3 | 2026-10-23 | Before confirmation, `wc -l` was run on `metadata/p02268.csv` and `metadata/p02270.csv`. Section 5 forbids reading per-problem files before confirmation. | Line counts only (unfiltered, including headers); no row content was printed. The problem-identity reasoning used statement text only. |

The outputs of D1 and D2 live only in a temporary cloud machine, outside the repository, and are
not committed anywhere.
