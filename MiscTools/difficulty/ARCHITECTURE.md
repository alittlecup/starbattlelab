# Star Battle 难度计算模块 —— 架构与实现说明

> 本文档面向「后续接手的 agent / 开发者」。读完它即可全面了解本模块**做什么、为什么这么做、怎么用、怎么扩展**，无需再逐文件逆向。
>
> - 代码位置：`MiscTools/difficulty/`
> - 语言/依赖：Python 3.11，**仅标准库**（无第三方依赖）
> - 运行形态：**离线命令行工具**（不在浏览器中运行）
> - 当前范围：**仅 1 星谜题**（multi-star 留待后续）
> - 设计与计划文档：
>   - 设计 spec：`docs/superpowers/specs/2026-06-24-starbattle-difficulty-metric-design.md`
>   - 实现计划：`docs/superpowers/plans/2026-06-24-starbattle-difficulty-metric.md`

---

## 1. 这个模块解决什么问题

仓库里的谜题难度此前只是**写死的人工标签**（文件名后缀 `ez/med/hard/expert`），没有任何"算出来"的难度，也没有模拟人类解题的逻辑求解器。

本模块提供一个**可复用的"单谜题难度计算"能力**：输入一个 SBN 谜题字符串，输出它的难度（档位 + 连续分），并附带一条**逐步解题轨迹，且每一步都标注了所用的人类解题技巧**。

### 核心理念（务必理解）

**核心交付物不是"分数公式"，而是"带技巧标注的解题轨迹（technique-attributed trace）"。** 难度分只是这条轨迹之上一层很薄的表达——计分公式怎么调都不影响主体。因此本模块的重心是：

> **用一组按"由易到难"排序的、人类会用的命名技巧，纯逻辑（不猜测、不回溯）地解题，并记录每一步用了哪个技巧。**

最难用到的技巧档位（tier）主导难度档位，再用使用次数/种类/步数做档内细分。这条路线与数独界的 Sudoku Explainer 同源，优点是**对玩家可解释、可教学**（未来能告诉玩家"这一步用了什么技巧"）。

### 为什么选"命名技巧"而不是"搜索统计 / 推理深度"

调研时对比过三条路线：
- **A. 命名技巧（本模块采用）**：枚举人类技巧、按难度分级。最贴合人类感受、可解释；代价是要逐个实现技巧。
- B. 搜索统计：直接用回溯求解器的节点数/回溯次数。实现快，但与人类感受相关性弱。
- C. 推理深度（refutation depth）：不命名技巧，测量"假设-反驳"深度。自动、不漏技巧，但不可解释。

选 A 的依据：游戏以"解谜与技巧成长"为乐趣；谜题单一解 → 必存在纯逻辑解题路径；技巧有限可收敛。**未覆盖的技巧通过"求解器驱动的补全循环"系统性补齐**（见 §6 `coverage.py`），而不是一次性穷举。

---

## 2. 数据流总览

```
SBN 字符串
   │  sbn_codec.decode_to_grid()
   ▼
{region_grid, stars, dim}
   │  CandidateState(region_grid, stars)
   ▼
CandidateState  ◀─────────────┐  反复 apply(Deduction)
   │                          │
   │  engine.solve(state, ALL_TECHNIQUES)
   ▼                          │
 逐轮：按 tier 升序扫描技巧 ──▶ 技巧库 techniques/*  （每个技巧 find(state)->Deduction|None）
   │  每步记录 Step(technique_name, tier, marks, reason)
   ▼
Trace { steps, solved, stuck_state }
   ├─ scorer.score_trace(trace) ──▶ {band, score, max_tier, steps}
   └─ coverage：solved=False 时导出 stuck_state 快照，供人工命名缺失技巧
```

终端入口：
- `rate.py` —— 评分单个谜题（`analyze(sbn)` + CLI）
- `coverage.py` —— 批量找"解不动"的卡点
- `calibrate.py` —— 在已标注语料上汇总，供人工校准计分参数

---

## 3. 候选态模型（求解的工作面）

所有技巧都工作在同一个三态模型上。**解题 = 不断把 UNKNOWN 格推成 STAR 或 ELIMINATED。**

`candidate_state.py`：

