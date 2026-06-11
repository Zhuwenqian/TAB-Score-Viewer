# TAB Score Viewer - 万能吉他谱查看器

[English](#english) | **中文**

一个功能强大的吉他谱（TAB）查看器，支持多种格式文件浏览、自动滚动播放（30fps平滑）、速度曲线调节、文本标注、循环播放和音频合成。

## 功能特性

| 功能 | 说明 |
|------|------|
| **多格式支持** | PNG、JPG、JPEG、WEBP 图片格式；PDF 文档；GP3/GP4/GP5/GPX 吉他谱文件 |
| **GTP解析与渲染** | 完整解析 Guitar Pro 文件，六线谱渲染引擎（含18种技巧符号），支持音轨切换 |
| **音频播放** | FluidSynth 合成引擎，SoundFont 音色，支持全轨并轨/单轨播放/关闭音频三种模式，推弦(Pitch Bend)渐变效果 |
| **播放光标** | 红色竖线跟随播放进度移动，当前小节高亮显示 |
| **自动滚动播放** | 30fps固定帧率平滑滚动，时间驱动模式（与音乐节奏同步，密集音符区自动加快） |
| **速度控制** | 图片/PDF模式：1-500ms可调；GTP模式：由BPM自动驱动，隐藏手动控制 |
| **速度曲线编辑器** | 贝塞尔曲线可视化编辑，预设模板（渐快/渐慢/先慢后快等），适用于变速练习（图片/PDF模式） |
| **循环播放** | 不循环 / 全局循环 / A-B 区域循环三种模式 |
| **文本标注系统** | 双击谱面任意位置添加演奏技巧说明，支持颜色、字体大小、粗体等样式，悬停显示删除按钮 |
| **标注自动导入/导出** | 自动加载同名 `.anno.json` 文件，实时保存，支持分轨/分页 PNG/PDF A4导出（含标注） |
| **标注全局撤销重做** | Ctrl+Z 撤销 / Ctrl+Y 重做，最大50步深度 |
| **标注管理器** | 批量管理标注，支持新建/编辑/删除 |
| **点击跳转播放** | 单击谱面任意位置自动跳转并开始播放 |
| **页码导航** | PDF / 多图片模式底部显示页码输入框，直接跳转指定页面 |
| **鼠标滚轮** | 滚轮滚动谱面，Ctrl 加速 / Shift 精细控制 |
| **右键菜单** | 打开文件所在位置（Windows/Linux 兼容） |
| **GTP音轨选择** | 下拉菜单切换音轨，即时重渲染，分轨独立标注 |
| **深色主题** | 现代化深色 UI，自定义组件风格 |
| **键盘快捷键** | 空格播放/暂停、方向键调速、Ctrl+Z撤销/Ctrl+Y重做/ESC关闭 |

## 快速开始

### 环境要求

- Python 3.8+
- Windows / Linux / Docker

### 安装

```bash
# 1. 克隆或下载项目
cd "e:\Projects\TAB Score Viewer"

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖（使用国内镜像源）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 运行
python guitar_tab_viewer.py
```

### 使用方法

1. 启动程序后，点击「选择文件夹」按钮选择存放吉他谱的目录
2. 文件列表会显示所有支持的格式文件（PNG/JPG/WEBP/PDF/GP3-GP5/GPX）
3. 双击文件打开谱面查看器：
   - 单张图片：直接显示并播放
   - PDF：逐页渲染为图片拼接显示
   - 多张图片：按文件名排序后拼接连续显示
   - GTP 文件：完整解析渲染为六线谱图像，支持音频播放、音轨切换、播放光标
4. 使用工具栏和控制面板进行播放、调速、标注等操作

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `空格` | 播放 / 暂停 |
| `↑` | 向上翻动谱面 |
| `↓` | 向下翻动谱面 |
| `←` | 减慢速度 |
| `→` | 加快速度 |
| `Ctrl+Z` | 标注撤销 |
| `Ctrl+Y` | 标注重做 |
| `ESC` | 关闭当前窗口 |

### 鼠标操作

| 操作 | 功能 |
|------|------|
| 滚轮 | 滚动谱面（默认30px/步） |
| `Ctrl + 滚轮` | 快速滚动（100px/步） |
| `Shift + 滚轮` | 精细滚动（10px/步） |
| 单击谱面 | 跳转到点击位置并开始播放 |
| 双击空白处 | 新建文本标注 |
| 双击已有标注 | 编辑该标注 |
| 进度条拖动 | 跳转播放位置 |
| `Ctrl + 点击进度条` | 设置循环 A 点 |
| `Shift + 点击进度条` | 设置循环 B 点 |

## 项目结构

```
TAB Score Viewer/
├── guitar_tab_viewer.py      # 主程序
├── README.md                 # 项目说明文档（本文件）
├── requirements.txt          # Python 依赖列表
├── LICENSE                   # 许可证文件 (MPL 2.0)
├── config/
│   └── settings.json         # 用户设置（运行时自动生成）
├── data/
│   └── annotations/          # 旧版标注数据存储（JSON格式，兼容保留）
├── gtp_engine/               # GTP 解析与渲染引擎
│   ├── __init__.py           # 库入口
│   ├── audio/                # 音频模块
│   │   ├── midi_converter.py # MIDI事件转换器（含推弦Pitch Bend支持）
│   │   └── synth_engine.py   # FluidSynth合成引擎
│   ├── models/               # 数据模型（song/track/measure/beat/note）
│   ├── parser/               # GTP解析器
│   ├── renderer/             # 六线谱渲染器 + 布局引擎
│   └── utils/                # 常量定义
├── libfluidsynth-3.dll       # FluidSynth 动态库 (LGPL 2.1)
├── SDL3.dll                  # SDL3 动态库 (FluidSynth 依赖)
├── sndfile.dll               # libsndfile 动态库 (FluidSynth 依赖)
├── readme/                   # 项目文档
│   ├── 功能更新.md           # 功能更新记录
│   ├── 开发文档.md           # 开发技术文档
│   └── 实施文档.md           # 实施部署文档
└── venv/                     # Python 虚拟环境
```

## 技术栈

- **GUI框架**: PyQt5 (Qt for Python)
- **PDF处理**: PyMuPDF (fitz)
- **图片处理**: Pillow (PIL)
- **GTP解析**: pyguitarpro (Guitar Pro 文件解析)
- **音频合成**: pyfluidsynth (FluidSynth MIDI 合成引擎)
- **架构模式**: MVC 分离、观察者模式(信号槽)、工厂模式(Worker)、命令模式(撤销重做)
- **异步处理**: QThreadPool + QRunnable 多线程加载

## 依赖库

```
PyQt5>=5.15      # GUI框架
PyMuPDF>=1.23    # PDF解析与渲染
Pillow>=10.0     # 图片格式支持(WEBP等)
pyguitarpro>=0.11  # Guitar Pro 文件解析
pyfluidsynth>=1.4.0  # MIDI音频合成 (LGPL 2.1)
```

## 第三方组件许可证

### FluidSynth

本项目使用 [FluidSynth](https://github.com/FluidSynth/fluidSynth) 作为音频合成引擎。

- **许可证**: [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **仓库地址**: https://github.com/FluidSynth/fluidSynth
- **使用方式**: 预编译的 DLL 文件位于项目根目录（`libfluidsynth-3.dll`、`SDL3.dll`、`sndfile.dll`）
- **用途**: 将 MIDI 事件合成音频输出，用于 GTP 吉他谱的音频播放功能（含推弦渐变效果）

> FluidSynth 是一个开源的 MIDI 合成器，基于 SoundFont 技术，支持高质量的实时音频生成。

## 许可证

本项目采用 [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/) 许可证。

---

# English

A powerful Guitar TAB score viewer with multi-format support, 30fps smooth auto-scroll playback, speed curve control, text annotations, loop playback, and audio synthesis.

## Features

| Feature | Description |
|---------|-------------|
| **Multi-format** | PNG, JPG, JPEG, WEBP images; PDF documents; GP3/GP4/GP5/GPX Guitar Pro files |
| **GTP Parsing & Rendering** | Complete Guitar Pro file parser, TAB renderer with 18 technique symbols, track switching |
| **Audio Playback** | FluidSynth engine with SoundFont, All tracks / Single track / Mute modes, Pitch Bend gradual effect |
| **Playhead** | Red vertical line following playback progress, current measure highlight |
| **Auto-scroll** | 30fps fixed-rate smooth scrolling, time-driven (synced with music rhythm) |
| **Speed Control** | Image/PDF: 1-500ms range; GTP: BPM-driven, auto-hides manual controls |
| **Speed Curve Editor** | Bezier curve visualization with preset templates (Image/PDF mode only) |
| **Loop Playback** | No loop / Global loop / A-B region loop |
| **Text Annotations** | Double-click to add notes with color/font/bold styles, hover to show delete button |
| **Annotation Import/Export** | Auto-load `.anno.json`, real-time save, per-track/per-page PNG/PDF A4 export |
| **Global Undo/Redo** | Ctrl+Z / Ctrl+Y, max 50 steps |
| **Annotation Manager** | Batch management with create/edit/delete |
| **Click-to-Play** | Click anywhere on score to jump and start playback |
| **Page Navigation** | Page input box for PDF/multi-image mode |
| **Mouse Wheel** | Scroll with Ctrl (fast) / Shift (fine) modifiers |
| **Context Menu** | Open file location (Windows/Linux compatible) |
| **Track Selection** | Dropdown to switch tracks, instant re-render, per-track annotations |
| **Dark Theme** | Modern dark UI with custom components |
| **Keyboard Shortcuts** | Space play/pause, arrow keys, Ctrl+Z/Y undo/redo, ESC close |

## Quick Start

```bash
#Create virtual environment
python -m venv venv
# Activate virtual environment
.\venv\Scripts\activate   # Windows
source venv/bin/activate   # Linux/Mac
# Install requirements
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Run
python guitar_tab_viewer.py
```

## Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `↑` / `↓` | Scroll up / down |
| `←` / `→` | Slower / Faster |
| `Ctrl+Z` | Undo annotation|
| `Ctrl+Y` | Redo annotation |
| `ESC` | Close window |

## Tech Stack

- **GUI**: PyQt5
- **PDF**: PyMuPDF
- **Image**: Pillow
- **GTP Parsing**: pyguitarpro
- **Audio**: pyfluidsynth (FluidSynth MIDI synthesis engine)
- **Pattern**: MVC, Observer (signals), Factory (Workers), Command (undo/redo), Async (QThreadPool)

## License

This project is licensed under [MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

## Third-Party Components

### FluidSynth

This project uses [FluidSynth](https://github.com/FluidSynth/fluidSynth) as the audio synthesis engine.

- **License**: [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
- **Repository**: https://github.com/FluidSynth/fluidSynth
- **Usage**: Precompiled DLL files in project root (`libfluidsynth-3.dll`, `SDL3.dll`, `sndfile.dll`)
- **Purpose**: Convert MIDI events to audio output for GTP guitar score playback (with Pitch Bend gradual effect)
