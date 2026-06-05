"""progressive 策略：区域大小互不相同（多为等差/递进）的划分。

做法：给各区域分配互不相同的目标大小（和为 N²），用「赤字驱动」的多源
生长——每步优先扩张当前离目标最远的区域。这样既保证铺满全格（不会孤立），
又把各区域大小逼近互不相同的目标。整体不对称 → 唯一解命中率正常。
"""

from .base import GenerationStrategy


def distinct_sizes(n):
    """n 个互不相同的正整数，和恰为 n²（基底 1..n，余量均摊到较大端）。"""
    base = list(range(1, n + 1))
    remainder = n * n - sum(base)
    q, r = divmod(remainder, n)
    sizes = [base[i] + q for i in range(n)]
    for i in range(n - r, n):
        sizes[i] += 1
    return sizes


class ProgressiveStrategy(GenerationStrategy):
    name = "progressive"

    def generate(self, size, stars, rng):
        for _ in range(20):                       # 内部重试，直到大小互不相同
            grid = self._carve(size, rng)
            sizes = [0] * (size + 1)
            for row in grid:
                for x in row:
                    sizes[x] += 1
            region_sizes = sizes[1:]
            if len(set(region_sizes)) == size:    # 全不相同 -> 接受
                return grid
        return None

    def _carve(self, size, rng):
        targets = distinct_sizes(size)
        rng.shuffle(targets)
        cells = [(r, c) for r in range(size) for c in range(size)]
        seeds = rng.sample(cells, size)

        grid = [[0] * size for _ in range(size)]
        cur = [0] * (size + 1)
        tgt = [0] * (size + 1)
        frontiers = {i: [] for i in range(1, size + 1)}
        for rid, (r, c) in enumerate(seeds, start=1):
            grid[r][c] = rid
            cur[rid] = 1
            tgt[rid] = targets[rid - 1]
            self._push(grid, frontiers[rid], r, c, size)

        filled = size
        total = size * size
        while filled < total:
            # 选「赤字最大」且仍有可扩张边界的区域（并列随机）
            best, best_def = None, None
            order = list(range(1, size + 1))
            rng.shuffle(order)
            for rid in order:
                if not frontiers[rid]:
                    continue
                deficit = tgt[rid] - cur[rid]
                if best_def is None or deficit > best_def:
                    best, best_def = rid, deficit
            if best is None:
                break                             # 不应发生（连通图必能铺满）
            fr = frontiers[best]
            r = c = None
            while fr:
                i = rng.randrange(len(fr))
                fr[i], fr[-1] = fr[-1], fr[i]
                cell = fr.pop()
                if grid[cell[0]][cell[1]] == 0:
                    r, c = cell
                    break
            if r is None:
                continue
            grid[r][c] = best
            cur[best] += 1
            filled += 1
            self._push(grid, frontiers[best], r, c, size)
        return grid

    @staticmethod
    def _push(grid, frontier, r, c, size):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == 0:
                frontier.append((nr, nc))
