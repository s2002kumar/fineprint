"""DailyMed endpoints and release-page parsing.

Endpoints are the documented ones from
https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
"""

from __future__ import annotations

import datetime as _dt
import html as _html
import re

BULK_PAGE = "https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm"
WEB_SERVICES_DOC = "https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm"
ARCHIVES_DOC = "https://dailymed.nlm.nih.gov/dailymed/archives/index.cfm"
GETFILE_VERSION = "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid={setid}&version={version}"
HISTORY = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}/history.json?pagesize=100&page={page}"
SPLS_SEARCH = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"

HUMAN_RX_PREFIX = "dm_spl_release_human_rx_part"

_PART_TEXT = re.compile(
    r"(?P<name>{prefix}\d+\.zip)\s*\[\s*HTTPS\s*/\s*FTP\s*\]\s*"
    r"Number of files:\s*(?P<files>[\d,]+)\s*"
    r"File size:\s*(?P<size>[\d.]+\s*[KMGT]?B)\s*"
    r"MD5 checksum:\s*(?P<md5>[0-9a-fA-F]{{32}})\s*"
    r"Last Modified:\s*(?P<modified>[A-Z][a-z]{{2}} \d{{1,2}}, \d{{4}})"
)


def _page_text(page_html: str) -> str:
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page_html, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", _html.unescape(s))


def parse_release_parts(page_html: str, prefix: str = HUMAN_RX_PREFIX) -> list[dict]:
    """Return the advertised release parts for ``prefix`` exactly as the page states them.

    Advertised values are kept as strings next to parsed forms; nothing is assumed
    about how many parts exist.
    """
    hrefs = set(re.findall(r'href="(https://[^"]+/%s\d+\.zip)"' % re.escape(prefix), page_html))
    text = _page_text(page_html)
    pat = re.compile(_PART_TEXT.pattern.format(prefix=re.escape(prefix)))
    parts, seen = [], set()
    for m in pat.finditer(text):
        name = m["name"]
        if name in seen:
            continue
        seen.add(name)
        https = sorted(h for h in hrefs if h.endswith("/" + name))
        parts.append({
            "name": name,
            "https_url": https[0] if https else None,
            "advertised_number_of_files": int(m["files"].replace(",", "")),
            "advertised_file_size": m["size"],
            "advertised_md5": m["md5"].lower(),
            "advertised_last_modified": _dt.datetime.strptime(m["modified"], "%b %d, %Y").date().isoformat(),
        })
    parts.sort(key=lambda p: int(re.search(r"part(\d+)\.zip$", p["name"]).group(1)))
    return parts


MAPPING_PAGE = "https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-mapping-files.cfm"
ZIP_METADATA_FILE = "dm_spl_zip_files_meta_data.zip"


def parse_advertised_file(page_html: str, filename: str) -> dict | None:
    """Advertised entry for one exactly-named file on a DailyMed resources page."""
    text = _page_text(page_html)
    pat = re.compile(_PART_TEXT.pattern.replace("(?P<name>{prefix}\\d+\\.zip)", "(?P<name>{name})")
                     .format(name=re.escape(filename)))
    m = pat.search(text)
    if not m:
        return None
    href = re.search(r'href="(https://[^"]+/%s)"' % re.escape(filename), page_html)
    return {
        "name": filename,
        "https_url": href.group(1) if href else None,
        "advertised_number_of_files": int(m["files"].replace(",", "")),
        "advertised_file_size": m["size"],
        "advertised_md5": m["md5"].lower(),
        "advertised_last_modified": _dt.datetime.strptime(m["modified"], "%b %d, %Y").date().isoformat(),
    }


def parse_history_date(s: str) -> str:
    """'Sep 01, 2020' -> '2020-09-01' (DailyMed history API format)."""
    return _dt.datetime.strptime(s, "%b %d, %Y").date().isoformat()


def latest_admissible(versions: list[dict], cutoff: str) -> dict | None:
    """Latest version whose ``published_at`` (ISO date) is on or before ``cutoff``.

    Versions published after the cutoff are never eligible, even if they carry
    an earlier XML effectiveTime.
    """
    pre = [v for v in versions if v["published_at"] <= cutoff]
    return max(pre, key=lambda v: v["version"]) if pre else None
