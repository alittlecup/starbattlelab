---
name: generating-star-battle-puzzles
description: Use when needing to batch-generate Star Battle puzzles with guaranteed unique solutions, validate that a puzzle has exactly one solution, or render puzzles as colored region images — in the starbattlelab.github.io repo (MiscTools/generator).
---

# Generating Star Battle Puzzles

## Overview

The `starbattlelab.github.io` repo ships a generator at `MiscTools/generator/` that does generation, unique-solution validation, and colored-image rendering. **Do not reinvent it** — use these CLIs. Uniqueness is built in: only puzzles whose Z3 solver finds exactly one solution are kept.

## When to Use

- Batch-generating new Star Battle puzzles (sizes 5–14, k=1 default)
- Checking whether a puzzle (SBN string) has a unique solution
- Producing PNG images of puzzles with colored regions

Not for: solving a puzzle for a player (use `Main/solver.js` / `MiscTools/Z3Solver.py`), or difficulty rating (use `MiscTools/difficulty/`).

## Prerequisites (do this first)

```bash
python3 -m pip install z3-solver tqdm Pillow
python3 -c "import z3"   # must NOT error
```
If `import z3` fails with an **architecture mismatch** (x86_64 Python under Rosetta on arm64), pin the working build:
```bash
python3 -m pip install --force-reinstall --no-deps z3-solver==4.13.0.0
```

**Always run from the repo root** (commands use `python3 -m MiscTools.generator.*`, and `uniqueness.py` imports `MiscTools.Z3Solver`).

## Quick Reference

| Goal | Command |
|------|---------|
| Generate + validate + render, archived by date/size | `python3 -m MiscTools.generator.batch --sizes 7 --count 5` |
| Generate only (append to `Main/puzzles/Files`) | `python3 -m MiscTools.generator.generate --sizes 4-14 --count 50` |
| Render existing SBN(s) to PNG | `python3 -m MiscTools.generator.render --input <SBN-or-file-or-dir> --out out/png` |

Common `batch` flags: `--sizes 5-9` / `7` / `6,8`, `--count N`, `--stars k` (default 1), `--out-root output`, `--date YYYY-MM-DD` (default today), `--workers 0` (=CPU), `--seed` (reproducible), `--max-attempts` (0=auto `count×5000`). Run any command with `--help` for the full list.

## Output Structure (batch)

```
output/<YYYY-MM-DD>/<size>x<size>/
    ├── puzzles.txt     # one SBN per line (all unique-solution)
    └── <SBN>.png       # colored-region image per puzzle (filename = SBN)
```
Re-running tops up the same folder (reads existing `puzzles.txt`, dedups, appends).

## Validate a single puzzle

```python
from MiscTools.generator.sbn_codec import decode_sbn
from MiscTools.generator.uniqueness import is_unique
d = decode_sbn("991WiSHUFrpQihv1246rWa46ZT1X")
is_unique(d["region_grid"], d["stars"])   # True iff exactly one solution
```
Strongest cross-check (independent code path): `python3 MiscTools/SBNBatchValidator.py <file> --find-all` (deletes-nothing; remove the `found_puzzles.txt` it leaves behind).

## Common Mistakes

- **Running from a subdirectory** → `ModuleNotFoundError: MiscTools`. Run from repo root.
- **Large sizes hang / fall short of `--count`**: random strategy hit-rate is very low at ≥12, k=1. Cap with `--max-attempts` or generate fewer; a higher-yield strategy is future work (see `MiscTools/generator/ARCHITECTURE.md`).
- **Expecting sizes <5 or >25**: SBN codec only supports 5–25; others are skipped.
- **`output/` is not gitignored** — don't accidentally commit generated artifacts.

Adding a new generation strategy: see `MiscTools/generator/ARCHITECTURE.md` §4.
