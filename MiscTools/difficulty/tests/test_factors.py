import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from factors import complexity


class TestFactors(unittest.TestCase):
    def test_region_confined_strict_split(self):
        self.assertEqual(complexity("region_confined", {"contiguous": True, "count": 2}), 0.0)
        self.assertEqual(complexity("region_confined", {"contiguous": False, "count": 7}), 1.0)
        self.assertEqual(complexity("region_confined", {"contiguous": True, "count": 7}), 0.5)
        # 任何不相连 >= 任何相连（严格劈半）
        noncontig_min = complexity("region_confined", {"contiguous": False, "count": 2})
        contig_max = complexity("region_confined", {"contiguous": True, "count": 7})
        self.assertGreaterEqual(noncontig_min, contig_max)

    def test_count_monotonic_within_half(self):
        a = complexity("region_confined", {"contiguous": True, "count": 2})
        b = complexity("region_confined", {"contiguous": True, "count": 5})
        self.assertLess(a, b)

    def test_pigeonhole_k(self):
        self.assertEqual(complexity("undercounting", {"k": 2}), 0.0)
        self.assertEqual(complexity("undercounting", {"k": 7}), 1.0)
        self.assertLess(complexity("overcounting", {"k": 3}), complexity("overcounting", {"k": 5}))

    def test_exclusion_candidate_count(self):
        self.assertEqual(complexity("exclusion", {"candidate_count": 2}), 0.0)
        self.assertEqual(complexity("exclusion", {"candidate_count": 7}), 1.0)

    def test_cap_clamps_above_7(self):
        self.assertEqual(complexity("undercounting", {"k": 9}), 1.0)

    def test_unknown_rule_is_midpoint(self):
        self.assertEqual(complexity("row_col_complete", {}), 0.5)
        self.assertEqual(complexity("adjacency", {}), 0.5)


if __name__ == "__main__":
    unittest.main()
