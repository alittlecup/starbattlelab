# Star Battle 难度计算指标 —— 设计文档（第一份 spec）

- 日期：2026-06-24
- 状态：已批准，待实现
- 范围：技巧标注 + 难度分的**最小可用闭环**，Python 离线分析，聚焦 1 星谜题

## 1. 背景与目标

仓库 `starbattlelab.github.io` 是一个 Star Battle 解谜网页应用。当前"难度"只是写死在谜题文件名/文本里的人工标签（`ez/med/hard/expert/unsorted`），没有任何计算出来的难度，也没有模拟人类解题的逻辑求解器。

**目标**：实现一个可复用的"单谜题难度计算"能力。其核心不是某个分数公式，而是**为解题过程中的每一步精确标注所用的人类解题技巧**，产出一条"带技巧标注的解题轨迹（technique-attributed trace）"。难度分只是这条轨迹之上一层很薄的表达，公式可随时调整而不动主体。

选择"命名技巧"路线（方案 A）的理由：
- 游戏本身以解谜与技巧成长为乐趣，玩家能从"这一步用了什么技巧"中学习和获得成就感（虽然 UI 展示不在本 spec，但数据结构为其预留）。
- 当前谜题均为单一解 → 一定存在纯逻辑解题路径。
- 技巧总量有限且可收敛，可通过"求解器驱动的技巧补全循环"系统性逼近完备。

### 非目标（本 spec 明确推迟）
- 技巧库的完备化（仅实现第一批足以解掉大部分 1 星题的技巧）。
- 2 星及以上的专属技巧（Kissing Ls / M / Pressured Ts / Fish 等）。
- 浏览器内、面向玩家的技巧展示 UI。
- 谜题生成。
- JavaScript 实现（本期纯 Python 离线）。

## 2. 设计哲学（来自调研）

业界谜题难度评估有两大流派：命名技巧加权（如数独的 Sudoku Explainer），与不命名技巧的"推理深度"自动指标。本项目选**命名技巧路线**，因为它对玩家有可解释性与教学价值。

核心结论（对标人类难度）：难度由"为了推进，最难需要用到的技巧档位"主导，再辅以"各技巧使用次数 / 用到多少种高档技巧 / 总步数"做档内细分。

## 3. 总体架构与数据流

```
SBN 字符串 ──decode_sbn()──▶ region grid (+ stars)
   │
   ▼
CandidateState（每格三态 + 行/列/区域派生信息）◀──┐
   │                                              │ 反复应用 Deduction
   ▼                                              │
Engine（最低档技巧优先）───────────────────────▶ Techniques 技巧库
   │ 每步产出 Step(technique_name, tier, marked_cells, reason)
   ▼
Trace（逐步轨迹 + 是否解出 + 卡点快照）
   ├──▶ Scorer ──▶ 难度分 + 档位
   └──▶ Coverage 工具：解不动 → 导出卡点供人工命名缺失技巧
```

核心交付物是 **Trace**。难度分是其薄层表达。

## 4. 组件设计

各组件单一职责、接口清晰、可独立测试。建议放在新建子目录 `MiscTools/difficulty/`。

### 4.1 `sbn_codec.py` —— SBN 解析
- 复用 / 抽取 `MiscTools/SBNBatchValidator.py` 中已有的 `decode_sbn()` 与 `reconstruct_grid_from_borders()`。
- 输入：SBN 字符串（v1/v2 均支持）。输出：`{region_grid: list[list[int]], stars: int, dim: int}`。
- 纯函数，无副作用。解析失败返回 `None`。

### 4.2 `candidate_state.py` —— 候选态模型
- `CandidateState`：每格三态 `STAR / ELIMINATED / UNKNOWN`。
- 维护派生信息，供技巧 O(1) 查询：每个行/列/区域的「已放星数」「剩余 UNKNOWN 格集合」。
- 由 `region_grid + stars` 初始化（全 UNKNOWN）。
- `apply(deduction)`：把一个 `Deduction`（一批标记）应用到状态，更新派生信息；遇到矛盾（如某单元星数超限）时可标记为 invalid。
- `is_solved()`：所有单元恰好满足 stars 约束且无相邻星。

### 4.3 `deduction.py` —— 数据结构
- `Deduction`：`{technique_name: str, tier: int, marks: list[(r, c, new_state)], reason: str}`。
- `Step`：引擎应用一次 `Deduction` 后记录的一步。
- `Trace`：`{steps: list[Step], solved: bool, stuck_state: CandidateState | None}`。

### 4.4 `techniques/` —— 技巧库
统一接口：每个技巧是一个可调用对象/函数 `find(state) -> Deduction | None`，并带属性 `name` 与 `tier`。彼此独立、可单测。

第一批技巧（针对 1 星，每行/列/区域恰好 1 星）：

**T1 基础（tier 1）**
- `adjacency_elimination`：某格已为 STAR → 其 8 邻格标 ELIMINATED。
- `unit_complete`：某行/列/区域已放满 1 星 → 该单元其余 UNKNOWN 标 ELIMINATED。
- `last_cell`：某行/列/区域有 0 星且只剩 1 个 UNKNOWN → 该格必为 STAR。

