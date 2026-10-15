from pathlib import Path
import unittest

from clinvar_monitor.vcf import (
    classification_group,
    extract_variants,
    parse_gene_symbols,
    parse_info,
    review_stars,
)


ROOT = Path(__file__).resolve().parents[1]


class TestVCF(unittest.TestCase):
    def test_parse_info(self):
        parsed = parse_info("ALLELEID=12;CLNSIG=Likely_benign;FLAG")
        self.assertEqual(parsed["ALLELEID"], "12")
        self.assertEqual(parsed["CLNSIG"], "Likely_benign")
        self.assertEqual(parsed["FLAG"], "true")

    def test_gene_symbols(self):
        self.assertEqual(parse_gene_symbols("BRCA1:672|NBR2:10230"), ["BRCA1", "NBR2"])

    def test_review_stars(self):
        self.assertEqual(review_stars("practice_guideline"), 4)
        self.assertEqual(review_stars("reviewed_by_expert_panel"), 3)
        self.assertEqual(review_stars("criteria_provided,_multiple_submitters,_no_conflicts"), 2)
        self.assertEqual(review_stars("criteria_provided,_conflicting_classifications"), 1)
        self.assertEqual(review_stars("no_assertion_criteria_provided"), 0)

    def test_classification_groups(self):
        self.assertEqual(classification_group("Uncertain_significance"), "Uncertain significance")
        self.assertEqual(classification_group("Likely_pathogenic"), "Likely pathogenic")
        self.assertEqual(
            classification_group("Likely_pathogenic/Pathogenic"),
            "Pathogenic / likely pathogenic",
        )
        self.assertEqual(
            classification_group("Conflicting_classifications_of_pathogenicity"),
            "Conflicting",
        )

    def test_extract_demo(self):
        path = ROOT / "data" / "demo" / "clinvar_demo_earlier.vcf"
        frame = extract_variants(path, ["BRCA1", "BRCA2", "PALB2", "CHEK2", "ATM", "TP53"])
        self.assertEqual(len(frame), 6)
        self.assertIn("BRCA1", set(frame["selected_genes"]))
        self.assertEqual(str(frame["variation_id"].dtype), "string")


if __name__ == "__main__":
    unittest.main()

