import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, ELIMINATED
from techniques.t3_fish import finned_fish


def any5():
    return [[r * 5 + c + 1 for c in range(5)] for r in range(5)]


class TestFinnedFish(unittest.TestCase):
    def test_finned_x_wing_single_fin(self):
        # 列0候选行{0,1,2}（含鳍行2），列2候选行{0,1}。几乎是 X-Wing(行0,1) + 鳍(2,0)。
        # 干净鱼消除行0/1 其它列；与鳍邻格交集 → 含 (1,1)。
        st = CandidateState(any5(), stars=1)
        for (r, c) in [(3, 0), (4, 0), (2, 2), (3, 2), (4, 2)]:
            st.set_cell(r, c, ELIMINATED)
        d = finned_fish(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.rule_id, "finned_fish")
        self.assertEqual(d.meta["n"], 2)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((1, 1), marked)

    def test_none_on_plain_board(self):
        st = CandidateState(any5(), stars=1)
        self.assertIsNone(finned_fish(st))


if __name__ == "__main__":
    unittest.main()
