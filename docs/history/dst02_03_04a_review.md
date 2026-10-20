> **Point-in-time record (DST-02/03/04A combined gate, 2026-10-20).** Kept for the audit trail of the pre-registered workflow. Counts, test totals and file paths reflect that stage; current results are in the README and `docs/`.

# fineprint — combined review: DST-02, DST-03, DST-04A (2026-10-20)

**Stopped at the gate.** DST-04B, refresh automation, ML and public release were not started.
Everything is on local branch `dst-02-03-04a`, which is stacked on `dst-01` → `dst-00`; nothing is pushed.

## 1. What shipped
| Card | Delivered |
|---|---|
| DST-02 | `migrations/002` (additive); dated registration loader; canonical-version selection; DUNS→FEI→address identity with STALE/NO_FEI/EXCLUDED/NOT_FOUND states; deterministic `operation_edge` projection (one atomic transaction, rebuild-idempotent) |
| DST-03 | `scripts/fp.py` CLI: `product`, `facility` (DUNS or `FEI:`), `labeler`, `compare`, `search`, `evidence [--raw]`, `coverage`, `unresolved`, each with `--json`. Every answer starts with a scope line (release 2026-10-16, registration 2026-10-19) and states it is not a historical state |
| DST-04A | Draft, **unfrozen** historical candidate universe and coverage under plan amendments A4–A4.2, each committed before its run; historical source manifest. No outcome access, no Rocky Mount classification |
| Security | Read-only full-history audit (`scripts/audit_git_history.py`); repo guards for contacts and home paths now cover the markdown docs |

## 2. Schema and relationship design
- **Separation.**
  - DST-01 tables are untouched; their fingerprint is verified equal after every build.
  - Historical work stays file-based under `evidence/historical/` and never enters `national`.
- **`set_version_selection`.** One row per set (`lower(set_id)`); all raw versions stay in `spl_document`.
  - Rule: use the official zip-metadata version when it is present in the release, otherwise the highest version.
  - Selection classes:
    - `confirmed`: metadata names the selected version.
    - `unconfirmed`: one version in the release, set not in the metadata.
    - `ambiguous`: the metadata names a version absent from the release, or several versions exist and no metadata.
    - `unresolved`: two different files share the same version; no document is chosen.
  - `published_date` comes **only** from metadata `UPLOAD_DATE`.
- **`registration_record`** holds FDA DECRS rows with **no contact columns**; they are dropped at parse time.
  - Snapshots loaded: current `drls_reg` and `drls_excluded` (FDA-generated 2026-10-19), plus archived copies chosen by a fixed rule: the latest capture per year, which gave 2024-12-23, 2025-12-05 and 2026-08-21. Every archive digest was verified.
- **`duns_identity`.** Status order: `CURRENT_REGISTERED` (with FEI) › `CURRENT_REGISTERED_NO_FEI` › `CURRENT_EXCLUDED` › `STALE_REGISTERED` (older snapshot only) › `NOT_FOUND`. It also records:
  - FEI history across snapshots, with a `fei_changed` flag;
  - how many DUNS share the FEI;
  - SPL name variants, kept for display only and **never used to match**.
- **`operation_edge`.** product → operation (NCI code) → DUNS → FEI, keyed by the DST-01 `assertion_pk`, so evidence IDs stay stable across rebuilds.
  - **DIRECT**: product-scoped, current registration with FEI, not expired, FEI unchanged, version selection not ambiguous.
  - **TENTATIVE**: partial or stale identity, or an ambiguous version.
  - **UNKNOWN**: no registration evidence, no DUNS, or the operation is not tied to a product.
  - The SQL is tested **equal** to the pure Python rule `graph.edge_confidence` on every edge.
  - Judgement calls to review: (a) `unconfirmed` selections are *not* downgraded; they back 306 DIRECT products. (b) A registration without an FEI counts as TENTATIVE.

## 3. Current graph coverage (build 6, clean commit `e5466dd`)
**Denominators:** 55,064 documents in the release → 52,747 sets → 52,747 canonical documents → 80,508 products (kit parts roll up to their kit).

