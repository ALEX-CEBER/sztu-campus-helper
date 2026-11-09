# -*- coding: utf-8 -*-
"""
fetch_news.py — 命令行抓取校园通资讯，生成 data/news.json 与 data/news.js

解析与校验逻辑都在 scripts/news_source.py 里，本文件只负责命令行参数和落盘。
所有参数在 config/news.json 中配置。

用法：
    python scripts/fetch_news.py                 # 正常抓取
    python scripts/fetch_news.py --max 10        # 临时限制条数
    python scripts/fetch_news.py --no-detail     # 不补摘要，只抓列表（快）
    python scripts/fetch_news.py --offline       # 只用上次缓存，不联网
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import news_source as ns  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="只用缓存，不发起网络请求")
    ap.add_argument("--max", type=int, default=0, help="临时限制条数")
    ap.add_argument("--no-detail", action="store_true", help="不抓详情摘要（只要列表）")
    ap.add_argument("--config", default="", help="指定配置文件（默认 config/news.json）")
    args = ap.parse_args()

    cfg = ns.load_config(args.config or None)
    max_items = args.max or int(cfg.get("max_items", 30))

    if args.offline:
        cache = ns.OUT_PATH if ns.OUT_PATH.exists() else ns.CACHE_PATH
        if not cache.exists():
            print("! 没有可用缓存，先跑一次在线抓取")
            return 1
        data = json.loads(cache.read_text(encoding="utf-8"))
        data["stale"] = True
        data["count"] = len(data.get("items", []))
        ns.write_payload(data)
        print(f"✔ 离线模式：沿用 {len(data.get('items', []))} 条缓存")
        return 0

    result = ns.fetch_all(cfg, max_items=max_items, with_details=not args.no_detail)
    if not result["items"]:
        print("! 本次没有抓到任何合规条目")
        for err in result["errors"]:
            print("  -", err)
        return 1

    payload = ns.build_payload(result, cfg, max_items)
    ns.write_payload(payload)
    print(f"✔ 写入 data/news.json：{len(result['items'])} 条"
          f"（拒绝 {len(result['rejected'])} 条，失败 {len(result['errors'])} 处）")
    for r in result["rejected"][:5]:
        print(f"  × {r['reason']}：{r['title'][:28]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
