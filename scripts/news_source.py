# -*- coding: utf-8 -*-
"""
news_source.py — 校园通资讯的抓取与字段校验（被命令行脚本和本地接口共用）

职责边界：
  1. 解析服务端直出的 HTML（博达 CMS），不依赖私有接口；
  2. 把解析结果按字段规则校验，不合格的条目单独记在 rejected 里，不静默丢弃；
  3. 失败时抛出可读的错误，由调用方决定是否回退缓存。

字段规则见 docs/api.md，改规则时两边要一起改。
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "news.json"
OUT_PATH = ROOT / "data" / "news.json"
CACHE_PATH = ROOT / "data" / "news-cache.json"
NEWS_JS = ROOT / "data" / "news.js"

CST = timezone(timedelta(hours=8))

# 栏目号 -> 中文分类（info/{栏目}/{文章}.htm）
COLUMN_MAP = {
    "1003": "校园新闻",
    "1018": "教务",
    "1019": "科研",
    "1020": "行政",
    "1021": "学工",
    "1022": "校园",
    "1032": "信息化",
}

# 分类白名单：不在表里的分类一律拒绝，避免页面上出现来路不明的标签
CATEGORY_WHITELIST = (
    "校园新闻", "教务", "科研", "行政", "学工", "校园", "信息化",
    "通知", "讲座", "活动", "公示",
)

# 只接受校内站点的链接，防止解析异常时把外站地址放进页面
ALLOWED_HOSTS = {"nbw.sztu.edu.cn", "www.sztu.edu.cn", "sztu.edu.cn"}
ALLOWED_DOMAIN = "sztu.edu.cn"

MIN_TITLE, MAX_TITLE = 4, 120
MAX_SUMMARY = 200


def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


def load_config(path: Path | str | None = None) -> dict:
    p = Path(path) if path else CONFIG_PATH
    with open(p, encoding="utf-8") as f:
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
    last_err: Exception | None = None
    for attempt in range(1, int(cfg.get("retries", 3)) + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=cfg.get("timeout_seconds", 15)) as resp:
                raw = resp.read()
            for enc in ("utf-8", "gb18030"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="ignore")
        except Exception as e:  # noqa: BLE001
            last_err = e
            wait = float(cfg.get("retry_backoff_seconds", 2)) * attempt
            if attempt < int(cfg.get("retries", 3)):
                time.sleep(wait)
    raise last_err  # type: ignore[misc]


def strip_tags(s: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    # 正文常被逐字套 <span>，会留下"数 字化"这类字间空格 → 去掉汉字之间的空格
    return re.sub(r"(?<=[\u4e00-\u9fa5]) (?=[\u4e00-\u9fa5])", "", s)


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

        title_attr = re.search(r'title="([^"]{4,})"', m.group(0))
        inner_text = strip_tags(inner)
        cat_tag = re.search(r"[\[【]([^\]】]{1,6})[\]】]", inner_text)
        category = cat_tag.group(1) if cat_tag else COLUMN_MAP.get(column, source_name)

        text_wo_cat = re.sub(r"[\[【][^\]】]{1,6}[\]】]", " ", inner_text)
        text_wo_date = DATE_RE.sub(" ", text_wo_cat).strip()
        title = (title_attr.group(1).strip() if title_attr else text_wo_date)
        title = unescape(re.sub(r"\s+", " ", title)).strip()
        if len(title) < MIN_TITLE:
            continue

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
    text = re.sub(r"^(发布(时间|者)?|来源|点击数|作者|编辑)[：:]\s*[\w\-\s:：]+", "", text)
    return text[:limit].strip() + ("…" if len(text) > limit else "")


def validate_item(item: dict) -> str:
    """按字段规则校验一条资讯；返回空串表示通过，否则返回给使用者看的原因。"""
    title = (item.get("title") or "").strip()
    if not title:
        return "标题为空"
    if len(title) < MIN_TITLE:
        return f"标题过短（少于 {MIN_TITLE} 字）"
    if len(title) > MAX_TITLE:
        return f"标题过长（超过 {MAX_TITLE} 字）"

    url = (item.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return "链接不是 http(s) 绝对地址"
    host = (urlsplit(url).hostname or "").lower()
    if not (host == ALLOWED_DOMAIN or host.endswith("." + ALLOWED_DOMAIN)):
        return f"链接域名不在白名单：{host or '空'}"

    date = (item.get("date") or "").strip()
    if date:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date):
            return f"日期格式应为 YYYY-MM-DD，实际为「{date}」"
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return f"日期不存在：{date}"

    category = (item.get("category") or "").strip()
    if category and category not in CATEGORY_WHITELIST:
        return f"分类不在白名单：{category}"

    return ""


def clean(item: dict) -> dict:
    """输出前统一裁剪：去空白、截断摘要、按白名单补分类。"""
    out = {
        "title": (item.get("title") or "").strip(),
        "url": (item.get("url") or "").strip(),
        "date": (item.get("date") or "").strip(),
        "category": (item.get("category") or "").strip() or COLUMN_MAP.get(item.get("column", ""), "校园新闻"),
        "column": item.get("column", ""),
        "source": item.get("source", ""),
        "summary": (item.get("summary") or "").strip()[:MAX_SUMMARY],
    }
    return out


def sort_key(item: dict) -> str:
    return item.get("date") or "0000-00-00"


def fetch_all(cfg: dict, max_items: int = 30, with_details: bool = True,
              previous_items: list[dict] | None = None, log=print) -> dict:
    """抓取全部源，返回 {items, errors, rejected, fetched_at}。

    previous_items 用来复用旧摘要，避免每次刷新都重抓详情页（也少打源站）。
    """
    delay = float(cfg.get("request_delay_seconds", 0.8))
    raw: list[dict] = []
    errors: list[str] = []

    for src in cfg.get("sources", []):
        if not src.get("enabled", True):
            continue
        log(f"· 抓取「{src['name']}」：{src['url']}")
        try:
            html = http_get(src["url"], cfg)
            got = parse_list(html, src["url"], src["name"])
            log(f"  解析到 {len(got)} 条")
            raw.extend(got)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{src['name']}: {e}")
            log(f"  ! 失败：{e}")
        time.sleep(delay)

    uniq, seen = [], set()
    for it in sorted(raw, key=sort_key, reverse=True):
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)
    uniq = uniq[:max_items]

    # 字段校验：不合格的进 rejected，附带原因，方便在报告里交代
    accepted, rejected = [], []
    for it in uniq:
        reason = validate_item(it)
        if reason:
            rejected.append({"title": (it.get("title") or "")[:60], "url": it.get("url", ""), "reason": reason})
            continue
        accepted.append(clean(it))
    if rejected:
        log(f"  ! 拒绝 {len(rejected)} 条不合规数据")

    # 详情摘要：先用旧缓存补（不发请求），缺的再抓（限条数、限频率）
    if accepted:
        old = {i.get("url"): i.get("summary", "") for i in (previous_items or [])}
        for it in accepted:
            if not it.get("summary") and old.get(it["url"]):
                it["summary"] = old[it["url"]]

    if with_details and accepted:
        limit = int(cfg.get("detail_limit", 12))
        summary_len = int(cfg.get("summary_length", 110))
        need = [it for it in accepted if not it.get("summary")][:limit]
        if need:
            log(f"· 补摘要 {len(need)} 条（间隔 {delay}s）")
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

    return {
        "items": accepted,
        "errors": errors,
        "rejected": rejected,
        "fetched_at": now_iso(),
    }


def build_payload(result: dict, cfg: dict, max_items: int) -> dict:
    return {
        "updated_at": result["fetched_at"],
        "stale": False,
        "count": len(result["items"]),
        "errors": result.get("errors", []),
        "rejected": result.get("rejected", []),
        "sources": [s["url"] for s in cfg.get("sources", []) if s.get("enabled", True)],
        "items": result["items"],
    }


def write_payload(payload: dict) -> None:
    """落盘两份：给接口/命令行读的 json，给静态版内嵌的 js。"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    NEWS_JS.write_text(
        "window.NEWS_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    if payload.get("items"):
        CACHE_PATH.write_text(
            json.dumps({"items": payload["items"], "fetched_at": payload["updated_at"]},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def read_payload() -> dict | None:
    if OUT_PATH.exists():
        try:
            return json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None
