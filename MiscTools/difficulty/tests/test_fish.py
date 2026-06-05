import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, ELIMINATED
from techniques.t3_fish import fish


def any4():
    # 区域对 fish 无关紧要，用任意 4x4 区域划分
    return [[r * 4 + c + 1 for c in range(4)] for r in range(4)]


class TestFish(unittest.TestCase):
    def test_x_wing_columns(self):
        # 第 0、2 列的候选都只剩行 0、1 -> X-Wing
        st = CandidateState(any4(), stars=1)
        for (r, c) in [(2, 0), (3, 0), (2, 2), (3, 2)]:
            st.set_cell(r, c, ELIMINATED)
        d = fish(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.meta["axis"], "col")
        self.assertEqual(d.meta["n"], 2)
        marked = {(r, c) for (r, c, s) in d.marks}
        # 行 0、行 1 里非第 0/2 列的格被打叉
        for cell in [(0, 1), (0, 3), (1, 1), (1, 3)]:
            self.assertIn(cell, marked)
        # 第 0、2 列自身不打叉
        self.assertNotIn((0, 0), marked)
        self.assertNotIn((1, 2), marked)

    def test_none_when_no_fish(self):
        st = CandidateState(any4(), stars=1)  # 全 UNKNOWN，无约束
        self.assertIsNone(fish(st))


if __name__ == "__main__":
    unittest.main()
