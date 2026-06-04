import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate import analyze


class TestRate(unittest.TestCase):
    def test_analyze_returns_band_and_score(self):
        result = analyze("551W9jo0cIn")
        self.assertIsNotNone(result)
        self.assertIn("band", result)
        self.assertIn("score", result)
        self.assertIn("solved", result)
        self.assertIn("steps", result)

    def test_analyze_invalid_sbn(self):
        result = analyze("garbage")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
