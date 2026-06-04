"""T1 基础技巧（tier 1）。每个函数 find(state)->Deduction|None。"""

from candidate_state import UNKNOWN, STAR, ELIMINATED
from deduction import Deduction

TIER = 1


def adjacency_elimination(state):
    marks = []
    seen = set()
    for r in range(state.dim):
        for c in range(state.dim):
            if state.grid[r][c] == STAR:
                for (nr, nc) in state.neighbors(r, c):
                    if state.grid[nr][nc] == UNKNOWN and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        marks.append((nr, nc, ELIMINATED))
    if not marks:
        return None
    return Deduction("adjacency_elimination", TIER, marks,
                     "星的 8 邻格不能再有星")


def unit_complete(state):
    marks = []
    seen = set()
    for (_kind, _key, cells) in state.all_units():
        if state.count_state(cells, STAR) == state.stars:
            for (r, c) in state.unknowns(cells):
                if (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, ELIMINATED))
    if not marks:
        return None
    return Deduction("unit_complete", TIER, marks,
                     "单元已放满所需星数，其余格清除")


def last_cell(state):
    marks = []
    seen = set()
    for (_kind, _key, cells) in state.all_units():
        placed = state.count_state(cells, STAR)
        unk = state.unknowns(cells)
        if placed < state.stars and len(unk) == state.stars - placed:
            for (r, c) in unk:
                if (r, c) not in seen:
                    seen.add((r, c))
                    marks.append((r, c, STAR))
    if not marks:
        return None
    return Deduction("last_cell", TIER, marks,
                     "单元剩余空格数恰等于待放星数")
