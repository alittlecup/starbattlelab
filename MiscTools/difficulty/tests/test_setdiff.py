import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, STAR, ELIMINATED
from techniques.t2_setdiff import set_differentials


class TestSetDiff(unittest.TestCase):
    def test_region_vs_two_rows_forces_star_and_x(self):
        # 区域 R=1 几乎占满行 0、1（仅缺 (0,3)=区域2），并多出 (2,0)。
        # R 与 L={行0,行1}：star(X)−star(O)=2−1=1，|uX|=1 → 强制 (0,3) 为星、(2,0) 打叉。
        region = [
            [1, 1, 1, 2, 1],
            [1, 1, 1, 1, 1],
            [1, 3, 3, 3, 3],
            [4, 4, 4, 5, 5],
            [4, 4, 4, 5, 5],
        ]
        st = CandidateState(region, stars=1)
        d = set_differentials(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "set_diff")
        self.assertIn((0, 3, STAR), d.marks)
        self.assertIn((2, 0, ELIMINATED), d.marks)

    def test_none_on_plain_board(self):
        # 竖直区域、全 UNKNOWN：无星数差强制
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        self.assertIsNone(set_differentials(st))


if __name__ == "__main__":
    unittest.main()
