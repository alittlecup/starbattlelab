import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell


def rows_region(dim):
    return [[r + 1 for _ in range(dim)] for r in range(dim)]


class TestT1(unittest.TestCase):
    def test_adjacency_marks_8_neighbors(self):
        st = CandidateState(rows_region(3), stars=1)
        st.set_cell(1, 1, STAR)
        d = adjacency_elimination(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.technique_name, "adjacency_elimination")
        self.assertEqual(d.tier, 1)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertEqual(marked, {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)})
        self.assertTrue(all(s == ELIMINATED for (_, _, s) in d.marks))

    def test_adjacency_none_when_no_star(self):
        st = CandidateState(rows_region(3), stars=1)
        self.assertIsNone(adjacency_elimination(st))

    def test_unit_complete_eliminates_rest_of_row(self):
        st = CandidateState([[c + 1 for c in range(3)] for _ in range(3)], stars=1)
        st.set_cell(0, 0, STAR)
        d = unit_complete(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 1), marked)
        self.assertIn((0, 2), marked)
        self.assertIn((1, 0), marked)
        self.assertIn((2, 0), marked)

    def test_last_cell_places_star(self):
        st = CandidateState([[c + 1 for c in range(3)] for _ in range(3)], stars=1)
        st.set_cell(0, 0, ELIMINATED)
        st.set_cell(0, 1, ELIMINATED)
        d = last_cell(st)
        self.assertIsNotNone(d)
        self.assertIn((0, 2, STAR), d.marks)

    def test_last_cell_none_when_multiple_unknown(self):
        st = CandidateState([[c + 1 for c in range(3)] for _ in range(3)], stars=1)
        self.assertIsNone(last_cell(st))


if __name__ == "__main__":
    unittest.main()
