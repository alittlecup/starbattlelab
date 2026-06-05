"""shape 策略：把某个区域固定成可识别图案（十字/菱形/心形/L/T/回字框…），
其余格子再切成剩下的连通区域。唯一解由 pipeline 过滤。

每个图案是一个 mask(size) -> set[(r,c)]，作为「特征区域」。其余格子按连通分量
分配给剩下 N-1 个区域（分量数须 ≤ N-1）。图案不适配该尺寸时 generate 返回 None。
"""
from collections import deque

from .base import GenerationStrategy


# ---- 图案模板：mask(size) 返回特征区域的格子集合（不适配则返回 None）----
def _plus(n):
    m = n // 2
    return {(m, c) for c in range(n)} | {(r, m) for r in range(n)}

def _diamond(n):
    m = n // 2
    return {(r, c) for r in range(n) for c in range(n) if abs(r - m) + abs(c - m) <= m - 1}

def _frame(n):
    return {(r, c) for r in range(n) for c in range(n) if r in (0, n - 1) or c in (0, n - 1)}

def _Lshape(n):
    return {(r, 0) for r in range(n)} | {(n - 1, c) for c in range(n)}

def _Tshape(n):
    m = n // 2
    return {(0, c) for c in range(n)} | {(r, m) for r in range(n)}

def _grid_mask(patterns):
    """patterns: {n: [行字符串]}，按尺寸取对应手工图案；无该尺寸返回 None。"""
    def fn(n):
        rows = patterns.get(n)
        if rows is None:
            return None
        return {(r, c) for r in range(n) for c in range(n) if rows[r][c] == "1"}
    return fn

_heart = _grid_mask({
    5: ["00000", "01010", "11111", "01110", "00100"],
    6: ["000000", "010010", "111111", "011110", "001100", "000000"],
})
_corner = lambda n: {(r, c) for r in range(n // 2 + 1) for c in range(n // 2 + 1)}  # 角上方块
_zigzag = _grid_mask({
    5: ["11100", "00100", "00100", "00111", "00000"],
    6: ["111000", "001000", "001100", "000100", "000111", "000000"],
})


TEMPLATES = {
    "cross": _diamond,   # 5 格小十字（中心+4），实测可产唯一解
    "L": _Lshape,
    "T": _Tshape,
    "corner": _corner,
    "zigzag": _zigzag,
    "heart": _heart,
}


def _components(cells):
    """cells(set) 的 4-连通分量列表。"""
    cells = set(cells)
    comps = []
    while cells:
        start = next(iter(cells))
        comp = {start}
        q = deque([start])
        cells.discard(start)
        while q:
            r, c = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                t = (r + dr, c + dc)
                if t in cells:
                    cells.discard(t); comp.add(t); q.append(t)
        comps.append(comp)
    return comps


def _carve(cells, k, rng):
    """把一个连通格子集 cells 切成 k 个连通区域，返回 [set,...]。"""
    cells = set(cells)
    if k == 1:
        return [cells]
    seeds = rng.sample(sorted(cells), k)
    region = {s: i for i, s in enumerate(seeds)}
    frontier = []
    for s in seeds:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            t = (s[0] + dr, s[1] + dc)
            if t in cells and t not in region:
                frontier.append((t, region[s]))
    assigned = len(seeds)
    while assigned < len(cells) and frontier:
        idx = rng.randrange(len(frontier))
        frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
        cell, rid = frontier.pop()
        if cell in region:
            continue
        region[cell] = rid
        assigned += 1
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            t = (cell[0] + dr, cell[1] + dc)
            if t in cells and t not in region:
                frontier.append((t, rid))
    if assigned != len(cells):
        return None
    out = [set() for _ in range(k)]
    for cell, rid in region.items():
        out[rid].add(cell)
    return out


class ShapeStrategy(GenerationStrategy):
    def __init__(self, shape_name):
        self.shape_name = shape_name
        self.name = f"shape-{shape_name}"
        self._mask_fn = TEMPLATES[shape_name]

    def generate(self, size, stars, rng):
        mask = self._mask_fn(size)
        if not mask:
            return None
        if not (1 <= len(mask) <= size * size - (size - 1)):
            return None  # 给剩下 N-1 个区域至少各留 1 格
        rest = {(r, c) for r in range(size) for c in range(size)} - mask
        comps = _components(rest)
        need = size - 1
        if len(comps) > need:
            return None  # 余下分量太多，无法只用 N-1 个区域覆盖
        # 给每个分量分配区域数：每个至少 1，多出来的给最大的分量
        comps.sort(key=len, reverse=True)
        alloc = [1] * len(comps)
        extra = need - len(comps)
        for i in range(extra):
            if len(comps[i % len(comps)]) > alloc[i % len(comps)]:
                alloc[i % len(comps)] += 1
        if sum(alloc) != need:
            return None
        regions = [mask]  # 区域 1 = 图案
        for comp, k in zip(comps, alloc):
            parts = _carve(comp, k, rng)
            if parts is None:
                return None
            regions.extend(parts)
        if len(regions) != size:
            return None
        grid = [[0] * size for _ in range(size)]
        for rid, cells in enumerate(regions, start=1):
            for (r, c) in cells:
                grid[r][c] = rid
        if any(0 in row for row in grid):
            return None
        return grid
