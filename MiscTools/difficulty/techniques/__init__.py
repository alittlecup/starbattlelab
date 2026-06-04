# techniques package
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell
from techniques.t2_geometry import region_confined_to_line, exclusion
from techniques.t2_counting import undercounting, overcounting


def _tag(fn, tier):
    fn.tier = tier
    return fn


ALL_TECHNIQUES = [
    _tag(adjacency_elimination, 1),
    _tag(unit_complete, 1),
    _tag(last_cell, 1),
    _tag(region_confined_to_line, 2),
    _tag(exclusion, 2),
    _tag(undercounting, 2),
    _tag(overcounting, 2),
]
