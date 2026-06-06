"""refine 策略（思路 B：解先行 + 反例制导边界精修）。

1. 随机摆合法星阵 S，围着 S 切出每区恰一星的区域 → S 必是解。
2. 反复：求解；若多解，取第二个解 S2，把"在 S2 是星、在 S 不是星"的格子 x
   从其区域 A 划给相邻区域 B —— 可证 S2 当场失效而 S 不受影响。
3. 收敛到唯一解则返回；卡住或超迭代则换新 S 重启。

仅 k=1。大尺寸命中率远高于盲目随机。
"""
from collections import deque

from .base import GenerationStrategy
from .solution_first import _random_star_solution
from ..fast_solver import find_solutions

_NB = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _carve_seeded(size, seeds, rng):
    """以 seeds（每区一颗星）为种子多源随机生长，返回 region_grid 或 None。"""
    grid = [[0] * size for _ in range(size)]
    frontier = []

    def push(r, c, rid):
        for dr, dc in _NB:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == 0:
                frontier.append((nr, nc, rid))

    for rid, (r, c) in enumerate(seeds, start=1):
        grid[r][c] = rid
        push(r, c, rid)
    filled = size
    total = size * size
    while filled < total and frontier:
        i = rng.randrange(len(frontier))
        frontier[i], frontier[-1] = frontier[-1], frontier[i]
        r, c, rid = frontier.pop()
        if grid[r][c] != 0:
            continue
        grid[r][c] = rid
        filled += 1
        push(r, c, rid)
    return grid if filled == total else None


def _connected_without(grid, region_id, xr, xc, size):
    """移除 (xr,xc) 后，region_id 的其余格子是否仍连通。"""
    cells = [(r, c) for r in range(size) for c in range(size)
             if grid[r][c] == region_id and (r, c) != (xr, xc)]
    if not cells:
        return False
    seen = {cells[0]}
    q = deque([cells[0]])
    while q:
        r, c = q.popleft()
        for dr, dc in _NB:
            t = (r + dr, c + dc)
            if (0 <= t[0] < size and 0 <= t[1] < size and grid[t[0]][t[1]] == region_id
                    and t != (xr, xc) and t not in seen):
                seen.add(t)
                q.append(t)
    return len(seen) == len(cells)


class RefineStrategy(GenerationStrategy):
    name = "refine"

    def __init__(self, restarts=25, max_iter=None):
        self.restarts = restarts
        self.max_iter = max_iter

    def generate(self, size, stars, rng):
        if stars != 1:
            return None
        max_iter = self.max_iter or size * 6
        for _ in range(self.restarts):
            cols = _random_star_solution(size, rng)
            if cols is None:
                continue
            seeds = [(r, cols[r]) for r in range(size)]
            grid = _carve_seeded(size, seeds, rng)
            if grid is None:
                continue
            if self._refine(grid, cols, size, max_iter, rng):
                return grid
        return None

    @staticmethod
    def _refine(grid, cols, size, max_iter, rng):
        target = tuple(cols)
        for _ in range(max_iter):
            sols = find_solutions(grid, 2)
            if len(sols) == 1:
                return True                       # 唯一解
            if not sols:
                return False                      # 异常：S 丢了（不应发生）
            s2 = sols[0] if sols[0] != target else sols[1]
            moved = False
            rows = list(range(size))
            rng.shuffle(rows)
            for r in rows:
                if s2[r] == cols[r]:
                    continue                      # 该行 S2 与 S 同列，不是差异格
                xr, xc = r, s2[r]                 # x：S2 的星、S 非星
                A = grid[xr][xc]
                nbrs = list(_NB)
                rng.shuffle(nbrs)
                for dr, dc in nbrs:
                    nr, nc = xr + dr, xc + dc
                    if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] != A:
                        if _connected_without(grid, A, xr, xc, size):
                            grid[xr][xc] = grid[nr][nc]   # x 改划给相邻区域 B
                            moved = True
                            break
                if moved:
                    break
            if not moved:
                return False                      # 卡住 → 换新 S
        return False
