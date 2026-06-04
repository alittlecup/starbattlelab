import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibrate import summarize_file


class TestCalibrate(unittest.TestCase):
    def test_summarize_file_structure(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("551W9jo0cIn\n")
            f.write("881W8AKBNEeYHXnmB62j6O0\n")
            path = f.name
        try:
            s = summarize_file(path)
            self.assertEqual(s["count"], 2)
            self.assertIn("solved_rate", s)
            self.assertIn("avg_score", s)
            self.assertIn("band_distribution", s)
            self.assertIsInstance(s["band_distribution"], dict)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
