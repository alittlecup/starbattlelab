"""Star Battle 候选态模型：每格三态 + 行/列/区域查询。"""

UNKNOWN = 0
STAR = 1
ELIMINATED = 2


class CandidateState:
    def __init__(self, region_grid, stars):
        self.region_grid = region_grid
        self.dim = len(region_grid)
        self.stars = stars
        self.grid = [[UNKNOWN] * self.dim for _ in range(self.dim)]
        self.invalid = False
        self.region_cells = {}
        for r in range(self.dim):
            for c in range(self.dim):
                self.region_cells.setdefault(region_grid[r][c], []).append((r, c))

    # --- 单元访问 ---
    def cells_of_row(self, r):
        return [(r, c) for c in range(self.dim)]

    def cells_of_col(self, c):
        return [(r, c) for r in range(self.dim)]

    def cells_of_region(self, region_id):
        return list(self.region_cells[region_id])

    def cells_of_line(self, axis, idx):
        return self.cells_of_row(idx) if axis == "row" else self.cells_of_col(idx)

    def all_units(self):
        """返回 [(kind, key, cells), ...]，kind in {'row','col','region'}。"""
        units = []
        for r in range(self.dim):
            units.append(("row", r, self.cells_of_row(r)))
        for c in range(self.dim):
            units.append(("col", c, self.cells_of_col(c)))
        for rid in self.region_cells:
            units.append(("region", rid, self.cells_of_region(rid)))
        return units

    # --- 查询 ---
    def count_state(self, cells, state):
        return sum(1 for (r, c) in cells if self.grid[r][c] == state)

    def unknowns(self, cells):
        return [(r, c) for (r, c) in cells if self.grid[r][c] == UNKNOWN]

    def neighbors(self, r, c):
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.dim and 0 <= nc < self.dim:
                    out.append((nr, nc))
        return out

    # --- 修改 ---
    def set_cell(self, r, c, state):
        self.grid[r][c] = state

    def copy(self):
        """浅复制：grid 深拷贝，region_grid/region_cells 只读共享。供回溯搜索分支用。"""
        new = CandidateState.__new__(CandidateState)
        new.region_grid = self.region_grid
        new.dim = self.dim
        new.stars = self.stars
        new.grid = [row[:] for row in self.grid]
        new.invalid = self.invalid
        new.region_cells = self.region_cells
        return new

    def apply(self, deduction):
        for (r, c, state) in deduction.marks:
            cur = self.grid[r][c]
            if cur != UNKNOWN and cur != state:
                self.invalid = True
            self.grid[r][c] = state
        for (_kind, _key, cells) in self.all_units():
            if self.count_state(cells, STAR) > self.stars:
                self.invalid = True

    def is_solved(self):
        if self.invalid:
            return False
        return is_complete_valid(self)


def is_complete_valid(state):
    """检查当前 STAR 布局是否为一个合法完整解。"""
    dim, stars = state.dim, state.stars
    for (_kind, _key, cells) in state.all_units():
        if state.count_state(cells, STAR) != stars:
            return False
    total = sum(1 for r in range(dim) for c in range(dim) if state.grid[r][c] == STAR)
    if total != dim * stars:
        return False
    for r in range(dim):
        for c in range(dim):
            if state.grid[r][c] == STAR:
                for (nr, nc) in state.neighbors(r, c):
                    if state.grid[nr][nc] == STAR:
                        return False
    return True
