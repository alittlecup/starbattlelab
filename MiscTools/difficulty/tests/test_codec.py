import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sbn_codec import decode_to_grid


class TestSbnCodec(unittest.TestCase):
    def test_decode_5x5_one_star(self):
        result = decode_to_grid("551W9jo0cIn")
        self.assertIsNotNone(result)
        self.assertEqual(result["dim"], 5)
        self.assertEqual(result["stars"], 1)
        grid = result["region_grid"]
        self.assertEqual(len(grid), 5)
        self.assertTrue(all(len(row) == 5 for row in grid))
        region_ids = {cell for row in grid for cell in row}
        self.assertEqual(len(region_ids), 5)

    def test_decode_8x8_one_star(self):
        result = decode_to_grid("881W8AKBNEeYHXnmB62j6O0")
        self.assertEqual(result["dim"], 8)
        self.assertEqual(result["stars"], 1)
        region_ids = {cell for row in result["region_grid"] for cell in row}
        self.assertEqual(len(region_ids), 8)

    def test_decode_invalid_returns_none(self):
        self.assertIsNone(decode_to_grid("not-a-real-sbn"))


if __name__ == "__main__":
    unittest.main()
