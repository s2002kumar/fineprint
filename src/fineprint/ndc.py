"""NDC handling that never pads or joins uncritically.

SPL documents carry hyphenated 10-digit NDCs (4-4-2, 5-3-2, 5-4-1 for packages;
4-4, 5-3, 5-4 for products). The 11-digit "5-4-2" billing form is derived ONLY
from an explicit hyphenated segment pattern; anything else returns None.
"""

from __future__ import annotations

PACKAGE_PATTERNS = {"4-4-2", "5-3-2", "5-4-1"}
PRODUCT_PATTERNS = {"4-4", "5-3", "5-4"}


def segments(raw: str) -> list[str]:
    return raw.strip().split("-")


def pattern(raw: str) -> str:
    return "-".join(str(len(s)) for s in segments(raw))


def is_well_formed(raw: str) -> bool:
    segs = segments(raw)
    return all(s.isdigit() for s in segs) and pattern(raw) in (PACKAGE_PATTERNS | PRODUCT_PATTERNS)


def package_belongs_to_product(package_raw: str, product_raw: str) -> bool:
    """True iff the package's first two raw segments equal the product's raw segments.

    Comparison is on the raw strings exactly as written in the same source; no
    zero padding, so '0409-3308-03' belongs to '0409-3308' but not to '00409-3308'.
    """
    p, q = segments(package_raw), segments(product_raw)
    return len(p) == 3 and len(q) == 2 and p[:2] == q


def to_11_digit(raw: str) -> str | None:
    """Hyphenated 10-digit package NDC -> '5-4-2' 11-digit form, else None.

    '0409-3308-03' (4-4-2) -> '00409-3308-03'. Unhyphenated or unknown patterns
    are ambiguous and deliberately not converted.
    """
    segs = segments(raw)
    if not all(s.isdigit() for s in segs):
        return None
    pat = pattern(raw)
    if pat == "4-4-2":
        a, b, c = "0" + segs[0], segs[1], segs[2]
    elif pat == "5-3-2":
        a, b, c = segs[0], "0" + segs[1], segs[2]
    elif pat == "5-4-1":
        a, b, c = segs[0], segs[1], "0" + segs[2]
    elif pat == "5-4-2":
        a, b, c = segs
    else:
        return None
    return f"{a}-{b}-{c}"
