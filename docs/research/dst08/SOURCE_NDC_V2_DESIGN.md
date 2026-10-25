# DST-08 rule `dst08-lineage-v2`: version-aware physical validation

**Status: research only, fixed before any historical label version was retrieved.** This note, the code that
implements it (`fineprint.lineage.validate_v2`, `scripts/research/dst08_lineage_v2.sql`) and its tests are committed
before the fetch script reads a single archived version. Nothing here changes the production graph, `site/data/`, the
frozen benchmark or a release. Rule `dst08-lineage-v1` (`SOURCE_NDC_DESIGN.md`) and its tables, counts and evidence are
left exactly as built at `c8ded0f`, so the effect of v2 can be measured against them.

## 1. Why v1 needs a second rule

The SPL Implementation Guide requires a repackaged product's active ingredients and strengths, dosage form, size, shape,
colour, imprint, flavour and scoring to equal its source's (3.2.2.3–3.2.2.10). Rule v1 compares only form and active
ingredients. The post-hoc diagnostic at `a4a7384` found 373 of the 19,668 v1-eligible references whose citing label and
the source's *current* label state a different imprint, colour, shape, size, score or flavour, 352 of them where the
source label is newer than the citing label. A comparison between labels from different dates can neither confirm nor
refute the link: the source may simply have changed after the repackager listed it. Rule v2 therefore judges each such
reference against the source label in force when the citing label was published.

## 2. Scope

- **Checked:** every reference that is ELIGIBLE under v1 and whose `lineage.physical_check.conflict` is true: a
  characteristic stated on both labels differs as the diagnostic compared it. The build reproduces the diagnostic's
  test exactly; at `c8ded0f` that is 373 references.
- **Not checked:** every other reference keeps its v1 status, reasons and evidence. Rule v2 can only remove links that
  v1 admits, or keep them with fewer sites; it never adds one.

## 3. Sources

- DailyMed SPL history service (`/services/v2/spls/{setid}/history.json`): every version number of a set with its
  DailyMed publication date.
- DailyMed version archive (`/dailymed/getFile.cfm?type=zip&setid={setid}&version={n}`): the label as published in that
  version.
- Retrieved with the project's generic User-Agent through `fineprint.historical.Fetcher`, which caches each response
  with its provenance (URL, status, retrieval time, SHA-256) under `$FINEPRINT_DATA/research/dst08/history/`.
- `docs/research/dst08/source_history_manifest.json`, committed, freezes what was retrieved: each set's version list and
  each archived version's status, ZIP and XML SHA-256, document id and effective time. `validate_v2` reads only the
  manifest and the cache and refuses any cached file whose hash differs.
- **Fetch scope, fixed here:** for every checked reference, the citing set's history and the source set's history;
  then every source version listed by the history, from 1 to the release's canonical version. Versions published after
  the release are never read. An archived version whose served set id or version differs from the request, that is
  not a ZIP, or that has no single XML file is recorded with that status and never used.
- **Fetch-path check:** the archive's copy of each source's canonical (release) version must be byte-identical to the
  XML in the release (`canonical_xml_matches_release`). If it is not, the archive cannot be trusted to return the
  version asked for, and the report says so.

## 4. Dates and the applicable version

- **Relevant date D:** the DailyMed publication date of the citing label version in the release, from the citing set's
  history. If the history service has no entry, the release metadata's upload date
  (`national.spl_document.published_date`) is used; the basis is recorded. D is when the repackager last asserted both
  the source NDC and the physical description, and when FDA's listing validation would have compared them with the
  source listing then in force.
- **Applicable source version A:** the highest source version number whose DailyMed publication date is on or before D
  (a version published the same day counts) and that is not later than the release's canonical version.
- Nothing newer substitutes for A. A later version is consulted only to show that the citing description matches a
  version other than A, which makes the case ambiguous, never acceptable.

## 5. Comparison and classification

Characteristics are read from the `manufacturedProduct` role exactly as the diagnostic read them
(`lineage.characteristics`). If several products in a label carry the cited code, their values are pooled. Each
characteristic stated on both sides is one of:

| Value | Meaning |
|---|---|
| `SAME` | equal |
| `SAME_MARKS` | imprints whose marks are the same, written differently (`RX692` against `RX692;RX692`) |
| `ONE_OF_SEVERAL` | the source states several values and the citing product's are among them |
| `DIFFERS` | anything else; no tolerance (10 mm is not 11 mm) |

