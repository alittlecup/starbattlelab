"""T2 鸽笼计数技巧（tier 2）：undercounting / overcounting。限 stars == 1。"""

from itertools import combinations

from candidate_state import STAR, ELIMINATED
from deduction import Deduction

TIER = 2
MAX_PIGEONHOLE = 3


def _lines_of(unk, axis):
    return {(r if axis == "row" else c) for (r, c) in unk}


def undercounting(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    regions = {}
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) < state.stars:
            unk = state.unknowns(cells)
            if unk:
                regions[rid] = unk
    rids = list(regions.keys())
    for axis in ("row", "col"):
        for k in range(2, MAX_PIGEONHOLE + 1):
            for combo in combinations(rids, k):
                lines = set()
                for rid in combo:
                    lines |= _lines_of(regions[rid], axis)
                if len(lines) == k:
                    combo_set = set(combo)
                    for line in lines:
                        cells = state.cells_of_line(axis, line)
                        for (r, c) in state.unknowns(cells):
                            if state.region_grid[r][c] not in combo_set and (r, c) not in seen:
                                seen.add((r, c)); marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("undercounting", TIER, marks,
                     "k 个区域候选落在 k 条线内，锁定这些线的星于这些区域")


def overcounting(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    for axis in ("row", "col"):
        line_count = state.dim
        line_regions = {}
        for idx in range(line_count):
            cells = state.unknowns(state.cells_of_line(axis, idx))
            if cells:
                line_regions[idx] = ({state.region_grid[r][c] for (r, c) in cells}, cells)
        line_ids = list(line_regions.keys())
        for k in range(2, MAX_PIGEONHOLE + 1):
            for combo in combinations(line_ids, k):
                regions = set()
                for idx in combo:
                    regions |= line_regions[idx][0]
                if len(regions) == k:
                    combo_lines = set(combo)
                    for rid in regions:
                        for (r, c) in state.unknowns(state.cells_of_region(rid)):
                            on_line = (r if axis == "row" else c) in combo_lines
                            if not on_line and (r, c) not in seen:
                                seen.add((r, c)); marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("overcounting", TIER, marks,
                     "k 条线候选落在 k 个区域内，锁定这些区域的星于这些线")


# 单一来源：技巧 tier 由本模块 TIER 决定。
undercounting.tier = TIER
overcounting.tier = TIER
