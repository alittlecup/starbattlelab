# Star Battle 难度计算模块 —— 架构与实现存档

> 面向后续接手的 agent / 开发者。读完即可全面了解本模块**做什么、怎么实现、当前到哪一步、如何扩展**。
>
> - 代码位置：`MiscTools/difficulty/`
> - 语言/依赖：Python 3.11，**仅标准库**（无第三方依赖）
> - 运行形态：**离线命令行工具**（不在浏览器中运行）
> - 范围：**1 星谜题**，当前**解出率 100%**（命名技巧 + 搜索兜底）
> - 配套文档：
>   - **[`RULES.md`](./RULES.md)** —— 全部解题规则（技巧）的含义、例子、难度因子、难度模型与各项决策（**权威规则清单**）
>   - [`README.md`](./README.md) —— 用法速查
>   - 设计 spec / 计划：`docs/superpowers/specs/2026-06-24-*`、`docs/superpowers/plans/2026-06-24-*`

---

## 1. 这个模块解决什么问题

仓库的谜题难度此前只是写死的人工标签（`ez/med/hard`）。本模块提供**可复用的"单谜题难度计算"**：输入一个 SBN 谜题，输出难度（档位 + 连续分），并附带**带技巧标注的解题轨迹**。

**核心理念**：核心交付物是"**每一步都标注了所用人类技巧的解题轨迹**"，难度分只是其上的薄层表达。用一组按"由易到难"排序的命名技巧纯逻辑解题、记录每步所用技巧；最难一步的难度 = 谜题难度。逻辑解不动的题，用**搜索兜底**收尾。这就是设计之初定的**方案 C 混合**（命名技巧作主指标 + 搜索兜底收尾不可约的尾巴）。

---

## 2. 数据流总览

```
SBN 字符串
   │ sbn_codec.decode_to_grid()
   ▼
{region_grid, stars, dim}
   │ CandidateState(region_grid, stars)         三态网格：UNKNOWN / STAR / ELIMINATED
   ▼
engine.solve(state, ALL_TECHNIQUES)             由易到难逐步推进，每步记 Step(rule_id, meta)
   │
   ├─ 解出 ──▶ scorer.score_trace(trace, config) ──▶ {band, score, hardest_rule}
   │            每步难度 = lo + complexity(因子)×(hi−lo)；谜题难度 = 最难一步
   │
   └─ 卡死 ──▶ search_solver.solve_complete()    逻辑传播 + MRV 回溯
                ├─ 唯一解 → 追加 guessing 步（rule 18）→ score：lo(600)+加成 → Expert
                ├─ 2 解   → Ambiguous（数据异常）
                └─ 0 解   → Broken（不应出现）
```

终端入口：`rate.py`（单题）、`coverage.py`（批量找逻辑卡点）、`calibrate.py`（语料汇总）、`tools/difficulty-editor.html`（区间配置编辑器）。

---

## 3. 难度模型（关键）

- **区间制**：每条规则在难度轴上占一个区间 `[lo, hi]`（来自 `difficulty-config.json`），区间可重叠。
- **区间内因子**：某步的具体难度 = `lo + complexity(因子) × (hi − lo)`，`complexity ∈ [0,1]` 由 `factors.py` 按结构因子算出（如规则 6 的"相连/数量"、规则 8/9 的 k、规则 7 的候选数）。归一化用**固定上限 CAP=7**（跨棋盘可比）。
- **聚合**：谜题难度 = 全程**最难一步**的值。
- **搜索兜底（规则 18 guessing）**：命名技巧解不动时，分 = `lo(600) + W_guess×guesses + W_depth×depth`（开放上限，搜索越多/越深越高）。
- **档位（band）**：basic→Easy、geo→Medium、adv→Hard、uniq→VeryHard、search→Expert。
- **熟练度层**：预留维度（玩家对规则/阵型的掌握会降难），当前默认恒等、不影响分。
- 详尽的规则排序决策见 `RULES.md §1`。

---

## 4. 已实现的规则（技巧）

