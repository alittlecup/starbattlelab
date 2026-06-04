# techniques package
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell


def _tag(fn, tier):
    fn.tier = tier
    return fn


# 按 tier 升序排列；新增技巧在此登记即可被引擎使用。
ALL_TECHNIQUES = [
    _tag(adjacency_elimination, 1),
    _tag(unit_complete, 1),
    _tag(last_cell, 1),
]
