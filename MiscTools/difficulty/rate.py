"""CLI：对单个 SBN 谜题计算难度。

用法：
    python3 rate.py <sbn>
"""

import argparse
import sys

from sbn_codec import decode_to_grid
from candidate_state import CandidateState
from engine import solve
from scorer import score_trace
from techniques import ALL_TECHNIQUES


def analyze(sbn):
    """解码并评分单个 SBN。失败返回 None。"""
    decoded = decode_to_grid(sbn)
    if decoded is None:
        return None
    state = CandidateState(decoded["region_grid"], decoded["stars"])
    trace = solve(state, list(ALL_TECHNIQUES))
    scored = score_trace(trace)
    return {
        "sbn": sbn,
        "dim": decoded["dim"],
        "stars": decoded["stars"],
        "solved": trace.solved,
        "band": scored["band"],
        "score": scored["score"],
        "steps": len(trace.steps),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="计算 Star Battle 谜题难度")
    parser.add_argument("sbn", help="SBN 谜题字符串")
    args = parser.parse_args(argv)
    result = analyze(args.sbn)
    if result is None:
        print("无法解析该 SBN", file=sys.stderr)
        return 1
    print("维度: {dim}x{dim}  星: {stars}".format(**result))
    print("解出: {}  档位: {}  分数: {:.2f}  步数: {}".format(
        result["solved"], result["band"], result["score"], result["steps"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