| 规则 | 技巧函数 | 文件 | 区间内因子 |
|------|----------|------|------------|
| 1 行/列已满 | `line_complete` | t1_basic.py | 中点 |
| 2 邻接打叉 | `adjacency_elimination` | t1_basic.py | 中点 |
| 3 区域已满 | `region_complete` | t1_basic.py | 中点 |
| 4 行/列唯一空格 | `line_last_cell` | t1_basic.py | 中点 |
| 5 区域唯一空格 | `region_last_cell` | t1_basic.py | 中点 |
| 6 区域限行/列 | `region_confined_to_line` | t2_geometry.py | 相连(主)+数量(次)，严格劈半 |
| 7 排除 | `exclusion` | t2_geometry.py | 候选数量 |
| 8 欠计数 | `undercounting` | t2_counting.py | k |
| 9 过计数 | `overcounting` | t2_counting.py | k |
| 11 带鳍计数（欠+过）| `finned_counts` | t2_finned.py | k |
| 12 集合差分 | `set_differentials` | t2_setdiff.py | m（线数）|
| 13 鱼 | `fish` | t3_fish.py | n |
| 14 带鳍鱼 | `finned_fish` | t3_fish.py | n |
| 18 搜索兜底 guessing | `solve_complete` | search_solver.py | guesses / depth |

- **跳过**：规则 10 受压排除（经分析与"规则 2/6 + 规则 7"等价，永不产出新结论，是死规则）。
- **未实现**：规则 15–17 唯一性类（复杂罕见；有搜索兜底后非必需）。
- 每条规则的含义、例子、难度因子详见 `RULES.md §3`。

### 各技巧实测增量（在 8×8 hard / 1444→1511 题语料上，体现"求解器驱动补全循环"）
带鳍计数 **+254**（决定性）≫ 带鳍鱼 +14 > 鱼 +3 > 集合差分 +0（与带鳍重叠）→ 剩余尾巴由搜索兜底收尾 → **100%**。

---

## 5. 各模块职责与公开接口

- **`sbn_codec.py`**：`decode_to_grid(sbn) -> {region_grid, stars, dim} | None`。复制自 `MiscTools/SBNBatchValidator.py` 的已验证解码（故意复制以避免其副作用）。
- **`candidate_state.py`**：`CandidateState(region_grid, stars)`；三态常量 `UNKNOWN/STAR/ELIMINATED`；查询 `cells_of_row/col/region/line`、`all_units`、`count_state`、`unknowns`、`neighbors`；修改 `set_cell`、`apply`、`copy`（回溯用）；`is_solved` / `is_complete_valid`（覆盖行/列/区域星数 + 对角相邻）。
- **`deduction.py`**：`Deduction` / `Step`（带 `rule_id`、`meta`）/ `Trace`。
- **`factors.py`**：`complexity(rule_id, meta) -> [0,1]`，集中所有规则的区间内因子映射（CAP=7）。
- **`engine.py`**：`solve(state, techniques) -> Trace`。按 `.tier` 升序选最便宜可推进的技巧，逐步应用直到解出或卡死。不猜测。
- **`scorer.py`**：`load_config(path)`、`score_trace(trace, config) -> {band, score, hardest_rule, steps}`。`_rule_value` 一般规则用区间+因子，`guessing` 用 `lo + 加成`。`RULE_CATEGORY` / `CATEGORY_BAND` 决定档位。
- **`search_solver.py`**：`solve_complete(state, max_solutions=2) -> {solutions, guesses, depth, nodes}`。逻辑传播（复用 engine）+ MRV 回溯；找最多 2 解判唯一性；统计搜索代价。安全上限 `MAX_NODES`。
- **`rate.py`**：`analyze(sbn, config=None) -> dict`（含 `solved_via`、`n_solutions`、`band`、`score`、`hardest_rule`）。CLI：`python3 rate.py <sbn> [--config p]`。
- **`coverage.py`**：`analyze_file(path)` 批量统计逻辑引擎的解出/卡死，导出卡点快照（命名技巧补全循环的机器侧）。
- **`calibrate.py`**：`summarize_file(path)` 在标注语料上汇总解出率/平均分/档位分布。
- **`difficulty-config.json`**：难度配置（每规则区间 + guessing 的 lo/权重）。由 `tools/difficulty-editor.html` 可视化编辑。
- **`tools/difficulty-editor.html`**：网页区间编辑器（共享轴 Gantt + 精调面板），导出/保存 JSON 配置。

---

## 6. 目录结构

```
MiscTools/difficulty/
├── README.md / ARCHITECTURE.md / RULES.md      文档（本文件为实现存档）
├── difficulty-config.json                      难度配置（区间 + guessing）
├── sbn_codec.py  candidate_state.py  deduction.py  factors.py
├── engine.py  scorer.py  search_solver.py
├── rate.py  coverage.py  calibrate.py           CLI 入口
├── techniques/
│   ├── __init__.py            ALL_TECHNIQUES 注册表（按 tier 升序）
│   ├── t1_basic.py            规则 1–5
│   ├── t2_geometry.py         规则 6–7
│   ├── t2_counting.py         规则 8–9
│   ├── t2_finned.py           规则 11（带鳍欠/过计数）
│   ├── t2_setdiff.py          规则 12（集合差分）
│   └── t3_fish.py             规则 13（鱼）、14（带鳍鱼）
├── tests/                     16 个 test_*.py（stdlib unittest）
└── tools/difficulty-editor.html
```

