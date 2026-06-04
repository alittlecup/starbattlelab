"""技巧覆盖分析：批量找出当前技巧库解不动的谜题及其卡点快照。

用法：
    python3 coverage.py <puzzle_file.txt> [--max-stuck 20]
"""

import argparse
import sys

from sbn_codec import decode_to_grid
from candidate_state import CandidateState, UNKNOWN, STAR, ELIMINATED
from engine import solve
from techniques import ALL_TECHNIQUES

_GLYPH = {UNKNOWN: ".", STAR: "★", ELIMINATED: "x"}


def render_state(state):
    lines = []
    for r in range(state.dim):
        lines.append(" ".join(_GLYPH[state.grid[r][c]] for c in range(state.dim)))
    return "\n".join(lines)


def analyze_file(path, max_stuck=20):
    total = solved = stuck = unparsable = 0
    stuck_samples = []
    with open(path, "r") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            total += 1
            decoded = decode_to_grid(line)
            if decoded is None:
                unparsable += 1
                continue
            state = CandidateState(decoded["region_grid"], decoded["stars"])
            trace = solve(state, list(ALL_TECHNIQUES))
            if trace.solved:
                solved += 1
            else:
                stuck += 1
                if len(stuck_samples) < max_stuck:
                    stuck_samples.append({
                        "sbn": line,
                        "snapshot": render_state(trace.stuck_state),
                    })
    return {"total": total, "solved": solved, "stuck": stuck,
            "unparsable": unparsable, "stuck_samples": stuck_samples}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Star Battle 技巧覆盖分析")
    parser.add_argument("path", help="谜题文件（每行一个 SBN）")
    parser.add_argument("--max-stuck", type=int, default=20,
                        help="最多导出多少个卡点快照")
    args = parser.parse_args(argv)
    report = analyze_file(args.path, args.max_stuck)
    print("总计 {total}  解出 {solved}  卡死 {stuck}  无法解析 {unparsable}".format(**report))
    for i, sample in enumerate(report["stuck_samples"], 1):
        print("\n--- 卡点 #{} ---\n{}\n{}".format(i, sample["sbn"], sample["snapshot"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
