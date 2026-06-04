"""T2 鸽笼计数技巧：undercounting / overcounting。限 stars == 1。

每次只返回**最小 k、按 行→列**找到的第一个能产出标记的实例，并把 (axis, k) 记入 meta，
使难度可按 k 在区间内定位。k 越大越难。
"""

from itertools import combinations

from candidate_state import STAR, ELIMINATED
from deduction import Deduction

MAX_PIGEONHOLE = 7  # 正常棋盘最大 14×14，故 k 最大 7


def _lines_of(unk, axis):
    return {(r if axis == "row" else c) for (r, c) in unk}


def undercounting(state):
    if state.stars != 1:
        return None
    regions = {}
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) < state.stars:
            unk = state.unknowns(cells)
            if unk:
                regions[rid] = unk
    rids = list(regions.keys())
    for k in range(2, MAX_PIGEONHOLE + 1):
        for axis in ("row", "col"):
            for combo in combinations(rids, k):
                lines = set()
                for rid in combo:
                    lines |= _lines_of(regions[rid], axis)
                if len(lines) != k:
                    continue
                combo_set = set(combo)
                marks = []
                seen = set()
                for line in lines:
                    for (r, c) in state.unknowns(state.cells_of_line(axis, line)):
                        if state.region_grid[r][c] not in combo_set and (r, c) not in seen:
                            seen.add((r, c)); marks.append((r, c, ELIMINATED))
                if marks:
                    return Deduction("undercounting", 8, marks,
                                     "k 个区域候选落在 k 条线内，锁定这些线的星于这些区域",
                                     rule_id="undercounting", meta={"axis": axis, "k": k})
    return None


def overcounting(state):
    if state.stars != 1:
        return None
    lr_by_axis = {}
    for axis in ("row", "col"):
        lr = {}
        for idx in range(state.dim):
            cells = state.unknowns(state.cells_of_line(axis, idx))
            if cells:
                lr[idx] = {state.region_grid[r][c] for (r, c) in cells}
        lr_by_axis[axis] = lr
    for k in range(2, MAX_PIGEONHOLE + 1):
        for axis in ("row", "col"):
            lr = lr_by_axis[axis]
            for combo in combinations(list(lr.keys()), k):
                regions = set()
                for idx in combo:
                    regions |= lr[idx]
                if len(regions) != k:
                    continue
                combo_lines = set(combo)
                marks = []
                seen = set()
                for rid in regions:
                    for (r, c) in state.unknowns(state.cells_of_region(rid)):
                        on_line = (r if axis == "row" else c) in combo_lines
                        if not on_line and (r, c) not in seen:
                            seen.add((r, c)); marks.append((r, c, ELIMINATED))
                if marks:
                    return Deduction("overcounting", 9, marks,
                                     "k 条线候选落在 k 个区域内，锁定这些区域的星于这些线",
                                     rule_id="overcounting", meta={"axis": axis, "k": k})
    return None


# .tier = 引擎选用顺序
undercounting.tier = 8
overcounting.tier = 9