---

## 7. 用法与测试

```bash
# 单题评分
python3 MiscTools/difficulty/rate.py 551W9jo0cIn

# 找逻辑引擎解不动的卡点（命名技巧补全循环）
python3 MiscTools/difficulty/coverage.py Main/puzzles/Files/8-1-hard.txt

# 在标注语料上校准
python3 MiscTools/difficulty/calibrate.py Main/puzzles/Files/8-1-ez.txt ...

# 全部测试
for f in MiscTools/difficulty/tests/test_*.py; do python3 "$f" || break; done
```

导入约定：`difficulty/` **不是包**（无顶层 `__init__.py`），模块间用顶层名互导，依赖该目录在 `sys.path`（脚本运行时自动；测试用头部片段加入）。`techniques/` 是子包（有 `__init__.py`）。

---

## 8. 最终成果（1 星语料）

| 文件 | 解出率 | 平均分 | 档位分布 |
|------|--------|--------|----------|
| 8-1-ez  | 100% | 99  | 全 Medium |
| 8-1-med | 100% | 176 | Medium 多，Hard 142，Expert 7 |
| 8-1-hard| 100% | 264 | Medium 1198，Hard 284，Expert 29 |
| 9-1-ez  | 100% | 57  | Easy/Medium |
| 9-1-med | 100% | 143 | Medium 多，Hard 44 |
| 9-1-hard| 100% | 288 | Medium 65，Hard 19，Expert 5 |

- **每道题都有唯一解 + 具体难度分**；难度**严格单调** 易 < 中 < 难；
- Expert（需试错）随难度递增、且内部按搜索量可比；
- 命名技巧解出 ~98%（hard），其余由搜索兜底收尾至 100%。

---

## 9. 决策日志（为什么这么做）

- **方案 A（命名技巧）+ 方案 C（搜索兜底）**：命名技巧给人类可理解、可教学的难度作主指标；解不动的尾巴用搜索保证 100% 可解 + 确认唯一。
- **难度 = 区间制 + 区间内因子**（非固定值）：每规则一个区间，因子（相连/数量/k/n…）定位区间内具体值；归一化固定 CAP=7（跨棋盘可比）；规则 6 用"严格劈半"。
- **行/列解耦、默认相同**：几何对称、个体差异无统一方向，故默认相等但参数独立可调。
- **反向(已满)< 正向(唯一空格)**；**区域 > 行列**；邻接打叉视为"固定形状区域"插在二者之间。
- **唯一性假设合法**（谜题保证唯一解）。
- **规则 10 跳过**（与规则 2/6+7 等价的死规则）；**规则 12 保留但当前增量为 0**（与带鳍计数重叠）。
- **数据驱动选技巧**：每加一个技巧就用 `coverage.py` 实测增量、用"解出数只增不减"作正确性护栏 —— 这正是"求解器驱动的补全循环"。

---

## 10. 后续可选方向（非必需）

1. **批量给关卡打分落库**，接回游戏 / 生成器（按目标难度筛选）。
2. **精调 config 区间**：用网页编辑器 + 更多人工标注对齐。
3. **编辑器 v2**：把行/列解耦、区间内因子权重也做成可视化可调。
4. **熟练度层**：引入玩家个性化难度（掌握的阵型降难）。
5. **规则 15–17 唯一性类**：给目前归为 Expert 的题更"人类可解释"的难度（有搜索兜底后非必需）。
6. **扩展 2 星及以上**（multi-star）：B 组专属技巧（2×2、Shapes、Kissing Ls 等，见 `RULES.md §11`）。

---

## 11. 给接手 agent 的"如何新增一条规则"清单

1. 在合适的 `techniques/*.py` 写 `def 规则(state) -> Deduction | None`：只标 UNKNOWN 格、无果返 None、每步只返回"最容易的单实例"并把因子记入 `meta`。
2. 设 `规则.tier`（引擎选用顺序）与 `rule_id`（配置键）。
3. 在 `techniques/__init__.py` 的 `ALL_TECHNIQUES` 按 tier 升序登记。
4. `factors.py` 加该 `rule_id` 的 `complexity`（无因子则默认中点）。
5. `difficulty-config.json` 加该规则区间；`scorer.RULE_CATEGORY` 加其类别。
6. 写单测（最小局面，断言恰好的标记）。
7. 跑 `coverage.py` 看实测增量、跑 `calibrate.py` 确认仍单调、确认解出数只增不减。
