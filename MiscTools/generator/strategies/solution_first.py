"""solution 策略（思路 B：解先行）。

先随机生成一组合法星阵（每行/列 1 星、互不相邻含对角），作为预定答案；
再用这些星作为种子多源生长出 N 个连通区域，每区恰好含 1 颗星
→ 该星阵天生是一个合法解，候选必有解，唯一解命中率比随机划分高几个数量级。
（仅 k=1。）唯一性仍交给 pipeline 过滤。
"""
from .base import GenerationStrategy


def _random_star_solution(n, rng, tries=200):
    """随机合法星阵（k=1）：每行 1 星的列排列，相邻行列号差 ≥2（即不相邻含对角）。

    回溯 + 随机化列顺序；失败重试。返回每行的列号列表，或 None。
    """
    for _ in range(tries):
        cols = [-1] * n
        used = [False] * n
        ok = True
        for r in range(n):
            cands = [c for c in range(n)
                     if not used[c] and (r == 0 or abs(c - cols[r - 1]) >= 2)]
            if not cands:
                ok = False
                break
            c = cands[rng.randrange(len(cands))]
            cols[r] = c
            used[c] = True
        if ok:
            return cols
    return None


class SolutionFirstStrategy(GenerationStrategy):
    name = "solution"

    def generate(self, size, stars, rng):
        if stars != 1:
            return None  # 当前仅支持 k=1
        cols = _random_star_solution(size, rng)
        if cols is None:
            return None
        seeds = [(r, cols[r]) for r in range(size)]  # 每个区域一颗星做种子

        grid = [[0] * size for _ in range(size)]
        frontier = []
        for rid, (r, c) in enumerate(seeds, start=1):
            grid[r][c] = rid
            self._push(grid, frontier, r, c, rid, size)

        filled = size
        total = size * size
        while filled < total and frontier:
            idx = rng.randrange(len(frontier))
            frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
            r, c, rid = frontier.pop()
            if grid[r][c] != 0:
                continue
            grid[r][c] = rid
            filled += 1
            self._push(grid, frontier, r, c, rid, size)

        if filled != total:
            return None
        return grid  # 每区恰好含其种子那一颗星 -> cols 是一个合法解

    @staticmethod
    def _push(grid, frontier, r, c, rid, size):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == 0:
                frontier.append((nr, nc, rid))
