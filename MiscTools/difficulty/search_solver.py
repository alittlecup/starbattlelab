"""搜索兜底（方案 C）：逻辑传播 + 回溯猜测的完整求解器。

对命名技巧引擎解不动的题：先用逻辑引擎传播到不动点，卡住就按 MRV 选格猜测、递归，
矛盾则回退。保证能解任何唯一解谜题，并统计搜索代价：
- guesses：分支（猜测）节点数 —— 越多越依赖试错；
- depth：最大嵌套猜测深度。
最多找 2 个解即停（用于判唯一性）。
"""

from candidate_state import STAR
from engine import solve
from techniques import ALL_TECHNIQUES

MAX_NODES = 200000   # 安全上限，防止极端情形爆炸


def _pick_cell(state):
    """MRV：选"仍需放星且候选最少"的单元，返回其一个 UNKNOWN 格（确定性）。"""
    best = None
    best_count = None
    for (_kind, _key, cells) in state.all_units():
        if state.count_state(cells, STAR) >= state.stars:
            continue
        unk = state.unknowns(cells)
        if not unk:
            continue
        if best_count is None or len(unk) < best_count:
            best_count = len(unk)
            best = unk[0]
    return best


def _solution_key(state):
    return frozenset((r, c) for r in range(state.dim) for c in range(state.dim)
                     if state.grid[r][c] == STAR)


def _search(state, stats, solutions, max_solutions, depth):
    if len(solutions) >= max_solutions or stats["nodes"] >= MAX_NODES:
        return
    stats["nodes"] += 1
    solve(state, list(ALL_TECHNIQUES))           # 逻辑传播（就地）
    if state.invalid:
        return
    if state.is_solved():
        key = _solution_key(state)
        if key not in solutions:
            solutions.append(key)
        return
    cell = _pick_cell(state)
    if cell is None:
        return                                    # 无候选却未解出 → 此分支死
    stats["guesses"] += 1
    if depth + 1 > stats["depth"]:
        stats["depth"] = depth + 1
    r, c = cell
    from candidate_state import STAR as _STAR, ELIMINATED as _ELIM
    for val in (_STAR, _ELIM):
        child = state.copy()
        child.set_cell(r, c, val)
        _search(child, stats, solutions, max_solutions, depth + 1)
        if len(solutions) >= max_solutions:
            return


def solve_complete(state, max_solutions=2):
    """返回 {solutions: [frozenset...], guesses, depth, nodes}。"""
    stats = {"guesses": 0, "depth": 0, "nodes": 0}
    solutions = []
    _search(state, stats, solutions, max_solutions, 0)
    return {"solutions": solutions, "guesses": stats["guesses"],
            "depth": stats["depth"], "nodes": stats["nodes"]}
