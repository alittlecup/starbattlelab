# techniques package
#
# 每个技巧函数在其所属模块里设置 .tier（来自模块 TIER 常量）——这是 tier 的单一来源，
# 引擎排序与 Deduction 计分共用同一值。新增技巧：在对应模块设好 .tier，在此按 tier 升序登记即可。
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell
from techniques.t2_geometry import region_confined_to_line, exclusion
from techniques.t2_counting import undercounting, overcounting

ALL_TECHNIQUES = [
    adjacency_elimination,
    unit_complete,
    last_cell,
    region_confined_to_line,
    exclusion,
    undercounting,
    overcounting,
]
