# -*- coding: utf-8 -*-
"""
server.py — 本地服务：静态页面 + 校园资讯实时接口

为什么需要它：浏览器直接抓 nbw.sztu.edu.cn 会被跨域拦住，静态页面只能读死数据。
这里用 Python 起一个本地小服务，页面请求 /api/news，服务端去抓官网再返回 JSON，
所以"刷新页面就能拿到最新的校园消息"这件事才成立。

接口约定见 docs/api.md（改字段时两边一起改）。

用法：
    python server.py                 # 默认 http://localhost:8000/
    python server.py --port 8100     # 换端口
    python server.py --open          # 启动后自动开浏览器
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import threading
import time
import traceback
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import news_source as ns  # noqa: E402

VERSION = "v0.4.0"
DEFAULT_TTL = 60          # 秒：缓存多久后触发后台刷新
MAX_ITEMS_LIMIT = 50      # 接口单次最多返回多少条


class NewsService:
    """把"抓取 + 缓存 + 后台刷新"收在一处，供接口调用。"""

    def __init__(self, config_path: str | None = None, ttl: int = DEFAULT_TTL,
                 use_cache: bool = True):
        self.config_path = config_path
        self.ttl = ttl
        self._lock = threading.Lock()
        self.payload: dict | None = ns.read_payload() if use_cache else None
        self.refreshing = False
        self.last_error: str | None = None
        self.started_at = time.time()

    # ---------- 缓存状态 ----------
    def age(self) -> int:
        if not self.payload:
            return 10 ** 9
        try:
            ts = datetime.fromisoformat(self.payload.get("updated_at", ""))
            return max(0, int((datetime.now(ns.CST) - ts).total_seconds()))
        except (ValueError, TypeError):
            return 10 ** 9

    def is_fresh(self) -> bool:
        return self.age() <= self.ttl

    # ---------- 抓取 ----------
    def _refresh_once(self, with_details: bool) -> None:
        """真正干活的部分；调用方负责加锁与 refreshing 标记。"""
        cfg = ns.load_config(self.config_path)
        previous = (self.payload or {}).get("items") or []
        result = ns.fetch_all(
            cfg,
            max_items=int(cfg.get("max_items", 30)),
            with_details=with_details,
            previous_items=previous,
            log=lambda m: print(m, flush=True),
        )
        if result["items"]:
            payload = ns.build_payload(result, cfg, int(cfg.get("max_items", 30)))
            ns.write_payload(payload)          # 落盘：重启后还在
            self.payload = payload
            self.last_error = None
        else:
            self.last_error = "；".join(result["errors"]) or "未解析到任何条目"
            if self.payload:
                self.payload = {**self.payload, "stale": True,
                                "errors": result["errors"],
                                "rejected": result["rejected"]}
            print(f"! 本次刷新失败：{self.last_error}", flush=True)

    def refresh(self, with_details: bool = True) -> None:
        """同步抓一次（点刷新、或首次没有缓存时用）。"""
        with self._lock:
            self.refreshing = True
            try:
                self._refresh_once(with_details)
            except Exception as e:  # noqa: BLE001
                self.last_error = f"{type(e).__name__}: {e}"
                traceback.print_exc()
            finally:
                self.refreshing = False

    def refresh_in_background(self) -> None:
        """缓存过期时用：立刻返回旧数据，后台悄悄抓新的。"""
        if self.refreshing:
            return
        self.refreshing = True

        def run() -> None:
            try:
                with self._lock:
                    self._refresh_once(with_details=False)
            except Exception as e:  # noqa: BLE001
                self.last_error = f"{type(e).__name__}: {e}"
                traceback.print_exc()
            finally:
                self.refreshing = False

        threading.Thread(target=run, daemon=True).start()

    # ---------- 对外快照 ----------
    def snapshot(self) -> dict:
        base = dict(self.payload or {})
        age = self.age()
        data = {
            "ok": True,
            "version": VERSION,
            "updated_at": base.get("updated_at"),
            "count": base.get("count", 0),
            "items": base.get("items", []),
            "sources": base.get("sources", []),
            "rejected": base.get("rejected", []),
            "stale": bool(base.get("stale")),
            "cache_age_seconds": age if age < 10 ** 8 else None,
            "refreshing": self.refreshing,
            "warning": None,
        }
        if data["stale"] and self.last_error:
            minutes = max(1, age // 60)
            data["warning"] = {
                "code": "CRAWL_FAILED",
                "message": f"校园通暂时连不上，当前显示约 {minutes} 分钟前的缓存",
            }
        return data


SERVICE: NewsService | None = None


class Handler(BaseHTTPRequestHandler):
    server_version = "SZTUHelper/" + VERSION

    # ---------- 工具 ----------
    def send_json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, code: int, err_code: str, message: str, detail: str = "") -> None:
        self.send_json(code, {
            "ok": False,
            "error": {"code": err_code, "message": message, "detail": detail},
        })

    def log_message(self, fmt: str, *args) -> None:  # 精简访问日志
        print(f"[{time.strftime('%H:%M:%S')}] {fmt % args}", flush=True)

    # ---------- 路由 ----------
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/news":
            return self.handle_news(parse_qs(parsed.query))
        if path == "/api/health":
            assert SERVICE is not None
            return self.send_json(200, {
                "ok": True, "version": VERSION,
                "uptime_seconds": int(time.time() - SERVICE.started_at),
                "cache_age_seconds": SERVICE.age() if SERVICE.age() < 10 ** 8 else None,
                "refreshing": SERVICE.refreshing,
            })
        if path.startswith("/api/"):
            return self.error_json(404, "NOT_FOUND", "这个接口不存在", path)

        return self.serve_static(path)

    def handle_news(self, qs: dict) -> None:
        assert SERVICE is not None
        try:
            limit = int((qs.get("max") or ["24"])[0])
        except ValueError:
            return self.error_json(400, "BAD_PARAM", "参数 max 需要是整数", f"收到的 max={qs.get('max')}")
        if limit < 1 or limit > MAX_ITEMS_LIMIT:
            return self.error_json(400, "BAD_PARAM", f"参数 max 需要在 1～{MAX_ITEMS_LIMIT} 之间", f"收到的 max={limit}")
        force = (qs.get("force") or ["0"])[0] in ("1", "true", "yes")

        # 没有缓存时只能等一次真实抓取
        if SERVICE.payload is None:
            SERVICE.refresh(with_details=True)
            if SERVICE.payload is None:
                return self.error_json(
                    502, "CRAWL_FAILED",
                    "校园通暂时连不上，也没找到本地缓存，请稍后再试",
                    SERVICE.last_error or "",
                )

        # 主动刷新（按钮）→ 同步抓，带摘要；自然过期 → 后台抓，先返回旧数据
        if force:
            SERVICE.refresh(with_details=True)
            if SERVICE.last_error:
                data = SERVICE.snapshot()
                data["warning"] = data["warning"] or {
                    "code": "CRAWL_FAILED",
                    "message": "刷新失败，页面保留上一次的数据",
                }
                return self.send_json(200, self.slice_items(data, limit))
        elif not SERVICE.is_fresh():
            SERVICE.refresh_in_background()

        data = SERVICE.snapshot()
        self.send_json(200, self.slice_items(data, limit))

    @staticmethod
    def slice_items(data: dict, limit: int) -> dict:
        data = dict(data)
        data["items"] = data.get("items", [])[:limit]
        data["count"] = len(data["items"])
        return data

    def serve_static(self, path: str) -> None:
        rel = "web/index.html" if path in ("/", "") else path.lstrip("/")
        target = (ROOT / rel).resolve()
        if ROOT not in target.parents and target != ROOT:
            return self.error_json(403, "FORBIDDEN", "只能访问项目内的文件", path)
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            return self.error_json(404, "NOT_FOUND", "文件不存在", rel)

        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix in (".html", ".js", ".css", ".json"):
            ctype += "; charset=utf-8"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--config", default="", help="指定资讯配置（默认 config/news.json）")
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL, help="缓存多少秒后后台刷新")
    ap.add_argument("--open", action="store_true", help="启动后打开浏览器")
    ap.add_argument("--no-cache", action="store_true",
                    help="忽略本地缓存启动（用于演示'没有缓存又抓不到'的失败返回）")
    args = ap.parse_args()

    global SERVICE
    SERVICE = NewsService(config_path=args.config or None, ttl=args.ttl,
                          use_cache=not args.no_cache)

    url = f"http://localhost:{args.port}/"
    print(f"SZTU 校园办事万事屋 {VERSION}")
    print(f"  页面：{url}")
    print(f"  接口：{url}api/news")
    if SERVICE.payload:
        print(f"  已有缓存：{SERVICE.payload.get('count', 0)} 条，{SERVICE.payload.get('updated_at')}")
    else:
        print("  暂无缓存，首次请求会现抓一次（约 10 秒）")

    if args.open:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.daemon_threads = True
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    return 0


if __name__ == "__main__":
    sys.exit(main())
