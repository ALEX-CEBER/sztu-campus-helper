@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SZTU Campus Helper

rem 找一个能用的 Python：PATH 里的 python / py，最后退回本机已知路径
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (
  where py >nul 2>nul && set "PY=py"
)
if not defined PY set "PY=C:\Users\you\.workbuddy\binaries\python\versions\3.13.12\python.exe"

echo ============================================
echo  SZTU 校园办事万事屋
echo  页面 http://localhost:8000/
echo  接口 http://localhost:8000/api/news
echo  关掉这个窗口即停止服务
echo ============================================
echo.

%PY% server.py --port 8000 --open
pause