```python
UNKNOWN = 0      # 未定
STAR = 1         # 确定有星
ELIMINATED = 2   # 确定无星（人类玩法里的 X / 点）

class CandidateState:
    def __init__(self, region_grid, stars): ...
    # 属性
    self.dim            # 棋盘维度 N（N×N）
    self.stars          # 每行/列/区域的星数（本期实际只测 1）
    self.region_grid    # 二维数组，每格的区域 id
    self.grid           # 二维数组，每格的三态值
    self.region_cells   # {region_id: [(r,c), ...]}（构造时算一次）
    self.invalid        # 出现矛盾时置 True

    # 单元访问（"单元" = 一行 / 一列 / 一个区域）
    def cells_of_row(r)            -> [(r,c)...]
    def cells_of_col(c)            -> [(r,c)...]
    def cells_of_region(region_id) -> [(r,c)...]
    def cells_of_line(axis, idx)   # axis ∈ {"row","col"}
    def all_units()                -> [(kind, key, cells), ...]  # kind ∈ {"row","col","region"}

    # 查询（按需扫描，不缓存——小棋盘足够，且避免缓存失效 bug）
    def count_state(cells, state)  -> int
    def unknowns(cells)            -> [(r,c)...]   # 仅 UNKNOWN 的格
    def neighbors(r, c)            -> [(r,c)...]   # 8 邻（棋盘内）

    # 修改
    def set_cell(r, c, state)
    def apply(deduction)           # 应用一批标记；放星导致单元超额则置 invalid
    def is_solved()                -> bool         # 见下方 is_complete_valid

def is_complete_valid(state) -> bool
    # 合法完整解的判定（也是 is_solved 的依据）：
    #   - 每个行/列/区域恰好 stars 颗星
    #   - 总星数 == dim * stars
    #   - 任意两颗星不相邻（含对角线 / 8 邻）
```

> 关键正确性保证：`is_complete_valid` 覆盖了 Star Battle 的全部约束（含对角相邻），所以引擎不会把"非法布局"误判为已解。

---

## 4. 推理数据结构

`deduction.py`：

```python
class Deduction:
    # 一个技巧在当前局面得出的一批确定标记
    technique_name: str
    tier: int
    marks: list[(row, col, new_state)]   # new_state ∈ {STAR, ELIMINATED}
    reason: str                          # 人类可读的中文理由（为未来 UI 预留）

class Step:
    # 引擎应用一次 Deduction 后记录的一步（字段同 Deduction）
    @classmethod
    def from_deduction(cls, d) -> Step

class Trace:
    steps: list[Step]            # 逐步轨迹（核心交付物）
    solved: bool                 # 是否纯逻辑解出
    stuck_state: CandidateState  # 未解出时的卡死局面快照（否则 None）
```

---

## 5. 技巧库（`techniques/`）

### 统一约定（实现新技巧必须遵守）

每个技巧是一个函数，签名固定：

```python
def 技巧名(state) -> Deduction | None
```

规则：
1. **只对当前为 `UNKNOWN` 的格子产出新标记**——这保证引擎不会反复应用同一技巧而死循环。
2. 没有任何新标记时**返回 `None`**。
3. 每个技巧模块定义常量 `TIER`，并在模块末尾对函数设置 `.tier = TIER`。
   **这是 tier 的单一来源**：引擎排序用 `fn.tier`，计分用 `Deduction.tier`，二者都来自这个 `TIER`，不会不一致。

### 已实现技巧一览

| tier | 技巧 | 文件 | 推理（1 星语境） |
|------|------|------|------|
| 1 | `adjacency_elimination` | `t1_basic.py` | 任意 STAR 的 8 邻格不可能有星 → 标 ELIMINATED |
| 1 | `unit_complete` | `t1_basic.py` | 某行/列/区域已放满所需星数 → 其余 UNKNOWN 标 ELIMINATED |
| 1 | `last_cell` | `t1_basic.py` | 某单元剩余 UNKNOWN 数恰等于待放星数 → 这些格必为 STAR |
| 2 | `region_confined_to_line` | `t2_geometry.py` | 某待放星区域的候选全在同一行/列 → 该行/列的星锁定在此区域 → 该行/列里属于其它区域的 UNKNOWN 标 ELIMINATED |
| 2 | `exclusion` | `t2_geometry.py` | 某待放星区域的**全部候选**都是格 X 的邻格（X 自身非候选）→ 在 X 放星会害死该区域 → X 标 ELIMINATED |
| 2 | `undercounting` | `t2_counting.py` | k 个待放星区域的候选恰落在 k 条行（或列）内 → 这 k 条线的星全被这些区域占用 → 这些线里属于集合外区域的 UNKNOWN 标 ELIMINATED |
| 2 | `overcounting` | `t2_counting.py` | （对偶）k 条行（或列）的候选区域恰为 k 个 → 这 k 个区域的星锁定在这 k 条线上 → 这些区域里不在这 k 条线上的 UNKNOWN 标 ELIMINATED |

