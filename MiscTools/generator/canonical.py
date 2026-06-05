"""区域划分的规范形（canonical form）—— 用于「真正不同形状」的去重。

两个划分若互为旋转/镜像（8 种二面体对称之一），或只是区域编号不同，
视为「同一形状」。canonical_key 给出在这些变换下都不变的指纹，
所以按它去重 = 每个保留下来的谜题都是几何上独一无二的形状。

这些原语也被 classify.py 复用（检测对称性）。
"""


def _transforms(grid):
    """返回 grid 在 8 种二面体对称下的全部变体（含自身）。"""
    n = len(grid)

    def rot90(g):  # 顺时针 90°
        return [[g[n - 1 - c][r] for c in range(n)] for r in range(n)]

    def flipH(g):  # 左右翻转
        return [row[::-1] for row in g]

    outs = []
    g = grid
    for _ in range(4):
        outs.append(g)
        outs.append(flipH(g))
        g = rot90(g)
    return outs


def relabel(grid):
    """按行优先扫描顺序把区域 id 重新编号为 1,2,3...，返回扁平 tuple。

    消除「同一分区、不同编号」的差异，便于比较/序列化。
    """
    n = len(grid)
    mapping = {}
    flat = []
    nxt = 1
    for r in range(n):
        for c in range(n):
            rid = grid[r][c]
            if rid not in mapping:
                mapping[rid] = nxt
                nxt += 1
            flat.append(mapping[rid])
    return tuple(flat)


def canonical_key(grid):
    """在「8 种对称 + 区域改号」下不变的指纹。

    对每种对称变体做规范化重编号，取字典序最小者。互为旋转/镜像的划分
    会得到相同 key。
    """
    return min(relabel(t) for t in _transforms(grid))
