"""CLI：对单个 SBN 谜题计算难度。

用法：
    python3 rate.py <sbn> [--config path]
"""

import argparse
import sys

from sbn_codec import decode_to_grid
from candidate_state import CandidateState
from engine import solve
from scorer import score_trace, load_config
from techniques import ALL_TECHNIQUES
from deduction import Step
from search_solver import solve_complete


def analyze(sbn, config=None):
    """解码并评分单个 SBN。失败返回 None。

    config：难度配置 dict；为 None 时读取默认配置文件。
    流程：命名技巧引擎解 → 解出则按区间评分；解不动则用搜索兜底确认唯一性并按
    guessing 规则评分（lo + 搜索量加成）。
    """
    if config is None:
        config = load_config()
    decoded = decode_to_grid(sbn)
    if decoded is None:
        return None
    state = CandidateState(decoded["region_grid"], decoded["stars"])
    trace = solve(state, list(ALL_TECHNIQUES))

    solved_via = "logic"
    n_solutions = 1
    if not trace.solved:
        fresh = CandidateState(decoded["region_grid"], decoded["stars"])
        res = solve_complete(fresh, max_solutions=2)
        n_solutions = len(res["solutions"])
        solved_via = "search"
        if n_solutions == 1:
            trace.steps.append(Step("guessing", 18, [], "搜索兜底（试错）",
                                    rule_id="guessing",
                                    meta={"guesses": res["guesses"], "depth": res["depth"]}))
            trace.solved = True

    if trace.solved:
        scored = score_trace(trace, config)
        band, score, hardest = scored["band"], scored["score"], scored["hardest_rule"]
    else:
        # 搜索仍未给出唯一解：标记异常
        band = "Ambiguous" if n_solutions >= 2 else "Broken"
        score = float(config.get("maxDifficulty", 1000)) * 2
        hardest = band.lower()

    return {
        "sbn": sbn,
        "dim": decoded["dim"],
        "stars": decoded["stars"],
        "solved": trace.solved,
        "solved_via": solved_via,
        "n_solutions": n_solutions,
        "band": band,
        "score": score,
        "hardest_rule": hardest,
        "steps": len(trace.steps),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="计算 Star Battle 谜题难度")
    parser.add_argument("sbn", help="SBN 谜题字符串")
    parser.add_argument("--config", help="难度配置 JSON 路径（默认 difficulty-config.json）")
    args = parser.parse_args(argv)
    config = load_config(args.config) if args.config else load_config()
    result = analyze(args.sbn, config)
    if result is None:
        print("无法解析该 SBN", file=sys.stderr)
        return 1
    print("维度: {dim}x{dim}  星: {stars}".format(**result))
    print("解出: {}  档位: {}  分数: {:.1f}  最难规则: {}  步数: {}".format(
        result["solved"], result["band"], result["score"],
        result["hardest_rule"], result["steps"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
