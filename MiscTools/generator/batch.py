"""一键编排：批量生成 → 唯一解验证 → 彩色图片，按 日期/尺寸 归档。

每个尺寸输出到独立目录：
    {out-root}/{YYYY-MM-DD}/{size}x{size}/
        ├── puzzles.txt        # 该尺寸全部 SBN（每行一个）
        └── {SBN}.png          # 每个谜题对应的彩色区域图片

唯一解由生成阶段保证（only 解数==1 的候选才会被收下）。

用法：
    python3 -m MiscTools.generator.batch --sizes 5-9 --count 10
    python3 -m MiscTools.generator.batch --sizes 7 --count 20 --out-root output --workers 8
"""

import argparse
import datetime
import os
import random

from .generate import generate_unique, parse_sizes
from .render import render_sbn
from .sbn_codec import DIM_TO_SBN_CODE_MAP
from .strategies import STRATEGIES


def run_size(size, stars, count, strategy_name, out_root, date_str,
             max_attempts, workers, base_seed, cell):
    """生成单个尺寸并写入归档目录，返回实际产出数量。"""
    if size not in DIM_TO_SBN_CODE_MAP:
        print(f"[skip] size {size} 不在 SBN 支持范围 (5-25)")
        return 0

    size_dir = os.path.join(out_root, date_str, f"{size}x{size}")
    os.makedirs(size_dir, exist_ok=True)
    txt_path = os.path.join(size_dir, "puzzles.txt")
    # 跨运行去重：把同目录已有 puzzles.txt 读进 seen。
    seen = set()
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            seen = {ln.strip() for ln in f if ln.strip()}

    print(f"[{size}x{size} k={stars}] 目标 {count}，已有 {len(seen)} -> {size_dir}")
    out = open(txt_path, "a", encoding="utf-8")
    try:
        def _persist(sbn):
            out.write(sbn + "\n")
            out.flush()
            render_sbn(sbn, size_dir, cell=cell)  # 谜题与图片同目录
        results, attempts = generate_unique(
            size, stars, count, strategy_name, max_attempts,
            workers, base_seed, seen=seen, on_found=_persist,
        )
    finally:
        out.close()

    rate = (len(results) / attempts * 100) if attempts else 0
    print(f"[{size}x{size} k={stars}] 产出 {len(results)} 个（含图片），"
          f"尝试 {attempts}，命中率 {rate:.2f}%")
    return len(results)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Star Battle 批量生成 + 验证 + 可视化（按日期/尺寸归档）")
    parser.add_argument("--sizes", default="5-9",
                        help="尺寸，如 '5-9' / '7' / '6,8,10'（默认 5-9）")
    parser.add_argument("--count", type=int, default=10,
                        help="每个尺寸目标数量（默认 10）")
    parser.add_argument("--stars", type=int, default=1, help="每区星数 k（默认 1）")
    parser.add_argument("--strategy", default="random", choices=sorted(STRATEGIES),
                        help="生成策略（默认 random）")
    parser.add_argument("--out-root", default="output",
                        help="归档根目录（默认 ./output）")
    parser.add_argument("--date", default="",
                        help="日期子目录名，默认今天 YYYY-MM-DD")
    parser.add_argument("--cell", type=int, default=48, help="图片每格像素（默认 48）")
    parser.add_argument("--max-attempts", type=int, default=0,
                        help="每尺寸最大尝试；0=自动(count*5000)")
    parser.add_argument("--workers", type=int, default=0, help="并行进程数；0=CPU 核数")
    parser.add_argument("--seed", type=int, default=0, help="随机基种子；0=系统随机")
    args = parser.parse_args(argv)

    workers = args.workers or os.cpu_count() or 1
    base_seed = args.seed or random.SystemRandom().randrange(2**31)
    date_str = args.date or datetime.date.today().isoformat()
    sizes = parse_sizes(args.sizes)

    total = 0
    for size in sizes:
        max_attempts = args.max_attempts or args.count * 5000
        total += run_size(size, args.stars, args.count, args.strategy,
                          args.out_root, date_str, max_attempts, workers,
                          base_seed, args.cell)
        base_seed += max_attempts
    print(f"完成：共产出 {total} 个谜题 -> {os.path.join(args.out_root, date_str)}")


if __name__ == "__main__":
    main()
