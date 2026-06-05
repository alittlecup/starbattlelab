"""批量谜题生成主入口（CLI）。

数据流（每个尺寸）：
    候选生成(策略) -> 唯一解校验(Z3) -> 去重(本次运行内 + 已有文件) -> 追加写 {size}-{stars}-unsorted.txt

并行：用 multiprocessing 把「生成+校验」分发到多进程（Z3 求解是瓶颈）。
可插拔：--strategy 选择生成策略，pipeline 与具体算法解耦。

用法：
    python -m MiscTools.generator.generate --sizes 4-14 --count 50
    python -m MiscTools.generator.generate --sizes 9 --count 20 --workers 4 --seed 123
"""

import argparse
import multiprocessing as mp
import os
import random
import sys
import time

from .sbn_codec import encode_sbn, DIM_TO_SBN_CODE_MAP
from .strategies import get_strategy, STRATEGIES
from .uniqueness import is_unique

DEFAULT_OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Main", "puzzles", "Files",
)


def _attempt(task):
    """单次尝试：生成候选 -> 校验唯一 -> 返回 (SBN, 策略名) 或 None。供 worker 进程调用。"""
    size, stars, strategy_name, seed = task
    rng = random.Random(seed)
    strategy = get_strategy(strategy_name)
    grid = strategy.generate(size, stars, rng)
    if grid is None:
        return None
    if not is_unique(grid, stars):
        return None
    return encode_sbn(grid, stars), strategy_name


def parse_sizes(spec):
    """解析 '4-14' / '9' / '8,10,12' 为去重排序的尺寸列表。"""
    sizes = set()
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            lo, hi = part.split('-')
            sizes.update(range(int(lo), int(hi) + 1))
        elif part:
            sizes.add(int(part))
    return sorted(sizes)


def load_existing(path):
    """读取已有文件中的 SBN 集合（用于跨运行去重）。"""
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def generate_unique(size, stars, count, strategy, max_attempts,
                    workers, base_seed, seen=None, on_found=None, key_fn=None):
    """为单个尺寸生成至多 count 个唯一解谜题，返回新 SBN 列表。

    纯生成核心，不做文件 I/O —— 调用方负责持久化（generate.py 写 txt，
    batch.py 写归档目录 + 渲染）。

    :param strategy: 策略名(str) 或 策略名列表(list)。给列表时按任务轮转，混合多策略。
    :param set seen: 已知去重键集合（跨运行去重），会被原地更新。
    :param callable on_found: 每产出一个新 SBN 时回调 on_found(sbn)。
    :param callable key_fn: SBN -> 去重键。默认按 SBN 串去重；batch 传入规范形去重。
    :returns: (新增 SBN 列表, 尝试次数)
    """
    seen = seen if seen is not None else set()
    key_fn = key_fn or (lambda sbn: sbn)
    strategies = [strategy] if isinstance(strategy, str) else list(strategy)
    results = []
    attempts = 0
    pool = mp.Pool(processes=workers)
    try:
        seed_counter = base_seed
        while len(results) < count and attempts < max_attempts:
            batch = min(workers * 8, max_attempts - attempts)
            tasks = [(size, stars, strategies[(seed_counter + i) % len(strategies)],
                      seed_counter + i) for i in range(batch)]
            seed_counter += batch
            attempts += batch
            for res in pool.imap_unordered(_attempt, tasks):
                if not res:
                    continue
                sbn, strat = res
                key = key_fn(sbn)
                if key not in seen:
                    seen.add(key)
                    results.append(sbn)
                    if on_found:
                        on_found(sbn, strat)
                    if len(results) >= count:
                        break
    finally:
        pool.terminate()
        pool.join()
    return results, attempts


def generate_for_size(size, stars, count, strategy_name, out_dir,
                      max_attempts, workers, base_seed):
    """为单个尺寸生成 count 个唯一解谜题，增量追加写入 {size}-{stars}-unsorted.txt。"""
    if size not in DIM_TO_SBN_CODE_MAP:
        print(f"[skip] size {size} 不在支持范围 (4-14)", file=sys.stderr)
        return 0

    path = os.path.join(out_dir, f"{size}-{stars}-unsorted.txt")
    seen = load_existing(path)
    start = time.monotonic()
    print(f"[{size}x{size} k={stars}] 目标 {count}，已有 {len(seen)}，"
          f"策略={strategy_name}，workers={workers}")

    os.makedirs(out_dir, exist_ok=True)
    out = open(path, "a", encoding="utf-8")
    try:
        def _write(sbn, strat):
            out.write(sbn + "\n")
            out.flush()
        results, attempts = generate_unique(
            size, stars, count, strategy_name, max_attempts,
            workers, base_seed, seen=seen, on_found=_write,
        )
    finally:
        out.close()

    elapsed = time.monotonic() - start
    rate = (len(results) / attempts * 100) if attempts else 0
    print(f"[{size}x{size} k={stars}] 新增 {len(results)} 个，尝试 {attempts} 次，"
          f"命中率 {rate:.2f}%，耗时 {elapsed:.1f}s -> {path}")
    return len(results)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Star Battle 批量谜题生成器")
    parser.add_argument("--sizes", default="4-14",
                        help="尺寸，如 '4-14' / '9' / '8,10,12'（默认 4-14）")
    parser.add_argument("--count", type=int, default=20,
                        help="每个尺寸目标生成数量（默认 20）")
    parser.add_argument("--stars", type=int, default=1,
                        help="每区星数 k（默认 1）")
    parser.add_argument("--strategy", default="random", choices=sorted(STRATEGIES),
                        help="生成策略（默认 random）")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                        help="输出目录（默认 Main/puzzles/Files）")
    parser.add_argument("--max-attempts", type=int, default=0,
                        help="每尺寸最大尝试次数；0 表示自动 = count*5000")
    parser.add_argument("--workers", type=int, default=0,
                        help="并行进程数；0 表示 CPU 核数")
    parser.add_argument("--seed", type=int, default=0,
                        help="随机基种子；0 表示用系统随机源")
    args = parser.parse_args(argv)

    workers = args.workers or os.cpu_count() or 1
    base_seed = args.seed or random.SystemRandom().randrange(2**31)
    sizes = parse_sizes(args.sizes)

    total = 0
    for size in sizes:
        max_attempts = args.max_attempts or args.count * 5000
        total += generate_for_size(
            size, args.stars, args.count, args.strategy, args.out_dir,
            max_attempts, workers, base_seed,
        )
        base_seed += max_attempts  # 不同尺寸用不相交的种子区间
    print(f"完成：共新增 {total} 个谜题。")


if __name__ == "__main__":
    main()