**T2 几何 / 计数（tier 2）**
- `region_confined_to_line`：某区域所有 UNKNOWN 都落在同一行（或列）→ 该行（列）的星必在此区域 → 该行（列）中此区域之外的格标 ELIMINATED。
- `exclusion`：若在某格放星会导致某个区域/行/列无法再放下所需的星 → 该格标 ELIMINATED。
- `undercounting` / `overcounting`：n 个区域的全部 UNKNOWN 恰好落在 n 个行/列内（或对偶）→ 这 n 行/列的星全部锁定在这 n 个区域内 → 行/列内其余区域、或区域内其余行/列标 ELIMINATED。

> 技巧的 tier 顺序即"由易到难"，引擎据此优先选用，也是难度分的主轴。新增技巧只需实现接口并赋 tier，引擎与计分器无需改动。

### 4.5 `engine.py` —— 解题引擎
- 循环：按 tier 从低到高扫描技巧；用**第一个**能产出非空 `Deduction` 的技巧，`apply` 之，记录 `Step`，回到最低 tier 重新扫描。
- 终止：`state.is_solved()` → `solved=True`；或所有技巧都返回 `None`（卡死）→ `solved=False` 并保存 `stuck_state`。
- 输出 `Trace`。
- 不做猜测/回溯（那是更高 spec 的事）；卡死即表示"当前技巧库覆盖不到"。

### 4.6 `scorer.py` —— 计分器（方案 2）
- 输入 `Trace`，输出 `{tier_band: str, score: float}`。
- 主档：解出时由 `max(step.tier)` 决定大档（如最高 T1→Easy 区间、最高 T2→Medium 区间……tier 与档名的映射集中可配）。
- 档内细分（连续分）：由「高档技巧使用次数」「用到多少种不同的高档技巧」「总步数」按可调权重组合。
- 未解出（引擎卡死，需超出当前技巧库 / 需猜测）→ 归为最高档（Expert / Ambiguous）。
- 所有权重与 tier→档名映射集中在一处常量/配置，便于校准时调整。

### 4.7 `coverage.py` —— 技巧补全循环工具
- 批量跑一个目录下的谜题，分类：纯逻辑解出 / 卡死。
- 对卡死谜题，导出其 SBN + `stuck_state` 快照（可读的网格文本），供人工查看并命名缺失技巧。
- 这是"求解器驱动的技巧补全循环"的机器侧：机器精确指出"哪里缺技巧"，人负责命名并实现新技巧加入 `techniques/`，再重跑直至收敛。

### 4.8 `rate.py` —— CLI 入口
- `python rate.py <sbn 或文件>`：输出难度分 + 可读 trace。
- `--batch <dir>`：批量评分，输出汇总。
- `--calibrate`：对比人工标签（见第 5 节）。
- 遵循现有 Python 工具约定：`argparse`、无类型注解、标准库为主。

## 5. 校准

利用已有人工标注语料（`Main/puzzles/Files/` 下的 1 星文件，如 `8-1-ez.txt / 8-1-med.txt / 8-1-hard.txt`、`9-1-ez/med/hard.txt`）：
- 批量计算每个文件内谜题的分数分布。
- 调整 tier→档名映射与档内权重，使计算档位与人工标签尽量**单调对应**（ez < med < hard）。
- 验收标准：在 1 星语料上，计算档位与人工标签的排序基本一致（允许少量边界样本错档）。不追求逐题完美，只求单调与可解释。

## 6. 错误处理与边界

- SBN 解析失败：返回 `None`，批处理中跳过并计数。
- 非单一解 / 引擎卡死：不视为错误，标记为"超出当前技巧库"状态，交由 `coverage.py` 收集。
- 矛盾局面（理论上单一解谜题不应出现）：`CandidateState` 标记 invalid，记录并跳过。
- 本期仅保证 1 星正确；2 星可运行但技巧覆盖不足属预期。

## 7. 测试策略

- **技巧单测**：每个技巧手工构造最小局面，断言它**恰好**做出预期标记、且在不该触发时返回 `None`。
- **引擎测试**：取若干已知单一解的小尺寸 1 星题，断言能解出且解正确；用 `SBNBatchValidator.py` 的校验或 `Z3Solver.py` 交叉验证解的正确性与唯一性。
- **计分测试**：对几个已知难度的题，断言落入预期档。
- **校准测试**：在 1 星语料上断言档位排序单调（见第 5 节验收标准）。

## 8. 目录结构（建议）

```
MiscTools/difficulty/
  __init__.py
  sbn_codec.py
  candidate_state.py
  deduction.py
  engine.py
  scorer.py
  coverage.py
  rate.py
  techniques/
    __init__.py
    t1_basic.py
    t2_geometry.py
  tests/
    test_techniques.py
    test_engine.py
    test_scorer.py
```

## 9. 后续路线（超出本 spec）

1. 跑通补全循环，逐步补齐 1 星技巧库直至语料几乎全解。
2. 扩展 2 星及以上专属技巧。
3. 将技巧 trace 暴露给浏览器 UI，向玩家展示"这一步用了什么技巧"（届时需 JS 重实现或共享逻辑）。
4. 用难度能力支撑谜题生成 / 按目标难度筛选。
