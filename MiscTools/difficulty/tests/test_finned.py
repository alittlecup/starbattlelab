import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState
from techniques.t2_finned import finned_counts, _finned_over


class TestFinned(unittest.TestCase):
    def test_finned_undercounting_single_fin(self):
        # A=1={(0,0),(1,0),(2,0)}（(2,0) 为鳍），B=2={(0,3),(1,3)}，其余=C=3。
        # 干净欠计数消除行0/1 的 C 格；与鳍 (2,0) 邻格交集 → 只剩 (1,1)。
        region = [
            [1, 3, 3, 2, 3],
            [1, 3, 3, 2, 3],
            [1, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
            [3, 3, 3, 3, 3],
        ]
        st = CandidateState(region, stars=1)
        d = finned_counts(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "finned_counts")
        self.assertEqual(d.meta["dir"], "under")
        self.assertEqual(d.meta["k"], 2)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((1, 1), marked)

    def test_finned_overcounting_single_fin(self):
        # 行 0、1 的候选落在区域 {A=1, B=2, g=3}（k+1=3）。g 在这两行只有单鳍 (1,2)。
        # 干净过计数消除 base 区域(A,B)在行0/1 之外的格；与鳍 (1,2) 邻格交集 → 只剩 (2,1)。
        region = [
            [1, 1, 1, 2, 2],
            [1, 1, 3, 2, 2],
            [1, 1, 4, 5, 5],
            [4, 4, 4, 5, 5],
            [4, 4, 4, 5, 5],
        ]
        st = CandidateState(region, stars=1)
        d = _finned_over(st, 2, "row")     # 直接测过计数逻辑（隔离欠计数的抢先）
        self.assertIsNotNone(d)
        self.assertEqual(d.meta["dir"], "over")
        self.assertEqual(d.meta["k"], 2)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((2, 1), marked)

    def test_none_on_empty_simple_board(self):
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        self.assertIsNone(finned_counts(st))


if __name__ == "__main__":
    unittest.main()
