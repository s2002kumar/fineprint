# Licensing scope, third-party data and attribution

## What the MIT license covers
[LICENSE](LICENSE) (MIT) covers the original work in this repository: source code, SQL migrations, tests,
scripts, site code and documentation written for fineprint.

It does **not** cover the third-party records listed below. They are in this repository as test fixtures or
as facts derived from them (identifiers, names, dates, operation codes, hashes and XPath citations). Each
keeps its publisher's terms.

## DailyMed (U.S. National Library of Medicine)
**Courtesy of the U.S. National Library of Medicine.**

- **Used:**
  - the DailyMed human prescription SPL full release of 2026-10-16 (six `dm_spl_release_human_rx_part*.zip` parts);
  - the official 2026-10-19 daily update;
  - DailyMed SPL version histories and archived label versions published on or before 2023-07-18;
  - the 2023 monthly update archives.
- **In this repository:**
  - SPL documents under `tests/fixtures/`, unmodified except that the two facility filings had their contact
    elements removed;
  - derived identifiers and citations under `evidence/`;
  - the explorer's data exports under `site/data/`. These hold identifiers, product names, dosage forms, label
    version metadata, XML locations and hashes, and FDA-registered firm names and business addresses. No label text
    and no personal contact data are included.
- **Currency.** This repository and anything built from it reflect the dated snapshots above. **They do not
  reflect the most current/accurate data available from NLM.** Current labels are at
  <https://dailymed.nlm.nih.gov/>.
- **Terms.**
  - NLM's [Terms and Conditions](https://www.nlm.nih.gov/databases/download/terms_and_conditions.html) ask
    for the "Courtesy of the U.S. National Library of Medicine" acknowledgment and no implied endorsement.
  - Redistributors must either keep the data current or state clearly that it is not current, as done above.
  - NLM provides the data without warranty.
- **Third-party content inside SPL documents.** SPL documents are written and submitted by the labeling
  companies. NLM's [web policies](https://www.nlm.nih.gov/web_policies.html) note that content contributed
  by companies may be protected by copyright. fineprint redistributes only the minimal fixtures needed for
  tests, and structured facts extracted from labels; no full archive is redistributed.

## U.S. Food and Drug Administration
- **Used:**
  - FDA Drug Establishments Current Registration Site (DECRS) files, current and dated archived snapshots;
  - the FDA NDC Directory generated 2023-05-05;
  - SPL documents retrieved by document ID from `accessdata.fda.gov`;
  - Pfizer's July 21, 2023 post-tornado low-inventory warning appendix, hosted by FDA at
    <https://www.fda.gov/media/170647/download>.
- **Terms.** FDA website content is in the public domain unless otherwise noted
  ([FDA website policies](https://www.fda.gov/about-fda/about-website/website-policies)).
- **Not redistributed:**
  - the Pfizer appendix PDF. Only its SHA-256, retrieval metadata and the 65 package NDC codes used for
    scoring are recorded, in `evidence/historical/evaluation_results.json`;
  - personal contact fields in FDA registration files. They are dropped at parse time and never stored or
    published.

## Internet Archive
Some dated FDA snapshots were read through the Wayback Machine (`web.archive.org`) when FDA no longer served
the original file. The underlying files are FDA records; the archive is cited as the access path and
capture timestamp in `evidence/`.

## Software dependencies
| Component | Role | License |
|---|---|---|
| Python standard library | parsing, download, CLI | PSF License |
| `psycopg[binary]` 3.3.6 | optional PostgreSQL driver, installed from PyPI, not vendored (its wheel bundles libpq and OpenSSL) | LGPL-3.0-only |
| PostgreSQL 18 | external database server | PostgreSQL License |
| GitHub Actions (`actions/*`), `postgres:18` container | CI and Pages deployment only | each project's own license |
| Newsreader, DM Sans and JetBrains Mono typefaces (variable WOFF2, latin and latin-ext subsets, from Fontsource 5.3.0) | explorer typography, self-hosted in `site/fonts/`, unmodified | SIL Open Font License 1.1 (`site/fonts/LICENSE-*.txt`) |

## Independence
fineprint is an independent project. It is not affiliated with, endorsed by, or reviewed by the U.S. National
Library of Medicine, the National Institutes of Health, the U.S. Food and Drug Administration, HHS, Pfizer or
Hospira. Nothing here is medical advice or a statement about current drug availability.
