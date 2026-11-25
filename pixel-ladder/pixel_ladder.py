#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画质阶梯生成器 / pixel ladder
把一条正常视频做成「240P 糊 → 480P 稍清 → 原画」逐级升档的效果，用于抖音剪辑。

用法（命令行）：
    python pixel_ladder.py 输入视频.mp4
    python pixel_ladder.py 输入视频.mp4 --steps "240:2.5,360:2.5,480:3,1080:5"
    python pixel_ladder.py 输入视频.mp4 --labels off --blur 0.8

也可以直接把视频文件拖到「一键画质阶梯.bat」上。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_tool(name, required=True):
    exe = name + (".exe" if os.name == "nt" else "")
    cands = [
        os.path.join(HERE, "ffmpeg", "bin", exe),
        os.path.join(HERE, "ffmpeg", exe),
        os.path.join(HERE, exe),
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    p = shutil.which(name)
    if p:
        return p
    if required:
        sys.exit("[错误] 找不到 %s，请确认 tools\\ffmpeg\\bin\\ 下有它。" % name)
    return None


def probe_duration(ffprobe, path):
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except Exception:
        return None


def has_audio(ffprobe, path):
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=index", "-of", "csv=p=0", path],
            capture_output=True, text=True, check=True).stdout.strip()
        return bool(out)
    except Exception:
        return False


def media_info(ffmpeg, ffprobe, path):
    """没有 ffprobe 时，退回解析 ffmpeg -i 的 stderr。"""
    dur, aud = None, True
    if ffprobe:
        dur = probe_duration(ffprobe, path)
        aud = has_audio(ffprobe, path)
        if dur is not None:
            return dur, aud
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-i", path],
                           capture_output=True, text=True, errors="ignore")
        txt = r.stderr or ""
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", txt)
        if m:
            dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        aud = "Audio:" in txt
    except Exception:
        pass
    return dur, aud


def parse_steps(s):
    steps = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        h, sec = part.split(":")
        steps.append((int(h), float(sec)))
    if not steps:
        sys.exit("[错误] --steps 解析为空")
    return steps


def ff_path(p):
    """转成 ffmpeg 能吃的路径：正斜杠 + 转义盘符冒号"""
    p = os.path.abspath(p).replace("\\", "/")
    return p.replace(":", "\\:")


def build_cmd(ffmpeg, src, out, steps, ow, oh, fps, blur, labels, font,
              with_audio, total, crf_final, bitrate):
    parts = []
    seg_labels = []
    t = 0.0
    n = len(steps)
    for i, (h, sec) in enumerate(steps):
        start, end = t, t + sec
        t = end
        chain = [
            "trim=%.3f:%.3f" % (start, end),
            "setpts=PTS-STARTPTS",
            "fps=%d" % fps,
        ]
        # 最后一档永远按原画处理（1080P 只是标记，不再降分辨率）
        if h < oh and i < n - 1:  # 真正降分辨率档位：先降采样，再用最近邻放大 → 像素块
            chain.append("scale=-2:%d:flags=area" % h)
            chain.append("scale=%d:%d:force_original_aspect_ratio=increase:flags=neighbor"
                         % (ow, oh))
            chain.append("crop=%d:%d" % (ow, oh))
            if blur > 0:
                chain.append("gblur=sigma=%.2f" % blur)
        else:       # 最高清档
            chain.append("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos"
                         % (ow, oh))
            chain.append("crop=%d:%d" % (ow, oh))
        chain.append("setsar=1")
        chain.append("format=yuv420p")
        parts.append("[0:v]" + ",".join(chain) + "[v%d]" % i)
        seg_labels.append("[v%d]" % i)

    parts.append("".join(seg_labels) + "concat=n=%d:v=1:a=0[vcat]" % len(steps))

    vlabel = "vcat"
    if labels and font and os.path.isfile(font):
        t = 0.0
        extra = []
        for i, (h, sec) in enumerate(steps):
            if h < oh and i < n - 1:
                start, end = t, t + sec
                extra.append(
                    "drawtext=fontfile='%s':text='%dP':fontcolor=white@0.9:"
                    "fontsize=%d:x=w-tw-56:y=h-th-180:"
                    "borderw=3:bordercolor=black@0.6:"
                    "enable='between(t,%.2f,%.2f)'" % (ff_path(font), h, int(oh * 0.042), start, end)
                )
            t += sec
        if extra:
            parts.append("[vcat]" + ",".join(extra) + "[vfin]")
            vlabel = "vfin"

    fc = ";".join(parts)

    cmd = [ffmpeg, "-y", "-i", src, "-filter_complex", fc, "-map", "[%s]" % vlabel]
    if with_audio:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-an"]
    cmd += [
        "-t", "%.3f" % total,
        "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-b:v", bitrate, "-maxrate", "12M", "-bufsize", "16M",
        "-r", str(fps), "-movflags", "+faststart",
        out,
    ]
    return cmd


def main():
    ap = argparse.ArgumentParser(description="画质阶梯生成器")
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--steps", default="240:2.5,360:2.5,480:3,1080:5",
                    help="档位:时长，例如 240:2.5,360:2.5,480:3,1080:5")
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--blur", type=float, default=0.6, help="低清档的柔化强度，0=关闭")
    ap.add_argument("--labels", default="on", choices=["on", "off"])
    ap.add_argument("--font", default=os.path.join(HERE, "font.ttf"))
    ap.add_argument("--bitrate", default="8M")
    ap.add_argument("--yes", action="store_true", help="跳过素材时长确认")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    if not os.path.isfile(src):
        sys.exit("[错误] 找不到文件：%s" % src)

    ow, oh = [int(x) for x in args.size.lower().split("x")]
    steps = parse_steps(args.steps)
    total = sum(s for _, s in steps)

    ffmpeg = find_tool("ffmpeg")
    ffprobe = find_tool("ffprobe", required=False)

    dur, audio = media_info(ffmpeg, ffprobe, src)
    print("素材：%s" % os.path.basename(src))
    print("时长：%s 秒｜音轨：%s" % (("%.2f" % dur) if dur else "未知", "有" if audio else "无"))
    print("档位：%s｜总长：%.1f 秒｜输出：%dx%d@%dfps" % (
        " → ".join("%dP(%.1fs)" % (h, s) for h, s in steps), total, ow, oh, args.fps))

    if dur and total > dur + 0.05:
        print("[提醒] 片段总长 %.1fs 超过素材时长 %.2fs，超出的部分会黑屏。"
              "建议缩短 --steps 里的秒数。" % (total, dur))
        total = min(total, dur)
    if dur and total < dur - 1:
        print("[提醒] 只用了素材前 %.1f 秒（共 %.2fs）。" % (total, dur))

    out = args.output or os.path.splitext(src)[0] + "_画质阶梯.mp4"
    out = os.path.abspath(out)

    cmd = build_cmd(ffmpeg, src, out, steps, ow, oh, args.fps, args.blur,
                    args.labels == "on", args.font, audio, total,
                    None, args.bitrate)
    print("\n开始渲染……（时长越久越慢，13 秒的片子一般 10-30 秒）")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit("\n[失败] ffmpeg 返回 %d，把上面的报错发我。" % r.returncode)

    print("\n完成 → %s" % out)
    if os.path.getsize(out):
        print("大小：%.1f MB" % (os.path.getsize(out) / 1048576.0))


if __name__ == "__main__":
    main()
