"""DST-08 final validation, Phase 3: the stated rule that classifies a DIRECT MANUFACTURE edge whose FDA registration
does not list MANUFACTURE (scripts/research/dst08_registration_audit.py). Pure function tests on synthetic snapshots;
the script itself only reads and never changes a DIRECT classification.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "research"))
try:
    import dst08_registration_audit as ra
except ImportError:  # the research script needs psycopg, like the database tests
    ra = None

CUR, ARCH, EXCL = "fda_decrs_registration", "fda_decrs_registration_archived", "fda_decrs_excluded"


def snap(as_of, operations, kind=ARCH):
    return {"kind": kind, "as_of": as_of, "operations": operations}


@unittest.skipIf(ra is None, "psycopg not installed")
class RegistrationClasses(unittest.TestCase):
    def cls(self, form, snaps, published):
        return ra.classify(form, snaps, published)[0]

    def test_a_label_that_agreed_with_the_registration_of_its_time_is_explained(self):
        snaps = [snap("2024-12-23", "MANUFACTURE"), snap("2026-10-19", "LABEL; PACK", CUR)]
        self.assertEqual(self.cls("CAPSULE", snaps, "2025-05-20"), "EXPLAINED_REGISTRATION_CHANGED")
        # a label older than every snapshot is compared with the earliest one
        self.assertEqual(self.cls("CAPSULE", snaps, "2018-01-01"), "EXPLAINED_REGISTRATION_CHANGED")

    def test_manufacture_registered_only_away_from_the_label_date_is_unresolved(self):
        snaps = [snap("2024-12-23", "MANUFACTURE"), snap("2025-12-05", "PACK"), snap("2026-10-19", "PACK", CUR)]
        self.assertEqual(self.cls("TABLET", snaps, "2026-01-10"), "UNRESOLVED")

    def test_medical_gas_fillers_and_pet_producers_are_explained(self):
        self.assertEqual(self.cls("GAS", [snap("2026-10-19", "TRANSFILL", CUR)], "2020-01-22"),
                         "EXPLAINED_MEDICAL_GAS_FILLER")
        self.assertEqual(self.cls("GAS", [snap("2026-10-19", "RELABEL; REPACK", CUR)], "2017-12-07"),
                         "EXPLAINED_MEDICAL_GAS_FILLER")
        self.assertEqual(self.cls("INJECTION", [snap("2026-10-19", ra.PET, CUR)], "2020-08-07"),
                         "EXPLAINED_PET_PRODUCTION")

    def test_a_registration_that_never_lists_manufacture_conflicts(self):
        api = [snap("2024-12-23", "ANALYSIS; API MANUFACTURE"), snap("2026-10-19", "ANALYSIS; API MANUFACTURE", CUR)]
        self.assertEqual(self.cls("TABLET", api, "2019-02-01"), "CONFLICTING")
        self.assertEqual(ra.conflict_kind({"ANALYSIS", "API MANUFACTURE"}), "API_MANUFACTURE_REGISTERED")
        self.assertEqual(self.cls("GAS", api, "2019-02-01"), "CONFLICTING")      # a gas firm registered for API only
        self.assertEqual(self.cls("INJECTION", [snap("2026-10-19", "ANALYSIS; LABEL; PACK", CUR)], "2022-09-21"),
                         "CONFLICTING")
        self.assertEqual(ra.conflict_kind({"ANALYSIS", "LABEL", "PACK"}), "LABEL_OR_PACK_ONLY")

    def test_the_exclusion_list_is_not_a_registration(self):
        snaps = [snap("2026-10-19", "MANUFACTURE", EXCL), snap("2026-10-19", "PACK", CUR)]
        self.assertEqual(self.cls("TABLET", snaps, "2026-01-01"), "CONFLICTING")
        self.assertEqual(self.cls("TABLET", [], "2026-01-01"), "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
