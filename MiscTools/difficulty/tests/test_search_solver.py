import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sbn_codec import decode_to_grid
from candidate_state import CandidateState
from search_solver import solve_complete


class TestSearchSolver(unittest.TestCase):
    def test_finds_exactly_one_solution(self):
        decoded = decode_to_grid("551W9jo0cIn")
        st = CandidateState(decoded["region_grid"], decoded["stars"])
        res = solve_complete(st, max_solutions=2)
        self.assertEqual(len(res["solutions"]), 1)   # 唯一解
        self.assertGreaterEqual(res["guesses"], 0)
        self.assertGreaterEqual(res["depth"], 0)

    def test_solution_is_valid(self):
        from candidate_state import STAR, is_complete_valid
        decoded = decode_to_grid("881W8AKBNEeYHXnmB62j6O0")
        st = CandidateState(decoded["region_grid"], decoded["stars"])
        res = solve_complete(st, max_solutions=2)
        self.assertEqual(len(res["solutions"]), 1)
        # 用解集重建并校验确为合法完整解
        sol = res["solutions"][0]
        check = CandidateState(decoded["region_grid"], decoded["stars"])
        for (r, c) in sol:
            check.set_cell(r, c, STAR)
        self.assertTrue(is_complete_valid(check))


if __name__ == "__main__":
    unittest.main()
