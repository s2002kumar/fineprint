# DST-08 source-NDC lineage: final validation

Research branch `research/dst-08-source-ndc`, 2026-10-25. Draft PR #3, stacked on draft PR #2
(`research/accuracy-coverage-2026-10`). Not merged, deployed or tagged.

**Nothing in production changed.** The following are all untouched:
- the database `fineprint` and the released graph;
- `site/data/` and the explorer;
- the Rocky Mount benchmark and `dst04b-freeze`;
- every release tag;
- `docs/human_audit_verdicts.csv`.

All work ran in the scratch database `fineprint_dst08`, a copy of `fineprint` (graph build 8, DailyMed release
2026-10-16, FDA registration files to 2026-10-19). The copy equalled production before every build and was
unchanged in every national table after it.

**Every validation here is AI-assisted. No person has adjudicated a source-NDC link, a version check or a
registration conflict, and no human verdict has been filled in or signed.**

## 1. Recommendation: NARROW

Keep a source-linked tier only in this narrow form, and only after the human gate in section 9.

- **Adopt rule `dst08-lineage-v2`; retire v1.** v1 admitted 171 links that cannot be validated against the source
  label in force when the citing label was published (0.87% of its 19,668). At least 7 of them describe a different
  physical product. v2 removes those links and never adds one.
- **Exclude medical gases from the tier.**
  - Medical gases need no source NDC (21 CFR 207.53(b)).
  - All 11 tier products whose source lists 5 or more sites are gases (up to 213 sites). There, a link says nothing
    useful about where the gas was produced.
  - Dropping the 15 gas products leaves **19,426** source-linked products.
- **Keep the tier separate and labelled.**
  - It reads as "upstream evidence about the cited source product, as listed in its own current label: made at one
    of N registered sites", with N shown.
  - It never enters the DIRECT count, never says which site made the repackaged lots, and is never used in the 2023
    historical evaluation.
- **Do not merge it yet.** Merge only if a person confirms at least 29 of the 30 random precision links and all 8
  version-check acceptances (section 9).
  - If that bar fails, the right answer is REJECT, not further rules.
  - Either way the capability is then closed. No further features are proposed.

**Why not MERGE now:**
- no human adjudication yet;
- 16% of version-checked links show that a source's current site list can include sites it did not name when the
  repackager listed it, and that cannot be checked for the other 19,295 links;
- the base DIRECT tier has 26 edges that contradict FDA registration (section 6), which a person should see first.

**Why not REJECT:**
- every link the evidence could test is supported: 0 contradictions among 57 AI-checked v2-eligible links;
- the rule re-derives identically from original labels by a separate code path;
- v2 resolves most physical mismatches deterministically.

| Products (80,508 in the DIRECT-tier population) | Count | Share |
|---|---|---|
| DIRECT (unchanged under both rules) | 24,614 | 30.57% |
| SOURCE_LINKED, rule v1 | 19,612 | 24.36% |
| SOURCE_LINKED, rule v2 | 19,441 | 24.15% |
| SOURCE_LINKED, rule v2 without medical gases (recommended scope) | 19,426 | 24.13% |
| DIRECT or SOURCE_LINKED: v1 / v2 / v2 without gases | 44,226 / 44,055 / 44,040 | 54.93% / 54.72% / 54.70% |

**None of the combined figures is verified manufacturing-site coverage, and they must not be described as such.**
Only the DIRECT tier names a site from the product's own label. A SOURCE_LINKED product carries a statement about
the product it cites.

## 2. Entry checks

| Check | Result |
|---|---|
| Local DST-08 commits | four (`8a2d0fd`, `43b3c5b`, `c8ded0f`, `a4a7384`), all with the noreply identity |
| Working tree | clean |
| PostgreSQL-backed suite | 113 tests, OK, none skipped |
| Scratch database | national tables equal production; the three v1 lineage fingerprints equal `lineage_build.json` |

## 3. Phase 1: reviewable

**Audit.** I ran the repository's history audit (`scripts/audit_git_history.py`) and a targeted scan of the diff
against PR #2:
- no secret, personal path, contact field or bulk dataset is in any DST-08 file;
- the only hits were pre-existing and known (audit patterns, test fixtures, the CI database password variable, the
  disclosed `590e97e` merge identity);
- the largest DST-08 file is a 1.3 MB manifest of fetched label versions;
- the 38 MB inventory CSV and the 562 MB label-version cache stay in `$FINEPRINT_DATA`.

