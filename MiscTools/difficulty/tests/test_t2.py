import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from techniques.t2_geometry import region_confined_to_line, exclusion


class TestT2(unittest.TestCase):
    def test_region_confined_to_row(self):
        region = [
            [1, 1, 2, 2],
            [3, 3, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        d = region_confined_to_line(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 2), marked)
        self.assertIn((0, 3), marked)
        self.assertNotIn((0, 0), marked)
        self.assertNotIn((0, 1), marked)

    def test_region_confined_to_col(self):
        # 区域 1 = {(0,0),(1,0)} 全在第 0 列 -> 第 0 列的星锁定在区域 1
        # -> 第 0 列中属于其它区域的格 (2,0)(3,0) 被清除
        region = [
            [1, 2, 2, 2],
            [1, 2, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        d = region_confined_to_line(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((2, 0), marked)
        self.assertIn((3, 0), marked)
        self.assertNotIn((0, 0), marked)
        self.assertNotIn((1, 0), marked)

    def test_exclusion_kills_dominating_cell(self):
        # 区域 2 = {(0,2),(1,2)}，二者公共邻格 {(0,1),(1,1)} 放星会害死区域 2
        region = [
            [1, 1, 2],
            [1, 1, 2],
            [3, 3, 3],
        ]
        st = CandidateState(region, stars=1)  # 全 UNKNOWN
        d = exclusion(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 1), marked)
        self.assertIn((1, 1), marked)

    def test_techniques_return_none_when_inapplicable(self):
        region = [[c + 1 for c in range(4)] for _ in range(4)]
        st = CandidateState(region, stars=1)
        self.assertIsNone(region_confined_to_line(st))


if __name__ == "__main__":
    unittest.main()
