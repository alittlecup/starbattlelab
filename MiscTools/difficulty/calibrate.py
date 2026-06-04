"""校准报告：在已标注语料上汇总解出率/平均分/档位分布。

用法：
    python3 calibrate.py Main/puzzles/Files/8-1-ez.txt Main/puzzles/Files/8-1-med.txt ...
"""

import argparse
import sys

from rate import analyze


def summarize_file(path):
    count = solved = 0
    score_sum = 0.0
    band_dist = {}
    with open(path, "r") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            result = analyze(line)
            if result is None:
                continue
            count += 1
            if result["solved"]:
                solved += 1
            score_sum += result["score"]
            band_dist[result["band"]] = band_dist.get(result["band"], 0) + 1
    return {
        "path": path,
        "count": count,
        "solved_rate": (solved / count) if count else 0.0,
        "avg_score": (score_sum / count) if count else 0.0,
        "band_distribution": band_dist,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Star Battle 难度校准报告")
    parser.add_argument("files", nargs="+", help="一个或多个谜题文件")
    args = parser.parse_args(argv)
    for path in args.files:
        s = summarize_file(path)
        print("{path}: 共 {count}  解出率 {solved_rate:.0%}  平均分 {avg_score:.1f}  分布 {band_distribution}".format(**s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
