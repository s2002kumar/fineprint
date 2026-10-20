> **Point-in-time record (DST-00 feasibility gate, 2026-10-19).** Kept for the audit trail of the pre-registered workflow. Counts, test totals and file paths reflect that stage; current results are in the README and `docs/`.

# fineprint DST-00 feasibility report — 2026-10-19

**Decisions: national ingest = GO · historical evaluation = NARROW** (target evidence and site
identity pass; frame completeness unproven). Every number below is from a run recorded in
`evidence/dst00/*.json`; full URLs, SHA-256s and dates are in `evidence/dst00/source_manifest.json`.
Machine: Windows 11, Python 3.14.5 (stdlib only), 22 logical CPUs, 16 GB RAM.

## 1. Five archived Rocky Mount targets: all pass
Each was fetched with `getFile.cfm?type=zip&setid=…&version=…`. The served XML `setId`/`versionNumber` equals the
request, and each version is the **latest published on or before 2023-07-18** (DailyMed history service). A re-fetch was byte-identical (11/11 ZIPs).

| Target (set ID) | Ver | Published | XML effTime | ZIP SHA-256 | `MANUFACTURE` (C43360) at DUNS 093132819 |
|---|---|---|---|---|---|
| acetylcysteine `5558a5f5` | 19 | 2020-09-01 | 20200831 | `37cb7fcf…` | 0409-3307, 0409-3308 |
| aminocaproic acid `1c5bc1dd` | 17 | 2022-11-30 | 20221129 | `fb26d263…` | 0409-4346 |
| aminophylline `9a663ef3` | 26 | 2022-12-02 | 20221129 | `5e900b27…` | 0409-5921, 0409-5922 |
| atropine `ad8916e7` | 25 | 2021-08-09 | 20210805 | `13190564…` | 0409-1630, -4910, -4911, -9630 |
| calcium chloride `c4c65e48` | 18 | 2023-06-06 | 20230531 | `2d68adad…` | 0409-1631, 0409-4928 |

Every edge cites an indexed XPath (`/document/author[1]/…/performance[n]`); a test resolves each one against
the raw XML. Aminophylline v27 (published 2023-08-28) is correctly excluded. The labels also show cases the model must keep apart:
- Hospira labeler `141588017` (a company, not a facility).
- `827731089` (Lake Forest IL HQ address) with **ANALYSIS only**.
- Rolabo `513603225` with **API MANUFACTURE (C82401)**, which is not finished-product `MANUFACTURE`.
- `PACK`/`LABEL` coded separately.

**McPherson controls** (rule fixed in `config/dst00_targets.json`: every `drug_name∈{naloxone, diazepam}` and
`labeler=Hospira` set ID, latest admissible version):
- **McPherson manufacture, admissible:** naloxone `b598c237` v23 (2023-06-07) has `MANUFACTURE` at `030606222` for 0409-1782; diazepam `41044928` v17 (2023-05-08) has it for 0409-1273.
- **Same drug names, made at Rocky Mount:** naloxone `8535cc84` v30 and diazepam `7e7dd743` v24. In the diazepam label McPherson appears only as **ANALYSIS**.

Site membership is product-level, not drug-name-level.

## 2. Pre-event DUNS ↔ FEI ↔ physical-site identity
| Evidence (dated) | Rocky Mount 093132819 ↔ 1021343 | McPherson 030606222 ↔ 1925262 |
|---|---|---|
| Facility-identification SPL `f435e79d` v5 (pub. 2013-05-29) and v7 (pub. 2015-05-22), raw XML | ✅ "Highway 301 North, Rocky Mount, NC 27801" | not listed |
| FDA DECRS `drls_reg.zip`, Internet Archive capture 2022-10-14 (FDA member mtime 2022-10-13; CDX SHA-1 digest matches) | ✅ exact pair; ops ANALYSIS, LABEL, MANUFACTURE, PACK, RELABEL, REPACK | ✅ exact pair; "1776 North Centennial Drive, McPherson, KS 67460" |
| FDA BLA 125545 review PDF (Last-Modified 2018-12-13), p.315 text layer | — | FEI↔address only. **DUNS not present.** The establishment tables (pp.79–80, 207–208) are redacted images. |
| *Current* DECRS 2026-10-19 (identity_current; not 2023 evidence) | same pair | same pair |

**Discrepancy with the research log.** The log cites the 2018 PDF as proof of `030606222`/`1925262`; it proves only the FEI. The pairing instead rests on the 2022 archived DECRS copy, a third-party archive of an FDA file. **Gap:** both 2022 registrations expire 12/31/2022, and no pre-event source dated Jan–Jul 2023 was found.

