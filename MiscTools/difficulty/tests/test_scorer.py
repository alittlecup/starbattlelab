import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduction import Step, Trace
from scorer import score_trace


def step(name, tier):
    return Step(name, tier, [(0, 0, 1)], "r")


class TestScorer(unittest.TestCase):
    def test_unsolved_is_expert(self):
        t = Trace(steps=[step("a", 1)], solved=False, stuck_state=object())
        result = score_trace(t)
        self.assertEqual(result["band"], "Expert")

    def test_band_from_max_tier(self):
        t1 = Trace(steps=[step("last_cell", 1)], solved=True)
        t2 = Trace(steps=[step("last_cell", 1), step("exclusion", 2)], solved=True)
        self.assertEqual(score_trace(t1)["band"], "Easy")
        self.assertEqual(score_trace(t2)["band"], "Medium")

    def test_higher_tier_scores_higher(self):
        t1 = Trace(steps=[step("last_cell", 1)], solved=True)
        t2 = Trace(steps=[step("exclusion", 2)], solved=True)
        self.assertLess(score_trace(t1)["score"], score_trace(t2)["score"])

    def test_more_hard_steps_scores_higher_within_band(self):
        few = Trace(steps=[step("exclusion", 2)], solved=True)
        many = Trace(steps=[step("exclusion", 2), step("undercounting", 2),
                            step("overcounting", 2)], solved=True)
        self.assertLess(score_trace(few)["score"], score_trace(many)["score"])


if __name__ == "__main__":
    unittest.main()