**Pull request.** The branch is pushed. Draft PR #3 targets `research/accuracy-coverage-2026-10`, and CI passed on
push and on the pull request. This session's commits are pushed to the same draft.

## 4. Phase 2: the 373 physical-description mismatches

### Method (pre-registered)

Rule v2 was fixed in `docs/research/dst08/SOURCE_NDC_V2_DESIGN.md`, with its code and 10 tests, and committed at
`3b22c4c`, before any historical label was read.

- The build now reproduces the post-hoc diagnostic exactly: all six outcome counts and the **373** conflicts. The
  three v1 tables stay byte-identical.
- Each conflict is judged against the **applicable source version**: the source label in force on the DailyMed
  publication date of the citing label version.
  - The candidates are read from the DailyMed history service and version archive.
  - They are frozen in `source_history_manifest.json` and read only through it, hash-verified.
- Classes, first that applies:

  | Class | Meaning |
  |---|---|
  | missing comparison evidence | no applicable version can be compared |
  | unresolved ambiguity | no source version by the date, or the citing description matches only another version |
  | confirmed conflict | the applicable version and every other version describe a different product |
  | multiple valid presentations | the applicable version lists several values, the citing product's among them |
  | version drift resolved | the applicable version matches; the source changed later |
  | notation only | the same marks, written differently |

- The accepted classes also need **site continuity**: a DUNS that the applicable version names with MANUFACTURE for
  the code must still be a DIRECT site. The v2 evidence keeps only those continuing sites.

### Retrieval

| What | Result |
|---|---|
| Set histories (319 citing, 112 source) | 431, all retrieved |
| Archived source versions (every version from 1 to the release version) | 1,275 requested; 1,262 usable; 13 HTTP 404, all from one Sun Pharma set (`6ae551f6…`) |
| Fetch-path check: the archive's copy of each source's release version | byte-identical to the release XML in all 369 retrievable cases |
| Date check: DailyMed history date against the release's upload date | equal for all 366 citing and 369 source versions that have both |

### Resolution

| Class | References | v2 eligible | v2 excluded |
|---|---|---|---|
| VERSION_DRIFT_RESOLVED | 239 | 169 | 70 (61 no product-scoped site named then; 9 entirely different sites) |
| NOTATION_ONLY (`RX692` / `RX692;RX692`) | 47 | 31 | 16 (no site named then) |
| MULTIPLE_VALID_PRESENTATIONS | 4 | 2 | 2 (no site named then) |
| CONFIRMED_CONFLICT | 50 | 0 | 50 |
| UNRESOLVED_AMBIGUITY | 28 | 0 | 28 (19 source set first published after the citing label; 9 match only another source version) |
| MISSING_COMPARISON_EVIDENCE | 5 | 0 | 5 (4 archive 404s; 1 field not stated then) |
| **Total** | **373** | **202** | **171** |

- **Labels from different dates are never compared to decide anything.** In 359 of the 373 the source label is newer
  than the citing label. The applicable version was an earlier one in 344 cases, the current one in 10, and absent
  in 19.
- **Amendment A1 (labels only, after the first run).** In 79 of the 88 continuity exclusions, the old label names no
  product-scoped MANUFACTURE site at all:
  - 39 unscoped;
  - 31 with no establishment block;
  - 5 without MANUFACTURE;
  - 4 scoped to other products only.

  None is a parsing artefact. They now say `no_site_named_at_applicable_version` rather than "sites changed". No
  class or count moved.
- **"Multiple valid presentations" is a misnomer in this data.** All four are multi-valued fields (two-colour
  capsules, two flavours) described with one value by the repackager. They are partial descriptions, not separate
  products.

### Anatomy of the 50 confirmed conflicts

`conflict_anatomy.json`, categories fixed in `scripts/research/dst08_conflict_anatomy.py`:

| What differs at the relevant date | n | Reading |
|---|---|---|
| only a coded field (colour, shape, score or size); imprint equal | 31 | description or coding variance |
| citing imprint is another strength's in the same source label (`ETO;200;MG` on a 300 mg product, `K;45` cited as `K;77`, warfarin 2 / 2½ mg) | 6 | the description belongs to a different product |
| imprint by one character (`O;25` / `0;25`, `RO;50` / `R0;50`, `A;42` / `A;43`) | 6 | transcription |
| imprint marks contained (`IG;228` / `100;mg;IG;228`) | 4 | notation beyond the normalisation |
| imprint otherwise distinct (`IG;209` / `D;74`; `I;G;213` / `213;IG`) | 2 | one is a different tablet, one is notation |
| imprint and other fields (`IG;228;100;mg` / `IG;228`, plus colour) | 1 | notation, plus colour |

