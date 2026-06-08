"""Star Battle 专用快速解计数器（仅 k=1），用于生成时快速筛唯一解。

按「区域、最小区域优先(MRV)」DFS：每个区域恰好放一颗星，
小区域候选少 → 分支因子低、剪枝层层级联，证明唯一性极快。
约束：每行/列至多一颗星，星之间 8 邻接不相邻。
数到 limit 个解即停。仅 k=1；其它星数用 Z3（见 uniqueness.py）。
"""


def _regions_by_size(region_grid):
    """返回 (n, 按格子数升序排列的区域格子列表)；区域数 != n 时返回 None。"""
    n = len(region_grid)
    regions = {}
    for r in range(n):
        row = region_grid[r]
        for c in range(n):
            regions.setdefault(row[c], []).append((r, c))
    if len(regions) != n:
        return None
    return n, sorted(regions.values(), key=len)


def count_solutions(region_grid, limit=2):
    """统计 k=1 解的数量，最多数到 limit 个即停。"""
    prep = _regions_by_size(region_grid)
    if prep is None:
        return 0
    n, order = prep
    occ = [[False] * n for _ in range(n)]   # 星占用网格，用于 O(1) 邻接检查
    count = 0

    def adj(r, c):
        for dr in (-1, 0, 1):
            rr = r + dr
            if 0 <= rr < n:
                orow = occ[rr]
                for dc in (-1, 0, 1):
                    cc = c + dc
                    if 0 <= cc < n and orow[cc]:
                        return True
        return False

    def dfs(i, used_row, used_col):
        nonlocal count
        if i == n:
            count += 1
            return
        for (r, c) in order[i]:
            rb = 1 << r
            if used_row & rb:
                continue
            cb = 1 << c
            if used_col & cb:
                continue
            if adj(r, c):
                continue
            occ[r][c] = True
            dfs(i + 1, used_row | rb, used_col | cb)
            occ[r][c] = False
            if count >= limit:
                return

    dfs(0, 0, 0)
    return count


def is_unique_fast(region_grid):
    """k=1 是否恰好唯一解。"""
    return count_solutions(region_grid, 2) == 1


def find_solutions(region_grid, limit=2):
    """返回至多 limit 个解，每个解是「各行星所在列」的元组。供精修取反例用。"""
    prep = _regions_by_size(region_grid)
    if prep is None:
        return []
    n, order = prep
    occ = [[False] * n for _ in range(n)]
    cols = [0] * n          # cols[r] = 该行星所在列
    sols = []

    def adj(r, c):
        for dr in (-1, 0, 1):
            rr = r + dr
            if 0 <= rr < n:
                orow = occ[rr]
                for dc in (-1, 0, 1):
                    cc = c + dc
                    if 0 <= cc < n and orow[cc]:
                        return True
        return False

    def dfs(i, used_row, used_col):
        if i == n:
            sols.append(tuple(cols))
            return
        for (r, c) in order[i]:
            rb = 1 << r
            if used_row & rb:
                continue
            cb = 1 << c
            if used_col & cb:
                continue
            if adj(r, c):
                continue
            occ[r][c] = True
            cols[r] = c
            dfs(i + 1, used_row | rb, used_col | cb)
            occ[r][c] = False
            if len(sols) >= limit:
                return

    dfs(0, 0, 0)
    return sols
