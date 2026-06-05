"""思路 A：多源随机 BFS 区域划分。

在网格上撒 size 个种子，随机蔓延吃相邻空格直到铺满。
天然保证：每个区域连通、恰好 size 个区域、覆盖全部格子。
不保证唯一解——唯一性交给 pipeline 校验。
"""

from .base import GenerationStrategy


class RandomCarveStrategy(GenerationStrategy):
    name = "random"

    def generate(self, size, stars, rng):
        grid = [[0] * size for _ in range(size)]  # 0 = 未分配
        all_cells = [(r, c) for r in range(size) for c in range(size)]
        seeds = rng.sample(all_cells, size)

        # frontier: 待分配的 (r, c, region_id) 候选，可能重复/失效，取用时再校验。
        frontier = []
        for region_id, (r, c) in enumerate(seeds, start=1):
            grid[r][c] = region_id
            self._push_neighbors(grid, frontier, r, c, region_id, size)

        filled = size  # 已分配格子数（种子）
        target = size * size
        while filled < target and frontier:
            idx = rng.randrange(len(frontier))
            # swap-pop：O(1) 随机取出
            frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
            r, c, region_id = frontier.pop()
            if grid[r][c] != 0:
                continue  # 已被别的区域吃掉
            grid[r][c] = region_id
            filled += 1
            self._push_neighbors(grid, frontier, r, c, region_id, size)

        if filled != target:
            return None  # 极端情况下 frontier 提前耗尽（理论上不会发生）
        return grid

    @staticmethod
    def _push_neighbors(grid, frontier, r, c, region_id, size):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == 0:
                frontier.append((nr, nc, region_id))
