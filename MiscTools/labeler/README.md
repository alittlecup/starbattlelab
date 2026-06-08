# Star Battle 谜题预览 / 难度标注工具

在网页上预览已生成的谜题、查看算法实时计算的难度分，并手动游玩打分、做标记，
用于校准难度指标（feature/difficulty-metric）。

## 启动

```bash
python3 MiscTools/labeler/server.py            # 默认端口 8765
# 或指定端口： python3 MiscTools/labeler/server.py --port 9000
```

然后浏览器打开 <http://localhost:8765/MiscTools/labeler/>

> 需要本地服务的原因：难度分由现有 Python 难度引擎（`MiscTools/difficulty`）
> 在运行时对当前谜题实时计算；SBN 也由权威 Python codec 解码（兼容 4–10 全尺寸）。

## 功能

- **尺寸选择 4–12**：自动检测 `output/` 下已生成的尺寸，未生成的（如 11/12）置灰。
- **可交互摆星**：单击格子 = ✕排除，双击 = ★星，右键也可直接放/取星。
  实时校验行/列/区星数与相邻规则，**解对后自动保存并随机进入下一题**。
- **算法难度分**：右侧实时显示当前谜题的 分数 / 档位 / 最难规则 / 解法 / 步数。
- **我的预期分数**：手动输入，或点 Easy/Medium/Hard/Expert 快捷填入。
- **标记**：收藏 / 特殊形状 / 丢弃（丢弃后短暂延时即跳下一题）。
- **数据**：标注存浏览器 localStorage，可一键导出 JSON / CSV，或导入合并。

## 键盘快捷键

| 键 | 作用 |
|----|------|
| `n` / `Enter` | 保存并下一题 |
| `s` | 跳过（不保存） |
| `f` | 收藏 |
| `x` | 特殊形状 |
| `d` | 丢弃 |

## 导出字段（CSV）

`sbn, size, stars, expectedScore, algoScore, algoBand, favorite, special, discard, ts`

其中 `algoScore` / `algoBand` 记录标注当时算法给出的分数与档位，便于离线对比校准。
