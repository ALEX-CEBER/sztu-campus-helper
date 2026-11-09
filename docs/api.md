# 校园资讯接口约定（/api/news）

> 主路径：**打开万事屋 → 切到「校园资讯」 → 看到最新校园通知 → 点进原文**。
> 这一步的关键就是本文件描述的接口。改字段或改错误码时，`server.py`、`web/news.js`、
> `docs/api.md` 三处必须一起改，报告里也以本文件为准。

## 1. 请求

| 项 | 内容 |
|---|---|
| 方法 / 路径 | `GET /api/news` |
| 调用方 | 页面 `web/news.js`（同源 `fetch`，无需跨域） |
| 参数 `max` | 整数，1～50，默认 24；超过范围返回 400 |
| 参数 `force` | `0` / `1`，默认 `0`。`1` 表示跳过缓存、当场重新抓官网（页面「刷新」按钮用） |
| 缓存策略 | 缓存 60 秒内直接返回；超过 60 秒返回旧数据并在后台抓新的（响应里 `refreshing=true`） |

示例：

```
curl "http://localhost:8000/api/news?max=3"
curl "http://localhost:8000/api/news?max=3&force=1"
```

## 2. 成功（HTTP 200）

| 字段 | 类型 | 规则 |
|---|---|---|
| `ok` | bool | 固定 `true` |
| `version` | string | 服务版本，如 `v0.4.0` |
| `updated_at` | string | 抓取完成时间，ISO 8601 带时区，例 `2026-11-09T22:47:18+08:00` |
| `count` | int | 本次返回的条数，等于 `items.length`，≤ `max` |
| `items` | array | 资讯列表，按 `date` 倒序 |
| `stale` | bool | `true` 表示本次抓取失败、返回的是上次缓存 |
| `refreshing` | bool | `true` 表示服务端正在后台抓新数据，2 秒后可再请求 |
| `cache_age_seconds` | int\|null | 距上次成功抓取的秒数；无缓存时为 `null` |
| `warning` | object\|null | 兜底提示，结构见第 3 节 |
| `rejected` | array | 被字段校验拒绝的条目，元素形如 `{"title":"…","url":"…","reason":"分类不在白名单：广告"}`；正常为空数组 |
| `sources` | array | 本次启用的源地址，排查用 |

`items` 每一项：

| 字段 | 类型 | 规则 |
|---|---|---|
| `title` | string | 必填，去空白后 4～120 字，唯一性不要求（不同栏目可能同名） |
| `url` | string | 必填，`http(s)` 绝对地址，域名必须是 `sztu.edu.cn` 或其子域 |
| `date` | string | 可空；非空时必须是真实存在的 `YYYY-MM-DD` |
| `category` | string | 取值必须在白名单：校园新闻/教务/科研/行政/学工/校园/信息化/通知/讲座/活动/公示 |
| `summary` | string | 可空，≤200 字；只在抓取详情页成功后才有 |
| `column` | string | 校内 CMS 栏目号，如 `1018`，用于排查解析问题 |
| `source` | string | 来源栏目名，如「校园通知」 |

成功示例（字段齐全、内容已截断）：

```json
{
  "ok": true,
  "version": "v0.4.0",
  "updated_at": "2026-11-09T22:47:18+08:00",
  "count": 2,
  "stale": false,
  "refreshing": false,
  "cache_age_seconds": 18,
  "warning": null,
  "rejected": [],
  "items": [
    {
      "title": "关于征集第六批教育评价改革典型案例的通知",
      "url": "https://nbw.sztu.edu.cn/info/1018/52742.htm",
      "date": "2026-11-09",
      "category": "教务",
      "summary": "各单位：根据《广东省教育厅办公室关于征集第六批教育评价改革典型案例的通知》…",
      "column": "1018",
      "source": "校园通知"
    }
  ]
}
```

## 3. 失败

### 3.1 抓不到、也没有缓存 → HTTP 502

本组实际会发生：断网、校园网维护、校园通临时不可用、学校站点超时。

```json
{
  "ok": false,
  "error": {
    "code": "CRAWL_FAILED",
    "message": "校园通暂时连不上，也没找到本地缓存，请稍后再试",
    "detail": "校园通知: timed out"
  }
}
```

页面上的提示文字：**「接口没连上：…。当前显示 … 的离线快照，用 start.bat 启动本地服务即可实时更新。」**
（页面同时退到内嵌快照，不会白屏。）

### 3.2 抓不到、但有缓存 → HTTP 200 + `stale`

```json
{
  "ok": true,
  "stale": true,
  "count": 2,
  "warning": {
    "code": "CRAWL_FAILED",
    "message": "校园通暂时连不上，当前显示约 1 分钟前的缓存"
  }
}
```

页面上的提示文字：黄条 **「校园通暂时连不上，当前显示约 1 分钟前的缓存（CRAWL_FAILED）」**。

### 3.3 参数不合法 → HTTP 400

```json
{"ok": false, "error": {"code": "BAD_PARAM", "message": "参数 max 需要在 1～50 之间", "detail": "收到的 max=999"}}
```

### 3.4 路径不存在 → HTTP 404 `NOT_FOUND`

静态托管（例如只把 `web/` 传到网上）没有这个接口，页面会走 3.1 的兜底，
提示「接口没连上：接口返回 HTTP 404」。

## 4. 数据存在哪里

| 文件 | 作用 | 是否进版本库 |
|---|---|---|
| `data/news.json` | 最近一次成功抓取的结果，服务启动时读它，接口返回它 | 是 |
| `data/news-cache.json` | 同上，作为「上次成功」的备份 | 是 |
| `data/news.js` | 把同一份数据包成 `window.NEWS_DATA`，供单机版/静态页读 | 是 |
| `config/news.json` | 源地址、条数上限、超时、重试、请求间隔、摘要长度、UA | 是 |

三者由 `scripts/news_source.py` 的 `write_payload()` 一次写入，所以命令行抓取和接口抓取
不会出现两份数据不一致。**重启服务后数据还在**：启动时直接从 `data/news.json` 读入内存，
不需要重新联网。

## 5. 字段校验

`scripts/news_source.py` 的 `validate_item()` 在写盘前逐条检查，不合格的进 `rejected`，
不写进 `items`，也不会让整次抓取失败。命令行复核：

```
python scripts/validate_news.py data/news.json
python scripts/validate_news.py tests/fixtures/bad_items.json
```

拒绝原因文案（给使用者看的）：

| 情况 | 文案 |
|---|---|
| 标题缺失或全空白 | `标题为空` |
| 标题过短 / 过长 | `标题过短（少于 4 字）` / `标题过长（超过 120 字）` |
| 链接不是绝对地址 | `链接不是 http(s) 绝对地址` |
| 链接指向校外 | `链接域名不在白名单：example.com` |
| 日期格式错 | `日期格式应为 YYYY-MM-DD，实际为「2026/11/9」` |
| 日期不存在 | `日期不存在：2026-13-45` |
| 分类不在白名单 | `分类不在白名单：广告` |

## 6. 变更记录

| 版本 | 变更 |
|---|---|
| v0.4.0（2026-11-09） | 新增本接口：把「构建时抓一次」改为「页面每次打开/刷新都取一次，服务端缓存 60 秒」 |
