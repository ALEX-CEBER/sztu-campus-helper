# 版本迭代记录（CHANGELOG）

> 用途：写周报/大报告时直接抄这一页。每个版本 = 一次 commit + 一个 tag，
> 报告里的"完成与验收""本周做了什么"都能在这里找到原文。
> 规则（AI 助手请遵守）：每次完成功能改动后，**必须**在本文件顶部追加一条，`git tag` 打版本号。

格式：`## vX.Y.Z · 日期 · 对应报告` → 变更内容 → 验收方式 → commit

---

## v0.4.0 · 2026-11-09 · 对应报告 R3（接口与数据）
**校园资讯改为实时接口 + 界面视觉升级**

- 🔌 **本地服务 `server.py`**：同源静态页 + `GET /api/news`，缓存 60 秒、过期后台刷新、
  `?force=1` 当场抓；约定写入 `docs/api.md`（请求/成功/失败/字段规则/错误码）
- 🧩 **抓取逻辑拆到 `scripts/news_source.py`**：解析、字段校验（标题长度、链接域名白名单、
  日期真实性、分类白名单）、摘要复用；`fetch_news.py` 变薄，命令行与接口共用同一套规则
- ✅ **字段校验可复核**：新增 `scripts/validate_news.py` + `tests/fixtures/bad_items.json`，
  违规条目进 `rejected` 并给出原因，不写进 `items`
- 🖥 **前端 `web/news.js` 重写**：打开页面、切标签、点刷新、切回前台（30s）、停留轮询（90s）
  都会重新请求；实时/离线快照两种徽标；红黄提示条区分「接口挂了」与「显示旧缓存」
- 🎨 **界面升级**：新的浅色配色与留白、毛玻璃顶栏、分段标签、搜索框聚焦环、
  卡片左侧渐变色条、资讯双列布局、分类配色徽标、骨架屏、宽屏「今日速览」侧栏
- 🚀 **入口调整**：`start.bat` 改为启动 `server.py`（自动选 python/py 并开浏览器），
  单文件版与 Pages 版仍保留内嵌快照，退化为「离线快照」而不是白屏
- ⚙️ **参数调整**：`request_delay_seconds` 0.8→0.5、`detail_limit` 12→8，一次刷新约 6 秒
- 🐛 **修复**：后台刷新会丢掉旧摘要（只在前台刷新时复用）→ 摘要复用提前到校验之后

**验收**：`curl /api/news?max=3` 返回 200 且 `updated_at` 为当前时间；
无缓存+源站不可达返回 502 `CRAWL_FAILED`；有缓存时返回 200 `stale=true` + `warning`；
重启服务后 `updated_at` 与摘要不变（读 `data/news.json`）；`validate_news.py` 对样例拒绝 4/5 条；
桌面 1200px 与手机 375px 无横向溢出（`scrollWidth == clientWidth`）。

---

## v0.3.0 · 2026-10-28 · 对应报告 R3/R4（功能扩展）
**新增「校园资讯」模块：自动同步校园通**

- 📰 **数据获取**：解析校园通（博达 CMS，服务端直出 HTML）列表页
  `https://nbw.sztu.edu.cn/`（通知）与 `/xyxw.htm`（新闻），字段
  `title / date / category / summary / url / column / source`；
  不用浏览器直连（跨域 + 反爬 + 无兜底），改为**构建时抓取**
- 🤖 **抓取脚本** `scripts/fetch_news.py`：3 次指数退避重试、0.8s 请求间隔、UA 标识项目、
  详情页补摘要（≤12 条）、缓存 `data/news-cache.json`、全失败时 stale 兜底、
  `--offline` / `--max` 参数
- ⚙️ **配置** `config/news.json`：源地址、`max_items`、超时、重试、间隔、摘要长度等 10 项
- 🖥 **前端** `web/news.js`：顶部「办事问答 / 校园资讯」切换、分类筛选、相对时间（今天/昨天/N 天前）、
  整卡跳原文（`target=_blank` + `noopener`）、刷新、失败兜底卡片、`#news` 与 `?view=news` 直达
- 🎨 **样式**：资讯头部白卡（标题/来源/更新时间/刷新/分类）+ 资讯卡片 + 640px 移动端适配
- ⏱ **定时同步**：`.github/workflows/sync-news.yml`（每 6 小时 + 手动触发，自动提交并重建 Pages 版）；
  本地一键 `同步校园资讯.bat`
