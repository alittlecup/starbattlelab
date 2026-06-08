---
name: generating-star-battle-puzzles
description: Use when needing to batch-generate Star Battle puzzles with guaranteed unique solutions, generate large grids (8x8 and up) efficiently, produce puzzles with special region shapes, validate a puzzle has one solution, or render puzzles as colored images — in the starbattlelab.github.io repo (MiscTools/generator).
---

# Generating Star Battle Puzzles

## Overview

The `starbattlelab.github.io` repo ships a generator at `MiscTools/generator/`. **Do not reinvent it.** Per-candidate pipeline:

`strategy.generate` → `uniqueness.is_unique` → canonical-form dedup → `classify` category → write `puzzles.txt` + render PNG.

Uniqueness is built in (only one-solution puzzles are kept). For k=1, `is_unique` uses a fast custom solver (`fast_solver.py`, region-MRV DFS, ~40x faster than Z3); k>1 falls back to Z3. Dedup is by **canonical form** (rotations/mirrors/relabel = same shape) so saved puzzles are geometrically distinct.

## Choosing a strategy (the key decision)

| Situation | Strategy | Why |
|-----------|----------|-----|
| Large grids **8x8–14x14** | **`refine`** | solution-first + counterexample-guided border repair → ~60–99% hit. Random is ~0.4% at 9x9 (HOURS); refine does 10000 in minutes. |
| Small grids 4x4–7x7, max variety | `all` (random+progressive) | huge distinct pool, high enough hit |
| Special recognizable shapes | `shapes` or `shape-<L/T/cross/corner/zigzag/heart>` | one region forms the shape |

**Never use `random`/`progressive`/`all` for 8x8+ — it is orders of magnitude slower. Use `refine`.**

## Quick Reference

```bash
# Fill a size to a target total (recommended; counts existing, dedups, resumable)
python3 -m MiscTools.generator.gen_to_target --size 11 --target 10000 --strategy refine

# One-off batch, archived by date/size/category + manifest.csv
python3 -m MiscTools.generator.batch --sizes 5 --count 1000 --strategy shapes
python3 -m MiscTools.generator.batch --sizes 9 --count 10000 --strategy refine

# Render existing SBN(s) to PNG
python3 -m MiscTools.generator.render --input <SBN-or-file-or-dir> --out out/png
```
Common flags: `--workers 0` (=CPU), `--seed` (reproducible), `--date`, `--cell`, `--max-attempts`. Run any command with `--help`. **Always run from repo root** (`python3 -m MiscTools.generator.*`).

## Output structure

```
output/<YYYY-MM-DD>/<size>x<size>/<category>/{puzzles.txt, <SBN>.png}
output/<YYYY-MM-DD>/<size>x<size>/manifest.csv   # sbn, category, symmetry, size_profile
```
`category` ∈ `shape-*`, `symmetric-rot90/-rot180/-mirror` (rare), `progressive`, `distinct`, `uniform`, `plain`.

## Validate / verify

```python
from MiscTools.generator.sbn_codec import decode_sbn
from MiscTools.generator.uniqueness import is_unique
d = decode_sbn("991WiSHUFrpQihv1246rWa46ZT1X"); is_unique(d["region_grid"], d["stars"])
```
Independent cross-check (separate code path): `python3 MiscTools/SBNBatchValidator.py <file> --find-all` (then delete the `found_puzzles.txt` it leaves).

## Setup

`pip install z3-solver tqdm Pillow`. If `import z3` errors with an arch mismatch (x86_64 Python under Rosetta on arm64), pin `z3-solver==4.13.0.0`.

## Common mistakes

- **Using random/progressive for 8x8+** → hours instead of minutes. Use `refine`.
- **Running from a subdirectory** → `ModuleNotFoundError: MiscTools`. Run from repo root.
- **Sizes <4 or >14** are skipped (generator supports 4–14; 4x4 is a custom extension the web app can't load).
- **PNG vs puzzles.txt count off by 1–2** on macOS: case-insensitive filesystem collapses two SBNs differing only in letter case. `puzzles.txt` is the source of truth.
- `output/` is not gitignored — don't commit artifacts unintentionally.

Internals & adding strategies: `MiscTools/generator/ARCHITECTURE.md`.
