"""SBN 渲染工具（独立，按需运行）。

把 SBN 谜题画成彩色区域 PNG：每个区域一种区分色，细线画格子、粗线画区域边界。
文件名直接用 SBN 字符串（其字母表 0-9A-Za-z-_ 对文件名安全）。

用法：
    python -m MiscTools.generator.render --input 991WiSHUFrpQihv1246rWa46ZT1X --out out/png
    python -m MiscTools.generator.render --input Main/puzzles/Files/9-1-unsorted.txt --out out/png
    python -m MiscTools.generator.render --input Main/puzzles/Files --out out/png
"""

import argparse
import colorsys
import os

from PIL import Image, ImageDraw

from .sbn_codec import decode_sbn


def region_palette(num_regions):
    """为 num_regions 个区域生成区分度高的浅色调色板（HSV 均匀取色）。"""
    colors = []
    for i in range(num_regions):
        hue = i / max(num_regions, 1)
        r, g, b = colorsys.hsv_to_rgb(hue, 0.35, 1.0)  # 低饱和 + 高明度 -> 浅色，衬黑边
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors


def render_grid(region_grid, cell=48, thin=1, thick=4):
    """把 region_grid 画成 PIL.Image。"""
    dim = len(region_grid)
    pad = thick
    size_px = dim * cell + 2 * pad
    img = Image.new("RGB", (size_px, size_px), "white")
    draw = ImageDraw.Draw(img)

    region_ids = sorted({x for row in region_grid for x in row})
    color_of = {rid: c for rid, c in zip(region_ids, region_palette(len(region_ids)))}

    # 1) 填充区域底色
    for r in range(dim):
        for c in range(dim):
            x0 = pad + c * cell
            y0 = pad + r * cell
            draw.rectangle([x0, y0, x0 + cell, y0 + cell], fill=color_of[region_grid[r][c]])

    # 2) 细线画所有格子线
    for i in range(dim + 1):
        x = pad + i * cell
        draw.line([(x, pad), (x, pad + dim * cell)], fill=(180, 180, 180), width=thin)
        y = pad + i * cell
        draw.line([(pad, y), (pad + dim * cell, y)], fill=(180, 180, 180), width=thin)

    # 3) 粗线画区域边界（相邻异区）+ 外框
    for r in range(dim):
        for c in range(dim):
            x0 = pad + c * cell
            y0 = pad + r * cell
            x1, y1 = x0 + cell, y0 + cell
            rid = region_grid[r][c]
            if r == 0 or region_grid[r - 1][c] != rid:
                draw.line([(x0, y0), (x1, y0)], fill="black", width=thick)
            if r == dim - 1 or region_grid[r + 1][c] != rid:
                draw.line([(x0, y1), (x1, y1)], fill="black", width=thick)
            if c == 0 or region_grid[r][c - 1] != rid:
                draw.line([(x0, y0), (x0, y1)], fill="black", width=thick)
            if c == dim - 1 or region_grid[r][c + 1] != rid:
                draw.line([(x1, y0), (x1, y1)], fill="black", width=thick)

    return img


def render_sbn(sbn, out_dir, cell=48):
    """渲染单个 SBN 并保存为 {sbn}.png，成功返回路径，失败返回 None。"""
    data = decode_sbn(sbn)
    if data is None:
        print(f"[skip] 无法解码 SBN: {sbn}")
        return None
    img = render_grid(data["region_grid"], cell=cell)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{sbn}.png")
    img.save(path)
    return path


def collect_sbns(input_arg):
    """根据 --input 收集 SBN 列表：目录 / 文件（每行一个）/ 字面 SBN 字符串。"""
    if os.path.isdir(input_arg):
        sbns = []
        for name in sorted(os.listdir(input_arg)):
            p = os.path.join(input_arg, name)
            if os.path.isfile(p) and name.endswith(".txt"):
                with open(p, encoding="utf-8") as f:
                    sbns.extend(line.strip() for line in f if line.strip())
        return sbns
    if os.path.isfile(input_arg):
        with open(input_arg, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return [input_arg.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="SBN -> 彩色区域 PNG 渲染工具")
    parser.add_argument("--input", required=True,
                        help="单个 SBN / 含 SBN 的 .txt 文件 / 含 .txt 的目录")
    parser.add_argument("--out", default="out/png", help="PNG 输出目录（默认 out/png）")
    parser.add_argument("--cell", type=int, default=48, help="每格像素大小（默认 48）")
    args = parser.parse_args(argv)

    sbns = collect_sbns(args.input)
    done = 0
    for sbn in sbns:
        if render_sbn(sbn, args.out, cell=args.cell):
            done += 1
    print(f"渲染完成：{done}/{len(sbns)} 张 -> {args.out}")


if __name__ == "__main__":
    main()
