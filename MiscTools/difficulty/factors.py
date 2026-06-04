"""区间内因子 → 复杂度 [0,1]。

把一步推理的结构因子（记录在 Deduction.meta 里）映射成 0~1 的复杂度：
最简单实例 = 0（落在规则区间下限），最难实例 = 1（落在上限）。
计分器据此算 value = lo + complexity × (hi - lo)。

归一化采用**固定上限 CAP=7**（不随棋盘尺寸变），保证难度跨棋盘可比：
norm(x) = clamp((x - lo_x) / (CAP - lo_x), 0, 1)
"""

CAP = 7


def _norm(x, lo=2):
    """把"数量/候选数/k/n"这类因子归一到 [0,1]，下限默认 2（最小有意义值）。"""
    if CAP <= lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / float(CAP - lo)))


def complexity(rule_id, meta):
    """返回该步在其规则区间内的复杂度 [0,1]。

    未定义因子的规则（如基础规则 1-5）返回 0.5（区间中点）——它们没有内部梯度，
    但仍通过各自不同的区间体现"区域比行列略难"等差异。
    """
    meta = meta or {}

    if rule_id == "region_confined":
        # 严格劈半：相连 → [0,0.5]，不相连 → [0.5,1]；数量在各半区内微调。
        contiguous = meta.get("contiguous", True)
        base = 0.0 if contiguous else 0.5
        return base + 0.5 * _norm(meta.get("count", 2))

    if rule_id == "exclusion":
        # 被威胁区域的候选数越多越难（候选都挤在公共邻格附近，跨度变化小，仅用数量）。
        return _norm(meta.get("candidate_count", 2))

    if rule_id in ("undercounting", "overcounting"):
        # k 越大越难；行/列默认相同，不影响。
        return _norm(meta.get("k", 2))

    if rule_id in ("fish", "finned_fish"):
        # 鱼规模 n 越大越难（带鳍鱼将来可叠加鳍项）。
        return _norm(meta.get("n", 2))

    # 其余（基础规则等）：无定义因子 → 取中点。
    return 0.5
