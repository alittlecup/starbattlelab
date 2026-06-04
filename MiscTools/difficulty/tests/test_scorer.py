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


def step(rule_id, meta=None):
    return Step("name", 1, [(0, 0, 1)], "r", rule_id=rule_id, meta=meta or {})


def sc(steps):
    return score_trace(Trace(steps=steps, solved=True), CONFIG)


class TestScorer(unittest.TestCase):
    def test_unsolved_is_expert(self):
        t = Trace(steps=[step("region_confined")], solved=False, stuck_state=object())
        r = score_trace(t, CONFIG)
        self.assertEqual(r["band"], "Expert")
        self.assertGreater(r["score"], CONFIG["maxDifficulty"])

    def test_factor_maps_to_interval_bounds(self):
        easy = sc([step("region_confined", {"contiguous": True, "count": 2})])
        hard = sc([step("region_confined", {"contiguous": False, "count": 7})])
        self.assertAlmostEqual(easy["score"], 40)    # lo
        self.assertAlmostEqual(hard["score"], 250)   # hi

    def test_count_increases_difficulty_within_half(self):
        a = sc([step("region_confined", {"contiguous": True, "count": 2})])
        b = sc([step("region_confined", {"contiguous": True, "count": 5})])
        self.assertLess(a["score"], b["score"])

    def test_noncontiguous_harder_than_contiguous(self):
        c = sc([step("region_confined", {"contiguous": True, "count": 2})])
        nc = sc([step("region_confined", {"contiguous": False, "count": 2})])
        self.assertLess(c["score"], nc["score"])

    def test_hardest_step_wins(self):
        t = sc([step("region_confined", {"contiguous": True, "count": 2}),
                step("exclusion", {"candidate_count": 7})])
        self.assertEqual(t["hardest_rule"], "exclusion")
        self.assertAlmostEqual(t["score"], 300)

    def test_band_from_category(self):
        self.assertEqual(sc([step("row_col_complete")])["band"], "Easy")
        self.assertEqual(sc([step("region_confined", {"contiguous": True, "count": 2})])["band"], "Medium")


if __name__ == "__main__":
    unittest.main()