## 5. Rule v1 against rule v2

The figures are exact. The site figures cover products that reach the SOURCE_LINKED tier. The 56 eligible links on
products that are already DIRECT stay DIRECT.

| Measure | v1 (`c8ded0f`, preserved) | v2 |
|---|---|---|
| Source-NDC references | 36,457 | 36,457 |
| Resolved to exactly one canonical source product | 30,283 | 30,283 |
| Eligible references | 19,668 | 19,497 |
| — accepted on the v1 basis (no physical conflict) | 19,668 | 19,295 |
| — accepted after the version check | — | 202 (169 drift, 31 notation, 2 multiple) |
| Products reaching SOURCE_LINKED | 19,612 | 19,441 |
| — from NO_MANUFACTURE_EVIDENCE / UNKNOWN_SITE / TENTATIVE | 19,607 / 3 / 2 | 19,436 / 3 / 2 |
| Evidence rows / distinct source products / distinct DIRECT source sites | 26,133 / 5,593 / 787 | 25,835 / 5,567 / 785 |
| Products with 1 / 2 / 3 / 4 / 5+ source sites | 14,979 / 3,285 / 1,256 / 81 / 11 | 14,891 / 3,243 / 1,218 / 78 / 11 |
| Medical-gas products in the tier (all 11 with 5+ sites) | 15 | 15 |

**Physical basis of the 19,497 v2-eligible references:**

| Basis | References |
|---|---|
| Imprint and all other stated characteristics equal | 16,936 |
| Nothing comparable (liquids, injectables, creams) | 1,639 |
| No imprint on either side, others equal | 720 |
| Accepted by the version check | 202 |

**Exclusions.** The v1 exclusions (16,789) are unchanged in v2, reason for reason; see
`DST_08_SOURCE_NDC_REVIEW.md` section 6.

**What v2 cannot see.** In 10,262 v2-eligible links (52.6%) the source label is newer than the citing label, with an
unchanged physical description. Site turnover is real:
- among the 202 version-checked links, 51 of 340 current site attributions (15%) were not named when the citing label
  was published;
- 33 links (16%) include such a site, and v2 drops them there;
- for the 19,295 v1-basis links no historical site list was read, so "made at one of N sites" can include a site
  added later.

## 6. Phase 3: DIRECT edges whose registration lacks MANUFACTURE

**Method.** `registration_operations_audit.json` / `.csv`, script `dst08_registration_audit.py` (5 tests). Each of
the 60 edges (57 products, 32 establishments) is set against:
- its SPL performance, re-read verbatim;
- every registration snapshot (2024-12-23, 2025-12-05, 2026-08-21, 2026-10-19);
- the label date;
- the regulatory text: 21 CFR 207.1, 207.53(b), 210.3(b)(12), 212.1 and 213.3(b)(11)/(13), and SPL IG 4.1.4.15 and
  6.1.6.8.

The CFR texts were fetched with a generic User-Agent; their hashes are recorded in the script.

| Class | Edges | Establishments | Basis |
|---|---|---|---|
| EXPLAINED_MEDICAL_GAS_FILLER | 19 | 15 | Medical gases need no source NDC (207.53(b)), and a product without a source must list a manufacture operation, which TRANSFILL is not (IG 4.1.4.15). Medical-gas CGMP counts packaging and labelling as manufacture (213.3(b)(11)) and names the gas's producer separately (213.3(b)(13)). The edge names a filling site. |
| EXPLAINED_REGISTRATION_CHANGED | 13 | 5 | The snapshot nearest the label listed MANUFACTURE; a later one dropped it (AndersonBrecon, scPharmaceuticals, V2 Pharma, two gas firms). The current DIRECT edge rests on an operation no longer registered. |
| EXPLAINED_PET_PRODUCTION | 2 | 2 | Registered PET drug production, which the IG counts as a manufacture operation and 212.1 defines as including manufacturing. |
| CONFLICTING | 26 | 10 | No snapshot lists MANUFACTURE: API only (Solara, Dynamit Nobel, Patheon Austria, Lacsa) 9; API with label/pack (Granules) 3; label or pack only (Meridian 8, Apotex, Actavis kits, Focus Health kits) 13; repack/relabel (Blessings) 1. |
| UNRESOLVED | 0 | 0 | |

- **No DIRECT classification was changed.** If the 26 conflicting edges were not DIRECT, 21 products would lose
  DIRECT (0.09% of 24,614). This is a sensitivity figure, not applied.