实现注意：
- `undercounting`/`overcounting` 用 `itertools.combinations`，并以 `MAX_PIGEONHOLE = 3` 限制组合规模，避免组合爆炸。
- T2 的四个技巧目前都**用 `if state.stars != 1: return None` 守卫**——它们的鸽笼推理只对 1 星严格成立。扩展 multi-star 时需要重新推导。

### 注册表

`techniques/__init__.py` 导出 `ALL_TECHNIQUES`：一个按 tier 升序排列的技巧函数列表。引擎、`rate.py`、`coverage.py` 都用它。新增技巧只需在对应模块实现 + 设 `.tier`，再在此列表按 tier 位置登记即可——**引擎与计分器无需改动**。

---

## 6. 各模块职责与公开接口

### `sbn_codec.py` —— SBN 解码
```python
def decode_to_grid(sbn_string) -> {"region_grid": list[list[int]], "stars": int, "dim": int} | None
```
- 解码失败返回 `None`。
- 内部 `decode_sbn` / `reconstruct_grid_from_borders` 复制自 `MiscTools/SBNBatchValidator.py`（已在生产验证），**故意复制而非 import**，以避免该脚本的 multiprocessing/argparse 副作用。
- 支持的 SBN：2 字符维度码（`55`=5×5 … `PP`=25×25）+ 单数字星数 + 区域边界 base64 位域。仓库的 1 星语料（`551W…`/`881W…`/`991W…`）均可解。

### `engine.py` —— 解题引擎
```python
def solve(state, techniques) -> Trace
```
算法：循环——按 `.tier` 升序扫描 `techniques`，用**第一个**产出非空 `Deduction` 的技巧，`apply` 之并记 `Step`，回到最低 tier 重扫；直到 `is_solved()`（solved=True）或所有技巧都无果（卡死，solved=False，带 `stuck_state`）。
- 有 `MAX_STEPS = 10000` 防御性上限。
- **不做猜测/回溯**：卡死即代表"当前技巧库覆盖不到"，这正是补全循环的信号。

### `scorer.py` —— 难度计分（方案 2）
```python
def score_trace(trace) -> {"band": str, "score": float, "max_tier": int, "steps": int}
```
- 未解出 → `band="Expert"`，分数 `UNSOLVED_BASE(=1000) + 0.1*步数`（保证高于任何已解出分）。
- 解出 → `band` 由最高 tier 经 `TIER_TO_BAND = {0:"Trivial",1:"Easy",2:"Medium"}` 映射；分数 = `BAND_BASE*max_tier + W_HIGH_STEP_COUNT*最高档步数 + W_DISTINCT_HIGH*最高档技巧种数 + W_TOTAL_STEPS*总步数`。
- **所有权重与映射都是模块顶部常量**，校准时只改这里。

### `rate.py` —— 单题评分入口
```python
def analyze(sbn) -> {"sbn","dim","stars","solved","band","score","steps"} | None
```
- 串起 decode → CandidateState → solve(ALL_TECHNIQUES) → score_trace。
- CLI：`python3 MiscTools/difficulty/rate.py <SBN>`

### `coverage.py` —— 技巧补全循环（机器侧）
```python
def render_state(state) -> str          # 把局面渲染成可读网格（'.' / '★' / 'x'）
def analyze_file(path, max_stuck=20) -> {"total","solved","stuck","unparsable","stuck_samples"}
```
- 批量跑一个谜题文件（每行一个 SBN），分类 solved/stuck/unparsable，导出 stuck 局面快照。
- 用法：`python3 MiscTools/difficulty/coverage.py Main/puzzles/Files/8-1-hard.txt --max-stuck 20`
- **工作流**：跑语料 → 看 stuck 快照 → 人工命名缺失技巧 → 实现并登记 → 重跑，直至覆盖收敛。

### `calibrate.py` —— 校准报告
```python
def summarize_file(path) -> {"path","count","solved_rate","avg_score","band_distribution"}
```
- 用法：`python3 MiscTools/difficulty/calibrate.py <file1> <file2> ...`
- 在已标注语料上对比，调 `scorer.py` 常量使计算档位与人工标签单调对齐。

---

## 7. 目录结构

```
MiscTools/difficulty/
├── README.md            快速上手（用法速查）
├── ARCHITECTURE.md      本文档（深入说明）
├── sbn_codec.py         SBN → region_grid
├── candidate_state.py   候选态模型 + 合法解校验
├── deduction.py         Deduction / Step / Trace
├── engine.py            解题引擎
├── scorer.py            难度计分
├── rate.py              单题评分 CLI（analyze）
├── coverage.py          卡点发现工具
├── calibrate.py         校准报告
├── techniques/
│   ├── __init__.py      ALL_TECHNIQUES 注册表
│   ├── t1_basic.py      T1：adjacency / unit_complete / last_cell
│   ├── t2_geometry.py   T2：region_confined_to_line / exclusion
│   └── t2_counting.py   T2：undercounting / overcounting
└── tests/               每个模块/技巧一个 test_*.py（stdlib unittest，38 个测试）
```

