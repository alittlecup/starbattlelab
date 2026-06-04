# Star Battle 难度计算指标 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个 Python 离线工具，对 1 星 Star Battle 谜题做"带技巧标注的逻辑解题"，产出逐步轨迹（Trace）并据此计算难度分。

**Architecture:** 解析 SBN → 候选态模型（每格三态）→ 解题引擎按"由易到难"的技巧库逐步推进、每步标注所用技巧 → 轨迹交给计分器算难度分，交给覆盖工具发现"技巧覆盖不到"的卡点。技巧库可独立增删，引擎与计分器无需改动。

**Tech Stack:** 纯 Python 3.11 标准库（`unittest`、`itertools`、`collections`、`argparse`），无第三方依赖。代码位于 `MiscTools/difficulty/`。

---

## 约定（所有任务通用）

- **测试框架**：标准库 `unittest`，每个测试文件可直接运行：`python3 <path/to/test_file.py> -v`。
- **包内导入**：`difficulty/` 不做成 Python 包（与 `MiscTools/` 现有脚本风格一致，无 `__init__.py`）。模块间用顶层名导入，如 `from candidate_state import CandidateState`。这依赖 `difficulty/` 在 `sys.path` 上：直接运行脚本时其所在目录自动入 `sys.path[0]`；测试文件用下方固定片段把 `difficulty/` 加入路径。
- **测试文件头部固定片段**（每个 `tests/test_*.py` 开头都放这段，使其独立于工作目录可运行）：

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- **单元类型常量**：`CandidateState` 暴露 `UNKNOWN = 0`、`STAR = 1`、`ELIMINATED = 2`。
- **代码风格**：跟随 `MiscTools/` 现有风格——标准库为主、`argparse`、不强制类型注解。

---

## Task 1: 项目骨架 + SBN 解析（sbn_codec）

**Files:**
- Create: `MiscTools/difficulty/sbn_codec.py`
- Create: `MiscTools/difficulty/tests/test_codec.py`

> 复用来源：`MiscTools/SBNBatchValidator.py:200-279` 的 `decode_sbn` / `reconstruct_grid_from_borders`。这里**复制**这两段已验证的纯函数（避免 import 触发该脚本的 multiprocessing/argparse 副作用），并新增一个返回二维 region_grid 的薄封装 `decode_to_grid`。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_codec.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sbn_codec import decode_to_grid


