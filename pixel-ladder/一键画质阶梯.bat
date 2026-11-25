@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if "%~1"=="" goto noarg

set PY=
where python >nul 2>nul
if not errorlevel 1 set PY=python
if not defined PY (
  where py >nul 2>nul
  if not errorlevel 1 set PY=py -3
)
if not defined PY goto nopy

echo.
echo ============================================
echo  画质阶梯：240P -^> 360P -^> 480P -^> 原画
echo ============================================
echo.
%PY% "%~dp0pixel_ladder.py" "%~1"
echo.
echo 渲染结束，按任意键关闭。
pause >nul
exit /b

:noarg
echo.
echo 把要做画质阶梯的视频文件，直接拖到本文件上松开即可。
echo.
echo 想改档位时长：右键本文件 - 编辑，把下面这行的 --steps 改掉。
echo 默认 240:2.5,360:2.5,480:3,1080:5（数字是「清晰度:秒数」）
echo.
pause >nul
exit /b

:nopy
echo.
echo [错误] 没找到 Python。装一个 Python 3 后重试，或在命令行里手动运行 pixel_ladder.py
echo.
pause >nul
exit /b
