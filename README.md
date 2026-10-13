# SZTU 校园办事万事屋 · 二次元问答台

AI 氛围编程（Vibe Coding）公选课学期课题 · **校园办事问答（含助手）**

把学校散落在各官网/通知里的办事流程（教务、宿舍、图书馆、校园卡、奖助、新生问题）
整理成一个可以**提问 → 秒回答案**的网页问答台，配有二次元看板娘"深小技"。

## ✨ 特性（当前迭代）
- 离线优先：不依赖大模型也能秒查（关键词打分检索）
- 数据与程序分离：知识库是 `data/knowledge/*.md`，构建脚本生成 `data/qa.json`
- 二次元元素：看板娘立绘 + 分类气泡 + 拟人化文案
- AI 增强预留：校内模型接口（仅上课当晚开放）作为检索零命中时的兜底

## 🚀 本地运行（3 种方式任选）
1. 双击 `start.bat`（自动起服务器并打开浏览器）
2. 命令行：`python -m http.server 8000`，浏览器访问 `http://localhost:8000/web/`
3. VS Code 装 Live Server 插件，右键 `web/index.html` → Open with Live Server

> ⚠️ 不要直接双击 index.html 打开（file:// 会被浏览器拦截 fetch）

## 🛠 改完知识库后
```bash
python scripts/build_index.py   # 重新生成 data/qa.json，刷新网页即可
```

## 📁 目录结构
```
├── data/knowledge/   知识库 Markdown（答案在这里改）
├── data/qa.json      构建产物（勿手改）
├── scripts/          构建脚本
├── web/              前端页面
├── assets/           看板娘等素材
├── docs/             文档（Git 教程、报告规划）
├── reports/          每周报告 .md
└── start.bat         一键启动
```

## ⚠️ 数据声明
知识库条目为通用流程整理稿，标注 `[待核实]` 的内容以学校官方通知为准；
上线前需逐条核实并替换来源。

## 👥 团队
- 姓名-学号（登记表为准）
