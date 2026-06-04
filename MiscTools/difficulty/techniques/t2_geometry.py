"""T2 几何技巧：region_confined_to_line / exclusion。限 stars == 1。

每次只返回**当前最容易的单个实例**（按区间内复杂度），并把结构因子记入 meta，
以便计分器按因子定位区间内的具体难度值。
"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction
from factors import complexity


def _confinement_instances(state):
    """枚举每个'区域候选全在单行/列'的实例（仅保留能产出标记的）。"""
    out = []
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) >= state.stars:
            continue
        unk = state.unknowns(cells)
        if not unk:
            continue
        rows = {r for (r, c) in unk}
        cols = {c for (r, c) in unk}
        for axis, lineset in (("row", rows), ("col", cols)):
            if len(lineset) != 1:
                continue
            line = next(iter(lineset))
            marks = []
            for (r, c) in state.unknowns(state.cells_of_line(axis, line)):
                if state.region_grid[r][c] != rid:
                    marks.append((r, c, ELIMINATED))
            if not marks:
                continue
            coords = sorted((c if axis == "row" else r) for (r, c) in unk)
            contiguous = (coords[-1] - coords[0] + 1 == len(coords))
            out.append({"axis": axis, "count": len(unk),
                        "contiguous": contiguous, "marks": marks})
    return out


def region_confined_to_line(state):
    if state.stars != 1:
        return None
    insts = _confinement_instances(state)
    if not insts:
        return None
    best = min(insts, key=lambda i: complexity(
        "region_confined", {"contiguous": i["contiguous"], "count": i["count"]}))
    return Deduction("region_confined_to_line", 6, best["marks"],
                     "区域候选全在单行/列，锁定该行/列的星于此区域",
                     rule_id="region_confined",
                     meta={"axis": best["axis"], "contiguous": best["contiguous"],
                           "count": best["count"]})


def exclusion(state):
    if state.stars != 1:
        return None
    insts = []
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) >= state.stars:
            continue
        unk = state.unknowns(cells)
        if not unk:
            continue
        candidate_set = set(unk)
        common = None
        for (r, c) in unk:
            nbrs = set(state.neighbors(r, c))
            common = nbrs if common is None else (common & nbrs)
        if not common:
            continue
        marks = []
        for (r, c) in common:
            if (r, c) not in candidate_set and state.grid[r][c] == UNKNOWN:
                marks.append((r, c, ELIMINATED))
        if marks:
            insts.append({"candidate_count": len(unk), "marks": marks})
    if not insts:
        return None
    best = min(insts, key=lambda i: complexity(
        "exclusion", {"candidate_count": i["candidate_count"]}))
    return Deduction("exclusion", 7, best["marks"],
                     "该格是某待放星区域全部候选的公共邻格，放星会害死该区域",
                     rule_id="exclusion",
                     meta={"candidate_count": best["candidate_count"]})


# .tier = 引擎选用顺序
region_confined_to_line.tier = 6
exclusion.tier = 7
