import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


class TestDashboard(unittest.TestCase):
    def test_demo_dashboard(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)

        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "6")
        self.assertEqual(app.metric[1].value, "3")

    def test_compact_official_results(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        app.text_input[0].set_value(str(ROOT / "reports" / "real_2026")).run(timeout=30)

        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "69,423")
        self.assertEqual(app.metric[1].value, "1,018")
        self.assertTrue(
            any("Compact portfolio view" in message.value for message in app.info)
        )


if __name__ == "__main__":
    unittest.main()
