# techniques package
#
# 每个技巧函数在其所属模块里设置 .tier（引擎选用顺序）与 rule_id（难度配置键）。
# 难度数值由计分器按 rule_id 查 difficulty-config.json 的区间得到，不再由 tier 决定。
# 新增技巧：实现 find(state)->Deduction|None，设好 .tier 与 rule_id，在此按 tier 升序登记。
from techniques.t1_basic import (
    adjacency_elimination, line_complete, region_complete,
    line_last_cell, region_last_cell,
)
from techniques.t2_geometry import region_confined_to_line, exclusion
from techniques.t2_counting import undercounting, overcounting
from techniques.t2_finned import finned_counts
from techniques.t2_setdiff import set_differentials
from techniques.t3_fish import fish, finned_fish

ALL_TECHNIQUES = [
    line_complete,            # tier 1
    adjacency_elimination,    # tier 2
    region_complete,          # tier 3
    line_last_cell,           # tier 4
    region_last_cell,         # tier 5
    region_confined_to_line,  # tier 6
    exclusion,                # tier 7
    undercounting,            # tier 8
    overcounting,             # tier 9
    finned_counts,            # tier 11（规则 11；带鳍计数）
    set_differentials,        # tier 12（规则 12；集合差分）
    fish,                     # tier 13（规则 13）
    finned_fish,              # tier 14（规则 14；带鳍鱼）
]
