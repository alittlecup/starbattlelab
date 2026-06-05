"""共享 SBN (Star Battle Notation) codec：encode + decode + 常量表。

- decode 逻辑复制自已在生产中验证的 MiscTools/SBNBatchValidator.py /
  MiscTools/difficulty/sbn_codec.py。
- encode 移植自 LegacyImplementations/API-main/backend/puzzle_handler.py
  的 encode_to_sbn，保证生成的 SBN 与现有 Main/puzzles/Files 文件格式一致。

生成器与渲染器共用本模块，确保两端编解码一致。
"""

import math
from collections import deque

# --- SBN 常量 ---
SBN_B64_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
SBN_CHAR_TO_INT = {c: i for i, c in enumerate(SBN_B64_ALPHABET)}
SBN_INT_TO_CHAR = {i: c for i, c in enumerate(SBN_B64_ALPHABET)}
SBN_CODE_TO_DIM_MAP = {
    '55': 5,  '66': 6,  '77': 7,  '88': 8,  '99': 9, 'AA': 10, 'BB': 11, 'CC': 12, 'DD': 13,
    'EE': 14, 'FF': 15, 'GG': 16, 'HH': 17, 'II': 18, 'JJ': 19, 'KK': 20, 'LL': 21, 'MM': 22,
    'NN': 23, 'OO': 24, 'PP': 25,
}
DIM_TO_SBN_CODE_MAP = {v: k for k, v in SBN_CODE_TO_DIM_MAP.items()}


# --- ENCODE ---
def encode_sbn(region_grid, stars):
    """将 region_grid + 每区星数编码为 SBN 字符串（不含玩家标注）。

    :param list[list[int]] region_grid: dim×dim 的区域网格。
    :param int stars: 每区星数。
    :returns: SBN 字符串，dim 不受支持时返回 None。
    :rtype: str | None
    """
    dim = len(region_grid)
    sbn_code = DIM_TO_SBN_CODE_MAP.get(dim)
    if not sbn_code:
        return None

    # 垂直边界：逐行扫描相邻列是否分属不同区域。
    vertical_bits = [
        '1' if c < dim - 1 and region_grid[r][c] != region_grid[r][c + 1] else '0'
        for r in range(dim) for c in range(dim - 1)
    ]
    # 水平边界：逐列存储以匹配解码器。
    horizontal_bits = [
        '1' if r < dim - 1 and region_grid[r][c] != region_grid[r + 1][c] else '0'
        for c in range(dim) for r in range(dim - 1)
    ]

    clean_bitfield = "".join(vertical_bits) + "".join(horizontal_bits)
    padding_needed = (6 - len(clean_bitfield) % 6) % 6
    padded_bitfield = ('0' * padding_needed) + clean_bitfield

    region_data = "".join(
        SBN_INT_TO_CHAR[int(padded_bitfield[i:i + 6], 2)]
        for i in range(0, len(padded_bitfield), 6)
    )
    flag = 'W'  # 'W' = 无玩家标注
    return f"{sbn_code}{stars}{flag}{region_data}"


# --- DECODE ---
def reconstruct_grid_from_borders(dim, vertical_bits, horizontal_bits):
    region_grid = [[0] * dim for _ in range(dim)]
    region_id = 1
    for r_start in range(dim):
        for c_start in range(dim):
            if region_grid[r_start][c_start] == 0:
                q = deque([(r_start, c_start)])
                region_grid[r_start][c_start] = region_id
                while q:
                    r, c = q.popleft()
                    if c < dim - 1 and region_grid[r][c+1] == 0 and vertical_bits[r*(dim-1) + c] == '0':
                        region_grid[r][c+1] = region_id; q.append((r, c+1))
                    if c > 0 and region_grid[r][c-1] == 0 and vertical_bits[r*(dim-1) + (c-1)] == '0':
                        region_grid[r][c-1] = region_id; q.append((r, c-1))
                    if r < dim - 1 and region_grid[r+1][c] == 0 and horizontal_bits[c*(dim-1) + r] == '0':
                        region_grid[r+1][c] = region_id; q.append((r+1, c))
                    if r > 0 and region_grid[r-1][c] == 0 and horizontal_bits[c*(dim-1) + (r-1)] == '0':
                        region_grid[r-1][c] = region_id; q.append((r-1, c))
                region_id += 1
    return region_grid


def decode_sbn(sbn_string):
    """解码 SBN 字符串为 {region_grid, stars, dim}，失败返回 None。"""
    try:
        dim = SBN_CODE_TO_DIM_MAP.get(sbn_string[0:2])
        if not dim:
            return None
        stars = int(sbn_string[2])
        border_bits_needed = 2 * dim * (dim - 1)
        border_chars_needed = math.ceil(border_bits_needed / 6)
        region_data_str = sbn_string[4: 4 + border_chars_needed]
        full_bitfield = "".join(
            bin(SBN_CHAR_TO_INT.get(char, 0))[2:].zfill(6) for char in region_data_str
        )
        padding_bits = len(full_bitfield) - border_bits_needed
        border_data = full_bitfield[padding_bits:]
        num_single = dim * (dim - 1)
        vertical_bits = border_data[:num_single]
        horizontal_bits = border_data[num_single:]
        region_grid = reconstruct_grid_from_borders(dim, vertical_bits, horizontal_bits)
        return {'region_grid': region_grid, 'stars': stars, 'dim': dim}
    except (KeyError, IndexError, ValueError):
        return None
