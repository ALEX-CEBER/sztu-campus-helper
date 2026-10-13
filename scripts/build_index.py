# -*- coding: utf-8 -*-
"""
build_index.py — 把 data/knowledge/*.md 解析成 data/qa.json
用法（在项目根目录执行）:
    python scripts/build_index.py
Windows 若未配 python 别名:
    C:\\Users\\you\\.workbuddy\\binaries\\python\\versions\\3.13.12\\python.exe scripts/build_index.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
OUTPUT = ROOT / "data" / "qa.json"


def parse_file(path: Path):
    text = path.read_text(encoding="utf-8")
    items = []
    # 按 "## 问：" 分块
    blocks = re.split(r"\n##\s*", text)[1:]
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        q = lines[0].strip()
        q = re.sub(r"^问[:：]?\s*", "", q)
        category, keywords, answer_lines, source = "", [], [], ""
        in_answer = False
        for line in lines[1:]:
            s = line.strip()
            if s.startswith("分类："):
                category = s.replace("分类：", "").strip()
            elif s.startswith("关键词："):
                keywords = [k.strip() for k in s.replace("关键词：", "").split("，") if k.strip()]
            elif s.startswith("答案："):
                in_answer = True
            elif s.startswith("来源："):
                source = s.replace("来源：", "").strip()
                in_answer = False
            elif in_answer:
                answer_lines.append(line)
        answer = "\n".join(answer_lines).strip()
        if q and answer:
            items.append({
                "id": f"{path.stem}-{len(items)+1:02d}",
                "file": path.name,
                "question": q,
                "category": category,
                "keywords": keywords,
                "answer": answer,
                "source": source,
            })
    return items


def main():
    all_items = []
    for md in sorted(KNOWLEDGE_DIR.glob("*.md")):
        items = parse_file(md)
        print(f"{md.name}: {len(items)} 条")
        all_items.extend(items)
    OUTPUT.write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"共 {len(all_items)} 条 -> {OUTPUT.relative_to(ROOT)}")

    # 额外生成 qa.js：把数据内嵌成 JS 变量，这样双击 index.html（file://）也能用
    JS = ROOT / "data" / "qa.js"
    JS.write_text(
        "window.QA_DATA = " + json.dumps(all_items, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"已生成内嵌数据 -> {JS.relative_to(ROOT)}（双击网页也能提问）")


if __name__ == "__main__":
    main()
