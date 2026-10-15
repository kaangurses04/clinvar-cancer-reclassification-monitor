import unittest

from clinvar_monitor.download import release_url


class TestDownload(unittest.TestCase):
    def test_release_url(self):
        self.assertEqual(
            release_url("2026-09-28"),
            "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/"
            "archive_2.0/2026/clinvar_20260928.vcf.gz",
        )

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            release_url("09/28/2026")


if __name__ == "__main__":
    unittest.main()

