"""基础技巧。每个函数 find(state)->Deduction|None。

按 RULES.md 的细粒度阶梯拆分：行/列 与 区域 分开（rule_id 对应难度配置）。
.tier 仅用于引擎"由易到难"的选用顺序，难度数值由计分器按 rule_id 查区间得到。
"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction


def adjacency_elimination(state):
    """规则 2：星的 8 邻格不能再有星。"""
    marks = []
    seen = set()
    for r in range(state.dim):
        for c in range(state.dim):
            if state.grid[r][c] == STAR:
                for (nr, nc) in state.neighbors(r, c):
                    if state.grid[nr][nc] == UNKNOWN and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        marks.append((nr, nc, ELIMINATED))
    if not marks:
        return None
    return Deduction("adjacency_elimination", 2, marks,
                     "星的 8 邻格不能再有星", rule_id="adjacency")


def _complete(state, want_region):
    """单元已放满所需星数 → 其余 UNKNOWN 清除。want_region 切换 区域 / 行列。"""
    marks = []
    seen = set()
    for (kind, _key, cells) in state.all_units():
        is_region = (kind == "region")
        if is_region != want_region:
            continue
        if state.count_state(cells, STAR) == state.stars:
            for (r, c) in state.unknowns(cells):
                if (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, ELIMINATED))
    return marks


def line_complete(state):
    """规则 1：某行/列已满星 → 其余格打叉。"""
    marks = _complete(state, want_region=False)
    if not marks:
        return None
    return Deduction("line_complete", 1, marks,
                     "行/列已放满所需星数，其余格清除", rule_id="row_col_complete")


def region_complete(state):
    """规则 3：某区域已满星 → 其余格打叉。"""
    marks = _complete(state, want_region=True)
    if not marks:
        return None
    return Deduction("region_complete", 3, marks,
                     "区域已放满所需星数，其余格清除", rule_id="region_complete")


def _last_cell(state, want_region):
    """单元剩余 UNKNOWN 数恰等于待放星数 → 这些格必为星。"""
    marks = []
    seen = set()
    for (kind, _key, cells) in state.all_units():
        is_region = (kind == "region")
        if is_region != want_region:
            continue
        placed = state.count_state(cells, STAR)
        unk = state.unknowns(cells)
        if placed < state.stars and len(unk) == state.stars - placed:
            for (r, c) in unk:
                if (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, STAR))
    return marks


def line_last_cell(state):
    """规则 4：某行/列只剩一个空格 → 必是星。"""
    marks = _last_cell(state, want_region=False)
    if not marks:
        return None
    return Deduction("line_last_cell", 4, marks,
                     "行/列剩余空格数恰等于待放星数", rule_id="row_col_last")


def region_last_cell(state):
    """规则 5：某区域只剩一个空格 → 必是星。"""
    marks = _last_cell(state, want_region=True)
    if not marks:
        return None
    return Deduction("region_last_cell", 5, marks,
                     "区域剩余空格数恰等于待放星数", rule_id="region_last")


# .tier = 引擎选用顺序（数字越小越先用）
adjacency_elimination.tier = 2
line_complete.tier = 1
region_complete.tier = 3
line_last_cell.tier = 4
region_last_cell.tier = 5
