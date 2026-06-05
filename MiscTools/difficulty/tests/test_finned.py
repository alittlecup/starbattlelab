import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState
from techniques.t2_finned import finned_counts


class TestFinned(unittest.TestCase):
    def test_finned_undercounting_single_fin(self):
        # 区域 A=1={(0,0),(1,0),(2,0)}（(2,0) 为鳍），B=2={(0,3),(1,3)}，其余=C=3。
        # A、B 候选几乎在行 {0,1}，A 多出鳍 (2,0)。
        # 干净欠计数会消除行0/1 的 C 格；与鳍 (2,0) 的邻格交集 → 只剩 (1,1)。
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
        self.assertEqual(d.meta["k"], 2)
        self.assertEqual(d.meta["axis"], "row")
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((1, 1), marked)

    def test_none_on_empty_simple_board(self):
        # 竖直区域、全 UNKNOWN：没有"几乎落在 k 线"的鳍结构
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        self.assertIsNone(finned_counts(st))


if __name__ == "__main__":
    unittest.main()
