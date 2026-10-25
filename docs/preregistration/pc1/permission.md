# PC1 permission: what must be recorded before any CodeNet data is touched

The gate (`python scripts/pc1.py gate`) stays closed until `permission/record.json` exists and
passes every check below. `permission/record.template.json` shows the shape. Its `status` is
`TEMPLATE`, so it never opens the gate.

## Who writes it

The owner writes it, by hand, after receiving a written answer. Claude never creates or edits
`record.json` (`recorded_by` must be `owner`).

## What the approval must come from

One of the following, as `granted_by_role`:

- `supervisor`
- `institutional research-data office`
- `institutional ethics office`
- `dataset owner (IBM)`

**Not sufficient, and rejected by the gate as a `basis`:**

- the repository's Apache-2.0 LICENSE, whose scope over the data is unstated;
- a third party's description, such as CodeContests calling CodeNet "Apache 2.0";
- the absence of a stated restriction.

`basis` must be `explicit approval`.

## Fields

| Field | Required value |
| --- | --- |
| `record_version` | `1` |
| `status` | `granted` |
| `dataset` | `IBM Project CodeNet 1.0.0` |
| `granted_by_role` | One of the four roles above |
| `basis` | `explicit approval` |
| `decision_date` | Date of the written approval (YYYY-MM-DD), not after `recorded_on` |
| `recorded_on` | Date the owner wrote this record |
| `recorded_by` | `owner` |
| `evidence_reference` | Where the written approval is kept, such as "supervisor email of 2026-11-01, owner's records". At least 8 characters, no email addresses, no names. |
| `conditions_verbatim` | Every condition in the approval, quoted exactly, or `none` |
| `scope.download_full_archive` | `true`. IBM offers no metadata-only download, so the archive includes all source code. |
| `scope.store_outside_repository` | `true` |
| `scope.metadata_analysis` | `true` (Phase F) |
| `scope.source_code_analysis` | `true` only if Phase E is approved too. Phase E's gate level `code` requires it. |
| `scope.publish_derived_statistics` | Whether counts and rates may be committed and shared |
| `scope.publish_submission_ids` | Whether CodeNet submission ids may be committed |
| `scope.redistribute_code` | Must be `false`. PC1 never redistributes code. |

If the approval's conditions are narrower than a scope field, set that field to `false`. If a
condition cannot be expressed here, such as a retention period, quote it in
`conditions_verbatim` and tell Claude before any run.

## The question to ask

> May this project download IBM Project CodeNet 1.0.0 (a 7.8 GB archive of public submissions
> to AIZU Online Judge and AtCoder, including source code), store it outside the project
> repository, and use it for non-commercial research analysis?
>
> Phase 1 reads only submission metadata (anonymised user id, time, language and verdict) to
> count usable submissions. A later phase, if approved separately, would compile and test about
> 100 submitted programs for one problem in a sandbox.
>
> No source code is committed or redistributed. Only derived statistics, and only if you agree,
> anonymised submission ids are published.
>
> IBM publishes no dataset licence. The repository's Apache-2.0 licence does not say it covers
> the data.

## Second basis: the published dataset licence (amendment A1)

For an owner with no supervisor or institutional office, a version 2 record may use the licence
that the dataset provider publishes. It opens the `metadata` level only. See
`record-licence.template.json`.

| Field | Required value |
| --- | --- |
| `record_version` | `2` |
| `status` | `granted` |
| `basis` | `published dataset licence` |
| `licence_id` | `CDLA-Permissive-2.0` |
| `licence_text_sha256` | SHA-256 of `permission/licences/CDLA-Permissive-2.0.txt` |
| `licence_evidence` | A list. At least one entry must be by the `dataset provider` (IBM or the CodeNet authors), `seen: first-hand` by the owner, with a `quote` naming the licence. Each entry has `source`, `locator`, `publisher`, `seen`, `accessed_on`, `quote`. Third-party and secondary entries may be added, labelled as such. |
| `unverified` | What the owner could not check, such as "no current IBM distribution page found" |
| `known_risks` | Remaining uncertainty, such as upstream submission rights and pseudonymous ids |
| `self_imposed_conditions` | All true: `aggregate_outputs_only`, `no_reidentification`, `no_linkage_with_other_sources`, `no_source_code_access`, `no_redistribution`, `data_outside_repository` |
| `scope` | As for version 1, except `source_code_analysis` and `publish_submission_ids` must be `false` |

**What this basis claims, and does not.** It records that the owner relies on a licence the
provider reports. It is not an approval by anyone, and it is not legal advice. The licence says
nothing about privacy law or about the rights of the people who wrote the submissions; the
self-imposed conditions exist for those gaps.

## After it is recorded

Run `python scripts/pc1.py gate`. If it prints `gate open`, the commands in `README.md`
("After permission") may be run, one at a time, stopping at the Phase F gate.
