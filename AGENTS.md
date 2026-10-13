# AGENTS.md — AI 助手项目规则（WorkBuddy / CodeBuddy 自动读取）

## 项目一句话
「SZTU 校园办事万事屋」：校园办事流程问答网页（离线检索优先 + 校内 LLM 兜底），二次元看板娘风格。

## 硬性约束（每次修改都要遵守）
1. **数据与程序分离**：答案只写在 `data/knowledge/*.md`；改完必须运行
   `python scripts/build_index.py` 重新生成 `data/qa.json`（qa.json 禁止手改）。
2. **离线优先**：核心问答不得依赖在线大模型（校内模型接口仅上课当晚开放、并发有限）。
   LLM 只做"检索零命中/答案润色"的增强层，必须有降级提示。
3. **不编造学校信息**：不确定的细节必须保留 `[待核实]` 标记并在来源列注明；禁止虚构电话、网址、办公室号。
4. **前端零依赖**：只用原生 HTML/CSS/JS，不引入 npm/框架（打包 zip < 10MB、可静态部署 GitHub Pages）。
5. **中文文案**：界面与注释用简体中文；代码文件保存为 UTF-8。
6. **每次改动后**：git add + commit，commit message 用中文一句话（如 `新增：图书馆分类 5 条问答`）。

## 常用命令
- 启动本地预览：`python -m http.server 8000` → http://localhost:8000/web/
- 重建知识库索引：`python scripts/build_index.py`
- Git 状态/提交：`git status` / `git add -A` / `git commit -m "..."` / `git push`

## 里程碑对照（勿超前实现，用于周报验收）
- W1-2 仓库+首次运行（当前）→ W3 数据扩充 → W4 前端美化 → W5 检索优化+LLM 接入 → W6 测试部署 → W7-8 交付
详细见 docs/报告规划.md。

## Git 教程
新人/新 AI 会话请先读 docs/Git使用说明.md。
