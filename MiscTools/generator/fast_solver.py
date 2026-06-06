"""Star Battle 专用快速解计数器（仅 k=1），用于生成时快速筛唯一解。

k=1 时一个解 = 每行选一列放星，满足：列互不相同、每区域恰好一颗、
相邻行的列号差 ≥2（即不相邻，含对角）。按行 DFS + 位掩码剪枝，
数到 limit 个解即停 —— 比通用 Z3 求解快 1~2 个数量级。

仅处理 k=1；其它星数请用 Z3（见 uniqueness.py 的路由）。
"""


def count_solutions(region_grid, limit=2):
    """统计 k=1 解的数量，最多数到 limit 个即停。"""
    n = len(region_grid)
    # 区域 id -> 0..m-1 位索引
    ids = {}
    reg = [[0] * n for _ in range(n)]
    for r in range(n):
        row = region_grid[r]
        rr = reg[r]
        for c in range(n):
            rid = row[c]
            idx = ids.get(rid)
            if idx is None:
                idx = len(ids)
                ids[rid] = idx
            rr[c] = idx
    if len(ids) != n:
        return 0  # 区域数 != n，k=1 不可能每行/列/区域各一星

    # 预存每行每列的区域位
    regbit = [[1 << reg[r][c] for c in range(n)] for r in range(n)]
    count = 0

    def dfs(r, used_cols, used_regs, prev_c):
        nonlocal count
        if r == n:
            count += 1
            return
        rb = regbit[r]
        for c in range(n):
            bit = 1 << c
            if used_cols & bit:
                continue
            if r > 0 and -2 < c - prev_c < 2:   # 与上一行相邻（含对角/同列）
                continue
            rbit = rb[c]
            if used_regs & rbit:
                continue
            dfs(r + 1, used_cols | bit, used_regs | rbit, c)
            if count >= limit:
                return

    dfs(0, 0, 0, -99)
    return count


def is_unique_fast(region_grid):
    """k=1 是否恰好唯一解。"""
    return count_solutions(region_grid, 2) == 1


def find_solutions(region_grid, limit=2):
    """返回至多 limit 个解，每个解是「各行星所在列」的元组。供精修取反例用。"""
    n = len(region_grid)
    ids = {}
    reg = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            rid = region_grid[r][c]
            idx = ids.get(rid)
            if idx is None:
                idx = len(ids)
                ids[rid] = idx
            reg[r][c] = idx
    if len(ids) != n:
        return []
    regbit = [[1 << reg[r][c] for c in range(n)] for r in range(n)]
    sols = []
    cur = [0] * n

    def dfs(r, used_cols, used_regs, prev_c):
        if r == n:
            sols.append(tuple(cur))
            return
        rb = regbit[r]
        for c in range(n):
            bit = 1 << c
            if used_cols & bit:
                continue
            if r > 0 and -2 < c - prev_c < 2:
                continue
            rbit = rb[c]
            if used_regs & rbit:
                continue
            cur[r] = c
            dfs(r + 1, used_cols | bit, used_regs | rbit, c)
            if len(sols) >= limit:
                return

    dfs(0, 0, 0, -99)
    return sols
