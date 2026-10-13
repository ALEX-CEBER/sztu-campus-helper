@echo off
rem SZTU Campus Helper - quick start (English comments to avoid encoding issues)
rem Usage: double-click this file. It starts a local server and opens the page.
chcp 65001 >nul
cd /d "%~dp0"
echo Starting local server at http://localhost:8000/web/ ...
start "" "http://localhost:8000/web/index.html"
python -m http.server 8000
pause
