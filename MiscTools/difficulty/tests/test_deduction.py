import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduction import Deduction, Step, Trace


class TestDeduction(unittest.TestCase):
    def test_deduction_fields(self):
        d = Deduction("adjacency_elimination", 1, [(0, 0, 2)], "邻接消除")
        self.assertEqual(d.technique_name, "adjacency_elimination")
        self.assertEqual(d.tier, 1)
        self.assertEqual(d.marks, [(0, 0, 2)])
        self.assertEqual(d.reason, "邻接消除")

    def test_step_from_deduction(self):
        d = Deduction("t", 2, [(1, 1, 1)], "r")
        step = Step.from_deduction(d)
        self.assertEqual(step.technique_name, "t")
        self.assertEqual(step.tier, 2)
        self.assertEqual(step.marks, [(1, 1, 1)])

    def test_trace_defaults(self):
        t = Trace()
        self.assertEqual(t.steps, [])
        self.assertFalse(t.solved)
        self.assertIsNone(t.stuck_state)


if __name__ == "__main__":
    unittest.main()
