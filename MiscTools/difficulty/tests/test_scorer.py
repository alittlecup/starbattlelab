import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduction import Step, Trace
from scorer import score_trace

CONFIG = {
    "maxDifficulty": 1000,
    "rules": {
        "row_col_complete": {"lo": 1, "hi": 11},
        "region_confined": {"lo": 40, "hi": 250},
        "exclusion": {"lo": 100, "hi": 300},
    },
}


def step(rule_id, tier):
    return Step("name", tier, [(0, 0, 1)], "r", rule_id=rule_id)


class TestScorer(unittest.TestCase):
    def test_unsolved_is_expert(self):
        t = Trace(steps=[step("row_col_complete", 1)], solved=False, stuck_state=object())
        r = score_trace(t, CONFIG)
        self.assertEqual(r["band"], "Expert")
        self.assertGreater(r["score"], CONFIG["maxDifficulty"])

    def test_score_is_midpoint_of_hardest_rule(self):
        t = Trace(steps=[step("row_col_complete", 1), step("region_confined", 6)], solved=True)
        r = score_trace(t, CONFIG)
        self.assertEqual(r["hardest_rule"], "region_confined")
        self.assertEqual(r["score"], (40 + 250) / 2.0)

    def test_harder_rule_scores_higher(self):
        t1 = Trace(steps=[step("region_confined", 6)], solved=True)
        t2 = Trace(steps=[step("exclusion", 7)], solved=True)
        self.assertLess(score_trace(t1, CONFIG)["score"], score_trace(t2, CONFIG)["score"])

    def test_band_from_category(self):
        t = Trace(steps=[step("row_col_complete", 1)], solved=True)
        self.assertEqual(score_trace(t, CONFIG)["band"], "Easy")
        t2 = Trace(steps=[step("region_confined", 6)], solved=True)
        self.assertEqual(score_trace(t2, CONFIG)["band"], "Medium")


if __name__ == "__main__":
    unittest.main()
