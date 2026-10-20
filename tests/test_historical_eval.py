"""Pinned DST-04B rules (plan A5): classification precedence, injectable rule, outcome NDCs, metrics."""

import io
import unittest

from fineprint import historical_eval as he
from fineprint import spl
from tests import spl_factory as sf

RM, OTHER = he.ROCKY_MOUNT, "222222222"
MFG, PACK = ("C43360", "MANUFACTURE"), ("C84731", "PACK")


def evidence(**kw):
    doc = spl.parse_spl(io.BytesIO(sf.spl_xml("s", 1, products=[("0409-0001", "X", [])], **kw)))
    return he.product_evidence(doc)["0409-0001"]


class Classification(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(he.classify(evidence(establishments=[(RM, "RM", [(*MFG, ["0409-0001"])]),
                                                              (OTHER, "O", [(*MFG, ["0409-0001"])])])), "DIRECT")
        self.assertEqual(he.classify(evidence(establishments=[(OTHER, "O", [(*MFG, ["0409-0001"])]),
                                                              (RM, "RM", [(*PACK, ["0409-0001"])])])), "OTHER_SITE")
        self.assertEqual(he.classify(evidence(establishments=[(RM, "RM", [(*PACK, ["0409-0001"])])])),
                         "RM_SECONDARY_ONLY")
        self.assertEqual(he.classify(evidence(with_block=False)), "UNKNOWN_NO_ESTABLISHMENT")
        self.assertEqual(he.classify(evidence(establishments=[(OTHER, "O", [(*MFG, [])])])),
                         "UNKNOWN_UNSCOPED_OPERATION")
        self.assertEqual(he.classify(evidence(establishments=[(OTHER, "O", [(*PACK, ["0409-0001"])])])),
                         "UNKNOWN_NO_MANUFACTURE_OP")
        self.assertEqual(he.classify(evidence(establishments=[("", "no duns", [(*MFG, ["0409-0001"])])])),
                         "UNKNOWN_MANUFACTURE_WITHOUT_DUNS")

    def test_pack_or_label_at_rocky_mount_is_never_direct(self):
        ev = evidence(establishments=[(RM, "RM", [(*PACK, ["0409-0001"]), ("C84732", "LABEL", ["0409-0001"])])])
        self.assertNotEqual(he.classify(ev), "DIRECT")

    def test_multi_provenance_any_direct_wins(self):
        self.assertEqual(he.combine(["OTHER_SITE", "DIRECT"]), "DIRECT")
        self.assertEqual(he.combine(["UNKNOWN_NO_ESTABLISHMENT", "OTHER_SITE"]), "OTHER_SITE")


class Baselines(unittest.TestCase):
    def test_injectable_rule(self):
        self.assertEqual(he.injectable("INJECTION, SOLUTION", []), "INJECTABLE")
        self.assertEqual(he.injectable("SOLUTION", ["INTRAVENOUS"]), "INJECTABLE")
        self.assertEqual(he.injectable("TABLET", ["ORAL"]), "NOT_INJECTABLE")
        self.assertEqual(he.injectable(None, []), "UNCLASSIFIED")


class OutcomeNdc(unittest.TestCase):
    def test_package_normalization_never_uses_product_codes(self):
        self.assertEqual(he.normalize_outcome_ndc("0409-4888-02"), "00409-4888-02")
        self.assertEqual(he.normalize_outcome_ndc("00409-4888-02"), "00409-4888-02")
        self.assertEqual(he.normalize_outcome_ndc("00409488802"), "00409-4888-02")
        self.assertIsNone(he.normalize_outcome_ndc("0409-4888"))      # product code: not a package
        self.assertIsNone(he.normalize_outcome_ndc("0409488802"))     # unhyphenated 10-digit: ambiguous

    def test_spaced_hyphens_from_pdf_text_layer(self):
        text = "Chain NDC 00409 - 3308 - 03 Acetylcysteine 6 g/30 mL 00409 - 4911 - 34 0.1 mg/mL; call 844 - 646 - 4398"
        self.assertEqual(he.extract_ndc_tokens(text), ["00409-3308-03", "00409-4911-34"])

    def test_stray_space_inside_segment_only_when_exactly_542(self):
        self.assertEqual(he.extract_ndc_tokens("needle 00409-114 1-02 23.4% Sodium"), ["00409-1141-02"])
        self.assertEqual(he.extract_ndc_tokens("00409-11 41-0 2 x"), ["00409-1141-02"])
        self.assertEqual(he.extract_ndc_tokens("00409-114 12-02"), [])          # would be 5-5-2: refused
        self.assertEqual(he.extract_ndc_tokens("lot 12345-6789-01 2026"), ["12345-6789-01"])

    def test_token_regex(self):
        text = "NDC 0409-4888-02 and 00409-1234-01; lot 1234-567; 00409123401x"
        self.assertEqual(he.NDC_TOKEN.findall(text), ["0409-4888-02", "00409-1234-01"])


class Metrics(unittest.TestCase):
    def test_metrics_and_matching_size(self):
        cohort = {f"p{i}" for i in range(10)}
        m = he.metrics(cohort, flags={"p0", "p1", "p2", "p3"}, positives={"p0", "p1", "p9", "zz"})
        self.assertEqual((m["N"], m["X"], m["positives_in_cohort"]), (4, 2, 3))
        self.assertEqual(m["recall_named"], 0.5)
        self.assertEqual(m["recall_panel_conditional"], round(2 / 3, 4))
        self.assertEqual(m["reduction_vs_B1"], 0.6)
        b1 = he.metrics(cohort, flags=cohort, positives={"p0", "p1", "p9", "zz"})
        self.assertEqual(he.size_to_match_recall(0.5, b1), round(0.5 / 0.75 * 10, 1))
        self.assertEqual(he.size_to_match_recall(0.9, b1), "unreachable")


if __name__ == "__main__":
    unittest.main()