---

## 8. 测试与运行

- 框架：**标准库 `unittest`**（pytest 未安装）。每个测试文件可单独运行。
- 跑全部测试：
  ```bash
  for f in MiscTools/difficulty/tests/test_*.py; do python3 "$f" || break; done
  ```
- 导入约定：`difficulty/` **不是 Python 包**（无顶层 `__init__.py`，与 `MiscTools/` 脚本风格一致）。模块间用顶层名互相导入（`from candidate_state import ...`），依赖 `difficulty/` 在 `sys.path` 上：直接运行脚本时其所在目录自动入 `sys.path[0]`；测试文件用头部片段把 `difficulty/` 加入路径。`techniques/` 因为要 `from techniques.x import y`，**有**自己的 `__init__.py`。

---

## 9. 校准结果（验证：难度分确实对标人类难度）

在仓库自带的人工标注 1 星语料上跑 `calibrate.py`，平均难度分**严格单调 易 < 中 < 难**：

| 文件 | 解出率 | 平均分 |
|------|--------|--------|
| `8-1-ez`  | 100% | 211.8 |
| `8-1-med` | 90%  | 298.6 |
| `8-1-hard`| 79%  | 384.8 |
| `9-1-ez`  | 97%  | 180.7 |
| `9-1-med` | 90%  | 281.3 |
| `9-1-hard`| 72%  | 440.0 |

解读：解出率随难度下降、平均分随难度上升，两端都单调——技巧型指标与人工标签方向一致。**这是本方案有效性的主要证据。**

---

## 10. 已知范围与局限（接手前必读）

- **仅 1 星**。T2 鸽笼技巧用 `stars != 1` 守卫；multi-star 会被当作"技巧不足"而卡死，属预期。
- **不猜测/不回溯**。需要唯一性假设或试探的高级技巧（如 Star Battle 的 By a Thread / At Sea / Fish 等）尚未实现，遇到这类题会卡死并归为 Expert。
- **技巧库尚未完备**。`coverage.py` 在 hard 语料上仍有一定 stuck 比例（如 9-1-hard ~28%）——这正是补全循环要继续推进的部分，不是 bug。
- **计分权重未精调**。当前只保证档位方向单调；档内分数尚未对照大量人工细分校准。
- **8×8 ez 样本偏少**（仅 8 题且都落 Medium），Easy 档阈值在 8×8 上可能需要下调——留待校准。

---

## 11. 后续路线（按优先级）

1. **跑补全循环补齐 1 星技巧库**：对 hard/expert 语料跑 `coverage.py`，按 stuck 快照命名并实现缺失技巧（优先：Squeeze、Composite Shapes、Set Differentials、Fish/Finned Fish，以及基于唯一性的 By a Thread / At Sea）。
2. **精调计分**：用更多人工标注做档内校准，必要时把 tier 细化（如把 T2 拆成 2a/2b）。
3. **扩展 multi-star**：重做鸽笼类技巧的 multi-star 推导，加入 2 星专属阵型（Kissing Ls / M / Pressured Ts）。
4. **接入浏览器 UI**：把 `Trace` 暴露给前端，向玩家逐步展示"这步用了什么技巧"（届时需用 JS 重实现或共享逻辑——本期是纯 Python 离线）。
5. **支撑谜题生成 / 按目标难度筛选**：用 `analyze` 给生成的谜题打分，只保留落在目标难度带的。

---

## 12. 给接手 agent 的"如何新增一个技巧"清单

1. 在合适的 `techniques/tX_*.py` 里写 `def 新技巧(state) -> Deduction | None`，遵守 §5 的统一约定（只标 UNKNOWN、无果返 None、用 `Deduction(name, TIER, marks, reason)`）。
2. 在该模块末尾设 `新技巧.tier = TIER`。
3. 在 `techniques/__init__.py` 的 `ALL_TECHNIQUES` 里按 tier 升序登记。
4. 在 `tests/` 写单测：构造**最小局面**，断言它**恰好**做出预期标记、且在不该触发时返回 `None`。
5. 跑 `coverage.py` 看新技巧把多少原本 stuck 的题变成 solved。
6. 跑 `calibrate.py` 确认难度档位仍单调。
```
