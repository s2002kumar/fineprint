# fineprint

**When a drug factory is disrupted, which medicines should investigators check first?**

Public FDA records contain clues, but the pieces live in different places: drug labels describe products and sometimes list manufacturing establishments; a separate registry identifies those establishments. **fineprint connects the records into a searchable, source-backed map of products and manufacturing sites.** It shows what the published records say, when they said it, and when the evidence is missing.

[**Explore the live project**](https://s2002kumar.github.io/fineprint/) · [**See the 2023 case study**](https://s2002kumar.github.io/fineprint/#/rocky-mount-2023) · [How it works](docs/ARCHITECTURE.md) · [Source code](src/fineprint/)

[![Python and PostgreSQL tests](https://github.com/s2002kumar/fineprint/actions/workflows/ci.yml/badge.svg)](https://github.com/s2002kumar/fineprint/actions/workflows/ci.yml)

## The result

In July 2023, a tornado disrupted Pfizer's Hospira facility in **Rocky Mount, North Carolina**. Two days later, Pfizer published a list of 65 product-package codes it expected to run low.

I tested whether fineprint could narrow the list of products worth investigating **using only drug-label records published before the tornado**.

| Approach | Packages to investigate | Items recovered from Pfizer's 65-item warning list |
| --- | ---: | ---: |
| Search every Hospira package in the study cohort | 890 | 63 |
| **Filter for documented Rocky Mount manufacturing links** | **480** | **63** |

**46.1% fewer candidates, with the same 63 of 65 warning-list items recovered.**

This is a **historical list-reduction experiment**, not a shortage prediction. Pfizer's warning list is not a complete list of everything the plant manufactured; the two missed items were sterile empty vials, which had no drug labels. [Read the evaluation and its limitations](docs/EVALUATION_REPORT.md).

![Fineprint facility explorer showing manufacturing evidence for the Rocky Mount site](docs/img/explorer-rocky-mount.png)

## Try it in 30 seconds

1. [**Open the Rocky Mount facility**](https://s2002kumar.github.io/fineprint/#/facility/093132819). Inspect the product links, manufacturing operations and cited label versions.
2. [**Open the historical 2023 comparison**](https://s2002kumar.github.io/fineprint/#/rocky-mount-2023). See the 480-versus-890 shortlist and exactly what it measures.
3. [**Search other establishments**](https://s2002kumar.github.io/fineprint/). Browse the public snapshot and export results as CSV.

The explorer is a **published snapshot**, not a live FDA API or an inventory monitoring service.

## How fineprint works

\`\`\`mermaid
flowchart LR
    A["DailyMed drug labels<br/>products + manufacturing claims"] --> C["Python ingestion<br/>PostgreSQL evidence graph"]
    B["FDA establishment registry<br/>facility IDs + addresses"] --> C
    C --> D["Product-to-facility links<br/>with evidence + uncertainty"]
    D --> E["Searchable web explorer<br/>and Python CLI"]
\`\`\`

For each reported manufacturing relationship, the project:

1. **Reads the original label.** It identifies the specific drug product and its manufacturing operation, rather than assuming the company marketing a medicine also manufactured it.
2. **Resolves the establishment.** It matches the label's facility identifier (DUNS) against dated FDA registration data to locate the corresponding registered facility (FEI), when available.
3. **Keeps the proof.** Results link to the exact label version, source document, XML location and recorded hashes. Missing or ambiguous evidence stays visible instead of being guessed.

The released graph labels evidence **DIRECT**, **TENTATIVE** or **UNKNOWN**. DIRECT means a product-scoped manufacturing statement appears in the label and its facility identity passes the graph's checks. It is **not** independent confirmation that a particular lot was manufactured there.

## What I engineered

| Engineering problem | Implemented approach | Recorded result |
| --- | --- | --- |
| Process a large public dataset without loading it into memory | Streaming ZIP/XML ingest into PostgreSQL, with per-document savepoints | **18 GB**, **55,064 label files**, **23.1 minutes**, **73 MB peak memory** |
| Recover safely from interrupted runs | Resumable downloads, idempotent ingest, bounded parsing and atomic graph rebuilds | Real crash, process kill and out-of-memory recovery produced **identical table fingerprints** to a clean run |
| Make every graph relationship explainable | Versioned records, facility identity history, source locations and hash-verified evidence lookup | Rebuilds reproduced identical graph fingerprints; source-evidence lookup measured at **81 ms** |
| Let anyone inspect the outcome | Deterministic JSON/CSV exports powering a static site | Public explorer across **4,314 establishment identifiers** mentioned in current labels |
| Evaluate without peeking into the future | Separate 2023 file-based replay with a frozen pre-event cohort | **480 vs. 890** candidates, both recovering **63/65** warning-list items |

These are **measured runs on the documented reference machine**, not simulated throughput or claims of production traffic. [Metrics and evidence files](docs/METRICS.md) · [Design and data model](docs/ARCHITECTURE.md).

## Explore the code

| Start here | What's inside |
| --- | --- |
| [\`src/fineprint/\`](src/fineprint/) | SPL parsing, streaming ingest, graph rules, identity resolution, historical replay |
| [\`scripts/fp.py\`](scripts/fp.py) | CLI for products, facilities and raw source evidence |
| [\`migrations/\`](migrations/) | PostgreSQL schema and additive changes |
| [\`site/\`](site/) | Static explorer, datasets and client-side CSV exports |
| [\`tests/\`](tests/) | Parsing, PostgreSQL integration, recovery, historical guards, export checks |
| [\`evidence/\`](evidence/) | Reproducible run manifests, benchmarks and frozen evaluation outputs |

Example CLI commands after [local data setup](docs/REPRODUCIBILITY.md):

\`\`\`sh
python -I scripts/fp.py product 0409-4346
python -I scripts/fp.py facility 030606222
python -I scripts/fp.py evidence 105515 --raw
\`\`\`

Run the released test suite with \`python -I -m unittest discover -s tests -t .\`. The main-branch suite contains **84 tests**, including **20 PostgreSQL-backed tests**; CI runs with PostgreSQL 18. A full ingest requires the separate source archives described in the [reproduction guide](docs/REPRODUCIBILITY.md).

## What fineprint cannot tell you

- **It does not predict shortages.** A label connection is not evidence of inventory, production volume, alternate suppliers or a future shortage.
- **Public records are incomplete.** Some labels have no product-specific manufacturing statement; others name a site that cannot be resolved in the available registration snapshots.
- **These are dated records.** The released national graph uses DailyMed data from **October 16, 2026**, and FDA registration files through **October 19, 2026**. The historical archive is incomplete, and the study covers one disruption.
- **Validation has limits.** Automated tests, source re-extraction and AI-assisted evidence checks are documented, but an **independent human source audit has not been completed**. Draft follow-up research also identifies label-versus-registration-operation conflicts that are not yet resolved in the released graph.

The experimental [accuracy/coverage review (PR #2)](https://github.com/s2002kumar/fineprint/pull/2) and [source-NDC lineage research (PR #3)](https://github.com/s2002kumar/fineprint/pull/3) are **draft, not part of this released explorer**. In particular, SOURCE_LINKED relationships in PR #3 must not be presented as verified facilities for specific repackaged lots.

**Deeper reading:** [Case study](docs/CASE_STUDY.md) · [Evaluation report](docs/EVALUATION_REPORT.md) · [Reproducibility](docs/REPRODUCIBILITY.md) · [Example queries](docs/EXAMPLE_QUERIES.md) · [Full metrics](docs/METRICS.md).

## Data and attribution

Code is [MIT-licensed](LICENSE); source datasets retain their own terms ([NOTICE](NOTICE.md)). Drug-label data is courtesy of the U.S. National Library of Medicine's DailyMed, and establishment records are from the U.S. FDA. Raw archives and personal contact data are not published here. fineprint is independent and is **not affiliated with or endorsed by FDA, NLM, NIH, HHS, Pfizer or Hospira**. It is not medical advice.
