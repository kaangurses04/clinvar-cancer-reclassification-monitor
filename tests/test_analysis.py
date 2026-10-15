from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from clinvar_monitor.analysis import change_evidence_matrix, compare_releases, generate_outputs
from clinvar_monitor.vcf import extract_variants


ROOT = Path(__file__).resolve().parents[1]
GENES = ["BRCA1", "BRCA2", "PALB2", "CHEK2", "ATM", "TP53"]


class TestAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.earlier = extract_variants(ROOT / "data" / "demo" / "clinvar_demo_earlier.vcf", GENES)
        cls.later = extract_variants(ROOT / "data" / "demo" / "clinvar_demo_later.vcf", GENES)

    def test_change_detection(self):
        comparison = compare_releases(self.earlier, self.later)
        changes = dict(zip(comparison["variation_id"], comparison["change_type"]))
        self.assertEqual(changes["DEMO1001"], "Classification changed")
        self.assertEqual(changes["DEMO1003"], "Unchanged")
        self.assertEqual(changes["DEMO1004"], "Added in later release")
        self.assertEqual(changes["DEMO1005"], "Review status changed")
        self.assertEqual(changes["DEMO1007"], "Removed from later release")

    def test_original_classification_evidence_context(self):
        comparison = compare_releases(self.earlier, self.later)
        contexts = dict(zip(comparison["variation_id"], comparison["evidence_context"]))
        self.assertEqual(
            contexts["DEMO1001"],
            "Classification changed; review strengthened",
        )
        self.assertEqual(
            contexts["DEMO1006"],
            "Classification changed; review weakened",
        )
        self.assertEqual(
            contexts["DEMO1005"],
            "Classification stable; review strengthened",
        )
        matrix = change_evidence_matrix(comparison)
        self.assertEqual(int(matrix["variant_count"].sum()), len(comparison))

    def test_generate_outputs(self):
        with TemporaryDirectory() as temp:
            summary = generate_outputs(
                self.earlier,
                self.later,
                "Demo A",
                "Demo B",
                temp,
            )
            self.assertEqual(summary["classification_changes"], 3)
            self.assertTrue((Path(temp) / "REPORT.md").exists())
            self.assertTrue((Path(temp) / "figures" / "comparison_outcomes.png").exists())
            self.assertTrue((Path(temp) / "change_evidence_matrix.csv").exists())
            self.assertTrue(
                (Path(temp) / "figures" / "classification_changes_by_evidence_direction.png").exists()
            )


if __name__ == "__main__":
    unittest.main()