class TestSbnCodec(unittest.TestCase):
    def test_decode_5x5_one_star(self):
        result = decode_to_grid("551W9jo0cIn")
        self.assertIsNotNone(result)
        self.assertEqual(result["dim"], 5)
        self.assertEqual(result["stars"], 1)
        grid = result["region_grid"]
        # 5x5 二维网格
        self.assertEqual(len(grid), 5)
        self.assertTrue(all(len(row) == 5 for row in grid))
        # Star Battle 不变量：区域数 == 维度
        region_ids = {cell for row in grid for cell in row}
        self.assertEqual(len(region_ids), 5)

    def test_decode_8x8_one_star(self):
        result = decode_to_grid("881W8AKBNEeYHXnmB62j6O0")
        self.assertEqual(result["dim"], 8)
        self.assertEqual(result["stars"], 1)
        region_ids = {cell for row in result["region_grid"] for cell in row}
        self.assertEqual(len(region_ids), 8)

    def test_decode_invalid_returns_none(self):
        self.assertIsNone(decode_to_grid("not-a-real-sbn"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_codec.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sbn_codec'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/sbn_codec.py`:

```python
"""SBN (Star Battle Notation) 解码为二维 region_grid。

decode_sbn / reconstruct_grid_from_borders 复制自 MiscTools/SBNBatchValidator.py
(原始实现，已在生产中验证)，此处复制而非 import，以避免引入该脚本的副作用。
"""

import math
from collections import deque

SBN_B64_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
SBN_CHAR_TO_INT = {c: i for i, c in enumerate(SBN_B64_ALPHABET)}
SBN_CODE_TO_DIM_MAP = {
    '55': 5,  '66': 6,  '77': 7,  '88': 8,  '99': 9, 'AA': 10, 'BB': 11, 'CC': 12, 'DD': 13,
    'EE': 14, 'FF': 15, 'GG': 16, 'HH': 17, 'II': 18, 'JJ': 19, 'KK': 20, 'LL': 21, 'MM': 22,
    'NN': 23, 'OO': 24, 'PP': 25
}


def reconstruct_grid_from_borders(dim, vertical_bits, horizontal_bits):
    region_grid = [[0] * dim for _ in range(dim)]
    region_id = 1
    for r_start in range(dim):
        for c_start in range(dim):
            if region_grid[r_start][c_start] == 0:
                q = deque([(r_start, c_start)])
                region_grid[r_start][c_start] = region_id
                while q:
                    r, c = q.popleft()
                    if c < dim - 1 and region_grid[r][c+1] == 0 and vertical_bits[r*(dim-1) + c] == '0':
                        region_grid[r][c+1] = region_id; q.append((r, c+1))
                    if c > 0 and region_grid[r][c-1] == 0 and vertical_bits[r*(dim-1) + (c-1)] == '0':
                        region_grid[r][c-1] = region_id; q.append((r, c-1))
                    if r < dim - 1 and region_grid[r+1][c] == 0 and horizontal_bits[c*(dim-1) + r] == '0':
                        region_grid[r+1][c] = region_id; q.append((r+1, c))
                    if r > 0 and region_grid[r-1][c] == 0 and horizontal_bits[c*(dim-1) + (r-1)] == '0':
                        region_grid[r-1][c] = region_id; q.append((r-1, c))
                region_id += 1
    return region_grid


def decode_sbn(sbn_string):
    try:
        size_code = sbn_string[0:2]
        dim = SBN_CODE_TO_DIM_MAP.get(size_code)
        if not dim:
            return None
        stars = int(sbn_string[2])
        border_bits_needed = 2 * dim * (dim - 1)
        border_chars_needed = math.ceil(border_bits_needed / 6)
        region_data_str = sbn_string[4: 4 + border_chars_needed]
        full_bitfield = "".join(
            bin(SBN_CHAR_TO_INT.get(char, 0))[2:].zfill(6) for char in region_data_str
        )
        padding_bits = len(full_bitfield) - border_bits_needed
        border_data = full_bitfield[padding_bits:]
        num_single_direction_borders = dim * (dim - 1)
        vertical_bits = border_data[:num_single_direction_borders]
        horizontal_bits = border_data[num_single_direction_borders:]
        region_grid = reconstruct_grid_from_borders(dim, vertical_bits, horizontal_bits)
        return {'region_grid': region_grid, 'stars': stars, 'dim': dim}
    except (KeyError, IndexError, ValueError):
        return None


def decode_to_grid(sbn_string):
    """解码 SBN 字符串为 {region_grid, stars, dim}，失败返回 None。"""
    return decode_sbn(sbn_string)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_codec.py -v`
Expected: PASS（3 个用例全过）

- [ ] **Step 5: 提交**

```bash
git add MiscTools/difficulty/sbn_codec.py MiscTools/difficulty/tests/test_codec.py
git commit -m "feat(difficulty): add SBN decoder reused from SBNBatchValidator"
```

---

## Task 2: 候选态模型（CandidateState）

**Files:**
- Create: `MiscTools/difficulty/candidate_state.py`
- Create: `MiscTools/difficulty/tests/test_state.py`

> `CandidateState` 维护每格三态与各单元（行/列/区域）的查询能力。派生信息（星数、剩余 UNKNOWN）按需扫描计算，不做缓存，避免失效 bug；小棋盘性能足够。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_state.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED, is_complete_valid


def make_3x3_rows():
    # region id == 行号+1（3 个水平区域），用于构造小测试
    return [[1, 1, 1], [2, 2, 2], [3, 3, 3]]


class TestCandidateState(unittest.TestCase):
    def test_init_all_unknown(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        self.assertEqual(st.dim, 3)
        self.assertEqual(st.stars, 1)
        for r in range(3):
            for c in range(3):
                self.assertEqual(st.grid[r][c], UNKNOWN)

    def test_region_cells_grouping(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        self.assertEqual(sorted(st.region_cells.keys()), [1, 2, 3])
        self.assertEqual(set(st.region_cells[1]), {(0, 0), (0, 1), (0, 2)})

    def test_set_and_count(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        st.set_cell(0, 0, STAR)
        self.assertEqual(st.count_state(st.cells_of_row(0), STAR), 1)
        self.assertEqual(len(st.unknowns(st.cells_of_row(0))), 2)

    def test_neighbors_corner(self):
        st = CandidateState(make_3x3_rows(), stars=1)
        self.assertEqual(set(st.neighbors(0, 0)), {(0, 1), (1, 0), (1, 1)})

    def test_apply_deduction_changes_cells(self):
        from deduction import Deduction
        st = CandidateState(make_3x3_rows(), stars=1)
        st.apply(Deduction("t", 1, [(1, 1, STAR), (0, 0, ELIMINATED)], "r"))
        self.assertEqual(st.grid[1][1], STAR)
        self.assertEqual(st.grid[0][0], ELIMINATED)

    def test_is_complete_valid_true(self):
        # 合法 5x5 解；区域取列分组，星位列互异且互不相邻
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        for (r, c) in [(0, 0), (1, 2), (2, 4), (3, 1), (4, 3)]:
            st.set_cell(r, c, STAR)
        self.assertTrue(is_complete_valid(st))

    def test_is_complete_valid_false_when_incomplete(self):
        region = [[c + 1 for c in range(5)] for _ in range(5)]
        st = CandidateState(region, stars=1)
        st.set_cell(0, 0, STAR)  # 只放 1 颗，远未完成
        self.assertFalse(is_complete_valid(st))


if __name__ == "__main__":
    unittest.main()

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'candidate_state'`

- [ ] **Step 3: 写实现**

写实现 `MiscTools/difficulty/candidate_state.py`:

```python
"""Star Battle 候选态模型：每格三态 + 行/列/区域查询。"""

UNKNOWN = 0
STAR = 1
ELIMINATED = 2


class CandidateState:
    def __init__(self, region_grid, stars):
        self.region_grid = region_grid
        self.dim = len(region_grid)
        self.stars = stars
        self.grid = [[UNKNOWN] * self.dim for _ in range(self.dim)]
        self.invalid = False
        self.region_cells = {}
        for r in range(self.dim):
            for c in range(self.dim):
                self.region_cells.setdefault(region_grid[r][c], []).append((r, c))

    # --- 单元访问 ---
    def cells_of_row(self, r):
        return [(r, c) for c in range(self.dim)]

    def cells_of_col(self, c):
        return [(r, c) for r in range(self.dim)]

    def cells_of_region(self, region_id):
        return list(self.region_cells[region_id])

    def cells_of_line(self, axis, idx):
        return self.cells_of_row(idx) if axis == "row" else self.cells_of_col(idx)

    def all_units(self):
        """返回 [(kind, key, cells), ...]，kind in {'row','col','region'}。"""
        units = []
        for r in range(self.dim):
            units.append(("row", r, self.cells_of_row(r)))
        for c in range(self.dim):
            units.append(("col", c, self.cells_of_col(c)))
        for rid in self.region_cells:
            units.append(("region", rid, self.cells_of_region(rid)))
        return units

    # --- 查询 ---
    def count_state(self, cells, state):
        return sum(1 for (r, c) in cells if self.grid[r][c] == state)

    def unknowns(self, cells):
        return [(r, c) for (r, c) in cells if self.grid[r][c] == UNKNOWN]

    def neighbors(self, r, c):
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.dim and 0 <= nc < self.dim:
                    out.append((nr, nc))
        return out

    # --- 修改 ---
    def set_cell(self, r, c, state):
        self.grid[r][c] = state

    def apply(self, deduction):
        for (r, c, state) in deduction.marks:
            # 矛盾检测：若试图覆盖一个已是相反确定态的格子
            cur = self.grid[r][c]
            if cur != UNKNOWN and cur != state:
                self.invalid = True
            self.grid[r][c] = state
        # 单元星数超限 -> 矛盾
        for (_kind, _key, cells) in self.all_units():
            if self.count_state(cells, STAR) > self.stars:
                self.invalid = True

    def is_solved(self):
        if self.invalid:
            return False
        return is_complete_valid(self)


def is_complete_valid(state):
    """检查当前 STAR 布局是否为一个合法完整解。"""
    dim, stars = state.dim, state.stars
    # 每个单元恰好 stars 颗星
    for (_kind, _key, cells) in state.all_units():
        if state.count_state(cells, STAR) != stars:
            return False
    # 总星数
    total = sum(1 for r in range(dim) for c in range(dim) if state.grid[r][c] == STAR)
    if total != dim * stars:
        return False
    # 无相邻星
    for r in range(dim):
        for c in range(dim):
            if state.grid[r][c] == STAR:
                for (nr, nc) in state.neighbors(r, c):
                    if state.grid[nr][nc] == STAR:
                        return False
    return True
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_state.py -v`
Expected: PASS（所有用例通过）

- [ ] **Step 5: 提交**

```bash
git add MiscTools/difficulty/candidate_state.py MiscTools/difficulty/tests/test_state.py
git commit -m "feat(difficulty): add CandidateState model with unit queries and validity check"
```

---

## Task 3: 推理数据结构（Deduction / Step / Trace）

**Files:**
- Create: `MiscTools/difficulty/deduction.py`
- Create: `MiscTools/difficulty/tests/test_deduction.py`

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_deduction.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduction import Deduction, Step, Trace


class TestDeduction(unittest.TestCase):
    def test_deduction_fields(self):
        d = Deduction("adjacency_elimination", 1, [(0, 0, 2)], "邻接消除")
        self.assertEqual(d.technique_name, "adjacency_elimination")
        self.assertEqual(d.tier, 1)
        self.assertEqual(d.marks, [(0, 0, 2)])
        self.assertEqual(d.reason, "邻接消除")

    def test_step_from_deduction(self):
        d = Deduction("t", 2, [(1, 1, 1)], "r")
        step = Step.from_deduction(d)
        self.assertEqual(step.technique_name, "t")
        self.assertEqual(step.tier, 2)
        self.assertEqual(step.marks, [(1, 1, 1)])

    def test_trace_defaults(self):
        t = Trace()
        self.assertEqual(t.steps, [])
        self.assertFalse(t.solved)
        self.assertIsNone(t.stuck_state)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_deduction.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'deduction'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/deduction.py`:

```python
"""解题推理的数据结构。"""


class Deduction:
    """一个技巧在当前局面下得出的一批确定标记。

    marks: list of (row, col, new_state)
    """

    def __init__(self, technique_name, tier, marks, reason):
        self.technique_name = technique_name
        self.tier = tier
        self.marks = marks
        self.reason = reason


class Step:
    """引擎应用一次 Deduction 后记录的一步。"""

    def __init__(self, technique_name, tier, marks, reason):
        self.technique_name = technique_name
        self.tier = tier
        self.marks = marks
        self.reason = reason

    @classmethod
    def from_deduction(cls, d):
        return cls(d.technique_name, d.tier, d.marks, d.reason)


class Trace:
    """一次解题的完整轨迹。"""

    def __init__(self, steps=None, solved=False, stuck_state=None):
        self.steps = steps if steps is not None else []
        self.solved = solved
        self.stuck_state = stuck_state
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_deduction.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add MiscTools/difficulty/deduction.py MiscTools/difficulty/tests/test_deduction.py
git commit -m "feat(difficulty): add Deduction/Step/Trace data structures"
```

---

## Task 4: T1 基础技巧（邻接消除 / 单元已满 / 末格）

**Files:**
- Create: `MiscTools/difficulty/techniques/t1_basic.py`
- Create: `MiscTools/difficulty/tests/test_t1.py`

> 技巧统一接口：函数 `find(state) -> Deduction | None`，**只产出当前为 UNKNOWN 的格子的新标记**（保证引擎不会反复应用同一技巧而死循环）；无新标记返回 `None`。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_t1.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell


def rows_region(dim):
    return [[r + 1 for _ in range(dim)] for r in range(dim)]


class TestT1(unittest.TestCase):
    def test_adjacency_marks_8_neighbors(self):
        st = CandidateState(rows_region(3), stars=1)
        st.set_cell(1, 1, STAR)
        d = adjacency_elimination(st)
        self.assertIsNotNone(d)
        self.assertEqual(d.technique_name, "adjacency_elimination")
        self.assertEqual(d.tier, 1)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertEqual(marked, {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)})
        self.assertTrue(all(s == ELIMINATED for (_, _, s) in d.marks))

    def test_adjacency_none_when_no_star(self):
        st = CandidateState(rows_region(3), stars=1)
        self.assertIsNone(adjacency_elimination(st))

    def test_unit_complete_eliminates_rest_of_row(self):
        # 区域设为竖直列，避免与行区域重叠干扰断言
        st = CandidateState([[c + 1 for c in range(3)] for _ in range(3)], stars=1)
        st.set_cell(0, 0, STAR)
        d = unit_complete(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        # 行 0 其余两格 + 列 0 其余两格 + 区域(列0)其余两格（列0 与区域0 相同）
        self.assertIn((0, 1), marked)
        self.assertIn((0, 2), marked)
        self.assertIn((1, 0), marked)
        self.assertIn((2, 0), marked)

    def test_last_cell_places_star(self):
        st = CandidateState([[c + 1 for c in range(3)] for _ in range(3)], stars=1)
        st.set_cell(0, 0, ELIMINATED)
        st.set_cell(0, 1, ELIMINATED)
        d = last_cell(st)
        self.assertIsNotNone(d)
        self.assertIn((0, 2, STAR), d.marks)

    def test_last_cell_none_when_multiple_unknown(self):
        st = CandidateState([[c + 1 for c in range(3)] for _ in range(3)], stars=1)
        self.assertIsNone(last_cell(st))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_t1.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'techniques.t1_basic'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/techniques/t1_basic.py`:

```python
"""T1 基础技巧（tier 1）。每个函数 find(state)->Deduction|None。"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction

TIER = 1


def adjacency_elimination(state):
    marks = []
    seen = set()
    for r in range(state.dim):
        for c in range(state.dim):
            if state.grid[r][c] == STAR:
                for (nr, nc) in state.neighbors(r, c):
                    if state.grid[nr][nc] == UNKNOWN and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        marks.append((nr, nc, ELIMINATED))
    if not marks:
        return None
    return Deduction("adjacency_elimination", TIER, marks,
                     "星的 8 邻格不能再有星")


def unit_complete(state):
    marks = []
    seen = set()
    for (_kind, _key, cells) in state.all_units():
        if state.count_state(cells, STAR) == state.stars:
            for (r, c) in state.unknowns(cells):
                if (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("unit_complete", TIER, marks,
                     "单元已放满所需星数，其余格清除")


def last_cell(state):
    marks = []
    seen = set()
    for (_kind, _key, cells) in state.all_units():
        placed = state.count_state(cells, STAR)
        unk = state.unknowns(cells)
        if placed < state.stars and len(unk) == state.stars - placed:
            for (r, c) in unk:
                if (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, STAR))
    if not marks:
        return None
    return Deduction("last_cell", TIER, marks,
                     "单元剩余空格数恰等于待放星数")
```

并创建空的技巧包标记文件 `MiscTools/difficulty/techniques/__init__.py`（内容留空一行即可，使 `from techniques.t1_basic import ...` 可用）：

```python
# techniques package
```

> 说明：`techniques/` 作为子目录需要 `__init__.py` 才能被 `from techniques.x import y` 导入；而 `difficulty/` 自身仍非包（靠 sys.path）。两者不冲突。

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_t1.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add MiscTools/difficulty/techniques/__init__.py MiscTools/difficulty/techniques/t1_basic.py MiscTools/difficulty/tests/test_t1.py
git commit -m "feat(difficulty): add T1 basic techniques (adjacency, unit-complete, last-cell)"
```

---

## Task 5: 解题引擎（engine）+ 技巧注册表

**Files:**
- Create: `MiscTools/difficulty/techniques/__init__.py`（修改：加入 `ALL_TECHNIQUES` 注册表）
- Create: `MiscTools/difficulty/engine.py`
- Create: `MiscTools/difficulty/tests/test_engine.py`

> 引擎：按 tier 升序扫描技巧，用第一个产出非空 Deduction 的技巧，应用、记录 Step、重头再扫；解出或全部技巧无果（卡死）则停止。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_engine.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, STAR
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell
from engine import solve


class TestEngine(unittest.TestCase):
    def _vertical_regions(self, dim):
        return [[c + 1 for c in range(dim)] for _ in range(dim)]

    def test_solves_from_four_placed_stars(self):
        # 区域=竖直列；已知合法解星位 (0,0),(1,2),(2,4),(3,1),(4,3)
        st = CandidateState(self._vertical_regions(5), stars=1)
        for (r, c) in [(0, 0), (1, 2), (2, 4), (3, 1)]:
            st.set_cell(r, c, STAR)
        techniques = [adjacency_elimination, unit_complete, last_cell]
        trace = solve(st, techniques)
        self.assertTrue(trace.solved)
        self.assertEqual(st.grid[4][3], STAR)
        self.assertTrue(len(trace.steps) >= 1)

    def test_stuck_returns_unsolved_with_state(self):
        # 空盘 + 仅 last_cell：无法推进 -> 卡死
        st = CandidateState(self._vertical_regions(5), stars=1)
        trace = solve(st, [last_cell])
        self.assertFalse(trace.solved)
        self.assertIsNotNone(trace.stuck_state)

    def test_registry_sorted_by_tier(self):
        from techniques import ALL_TECHNIQUES
        tiers = [getattr(t, "tier", None) for t in ALL_TECHNIQUES]
        self.assertEqual(tiers, sorted(t for t in tiers))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/engine.py`:

```python
"""解题引擎：最低档技巧优先，逐步推进直至解出或卡死。"""

from deduction import Step, Trace

MAX_STEPS = 10000  # 安全上限，防御性


def _tier_of(technique):
    # 技巧函数可带 .tier 属性；缺省按其返回 Deduction 的 tier。
    return getattr(technique, "tier", 1)


def solve(state, techniques):
    ordered = sorted(techniques, key=_technique_sort_key)
    steps = []
    for _ in range(MAX_STEPS):
        if state.is_solved():
            return Trace(steps=steps, solved=True, stuck_state=None)
        if state.invalid:
            return Trace(steps=steps, solved=False, stuck_state=state)
        progressed = False
        for technique in ordered:
            deduction = technique(state)
            if deduction and deduction.marks:
                state.apply(deduction)
                steps.append(Step.from_deduction(deduction))
                progressed = True
                break
        if not progressed:
            return Trace(steps=steps, solved=False, stuck_state=state)
    return Trace(steps=steps, solved=False, stuck_state=state)


def _technique_sort_key(technique):
    # 优先用注册表里声明的 tier；普通函数缺省 tier=1。
    return getattr(technique, "tier", 1)
```

修改 `MiscTools/difficulty/techniques/__init__.py` 为带 tier 标注的注册表：

```python
# techniques package
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell


def _tag(fn, tier):
    fn.tier = tier
    return fn


# 按 tier 升序排列；新增技巧在此登记即可被引擎使用。
ALL_TECHNIQUES = [
    _tag(adjacency_elimination, 1),
    _tag(unit_complete, 1),
    _tag(last_cell, 1),
]
```

> `solve()` 接收任意技巧函数列表（测试里传裸函数，默认 tier=1）；生产用 `ALL_TECHNIQUES`（带 `.tier`）。排序键读取 `.tier`，缺省 1。

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_engine.py -v`
Expected: PASS（3 个用例通过）

- [ ] **Step 5: 运行全部已有测试，确认无回归**

Run: `for f in MiscTools/difficulty/tests/test_*.py; do python3 "$f" || exit 1; done; echo ALL_OK`
Expected: 末行输出 `ALL_OK`

- [ ] **Step 6: 提交**

```bash
git add MiscTools/difficulty/engine.py MiscTools/difficulty/techniques/__init__.py MiscTools/difficulty/tests/test_engine.py
git commit -m "feat(difficulty): add solving engine and technique registry"
```

---

## Task 6: T2 技巧之一（区域限行/列 + 排除）

**Files:**
- Create: `MiscTools/difficulty/techniques/t2_geometry.py`
- Modify: `MiscTools/difficulty/techniques/__init__.py`（注册新技巧）
- Create: `MiscTools/difficulty/tests/test_t2.py`

> `region_confined_to_line`：某区域剩余可放星的 UNKNOWN 全在同一行/列 → 该行/列的星必在此区域 → 清除该行/列中此区域外的 UNKNOWN。
> `exclusion`：某仍需放星的区域，其所有候选 UNKNOWN 都是某格 X 的邻格 → 放 X 会害死该区域 → 清除 X。
> 两者均限 `stars == 1`（多星情形留待覆盖循环后续补充）。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_t2.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from techniques.t2_geometry import region_confined_to_line, exclusion


class TestT2(unittest.TestCase):
    def test_region_confined_to_row(self):
        # 4x4：区域 1 占据第 0 行的前两格 (0,0)(0,1)；其余格分配给其它区域
        region = [
            [1, 1, 2, 2],
            [3, 3, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        # 区域 1 的两格都在行 0 -> 行 0 的星必在区域 1 -> 行 0 中区域 1 外的格清除
        d = region_confined_to_line(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 2), marked)
        self.assertIn((0, 3), marked)
        self.assertNotIn((0, 0), marked)
        self.assertNotIn((0, 1), marked)

    def test_exclusion_kills_dominating_cell(self):
        # 3x3：区域 2 = {(0,2),(1,2)}，二者的公共邻格 {(0,1),(1,1)} 若放星会害死区域 2
        region = [
            [1, 1, 2],
            [1, 1, 2],
            [3, 3, 3],
        ]
        st = CandidateState(region, stars=1)  # 全 UNKNOWN
        d = exclusion(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        # 区域 2 的两个候选 (0,2)(1,2) 的公共邻格 -> 应被清除
        self.assertIn((0, 1), marked)
        self.assertIn((1, 1), marked)

    def test_techniques_return_none_when_inapplicable(self):
        region = [[c + 1 for c in range(4)] for _ in range(4)]
        st = CandidateState(region, stars=1)
        # 全 UNKNOWN、竖直区域：每个区域候选跨 4 行，不限行/列
        self.assertIsNone(region_confined_to_line(st))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_t2.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'techniques.t2_geometry'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/techniques/t2_geometry.py`:

```python
"""T2 几何/计数技巧（tier 2）。均限 stars == 1。"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction

TIER = 2


def _regions_needing_star(state):
    """返回 {region_id: [候选 UNKNOWN 格...]}，仅含仍需放星的区域。"""
    out = {}
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, STAR) < state.stars:
            unk = state.unknowns(cells)
            if unk:
                out[rid] = unk
    return out


def region_confined_to_line(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    for rid, unk in _regions_needing_star(state).items():
        rows = {r for (r, c) in unk}
        cols = {c for (r, c) in unk}
        if len(rows) == 1:
            row = next(iter(rows))
            for (r, c) in state.unknowns(state.cells_of_row(row)):
                if state.region_grid[r][c] != rid and (r, c) not in seen:
                    seen.add((r, c)); marks.append((r, c, ELIMINATED))
        if len(cols) == 1:
            col = next(iter(cols))
            for (r, c) in state.unknowns(state.cells_of_col(col)):
                if state.region_grid[r][c] != rid and (r, c) not in seen:
                    seen.add((r, c)); marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("region_confined_to_line", TIER, marks,
                     "区域候选全在单行/列，锁定该行/列的星于此区域")


def exclusion(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    for rid, unk in _regions_needing_star(state).items():
        # 该区域所有候选的公共邻格（且非候选自身）= 放则害死本区域
        candidate_set = set(unk)
        common = None
        for (r, c) in unk:
            nbrs = set(state.neighbors(r, c))
            common = nbrs if common is None else (common & nbrs)
        if not common:
            continue
        for (r, c) in common:
            if (r, c) in candidate_set:
                continue
            if state.grid[r][c] == UNKNOWN and (r, c) not in seen:
                seen.add((r, c)); marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("exclusion", TIER, marks,
                     "该格是某待放星区域全部候选的公共邻格，放星会害死该区域")
```

修改 `MiscTools/difficulty/techniques/__init__.py`，登记新技巧（在 `ALL_TECHNIQUES` 列表中追加，保持按 tier 升序）：

```python
# techniques package
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell
from techniques.t2_geometry import region_confined_to_line, exclusion


def _tag(fn, tier):
    fn.tier = tier
    return fn


ALL_TECHNIQUES = [
    _tag(adjacency_elimination, 1),
    _tag(unit_complete, 1),
    _tag(last_cell, 1),
    _tag(region_confined_to_line, 2),
    _tag(exclusion, 2),
]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_t2.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add MiscTools/difficulty/techniques/t2_geometry.py MiscTools/difficulty/techniques/__init__.py MiscTools/difficulty/tests/test_t2.py
git commit -m "feat(difficulty): add T2 techniques region-confined-to-line and exclusion"
```

---

## Task 7: T2 技巧之二（欠计数 / 过计数 鸽笼）

**Files:**
- Create: `MiscTools/difficulty/techniques/t2_counting.py`
- Modify: `MiscTools/difficulty/techniques/__init__.py`
- Create: `MiscTools/difficulty/tests/test_t2_counting.py`

> `undercounting`：k 个待放星区域的候选恰好落在 k 条行（或列）内 → 这 k 条线的星全被这些区域占用 → 清除这些线内、属于集合外区域的 UNKNOWN。
> `overcounting`：对偶——k 条行（或列）的候选恰好落在 k 个区域内 → 清除这些区域内、不在这 k 条线上的 UNKNOWN。
> 均限 `stars == 1`，并用 `MAX_PIGEONHOLE = 3` 限制组合规模（小棋盘足够，避免组合爆炸）。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_t2_counting.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from candidate_state import CandidateState, ELIMINATED
from techniques.t2_counting import undercounting, overcounting


class TestT2Counting(unittest.TestCase):
    def test_undercounting_two_regions_two_rows(self):
        # 4x4：让区域 1、2 的候选都只落在行 0、行 1 内
        region = [
            [1, 1, 2, 2],
            [1, 1, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        # 区域1 候选 {(0,0),(0,1),(1,0),(1,1)}，区域2 候选 {(0,2),(0,3),(1,2),(1,3)}
        # 两区域候选并集落在行 {0,1}，|rows|==2==k -> 行0、行1 的星都在区域1、2内
        # -> 行0、行1 中属于其它区域的 UNKNOWN 被清除（此布局行0/1全属区域1、2，故无可清；
        #    改为构造存在跨区域的行）
        region = [
            [1, 1, 2, 5],
            [1, 1, 2, 5],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        # 此时区域1候选 ⊆ 行{0,1}，区域2候选 ⊆ 行{0,1}
        # 行0、行1 含区域5的格 (0,3)(1,3) -> 应被清除
        d = undercounting(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((0, 3), marked)
        self.assertIn((1, 3), marked)

    def test_overcounting_two_rows_two_regions(self):
        # 对偶构造：行0、行1 的候选恰落在区域 1、2 内
        region = [
            [1, 1, 2, 2],
            [1, 1, 2, 2],
            [1, 3, 4, 4],
            [3, 3, 4, 4],
        ]
        st = CandidateState(region, stars=1)
        # 行0、行1 的候选区域 = {1,2}，|regions|==2==k
        # -> 区域1、2 内不在行0/1 的 UNKNOWN 被清除：区域1 含 (2,0) -> 应清除
        d = overcounting(st)
        self.assertIsNotNone(d)
        marked = {(r, c) for (r, c, s) in d.marks}
        self.assertIn((2, 0), marked)

    def test_none_when_no_pigeonhole(self):
        region = [[c + 1 for c in range(4)] for _ in range(4)]
        st = CandidateState(region, stars=1)
        self.assertIsNone(undercounting(st))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_t2_counting.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'techniques.t2_counting'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/techniques/t2_counting.py`:

```python
"""T2 鸽笼计数技巧（tier 2）：undercounting / overcounting。限 stars == 1。"""

from itertools import combinations

from candidate_state import ELIMINATED
from deduction import Deduction

from candidate_state import STAR

TIER = 2
MAX_PIGEONHOLE = 3


def _lines_of(unk, axis):
    return {(r if axis == "row" else c) for (r, c) in unk}


def undercounting(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    regions = {}
    for rid, cells in state.region_cells.items():
        if state.count_state(cells, 1) < state.stars:
            unk = state.unknowns(cells)
            if unk:
                regions[rid] = unk
    rids = list(regions.keys())
    for axis in ("row", "col"):
        for k in range(2, MAX_PIGEONHOLE + 1):
            for combo in combinations(rids, k):
                lines = set()
                for rid in combo:
                    lines |= _lines_of(regions[rid], axis)
                if len(lines) == k:
                    combo_set = set(combo)
                    for line in lines:
                        cells = state.cells_of_line(axis, line)
                        for (r, c) in state.unknowns(cells):
                            if state.region_grid[r][c] not in combo_set and (r, c) not in seen:
                                seen.add((r, c)); marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("undercounting", TIER, marks,
                     "k 个区域候选落在 k 条线内，锁定这些线的星于这些区域")


def overcounting(state):
    if state.stars != 1:
        return None
    marks = []
    seen = set()
    for axis in ("row", "col"):
        line_count = state.dim
        # 每条线的候选区域集合
        line_regions = {}
        for idx in range(line_count):
            cells = state.unknowns(state.cells_of_line(axis, idx))
            if cells:
                line_regions[idx] = ({state.region_grid[r][c] for (r, c) in cells}, cells)
        line_ids = list(line_regions.keys())
        for k in range(2, MAX_PIGEONHOLE + 1):
            for combo in combinations(line_ids, k):
                regions = set()
                for idx in combo:
                    regions |= line_regions[idx][0]
                if len(regions) == k:
                    combo_lines = set(combo)
                    for rid in regions:
                        for (r, c) in state.unknowns(state.cells_of_region(rid)):
                            on_line = (r if axis == "row" else c) in combo_lines
                            if not on_line and (r, c) not in seen:
                                seen.add((r, c)); marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("overcounting", TIER, marks,
                     "k 条线候选落在 k 个区域内，锁定这些区域的星于这些线")
```

> 注意：`_regions_needing_star` 在 undercounting 内联重写（上面的独立版本含占位逻辑，最终以 undercounting/overcounting 内联实现为准；删除文件顶部的 `_regions_needing_star` 占位函数，保留 `_lines_of`）。请确保提交的文件中**不包含** `_regions_needing_star`（它带有无效的占位表达式）。

修改 `MiscTools/difficulty/techniques/__init__.py`：

```python
# techniques package
from techniques.t1_basic import adjacency_elimination, unit_complete, last_cell
from techniques.t2_geometry import region_confined_to_line, exclusion
from techniques.t2_counting import undercounting, overcounting


def _tag(fn, tier):
    fn.tier = tier
    return fn


ALL_TECHNIQUES = [
    _tag(adjacency_elimination, 1),
    _tag(unit_complete, 1),
    _tag(last_cell, 1),
    _tag(region_confined_to_line, 2),
    _tag(exclusion, 2),
    _tag(undercounting, 2),
    _tag(overcounting, 2),
]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_t2_counting.py -v`
Expected: PASS

- [ ] **Step 5: 运行全部测试确认无回归**

Run: `for f in MiscTools/difficulty/tests/test_*.py; do python3 "$f" || exit 1; done; echo ALL_OK`
Expected: 末行 `ALL_OK`

- [ ] **Step 6: 提交**

```bash
git add MiscTools/difficulty/techniques/t2_counting.py MiscTools/difficulty/techniques/__init__.py MiscTools/difficulty/tests/test_t2_counting.py
git commit -m "feat(difficulty): add T2 pigeonhole techniques (under/overcounting)"
```

---

## Task 8: 计分器（scorer）

**Files:**
- Create: `MiscTools/difficulty/scorer.py`
- Create: `MiscTools/difficulty/tests/test_scorer.py`

> 方案 2：最高 tier 决定档位（band），档内由"最高档技巧使用次数 / 用到多少种不同最高档技巧 / 总步数"加权细分。未解出 → Expert。权重与映射集中为模块常量，便于校准调整。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_scorer.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deduction import Step, Trace
from scorer import score_trace


def step(name, tier):
    return Step(name, tier, [(0, 0, 1)], "r")


class TestScorer(unittest.TestCase):
    def test_unsolved_is_expert(self):
        t = Trace(steps=[step("a", 1)], solved=False, stuck_state=object())
        result = score_trace(t)
        self.assertEqual(result["band"], "Expert")

    def test_band_from_max_tier(self):
        t1 = Trace(steps=[step("last_cell", 1)], solved=True)
        t2 = Trace(steps=[step("last_cell", 1), step("exclusion", 2)], solved=True)
        self.assertEqual(score_trace(t1)["band"], "Easy")
        self.assertEqual(score_trace(t2)["band"], "Medium")

    def test_higher_tier_scores_higher(self):
        t1 = Trace(steps=[step("last_cell", 1)], solved=True)
        t2 = Trace(steps=[step("exclusion", 2)], solved=True)
        self.assertLess(score_trace(t1)["score"], score_trace(t2)["score"])

    def test_more_hard_steps_scores_higher_within_band(self):
        few = Trace(steps=[step("exclusion", 2)], solved=True)
        many = Trace(steps=[step("exclusion", 2), step("undercounting", 2),
                            step("overcounting", 2)], solved=True)
        self.assertLess(score_trace(few)["score"], score_trace(many)["score"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_scorer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scorer'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/scorer.py`:

```python
"""难度计分器（方案 2）。所有权重集中于此，便于校准。"""

TIER_TO_BAND = {0: "Trivial", 1: "Easy", 2: "Medium"}
UNSOLVED_BAND = "Expert"

W_HIGH_STEP_COUNT = 1.0     # 每个最高档步数
W_DISTINCT_HIGH = 5.0       # 每种不同的最高档技巧
W_TOTAL_STEPS = 0.1         # 每个总步数
UNSOLVED_BASE = 1000.0      # 未解出基线分（高于任何已解出分）
BAND_BASE = 100.0           # 每提升一档的基础分


def score_trace(trace):
    if not trace.solved:
        return {"band": UNSOLVED_BAND,
                "score": UNSOLVED_BASE + W_TOTAL_STEPS * len(trace.steps)}

    max_tier = max((s.tier for s in trace.steps), default=0)
    band = TIER_TO_BAND.get(max_tier, "Medium")
    high_steps = [s for s in trace.steps if s.tier == max_tier]
    distinct_high = len({s.technique_name for s in high_steps})

    score = (BAND_BASE * max_tier
             + W_HIGH_STEP_COUNT * len(high_steps)
             + W_DISTINCT_HIGH * distinct_high
             + W_TOTAL_STEPS * len(trace.steps))
    return {"band": band, "score": score, "max_tier": max_tier,
            "steps": len(trace.steps)}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_scorer.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add MiscTools/difficulty/scorer.py MiscTools/difficulty/tests/test_scorer.py
git commit -m "feat(difficulty): add difficulty scorer (band + intra-band weighting)"
```

---

## Task 9: 评分入口（rate.py，含 analyze 函数）

**Files:**
- Create: `MiscTools/difficulty/rate.py`
- Create: `MiscTools/difficulty/tests/test_rate.py`

> `analyze(sbn) -> dict`：串起 decode → CandidateState → solve(ALL_TECHNIQUES) → score_trace。CLI 用 argparse 包装：`python3 rate.py <sbn>`。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_rate.py`:

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate import analyze


class TestRate(unittest.TestCase):
    def test_analyze_returns_band_and_score(self):
        result = analyze("551W9jo0cIn")
        self.assertIsNotNone(result)
        self.assertIn("band", result)
        self.assertIn("score", result)
        self.assertIn("solved", result)
        self.assertIn("steps", result)

    def test_analyze_invalid_sbn(self):
        result = analyze("garbage")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_rate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rate'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/rate.py`:

```python
"""CLI：对单个 SBN 谜题计算难度。

用法：
    python3 rate.py <sbn>
"""

import argparse
import sys

from sbn_codec import decode_to_grid
from candidate_state import CandidateState
from engine import solve
from scorer import score_trace
from techniques import ALL_TECHNIQUES


def analyze(sbn):
    """解码并评分单个 SBN。失败返回 None。"""
    decoded = decode_to_grid(sbn)
    if decoded is None:
        return None
    state = CandidateState(decoded["region_grid"], decoded["stars"])
    trace = solve(state, list(ALL_TECHNIQUES))
    scored = score_trace(trace)
    return {
        "sbn": sbn,
        "dim": decoded["dim"],
        "stars": decoded["stars"],
        "solved": trace.solved,
        "band": scored["band"],
        "score": scored["score"],
        "steps": len(trace.steps),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="计算 Star Battle 谜题难度")
    parser.add_argument("sbn", help="SBN 谜题字符串")
    args = parser.parse_args(argv)
    result = analyze(args.sbn)
    if result is None:
        print("无法解析该 SBN", file=sys.stderr)
        return 1
    print("维度: {dim}x{dim}  星: {stars}".format(**result))
    print("解出: {}  档位: {}  分数: {:.2f}  步数: {}".format(
        result["solved"], result["band"], result["score"], result["steps"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_rate.py -v`
Expected: PASS

- [ ] **Step 5: 手动冒烟测试 CLI**

Run: `python3 MiscTools/difficulty/rate.py 551W9jo0cIn`
Expected: 打印两行，含"维度: 5x5"、"档位: ..."（band 为 Easy/Medium/Expert 之一，不报错）

- [ ] **Step 6: 提交**

```bash
git add MiscTools/difficulty/rate.py MiscTools/difficulty/tests/test_rate.py
git commit -m "feat(difficulty): add rate CLI and analyze entrypoint"
```

---

## Task 10: 覆盖工具（coverage.py）—— 找出技巧覆盖不到的卡点

**Files:**
- Create: `MiscTools/difficulty/coverage.py`
- Create: `MiscTools/difficulty/tests/test_coverage.py`

> 批量跑一个谜题文件（每行一个 SBN），分类为 solved / stuck，并对 stuck 谜题导出可读的卡点网格快照，供人工命名缺失技巧。这是"求解器驱动的技巧补全循环"的机器侧。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_coverage.py`:

```python
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coverage import analyze_file, render_state


class TestCoverage(unittest.TestCase):
    def test_analyze_file_classifies(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("551W9jo0cIn\n")
            f.write("881W8AKBNEeYHXnmB62j6O0\n")
            f.write("garbage-line\n")
            path = f.name
        try:
            report = analyze_file(path)
            self.assertEqual(report["total"], 3)
            self.assertEqual(report["unparsable"], 1)
            self.assertEqual(report["solved"] + report["stuck"], 2)
            self.assertIsInstance(report["stuck_samples"], list)
        finally:
            os.unlink(path)

    def test_render_state_returns_text(self):
        from candidate_state import CandidateState, STAR
        st = CandidateState([[1, 2], [1, 2]], stars=1)
        st.set_cell(0, 0, STAR)
        text = render_state(st)
        self.assertIsInstance(text, str)
        self.assertIn("★", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_coverage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'coverage'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/coverage.py`:

```python
"""技巧覆盖分析：批量找出当前技巧库解不动的谜题及其卡点快照。

用法：
    python3 coverage.py <puzzle_file.txt> [--max-stuck 20]
"""

import argparse
import sys

from sbn_codec import decode_to_grid
from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from engine import solve
from techniques import ALL_TECHNIQUES

_GLYPH = {UNKNOWN: ".", STAR: "★", ELIMINATED: "x"}


def render_state(state):
    lines = []
    for r in range(state.dim):
        lines.append(" ".join(_GLYPH[state.grid[r][c]] for c in range(state.dim)))
    return "\n".join(lines)


def analyze_file(path, max_stuck=20):
    total = solved = stuck = unparsable = 0
    stuck_samples = []
    with open(path, "r") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            total += 1
            decoded = decode_to_grid(line)
            if decoded is None:
                unparsable += 1
                continue
            state = CandidateState(decoded["region_grid"], decoded["stars"])
            trace = solve(state, list(ALL_TECHNIQUES))
            if trace.solved:
                solved += 1
            else:
                stuck += 1
                if len(stuck_samples) < max_stuck:
                    stuck_samples.append({
                        "sbn": line,
                        "snapshot": render_state(trace.stuck_state),
                    })
    return {"total": total, "solved": solved, "stuck": stuck,
            "unparsable": unparsable, "stuck_samples": stuck_samples}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Star Battle 技巧覆盖分析")
    parser.add_argument("path", help="谜题文件（每行一个 SBN）")
    parser.add_argument("--max-stuck", type=int, default=20,
                        help="最多导出多少个卡点快照")
    args = parser.parse_args(argv)
    report = analyze_file(args.path, args.max_stuck)
    print("总计 {total}  解出 {solved}  卡死 {stuck}  无法解析 {unparsable}".format(**report))
    for i, sample in enumerate(report["stuck_samples"], 1):
        print("\n--- 卡点 #{} ---\n{}\n{}".format(i, sample["sbn"], sample["snapshot"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_coverage.py -v`
Expected: PASS

- [ ] **Step 5: 在真实语料上冒烟测试**

Run: `python3 MiscTools/difficulty/coverage.py Main/puzzles/Files/8-1-ez.txt --max-stuck 3`
Expected: 打印"总计 N  解出 X  卡死 Y  无法解析 Z"统计行（不报错）；若有卡死则附带网格快照

- [ ] **Step 6: 提交**

```bash
git add MiscTools/difficulty/coverage.py MiscTools/difficulty/tests/test_coverage.py
git commit -m "feat(difficulty): add coverage tool to surface uncovered impasses"
```

---

## Task 11: 校准报告（calibrate.py）+ 文档

**Files:**
- Create: `MiscTools/difficulty/calibrate.py`
- Create: `MiscTools/difficulty/tests/test_calibrate.py`
- Create: `MiscTools/difficulty/README.md`

> 在已标注的 1 星语料上批量评分，输出每个难度文件的"解出率 / 平均分 / 档位分布"，供人工调整 `scorer.py` 常量。验收只做**软检查**（结构正确、运行不报错），因为初版技巧库未必能解开 hard 题；单调对齐由人工看报告完成。

- [ ] **Step 1: 写失败测试**

`MiscTools/difficulty/tests/test_calibrate.py`:

```python
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibrate import summarize_file


class TestCalibrate(unittest.TestCase):
    def test_summarize_file_structure(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("551W9jo0cIn\n")
            f.write("881W8AKBNEeYHXnmB62j6O0\n")
            path = f.name
        try:
            s = summarize_file(path)
            self.assertEqual(s["count"], 2)
            self.assertIn("solved_rate", s)
            self.assertIn("avg_score", s)
            self.assertIn("band_distribution", s)
            self.assertIsInstance(s["band_distribution"], dict)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 MiscTools/difficulty/tests/test_calibrate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'calibrate'`

- [ ] **Step 3: 写实现**

`MiscTools/difficulty/calibrate.py`:

```python
"""校准报告：在已标注语料上汇总解出率/平均分/档位分布。

用法：
    python3 calibrate.py Main/puzzles/Files/8-1-ez.txt Main/puzzles/Files/8-1-med.txt ...
"""

import argparse
import sys

from rate import analyze


def summarize_file(path):
    count = solved = 0
    score_sum = 0.0
    band_dist = {}
    with open(path, "r") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            result = analyze(line)
            if result is None:
                continue
            count += 1
            if result["solved"]:
                solved += 1
            score_sum += result["score"]
            band_dist[result["band"]] = band_dist.get(result["band"], 0) + 1
    return {
        "path": path,
        "count": count,
        "solved_rate": (solved / count) if count else 0.0,
        "avg_score": (score_sum / count) if count else 0.0,
        "band_distribution": band_dist,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Star Battle 难度校准报告")
    parser.add_argument("files", nargs="+", help="一个或多个谜题文件")
    args = parser.parse_args(argv)
    for path in args.files:
        s = summarize_file(path)
        print("{path}: 共 {count}  解出率 {solved_rate:.0%}  平均分 {avg_score:.1f}  分布 {band_distribution}".format(**s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 MiscTools/difficulty/tests/test_calibrate.py -v`
Expected: PASS

- [ ] **Step 5: 在真实 1 星语料上生成校准报告（人工查看）**

Run:
```bash
python3 MiscTools/difficulty/calibrate.py \
  Main/puzzles/Files/8-1-ez.txt \
  Main/puzzles/Files/8-1-med.txt \
  Main/puzzles/Files/8-1-hard.txt \
  Main/puzzles/Files/9-1-ez.txt \
  Main/puzzles/Files/9-1-med.txt \
  Main/puzzles/Files/9-1-hard.txt
```
Expected: 每个文件一行报告。**人工检查**：ez 的平均分应 ≤ med ≤ hard（大致单调）。若不单调或 hard 解出率过低，调整 `scorer.py` 常量或用 `coverage.py` 找缺失技巧（属后续迭代，不阻塞本计划完成）。

- [ ] **Step 6: 写 README**

`MiscTools/difficulty/README.md`:

```markdown
# Star Battle 难度计算（离线，Python）

对 1 星 Star Battle 谜题做"带技巧标注的逻辑解题"，产出逐步轨迹并计算难度分。

## 用法

评分单个谜题：

    python3 MiscTools/difficulty/rate.py <SBN>

找出技巧库解不动的卡点（用于补全技巧）：

    python3 MiscTools/difficulty/coverage.py Main/puzzles/Files/8-1-hard.txt

在已标注语料上生成校准报告：

    python3 MiscTools/difficulty/calibrate.py Main/puzzles/Files/8-1-ez.txt ...

## 运行测试

    for f in MiscTools/difficulty/tests/test_*.py; do python3 "$f" || break; done

## 结构

- `sbn_codec.py` —— SBN 解码为 region_grid（复用自 SBNBatchValidator）
- `candidate_state.py` —— 候选态模型（三态 + 行/列/区域查询 + 合法解校验）
- `deduction.py` —— Deduction / Step / Trace 数据结构
- `techniques/` —— 技巧库；每个技巧 `find(state)->Deduction|None`，带 `.tier`
- `engine.py` —— 最低档技巧优先的解题引擎
- `scorer.py` —— 难度计分（最高 tier 定档 + 档内加权）
- `coverage.py` —— 卡点发现（技巧补全循环的机器侧）
- `calibrate.py` —— 在标注语料上汇总，供人工校准

## 扩展技巧

实现一个 `find(state)->Deduction|None` 函数，在 `techniques/__init__.py` 的
`ALL_TECHNIQUES` 中以正确 tier 登记即可——引擎与计分器无需改动。

## 范围

当前仅针对 1 星谜题；多星专属技巧、浏览器 UI 展示为后续工作。
```

- [ ] **Step 7: 运行全部测试，确认整套无回归**

Run: `for f in MiscTools/difficulty/tests/test_*.py; do python3 "$f" || exit 1; done; echo ALL_OK`
Expected: 末行 `ALL_OK`

- [ ] **Step 8: 提交**

```bash
git add MiscTools/difficulty/calibrate.py MiscTools/difficulty/tests/test_calibrate.py MiscTools/difficulty/README.md
git commit -m "feat(difficulty): add calibration report and module README"
```

---

## 自检结果（写计划者已核对）

**Spec 覆盖：**
- SBN 解析 → Task 1
- 候选态模型 → Task 2
- 数据结构（Deduction/Step/Trace）→ Task 3
- T1 基础技巧 → Task 4
- 解题引擎 → Task 5
- T2 区域限行/列 + 排除 → Task 6
- T2 欠计数/过计数 → Task 7
- 计分器（方案 2）→ Task 8
- CLI 入口 → Task 9
- 覆盖/补全循环工具 → Task 10
- 校准 + README + 测试策略 → Task 11
- 测试策略（每技巧单测、引擎解题验证、计分档位、校准）→ 贯穿 Task 4–11
- 错误处理（解析失败/卡死/矛盾）→ Task 1（None）、Task 2（invalid）、Task 5（卡死返回 stuck_state）、Task 10（unparsable 计数）

**placeholder 扫描：** 已清除（Task 2 测试与 Task 7 `t2_counting.py` 原先的占位均已替换为可运行代码）。

**类型/命名一致性（已核对）：**
- `decode_to_grid` 返回键 `region_grid` / `stars` / `dim`，所有调用方一致。
- `Deduction.marks` 统一为 `(row, col, new_state)` 三元组。
- 技巧统一签名 `find(state) -> Deduction | None`，且只对 `UNKNOWN` 格产出新标记（保证引擎不死循环）。
- 引擎按技巧的 `.tier` 升序选用；`ALL_TECHNIQUES` 始终按 tier 升序登记。
- 单元访问统一经由 `CandidateState.all_units()` / `cells_of_row|col|region|line`。
```
