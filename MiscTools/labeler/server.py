#!/usr/bin/env python3
"""Star Battle 谜题预览 / 难度标注 本地服务。

职责：
  - 提供静态页面（标注工具 UI、复用 Main/sbn.js）。
  - 列出 output/ 下各尺寸已生成的谜题（文件名即 SBN）。
  - 随机出题（按尺寸，可排除已看过的）。
  - 运行时调用现有难度引擎（MiscTools/difficulty）计算当前谜题难度分。

标注数据本身存浏览器 localStorage + 导出，不由本服务落盘。

用法：
    python3 MiscTools/labeler/server.py [--port 8765]
然后浏览器打开 http://localhost:8765/MiscTools/labeler/
"""

import argparse
import json
import os
import random
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# 仓库根目录（本文件位于 <root>/MiscTools/labeler/server.py）
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(ROOT, "output")
DIFFICULTY_DIR = os.path.join(ROOT, "MiscTools", "difficulty")

# 让难度引擎可被 import
sys.path.insert(0, DIFFICULTY_DIR)
_analyze = None
_config = None
_decode = None


def _load_difficulty():
    """惰性加载难度引擎，避免无谓的导入开销 / 报错。"""
    global _analyze, _config
    if _analyze is None:
        from rate import analyze  # noqa: E402
        from scorer import load_config  # noqa: E402
        _analyze = analyze
        _config = load_config()
    return _analyze, _config


def _load_decoder():
    """惰性加载 SBN 解码器（权威 Python codec，兼容生成器全部尺寸）。"""
    global _decode
    if _decode is None:
        from sbn_codec import decode_to_grid  # noqa: E402
        _decode = decode_to_grid
    return _decode


def _decode_payload(sbn):
    """解码 SBN -> 前端渲染所需的 {sbn, dim, stars, regionGrid}。失败返回 None。"""
    decoded = _load_decoder()(sbn)
    if decoded is None:
        return None
    return {
        "sbn": sbn,
        "dim": decoded["dim"],
        "stars": decoded["stars"],
        "regionGrid": decoded["region_grid"],
    }


# SBN -> 文件路径 的索引，按尺寸缓存。{size: [sbn, ...]}
_index_cache = {}


def _scan_size(size):
    """扫描 output/*/{size}x{size}/ 下所有 png，文件名（去扩展名）即 SBN。"""
    if size in _index_cache:
        return _index_cache[size]
    sbns = set()
    if os.path.isdir(OUTPUT_DIR):
        for date_dir in os.listdir(OUTPUT_DIR):
            size_dir = os.path.join(OUTPUT_DIR, date_dir, f"{size}x{size}")
            if not os.path.isdir(size_dir):
                continue
            for sub in os.listdir(size_dir):
                sub_path = os.path.join(size_dir, sub)
                if not os.path.isdir(sub_path):
                    continue
                for fn in os.listdir(sub_path):
                    if fn.endswith(".png"):
                        sbns.add(fn[:-4])
    result = sorted(sbns)
    _index_cache[size] = result
    return result


def _available_sizes():
    sizes = {}
    for size in range(4, 13):
        count = len(_scan_size(size))
        if count:
            sizes[size] = count
    return sizes


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 静默，避免刷屏

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            return self._handle_api(path, parse_qs(parsed.query))
        return self._serve_static(path)

    # ---------------- API ----------------
    def _handle_api(self, path, qs):
        try:
            if path == "/api/sizes":
                return self._send_json({"sizes": _available_sizes()})

            if path == "/api/random":
                size = int(qs.get("size", ["0"])[0])
                exclude = set(qs.get("exclude", [""])[0].split(",")) if qs.get("exclude") else set()
                pool = _scan_size(size)
                if not pool:
                    return self._send_json({"error": f"没有 {size}x{size} 谜题"}, 404)
                candidates = [s for s in pool if s not in exclude] or pool
                sbn = random.choice(candidates)
                payload = _decode_payload(sbn)
                if payload is None:
                    return self._send_json({"error": f"SBN 解码失败：{sbn}"}, 422)
                payload["remaining"] = len(candidates)
                return self._send_json(payload)

            if path == "/api/difficulty":
                sbn = qs.get("sbn", [""])[0]
                if not sbn:
                    return self._send_json({"error": "缺少 sbn"}, 400)
                analyze, config = _load_difficulty()
                result = analyze(sbn, config)
                if result is None:
                    return self._send_json({"error": "无法解析该 SBN"}, 422)
                return self._send_json(result)

            return self._send_json({"error": "未知接口"}, 404)
        except Exception as e:  # 把后端错误透传给前端便于排查
            return self._send_json({"error": str(e)}, 500)

    # ---------------- 静态文件 ----------------
    def _serve_static(self, path):
        if path in ("/", "/MiscTools/labeler", "/MiscTools/labeler/"):
            path = "/MiscTools/labeler/index.html"
        rel = path.lstrip("/")
        full = os.path.abspath(os.path.join(ROOT, rel))
        if not full.startswith(ROOT) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".png": "image/png",
            ".json": "application/json; charset=utf-8",
        }.get(os.path.splitext(full)[1], "application/octet-stream")
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://localhost:{args.port}/MiscTools/labeler/"
    print(f"Star Battle 标注工具已启动： {url}")
    print(f"可用尺寸： {_available_sizes()}")
    print("Ctrl+C 退出。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出。")


if __name__ == "__main__":
    main()
