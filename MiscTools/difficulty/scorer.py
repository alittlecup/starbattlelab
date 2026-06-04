"""难度计分器（配置驱动）。

难度由 difficulty-config.json 给出的"每条规则的区间 [lo,hi]"决定：
- 某一步的难度 = 其规则区间的中点（区间内因子尚未实现，先取中点作为代表值）；
- 一道谜题的难度 = 解题过程中**最难一步**的难度（聚合方式 a，详见 RULES.md §1.5）；
- 纯逻辑解不出 → Expert（难度轴顶端之上）。

配置由网页编辑器 tools/difficulty-editor.html 生成。
"""

import json
import os

# rule_id -> 类别（仅用于 band 名称展示）
RULE_CATEGORY = {
    "row_col_complete": "basic", "adjacency": "basic", "region_complete": "basic",
    "row_col_last": "basic", "region_last": "basic",
    "region_confined": "geo", "exclusion": "geo",
    "undercounting": "geo", "overcounting": "geo",
    "pressured_excl": "adv", "finned_counts": "adv", "set_diff": "adv",
    "fish": "adv", "finned_fish": "adv",
    "by_a_thread": "uniq", "at_sea": "uniq", "thread_at_sea": "uniq",
}
CATEGORY_BAND = {"basic": "Easy", "geo": "Medium", "adv": "Hard", "uniq": "VeryHard"}
UNSOLVED_BAND = "Expert"

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "difficulty-config.json")


def load_config(path=None):
    """读取难度配置。默认读模块同级的 difficulty-config.json。"""
    with open(path or DEFAULT_CONFIG_PATH, "r") as f:
        return json.load(f)


def _rule_value(config, rule_id):
    """规则在难度轴上的代表值 = 区间中点；未配置则返回 None。"""
    r = config.get("rules", {}).get(rule_id)
    if not r:
        return None
    return (r["lo"] + r["hi"]) / 2.0


def score_trace(trace, config):
    """对一条解题轨迹评分。

    返回 {band, score, hardest_rule, steps}。
    """
    max_dif = config.get("maxDifficulty", 1000)
    if not trace.solved:
        return {"band": UNSOLVED_BAND, "score": float(max_dif) + 1.0,
                "hardest_rule": None, "steps": len(trace.steps)}

    best_value = 0.0
    best_rule = None
    for s in trace.steps:
        rid = getattr(s, "rule_id", None) or s.technique_name
        v = _rule_value(config, rid)
        if v is not None and v >= best_value:
            best_value = v
            best_rule = rid

    cat = RULE_CATEGORY.get(best_rule, "geo")
    return {"band": CATEGORY_BAND.get(cat, "Medium"), "score": best_value,
            "hardest_rule": best_rule, "steps": len(trace.steps)}