- 📄 **文档** `docs/校园资讯模块说明.md`：数据获取方式、字段定义、更新与兜底链、配置表、合规说明
- 🐛 **修复（真实踩坑）**：`news.js` 的颜文字 `(´･_･`)` 中含反引号，提前终止模板字符串
  → 整个脚本语法错误、资讯视图切不过去；已改文案并加 `node --check` 校验步骤

**验收**：抓取 29 条（16 通知 + 21 新闻，去重）；桌面/移动双截图检查；
`document.scrollWidth == clientWidth` 确认无横向溢出；单机版 2.1MB 全内嵌。

> 版本号说明：跳过 v0.2.x —— v0.2.0 是已被回滚的界面实验版（存于 `backup/apple-v0.2.0`）。

---

## v0.1.4 · 2026-10-13 · 对应报告 R1（工程化里程碑）
**代码首次推送到 GitHub + Pages 就绪**

- ☁️ 仓库上线：https://github.com/ALEX-CEBER/sztu-campus-helper（30 个文件）
- 🔑 通道：校园网封 22 端口且代理破坏 HTTPS 证书校验 → 改用 **SSH over 443**（`~/.ssh/config`）
- 🏷️ 版本标签 v0.1.0~v0.2.0 已推送（Releases 可对照每次迭代）
- 📄 生成 `docs/index.html`（Pages 部署版，2.10MB 单文件），README 补全仓库与在线预览链接
- 📝 新增 `docs/GitHub提交指南.md`（建仓库 / Pages / zip 打包 / 常见坑）

**验收**：`git ls-remote origin` 可见 main 与 4 个 tag；仓库页面可浏览全部源码。
**commit**：`83532df`

---

## v0.1.3 · 2026-10-13 · 对应报告 R1（用户反馈驱动的回滚）
**撤销 v0.2.0 界面改版与看板娘动效**

- ↩️ **回滚到 v0.1.2**：用户反馈"不喜欢这版风格" → 恢复原界面与静态看板娘
  （移除 `web/mascot.js`、`docs/index.html`；`index.html` / `style.css` / `app.js` 回到 v0.1.2）
- 💾 **未丢失**：v0.2.0 完整保存在分支 `backup/apple-v0.2.0`，日后可 `git checkout backup/apple-v0.2.0 -- web/` 取回参考
- ✅ **保留无害改进**：`docs/GitHub提交指南.md`、`build_standalone.py` 的 `--pages` 参数
  与"mascot.js 可选内联"（脚本现在兼容有/无动效两种版本）
- 🔁 重跑 `build_standalone.py` 生成旧版单机版（2.10MB，Q 版看板娘保留）

**验收**：单机版无 `window.Mascot`、无 `.eye` 元素；检索功能与 Q 版立绘正常。
**经验（报告可用）**：① git 让"不喜欢就撤回"变成一条命令的事；
② 风格类改动应先出预览确认再正式合入。

---

## v0.1.2 · 2026-10-13 · 对应报告 R1（二次元元素迭代）
**看板娘 v2：Q 版形象升级**

- 🎨 以用户提供的参考立绘为原型，用图像模型图生图生成 **Q 版看板娘 v2**
  （白发蓝瞳、深蓝礼帽燕尾服、水花泡泡元素、蓝色小海豹伙伴），替换 `assets/mascot.png`
- 📦 旧版立绘保留为 `assets/mascot-v1.png`（可对比、可回滚）
- 🔧 重建单机版：`dist/SZTU校园办事万事屋.html` 体积 2.96MB → **2.10MB**（新图更小）

**验收**：打开网页/单机版，左上角立绘已更换为 Q 版形象。
**commit**：见 `git log v0.1.2`

---

## v0.1.1 · 2026-10-13 · 对应报告 R1（含"修复"章节）
**中文检索失效修复 + 单机版分发**

- 🐛 **修复**：中文整句查询永远搜不到（原逻辑把整句当一个字符串做 `includes`）
  - 新增 `web/search-core.js`：2/3-gram 切分 + 剥离"怎么/如何/吗"等疑问词提取实词加权 + 同义词表 + 停用词 + 相关度阈值
  - 新增 `scripts/test_search.js`：20 条真实问法回归测试
- 🐛 **修复**：预览面板/双击打开时 `../data/qa.json` 加载失败
  - `build_index.py` 额外生成 `data/qa.js`，数据内嵌进页面
- ✨ **新增**：`scripts/build_standalone.py` → `dist/SZTU校园办事万事屋.html` 单文件版（2.9MB，全内嵌、断网可用）
- 🎨 **新增**：无结果时推荐热门问题、分类气泡可点、"含待核实"黄色角标、XSS 转义

**验收**：`node scripts/test_search.js` → 命中率 **20/20 = 100%**，首条结果 20/20 正确；双击单机版可正常提问。
**commit**：`0fd2259`

---

## v0.1.0 · 2026-10-13 · 对应报告 R1（立项与首次运行）
**项目立项 + 骨架 + 可运行原型**

- ✨ 定题：校园办事问答（含助手） → 「SZTU 校园办事万事屋 · 二次元问答台」
- ✨ 知识库：`data/knowledge/*.md` 六类共 **31 条**（教务/宿舍/图书馆/校园卡/奖助/新生），含 `[待核实]` 数据质量机制
- ✨ 构建脚本 `scripts/build_index.py`：Markdown → `data/qa.json`（数据与程序分离）
- ✨ 前端 `web/`：原生 HTML/CSS/JS 关键词打分检索问答页（零框架、零依赖）
- 🎨 二次元元素：AI 生成看板娘「深小技」立绘 `assets/mascot.png` + 拟人化文案
- 🔧 环境：Git v2.55 全局配置、SSH 密钥、仓库初始化、首次提交（17 文件）
- 📝 文档：`README.md`、`AGENTS.md`（AI 项目规则）、`docs/Git使用说明.md`、`docs/报告规划.html`（已导出 PDF）

**验收**：`python -m http.server` 本地访问 index.html / qa.json / mascot.png 全部 HTTP 200；
`git log` 可见首次提交 `519fccf`。
**commit**：`519fccf`（文档补充 `49dca7f`）

---

### 版本规划（后续按此推进，写报告时对照）
| 版本 | 对应报告 | 计划内容 |
|---|---|---|
| v0.2.0 | R2 | 需求问卷 + 知识库扩到 ≥60 条 + 分类筛选 |
| v0.3.0 | R3 | 移动端适配、深色模式、无结果引导优化 |
| v0.4.0 | R4 | 同义词扩充、拼音/错别字容错、命中率实验 |
| v0.5.0 | R5 | 接入校内 AI 模型（LLM 兜底 + 降级策略） |
| v1.0.0 | R6 / 大报告 | GitHub Pages 上线、测试报告、演示视频 |
