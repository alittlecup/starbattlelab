"""解题推理的数据结构。"""


class Deduction:
    """一个技巧在当前局面下得出的一批确定标记。

    marks: list of (row, col, new_state)
    """

    def __init__(self, technique_name, tier, marks, reason):
        self.technique_name = technique_name
        self.tier = tier
        self.marks = marks
        self.reason = reason


class Step:
    """引擎应用一次 Deduction 后记录的一步。"""

    def __init__(self, technique_name, tier, marks, reason):
        self.technique_name = technique_name
        self.tier = tier
        self.marks = marks
        self.reason = reason

    @classmethod
    def from_deduction(cls, d):
        return cls(d.technique_name, d.tier, d.marks, d.reason)


class Trace:
    """一次解题的完整轨迹。"""

    def __init__(self, steps=None, solved=False, stuck_state=None):
        self.steps = steps if steps is not None else []
        self.solved = solved
        self.stuck_state = stuck_state
