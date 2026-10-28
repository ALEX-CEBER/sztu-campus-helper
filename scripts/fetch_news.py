# -*- coding: utf-8 -*-
"""
fetch_news.py — 抓取 SZTU「校园通」资讯，生成 data/news.json

设计要点（对应报告"数据获取方式"一节）：
1. 数据获取：解析服务端直出 HTML（博达 CMS，非 SPA），不依赖任何私有接口；
2. 稳健性：超时 + 指数退避重试 + 限频 + 上次成功结果缓存（失败时兜底为 stale 数据）；
3. 合规：自定义 UA 标注项目与仓库、单次请求间隔 0.8s、只保留标题/时间/分类/摘要/链接，
   不转载正文全文；
4. 可配置：全部参数在 config/news.json。

用法：
    python scripts/fetch_news.py                 # 正常抓取
    python scripts/fetch_news.py --offline       # 只用缓存（演示/断网时）
    python scripts/fetch_news.py --max 10        # 临时限制条数
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "news.json"
OUT_PATH = ROOT / "data" / "news.json"
CACHE_PATH = ROOT / "data" / "news-cache.json"

# 栏目号 -> 中文分类（博达 CMS 的 info/{栏目}/{文章}.htm）
COLUMN_MAP = {
    "1003": "校园新闻",
    "1019": "科研",
    "1020": "行政",
    "1021": "学工",
    "1022": "校园",
    "1032": "信息化",
}

CST = timezone(timedelta(hours=8))  # 中国标准时间


def log(msg: str) -> None:
    print(msg, flush=True)


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def http_get(url: str, cfg: dict, referer: str = "") -> str:
    """带重试与退避的 GET；失败抛最后一次异常。"""
    headers = {
        "User-Agent": cfg.get("user_agent", "Mozilla/5.0"),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    last_err = None
    for attempt in range(1, int(cfg.get("retries", 3)) + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=cfg.get("timeout_seconds", 15)) as resp:
                raw = resp.read()
            # 博达站点多为 UTF-8，少量页面为 GBK：按 meta 猜测
            for enc in ("utf-8", "gb18030"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="ignore")
        except Exception as e:  # noqa: BLE001
            last_err = e
            wait = float(cfg.get("retry_backoff_seconds", 2)) * attempt
            log(f"    ! 第 {attempt} 次请求失败：{e}；{wait:.1f}s 后重试")
            time.sleep(wait)
    raise last_err  # type: ignore[misc]


def strip_tags(s: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    # 正文常被逐字套 <span>，会留下"数 字化"这类字间空格 → 去掉中文字符之间的空格
    s = re.sub(r"(?<=[\u4e00-\u9fa5]) (?=[\u4e00-\u9fa5])", "", s)
    return s


def absolutize(href: str, base: str) -> str:
    href = href.strip()
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://nbw.sztu.edu.cn" + href
    return base.rstrip("/") + "/" + href.lstrip("./")


A_TAG_RE = re.compile(
    r'<a\s[^>]*href="([^"]*info/(\d+)/\d+\.htm)"[^>]*>(.*?)</a>', re.S | re.I
)
DATE_RE = re.compile(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})")


def parse_list(html: str, base: str, source_name: str) -> list[dict]:
    """从列表页/首页解析条目：标题、分类、日期、链接。"""
    items, seen = [], set()
    for m in A_TAG_RE.finditer(html):
        href, column, inner = m.group(1), m.group(2), m.group(3)

        # 标题：优先 title 属性，否则取内部最长中文文本
        title_attr = re.search(r'title="([^"]{4,})"', m.group(0))
        inner_text = strip_tags(inner)
        cat_tag = re.search(r"[\[【]([^\]】]{1,6})[\]】]", inner_text)
        category = cat_tag.group(1) if cat_tag else COLUMN_MAP.get(column, source_name)

        text_wo_cat = re.sub(r"[\[【][^\]】]{1,6}[\]】]", " ", inner_text)
        text_wo_date = DATE_RE.sub(" ", text_wo_cat).strip()
        title = (title_attr.group(1).strip() if title_attr else text_wo_date)
        title = unescape(re.sub(r"\s+", " ", title)).strip()
        if len(title) < 4:
            continue

        # 日期：链接内部或其后 260 个字符内
        tail = html[m.end(): m.end() + 260]
        date_m = DATE_RE.search(inner_text) or DATE_RE.search(tail)
        if date_m:
            date = f"{date_m.group(1)}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"
        else:
            date = ""

        url = absolutize(href, base)
        if url in seen:
            continue
        seen.add(url)
        items.append({
            "title": title,
            "url": url,
            "date": date,
            "category": category,
            "column": column,
            "source": source_name,
        })
    return items


DETAIL_BODY_RE = re.compile(
    r'<(?:div|td)[^>]*(?:id="vsb_content[^"]*"|class="[^"]*v_news_content[^"]*")[^>]*>(.*?)</(?:div|td)>',
    re.S | re.I,
)


def parse_detail_summary(html: str, limit: int) -> str:
    m = DETAIL_BODY_RE.search(html)
    body = m.group(1) if m else html
    text = strip_tags(body)
    # 去掉常见的"发布时间/来源/点击数"前缀噪声
    text = re.sub(r"^(发布(时间|者)?|来源|点击数|作者|编辑)[：:]\s*[\w\-\s:：]+", "", text)
    return text[:limit].strip() + ("…" if len(text) > limit else "")


def sort_key(item: dict) -> str:
    return item.get("date") or "0000-00-00"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="只用缓存，不发起网络请求")
    ap.add_argument("--max", type=int, default=0, help="临时限制条数")
    args = ap.parse_args()

    cfg = load_config()
    max_items = args.max or int(cfg.get("max_items", 30))
    delay = float(cfg.get("request_delay_seconds", 0.8))
    all_items: list[dict] = []
    errors: list[str] = []

    if args.offline:
        log("· 离线模式：直接读取缓存")
        if CACHE_PATH.exists():
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            all_items = cache.get("items", [])
        else:
            log("  ! 无缓存可用")
    else:
        for src in cfg.get("sources", []):
            if not src.get("enabled", True):
                continue
            log(f"· 抓取「{src['name']}」：{src['url']}")
            try:
                html = http_get(src["url"], cfg)
                items = parse_list(html, src["url"], src["name"])
                log(f"  解析到 {len(items)} 条")
                all_items.extend(items)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{src['name']}: {e}")
                log(f"  ! 失败：{e}")
            time.sleep(delay)

    # 去重（按 URL）+ 按日期倒序
    uniq, seen = [], set()
    for it in sorted(all_items, key=sort_key, reverse=True):
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)
    uniq = uniq[:max_items]

    # 详情摘要（只抓缺摘要的前 N 条，限频）
    if cfg.get("fetch_detail_summary") and not args.offline:
        detail_limit = int(cfg.get("detail_limit", 12))
        summary_len = int(cfg.get("summary_length", 110))
        need = [it for it in uniq if not it.get("summary")][:detail_limit]
        log(f"· 抓取详情摘要 {len(need)} 条（间隔 {delay}s）")
        for idx, it in enumerate(need, 1):
            try:
                time.sleep(delay)
                html = http_get(it["url"], cfg, referer="https://nbw.sztu.edu.cn/")
                it["summary"] = parse_detail_summary(html, summary_len)
                log(f"  [{idx}/{len(need)}] {it['title'][:18]}…")
            except Exception as e:  # noqa: BLE001
                errors.append(f"详情 {it['url']}: {e}")
                it["summary"] = ""
                log(f"  [{idx}/{len(need)}] 失败：{e}")

    # 缓存上次成功结果
    stale = False
    if uniq:
        CACHE_PATH.write_text(
            json.dumps({"items": uniq, "fetched_at": datetime.now(CST).isoformat(timespec="seconds")},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        # 全部源都失败 → 用缓存兜底
        stale = True
        if CACHE_PATH.exists():
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            uniq = cache.get("items", [])[:max_items]
            log(f"  ! 本次全部源失败，回退到缓存（{len(uniq)} 条）")

    payload = {
        "updated_at": datetime.now(CST).isoformat(timespec="seconds"),
        "stale": stale,
        "count": len(uniq),
        "errors": errors,
        "sources": [s["url"] for s in cfg.get("sources", []) if s.get("enabled", True)],
        "items": uniq,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # 同步生成 news.js：数据内嵌，双击网页/预览面板也能读（无需服务器）
    (ROOT / "data" / "news.js").write_text(
        "window.NEWS_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    log(f"✔ 写入 {OUT_PATH.relative_to(ROOT)}：{len(uniq)} 条"
        f"{'（缓存兜底）' if stale else ''}（已同步 data/news.js）")
    return 0 if uniq else 1


if __name__ == "__main__":
    sys.exit(main())
