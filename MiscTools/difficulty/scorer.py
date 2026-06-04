"""难度计分器（方案 2）。所有权重集中于此，便于校准。"""

TIER_TO_BAND = {0: "Trivial", 1: "Easy", 2: "Medium"}
UNSOLVED_BAND = "Expert"

W_HIGH_STEP_COUNT = 1.0     # 每个最高档步数
W_DISTINCT_HIGH = 5.0       # 每种不同的最高档技巧
W_TOTAL_STEPS = 0.1         # 每个总步数
UNSOLVED_BASE = 1000.0      # 未解出基线分（高于任何已解出分）
BAND_BASE = 100.0           # 每提升一档的基础分


def score_trace(trace):
    if not trace.solved:
        return {"band": UNSOLVED_BAND,
                "score": UNSOLVED_BASE + W_TOTAL_STEPS * len(trace.steps)}

    max_tier = max((s.tier for s in trace.steps), default=0)
    band = TIER_TO_BAND.get(max_tier, "Medium")
    high_steps = [s for s in trace.steps if s.tier == max_tier]
    distinct_high = len({s.technique_name for s in high_steps})

    score = (BAND_BASE * max_tier
             + W_HIGH_STEP_COUNT * len(high_steps)
             + W_DISTINCT_HIGH * distinct_high
             + W_TOTAL_STEPS * len(trace.steps))
    return {"band": band, "score": score, "max_tier": max_tier,
            "steps": len(trace.steps)}