| Products by manufacturing status | Count | % |
|---|---|---|
| DIRECT | 24,614 | 30.6 |
| TENTATIVE | 435 | 0.5 |
| UNKNOWN site (MANUFACTURE to an unregistered DUNS) | 1,002 | 1.2 |
| No MANUFACTURE evidence (other operations only 28,123 · no establishment block 18,453 · unscoped operations only 7,762 · not for this product 119) | 54,457 | 67.6 |

- **Sets:** 12,477 of 52,747 (23.7%) have a DIRECT manufacture edge; 14,500 have any manufacture edge.
- **Facility resolution, over the 3,333 MANUFACTURE DUNS:**

  | Status | DUNS | % |
  |---|---|---|
  | Currently registered with FEI | 2,562 | 76.9 |
  | Not found in any snapshot | 656 | 19.7 |
  | Stale | 109 | 3.3 |
  | Registered without FEI | 6 | 0.2 |

  - Facilities: 3,444 FEI, of which 3,300 are currently registered.
  - 73 FEI are shared by more than one DUNS, and 45 DUNS changed FEI across snapshots.
- **MANUFACTURE edges:**
  - DIRECT 30,015
  - TENTATIVE 553: stale 400, FEI changed 86, ambiguous version 55, no FEI 12
  - UNKNOWN 3,008: unscoped 1,824, not found 1,184

## 4. Five real query examples (verbatim in `evidence/dst03/examples.txt`)
1. **`product 0409-4346`** (aminocaproic acid, set `1c5bc1dd` v20, published 2026-05-04) has DIRECT MANUFACTURE at two sites:
   - `093132819`, FEI 1021343, Highway 301 North, Rocky Mount NC [evidence 105515];
   - `860037912`, FEI 3008316085, Pfizer Healthcare India [105517].

   PACK, LABEL and ANALYSIS are listed separately. *Current only:* DST-00's 2022 version listed only Rocky Mount.
2. **`compare 093132819 030606222 --labeler 141588017`**: among Hospira-labeled products, 144 are made only at Rocky Mount (e.g. ondansetron 00409-0009), 62 only at McPherson (e.g. midazolam 00409-0001) and 27 at both (e.g. Precedex 00409-0155). These totals match `labeler 141588017` (171 and 89).
3. **`search naloxone`** lists products one by one with an explicit name warning. Hospira `00409-1215` and `-1219` (set `8535cc84`) are DIRECT at Rocky Mount; `00409-1782` (set `b598c237`) is DIRECT at McPherson. Same name, different sites, never merged.
4. **`facility 080105003`** (Sincerus Florida) is `NOT_FOUND` in every registration snapshot. It is the *labeler* on 204 labels and claims MANUFACTURE for 203 products; all 203 stay **UNKNOWN**, never presented as a known factory. The SPL spells its name 9 different ways.
5. **`evidence 105515 --raw`** traces the full chain:
   - part-5 SHA-256 `d9c41cbf…` (retrieved 2026-10-19), then member and XML SHA-256s;
   - the XPath `…/assignedEntity[1]/performance[3]`, re-read from the original archive with hashes verified, which prints the `<code code="C43360"…>` / `0409-4346` element verbatim;
   - DECRS file SHA-256 `d225e7b7…`, line 656.

## 5. Discrepancies
- **Version selection.**
  - 2,311 sets ship with several versions. All were resolved by metadata, and in every one the metadata version equals the highest version in the release.
  - 730 sets are absent from the metadata: kept as `unconfirmed`, with a NULL publication date.
  - 107 sets have metadata naming a version not in the release: `ambiguous`. That covers 171 products; 55 of their MANUFACTURE edges become TENTATIVE.
  - 0 same-version conflicts.
