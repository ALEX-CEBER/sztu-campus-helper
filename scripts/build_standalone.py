# -*- coding: utf-8 -*-
"""
build_standalone.py — 生成"单机版单文件网页" dist/SZTU校园办事万事屋.html
把 CSS / JS / 知识库数据 / 看板娘图片全部塞进一个 HTML：
双击就能用、发给同学能用、微信传过去也能用，不需要服务器。

用法：python scripts/build_standalone.py
"""
import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
OUT = DIST / "SZTU校园办事万事屋.html"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main():
    html = read(WEB / "index.html")

    # 1) CSS 内联
    css = read(WEB / "style.css")
    html = html.replace('<link rel="stylesheet" href="style.css" />', f"<style>\n{css}\n</style>")

    # 2) JS 内联（顺序：数据 → 检索核心 → 页面逻辑）
    qa_js = read(ROOT / "data" / "qa.js")
    core = read(WEB / "search-core.js")
    # 去掉 Node 导出段，浏览器不需要
    core = re.sub(r"\nif \(typeof module.*?\n\}\n", "\n", core, flags=re.S)
    app = read(WEB / "app.js")
    scripts = f"<script>\n{qa_js}\n{core}\n{app}\n</script>"
    html = re.sub(
        r'<script src="\.\./data/qa\.js"></script>\s*<script src="search-core\.js"></script>\s*<script src="app\.js"></script>',
        lambda _m: scripts, html)

    # 3) 看板娘图片转 base64 内联（保证完全离线可用）
    mascot = ROOT / "assets" / "mascot.png"
    if mascot.exists():
        b64 = base64.b64encode(mascot.read_bytes()).decode("ascii")
        html = html.replace(
            'src="../assets/mascot.png"',
            f'src="data:image/png;base64,{b64}"')

    OUT.write_text(html, encoding="utf-8")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"✔ 单机版已生成：{OUT}\n  大小：{size_mb:.2f} MB（含立绘，双击即用）")


if __name__ == "__main__":
    main()
