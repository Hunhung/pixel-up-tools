# pixel-up-tools

做抖音 / 剪映「画质逐档升级」效果的两套小工具：一个是在浏览器里实时操作的画质菜单，一个是把视频批量做成画质阶梯的命令行脚本。

## 目录

- `quality-menu/` — 画质菜单（最终交互版 + 早期静态版 + 历史渲染脚本）
- `pixel-ladder/` — 画质阶梯生成器（Python 脚本 + 拖拽 BAT + 效果示例）

## 一、画质菜单 · 交互版（最终版）

打开 `quality-menu/画质菜单_交互版.html`（Chrome / Edge），一个 HTML 就是完整工具：

1. 点「导入视频」或直接把视频拖进页面；
2. 左侧面板可调每档像素强度、鼠标描边 / 大小、背景色、菜单四档文字；
3. 点画面上的下拉框展开菜单，选 240p / 480p / 720p / 1080p，视频会实时变糊或变清晰；按住菜单可拖动位置；
4. 点「导出画面（含菜单+鼠标）」，3 秒倒数后开始录制，期间正常操作即可，全程会被录进去；导出完成自动保存到浏览器下载文件夹。

快捷键：`H` 隐藏/显示面板 · `1`–`4` 快切画质 · `空格` 播放/暂停 · `←/→` ±5 秒 · 菜单展开后 `↑↓` + `Enter` 选择。

**导出要带声音就不要勾「静音」。** 鼠标手型图已经 base64 内嵌在 HTML 里，不需要额外文件。

> `mp4-muxer.js` 是导出 MP4 的依赖，**必须和 HTML 放在同一目录**（本仓库已提供）；`mp4-muxer.LICENSE.txt` 是它的许可证。

## 二、画质阶梯生成器

把一条正常视频做成 240P 糊 → 360P → 480P → 原画逐级升档的效果。

- Windows：把视频文件直接拖到 `pixel-ladder/一键画质阶梯.bat` 上；
- 命令行：`python pixel_ladder.py 输入视频.mp4`；
- 自定义档位：`python pixel_ladder.py 输入视频.mp4 --steps "240:2.5,360:2.5,480:3,1080:5"`（格式是 `清晰度:秒数`）；
- 关掉档位文字：`--labels off`。

`pixel-ladder/示例_画质阶梯.mp4` 是效果示例。

## 三、早期版本（留作迭代记录）

- `quality-menu/quality_menu.html`：最早的静态绿幕菜单，纯绿背景方便剪映色度抠图；
- `quality-menu/render.sh`：用 Edge 无头截图逐帧合成绿幕 MP4 的历史脚本，在 Git Bash / WSL 下运行。默认 Edge 路径是 Windows 常见安装位置，可设置环境变量 `EDGE` 覆盖，例如 `EDGE="/path/to/msedge.exe" ./render.sh`；
- `quality-menu/绿幕_画质菜单.mp4`：早期脚本生成的成片示例。

新项目直接用最终交互版即可，这几个主要是留存迭代过程。

## 依赖安装（自己装，不随仓库提供）

| 依赖 | 用途 | 说明 |
|---|---|---|
| Chrome / Edge | 交互版 | 需要支持 canvas `captureStream` 的现代版本 |
| Python 3.x | 画质阶梯 | [python.org](https://www.python.org/downloads/) |
| ffmpeg | 画质阶梯 | [gyan.dev 构建](https://www.gyan.dev/ffmpeg/builds/)，解压后把 `bin` 目录加入 PATH。脚本会先找同目录 `ffmpeg/bin`，再找 PATH |
| Microsoft Edge | `render.sh` | 仅历史脚本需要 |

字体文件 `font.ttf`（约 1MB）和随工具自带的 `ffmpeg.exe`（64MB）有意不入库：前者有再分发版权风险，后者请按上表自行安装。
