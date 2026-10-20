# Five example queries

Each query was run on 2026-10-20 against graph build 8 (DailyMed release 2026-10-16, FDA registration files as of
2026-10-19). Full, unedited output is in [`evidence/queries/`](../evidence/queries/). Times are single runs; medians
over repeated runs are in [METRICS.md](METRICS.md).

To reproduce, build the database ([REPRODUCIBILITY.md](REPRODUCIBILITY.md)), then run the commands as shown. Evidence
IDs are database row keys: they are stable across graph rebuilds of the same ingest, but a fresh ingest may number
them differently. The set ID, version and XML location are the portable reference.

## 1. Which registered sites manufacture a product?
```text
$ python -I scripts/fp.py product 0409-4346
00409-4346  Aminocaproic Acid  INJECTION, SOLUTION  [labeler: Hospira, Inc. — a labeler is not a facility]
  set 1c5bc1dd-e9ec-44c1-9281-67ad482315d9 v20  published 2026-05-04  version selection: confirmed
  MANUFACTURE DIRECT:
    093132819  FEI 1021343 — Hospira, Inc., Highway 301 North, Rocky Mount, North Carolina (NC) 27801 …  [evidence 105515]
    860037912  FEI 3008316085 — Pfizer Healthcare India Private Limited, … Andhra Pradesh 531019, India  [evidence 105517]
  MANUFACTURE TENTATIVE: none
  MANUFACTURE UNKNOWN: none
  other operations (not manufacture): ANALYSIS 093132819 DIRECT [105513]; LABEL 093132819 DIRECT [105514]; …
```
Two sites are documented for this product. The labeler is reported but never counted as a site.
**Check it yourself:**
1. Open the [DailyMed label](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1c5bc1dd-e9ec-44c1-9281-67ad482315d9).
2. Confirm that it still shows version 20.
3. Read the establishment table at the end.

## 2. What exactly does the label say?
```text
$ python -I scripts/fp.py evidence 105515 --raw
  set_id: 1c5bc1dd-e9ec-44c1-9281-67ad482315d9   version: 20   document_id: eddf1507-1869-4ac6-9751-4cb12bdce2c1
  xml_sha256: 7c342e8bc47018bb10ee9c0c1a7c97acdee449384036c9256d5d9a68d9913193
  member_name: prescription/20260503_1c5bc1dd-e9ec-44c1-9281-67ad482315d9.zip   source_part: dm_spl_release_human_rx_part5.zip
  loc: /document/author[1]/assignedEntity[1]/representedOrganization/assignedEntity[1]/assignedOrganization/assignedEntity[1]/performance[3]
  duns: 093132819   confidence: DIRECT   identity_source: drls_reg.zip   identity_line: 656   identity_as_of: 2026-10-19
  raw XML (re-read from the archive; member and XML SHA-256 verified):
    <performance xmlns="urn:hl7-org:v3">
      <actDefinition>
        <code code="C43360" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="MANUFACTURE" />
        <product><manufacturedProduct classCode="MANU"><manufacturedMaterialKind>
          <code code="0409-4346" codeSystem="2.16.840.1.113883.6.69" />
        …
```
The CLI re-opens the 3 GB release part, re-hashes the archive member and the XML, and prints the element at the
cited XPath.
**Check it yourself:**
- Download FDA's copy of the same document, [`eddf1507-….xml`](https://www.accessdata.fda.gov/spl/data/eddf1507-1869-4ac6-9751-4cb12bdce2c1/eddf1507-1869-4ac6-9751-4cb12bdce2c1.xml).
  Its SHA-256 should equal `xml_sha256`; spot checks of other documents matched byte for byte.
- Search the [FDA DECRS site](https://www.accessdata.fda.gov/scripts/cder/drls/default.cfm) for FEI `1021343`.

## 3. What is a site documented to make?
```text
$ python -I scripts/fp.py facility 030606222
DUNS 030606222: CURRENT_REGISTERED, FEI 1925262, Hospira, Inc., 1776 North Centennial Drive, McPherson, Kansas (KS) 67460, …
  (registration file 2026-10-19, expires 2026-12-31)
  MANUFACTURE DIRECT: 122 product edge(s)
    00069-0293  Nivestym  set d23ab39c-b6ec-41cf-a529-9dd2852c9d9a v18  [evidence 75182]
    00069-1305  RETACRIT  set 3af26b0d-8ad0-44e1-a538-8bdb5ab39374 v19  [evidence 71617]
    …
  MANUFACTURE TENTATIVE: 0 product edge(s)
  MANUFACTURE UNKNOWN: 0 product edge(s)
  other operations: ANALYSIS DIRECT 149 products; LABEL DIRECT 112 products; PACK DIRECT 112 products
```
McPherson was the historical replay's negative control. The same view is in the
[explorer](https://s2002kumar.github.io/fineprint/#/facility/030606222), with every package NDC and a CSV download.

## 4. Which products does one site make that another does not?
```text
$ python -I scripts/fp.py compare 093132819 030606222 --labeler 141588017 --limit 5
MANUFACTURE at 093132819 vs 030606222 (labeler 141588017): {'only_a': 144, 'only_b': 62, 'both': 27}
  only_a:
    00409-0009  Ondansetron  set d62cd60b-f87e-4825-bead-1d18bbc4e480  ['DIRECT']
    …
  both:
    00409-0155  Precedex  set 92b7ddaa-e45a-4b64-a802-bb5df8771dd6  ['DIRECT']
    …
```
The comparison is restricted to Hospira-labeled products. The "both" group lists more than one site for the same
product: a single-site outage need not stop those products, though the label does not say how production is split.

## 5. What does an unresolved manufacturer look like?
```text
$ python -I scripts/fp.py facility 080105003
DUNS 080105003: NOT_FOUND
  also LABELER on 204 current labels (company role; not counted as manufacturing)
  MANUFACTURE DIRECT: 0 product edge(s)
  MANUFACTURE TENTATIVE: 0 product edge(s)
  MANUFACTURE UNKNOWN: 203 product edge(s)
    72934-1002  ADAPALENE 0.1% / BENZOYL PEROXIDE 2.5% / CLINDAMYCIN 1%  set 887ae1db-bcb4-2e8b-e053-2a95a90abc08 v2  [evidence 18936]  (identity:NOT_FOUND)
    …
```
These 203 labels name this DUNS as the manufacturer, but the DUNS appears in none of the five loaded FDA
registration files: the current file, the excluded list and three dated archives. fineprint does not guess a site from the company name, so every link stays UNKNOWN with the
reason attached.
