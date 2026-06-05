"""把某尺寸关卡补到目标总数（规范形去重）。后台跑用。

用法：
    python3 -m MiscTools.generator.gen_to_target --size 5 --target 10000
"""
import argparse
import os
import random

from .batch import run_size, _load_seen, ALL_STRATEGIES


def main(argv=None):
    p = argparse.ArgumentParser(description="补足某尺寸到目标总数")
    p.add_argument("--size", type=int, default=5)
    p.add_argument("--target", type=int, default=10000)
    p.add_argument("--stars", type=int, default=1)
    p.add_argument("--out-root", default="output")
    p.add_argument("--date", default="2026-06-05")
    p.add_argument("--cell", type=int, default=48)
    p.add_argument("--workers", type=int, default=0)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)

    workers = a.workers or os.cpu_count() or 1
    seed = a.seed or random.SystemRandom().randrange(2**31)
    size_dir = os.path.join(a.out_root, a.date, f"{a.size}x{a.size}")
    current = len(_load_seen(size_dir))
    need = a.target - current
    print(f"现有 {current} 个，目标 {a.target}，需新增 {need}", flush=True)
    if need <= 0:
        print("已达标。", flush=True)
        return
    # 余量足够大的尝试上限（5x5 布局池远大于 1 万，命中率约 16%）
    max_attempts = need * 50
    produced = run_size(a.size, a.stars, need, ALL_STRATEGIES, a.out_root, a.date,
                        max_attempts, workers, seed, a.cell)
    final = len(_load_seen(size_dir))
    print(f"新增 {produced}，当前总计 {final} / 目标 {a.target}", flush=True)


if __name__ == "__main__":
    main()
