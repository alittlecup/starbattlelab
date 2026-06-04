"""解题推理的数据结构。"""


class Deduction:
    """一个技巧在当前局面下得出的一批确定标记。

    marks: list of (row, col, new_state)
    """

    def __init__(self, technique_name, tier, marks, reason, rule_id=None, meta=None):
        self.technique_name = technique_name
        self.tier = tier
        self.marks = marks
        self.reason = reason
        # rule_id：对应难度配置（difficulty-config.json）里的规则键，供计分器查区间。
        # 默认回退到 technique_name。
        self.rule_id = rule_id if rule_id is not None else technique_name
        # meta：该步的结构因子（如 {"contiguous": False, "count": 4} / {"axis":"row","k":3}），
        # 供 factors.complexity() 计算"区间内的具体难度位置"。
        self.meta = meta if meta is not None else {}


class Step:
    """引擎应用一次 Deduction 后记录的一步。"""

    def __init__(self, technique_name, tier, marks, reason, rule_id=None, meta=None):
        self.technique_name = technique_name
        self.tier = tier
        self.marks = marks
        self.reason = reason
        self.rule_id = rule_id if rule_id is not None else technique_name
        self.meta = meta if meta is not None else {}

    @classmethod
    def from_deduction(cls, d):
        return cls(d.technique_name, d.tier, d.marks, d.reason, d.rule_id, d.meta)


class Trace:
    """一次解题的完整轨迹。"""

    def __init__(self, steps=None, solved=False, stuck_state=None):
        self.steps = steps if steps is not None else []
        self.solved = solved
        self.stuck_state = stuck_state