- **Medical gases.** DIRECT for gases means "filling site", not where the gas was produced. That is a labelling
  question for the existing tier, separate from DST-08.
- **The separate findings are preserved unchanged** (`repackager_manufacture_audit.*`):
  - 139 repackager-MANUFACTURE products and 19 DIRECT edges, 18 of them registered manufacturers;
  - the labeler-as-manufacturer contradictions S098 and S104 (UNKNOWN_SITE) and S077 (NO_MANUFACTURE_EVIDENCE).
  - One edge appears in both audits: ProCare's oxygen (72258-020). The earlier audit called it "potentially
    erroneous". The regulatory evidence above explains it as a medical-gas filling site, which is the more precise
    reading.

## 7. False links and unresolved cases

**Bounds on v1's unsafe links (of 19,668):**

| Bound | Links | Share | What it covers |
|---|---|---|---|
| Strong | 7 | 0.04% | a different physical product at the relevant date: one different tablet (`IG;209` cited as Aurobindo's `D;74`) and six descriptions of another strength |
| Wider | 50 | 0.25% | confirmed description conflicts |
| Widest | 171 | 0.87% | everything v2 excludes as not validated |

The other 43 confirmed conflicts are probably right links with noisy descriptions; v2 excludes them anyway, which
costs 0.2% of coverage. The orphenadrine case shows why site continuity matters. The source tablet was `GG931` in 2010
and is `NL4` now, and the 2010 label named no site. v1 linked the 2011 repackaged product to today's Novel
Laboratories site, though the source label that matched its description named no site at all.

**v2's links.**
- AI-assisted checks found **0 contradictions in 57 distinct v2-eligible links**:
  - the 42 eligible links of the frozen 96-reference sample (`43b3c5b`), all still eligible under v2;
  - 15 more from the expanded cases.
- Wilson 95% lower bounds: 93.7% for all 57, and 88.6% for the 30 random R9 links alone. The 15 expanded cases are
  not a random sample.
- Residual risks:
  - links whose source label is newer than the citing label (section 5);
  - 1,639 links where no physical field applies;
  - multi-site sources;
  - one gas link whose product name ("Oxygen") contradicts its own active ingredient (nitrous oxide).

**Unresolved and excluded.**
- 16,789 references are excluded by v1 rules and 171 more by v2.
- Exclusion is not falsity. 16 of the 67 review cases are plausible links excluded conservatively, for example:
  - two candidate sets naming the same site;
  - a package code;
  - a two-hop chain;
  - an old label without a site.

## 8. Phase 4: research quality

**Reproduction of the 32-case worksheet.** Every row was re-derived from the original evidence by an independent code
path:
- the raw-XML walkers of the inventory and audit scripts;
- candidates from the independent inventory extract;
- the FDA registration files read directly;
- for v2, the archived source versions re-read from the cache and checked against the manifest.

All reproduced facts agree with the prototype (`final_cases_evidence.json`, `final_cases_digest.md`).

**Expansion.** 35 high-risk cases were drawn with a seed and frozen (`final_cases_FREEZE.json`, commit `7ef162a`)
before review:
- every v2 outcome class;
- multi-site sources (2–4 and 5+ sites);
- tablets or capsules with no imprint;
- several candidates naming different sites;
- a package code.

| Independent re-derivation of the 67 cases | Agreement |
|---|---|
| Source set (single-candidate cases) | 54/54 |
| Current physical comparison | 54/54 |
| Evidence sites stated in the source label | 54/54 |
| v2 class | 35/35 |
| Applicable version | 35/35 |
| Continuing sites | 20/20 |

**AI-assisted validation** (`final_ai_verdicts.json` → `final_ai_validation.csv`). Every citation names the exact set,
version, document id, element location and XML hash.

| Verdict | Cases |
|---|---|
| Link supported | 9 |
| Link supported, with a caveat (multi-site, gas, no imprint, the citing establishment's own MANUFACTURE claim) | 10 |
| Correctly excluded | 9 |
| Excluded, plausible link | 16 |
| Quarantine correct: a different product | 3 |
| Quarantine correct: description noise | 5 |
| Quarantine correct: unverifiable | 15 |

**Determinism and integrity**, from clean commit `9cd9c5e` (`lineage_build_v2.json`):
- two full builds, each followed by v2, gave identical fingerprints;
- the national tables were unchanged;
- the v1 tables equal the `c8ded0f` record, which preserves the v1 counts and evidence;
- the regenerated case evidence, anatomy and review tables are byte-identical to the pre-rebuild copies.

| Table | Rows | SHA-256 (prefix) |
|---|---|---|
| `source_reference` (v1) | 36,457 | `6e73b8a6…` |
| `source_resolution` (v1) | 36,457 | `304e344e…` |
| `source_linked_evidence` (v1) | 26,866 | `96e121a6…` |
| `physical_check` | 30,283 | `8077b8ac…` |
| `version_check` | 373 | `1323c01f…` |
| `resolution_v2` | 36,457 | `cedf11d9…` |
| `source_linked_evidence_v2` | 26,568 | `a72b0c1f…` |

**Performance:**
- a build takes 691–817 s, on a laptop near its memory limit;
- v2 takes 39–72 s;
- one product's evidence chain takes 5.6 ms in SQL, or 0.23 s with both cited XML elements re-read and hash-verified.

**Tests:** 128, OK, none skipped (`python -I -m unittest discover -s tests -t .`). Of these, 113 existed before; 10
are v2 tests (one synthetic scenario per class) and 5 are registration-rule tests.

## 9. Independent human review before any production use

`docs/research/dst08/final_human_worksheet.csv` has 52 items, with every human column blank:

| Items | Why a person must decide |
|---|---|
| 30 random links (frozen R9 sample) | the only unbiased precision estimate; pass mark at least 29 of 30 |
| 8 version-check acceptances | the one new way v2 accepts a link: drift resolved ×3, notation ×3, multiple presentations ×2 |
| 3 medical-gas links | the policy to exclude gases (1 with 180+ sites, 1 with 29, 1 named "Oxygen" with nitrous oxide as its ingredient) |
| 1 repackager with its own MANUFACTURE claim beside a source link | how such a product is presented |
| 10 conflicting DIRECT edges, one per establishment | they are in the released DIRECT tier today; keep or reclassify is a decision for the DIRECT rules, not for DST-08 |

Not required before production, though useful: the confirmed conflicts and the other exclusions. They publish
nothing.

## 10. Limitations

- All validation is AI-assisted.
- The relevant date is the citing label version's publication date. Its physical description may have been written
  earlier, which is why matches with other versions are recorded and treated as ambiguous.
- Site continuity is checked only for the 373 version-checked links (section 5).
- The DailyMed archive could not supply one source set at all.
- Comparison is exact: no size tolerance, and the IG's marketing-date rule (3.1.2.10) is not applied.
- Registration operations are establishment-level and cover only four snapshots, the earliest from 2024-12-23.
- Kits, multi-hop chains, several-candidate cases and package codes stay out of scope.

## 11. Reproduce

```
CREATE DATABASE fineprint_dst08 TEMPLATE fineprint;      -- with no open connection to fineprint
python -I scripts/research/dst08_fetch_source_versions.py --db fineprint_dst08   # network; once, then frozen
python -I scripts/research/dst08_build_lineage.py --db fineprint_dst08 --production fineprint \
       --manifest docs/research/dst08/source_history_manifest.json
python -I scripts/research/dst08_conflict_anatomy.py --db fineprint_dst08
python -I scripts/research/dst08_final_cases.py evidence --db fineprint_dst08       # the case list is frozen
python -I scripts/research/dst08_final_review_tables.py
python -I scripts/research/dst08_evidence_chain.py --db fineprint_dst08 --representative-v2
python -I scripts/research/dst08_final_counts.py --db fineprint_dst08
python -I scripts/research/dst08_registration_audit.py --db fineprint
python -I -m unittest discover -s tests -t .
```

**Notes:**
- The fetch needs a lineage build first; the design note fixes its scope.
- The label-version cache (562 MB) and the eCFR sources are in `$FINEPRINT_DATA/research/dst08/`. Their hashes are in
  the manifest and the audit script.

**Commits on this branch:**

| Commit | Content |
|---|---|
| `8a2d0fd` | design |
| `43b3c5b` | frozen sample |
| `c8ded0f` | prototype v1 |
| `a4a7384` | review gate |
| `3b22c4c` | v2 pre-registration |
| `7ef162a` | history, registration audit, frozen cases |
| `9cd9c5e` | final-validation scripts and AI readings |

This report and its outputs are the final commit.

## 12. Stop

This is the final review gate:
- nothing is merged, deployed or tagged;
- the production graph, the explorer, the Rocky Mount benchmark and the tags are untouched;
- the scratch database `fineprint_dst08` and `$FINEPRINT_DATA/research/dst08/` are kept until you decide.
