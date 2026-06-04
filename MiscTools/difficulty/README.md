# Star Battle 难度计算（离线，Python）

对 1 星 Star Battle 谜题做"带技巧标注的逻辑解题"，产出逐步轨迹并计算难度分。

> 📖 **完整的架构与实现说明见 [`ARCHITECTURE.md`](./ARCHITECTURE.md)** —— 设计动机、数据模型、每个技巧的推理逻辑、引擎/计分算法、校准结果、范围与后续路线、如何新增技巧。后续接手者请先读它。

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
