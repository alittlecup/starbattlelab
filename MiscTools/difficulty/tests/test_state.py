import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED, is_complete_valid


def make_3x3_rows():
    # region id == 行号+1（3 个水平区域）
    return [[1, 1, 1], [2, 2, 2], [3, 3, 3]]


class TestCandidateState(unittest.TestCase):
    def test_init_all_unknown(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        self.assertEqual(st.dim, 3)
        self.assertEqual(st.stars, 1)
        for r in range(3):
            for c in range(3):
                self.assertEqual(st.grid[r][c], UNKNOWN)

    def test_region_cells_grouping(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        self.assertEqual(sorted(st.region_cells.keys()), [1, 2, 3])
        self.assertEqual(set(st.region_cells[1]), {(0, 0), (0, 1), (0, 2)})

    def test_set_and_count(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        st.set_cell(0, 0, STAR)
        self.assertEqual(st.count_state(st.cells_of_row(0), STAR), 1)
        self.assertEqual(len(st.unknowns(st.cells_of_row(0))), 2)

    def test_neighbors_corner(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        self.assertEqual(set(st.neighbors(0, 0)), {(0, 1), (1, 0), (1, 1)})

    def test_apply_deduction_changes_cells(self):
        from deduction import Deduction
        st = CandidateState(make_3x3_rows(), stars=1)
        st.apply(Deduction("t", 1, [(1, 1, STAR), (0, 0, ELIMINATED)], "r"))
        self.assertEqual(st.grid[1][1], STAR)
        self.assertEqual(st.grid[0][0], ELIMINATED)

    def test_is_complete_valid_true(self):
        # 合法 5x5 解；区域取列分组，星位列互异且互不相邻
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        for (r, c) in [(0, 0), (1, 2), (2, 4), (3, 1), (4, 3)]:
            st.set_cell(r, c, STAR)
        self.assertTrue(is_complete_valid(st))

    def test_is_complete_valid_false_when_incomplete(self):
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        st.set_cell(0, 0, STAR)
        self.assertFalse(is_complete_valid(st))

    def test_is_complete_valid_false_when_adjacent_stars(self):
        # 每行/列/区域各 1 星，但对角线相邻 -> 必须判为非法
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        for (r, c) in [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]:
            st.set_cell(r, c, STAR)
        self.assertFalse(is_complete_valid(st))


if __name__ == "__main__":
    unittest.main()
