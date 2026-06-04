"""SBN (Star Battle Notation) 解码为二维 region_grid。

decode_sbn / reconstruct_grid_from_borders 复制自 MiscTools/SBNBatchValidator.py
(原始实现，已在生产中验证)，此处复制而非 import，以避免引入该脚本的副作用。
"""

import math
from collections import deque

SBN_B64_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
SBN_CHAR_TO_INT = {c: i for i, c in enumerate(SBN_B64_ALPHABET)}
SBN_CODE_TO_DIM_MAP = {
    '55': 5,  '66': 6,  '77': 7,  '88': 8,  '99': 9, 'AA': 10, 'BB': 11, 'CC': 12, 'DD': 13,
    'EE': 14, 'FF': 15, 'GG': 16, 'HH': 17, 'II': 18, 'JJ': 19, 'KK': 20, 'LL': 21, 'MM': 22,
    'NN': 23, 'OO': 24, 'PP': 25
}


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
    try:
        size_code = sbn_string[0:2]
        dim = SBN_CODE_TO_DIM_MAP.get(size_code)
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
        num_single_direction_borders = dim * (dim - 1)
        vertical_bits = border_data[:num_single_direction_borders]
        horizontal_bits = border_data[num_single_direction_borders:]
        region_grid = reconstruct_grid_from_borders(dim, vertical_bits, horizontal_bits)
        return {'region_grid': region_grid, 'stars': stars, 'dim': dim}
    except (KeyError, IndexError, ValueError):
        return None


def decode_to_grid(sbn_string):
    """解码 SBN 字符串为 {region_grid, stars, dim}，失败返回 None。"""
    return decode_sbn(sbn_string)
