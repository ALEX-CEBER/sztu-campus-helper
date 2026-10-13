@echo off
rem Push SZTU Campus Helper to GitHub (UTF-8)
rem Double-click this file. If a browser window opens, sign in and authorize.
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   推送到 GitHub: ALEX-CEBER/sztu-campus-helper
echo ============================================
echo.
echo [1/2] 正在推送（如弹出浏览器请登录并授权）...
git push -u origin main

if errorlevel 1 (
  echo.
  echo 第一次尝试失败，可能是校园网/代理导致证书校验失败。
  echo [2/2] 正在以跳过证书校验的方式重试...
  git -c http.sslVerify=false push -u origin main
)

if errorlevel 1 (
  echo.
  echo 推送失败。请检查：
  echo   1. 仓库是否已创建：https://github.com/ALEX-CEBER/sztu-campus-helper
  echo   2. 浏览器授权是否完成
  echo   3. 网络是否正常（可换手机热点重试）
) else (
  echo.
  echo 推送成功！打开看看：https://github.com/ALEX-CEBER/sztu-campus-helper
)
echo.
pause
