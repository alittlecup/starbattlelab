import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from techniques.t1_basic import (
    adjacency_elimination, line_complete, region_complete,
    line_last_cell, region_last_cell,
)


def vcols(dim):
    # 竖直区域：region id == 列号+1
    return [[c + 1 for c in range(dim)] for _ in range(dim)]


class TestT1(unittest.TestCase):
    def test_adjacency_marks_8_neighbors(self):
        st = CandidateState([[r + 1 for _ in range(3)] for r in range(3)], stars=1)
        st.set_cell(1, 1, STAR)
        d = adjacency_elimination(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "adjacency")
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertEqual(marked, {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)})

    def test_adjacency_none_when_no_star(self):
        st = CandidateState(vcols(3), stars=1)
        self.assertIsNone(adjacency_elimination(st))

    def test_line_complete_row_and_col(self):
        st = CandidateState(vcols(3), stars=1)
        st.set_cell(0, 0, STAR)
        d = line_complete(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "row_col_complete")
        m = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 1), m); self.assertIn((0, 2), m)   # 行 0
        self.assertIn((1, 0), m); self.assertIn((2, 0), m)   # 列 0

    def test_region_complete_only_region(self):
        st = CandidateState(vcols(3), stars=1)
        st.set_cell(0, 0, STAR)
        d = region_complete(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "region_complete")
        m = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((1, 0), m); self.assertIn((2, 0), m)   # 区域=列0
        self.assertNotIn((0, 1), m); self.assertNotIn((0, 2), m)  # 不含行方向

    def test_line_last_cell(self):
        st = CandidateState(vcols(3), stars=1)
        st.set_cell(0, 0, ELIMINATED); st.set_cell(0, 1, ELIMINATED)
        d = line_last_cell(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "row_col_last")
        self.assertIn((0, 2, STAR), d.marks)

    def test_region_last_cell(self):
        st = CandidateState(vcols(3), stars=1)
        st.set_cell(0, 0, ELIMINATED); st.set_cell(1, 0, ELIMINATED)
        d = region_last_cell(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "region_last")
        self.assertIn((2, 0, STAR), d.marks)

    def test_none_when_inapplicable(self):
        st = CandidateState(vcols(3), stars=1)
        self.assertIsNone(line_complete(st))
        self.assertIsNone(region_complete(st))
        self.assertIsNone(line_last_cell(st))
        self.assertIsNone(region_last_cell(st))


if __name__ == "__main__":
    unittest.main()
