"""规则 11：带鳍计数（Finned Counts）。限 stars == 1。

当前实现**带鳍欠计数（单鳍线）**：
k 个区域的候选几乎落在 k 条线内，只多出一条"鳍线"f。分两种情况——
- 鳍线上无星 → 退化为干净欠计数，其消除（base k 线里其它区域的格）成立；
- 鳍线上某格为星 → 该鳍格的邻格被消除。
两种情况都被消除的 = （干净欠计数消除集）∩（所有鳍格的公共邻格），安全打叉。

对偶的"带鳍过计数"逻辑更复杂，暂未实现。
"""

from itertools import combinations

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction

MAX_K = 7


def _line_of(cell, axis):
    return cell[0] if axis == "row" else cell[1]


def _finned_under(state, regions, rids, k, axis):
    for combo in combinations(rids, k):
        lines = {}
        for rid in combo:
            for cell in regions[rid]:
                lines.setdefault(_line_of(cell, axis), []).append((rid, cell))
        if len(lines) != k + 1:        # 只处理"恰好多出一条鳍线"的情形
            continue
        combo_set = set(combo)
        for f in list(lines.keys()):
            base = [L for L in lines if L != f]
            fin_cells = [cell for (_rid, cell) in lines[f]]
            covered = set()
            for L in base:
                for (rid, _cell) in lines[L]:
                    covered.add(rid)
            if len(covered) != k:       # 某区域只在鳍线上有候选 → base 不成立
                continue
            clean = set()               # 干净欠计数会消除的格：base k 线里、combo 外区域的 UNKNOWN
            for L in base:
                for (r, c) in state.unknowns(state.cells_of_line(axis, L)):
                    if state.region_grid[r][c] not in combo_set:
                        clean.add((r, c))
            if not clean:
                continue
            common_nb = None            # 所有鳍格的公共邻格
            for (fr, fc) in fin_cells:
                nb = set(state.neighbors(fr, fc))
                common_nb = nb if common_nb is None else (common_nb & nb)
            if not common_nb:
                continue
            marks = [(r, c, ELIMINATED) for (r, c) in (clean & common_nb)
                     if state.grid[r][c] == UNKNOWN]
            if marks:
                return Deduction("finned_counts", 11, marks,
                                 "带鳍欠计数：干净欠计数消除集 ∩ 鳍邻格",
                                 rule_id="finned_counts",
                                 meta={"axis": axis, "k": k, "fin": len(fin_cells)})
    return None


def finned_counts(state):
    if state.stars != 1:
        return None
    regions = {}
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) < state.stars:
            unk = state.unknowns(cells)
            if unk:
                regions[rid] = unk
    rids = list(regions.keys())
    for k in range(2, MAX_K + 1):
        for axis in ("row", "col"):
            d = _finned_under(state, regions, rids, k, axis)
            if d is not None:
                return d
    return None


finned_counts.tier = 11
