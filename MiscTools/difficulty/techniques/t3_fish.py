"""规则 13：鱼（Fish）。限 stars == 1。

纯行↔列计数（不涉及区域）：若 n 个列的星都只可能落在同样的 n 个行里（或行列对调），
则这 n 行的星被这 n 列包圆 → 这 n 行里不属于这 n 列的格打叉。
n=2 即 X-Wing，n=3 Swordfish……n 越大越难。

每次只返回最小 n、按 列→行 方向找到的第一个能产出标记的实例，meta={axis,n}。
"""

from itertools import combinations

from candidate_state import STAR, ELIMINATED
from deduction import Deduction

MAX_FISH = 7


def _other(axis):
    return "row" if axis == "col" else "col"


def _fish_dir(state, set_axis, n):
    """set_axis 的线作为"集合"（其星被困于另一轴的若干线）。"""
    cand = {}  # 集合线号 -> 其候选"约束坐标"集合
    for i in range(state.dim):
        cells = state.cells_of_line(set_axis, i)
        if state.count_state(cells, STAR) >= state.stars:
            continue
        unk = state.unknowns(cells)
        if not unk:
            continue
        # set_axis=col -> 候选行；set_axis=row -> 候选列
        cand[i] = {(r if set_axis == "col" else c) for (r, c) in unk}

    other = _other(set_axis)
    for combo in combinations(cand.keys(), n):
        confine = set()
        for i in combo:
            confine |= cand[i]
        if len(confine) != n:
            continue
        combo_set = set(combo)
        marks = []
        seen = set()
        for j in confine:  # j：被约束的另一轴的线号
            for (r, c) in state.unknowns(state.cells_of_line(other, j)):
                set_index = c if set_axis == "col" else r
                if set_index not in combo_set and (r, c) not in seen:
                    seen.add((r, c)); marks.append((r, c, ELIMINATED))
        if marks:
            return Deduction(
                "fish", 13, marks,
                "n 个{}的星被锁定在 n 个{}内，交叉外打叉".format(
                    "列" if set_axis == "col" else "行",
                    "行" if set_axis == "col" else "列"),
                rule_id="fish", meta={"axis": set_axis, "n": n})
    return None


def fish(state):
    if state.stars != 1:
        return None
    for n in range(2, MAX_FISH + 1):
        for set_axis in ("col", "row"):
            d = _fish_dir(state, set_axis, n)
            if d is not None:
                return d
    return None


fish.tier = 13
