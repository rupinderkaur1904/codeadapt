# PC1 synthetic fixtures

Everything under `synthetic-basic/` was invented by `../scripts/make_fixtures.py`. None of it
comes from CodeNet. The marker file `SYNTHETIC-FIXTURE-NOT-REAL-DATA` makes `pc1.py` refuse
these files in real mode. Real data is refused here.

All ids are invented:

- problems `p99001`–`p99004`;
- users `u9000*`;
- submissions `s9000*`.

`p99001` is a stand-in for ALDS1_4_B. It holds 326 rows:

- 200 filler users: 100 who fail and then pass, and 100 who pass first time;
- one user for each pairing rule (`make_fixtures.binary_search_rows`);
- an exact duplicate row and a conflicting duplicate pair;
- three malformed rows: a missing user id, a bad date, and the wrong problem id.

The counts in `synthetic-basic/expected.json` were computed by hand from that list. The tests
check the scripts against them:

- 104 primary pairs and 105 secondary pairs;
- 207 users with an accept;
- the rest as listed in the file.

`p99002` (Allocation) and `p99003`/`p99004` exist only for the identification tests.
