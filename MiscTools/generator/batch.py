"""一键编排：批量生成 → 唯一解验证 → 彩色图片，按 日期/尺寸/类目 归档。

输出结构：
    {out-root}/{YYYY-MM-DD}/{size}x{size}/{category}/
        ├── puzzles.txt        # 该类目全部 SBN
        └── {SBN}.png          # 每题彩色图片
    {out-root}/{YYYY-MM-DD}/{size}x{size}/manifest.csv   # SBN/类目/对称/大小分布 一览

特性：
- 规范形去重：旋转/镜像/改号视为同一形状，保证形状尽量多样。
- 类目归档：对称布局(symmetric-*)、楼梯(staircase)、大小递进(progressive) 等分目录。
- 多策略混合：--strategy all 轮转 random/progressive/staircase，最大化多样性。

用法：
    python3 -m MiscTools.generator.batch --sizes 7 --count 20 --strategy all
    python3 -m MiscTools.generator.batch --sizes 5-9 --count 10 --strategy progressive
"""

import argparse
import csv
import datetime
import glob
import os
import random

from .canonical import canonical_key
from .classify import category as geom_category, detect_symmetry, size_profile
from .generate import generate_unique, parse_sizes
from .render import render_sbn
from .sbn_codec import decode_sbn, DIM_TO_SBN_CODE_MAP
from .strategies import STRATEGIES

STRUCTURED = ('progressive',)
ALL_STRATEGIES = ['random', 'progressive']


def folder_category(grid, strategy_name):
    """归档类目：对称布局最优先，其次生成它的结构化策略名，最后按几何大小分布。"""
    if detect_symmetry(grid):
        return geom_category(grid)            # symmetric-rot90 / -rot180 / -mirror
    if strategy_name in STRUCTURED:
        return strategy_name                  # staircase / progressive
    label = size_profile(grid)[1]             # uniform / progressive / distinct / mixed
    return label if label in ('uniform', 'progressive', 'distinct') else 'plain'


def _load_seen(size_dir):
    """从该尺寸目录下所有 category/puzzles.txt 重建规范形去重集合。"""
    seen = set()
    for txt in glob.glob(os.path.join(size_dir, "*", "puzzles.txt")):
        with open(txt, encoding="utf-8") as f:
            for line in f:
                sbn = line.strip()
                d = decode_sbn(sbn) if sbn else None
                if d:
                    seen.add(canonical_key(d["region_grid"]))
    return seen


def run_size(size, stars, count, strategies, out_root, date_str,
             max_attempts, workers, base_seed, cell):
    """生成单个尺寸，按类目归档，写 manifest，返回产出数量。"""
    if size not in DIM_TO_SBN_CODE_MAP:
        print(f"[skip] size {size} 不在支持范围 (4-14)")
        return 0

    size_dir = os.path.join(out_root, date_str, f"{size}x{size}")
    os.makedirs(size_dir, exist_ok=True)
    seen = _load_seen(size_dir)
    manifest_rows = []
    open_files = {}

    def _persist(sbn, strat):
        d = decode_sbn(sbn)
        grid = d["region_grid"]
        cat = folder_category(grid, strat)
        cat_dir = os.path.join(size_dir, cat)
        if cat not in open_files:
            os.makedirs(cat_dir, exist_ok=True)
            open_files[cat] = open(os.path.join(cat_dir, "puzzles.txt"), "a", encoding="utf-8")
        open_files[cat].write(sbn + "\n")
        open_files[cat].flush()
        render_sbn(sbn, cat_dir, cell=cell)
        syms = detect_symmetry(grid)
        sizes, profile = size_profile(grid)
        manifest_rows.append({
            "sbn": sbn, "size": size, "category": cat,
            "symmetry": "|".join(syms) if syms else "none",
            "size_profile": profile, "sizes": " ".join(map(str, sizes)),
        })

    print(f"[{size}x{size} k={stars}] 目标 {count}，已有 {len(seen)}，"
          f"策略={'+'.join(strategies)} -> {size_dir}")
    try:
        results, attempts = generate_unique(
            size, stars, count, strategies, max_attempts, workers, base_seed,
            seen=seen, on_found=_persist, key_fn=lambda s: canonical_key(decode_sbn(s)["region_grid"]),
        )
    finally:
        for f in open_files.values():
            f.close()

    # 写/追加 manifest.csv
    if manifest_rows:
        mpath = os.path.join(size_dir, "manifest.csv")
        new = not os.path.exists(mpath)
        with open(mpath, "a", newline="", encoding="utf-8") as mf:
            w = csv.DictWriter(mf, fieldnames=["sbn", "size", "category",
                                               "symmetry", "size_profile", "sizes"])
            if new:
                w.writeheader()
            w.writerows(manifest_rows)

    from collections import Counter
    by_cat = Counter(r["category"] for r in manifest_rows)
    rate = (len(results) / attempts * 100) if attempts else 0
    print(f"[{size}x{size} k={stars}] 产出 {len(results)} 个，尝试 {attempts}，"
          f"命中率 {rate:.2f}%，类目分布 {dict(by_cat)}")
    return len(results)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Star Battle 批量生成 + 验证 + 可视化（按日期/尺寸/类目归档）")
    parser.add_argument("--sizes", default="5-9", help="尺寸，如 '5-9'/'7'/'6,8'（默认 5-9）")
    parser.add_argument("--count", type=int, default=10, help="每个尺寸目标数量（默认 10）")
    parser.add_argument("--stars", type=int, default=1, help="每区星数 k（默认 1）")
    parser.add_argument("--strategy", default="all",
                        choices=sorted(STRATEGIES) + ["all"],
                        help="生成策略，all=混合 random/progressive/staircase（默认 all）")
    parser.add_argument("--out-root", default="output", help="归档根目录（默认 ./output）")
    parser.add_argument("--date", default="", help="日期子目录名，默认今天 YYYY-MM-DD")
    parser.add_argument("--cell", type=int, default=48, help="图片每格像素（默认 48）")
    parser.add_argument("--max-attempts", type=int, default=0, help="每尺寸最大尝试；0=自动(count*5000)")
    parser.add_argument("--workers", type=int, default=0, help="并行进程数；0=CPU 核数")
    parser.add_argument("--seed", type=int, default=0, help="随机基种子；0=系统随机")
    args = parser.parse_args(argv)

    workers = args.workers or os.cpu_count() or 1
    base_seed = args.seed or random.SystemRandom().randrange(2**31)
    date_str = args.date or datetime.date.today().isoformat()
    strategies = ALL_STRATEGIES if args.strategy == "all" else [args.strategy]
    sizes = parse_sizes(args.sizes)

    total = 0
    for size in sizes:
        max_attempts = args.max_attempts or args.count * 5000
        total += run_size(size, args.stars, args.count, strategies, args.out_root,
                          date_str, max_attempts, workers, base_seed, args.cell)
        base_seed += max_attempts
    print(f"完成：共产出 {total} 个谜题 -> {os.path.join(args.out_root, date_str)}")


if __name__ == "__main__":
    main()
