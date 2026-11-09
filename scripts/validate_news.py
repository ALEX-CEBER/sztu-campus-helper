# -*- coding: utf-8 -*-
"""
validate_news.py — 按字段规则检查一份资讯数据（列表或 {"items": [...]} 都可以）

用途：
  1. 改解析代码后，先拿样例数据验一遍字段规则，不用每次都去抓官网；
  2. 报告里演示"违规数据被拒绝"时，直接跑这个脚本贴输出。

用法：
    python scripts/validate_news.py tests/fixtures/bad_items.json
    python scripts/validate_news.py data/news.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import news_source as ns  # noqa: E402


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("items", [])
    return data


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python scripts/validate_news.py <json 文件>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"! 文件不存在：{path}")
        return 2

    items = load_items(path)
    ok, bad = 0, []
    for idx, item in enumerate(items, 1):
        reason = ns.validate_item(item)
        title = (item.get("title") or "(无标题)")[:34]
        if reason:
            bad.append((idx, title, reason))
            print(f"  × 第 {idx} 条被拒绝：{reason}  ← {title}")
        else:
            ok += 1
            print(f"  ✓ 第 {idx} 条通过：{title}")

    print(f"\n共 {len(items)} 条：通过 {ok}，拒绝 {len(bad)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
