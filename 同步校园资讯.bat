@echo off
rem Sync campus news then rebuild standalone page and push (UTF-8)
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   同步校园资讯（来源：深圳技术大学校园通）
echo ============================================
echo.

echo [1/3] 抓取资讯...
python scripts/fetch_news.py
if errorlevel 1 (
  echo 抓取失败，将使用上次缓存（data/news-cache.json）
)

echo.
echo [2/3] 重建网页（单机版 + Pages 版）...
python scripts/build_standalone.py
python scripts/build_standalone.py --pages

echo.
echo [3/3] 提交并推送...
git add data/news.json data/news.js docs/index.html
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "同步：校园资讯更新"
  git push
  echo 已推送。
) else (
  echo 资讯无变化，无需提交。
)

echo.
echo 完成。可双击 dist\SZTU校园办事万事屋.html 查看。
pause
