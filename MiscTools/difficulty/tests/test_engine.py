import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, STAR, is_complete_valid
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell
from engine import solve


class TestEngine(unittest.TestCase):
    def _vertical_regions(self, dim):
        return [[c + 1 for c in range(dim)] for _ in range(dim)]

    def test_solves_from_four_placed_stars(self):
        st = CandidateState(self._vertical_regions(5), stars=1)
        for (r, c) in [(0, 0), (1, 2), (2, 4), (3, 1)]:
            st.set_cell(r, c, STAR)
        techniques = [adjacency_elimination, unit_complete, last_cell]
        trace = solve(st, techniques)
        self.assertTrue(trace.solved)
        self.assertEqual(st.grid[4][3], STAR)
        self.assertTrue(len(trace.steps) >= 1)
        # solved 不仅是标志位——结果必须是一个真正合法的 Star Battle 解
        self.assertTrue(is_complete_valid(st))

    def test_stuck_returns_unsolved_with_state(self):
        st = CandidateState(self._vertical_regions(5), stars=1)
        trace = solve(st, [last_cell])
        self.assertFalse(trace.solved)
        self.assertIsNotNone(trace.stuck_state)

    def test_registry_sorted_by_tier(self):
        from techniques import ALL_TECHNIQUES
        tiers = [getattr(t, "tier", None) for t in ALL_TECHNIQUES]
        self.assertEqual(tiers, sorted(t for t in tiers))


if __name__ == "__main__":
    unittest.main()
