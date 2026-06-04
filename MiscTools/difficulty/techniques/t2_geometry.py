"""T2 几何/计数技巧（tier 2）。均限 stars == 1。"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction

TIER = 2


def _regions_needing_star(state):
    """返回 {region_id: [候选 UNKNOWN 格...]}，仅含仍需放星的区域。"""
    out = {}
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) < state.stars:
            unk = state.unknowns(cells)
            if unk:
                out[rid] = unk
    return out


def region_confined_to_line(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    for rid, unk in _regions_needing_star(state).items():
        rows = {r for (r, c) in unk}
        cols = {c for (r, c) in unk}
        if len(rows) == 1:
            row = next(iter(rows))
            for (r, c) in state.unknowns(state.cells_of_row(row)):
                if state.region_grid[r][c] != rid and (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, ELIMINATED))
        if len(cols) == 1:
            col = next(iter(cols))
            for (r, c) in state.unknowns(state.cells_of_col(col)):
                if state.region_grid[r][c] != rid and (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("region_confined_to_line", 6, marks,
                     "区域候选全在单行/列，锁定该行/列的星于此区域",
                     rule_id="region_confined")


def exclusion(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    for rid, unk in _regions_needing_star(state).items():
        candidate_set = set(unk)
        common = None
        for (r, c) in unk:
            nbrs = set(state.neighbors(r, c))
            common = nbrs if common is None else (common & nbrs)
        if not common:
            continue
        for (r, c) in common:
            if (r, c) in candidate_set:
                continue
            if state.grid[r][c] == UNKNOWN and (r, c) not in seen:
                seen.add((r, c))
                marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("exclusion", 7, marks,
                     "该格是某待放星区域全部候选的公共邻格，放星会害死该区域",
                     rule_id="exclusion")


# .tier = 引擎选用顺序
region_confined_to_line.tier = 6
exclusion.tier = 7