## 3. National bulk release (current, 2026-10-16), bounded
- **Manifest:** 6 parts were discovered from the live page. Central directories of **all 6** were read by HTTP Range. Observed members equal advertised for every part: **55,064**. Content-Length totals **17,979,089,637 bytes**. Only part 6 was downloaded. This is the official manifest, not an import.
- **Shard (part 6), full:**
  - Download: 1,875,296,318 bytes, **MD5 = advertised**, SHA-256 `7708d214…`, 7.43 MB/s.
  - Streaming: 4,311/4,311 parsed, **0 failures, 0 anomalies**.
  - Runs: 66.3 s cold / 45.0 s warm cache (65–96 docs/s), peak RSS 60.5–72.8 MB.
  - **Caveat:** parts are ordered by label date, and every part-6 member is dated 2026, so it is a recency slice.
- **Cross-part sample:** 25 members per part from a SHA-256-seeded ranking (`fineprint-dst00`), 150 in total, member dates 2010–2026. All 150 parsed.

| Observed category (counts describe these documents only) | Part 6 | Sample (150) |
|---|---|---|
| Docs with no establishment block (e.g. repackagers) | 1,979 / 4,311 | 36 / 150 |
| Docs with ≥1 `MANUFACTURE` edge to a DUNS | 1,146 | 40 |
| Products with a `MANUFACTURE` DUNS | 2,569 / 7,498 | 73 / 200 |
| Packages without an NDC code | 3,067 / 19,936 | 78 / 523 |
| Operation edges / without product scope | 10,820 / 0 | 339 / 6 (4 docs, 2010–11) |
| Establishments carrying FEI or address *in drug labels* | 0 | 0 |
| Distinct MANUFACTURE DUNS → found in **current** DECRS (with FEI) | 550 → 548 (547) | 43 → 40 (40) |

Operation display names vary in case and trailing spaces for every code (e.g. `MANUFACTURE`, `manufacture`,
`MANUFACTURE `), so operations are keyed by **NCI code**. 106 part-6 DUNS appear as both labeler and
establishment, so role must be judged per assertion, never per DUNS. Labels carry no FEI or address, so all physical
identity must come from registration sources. Current DECRS has 264 FEIs with more than one DUNS: an ambiguity to carry, not to collapse.

## 4. Historical candidate frame (pre-registered before discovery)
The method, `docs/historical_panel_plan.md`, was committed (`5179eb9`) **before** the pilot ran. The outcome appendix is **sealed and was never fetched**. Pilot results (§8 of the plan; set-ID and listing level only, no frame frozen):
- **A — DailyMed `labeler=Hospira`:** 200 set IDs (no result cap; a Teva query returns 304). **189** have an admissible version and 11 were first published after the cutoff.
- **D — NDC Directory archived 2023-05-07** (FDA mtime 2023-05-05, digest verified): **477** `0409` package NDCs, 339 product NDCs, **213** distinct SPL document IDs. All are human Rx; none ended marketing by the cutoff.
- **D lists 213 SPL documents versus 189 admissible set IDs in A.** That is a survivorship-gap signal; document-ID → set-ID mapping is needed to size it. DailyMed still hosts the Jun 2023 (2.77 GB) and Jul 2023 (3.11 GB) monthly archives, which were not downloaded.
- **B3 is NOT EVALUABLE** for now: no dated, package-level, pre-cutoff shortage source has been identified.

## 5. Decisions and conditions
- **National ingest — GO.** Downloads, checksums, range access, safe streaming and bounded memory all work on real bytes. DST-01 must:
  - fetch the remaining ~16.1 GB **outside OneDrive** with resume, SHA-256 and MD5;
  - key operations by code;
  - report docs with no establishment block as UNKNOWN, not absent;
  - treat DECRS resolution as current-only.
- **Historical evaluation — NARROW.** Targets, controls and site identity are admissible and verified. **The frame is not yet defensibly complete.** Before DST-04 scoring:
  1. the researcher requests DailyMed's all-labels export for 2023-07-18 via customer support (email required);
  2. A∪D reconciliation quantifies uncovered packages;
  3. results carry an incomplete-frame caveat unless that export arrives.

  The Jan–Jul 2023 identity gap is disclosed, not closed.

**Not done in DST-00:** no Postgres or schema, no ingest of parts 1–5, no package-level frame freeze, no outcome
retrieval, no national rates (the part-6 and sample counts above are not extrapolated).
