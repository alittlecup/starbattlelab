"""staircase 策略：楼梯/带状划分。

把网格按「蛇形」顺序串成一条 4-邻接的哈密顿路径，再切成 N 段连续区块。
等分会得到笔直的横/竖带（左右对称，唯一解难）；因此对每段大小做随机抖动，
让区块边界变成台阶状、并打破严格对称 → 既有规律又能产唯一解。
"""

from .base import GenerationStrategy


class StaircaseStrategy(GenerationStrategy):
    name = "staircase"

    def generate(self, size, stars, rng):
        path = self._snake_path(size, rng)
        sizes = self._jittered_sizes(size, rng)

        grid = [[0] * size for _ in range(size)]
        i = 0
        for rid, seg in enumerate(sizes, start=1):
            for _ in range(seg):
                r, c = path[i]
                grid[r][c] = rid
                i += 1
        return grid

    @staticmethod
    def _snake_path(size, rng):
        """蛇形哈密顿路径：相邻元素 4-邻接。随机选行蛇形或列蛇形。"""
        by_column = rng.random() < 0.5
        path = []
        for a in range(size):
            line = range(size) if a % 2 == 0 else range(size - 1, -1, -1)
            for b in line:
                path.append((b, a) if by_column else (a, b))
        return path

    @staticmethod
    def _jittered_sizes(size, rng):
        """N 段、和为 N²、各 ≥1 的抖动大小，制造台阶边界。"""
        sizes = [size] * size
        for _ in range(size * 2):
            i = rng.randrange(size)
            j = i + rng.choice((-1, 1))
            if 0 <= j < size and sizes[i] > 1:
                sizes[i] -= 1
                sizes[j] += 1
        return sizes