A source version *describes* the citing product when nothing differs and every characteristic that conflicts in the
current release is stated on both sides and consistent. Each checked reference gets the first class that applies:

1. `MISSING_COMPARISON_EVIDENCE`: D is unknown; the source history is unavailable; or A cannot be retrieved or parsed.
2. `UNRESOLVED_AMBIGUITY`: no source version was published by D (the set postdates the citing label), or A does not
   carry the cited code.
3. A characteristic `DIFFERS` at A:
   - `UNRESOLVED_AMBIGUITY` if another source version (earlier, superseded by D, or later, up to the release)
     describes the citing product, or if another version could not be retrieved, so such a match cannot be ruled out;
   - otherwise `CONFIRMED_CONFLICT`: the source, as listed when the citing label was published, described a different
     physical product, and so did every other version.
4. `MISSING_COMPARISON_EVIDENCE`: a characteristic that conflicts now is not stated on both sides at A.
5. `MULTIPLE_VALID_PRESENTATIONS`: at A the source states several values and the citing product's are among them.
6. `VERSION_DRIFT_RESOLVED`: A describes the citing product exactly (`SAME` or `SAME_MARKS`), and the current source
   label differs. The source changed after the citing label was published.
7. `NOTATION_ONLY`: A describes the citing product, and the only current differences are `SAME_MARKS`.

## 6. Eligibility under v2

- `CONFIRMED_CONFLICT`, `UNRESOLVED_AMBIGUITY` and `MISSING_COMPARISON_EVIDENCE` are EXCLUDED, with the reason
  `version:<class>`. They stay quarantined: not validated, not counted, and not called false.
- `VERSION_DRIFT_RESOLVED`, `MULTIPLE_VALID_PRESENTATIONS` and `NOTATION_ONLY` establish the source's identity at D.
  They are still ELIGIBLE only with **site continuity**:
  - at least one DUNS that A names with MANUFACTURE scoped to the cited code must also be a current DIRECT MANUFACTURE
    site of the source product;
  - the v2 evidence keeps only those continuing sites;
  - with none, the reference is EXCLUDED as `version:sites_changed_since_citing`. The sites the source names today
    are not the ones it named when the repackager listed it, so today's DIRECT edge says nothing about the lots.
- The source's current DIRECT edge stays the only manufacturing evidence. A site named only in a historical version
  never becomes evidence, because DIRECT requires the current label and the current registration.

### Amendment A1 (2026-10-25, after the first v2 run; labels only)

Of the 88 accepted-class references excluded for lack of site continuity, 79 have an applicable version that names no
MANUFACTURE site scoped to the cited code at all:
- 39 state MANUFACTURE without a product scope;
- 31 have no establishment block;
- 5 list establishments without MANUFACTURE;
- 4 scope MANUFACTURE only to other products.

None is a package-code scope. "The sites changed" does not describe them, so they carry the reason
`version:no_site_named_at_applicable_version` instead of `version:sites_changed_since_citing`. The rule, every class and
every eligibility decision are unchanged: in both cases no site continuity can be shown and the reference is
excluded.

## 7. What v2 does not do

- It does not compare characteristics with a tolerance, or use names, companies, addresses or product similarity.
- It does not re-examine references without a current conflict. Their source may also have changed since the citing
  label (for example a site change with the same tablet), which no characteristic would show; that remains a
  limitation of the tier.
- It does not follow multi-hop chains, choose among several candidates, truncate package codes or enter the
  historical 2023 evaluation. Every v1 exclusion stands.
- It does not apply the Implementation Guide's marketing-date condition (3.1.2.10: a repackaged product must not be
  marketed after its source's marketing end date). That is a separate question from physical identity.

## 8. Outputs

- `lineage.source_version_document`: every archived version in the manifest, with its provenance.
- `lineage.version_check`: one row per checked reference, with:
  - both NDCs;
  - the citing version and date D with its basis;
  - the current and the applicable source versions with their dates, document id and XML hash;
  - the characteristics on each side and the per-characteristic comparison at A and now;
  - the sites at A, now and continuing;
  - the other versions that match or could not be retrieved;
  - the class and a one-line reason.
- `lineage.resolution_v2`: every reference under v2, with its basis (`v1` or `version_check`).
- `lineage.source_linked_evidence_v2` and `lineage.v_product_coverage_v2`.
- The v1 tables are not touched: their fingerprints must equal those recorded at `c8ded0f`.
