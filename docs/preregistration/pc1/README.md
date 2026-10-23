# PC1: public-corpus audit (CodeNet), Phase F tooling

Status on 2026-10-23: the protocol is frozen, and the scripts are tested on synthetic fixtures
only. **No CodeNet data has been downloaded or read. The permission gate is closed:** no
`permission/record.json` exists. No real-data result exists.

| File | What it is |
| --- | --- |
| `protocol.md` | Frozen protocol 1.0: questions, rules, outcomes, stop conditions, limitations |
| `permission.md` | Exactly what the owner must record before anything touches CodeNet |
| `permission/record.template.json` | Shape of the record. Its `status` is `TEMPLATE`, so it never opens the gate |
| `scripts/pc1.py` | Gate, extract, identify, confirm and feasibility (standard library, metadata only) |
| `scripts/make_fixtures.py` | Writes the synthetic fixtures deterministically |
| `fixtures/synthetic-basic/` | Invented data with a `SYNTHETIC-FIXTURE-NOT-REAL-DATA` marker. `expected.json` holds hand-computed counts |
| `MANIFEST.sha256` | Hashes of the frozen files |
| `../../../backend/tests/unit/test_pc1_feasibility.py` | 31 tests, run in CI |

## Run the checks (no permission needed, synthetic only)

From the repository root:

```bash
cd backend && uv run pytest tests/unit/test_pc1_feasibility.py -q && cd ..

# The whole pipeline on the fixtures (outputs go to a temporary directory):
P=docs/preregistration/pc1/scripts/pc1.py
F=docs/preregistration/pc1/fixtures/synthetic-basic
O=$(mktemp -d)
python3 $P identify --data-dir $F --out $O --synthetic-fixtures
python3 $P confirm --identification $O/identification.json --candidate ALDS1_4_B \
    --problem p99001 --role synthetic-fixture
python3 $P feasibility --data-dir $F --identification $O/identification.json --out $O \
    --synthetic-fixtures
cat $O/feasibility.md

# Regenerate the fixtures (byte-identical; a test checks this):
python3 docs/preregistration/pc1/scripts/make_fixtures.py

# The gate, which is closed today (exit code 3):
python3 $P gate
```

The tests cover:

- metadata parsing, schema checks, and missing or extra cells;
- problem identification, including absent, ambiguous and non-AIZU cases, and human
  confirmation rules;
- C++ and status filtering;
- same-user pairing, with ties, rejections after the accept, never-accepted users, long gaps and
  language-version changes;
- exact and conflicting duplicates, and count reconciliation;
- stop conditions and the fallback order;
- byte-identical reruns;
- the permission gate (11 refusal cases);
- refusal of real-data commands without permission;
- separation of fixtures from real data;
- safe extraction (metadata and descriptions only, with no links, `..` or code).

## After permission: the exact commands

Run these only after `permission/record.json` has been written by the owner (see
`permission.md`). Run one at a time, and stop after step 7.

The network must reach `codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud`. This
project's default cloud environment blocks it. Use a cloud environment that allows that host, or
run the commands on your own computer.

```bash
set -euo pipefail
P=docs/preregistration/pc1/scripts/pc1.py
export PC1_DATA="$HOME/pc1-data"   # outside the repository (the script refuses otherwise)
export PC1_OUT="$HOME/pc1-out"     # outside the repository
mkdir -p "$PC1_OUT"

# 1. The gate must print "gate open for level 'metadata'".
python3 $P gate

# 2. Stream the archive and keep only metadata/ and problem_descriptions/.
#    The 7.8 GB archive is not stored. The output records its SHA-256 and size.
curl -fL https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-project-codenet/1.0.0/Project_CodeNet.tar.gz \
  | python3 $P extract --archive - --data-dir "$PC1_DATA" > "$PC1_OUT/extract.json"

# 3. Shortlist ALDS1_4_B and ALDS1_4_D (nothing is chosen automatically).
python3 $P identify --data-dir "$PC1_DATA" --out "$PC1_OUT"

# 4. A person reads each shortlisted statement (problem ids are in identification.json):
sed 's/<[^>]*>/ /g' "$PC1_DATA/Project_CodeNet/problem_descriptions/pNNNNN.html"

# 5. If it matches the task in protocol section 5, record the confirmation
#    (role: owner or supervisor). If none match, confirm nothing.
python3 $P confirm --identification "$PC1_OUT/identification.json" \
    --candidate ALDS1_4_B --problem pNNNNN --role owner

# 6. Count, pair and reconcile. Exit code 4 means a stop condition fired; read the report.
python3 $P feasibility --data-dir "$PC1_DATA" \
    --identification "$PC1_OUT/identification.json" --out "$PC1_OUT"

# 7. Stop. Share $PC1_OUT/feasibility.md with the owner. Commit counts only if the
#    permission's scope.publish_derived_statistics is true. Phase E needs its own approval.
```

If step 3 says `not_present` or `ambiguous` for ALDS1_4_B, step 5 confirms ALDS1_4_D instead,
under the same rule. No other problem is substituted. The fallback is counted only when
ALDS1_4_B is absent or below 60 pairs.
