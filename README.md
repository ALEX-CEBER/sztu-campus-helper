# SZTU 校园办事万事屋 · 二次元问答台

AI 氛围编程（Vibe Coding）公选课学期课题 · **校园办事问答（含助手）**

[![GitHub](https://img.shields.io/badge/GitHub-ALEX--CEBER%2Fsztu--campus--helper-181717?logo=github)](https://github.com/ALEX-CEBER/sztu-campus-helper)

把学校散落在各官网/通知里的办事流程（教务、宿舍、图书馆、校园卡、奖助、新生问题）
整理成一个可以**提问 → 秒回答案**的网页问答台，配有二次元看板娘"深小技"。

## ✨ 特性（当前迭代）
- 离线优先：不依赖大模型也能秒查（关键词打分检索）
- 数据与程序分离：知识库是 `data/knowledge/*.md`，构建脚本生成 `data/qa.json`
- 二次元元素：看板娘立绘 + 分类气泡 + 拟人化文案
- AI 增强预留：校内模型接口（仅上课当晚开放）作为检索零命中时的兜底

## 🚀 怎么打开（任选）

**① 最省事：双击 `dist/SZTU校园办事万事屋.html`**
单文件版——CSS/JS/知识库/看板娘全内嵌，2.9MB，不需要服务器、断网也能用、可直接发给同学。
> 改了知识库后要重新生成：`python scripts/build_standalone.py`

**② 开发模式（改代码时用）**
- 双击 `start.bat`，或命令行 `python -m http.server 8000` → 访问 `http://localhost:8000/web/`
- VS Code 装 Live Server 插件，右键 `web/index.html` → Open with Live Server

> 说明：知识库已同时生成 `data/qa.js` 内嵌数据，所以直接双击 `web/index.html` 也能提问；
> 只有在预览工具不支持上级目录路径时才需要 ① 或 ②。

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

## 👤 作者
- GitHub：[ALEX-CEBER](https://github.com/ALEX-CEBER)
- 深圳技术大学 · 工程物理学院 · 光电信息科学与工程 董子晔
- 
- 课程：AI 氛围编程（Vibe Coding）公选课 · 2026 秋
- 仓库：https://github.com/ALEX-CEBER/sztu-campus-helper
- 线上预览（GitHub Pages）：https://alex-ceber.github.io/sztu-campus-helper/
> 项目规则见 `AGENTS.md`，版本记录见 `CHANGELOG.md`。
