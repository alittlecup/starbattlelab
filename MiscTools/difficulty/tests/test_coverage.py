import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coverage import analyze_file, render_state


class TestCoverage(unittest.TestCase):
    def test_analyze_file_classifies(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("551W9jo0cIn\n")
            f.write("881W8AKBNEeYHXnmB62j6O0\n")
            f.write("garbage-line\n")
            path = f.name
        try:
            report = analyze_file(path)
            self.assertEqual(report["total"], 3)
            self.assertEqual(report["unparsable"], 1)
            self.assertEqual(report["solved"] + report["stuck"], 2)
            self.assertIsInstance(report["stuck_samples"], list)
        finally:
            os.unlink(path)

    def test_render_state_returns_text(self):
        from candidate_state import CandidateState, STAR
        st = CandidateState([[1, 2], [1, 2]], stars=1)
        st.set_cell(0, 0, STAR)
        text = render_state(st)
        self.assertIsInstance(text, str)
        self.assertIn("★", text)


if __name__ == "__main__":
    unittest.main()
