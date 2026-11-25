#!/usr/bin/env bash
# 把 quality_menu.html 逐帧截图 → 合成绿幕 MP4
set -e
cd "$(dirname "$0")"
# Edge 路径：Windows 常见安装位置，可用环境变量 EDGE 覆盖
EDGE="${EDGE:-/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
FF="../ffmpeg/bin/ffmpeg.exe"
FPS=30
DUR=6.8
N=$(awk "BEGIN{printf \"%d\", $FPS*$DUR+0.5}")

mkdir -p frames
URL_BASE=$(python -c "
from urllib.parse import quote
import os
p=os.path.abspath('quality_menu.html').replace(os.sep,'/')
print('file:///'+quote(p,safe='/'))")

echo "共 $N 帧"
for i in $(seq 0 $((N-1))); do
  t=$(awk "BEGIN{printf \"%.4f\", $i/$FPS}")
  f=$(printf "frames/frame_%04d.png" "$i")
  if [ ! -s "$f" ]; then
    "$EDGE" --headless=new --disable-gpu --hide-scrollbars \
      --window-size=1080,1920 --screenshot="$f" \
      "${URL_BASE}?t=${t}" >/dev/null 2>&1
  fi
  if [ $((i % 30)) -eq 0 ]; then echo "… $i / $N"; fi
done

echo "合成视频……"
"$FF" -hide_banner -loglevel error -y -framerate $FPS -i frames/frame_%04d.png \
  -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -movflags +faststart \
  绿幕_画质菜单.mp4
ls -lh 绿幕_画质菜单.mp4
echo DONE