- **Historical coverage (DST-04A draft, `evidence/historical/dst04a_candidates_draft.json`):**
  - **All 213/213** archived NDC Directory documents were retrieved by document ID from FDA's SPL repository, verified byte-identical on a DST-00 control. The **43** that today's DailyMed search misses all resolve to sets with DailyMed history; they are archived labels.
  - Universe: 247 sets (A∩D 166, A-only 34, of which 17 are labeler `61703` and out of scope; D-only 47).
  - Cutoff versions:
    - 189 via `getFile`;
    - **37** identical version by document ID (`getFile` 404);
    - **9** recovered from the 2023 monthly archives by HTTP Range (about 13 MB read of about 8.7 GB);
    - **1 not retrievable** (`99a0571d` v14, published 2023-06-16);
    - 11 first published after the cutoff.
  - Packages:
    - 983 in-scope `0409` packages; excluded: 197 without NDC, 87 marketing ended by the cutoff;
    - **896 draft candidates**, 890 distinct 11-digit codes;
    - 6 NDCs appear in two sets;
    - 0 product/package segment mismatches;
    - 6 with unknown marketing status.
  - Of the 477 listed packages, 475 are present in their cutoff document; 2 are unresolved (the blocked set).
  - **426 candidates are in cutoff SPLs but not in the May listing.** The listing is a cross-check, not the frame.
  - 738 of 896 candidates' products carry some MANUFACTURE assertion (any site; not classified).
  - Monthly archive labels are offset: "may2023" holds uploads 05-06 to 06-30.

## 6. Tests and performance
- **64 tests pass**: 18 run against PostgreSQL; with a stdlib-only interpreter those 18 skip.
- New tests cover duplicate versions (only the canonical version contributes edges), same-version conflicts, metadata naming another version, every identity state, contacts never stored, an SQL = Python confidence mirror, misleading same-name products, PACK ≠ MANUFACTURE for a labeler DUNS, missing establishment blocks, unscoped operations, raw XML evidence, refusal of unhyphenated NDCs, and rebuild idempotence with the base untouched.
- **Graph build:** 6.2–14.1 s per atomic rebuild (six builds; the variation is machine load); rebuild fingerprints are always equal. The database is 706 MB, up from 532 MB.
- **Query medians** (5 runs, real DB): product 16–22 ms · facility 4–6 ms · compare 3 ms · labeler 8 ms · search 27 ms · unresolved 32 ms · coverage 0.73 s · `evidence --raw` 81 ms, which re-opens a 3 GB part and verifies hashes.

## 7. Security and reproducibility
- Raw data (18 GB plus historical sources), the database cluster, credentials and the venv all live under `$FINEPRINT_DATA`, outside OneDrive and git.
- Contact fields never reach the database or the repo. All external requests use a generic User-Agent.
- **History audit** (`evidence/security/git_history_audit.json`, 140 blobs, all refs):
  - the database password is **absent**;
  - HEAD hits are only pattern literals in guard and audit code;
  - **5 history-only blobs** carry personal fragments: the local home path and username in pre-scrub DST-00/01 evidence and the first DST-01 report, plus the first audit report, whose "masking" kept a path prefix and two username characters. The repo guard test caught that one; the masking is now category-only;
  - **every commit's author email is a personal Outlook address**.
- A remote `origin` (`github.com/s2002kumar/fineprint`) is configured but has never been fetched or pushed.
- **Before any push, you need to approve a history rewrite** (fresh squashed history, or `git filter-repo`, plus a noreply author email). Nothing was rewritten.

## 8. Remaining DST-04 blockers
1. **The DailyMed all-labels export for 2023-07-18 has not been requested** (it needs your email). Without it, frame completeness is unproven: Hospira labels missing from both today's search and the May 2023 listing are invisible.
2. Set `99a0571d` v14 is unretrievable; it affects 2 listed packages.
3. Decisions to freeze: whether the 426 packages absent from the listing stay (the A4 rule says yes), how the 6 duplicate NDCs are handled, and the 6 unknown-marketing packages.
4. B3 remains NOT EVALUABLE.
5. 2023 registration status is unestablished (amendment A2).

## 9. Recommendation
Approve **DST-04B** as two gated steps:
1. **Freeze.** Send the DailyMed request, or explicitly accept the incomplete-frame caveat. Then apply the A4 rules unchanged, classify Rocky Mount links on the frozen candidates, and commit the frame manifest with its SHA-256.
2. **Unseal and score** (B1, B2, graph; B3 stays NOT EVALUABLE).

Separately, decide the history-rewrite question before the first push.
