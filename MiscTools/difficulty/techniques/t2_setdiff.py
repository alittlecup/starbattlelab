"""规则 12：集合差分（Set Differentials）。限 stars == 1。

实现"单区域 vs 若干同向线"的星数差强制（带鳍计数抓不到的形状）：

设区域 R（1 星）与 m 条同向线 L（共 m 星）。把相关格分三类：
  I = R ∩ L，O = R 在 L 之外的格，X = L 中不属于 R 的格。
由 star(R)=1、star(L)=m 相减得：**star(X) − star(O) = m − 1**。
其中 star(·) = 已放星数 + 未定格中将放的星数。令
  d = (m−1) − sX + sO        （sX/sO 为 X/O 中已放星数）
则 aX − aO = d（aX/aO 为 X/O 未定格中将放的星数，0 ≤ aX ≤ |uX|，0 ≤ aO ≤ |uO|）。
- 若 d == |uX|：aX 取满、aO=0 → uX 全为星、uO 全打叉；
- 若 d == −|uO|：aO 取满、aX=0 → uO 全为星、uX 全打叉。

枚举：每个区域 × 行/列 × （不丢线 / 丢掉它跨越的某一条线）。
"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction


def _coord(cell, axis):
    return cell[0] if axis == "row" else cell[1]


def set_differentials(state):
    if state.stars != 1:
        return None
    for rid, cells in state.region_cells.items():
        region_set = set(cells)
        for axis in ("row", "col"):
            touched = sorted({_coord(cell, axis) for cell in cells})
            if len(touched) < 2:
                continue
            for drop in [None] + touched:
                L_lines = [t for t in touched if t != drop]
                if not L_lines:
                    continue
                m = len(L_lines)
                L_set = set(L_lines)
                L_cells = set()
                for t in L_lines:
                    L_cells.update(state.cells_of_line(axis, t))

                cells_O = [c for c in cells if _coord(c, axis) not in L_set]
                cells_X = [c for c in L_cells if c not in region_set]
                sO = sum(1 for (r, c) in cells_O if state.grid[r][c] == STAR)
                sX = sum(1 for (r, c) in cells_X if state.grid[r][c] == STAR)
                uO = [(r, c) for (r, c) in cells_O if state.grid[r][c] == UNKNOWN]
                uX = [(r, c) for (r, c) in cells_X if state.grid[r][c] == UNKNOWN]

                d = (m - 1) - sX + sO
                marks = None
                if d == len(uX) and (uX or uO):
                    marks = ([(r, c, STAR) for (r, c) in uX] +
                             [(r, c, ELIMINATED) for (r, c) in uO])
                elif d == -len(uO) and (uX or uO):
                    marks = ([(r, c, STAR) for (r, c) in uO] +
                             [(r, c, ELIMINATED) for (r, c) in uX])
                if marks:
                    return Deduction("set_differentials", 12, marks,
                                     "集合差分：区域与若干行/列的星数差强制定星/打叉",
                                     rule_id="set_diff", meta={"axis": axis, "m": m})
    return None


set_differentials.tier = 12
