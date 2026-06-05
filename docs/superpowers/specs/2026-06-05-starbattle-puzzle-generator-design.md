# Star Battle 批量谜题生成器 + SBN 渲染工具 — 设计文档

- 日期：2026-06-05
- 分支：feature/difficulty-metric（后续可新开分支）
- 状态：已与用户确认，待实现

## 1. 目标

批量、大范围生成 Star Battle 谜题，保证每个谜题**唯一解**，按尺寸保存到本地 SBN 文本文件；
另提供一个独立的渲染工具，把任意 SBN 谜题画成彩色区域图片、按 SBN 命名保存。

## 2. 范围与决策（已确认）

| 项 | 决策 |
|---|---|
| 尺寸范围 | 4×4 ~ 14×14 |
| 每区星数 k | 当前所有尺寸默认 **k=1**；保留 `--stars` 参数供后续扩展 |
| 生成策略 | **思路 A：随机划分 → Z3 筛唯一解**；策略可插拔，后续可加思路 B / 形状约束 |
| 形状约束（心形等） | 本期**不做**；作为未来的一种生成策略接入，不影响 pipeline |
| 唯一解校验 | 复用 `MiscTools/Z3Solver.py` 的 `Z3StarBattleSolver.solve()`（最多返回 2 解，`len==1` 即唯一）|
| SBN 输出存储 | 沿用现有 `Main/puzzles/Files/{size}-{k}-unsorted.txt`，每行一个 SBN，追加写、去重 |
| 难度分类 | 本期不做，交给现有 `MiscTools/difficulty/` 工具后续独立跑 |
| 渲染工具 | **独立按需运行**；纯 Python（Pillow）；输入 SBN/文件，输出 `{SBN}.png` |

## 3. 架构

```
MiscTools/generator/
├── sbn_codec.py        # 共享 codec：decode（复用 difficulty 逻辑）+ 新增 encode（从 Legacy 移植）+ SBN 常量表
├── strategies/
│   ├── base.py         # GenerationStrategy 抽象接口（可插拔关键点）
│   └── random_carve.py # 思路 A：多源随机 BFS 区域划分
├── uniqueness.py       # 封装 Z3：is_unique(region_grid, stars) -> bool
├── generate.py         # CLI 主入口：生成 → 校验唯一 → 去重 → 按尺寸写文件
└── render.py           # CLI 独立工具：SBN → Pillow 彩色区域 PNG
```

**核心解耦**：`generate.py` 只依赖 `GenerationStrategy` 接口与 `uniqueness`/`sbn_codec`，
与具体生成算法无关。换策略 = 传 `--strategy random`。

## 4. 关键接口

```python
# strategies/base.py
class GenerationStrategy(ABC):
    @abstractmethod
    def generate(self, size: int, stars: int, rng) -> list[list[int]]:
        """返回一个 size×size 的 region_grid（N 个连通区域，区域 id 从 1 起）。
        只负责产出候选区域划分，不保证唯一解。"""

# strategies/random_carve.py — 思路 A
#   1. 在网格上撒 size 个种子点（每个未来区域一个）
#   2. 多源随机 BFS：每轮从某个区域的边界随机吃一个相邻空格，直到铺满
#   3. 保证每个区域连通、N 个区域覆盖全部格子

# uniqueness.py
def is_unique(region_grid, stars) -> bool:
    solutions, _ = Z3StarBattleSolver(region_grid, stars).solve()
    return len(solutions) == 1

# sbn_codec.py
def encode_sbn(region_grid, stars) -> str   # 移植 encode_to_sbn
def decode_sbn(sbn) -> dict                  # {region_grid, stars, dim}
```

## 5. 数据流（generate.py）

```
for size in 请求的尺寸列表:
    seen = 读取已有 {size}-{k}-unsorted.txt 的 SBN 集合（去重）
    while 未达目标数量 and 未超尝试/时间预算:
        region_grid = strategy.generate(size, stars, rng)
        if not is_unique(region_grid, stars): continue
        sbn = encode_sbn(region_grid, stars)
        if sbn in seen: continue
        seen.add(sbn); 追加写入文件
    打印该尺寸命中率/产出数
```

- 用 `multiprocessing` 并行候选生成+校验（参考 `SBNBatchValidator.py` 的并行模式）。
- 抑制 `Z3Solver` 内部的 print 噪声（批量场景）。

## 6. 渲染工具（render.py）

```
输入：单个 SBN，或含多行 SBN 的文件/目录；--out 输出目录
流程：decode_sbn → region_grid → Pillow 画布
      - 每个区域 id 映射一个区分度高的颜色（调色板循环）
      - 细线画格子，粗线画区域边界
      - 保存为 {SBN}.png（SBN 字母表 0-9A-Za-z-_，文件名安全）
依赖：Pillow
```

## 7. CLI 示例

```bash
# 生成：尺寸 4-14，每尺寸目标 50 个唯一解谜题
python -m MiscTools.generator.generate --sizes 4-14 --count 50 --stars 1

# 渲染：把一个文件里的所有 SBN 画成 PNG
python -m MiscTools.generator.render --input Main/puzzles/Files/9-1-unsorted.txt --out out/png
```

## 8. 未来扩展（本期不做）

- 思路 B（解先行→围星切区域）提升大尺寸命中率
- 形状约束生成策略（心形等目标轮廓）
- 难度自动分类写入 `{size}-{k}-{难度}.txt`
- 同构去重（复用 `puzzle_variator.py`）

## 9. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 大尺寸（12-14, k=1）命中率低 | 尝试/时间预算 + 并行 + 命中率日志；未来上思路 B |
| Z3 求解慢 | 并行；MVP 后台跑可接受 |
| SBN 格式不兼容现有文件 | 移植同一套 `encode_to_sbn` + 常量表，已核对 |
