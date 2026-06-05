# Generator 模块架构（面向后续 AGENT）

本文件给将来维护/扩展本模块的 AI agent 看，讲清楚**它怎么运转、为什么这么设计、坑在哪、怎么改**。
用户向文档见 `README.md`；设计决策见 `docs/superpowers/specs/2026-06-05-starbattle-puzzle-generator-design.md`。

---

## 1. 这个模块解决什么问题

批量生成**保证唯一解**的 Star Battle 谜题，按尺寸存成 SBN 文本；外加一个把 SBN 画成彩色区域 PNG 的独立工具。

在此之前，仓库**没有从零生成谜题的能力**——`Main/puzzles/Files/*.txt` 里的谜题是外部工具产出后导入的。本模块补上了这块。

## 2. 核心概念（先搞懂这些再动手）

- **Star Battle 规则**：N×N 网格切成 **N 个连通区域**，每行/列/区域恰好放 **k 颗星**，星星（含对角）互不相邻。
- **SBN (Star Battle Notation)**：紧凑字符串。格式 `{2位尺寸码}{星数}{flag}{区域边界数据}{可选标注}`。
  - 只编码**区域边界**，不编码区域 id。所以 `decode(encode(grid))` 得到的区域 id 会被按扫描顺序**重新编号**——
    **分区（哪些格子同组）不变，但 id 可能不同**。比较两个 grid 是否等价时要比分区，不要比 id。验证见 git 历史里的 roundtrip 测试思路。
  - 字母表 `0-9A-Za-z-_`（URL-safe），所以 SBN 可直接当文件名。
- **唯一解的稀缺性**：绝大多数随机区域划分要么无解要么多解。生成的本质是 **「大量产候选 → Z3 筛唯一解」**，大尺寸命中率很低（9×9 约 0.4%，更大更低）。这是设计内的代价，不是 bug。

## 3. 数据流

```
strategy.generate(size, stars, rng)  ->  region_grid (候选，不保证唯一解)
            |
   uniqueness.is_unique(grid, stars) ->  True/False   (Z3：解数==1)
            |  (仅 True 通过)
   sbn_codec.encode_sbn(grid, stars) ->  SBN 字符串
            |
   去重(本次运行 seen 集 + 已有文件)  ->  追加写 {size}-{stars}-unsorted.txt
```

并行：`generate.py` 用 `multiprocessing.Pool`，每个 worker 跑一次 `_attempt`（生成+校验）。
Z3 求解是瓶颈，所以并行收益主要在校验环节。

## 4. 关键设计：可插拔策略（最重要的扩展点）

`generate.py` **只依赖 `GenerationStrategy` 接口 + `uniqueness` + `sbn_codec`**，完全不知道用的是哪种生成算法。

```
strategies/base.py        GenerationStrategy.generate(size, stars, rng) -> region_grid | None
strategies/random_carve.py  策略 A：多源随机 BFS
strategies/__init__.py    STRATEGIES 注册表 + get_strategy(name)
```

### 加一个新策略（如「解先行」或「形状约束」）

1. 在 `strategies/` 新建文件，实现 `GenerationStrategy` 子类，`generate()` 返回 `size×size` 的
   region_grid（区域 id 1..size、连续、连通），无法产出时返回 `None`。
2. 在 `strategies/__init__.py` 的 `STRATEGIES` 字典注册。
3. 完事。`--strategy <name>` 即可用，pipeline、去重、写文件、渲染**一行都不用改**。

> ⚠️ worker 在 `multiprocessing`（macOS 默认 spawn）下会重新 import 模块，所以策略类必须是
> **模块级可导入**、`generate()` 的返回值是纯数据（list of list of int）。不要在策略里持有不可
> pickle 的状态。

### 已规划但未实现的策略（来自设计文档）

- **策略 B「解先行」**：先随机摆合法星阵当答案，再围着星切连通区域 → 命中率远高于随机划分。
- **形状约束策略**：把区域整体轮廓约束成心形等目标图案（用户最初的「可选形状」需求）。

## 5. 各文件职责速查

| 文件 | 职责 | 改动时注意 |
|---|---|---|
| `sbn_codec.py` | encode/decode + 常量 | encode 移植自 `LegacyImplementations/API-main/backend/puzzle_handler.py`，**改了要保证与现有文件格式一致**（水平边界逐列存储） |
| `strategies/base.py` | 抽象接口 | 改接口签名会波及所有策略 |
| `strategies/random_carve.py` | 策略 A | frontier 用 swap-pop 做 O(1) 随机取；返回 None 表示该次失败 |
| `uniqueness.py` | `is_unique()` | 复用 `MiscTools/Z3Solver.py` 的 `Z3StarBattleSolver.solve()`（最多返回 2 解）；静音了它的 print |
| `generate.py` | 生成 CLI + 并行 + 写文件 | 入口有 `if __name__=='__main__'` 守卫（spawn 必需）；按尺寸用不相交种子区间 |
| `render.py` | 渲染 CLI | 纯 Pillow，无浏览器；颜色用 HSV 均匀取色 |

## 6. 坑 / 注意事项

1. **z3 架构坑（重要）**：本机 arm64 但 `python3` 是 x86_64（Rosetta）。z3-solver **4.16.0.0 的 x86_64
   wheel 上游打包了 arm64 二进制**，`import z3` 会架构不匹配报错。解法：装 **4.13.0.0**：
   `python3 -m pip install --force-reinstall --no-deps z3-solver==4.13.0.0`。
   （根因是 python 解释器架构，换 arm64 原生 python 也可。）
2. **`Z3Solver.solve()` 会 print 计时**——批量场景很吵，`uniqueness._silenced()` 已重定向 stdout 屏蔽。
3. **`SBNBatchValidator.py` 会在 cwd 生成 `found_puzzles.txt`** 做去重缓存，跑完记得清理，别误提交。
4. **大尺寸慢且命中率低**：12-14、k=1 时随机策略可能跑很久。用 `--max-attempts` 兜底，或上策略 B。
5. **去重只做精确字符串匹配**，不做同构（旋转/镜像）去重。需要的话复用 `MiscTools/puzzle_variator.py`。

## 7. 如何验证改动没坏

- **编解码**：取一个真实 SBN，`decode -> encode` 应得回原串；`decode(encode(grid))` 的**分区**应与原 grid 相同。
- **唯一解**：生成几个谜题后，用项目自带独立验证器交叉复核（不同代码路径，最可信）：
  ```bash
  python3 MiscTools/SBNBatchValidator.py <生成的txt> --find-all   # 跑完删掉 found_puzzles.txt
  ```
- **策略**：检查输出 grid 区域数 == size、每区连通、覆盖全格。
- **渲染**：抽一张 PNG 肉眼看区域色 + 粗边框是否正确。
