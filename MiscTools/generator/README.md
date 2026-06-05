# Star Battle 谜题生成器 + SBN 渲染工具

批量、大范围生成保证**唯一解**的 Star Battle 谜题，并提供独立的 SBN → 彩色区域图片渲染工具。

设计文档：`docs/superpowers/specs/2026-06-05-starbattle-puzzle-generator-design.md`

## 安装依赖

```bash
python3 -m pip install z3-solver tqdm Pillow
```

> ⚠️ Apple Silicon + x86_64 Python（Rosetta）环境注意：z3-solver 4.16.0.0 的 x86_64
> wheel 打包了错误的 arm64 二进制。若 `import z3` 报架构不匹配，改装 4.13.0.0：
> `python3 -m pip install --force-reinstall --no-deps z3-solver==4.13.0.0`

## 生成谜题

```bash
# 尺寸 4-14，每个尺寸生成 50 个唯一解谜题
python3 -m MiscTools.generator.generate --sizes 4-14 --count 50

# 只生成 9x9，限定尝试次数与并行数，固定随机种子复现
python3 -m MiscTools.generator.generate --sizes 9 --count 20 --workers 8 --seed 123
```

参数：

| 参数 | 说明 | 默认 |
|---|---|---|
| `--sizes` | 尺寸，`4-14` / `9` / `8,10,12` | `4-14` |
| `--count` | 每尺寸目标数量 | `20` |
| `--stars` | 每区星数 k | `1` |
| `--strategy` | 生成策略 | `random` |
| `--out-dir` | 输出目录 | `Main/puzzles/Files` |
| `--max-attempts` | 每尺寸最大尝试，0=自动(count×5000) | `0` |
| `--workers` | 并行进程数，0=CPU 核数 | `0` |
| `--seed` | 随机基种子，0=系统随机 | `0` |

输出：按尺寸追加写入 `{size}-{stars}-unsorted.txt`，每行一个 SBN，自动跨运行去重。

> 注：随机划分（策略 A）在大尺寸（≥12, k=1）命中率很低，靠数量堆。后续可加
> 「解先行」策略提升命中率（见设计文档「未来扩展」）。

## 渲染截图

```bash
# 渲染单个 SBN
python3 -m MiscTools.generator.render --input 991WiSHUFrpQihv1246rWa46ZT1X --out out/png

# 渲染整个文件 / 目录
python3 -m MiscTools.generator.render --input Main/puzzles/Files/9-1-unsorted.txt --out out/png
python3 -m MiscTools.generator.render --input Main/puzzles/Files --out out/png
```

输出：每个谜题一张 `{SBN}.png`，区域上不同颜色、粗线画区域边界。

## 模块结构

```
generator/
├── sbn_codec.py        # 共享 codec：encode_sbn / decode_sbn + SBN 常量
├── strategies/
│   ├── base.py         # GenerationStrategy 抽象接口
│   └── random_carve.py # 策略 A：多源随机 BFS 区域划分
├── uniqueness.py       # is_unique()：封装 Z3 求解器
├── generate.py         # 生成 CLI 主入口
└── render.py           # 渲染 CLI 工具
```

## 扩展生成策略

1. 在 `strategies/` 新增实现 `GenerationStrategy` 的类；
2. 在 `strategies/__init__.py` 的 `STRATEGIES` 注册；
3. `--strategy <name>` 即可使用。pipeline 其余部分无需改动。
