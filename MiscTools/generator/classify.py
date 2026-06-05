"""区域划分分类器：识别对称性与区域大小分布，归出主类目。

纯几何判断，与生成策略无关。batch 用它把结构化布局（尤其碰巧出现的
对称布局）识别出来并分目录归档。
"""

from collections import Counter

from .canonical import relabel


def _named_transforms(grid):
    """返回 {对称名: 变换后的 grid}，不含 identity。"""
    n = len(grid)
    return {
        'rot90':    [[grid[n - 1 - c][r] for c in range(n)] for r in range(n)],
        'rot180':   [[grid[n - 1 - r][n - 1 - c] for c in range(n)] for r in range(n)],
        'rot270':   [[grid[c][n - 1 - r] for c in range(n)] for r in range(n)],
        'flipH':    [[grid[r][n - 1 - c] for c in range(n)] for r in range(n)],
        'flipV':    [[grid[n - 1 - r][c] for c in range(n)] for r in range(n)],
        'transpose':     [[grid[c][r] for c in range(n)] for r in range(n)],
        'antitranspose': [[grid[n - 1 - c][n - 1 - r] for c in range(n)] for r in range(n)],
    }


def detect_symmetry(grid):
    """返回该划分（作为分区，忽略区域编号）保持不变的对称名列表。"""
    base = relabel(grid)
    return [name for name, t in _named_transforms(grid).items() if relabel(t) == base]


def size_profile(grid):
    """区域大小分布：返回 (排序后的大小列表, 标签)。

    标签：uniform(全等) / progressive(各不相同且等差) / distinct(各不相同非等差) / mixed。
    """
    sizes = sorted(Counter(x for row in grid for x in row).values())
    if len(set(sizes)) == 1:
        return sizes, 'uniform'
    if len(set(sizes)) == len(sizes):  # 全不相同
        diffs = {sizes[i + 1] - sizes[i] for i in range(len(sizes) - 1)}
        if len(diffs) == 1:            # 等差（含连续）
            return sizes, 'progressive'
        return sizes, 'distinct'
    return sizes, 'mixed'


def category(grid):
    """几何主类目（用于归档）：symmetric-* 优先，其次大小分布，否则 plain。"""
    syms = detect_symmetry(grid)
    if 'rot90' in syms:
        return 'symmetric-rot90'      # 四重旋转对称，最强
    if 'rot180' in syms:
        return 'symmetric-rot180'
    if syms:                          # 仅镜像/对角对称
        return 'symmetric-mirror'
    label = size_profile(grid)[1]
    if label in ('progressive', 'uniform'):
        return label
    return 'plain'
