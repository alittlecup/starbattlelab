import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, ELIMINATED
from techniques.t2_counting import undercounting, overcounting


class TestT2Counting(unittest.TestCase):
    def test_undercounting_two_regions_two_rows(self):
        region = [
            [1, 1, 2, 5],
            [1, 1, 2, 5],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        d = undercounting(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.meta["k"], 2)
        self.assertIn(d.meta["axis"], ("row", "col"))
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 3), marked)
        self.assertIn((1, 3), marked)

    def test_overcounting_two_rows_two_regions(self):
        region = [
            [1, 1, 2, 2],
            [1, 1, 2, 2],
            [1, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        d = overcounting(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((2, 0), marked)

    def test_none_when_no_pigeonhole(self):
        region = [[c + 1 for c in range(4)] for _ in range(4)]
        st = CandidateState(region, stars=1)
        self.assertIsNone(undercounting(st))


if __name__ == "__main__":
    unittest.main()
