"""唯一解校验：封装现有 Z3 求解器。

复用 MiscTools/Z3Solver.py 的 Z3StarBattleSolver.solve()，它最多返回 2 个解：
  len == 0 -> 无解；len == 1 -> 唯一解；len == 2 -> 多解。
本模块只暴露一个布尔判定，并抑制求解器内部的 print 噪声（批量场景）。
"""

import os
import sys
import contextlib

from MiscTools.Z3Solver import Z3StarBattleSolver


@contextlib.contextmanager
def _silenced():
    """临时把 stdout 重定向到 /dev/null，屏蔽 Z3Solver 的计时打印。"""
    with open(os.devnull, 'w') as devnull:
        old = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old


def is_unique(region_grid, stars):
    """region_grid + 每区星数 是否恰好有唯一解。"""
    with _silenced():
        solutions, _ = Z3StarBattleSolver(region_grid, stars).solve()
    return len(solutions) == 1
