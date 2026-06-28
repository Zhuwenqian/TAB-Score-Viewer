# -*- coding: utf-8 -*-
"""
============================================================
File: TAB Score Viewer.py / 文件名: TAB Score Viewer.py
Description: Universal Guitar TAB Score Viewer / 功能描述: 万能吉他谱查看器
             Multi-format viewing, playback, annotation, and export
             支持格式: PNG, JPG, JPEG, WEBP(image), PDF(document), GP3-GP5/GPX(GTP tablature)

Core Features / 核心功能:
  1. Multi-format score viewing with auto-scroll playback (350-700ms speed range)
     多格式吉他谱查看与自动滚动播放(速度范围350-700ms)
  2. Draggable progress bar + loop playback (no-loop/global-loop/A-B-region-loop)
     可拖动进度条 + 循环播放(不循环/全局循环/区域A-B循环)
  3. Speed curve editor - Bezier curve visualization with preset templates (image/PDF mode)
     速度曲线编辑器 - 贝塞尔曲线可视化编辑，含预设模板(图片/PDF格式)
  4. Score text annotation system - double-click to add/drag to move/custom styles
     谱面文本标注系统 - 双击添加/拖动移动/样式自定义
  5. Annotation import/export - auto-load .anno.json files, A4 PNG/PDF export, print to printer
     标注导入导出 - 自动加载同名.anno.json标注文件，A4尺寸PNG/PDF导出，打印到打印机
  6. Global undo/redo - Ctrl+Z/Y for all annotation operations (shared stack)
     全局撤销重做 - Ctrl+Z/Y统一撤销所有标注操作(画布+管理器共享栈)
  7. Page navigation - page input box for PDF/multi-image mode
     页码导航 - PDF/多图模式底部页码输入框直接跳转
  8. Mouse wheel scrolling - Ctrl-acceleration / Shift-fine-control support
     鼠标滚轮滚动 - 支持Ctrl加速/Shift精细控制
  9. Dark/Light theme UI + custom components (buttons/sliders/progress bar) + real-time switching
     深色/浅色主题UI + 自定义组件(按钮/滑块/进度条) + 实时主题切换
 10. Keyboard shortcuts - Space play/pause, arrow keys speed, Ctrl+Z/Y undo/redo, ESC close
     键盘快捷键 - 空格播放暂停/方向键调速/Ctrl+Z撤销/Ctrl+Y重做/ESC关闭
 11. GTP file full rendering - parse and render as tablature via ApolloTab library
     GTP文件完整渲染 - 基于ApolloTab库解析并渲染为六线谱图像
 12. Right-click open file location - context menu to locate file in explorer
     右键打开文件位置 - 文件列表右键菜单支持在资源管理器中定位文件
 13. GTP track switch - dropdown to select different tracks (with tuning info display)
     GTP音轨切换 - 下拉菜单选择不同音轨查看(含调弦信息显示)
 14. Playhead cursor - vertical line follows playback, current measure highlighted
     播放光标 - 竖线跟随播放进度移动，当前小节高亮显示
 15. Playback performance optimization - image scale cache + UI throttle updates
     播放性能优化 - 图片缩放缓存+UI节流更新，解决播放卡顿
 16. Internationalization (i18n) - Chinese/English/Russian trilingual, JSON translation files
     国际化支持(i18n) - 中文/英文/俄文三语切换，JSON翻译文件
 17. GTP track volume control - DAW-style vertical sliders with dB scale (-∞ ~ +12dB)
     GTP音轨音量控制 - 专业DAW风格垂直滑块(dB刻度)，支持每轨独立调节+Master总音量
 18. Platform-aware default fonts - automatically selects system-preinstalled fonts on Windows/Linux/macOS
     平台自适应默认字体 - 根据 Windows/Linux/macOS 自动选择系统预装字体
 19. Selection Window rename - main file browser window renamed from "Settings" to "Selection Window"
     选择窗口重命名 - 主文件浏览窗口从"设置"重命名为"选择窗口"
 20. Settings panel - centralized configuration for language, theme, UI font, GTP rendering parameters, and restore defaults
     设置面板 - 集中管理语言/主题/UI字体/GTP渲染参数，支持一键恢复默认，支持持久化与实时预览
 21. Fullscreen mode - F11 toggle / toolbar button / smart ESC behavior (exit fullscreen instead of close)
     全屏模式 - F11切换/工具栏按钮/ESC智能行为(全屏时退出全屏而非关闭)

Created: 2026-06-06 / 创建日期: 2026-06-06
Last Modified: 2026-06-20 (v2.1.0 - Fullscreen Mode + GTP scroll bug fix)
最后修改: 2026-06-20 (v2.1.0 - 全屏模式 + GTP滚动偏移修复)

Dependencies / 依赖库:
  - PyQt5 >= 5.15     # GUI framework (windows/widgets/signals/painting/PDF export)
                       # GUI框架(窗口/控件/信号槽/绘图/PDF导出)
  - PyMuPDF >= 1.23   # PDF parsing and page rendering (Open Source: Artifex Software)
                       # PDF解析与页面渲染为图片 (开源项目: Artifex Software)
  - Pillow >= 10.0    # Image processing (PNG/JPG/WEBP decoding) (Open Source: PIL)
                       # 图片处理(PNG/JPG/WEBP解码) (开源项目: Python Imaging Library)
  - guitarpro >= 0.11 # Guitar Pro file parsing (Open Source: pyguitarpro) - GTP dependency
                       # Guitar Pro文件解析 (开源项目: pyguitarpro) - GTP渲染功能依赖
  - ApolloTab >= 0.3.7  # GTP tablature rendering (Open Source: ApolloTab)
                       # GTP六线谱渲染 (开源项目: ApolloTab)

Tech Stack / 技术栈: Python 3.8+ / PyQt5 / PyMuPDF / Pillow / guitarpro(gtp_engine)
Compatibility / 兼容性: Windows / Linux / macOS (all paths use relative paths)

Project Structure / 项目结构:
  TAB Score Viewer.py     - Main program (this file, includes I18n class) / 主程序(本文件，含I18n国际化类)
  TAB Score Viewer.spec   - PyInstaller packaging config / PyInstaller打包配置
  icons/                  - SVG icon files (Lucide-style, for toolbar buttons) / SVG图标目录(Lucide风格工具栏图标)
  locales/                - Translation file directory (zh_CN.json/en_US.json/ru_RU.json) / 翻译文件目录
  soundfont/              - SoundFont directory (GTP audio required, download FluidR3_GM.sf2) / SoundFont音色库目录
  config/settings.json    - User settings (language/theme, auto-generated at runtime) / 用户配置
  data/annotations/       - Annotation data storage (JSON format) / 标注数据存储
  readme/                 - Project documentation / 项目文档目录
============================================================
"""

import sys
import os
import time  # 高精度计时(用于线性模式下play_time与真实时间同步)
import json
import math
import copy
import uuid
import bisect
import platform  # 检测操作系统, 用于选择平台默认字体
from typing import Any, List, Dict, Tuple, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# Qt GUI组件
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QListWidget,
    QListWidgetItem, QMenu, QAction, QMessageBox, QLineEdit,
    QDialog, QTextEdit, QDialogButtonBox, QGroupBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QColorDialog, QFontDialog, QFontComboBox,
    QSplitter, QFrame, QScrollArea, QGraphicsDropShadowEffect, QSizePolicy,
    QToolTip, QProgressBar, QComboBox, QTabWidget, QToolButton, QRadioButton,
    QAbstractButton
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog  # 打印支持(用于打印曲谱到物理打印机+预览)
from PyQt5.QtGui import (
    QPixmap, QPainter, QPen, QColor, QFont, QFontMetrics, QIcon,
    QImage, QCursor, QPainterPath, QLinearGradient, QRadialGradient,
    QMouseEvent, QKeyEvent, QWheelEvent, QResizeEvent, QShowEvent,
    QContextMenuEvent,
    QKeySequence, QPalette, QBrush, QTransform, QPolygonF, QFontDatabase
)
from PyQt5.QtCore import (
    Qt, QTimer, QRect, QSize, QPoint, QRunnable, QThreadPool,
    pyqtSignal, QObject, QEasingCurve, QPropertyAnimation,
    QRectF, QPointF, pyqtProperty, QBuffer, QEvent
)

# 第三方库
import fitz  # PyMuPDF - PDF解析 (开源库)
from PIL import Image as PILImage  # Pillow - 图片处理(含WEBP) (开源库)
from ApolloTab.utils.constants import RenderConfig  # ApolloTab 渲染配置类 (开源库: ApolloTab 0.3.7)


# ============================================================
# 配置常量
# ============================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "settings.json")
ANNOTATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "annotations")
# 应用图标路径(开发模式: 脚本目录; 打包模式: exe所在目录)
_APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(_APP_BASE_DIR, "icon.ico")


def _find_icon_file(*dirs: str) -> str:
    """在给定目录中搜索图标文件 (支持 .icns .ico .png)"""
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in ("icon.icns", "icon.ico", "icon.png"):
            path = os.path.join(d, name)
            if os.path.exists(path):
                return path
    return ""


def get_app_icon() -> QIcon:
    """
    获取应用图标(QIcon对象)
    原理: 兼容开发和PyInstaller打包两种运行模式
      - 开发模式: 从脚本同目录读取图标
      - 打包模式(sys.frozen): 优先从exe所在目录读取，若不存在则从_internal/子目录读取
    支持格式: .icns (macOS), .ico (Windows), .png (通用)
    返回: QIcon对象，文件不存在时返回空 QIcon
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        path = _find_icon_file(base, os.path.join(base, "_internal"))
    else:
        path = _find_icon_file(_APP_BASE_DIR)
    if path:
        return QIcon(path)
    return QIcon()  # 文件不存在时返回空图标


# ============================================================
# SVG 图标加载器 (SVG Icon Loader)
# ============================================================

def load_icon(icon_name: str, size: tuple = None) -> QIcon:
    """
    加载 SVG 图标为 QIcon 对象 / Load SVG icon as QIcon object
    原理: 从 icons/ 目录读取 SVG 文件，使用 Qt 渲染为像素图标
         兼容开发模式和 PyInstaller 打包模式(onedir: _internal/)
    参数:
      icon_name: 图标文件名(不含扩展名), 如 "annotate", "export", "play"
      size:     可选图标尺寸 (宽, 高) 元组, 默认 None(使用SVG原始尺寸)
    返回:
      QIcon 对象, 文件不存在时返回空 QIcon
    """
    # 确定应用根目录(兼容开发和打包模式)
    if getattr(sys, 'frozen', False):
        # PyInstaller onedir 模式: 数据文件在 _internal/ 子目录
        base = os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        base = _APP_BASE_DIR
    svg_path = os.path.join(base, 'icons', f'{icon_name}.svg')
    if os.path.exists(svg_path):
        icon = QIcon(svg_path)
        return icon
    return QIcon()  # 文件不存在时返回空图标


# 标注文件扩展名: 与源文件同目录，命名为 {源文件名}.anno.json
# 例如: 晚安北京.gp4 → 晚安北京.gp4.anno.json
ANNOTATION_EXT = ".anno.json"

# 支持的文件扩展名
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
SUPPORTED_PDF_EXTENSIONS = ('.pdf',)
SUPPORTED_GTP_EXTENSIONS = ('.gp3', '.gp4', '.gp5', '.gpx', '.gtp', '.gp')
SUPPORTED_ALL_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_PDF_EXTENSIONS + SUPPORTED_GTP_EXTENSIONS

# UI颜色主题 - 深色音乐风格(默认)
THEME_DARK = {
    'bg_primary': '#121212',
    'bg_secondary': '#1E1E2E',
    'bg_surface': '#252536',
    'bg_card': '#2D2D44',
    'border': '#3A3A4A',
    'text_primary': '#E2E8F0',
    'text_secondary': '#94A3B8',
    'text_muted': '#64748B',
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'primary_light': '#60A5FA',
    'accent': '#F97316',
    'accent_hover': '#EA580C',
    'accent_light': '#FB923C',  # accent浅色(选中高亮)
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
}

# UI颜色主题 - 浅色清新风格
THEME_LIGHT = {
    'bg_primary': '#F8FAFC',       # 主背景: 极浅灰白
    'bg_secondary': '#F1F5F9',     # 次背景: 浅灰
    'bg_surface': '#FFFFFF',       # 表面: 纯白
    'bg_card': '#FFFFFF',          # 卡片: 纯白
    'border': '#E2E8F0',           # 边框: 浅灰蓝
    'text_primary': '#1E293B',     # 主文字: 深蓝灰
    'text_secondary': '#64748B',   # 次文字: 灰蓝
    'text_muted': '#94A3B8',       # 弱文字: 中灰
    'primary': '#2563EB',          # 主色: 深蓝
    'primary_hover': '#1D4ED8',    # 主色悬停: 更深蓝
    'primary_light': '#60A5FA',    # 主色浅: 天蓝
    'accent': '#EA580C',           # 强调色: 深橙
    'accent_hover': '#C2410C',     # 强调悬停: 更深橙
    'accent_light': '#FDBA74',     # 强调浅: 浅橙
    'success': '#059669',          # 成功: 深绿
    'warning': '#D97706',          # 警告: 深黄
    'danger': '#DC2626',           # 危险: 深红
}

# 向后兼容: 默认引用深色主题
THEME_COLORS = THEME_DARK


# ============================================================
# QSS样式表缓存（性能优化：P0-1）
# ============================================================
# 原理: _apply_theme()中通过f-string生成1000+字符的QSS字符串，
#       Qt每次setStyleSheet()都会重新解析整个样式表并遍历所有子控件重新应用样式。
#       缓存QSS字符串可避免重复的字符串格式化和Qt样式表解析开销。
#       缓存key为(theme_name, window_class)，切换主题时theme_name变化自动刷新。

# 全局QSS缓存: {theme_name: {window_class: qss_string}}
_QSS_CACHE: Dict[str, Dict[str, str]] = {}

def _get_cached_qss(window_class: str, theme_name: str, builder_fn) -> str:
    """
    获取缓存的QSS样式表字符串（首次调用时生成并缓存，后续直接返回）
    
    参数:
        window_class: 窗口类名，如 'DisplayWindow', 'SelectionWindow', 'SettingsDialog'
        theme_name:   主题名称，如 'dark', 'light'
        builder_fn:   无参构建函数，返回QSS字符串
    """
    if theme_name not in _QSS_CACHE:
        _QSS_CACHE[theme_name] = {}
    cache = _QSS_CACHE[theme_name]
    if window_class not in cache:
        cache[window_class] = builder_fn()
    return cache[window_class]


# ============================================================
# 平台自适应字体工具函数
# ============================================================

def get_font_families(font_type: str = "ui") -> List[str]:
    """
    根据当前操作系统返回推荐的字体族列表(含 fallback)

    参数:
        font_type: 字体用途类型
            - "ui":      主UI/标注字体, 优先保证中文显示效果
            - "numeric": 数字/英文标签字体, 优先清晰可读
            - "mono":    等宽字体, 用于 dB 值、页码等需对齐的场景

    返回:
        字体族名称列表, 元素可直接用于 QFont, 也可用 get_font_family_css() 转为 CSS 字符串

    平台映射说明:
        Windows: 使用系统预装的微软雅黑/Consolas, 显示效果最佳
        Linux:   使用常见开源字体(Noto Sans CJK SC / DejaVu), 适配 Ubuntu/Debian/Fedora/Arch
        macOS:   使用苹方/Heiti SC/Menlo, 与系统风格一致
    """
    sys_name = platform.system()
    if font_type == "mono":
        if sys_name == "Windows":
            return ["Consolas", "DejaVu Sans Mono", "monospace"]
        elif sys_name == "Darwin":
            return ["Menlo", "Monaco", "DejaVu Sans Mono", "monospace"]
        else:  # Linux 及其他 Unix-like
            return ["DejaVu Sans Mono", "Consolas", "monospace"]
    elif font_type == "numeric":
        if sys_name == "Windows":
            return ["Segoe UI", "Microsoft YaHei", "Arial", "sans-serif"]
        elif sys_name == "Darwin":
            return ["SF Pro Text", "PingFang SC", "Helvetica Neue", "Arial", "sans-serif"]
        else:
            return ["DejaVu Sans", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "sans-serif"]
    else:  # "ui" 默认
        defaults = []
        if sys_name == "Windows":
            defaults = ["Microsoft YaHei", "Segoe UI", "Arial", "sans-serif"]
        elif sys_name == "Darwin":
            defaults = ["PingFang SC", "Heiti SC", "STHeiti", "Helvetica Neue", "Arial", "sans-serif"]
        else:
            defaults = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans", "sans-serif"]
        # 如果用户通过设置面板指定了 UI 字体，则放在首位优先使用
        if font_type == "ui" and _UI_FONT_FAMILY and _UI_FONT_FAMILY not in defaults:
            return [_UI_FONT_FAMILY] + defaults
        return defaults


def get_font_family(font_type: str = "ui") -> str:
    """
    返回当前平台指定类型的首选字体族名称(单个字体名)

    用途: 直接传给 QFont(family, size) 构造函数
    """
    return get_font_families(font_type)[0]


def get_font_family_css(font_type: str = "ui") -> str:
    """
    返回当前平台指定类型的 CSS font-family 字符串(含 fallback 列表)

    用途: 直接嵌入 Qt 样式表, 例如:
        QLabel {{ font-family: {get_font_family_css('ui')}; }}
    """
    return ", ".join(f"'{f}'" for f in get_font_families(font_type))


# 用户自定义 UI 字体，None 表示使用平台默认推荐字体
# 通过设置面板修改后，全局样式表会优先使用该字体
_UI_FONT_FAMILY: Optional[str] = None


def set_ui_font(family: Optional[str]) -> None:
    """
    设置用户自定义 UI 字体

    参数:
        family: 字体族名称，None 或空字符串表示恢复平台默认

    说明:
        修改后需手动调用各窗口的 _apply_theme() / _refresh_theme()
        重新应用样式表，才能看到实时效果
    """
    global _UI_FONT_FAMILY
    _UI_FONT_FAMILY = family if family else None


# ============================================================
# 主题管理器（单例模式） - v2.0 新增
# ============================================================

class ThemeManager(QObject):
    """
    全局主题管理器（单例模式）
    
    功能:
      1. 统一管理深色/浅色两套UI配色方案
      2. 提供运行时动态切换主题能力
      3. 通过 theme_changed 信号通知所有UI组件刷新样式
      4. 与 ApolloTab 渲染主题联动（浅色UI → light渲染 / 深色UI → dark渲染）
      5. 主题选择持久化到 settings.json
    
    使用方式:
        # 获取当前主题颜色
        color = ThemeManager.get('primary')  # 返回当前主题的主色
        
        # 切换主题
        ThemeManager.set_theme('light')      # 切换到浅色
        
        # 监听主题变更
        ThemeManager.theme_changed.connect(my_refresh_func)
        
        # 获取ApolloTab渲染主题名称
        render_theme = ThemeManager.gtp_render_theme  # "light" 或 "dark"
    
    可用主题:
      - "dark":  深色音乐风格（默认，护眼）
      - "light": 浅色清新风格（明亮，适合白天/打印）
    """
    
    # === pyqtSignal 必须定义为类属性 (PyQt5硬性要求) ===
    # 不能在 __init__ 或其他方法中动态赋值为实例属性，否则 connect/emit 不工作
    theme_changed = pyqtSignal(str)   # 信号参数: 新主题名称 ("dark" | "light")

    _instance = None              # 单例实例
    _initialized: bool = False     # 是否已完成初始化(避免重复调用 QObject.__init__)
    
    # GTP渲染主题映射: UI主题名 → ApolloTab渲染主题名
    _GTP_THEME_MAP = {
        'dark': 'dark',
        'light': 'light',
    }
    
    def __new__(cls):
        """单例模式: 确保全局只有一个ThemeManager实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化单例实例

        注意: 由于单例模式，__init__ 可能被多次调用(每次 ThemeManager() 都会触发)，
              使用 _initialized 标志确保 QObject.__init__() 只执行一次。
        """
        if self._initialized:
            return  # 已初始化过，跳过(单例复用)
        self._initialized = True
        # 必须调用 QObject.__init__()，否则 pyqtSignal 无法正常工作
        super().__init__()
        self._current_theme_name = "dark"
        self._theme_data = dict(THEME_DARK)

    @classmethod
    def get(cls, key: str, default: str = None) -> str:
        """
        获取当前主题的颜色值
        
        参数:
            key: 颜色键名 (如 'primary', 'bg_surface', 'text_primary')
            default: 键不存在时的默认值
            
        返回:
            十六进制颜色字符串 (如 "#3B82F6")
        """
        instance = cls()
        return instance._theme_data.get(key, default or THEME_DARK.get(key, '#000000'))
    
    @classmethod
    def current(cls) -> dict:
        """获取当前完整的主题配色字典（副本）"""
        instance = cls()
        return dict(instance._theme_data)
    
    @classmethod
    def current_name(cls) -> str:
        """获取当前主题名称 ('dark' | 'light')"""
        return cls()._current_theme_name
    
    @classmethod
    def is_dark(cls) -> bool:
        """判断当前是否为深色主题"""
        return cls()._current_theme_name == 'dark'
    
    @classmethod
    def is_light(cls) -> bool:
        """判断当前是否为浅色主题"""
        return cls()._current_theme_name == 'light'
    
    @property
    def gtp_render_theme(self) -> str:
        """
        获取当前UI主题对应的ApolloTab渲染主题名称
        用于GTP谱面渲染时传递给 TabRenderer.set_theme()
        
        返回:
            "light" 或 "dark" （与 ApolloTab.ThemeConfig.PRESET_THEMES 对应）
        """
        return self._GTP_THEME_MAP.get(self._current_theme_name, 'dark')
    
    @classmethod
    def get_gtp_render_theme(cls) -> str:
        """类方法接口: 获取GTP渲染主题名称"""
        return cls().gtp_render_theme
    
    @classmethod
    def set_theme(cls, theme_name: str) -> bool:
        """
        切换全局主题
        
        参数:
            theme_name: 目标主题名称 ("dark" | "light")
            
        返回:
            True 成功, False 失败(主题名称无效)
            
        注意:
          切换成功后会发射 theme_changed 信号，
          所有连接此信号的组件应重新应用样式。
        """
        instance = cls()
        theme_name = theme_name.lower().strip()
        
        if theme_name == instance._current_theme_name:
            return True  # 相同主题无需切换
        
        if theme_name == 'dark':
            instance._theme_data = dict(THEME_DARK)
        elif theme_name == 'light':
            instance._theme_data = dict(THEME_LIGHT)
        else:
            print(f"[ThemeManager] 未知主题: '{theme_name}'，可用: dark, light")
            return False
        
        old_theme = instance._current_theme_name
        instance._current_theme_name = theme_name
        
        # 更新向后兼容的全局变量
        global THEME_COLORS
        THEME_COLORS = instance._theme_data
        
        print(f"[ThemeManager] 主题已切换: {old_theme} → {theme_name}")
        
        # 发射主题变更信号
        try:
            instance.theme_changed.emit(theme_name)
        except Exception:
            pass
        
        return True
    
    @classmethod
    def available_themes(cls) -> list:
        """获取所有可用主题列表 [(name, display_name), ...]"""
        return [
            ('dark', '深色模式 (Dark)'),
            ('light', '浅色模式 (Light)'),
        ]
    
    @classmethod
    def apply_stylesheet(cls, widget, extra_css: str = "") -> None:
        """
        为指定控件应用当前主题的基础样式表（便捷方法）
        
        参数:
            widget:   目标Qt控件
            extra_css: 额外的CSS规则（追加在基础样式之后）
        """
        theme = cls.current()
        base_css = f"""
            {{ background-color: {theme['bg_primary']}; color: {theme['text_primary']};
               font-family: {get_font_family_css('ui')}; }}
            QLabel {{ color: {theme['text_primary']}; font-size: 13px; }}
            QLineEdit {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 5px; padding: 5px 8px; }}
            QSpinBox {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 4px; padding: 4px; }}
            QComboBox {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 4px; padding: 4px 8px; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                selection-background-color: {theme['primary']}; }}
            QGroupBox {{ color: {theme['text_primary']}; border: 1px solid {theme['border']};
                border-radius: 8px; margin-top: 12px; padding-top: 8px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
            QSlider::groove:horizontal {{ border: none; height: 4px;
                background: {theme['bg_surface']}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {theme['primary']};
                border: 2px solid {theme['bg_primary']}; width: 16px; margin: -7px 0; border-radius: 8px; }}
            QListWidget {{ background-color: {theme['bg_surface']}; color: {theme['text_primary']};
                border: 1px solid {theme['border']}; border-radius: 6px; outline: none; }}
            QListWidget::item {{ padding: 6px; border-bottom: 1px solid {theme['border']}; }}
            QListWidget::item:selected {{ background-color: {theme['primary']}; color: white; }}
            QListWidget::item:hover {{ background-color: {theme['primary']}; opacity:0.15; border-radius:4px; }}
            QScrollBar:vertical {{ background: {theme['bg_secondary']}; width: 10px; border-radius: 5px; }}
            QScrollBar::handle:vertical {{ background: {theme['border']}; border-radius: 5px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: {theme['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """
        widget.setStyleSheet(base_css + extra_css)


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Annotation:
    """文本标注数据模型 - 存储谱面上的文字说明"""
    id: str = ""
    x: float = 0.0          # X坐标比例 (0-1)
    y: float = 0.0          # Y坐标比例 (0-1)
    text: str = ""          # 标注文本内容
    color: str = "#F97316"  # 标注颜色
    font_size: int = 14     # 字体大小(px)
    font_family: str = field(default_factory=lambda: get_font_family("ui"))  # 默认使用平台推荐UI字体
    is_bold: bool = False
    background_color: str = "#00000080"


@dataclass
class SpeedCurvePoint:
    """速度曲线控制点
    position: 位置百分比 (0-100)，表示在播放进度的哪个位置
    speed: 速度倍率基准值 (建议范围25-120)
           实际播放速度 = base_speed * (speed / 50)
           speed=50 → 与base_speed相同(1倍速，基准)
           speed>50 → 比base_speed慢(总时长更长)
           speed<50 → 比base_speed快(总时长更短)
    """
    position: float = 0.0   # 位置百分比 (0-100)
    speed: float = 50.0     # 速度倍率基准值(见类注释)


# ============================================================
# 国际化(I18n) - 多语言支持
# ============================================================

class I18n:
    """
    国际化翻译管理器（单例模式）
    
    功能:
      1. 从 locales/ 目录加载JSON翻译文件(如 zh_CN.json, en_US.json, ru_RU.json)
      2. 提供 t(key, **kwargs) 方法获取翻译文本，支持 {} 占位符格式化
      3. 支持运行时语言切换，切换后通过 language_changed 信号通知UI刷新
      4. 缺失翻译自动回退到中文(zh_CN)，确保UI不会出现空白字符串
    
    使用方式:
      # 获取翻译文本
      text = I18n.t("app.title")                    # 无占位符
      text = I18n.t("messages.export_success_msg",  # 带占位符
                   fmt="PDF", path="/tmp/a.pdf", count=3)
      
      # 切换语言
      I18n.set_language("en_US")  # 或 "ru_RU" 切换到俄语
    
    翻译文件格式 (locales/xx_XX.json):
      {
        "_meta": {"language": "zh_CN", "name": "简体中文"},
        "app": {"title": "..."},
        "toolbar": {"zoom": "缩放:", ...},
        ...
      }
    
    调整说明:
      - 新增语言: 在 locales/ 下新建 xx_XX.json 文件即可，程序会自动识别
      - 新增翻译项: 同时更新所有语言的JSON文件中的对应key
      - 缺失key: 自动回退到zh_CN的值，控制台打印警告
    """
    
    _instance = None           # 单例实例
    _translations: dict = {}   # 当前加载的翻译字典 {key: value}
    _current_lang: str = ""    # 当前语言代码 (如 "zh_CN", "en_US")
    _locales_dir: str = ""     # 翻译文件目录路径
    
    # 语言切换信号 - 连接此信号可在语言变更时刷新UI
    language_changed = None  # 类型: pyqtSignal(str)，延迟初始化（需在QApplication之后）
    
    def __new__(cls):
        """单例模式 - 全程只创建一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化国际化管理器"""
        if self._initialized:
            return
        self._initialized = True
        
        # 翻译文件目录: 项目根目录下的 locales/ 文件夹
        # 使用相对路径，兼容 Windows/Linux/macOS
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._locales_dir = os.path.join(base_dir, "locales")
        
        # 默认使用中文
        self._current_lang = "zh_CN"
        self._translations = {}
        
        # 加载默认语言翻译
        self._load_language(self._current_lang)
    
    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        """
        获取翻译文本（类方法，可直接通过 I18n.t() 调用）
        
        参数:
            key: 翻译键名，支持点号分隔的嵌套访问 (如 "app.title", "control_panel.play_btn")
            **kwargs: 占位符参数，用于 .format() 格式化
        
        返回:
            翻译后的文本字符串。如果key缺失则回退到中文，中文也缺失则返回原始key
        
        示例:
            I18n.t("app.title")  → "TAB Score Viewer - 吉他谱查看器" (中文)
            I18n.t("app.title")  → "TAB Score Viewer - Guitar Tab Viewer" (英文)
            I18n.t("messages.track_switch_fail_msg", index=1, error="xxx")
                          → "无法渲染音轨 1:\nxxx"
        """
        instance = cls()
        
        # 按点号分割key，逐级查找嵌套字典
        value = instance._translations
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # 当前语言找不到 → 回退到中文
                fallback = instance._get_fallback(key)
                if fallback is not None:
                    value = fallback
                else:
                    # 中文也没有 → 返回key本身并警告
                    print(f"[I18n] 缺失翻译 key='{key}' (lang={instance._current_lang})")
                    return key
        
        # 如果结果是字符串且有占位符参数，进行格式化
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError) as e:
                print(f"[I18n] 格式化失败 key='{key}', error={e}")
                return value
        
        return value if isinstance(value, str) else str(value)
    
    @classmethod
    def set_language(cls, lang_code: str) -> bool:
        """
        切换当前语言（类方法）
        
        参数:
            lang_code: 目标语言代码，如 "zh_CN", "en_US", "ru_RU"
                     必须与 locales/ 下的JSON文件名(不含扩展名)一致
        
        返回:
            True 切换成功, False 失败(语言文件不存在)
        
        注意: 切换成功后会发射 language_changed 信号，
              UI组件应连接此信号以刷新显示文本。
        """
        instance = cls()
        if lang_code == instance._current_lang:
            return True  # 相同语言无需切换
        
        success = instance._load_language(lang_code)
        if success:
            old_lang = instance._current_lang
            instance._current_lang = lang_code
            print(f"[I18n] 语言已切换: {old_lang} → {lang_code}")
            
            # 发射语言变更信号（通知UI刷新）
            if instance.language_changed is not None:
                try:
                    instance.language_changed.emit(lang_code)
                except Exception:
                    pass
            return True
        else:
            print(f"[I18n] 语言文件不存在: {lang_code}.json")
            return False
    
    @classmethod
    def current_language(cls) -> str:
        """获取当前语言代码"""
        return cls()._current_lang
    
    @classmethod
    def available_languages(cls) -> list:
        """
        获取所有可用语言列表
        
        返回:
            [(code, name), ...] 如 [("zh_CN", "简体中文"), ("en_US", "English"), ("ru_RU", "Русский")]
        """
        instance = cls()
        languages = []
        if os.path.isdir(instance._locales_dir):
            for fname in sorted(os.listdir(instance._locales_dir)):
                if fname.endswith('.json'):
                    code = fname[:-5]  # 去掉 ".json"
                    fpath = os.path.join(instance._locales_dir, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            meta = json.load(f).get('_meta', {})
                            name = meta.get('name', code)
                            languages.append((code, name))
                    except Exception:
                        languages.append((code, code))
        return languages
    
    def _load_language(self, lang_code: str) -> bool:
        """加载指定语言的翻译文件"""
        filepath = os.path.join(self._locales_dir, f"{lang_code}.json")
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
            # 移除元数据键（不影响翻译查找）
            self._translations.pop('_meta', None)
            return True
        except Exception as e:
            print(f"[I18n] 加载语言文件失败 '{filepath}': {e}")
            return False
    
    def _get_fallback(self, key: str):
        """回退到中文(zh_CN)查找翻译"""
        if self._current_lang == "zh_CN":
            return None  # 已经是中文，无需回退
        filepath = os.path.join(self._locales_dir, "zh_CN.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                zh_data = json.load(f)
            zh_data.pop('_meta', None)
            value = zh_data
            for part in key.split('.'):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        except Exception:
            return None


@dataclass
class SpeedCurveConfig:
    """速度曲线配置"""
    points: List[SpeedCurvePoint] = field(default_factory=lambda: [
        SpeedCurvePoint(0, 50), SpeedCurvePoint(100, 50)  # 默认线性匀速曲线
    ])
    is_enabled: bool = False


@dataclass
class LoopConfig:
    """循环播放配置"""
    is_enabled: bool = False
    loop_type: str = "none"  # none/all/region
    start_position: float = 0.0
    end_position: float = 100.0


# ============================================================
# 异步工作线程
# ============================================================

class WorkerSignals(QObject):
    """通用异步工作信号类"""
    finished = pyqtSignal(object)  # object: 可携带任意数据(如文件列表)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)


class LoadFileListWorker(QRunnable):
    """异步加载文件列表的工作线程"""
    def __init__(self, folder: str):
        super().__init__()
        self.folder = folder
        self.signals = WorkerSignals()
        self._result: List[Tuple] = []

    def run(self) -> None:
        """异步扫描文件夹 - 过滤支持的文件格式"""
        try:
            # 预检查: 目录不存在或不可访问时立即返回错误
            if not os.path.exists(self.folder):
                self.signals.error.emit(f"目录不存在: {self.folder}"); return
            if not os.path.isdir(self.folder):
                self.signals.error.emit(f"路径不是文件夹: {self.folder}"); return
            if not os.access(self.folder, os.R_OK):
                self.signals.error.emit(f"无权限访问目录: {self.folder}"); return

            file_items = []
            for file in os.listdir(self.folder):
                file_path = os.path.join(self.folder, file)
                if os.path.isdir(file_path) and not file.startswith('.'):
                    file_items.append((file + '/', file_path, True))
            for file in os.listdir(self.folder):
                file_path = os.path.join(self.folder, file)
                if os.path.isfile(file_path) and file.lower().endswith(SUPPORTED_ALL_EXTENSIONS):
                    file_items.append((file, file_path, False))
            self._result = sorted(file_items, key=lambda x: (not x[2], x[0]))
            self.signals.finished.emit(self._result)  # 携带文件列表数据
        except PermissionError:
            self.signals.error.emit(f"无权限访问目录: {self.folder}")
        except OSError as e:
            self.signals.error.emit(f"访问目录出错: {e}")
        except Exception as e:
            self.signals.error.emit(str(e))


class LoadContentWorker(QRunnable):
    """
    异步加载谱面内容的工作线程
    原理: 在后台线程中解析文件，避免阻塞UI主线程
    支持: PDF(PyMuPDF)、图片(Pillow)、GTP(基础预览)
    """
    def __init__(self, window: 'DisplayWindow', file_path, file_type: str):
        super().__init__()
        self.window = window
        self.file_path = file_path
        self.file_type = file_type
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            images = []
            if self.file_type == 'pdf':
                images = self._load_pdf()
            elif self.file_type == 'images':
                images = self._load_images()
            elif self.file_type == 'gtp':
                images = self._load_gtp()
            self.window.loaded_images = images
            self.signals.finished.emit(images)  # 携带加载结果
        except Exception as e:
            self.signals.error.emit(str(e))

    def _load_pdf(self) -> List[QPixmap]:
        """
        加载PDF文件 - 使用PyMuPDF渲染每页为高DPI图片
        
        性能优化(P1-2): 使用 concurrent.futures.ThreadPoolExecutor 并行渲染多页，
                        max_workers=4，将50页PDF加载时间从~3s降至~1s。
                        PyMuPDF文档非线程安全，每个线程独立打开文档实例。
        """
        pdf_document = fitz.open(self.file_path)
        total_pages = len(pdf_document)
        pdf_document.close()
        
        # 定义单页渲染函数（每个线程独立打开文档实例）
        def _render_page(page_num: int) -> QPixmap:
            doc = fitz.open(self.file_path)
            try:
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)  # 高DPI渲染保证清晰度
                qt_image = QPixmap()
                qt_image.loadFromData(pix.tobytes("png"))
                return qt_image
            finally:
                doc.close()
        
        # 并行渲染：使用ThreadPoolExecutor，max_workers=4
        images = [None] * total_pages
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有渲染任务
            future_to_page = {executor.submit(_render_page, i): i for i in range(total_pages)}
            completed = 0
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                images[page_num] = future.result()
                completed += 1
                self.signals.progress.emit(int(completed / total_pages * 100))
        
        return images

    def _load_images(self) -> List[QPixmap]:
        """
        加载图片文件列表
        支持: PNG, JPG, JPEG, WEBP (通过Pillow库)
        Pillow是Python图像处理标准库(PIL fork)，支持多种格式
        """
        images = []
        paths = self.file_path if isinstance(self.file_path, list) else [self.file_path]
        total = len(paths)
        for idx, path in enumerate(paths):
            pil_img = PILImage.open(path)
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')  # 统一转换为RGBA确保兼容性
            qimage = QImage(pil_img.tobytes('raw', 'RGBA'), pil_img.width, pil_img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            if not pixmap.isNull():
                images.append(pixmap)
            pil_img.close()
            self.signals.progress.emit(int((idx + 1) / total * 100))
        return images

    def _load_gtp(self) -> List[QPixmap]:
        """
        加载Guitar Pro文件(.gp3/.gp4/.gp5/.gpx/.gtp/.gp)
        
        原理: 使用 gtp_engine 库的 GTPPlayer 高级API完整处理 GTP 文件，
              包括解析、渲染、音频初始化等。
              GTPPlayer 封装了所有GTP相关逻辑，主程序只需简单调用。
        
        依赖库:
          - gtp_engine (含 guitarpro, PyQt5, pyfluidsynth)
        """
        images = []
        try:
            # 使用 GTPPlayer 进行完整的加载和渲染
            from ApolloTab import GTPPlayer
            
            # 创建播放器实例并加载文件
            player = GTPPlayer()
            player.load(self.file_path)
            
            # v2.0新增: 根据当前UI主题设置GTP渲染主题
            # 浅色UI → light渲染 / 深色UI → dark渲染（用户可在深色模式下手动切换）
            render_theme = ThemeManager.get_gtp_render_theme()
            # 安全检查: 确保GTPPlayer版本支持set_theme方法
            if hasattr(player, 'set_theme') and callable(getattr(player, 'set_theme')):
                try:
                    player.set_theme(render_theme)
                    print(f"[LoadContentWorker] GTP渲染主题: {render_theme}")
                except Exception as e:
                    print(f"[LoadContentWorker] 设置GTP渲染主题失败(使用默认): {e}")
            else:
                print(f"[LoadContentWorker] 当前GTPPlayer版本不支持主题切换，使用默认主题")
            
            # 渲染当前音轨（默认第0轨）
            pixmaps = player.render_track(0)
            
            # 保存播放器实例到window（供后续音频/时间线功能使用）
            self.window.gtp_player = player
            
            # 捕获布局数据(播放光标功能依赖此数据)
            self.window._page_layouts = player.last_layouts
            
            # 进度报告：完成
            self.signals.progress.emit(100)
            
            images = pixmaps
            
        except ImportError as e:
            # gtp_engine 或依赖未安装时，回退到信息展示图
            info_pixmap = self._create_gtp_info_image(
                f"GTP引擎依赖缺失:\n{str(e)}\n\n请安装: pip install gtp-engine"
            )
            images.append(info_pixmap)
        except Exception as e:
            # 其他错误时，显示错误信息和回退预览
            error_pixmap = self._create_error_image(f"GTP加载失败:\n{str(e)}")
            images.append(error_pixmap)
        
        return images

    def _create_error_image(self, message: str) -> QPixmap:
        """创建错误展示图（当GTP加载失败时显示）- 支持动态主题"""
        width, height = 800, 500
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(ThemeManager.get('bg_surface', '#252536')))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 标题
        painter.setPen(QColor(ThemeManager.get('danger', '#EF4444')))
        title_font = QFont(get_font_family("ui"), 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path)
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"加载失败: {filename}")

        # 错误文本
        painter.setPen(QColor(ThemeManager.get('text_primary', '#E2E8F0')))
        info_font = QFont(get_font_family("ui"), 13)
        painter.setFont(info_font)
        
        # 将message按行分割并绘制
        lines = message.split('\n')
        y = 130
        for line in lines:
            if line.strip():
                painter.drawText(QRect(50, y, 700, 32), Qt.AlignLeft, line)
            y += 30

        # 边框
        painter.setPen(QPen(QColor(ThemeManager.get('danger', '#EF4444')), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(30, 30, width - 60, height - 60, 15, 15)
        painter.end()
        return pixmap

    def _create_gtp_info_image(self, message: str) -> QPixmap:
        """创建GTP信息/错误展示图（当gtp_engine不可用时回退显示）- 支持动态主题"""
        width, height = 800, 500
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(ThemeManager.get('bg_surface', '#252536')))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 标题
        painter.setPen(QColor(ThemeManager.get('primary', '#3B82F6')))
        title_font = QFont(get_font_family("ui"), 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path)
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"Guitar Pro 文件: {filename}")

        # 信息文本
        painter.setPen(QColor(ThemeManager.get('text_primary', '#E2E8F0')))
        info_font = QFont(get_font_family("ui"), 13)
        painter.setFont(info_font)
        
        # 将message按行分割并绘制
        lines = message.split('\n')
        y = 130
        for line in lines:
            if line.strip():
                painter.drawText(QRect(50, y, 700, 32), Qt.AlignLeft, line)
            y += 30

        # 边框
        painter.setPen(QPen(QColor(ThemeManager.get('primary', '#3B82F6')), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(30, 30, width - 60, height - 60, 15, 15)
        painter.end()
        return pixmap


# ============================================================
# 自定义UI组件
# ============================================================

class ModernButton(QPushButton):
    """
    现代化按钮组件 - 支持动态主题切换 + SVG 图标
    Modern Button Component with dynamic theme switching + SVG icon support
    功能: 带悬停效果、阴影、圆角、可选图标的按钮基类
    主题: 通过 ThemeManager.get() 读取当前主题色，支持运行时切换
    图标: 可选 SVG 图标(从 icons/ 目录加载), 显示在文字左侧
    """

    def __init__(self, text: str, color_key: str = 'primary', icon_name: str = None, parent=None):
        super().__init__(text, parent)
        self.color_key = color_key
        # 加载可选的 SVG 图标 / Load optional SVG icon
        if icon_name:
            icon = load_icon(icon_name)
            if not icon.isNull():
                self.setIcon(icon)
                # 设置图标与文字间距 / Set spacing between icon and text
                self.setIconSize(QSize(16, 16))
                self.setStyleSheet(self._build_style_with_icon(color_key))
                return
        self._setup_style()

    def _setup_style(self) -> None:
        """初始化按钮样式 - 从ThemeManager读取当前主题配色"""
        color = ThemeManager.get(self.color_key, THEME_DARK['primary'])
        hover_color = ThemeManager.get(f'{self.color_key}_hover', color)
        bg_primary = ThemeManager.get('bg_primary', '#121212')

        self.setMinimumHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(f"""
            ModernButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-family: {get_font_family_css('ui')};
                font-size: 12px;
                font-weight: 500;
            }}
            ModernButton:hover {{ background-color: {hover_color}; }}
            ModernButton:pressed {{ background-color: {color}; }}
            ModernButton:disabled {{ background-color: #4a5568; color: #a0aec0; }}
        """)
        # 浅色模式下阴影颜色调整为半透明灰而非纯黑
        shadow_color = QColor(0, 0, 0, 25) if ThemeManager.is_light() else QColor(0, 0, 0, 40)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def _build_style_with_icon(self, color_key: str) -> str:
        """
        构建带图标的按钮样式表 / Build stylesheet for button with icon
        与 _setup_style 相似，但增加了图标内边距调整
        参数: color_key - 主题色键名
        返回: CSS 样式字符串
        """
        color = ThemeManager.get(color_key, THEME_DARK['primary'])
        hover_color = ThemeManager.get(f'{color_key}_hover', color)
        bg_primary = ThemeManager.get('bg_primary', '#121212')

        self.setMinimumHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        # 浅色模式下阴影颜色调整为半透明灰而非纯黑
        shadow_color = QColor(0, 0, 0, 25) if ThemeManager.is_light() else QColor(0, 0, 0, 40)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        return f"""
            ModernButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px 8px 10px;
                font-family: {get_font_family_css('ui')};
                font-size: 12px;
                font-weight: 500;
            }}
            ModernButton:hover {{ background-color: {hover_color}; }}
            ModernButton:pressed {{ background-color: {color}; }}
            ModernButton:disabled {{ background-color: #4a5568; color: #a0aec0; }}
        """

    def set_color(self, color_key: str) -> None:
        """
        动态切换按钮主题色 / Dynamically change button theme color
        用途: 播放/暂停状态切换时改变按钮颜色（如 success → warning）
        原理: 更新 color_key 属性后重新应用完整样式表（保留圆角/字体/阴影/图标）
        参数:
          color_key: 新的主题色键名 (如 'success', 'warning', 'primary')
        """
        self.color_key = color_key
        self.refresh_theme()

    def refresh_theme(self) -> None:
        """主题切换时调用 - 重新应用样式 / Re-apply style on theme change"""
        if not self.icon().isNull():
            self.setStyleSheet(self._build_style_with_icon(self.color_key))
        else:
            self._setup_style()


class ModernSlider(QSlider):
    """
    现代化滑块组件 - 支持动态主题切换
    功能: 继承QSlider，应用当前主题样式
    参数:
      orientation: 滑块方向(水平/垂直)
      color_key:   主题色键名(对应ThemeManager)
    """

    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal,
                 color_key: str = 'primary', parent=None):
        super().__init__(orientation, parent)
        self.color_key = color_key
        self._setup_style()

    def _setup_style(self) -> None:
        """初始化滑块样式 - 从ThemeManager读取当前主题配色"""
        color = ThemeManager.get(self.color_key, THEME_DARK['primary'])
        bg_primary = ThemeManager.get('bg_primary', '#121212')
        bg_surface = ThemeManager.get('bg_surface', '#252536')

        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {bg_surface};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                border: 2px solid {bg_primary};
                width: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 3px;
            }}
            QSlider::groove:vertical {{
                border: none;
                width: 6px;
                background: {bg_surface};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {color};
                border: 2px solid {bg_primary};
                height: 18px;
                margin: 0 -7px;
                border-radius: 9px;
            }}
            QSlider::add-page:vertical {{
                background: {color};
                border-radius: 3px;
            }}
        """)

    def refresh_theme(self) -> None:
        """主题切换时调用 - 重新应用样式"""
        self._setup_style()


class TrackVolumeSlider(QWidget):
    """
    专业音轨音量垂直滑块组件 (类似DAW混音器推子)
    
    功能:
      1. 垂直音量滑块，带dB刻度标记(-∞ ~ +6dB)
      2. 实时显示当前dB值
      3. 支持鼠标拖动/滚轮调整
      4. 动态主题适配(深色/浅色)
      5. 专业音频设备外观(金属质感滑块)
    
    参数:
      track_name: 音轨名称(显示在底部)
      is_master:  是否为Master总音量滑块(特殊样式)
    
    使用方式:
        slider = TrackVolumeSlider("Guitar 1", is_master=False)
        slider.valueChanged.connect(lambda db: print(f"音量: {db} dB"))
        slider.set_db_value(-3.0)  # 设置为-3dB
    
    音量范围: -∞(静音) ~ +6dB(最大增益)
              默认值: 0.0 dB (单位增益)
    
    调整精度:
      - 鼠标拖动: 连续调整
      - 滚轮: 每次±1dB
      - 双击: 重置为0dB
    """
    
    # 信号: 音量值变化时发射(dB值, float)
    valueChanged = pyqtSignal(float)
    
    def __init__(self, track_name: str = "Track", is_master: bool = False, parent=None):
        super().__init__(parent)
        self.track_name = track_name
        self.is_master = is_master
        
        # 音量参数
        self._db_value: float = 0.0          # 当前dB值(默认0dB=单位增益)
        self._min_db: float = -60.0           # 最小dB值(近似-∞)
        self._max_db: float = 12.0            # 最大dB值(+12dB预留)
        self._dragging: bool = False
        self._last_y: int = 0                 # 拖动起始Y坐标
        
        # UI尺寸常量(可调整效果)
        self.SLIDER_WIDTH = 16                # 滑块轨道宽度(px)
        self.HANDLE_HEIGHT = 18               # 滑块手柄高度(px)
        self.WIDGET_WIDTH = 48                # 组件总宽度(px)
        self.WIDGET_HEIGHT = 140              # 组件总高度(px)
        self.SCALE_WIDTH = 0                  # 刻度区宽度(px) - 不绘制左侧刻度，节省空间
        
        # 设置固定尺寸
        self.setFixedWidth(self.WIDGET_WIDTH)
        self.setFixedHeight(self.WIDGET_HEIGHT)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMouseTracking(True)

    def set_db_value(self, db: float) -> None:
        """
        设置音量值(dB)
        参数:
            db: 目标dB值(范围: -60.0 ~ +12.0)
        效果: 自动clamp到有效范围并刷新显示
        """
        self._db_value = max(self._min_db, min(self._max_db, db))
        self.update()
        self.valueChanged.emit(self._db_value)

    def get_db_value(self) -> float:
        """获取当前dB值"""
        return self._db_value

    def _db_to_y(self, db: float, track_top: int = 8, track_bottom: int = None) -> float:
        """
        将dB值转换为Y坐标(像素)
        原理: 线性映射 dB范围 → 滑块轨道高度
              顶部=最大dB, 底部=最小dB(符合直觉:向上推=音量大)
        
        参数:
            db: dB值
            track_top: 轨道顶部Y坐标(默认8)
            track_bottom: 轨道底部Y坐标(默认WIDGET_HEIGHT-28)
        """
        if track_bottom is None:
            track_bottom = self.WIDGET_HEIGHT - 28
        
        if db <= self._min_db:
            return float(track_bottom)  # 最底部(留出标签空间)
        if db >= self._max_db:
            return float(track_top)  # 最顶部(留出边距)
        
        # 线性插值
        ratio = (db - self._min_db) / (self._max_db - self._min_db)
        y = track_bottom - ratio * (track_bottom - track_top)
        return y

    def _y_to_db(self, y: int) -> float:
        """将Y坐标转换为dB值"""
        track_top = 8
        track_bottom = self.WIDGET_HEIGHT - 28
        
        if y >= track_bottom:
            return self._min_db
        if y <= track_top:
            return self._max_db
        
        ratio = (track_bottom - y) / (track_bottom - track_top)
        db = self._min_db + ratio * (self._max_db - self._min_db)
        return round(db, 1)

    def paintEvent(self, event) -> None:
        """绘制音量滑块(简洁DAW风格)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取主题颜色
        bg_surface = ThemeManager.get('bg_surface', '#252536')
        bg_card = ThemeManager.get('bg_card', '#2D2D44')
        border_color = ThemeManager.get('border', '#3A3A4A')
        text_primary = ThemeManager.get('text_primary', '#E2E8F0')
        text_muted = ThemeManager.get('text_muted', '#64748B')
        primary = ThemeManager.get('primary', '#3B82F6')
        
        # Master滑块使用特殊高亮色
        if self.is_master:
            accent = ThemeManager.get('accent', '#F97316')
            slider_color = accent
        else:
            slider_color = primary
        
        # ===== 1. 绘制背景 =====
        painter.fillRect(self.rect(), QColor(bg_surface))
        
        # ===== 2. 计算布局(轨道居中) =====
        margin_x = (self.WIDGET_WIDTH - self.SLIDER_WIDTH) // 2  # 水平居中
        track_top = 8
        track_bottom = self.WIDGET_HEIGHT - 28  # 底部留空间给名称和dB值
        track_height = track_bottom - track_top
        
        # ===== 3. 绘制滑块轨道 =====
        track_rect = QRect(margin_x, track_top, self.SLIDER_WIDTH, track_height)
        
        # 轨道背景(深色凹槽)
        painter.fillRect(track_rect, QColor(bg_card))
        painter.setPen(QPen(QColor(border_color), 1))
        painter.drawRoundedRect(track_rect, 3, 3)
        
        # 已填充部分(当前位置到顶部)
        handle_y = self._db_to_y(self._db_value, track_top, track_bottom)
        filled_height = int(track_bottom - handle_y)
        if filled_height > 0:
            filled_rect = QRect(margin_x, int(handle_y), self.SLIDER_WIDTH, filled_height)
            
            # 渐变填充
            gradient = QLinearGradient(0, handle_y, 0, track_bottom)
            gradient.setColorAt(0.0, QColor(slider_color).lighter(130))
            gradient.setColorAt(1.0, QColor(slider_color).darker(120))
            painter.fillRect(filled_rect, gradient)
        
        # ===== 4. 绘制滑块手柄 =====
        handle_rect = QRect(margin_x - 4, int(handle_y) - self.HANDLE_HEIGHT//2,
                           self.SLIDER_WIDTH + 8, self.HANDLE_HEIGHT)
        
        # 手柄渐变(3D立体效果)
        handle_gradient = QLinearGradient(0, handle_rect.top(), 
                                          0, handle_rect.bottom())
        if self.is_master:
            handle_gradient.setColorAt(0.0, QColor('#FFAA66'))   # 亮橙
            handle_gradient.setColorAt(0.5, QColor('#DD6600'))   # 中橙
            handle_gradient.setColorAt(1.0, QColor('#994400'))   # 深橙
        else:
            handle_gradient.setColorAt(0.0, QColor('#66AAFF'))   # 亮蓝
            handle_gradient.setColorAt(0.5, QColor('#2266CC'))   # 中蓝
            handle_gradient.setColorAt(1.0, QColor('#114488'))   # 深蓝
        
        painter.setBrush(handle_gradient)
        painter.setPen(QPen(QColor(border_color), 1))
        painter.drawRoundedRect(handle_rect, 3, 3)
        
        # 手柄上的指示线
        painter.setPen(QPen(QColor(text_primary), 2))
        mid_x = margin_x + self.SLIDER_WIDTH // 2
        painter.drawLine(mid_x - 4, int(handle_y), mid_x + 4, int(handle_y))
        
        # ===== 5. 绘制当前dB值(手柄下方) =====
        font = QFont(get_font_family("mono"), 7, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(text_primary))
        
        if self._db_value <= -59:
            db_text = "-∞"
        else:
            db_text = f"{self._db_value:+.1f}"
        
        # dB值居中显示在手柄下方
        db_text_width = QFontMetrics(font).horizontalAdvance(db_text)
        db_text_x = (self.WIDGET_WIDTH - db_text_width) // 2
        painter.drawText(db_text_x, track_bottom + 12, db_text)
        
        # ===== 6. 绘制底部音轨名称 =====
        font = QFont(get_font_family("ui"), 8)
        painter.setFont(font)
        painter.setPen(QColor(text_muted))
        
        # 截断过长的名称
        display_name = self.track_name[:7] + ".." if len(self.track_name) > 7 else self.track_name
        name_text_width = QFontMetrics(font).horizontalAdvance(display_name)
        name_x = (self.WIDGET_WIDTH - name_text_width) // 2
        painter.drawText(name_x, self.WIDGET_HEIGHT - 4, display_name)
        
        painter.end()

    def mousePressEvent(self, event) -> None:
        """鼠标按下事件 - 开始拖动或双击重置"""
        if event.button() == Qt.LeftButton:
            if event.type() == QEvent.MouseButtonDblClick:
                # 双击: 重置为0dB
                self.set_db_value(0.0)
            else:
                # 单击: 开始拖动
                self._dragging = True
                self._last_y = event.y()
                # 直接跳转到点击位置
                new_db = self._y_to_db(event.y())
                self.set_db_value(new_db)

    def mouseMoveEvent(self, event) -> None:
        """鼠标移动事件 - 拖动调整音量"""
        if self._dragging and event.buttons() & Qt.LeftButton:
            # 根据Y轴移动量计算新dB值
            delta_y = self._last_y - event.y()  # 向上拖=正值(音量增大)
            sensitivity = (self._max_db - self._min_db) / (self.WIDGET_HEIGHT - 40)
            delta_db = delta_y * sensitivity * 2  # 加速拖动
            new_db = self._db_value + delta_db
            self.set_db_value(new_db)
            self._last_y = event.y()

    def mouseReleaseEvent(self, event) -> None:
        """鼠标释放事件 - 结束拖动"""
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def wheelEvent(self, event) -> None:
        """滚轮事件 - 微调音量(每次±1dB)"""
        delta = event.angleDelta().y()
        if delta > 0:
            # 向上滚: 音量增加
            new_db = min(self._max_db, self._db_value + 1.0)
        else:
            # 向下滚: 音量减小
            new_db = max(self._min_db, self._db_value - 1.0)
        self.set_db_value(new_db)


class ProgressBarSlider(QWidget):
    """
    自定义进度条滑块组件 - 支持动态主题切换
    功能: 显示播放进度(0-100%)，支持拖动跳转，支持A-B区域标记
    操作: 左键拖动=跳转, Ctrl+点击=A点, Shift+点击=B点
    主题: 通过 ThemeManager.get() 读取当前主题色
    """
    positionChanged = pyqtSignal(float)
    regionSelected = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._position: float = 0.0
        self._region_start: float = -1.0   # A点(-1表示未设置)
        self._region_end: float = -1.0     # B点
        self._dragging: bool = False

        self.setMinimumHeight(28)
        self.setMaximumHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMouseTracking(True)

    @property
    def position(self) -> float:
        return self._position

    @position.setter
    def position(self, value: float) -> None:
        self._position = max(0.0, min(100.0, value))
        self.update()

    def set_region(self, start: float, end: float) -> None:
        """设置A-B循环区域"""
        self._region_start = min(start, end)
        self._region_end = max(start, end)
        self.update()

    def clear_region(self) -> None:
        """清除A-B循环区域"""
        self._region_start = -1.0
        self._region_end = -1.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 从ThemeManager读取当前主题色
        bg_surface = ThemeManager.get('bg_surface', '#252536')
        accent = ThemeManager.get('accent', '#F97316')
        primary = ThemeManager.get('primary', '#3B82F6')
        primary_light = ThemeManager.get('primary_light', '#60A5FA')
        text_muted = ThemeManager.get('text_muted', '#64748B')

        rect = self.rect()
        bar_height = 6
        bar_y = (rect.height() - bar_height) // 2
        bar_rect = QRect(8, bar_y, rect.width() - 16, bar_height)

        # 背景轨道
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(bg_surface))
        painter.drawRoundedRect(bar_rect, 3, 3)

        # A-B循环区域高亮
        if self._region_start >= 0 and self._region_end > self._region_start:
            rx = bar_rect.x() + int(bar_rect.width() * self._region_start / 100)
            rw = int(bar_rect.width() * (self._region_end - self._region_start) / 100)
            painter.setBrush(QColor(accent + "50"))
            painter.drawRoundedRect(rx, bar_y, max(rw, 1), bar_height, 3, 3)

        # 已播放进度
        pw = int(bar_rect.width() * self._position / 100)
        if pw > 0:
            gradient = QLinearGradient(bar_rect.left(), 0, bar_rect.left() + pw, 0)
            gradient.setColorAt(0, QColor(primary))
            gradient.setColorAt(1, QColor(primary_light))
            painter.setBrush(gradient)
            painter.drawRoundedRect(bar_rect.x(), bar_y, pw, bar_height, 3, 3)

        # 滑块手柄
        hx = bar_rect.x() + int(bar_rect.width() * self._position / 100)
        hy = rect.height() // 2
        # 浅色模式手柄边框用深色，深色模式用白色
        handle_border = '#1E293B' if ThemeManager.is_light() else '#ffffff'
        painter.setPen(QPen(QColor(handle_border), 2))
        painter.setBrush(QColor(primary))
        painter.drawEllipse(QPoint(hx, hy), 9, 9)

        # 位置文字
        painter.setPen(QColor(text_muted))
        painter.setFont(QFont(get_font_family("numeric"), 9))
        painter.drawText(rect.x() + 4, rect.y() + 11, f"{self._position:.1f}%")
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._update_pos(event)
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.ControlModifier:
                self._region_start = self._position
                self.regionSelected.emit(self._region_start, max(self._region_end, 100))
            elif modifiers & Qt.ShiftModifier:
                self._region_end = self._position
                self.regionSelected.emit(max(self._region_start, 0), self._region_end)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self._update_pos(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def _update_pos(self, event: QMouseEvent) -> None:
        rect = self.rect()
        bw = rect.width() - 16
        new_pos = ((event.x() - 8) / bw) * 100 if bw > 0 else 0
        new_pos = max(0.0, min(100.0, new_pos))
        if abs(new_pos - self._position) > 0.05:
            self._position = new_pos
            self.positionChanged.emit(self._position)
            self.update()


class SpeedCurveEditor(QDialog):
    """
    速度曲线编辑器对话框
    功能: 可视化编辑播放速度随时间变化的曲线
    适用: 图片/PDF格式谱子需要变速练习时使用
    X轴=播放进度(%), Y轴=速度值(ms, 越小越快)
    """
    curveUpdated = pyqtSignal(object)

    def __init__(self, parent=None, current_curve: SpeedCurveConfig = None):
        super().__init__(parent)
        self.curve_config = current_curve or SpeedCurveConfig()
        self.init_ui()

    def init_ui(self) -> None:
        """初始化速度曲线编辑器UI - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("speed_curve.window_title"))
        self.setMinimumSize(680, 480)
        # 使用ThemeManager获取当前主题色
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_primary']}; }}
            QLabel {{ color: {t['text_primary']}; font-family: {get_font_family_css('ui')}; }}
            QGroupBox {{ color: {t['text_primary']}; border: 1px solid {t['border']};
                         border-radius: 8px; margin-top: 10px; padding-top: 10px; font-weight: bold; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                          border-radius: 6px; padding: 6px 14px; font-family: {get_font_family_css('ui')}; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
        """)

        layout = QVBoxLayout(self)

        # 启用开关
        top_row = QHBoxLayout()
        self.enable_check = QCheckBox(I18n.t("speed_curve.enable_check"))
        self.enable_check.setChecked(self.curve_config.is_enabled)
        self.enable_check.stateChanged.connect(self._on_enable_changed)
        top_row.addWidget(self.enable_check)
        top_row.addStretch()
        layout.addLayout(top_row)

        # 曲线画布
        canvas_group = QGroupBox(I18n.t("speed_curve.canvas_group"))
        canvas_layout = QVBoxLayout(canvas_group)
        self.canvas_widget = _SpeedCurveCanvas(self, self.curve_config)
        self.canvas_widget.setMinimumHeight(280)
        self.canvas_widget.curveChanged.connect(self._on_curve_changed)
        canvas_layout.addWidget(self.canvas_widget)
        layout.addWidget(canvas_group)

        # 预设按钮
        btn_group = QGroupBox(I18n.t("speed_curve.preset_group"))
        btn_layout = QHBoxLayout(btn_group)
        for name, fn in [(I18n.t("speed_curve.preset_linear"), self._preset_linear), (I18n.t("speed_curve.preset_ease_in"), self._preset_ease_in),
                         (I18n.t("speed_curve.preset_ease_out"), self._preset_ease_out), (I18n.t("speed_curve.preset_ease_in_out"), self._preset_ease_in_out)]:
            btn = QPushButton(name)
            btn.clicked.connect(fn)
            btn.setMaximumWidth(75)
            btn_layout.addWidget(btn)
        clear_btn = QPushButton(I18n.t("speed_curve.clear_all"))
        clear_btn.setStyleSheet(f"background-color: {ThemeManager.get('danger', '#EF4444')};")
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)
        layout.addWidget(btn_group)

        # 说明
        hint = QLabel(I18n.t("speed_curve.hint"))
        hint.setStyleSheet(f"color: {ThemeManager.get('text_muted', '#64748B')}; font-size: 11px;")
        layout.addWidget(hint)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _on_enable_changed(self, state) -> None:
        self.curve_config.is_enabled = (state == Qt.Checked)
        self.canvas_widget.setEnabled(state == Qt.Checked)
        self.curveUpdated.emit(self.curve_config)

    def _on_curve_changed(self, config: SpeedCurveConfig) -> None:
        self.curve_config = config
        self.curveUpdated.emit(config)

    def _preset_linear(self) -> None:
        self.curve_config.points = [SpeedCurvePoint(0, 50), SpeedCurvePoint(100, 50)]
        self.canvas_widget.load_curve(self.curve_config)
        self.curveUpdated.emit(self.curve_config)

    def _preset_ease_in(self) -> None:
        """慢->快: 适合从慢速开始逐渐加速练习"""
        self.curve_config.points = [
            SpeedCurvePoint(0, 120), SpeedCurvePoint(50, 60), SpeedCurvePoint(100, 25)
        ]
        self.canvas_widget.load_curve(self.curve_config)
        self.curveUpdated.emit(self.curve_config)

    def _preset_ease_out(self) -> None:
        """快->慢: 适合开始正常后减速精练"""
        self.curve_config.points = [
            SpeedCurvePoint(0, 25), SpeedCurvePoint(50, 60), SpeedCurvePoint(100, 120)
        ]
        self.canvas_widget.load_curve(self.curve_config)
        self.curveUpdated.emit(self.curve_config)

    def _preset_ease_in_out(self) -> None:
        """慢-快-慢: 两端慢中间快的标准练习曲线"""
        self.curve_config.points = [
            SpeedCurvePoint(0, 100), SpeedCurvePoint(25, 45),
            SpeedCurvePoint(75, 45), SpeedCurvePoint(100, 100)
        ]
        self.canvas_widget.load_curve(self.curve_config)
        self.curveUpdated.emit(self.curve_config)

    def _clear_all(self) -> None:
        """清除所有控制点 - 保留默认线性端点避免空曲线异常"""
        self.curve_config.points = [SpeedCurvePoint(0, 50), SpeedCurvePoint(100, 50)]
        self.canvas_widget.load_curve(self.curve_config)
        self.curveUpdated.emit(self.curve_config)


class _SpeedCurveCanvas(QWidget):
    """
    速度曲线绘图画布内部组件 - 支持动态主题切换
    主题: 通过 ThemeManager.get() 读取当前主题色
    """

    curveChanged = pyqtSignal(object)

    def __init__(self, parent, curve_config: SpeedCurveConfig):
        super().__init__(parent)
        self.curve_config = curve_config
        self._selected_idx: int = -1
        self._dragging: bool = False
        self.setMouseTracking(True)
        self.setMinimumSize(500, 240)

    def load_curve(self, config: SpeedCurveConfig) -> None:
        self.curve_config = config
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 从ThemeManager读取当前主题色
        bg_surface = ThemeManager.get('bg_surface', '#252536')
        border = ThemeManager.get('border', '#3A3A4A')
        text_muted = ThemeManager.get('text_muted', '#64748B')
        primary = ThemeManager.get('primary', '#3B82F6')
        accent = ThemeManager.get('accent', '#F97316')
        accent_light = ThemeManager.get('accent_light', '#FB923C')

        rect = self.rect()
        pad = 40
        draw_rect = QRect(pad, pad, rect.width() - 2*pad, rect.height() - 2*pad)
        painter.fillRect(rect, QColor(bg_surface))

        # 网格
        painter.setPen(QPen(QColor(border), 1, Qt.DotLine))
        for pct in [25, 50, 75]:
            x = draw_rect.x() + int(draw_rect.width()*pct/100)
            painter.drawLine(x, draw_rect.top(), x, draw_rect.bottom())
        for spd in [30, 80, 130]:
            y = draw_rect.bottom() - int(draw_rect.height()*spd/160)
            painter.drawLine(draw_rect.left(), y, draw_rect.right(), y)

        # 坐标标签
        painter.setPen(QColor(text_muted))
        painter.setFont(QFont(get_font_family("numeric"), 9))
        for pct in [0, 25, 50, 75, 100]:
            painter.drawText(draw_rect.x()+int(draw_rect.width()*pct/100)-10, draw_rect.bottom()+16, f"{pct}%")
        for spd in [0, 50, 100, 150]:
            painter.drawText(pad-28, draw_rect.bottom()-int(draw_rect.height()*spd/160)+4, f"{spd}")

        # 绘制曲线
        points = sorted(self.curve_config.points, key=lambda p: p.position)
        if len(points) >= 2:
            path = QPainterPath()
            sx = draw_rect.x()+int(draw_rect.width()*points[0].position/100)
            sy = draw_rect.bottom()-int(draw_rect.height()*points[0].speed/160)
            path.moveTo(sx, draw_rect.bottom())
            path.lineTo(sx, sy)
            for p in points:
                px = draw_rect.x()+int(draw_rect.width()*p.position/100)
                py = draw_rect.bottom()-int(draw_rect.height()*p.speed/160)
                path.lineTo(px, py)
            last_p = points[-1]
            path.lineTo(draw_rect.x()+int(draw_rect.width()*last_p.position/100), draw_rect.bottom())
            path.closeSubpath()
            painter.fillPath(path, QColor(primary + "35"))

            pen = QPen(QColor(primary), 2)
            painter.setPen(pen)
            for i in range(len(points)-1):
                p1, p2 = points[i], points[i+1]
                x1 = draw_rect.x()+int(draw_rect.width()*p1.position/100)
                y1 = draw_rect.bottom()-int(draw_rect.height()*p1.speed/160)
                x2 = draw_rect.x()+int(draw_rect.width()*p2.position/100)
                y2 = draw_rect.bottom()-int(draw_rect.height()*p2.speed/160)
                painter.drawLine(x1, y1, x2, y2)

        # 控制点
        for idx, p in enumerate(points):
            px = draw_rect.x()+int(draw_rect.width()*p.position/100)
            py = draw_rect.bottom()-int(draw_rect.height()*p.speed/160)
            is_sel = (idx==self._selected_idx)
            painter.setPen(QPen(QColor(accent) if is_sel else QColor(primary), 2))
            painter.setBrush(QColor(accent_light) if is_sel else QColor(primary))
            painter.drawEllipse(QPoint(px, py), 8 if is_sel else 6, 8 if is_sel else 6)

        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(draw_rect)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button()==Qt.LeftButton:
            cp = event.pos(); pad=40; dr=QRect(pad,pad,self.width()-2*pad,self.height()-2*pad)
            pts = sorted(self.curve_config.points,key=lambda p:p.position)
            for idx,p in enumerate(pts):
                px=dr.x()+int(dr.width()*p.position/100); py=dr.bottom()-int(dr.height()*p.speed/160)
                if (cp.x()-px)**2+(cp.y()-py)**2<169:
                    self._selected_idx=idx; self._dragging=True; self.update(); return
            if dr.contains(cp):
                np_=max(0,min(100,((cp.x()-pad)/dr.width())*100))
                ns=max(5,min(150,((dr.bottom()-cp.y())/dr.height())*160))
                self.curve_config.points.append(SpeedCurvePoint(np_,ns))
                self._selected_idx=len(self.curve_config.points)-1; self._dragging=True
                self.update(); self.curveChanged.emit(self.curve_config)
        elif event.button()==Qt.RightButton and self._selected_idx>=0:
            pts=sorted(self.curve_config.points,key=lambda p:p.position)
            if 0<=self._selected_idx<len(pts):
                del self.curve_config.points[self._selected_idx]; self._selected_idx=-1
                self.update(); self.curveChanged.emit(self.curve_config)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging and self._selected_idx>=0:
            pos=event.pos(); pad=40; dr=QRect(pad,pad,self.width()-2*pad,self.height()-2*pad)
            pts=sorted(self.curve_config.points,key=lambda p:p.position)
            if 0<=self._selected_idx<len(pts):
                p=pts[self._selected_idx]
                p.position=max(0,min(100,((pos.x()-pad)/dr.width())*100))
                p.speed=max(5,min(150,((dr.bottom()-pos.y())/dr.height())*160))
                self.update(); self.curveChanged.emit(self.curve_config)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging=False


class AnnotationCreateDialog(QDialog):
    """
    新建标注对话框 - 专门用于创建新标注(无删除功能)
    
    与AnnotationEditDialog的区别:
      - 标题: "新建标注" vs "编辑标注"
      - 无删除按钮(新标注不存在删除概念)
      - 只有 [确定] [取消] 两个按钮
    
    调用方式:
      dialog = AnnotationCreateDialog(parent, x, y)
      if dialog.exec_() == QDialog.Accepted:
          ann = dialog.get_annotation()  # 获取新建的标注
    """

    def __init__(self, parent=None, x: float = 0.1, y: float = 0.1):
        super().__init__(parent)
        self.annotation = Annotation(
            id=f"ann_{uuid.uuid4().hex[:8]}", x=x, y=y,
            text=I18n.t("annotation_create.default_text")
        )
        self._temp_color = self.annotation.color
        self.init_ui()

    def init_ui(self)->None:
        """初始化标注编辑对话框UI - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("annotation_create.window_title")); self.setFixedSize(420,360)
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_primary']}; }}
            QLabel {{ color: {t['text_primary']}; font-family: {get_font_family_css('ui')}; }}
            QTextEdit {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: {get_font_family_css('ui')}; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
        """)
        layout=QVBoxLayout(self)
        
        # 位置信息(只读显示)
        pg=QGroupBox(I18n.t("annotation_create.position_group")); pl=QHBoxLayout(pg)
        pl.addWidget(QLabel(I18n.t("annotation_create.coord_display", x=self.annotation.x, y=self.annotation.y))); layout.addWidget(pg)
        
        # 标注内容
        tg=QGroupBox(I18n.t("annotation_create.content_group")); tl=QVBoxLayout(tg)
        self.text_edit=QTextEdit(); self.text_edit.setPlainText(self.annotation.text)
        self.text_edit.setPlaceholderText(I18n.t("annotation_create.placeholder")); tl.addWidget(self.text_edit); layout.addWidget(tg)
        
        # 字体设置
        fg=QGroupBox(I18n.t("annotation_create.font_group")); fl=QHBoxLayout(fg)
        fl.addWidget(QLabel(I18n.t("annotation_create.size_label"))); self.font_size_spin=QSpinBox()
        self.font_size_spin.setRange(8,72); self.font_size_spin.setValue(self.annotation.font_size); fl.addWidget(self.font_size_spin)
        self.bold_check=QCheckBox(I18n.t("annotation_create.bold_check")); self.bold_check.setChecked(self.annotation.is_bold); fl.addWidget(self.bold_check)
        fl.addStretch(); layout.addWidget(fg)
        
        # 颜色选择
        cg=QGroupBox(I18n.t("annotation_create.color_group")); cl=QHBoxLayout(cg)
        self.color_btn=QPushButton(I18n.t("annotation_create.color_btn")); self.color_btn.clicked.connect(self._pick_color)
        self.color_btn.setStyleSheet(f"background-color:{self.annotation.color};color:white;")
        cl.addWidget(self.color_btn); cl.addStretch(); layout.addWidget(cg)

        # 按钮区域: 确定 / 取消 (无删除按钮，因为是新建)
        btn_layout=QHBoxLayout()
        ok_btn=QPushButton(I18n.t("annotation_create.create_btn"))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn=QPushButton(I18n.t("annotation_create.cancel_btn"))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"background-color:{ThemeManager.get('bg_surface', '#252536')};color:{ThemeManager.get('text_secondary', '#94A3B8')};")
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _pick_color(self)->None:
        c=QColorDialog.getColor(QColor(self._temp_color),self,I18n.t("annotation_create.color_dialog_title"))
        if c.isValid(): self._temp_color=c.name(); self.color_btn.setStyleSheet(f"background-color:{self._temp_color};color:white;")

    def get_annotation(self)->Annotation:
        """获取用户输入的标注数据"""
        self.annotation.text=self.text_edit.toPlainText()
        self.annotation.font_size=self.font_size_spin.value()
        self.annotation.is_bold=self.bold_check.isChecked()
        self.annotation.color=self._temp_color
        return self.annotation


class AnnotationEditDialog(QDialog):
    """
    编辑标注对话框 - 专门用于编辑已有标注(含删除功能)
    
    与AnnotationCreateDialog的区别:
      - 标题: "编辑标注" vs "新建标注"
      - 有删除按钮(🗑 删除此标注)
      - 按钮布局: [确定保存] [🗑 删除此标注] [取消]
      - 返回 should_delete 标记告知调用方是否执行删除
    
    调用方式:
      dialog = AnnotationEditDialog(parent, annotation)
      if dialog.exec_() == QDialog.Accepted:
          if dialog.should_delete:  # 用户点击了删除
              # 执行删除逻辑
          else:
              ann = dialog.get_annotation()  # 获取修改后的标注
    """

    def __init__(self, parent=None, annotation: Annotation = None):
        super().__init__(parent)
        self.annotation = annotation or Annotation(
            id=f"ann_{uuid.uuid4().hex[:8]}", x=0.1, y=0.1,
            text=I18n.t("annotation_edit.default_text")
        )
        self._temp_color=self.annotation.color
        self.should_delete = False  # 标记用户是否点击了删除按钮
        self.init_ui()

    def init_ui(self)->None:
        """初始化标注编辑对话框UI(编辑模式) - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("annotation_edit.window_title")); self.setFixedSize(420,400)
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_primary']}; }}
            QLabel {{ color: {t['text_primary']}; font-family: {get_font_family_css('ui')}; }}
            QTextEdit {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: {get_font_family_css('ui')}; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QPushButton#deleteBtn {{ background-color: {ThemeManager.get('danger', '#EF4444')}; }}
            QPushButton#deleteBtn:hover {{ background-color: #DC2626; }}
        """)
        layout=QVBoxLayout(self)
        pg=QGroupBox(I18n.t("annotation_edit.position_group")); pl=QHBoxLayout(pg)
        pl.addWidget(QLabel(I18n.t("annotation_edit.coord_display", x=self.annotation.x, y=self.annotation.y))); layout.addWidget(pg)
        tg=QGroupBox(I18n.t("annotation_edit.content_group")); tl=QVBoxLayout(tg)
        self.text_edit=QTextEdit(); self.text_edit.setPlainText(self.annotation.text)
        self.text_edit.setPlaceholderText(I18n.t("annotation_edit.placeholder")); tl.addWidget(self.text_edit); layout.addWidget(tg)
        fg=QGroupBox(I18n.t("annotation_edit.font_group")); fl=QHBoxLayout(fg)
        fl.addWidget(QLabel(I18n.t("annotation_edit.size_label"))); self.font_size_spin=QSpinBox()
        self.font_size_spin.setRange(8,72); self.font_size_spin.setValue(self.annotation.font_size); fl.addWidget(self.font_size_spin)
        self.bold_check=QCheckBox(I18n.t("annotation_edit.bold_check")); self.bold_check.setChecked(self.annotation.is_bold); fl.addWidget(self.bold_check)
        fl.addStretch(); layout.addWidget(fg)
        cg=QGroupBox(I18n.t("annotation_edit.color_group")); cl=QHBoxLayout(cg)
        self.color_btn=QPushButton(I18n.t("annotation_edit.color_btn")); self.color_btn.clicked.connect(self._pick_color)
        self.color_btn.setStyleSheet(f"background-color:{self.annotation.color};color:white;")
        cl.addWidget(self.color_btn); cl.addStretch(); layout.addWidget(cg)

        # 按钮区域: 确定 / 删除 / 取消 (编辑模式特有删除按钮)
        btn_layout=QHBoxLayout()
        ok_btn=QPushButton(I18n.t("annotation_edit.save_btn"))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        del_btn=QPushButton(I18n.t("annotation_edit.delete_btn"))
        del_btn.setObjectName("deleteBtn")
        del_btn.clicked.connect(self._on_delete_clicked)
        btn_layout.addWidget(del_btn)

        cancel_btn=QPushButton(I18n.t("annotation_edit.cancel_btn"))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"background-color:{ThemeManager.get('bg_surface', '#252536')};color:{ThemeManager.get('text_secondary', '#94A3B8')};")
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _pick_color(self)->None:
        c=QColorDialog.getColor(QColor(self._temp_color),self,I18n.t("annotation_edit.color_dialog_title"))
        if c.isValid(): self._temp_color=c.name(); self.color_btn.setStyleSheet(f"background-color:{self._temp_color};color:white;")

    def _on_delete_clicked(self)->None:
        """点击删除按钮: 设置标记并以Accepted状态关闭(由调用方执行实际删除)"""
        reply = QMessageBox.question(
            self, I18n.t("messages.delete_confirm_title"),
            I18n.t("messages.delete_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.should_delete = True
            self.accept()

    def get_annotation(self)->Annotation:
        self.annotation.text=self.text_edit.toPlainText()
        self.annotation.font_size=self.font_size_spin.value()
        self.annotation.is_bold=self.bold_check.isChecked()
        self.annotation.color=self._temp_color
        return self.annotation


class AnnotationManagerDialog(QDialog):
    """
    标注管理器 - 列表管理所有标注
    
    功能: 新增/编辑/删除标注，支持 Ctrl+Z 撤销 / Ctrl+Y 重做
    注意: 撤销/重做已统一委托给父窗口DisplayWindow的全局栈，
          管理器内的操作与画布双击操作共享同一套撤销历史。
    
    调用方: DisplayWindow._open_annotation_manager()
    """
    annotationsChanged=pyqtSignal(list)

    def __init__(self,parent=None,annotations:List[Annotation]=None):
        super().__init__(parent); self.annotations=annotations or []
        # 引用父窗口的撤销/重做方法(全局统一栈)
        self._parent_window = parent
        self.init_ui()

    def init_ui(self)->None:
        """初始化标注管理器UI(列表模式) - 从ThemeManager读取当前主题"""
        self.setWindowTitle(I18n.t("annotation_manager.window_title")); self.setMinimumSize(550,400)
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QDialog{{background-color:{t['bg_primary']};}}
            QLabel{{color:{t['text_primary']};font-family:{get_font_family_css('ui')};}}
            QListWidget{{background-color:{t['bg_surface']};color:{t['text_primary']};
                        border:1px solid{t['border']};border-radius:6px;}}
            QListWidget::item:selected{{background-color:{t['primary']};}}
            QListWidget::item:hover{{background-color:{t['primary']};opacity:0.15;border-radius:4px;}}
            QPushButton{{background-color:{t['primary']};color:white;border:none;border-radius:6px;padding:7px14px;}}
            QPushButton:hover{{background-color:{t['primary_hover']};}}
            QPushButton#delBtn{{background-color:{ThemeManager.get('danger', '#EF4444')};}}
            QPushButton#delBtn:hover{{background-color:#DC2626;}}
        """)
        layout=QVBoxLayout(self)
        title=QLabel(I18n.t("annotation_manager.list_title", count=len(self.annotations)))
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{ThemeManager.get('primary_light', '#60A5FA')};")
        layout.addWidget(title)
        self.list_widget=QListWidget(); self._populate_list()
        self.list_widget.itemDoubleClicked.connect(self._edit_item); layout.addWidget(self.list_widget)
        bl=QHBoxLayout()
        for txt,slot,st in[(I18n.t("annotation_manager.add_btn"),self._add_new,""),(I18n.t("annotation_manager.edit_btn"),lambda:self._edit_item(self.list_widget.currentItem()), ""),
                             (I18n.t("annotation_manager.delete_btn"),self._delete_item,"#delBtn"),(I18n.t("annotation_manager.clear_btn"),self._clear_all,"#delBtn")]:
            b=QPushButton(txt)
            if st:b.setObjectName(st)
            b.clicked.connect(slot);bl.addWidget(b)
        layout.addLayout(bl)
        bbox=QDialogButtonBox(QDialogButtonBox.Close);bbox.rejected.connect(self.reject);layout.addWidget(bbox)

    def _populate_list(self)->None:
        self.list_widget.clear()
        for a in self.annotations:
            pv=a.text[:28]+"..."if len(a.text)>28 else a.text
            item=QListWidgetItem(f"[{a.id}]({a.x:.0%},{a.y:.0%}){pv}")
            item.setData(Qt.UserRole,a.id);self.list_widget.addItem(item)

    # ========== 撤销/重做(委托给父窗口全局栈) ==========
    def _save_snapshot(self)->None:
        """修改前保存快照 → 委托给父窗口的全局撤销栈"""
        if self._parent_window and hasattr(self._parent_window, '_anno_save_snapshot'):
            self._parent_window._anno_save_snapshot()

    def _undo(self)->None:
        """Ctrl+Z 撤销 → 委托给父窗口"""
        if self._parent_window and hasattr(self._parent_window, '_anno_undo'):
            self._parent_window._anno_undo()
            # 同步本地列表
            self.annotations = self._parent_window.annotations
            self._populate_list()

    def _redo(self)->None:
        """Ctrl+Y 重做 → 委托给父窗口"""
        if self._parent_window and hasattr(self._parent_window, '_anno_redo'):
            self._parent_window._anno_redo()
            # 同步本地列表
            self.annotations = self._parent_window.annotations
            self._populate_list()

    def keyPressEvent(self,event:QKeyEvent)->None:
        """键盘事件: Ctrl+Z撤销 / Ctrl+Y重做"""
        try:
            if event.modifiers()&Qt.ControlModifier:
                if event.key()==Qt.Key_Z:   self._undo()
                elif event.key()==Qt.Key_Y:  self._redo()
                else: super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        except Exception:
            super().keyPressEvent(event)

    # ========== 标注操作(已集成撤销) ==========
    def _add_new(self)->None:
        self._save_snapshot()  # 修改前保存快照(委托给父窗口全局栈)
        dlg=AnnotationEditDialog(self)
        if dlg.exec_()==QDialog.Accepted:
            self.annotations.append(dlg.get_annotation());self._populate_list()
            self.annotationsChanged.emit(self.annotations)
        else:
            # 取消则撤销刚才保存的快照，恢复状态
            self._undo()

    def _edit_item(self,item)->None:
        if not item:return
        aid=item.data(Qt.UserRole);ann=next((a for a in self.annotations if a.id==aid),None)
        if ann:
            self._save_snapshot()  # 修改前保存快照(委托给父窗口全局栈)
            dlg=AnnotationEditDialog(self,annotation=ann)
            if dlg.exec_()==QDialog.Accepted:
                upd=dlg.get_annotation();idx=next(i for i,a in enumerate(self.annotations) if a.id==aid)
                self.annotations[idx]=upd;self._populate_list();self.annotationsChanged.emit(self.annotations)
            else:
                # 取消则撤销刚才保存的快照，恢复状态
                self._undo()

    def _delete_item(self)->None:
        item=self.list_widget.currentItem()
        if item:
            self._save_snapshot()
            aid=item.data(Qt.UserRole)
            self.annotations=[a for a in self.annotations if a.id!=aid];self._populate_list()
            self.annotationsChanged.emit(self.annotations)

    def _clear_all(self)->None:
        if QMessageBox.question(self,I18n.t("messages.clear_all_confirm_title"),I18n.t("messages.clear_all_confirm_msg"),QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self._save_snapshot()
            self.annotations.clear();self._populate_list();self.annotationsChanged.emit(self.annotations)


# ============================================================
# 谱面显示画布组件
# ============================================================

class DisplayWidget(QWidget):
    """
    谱面显示画布组件
    功能: 渲染图片/PDF页面，叠加绘制标注层，支持双击添加/拖动移动/悬停删除标注
    
    标注交互:
      - 双击空白处: 新建标注
      - 双击已有标注: 编辑标注(含删除按钮)
      - 左键按住标注拖动: 移动标注位置(实时预览,松手保存+入撤销栈)
      - 悬停标注: 显示×删除按钮，点击可快速删除
    """

    def __init__(self, parent: 'DisplayWindow' = None):
        super().__init__(parent)
        self.parent_window = parent
        self.images: List[QPixmap] = []
        self.annotations: List[Annotation] = []
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)  # 启用鼠标追踪(不按下也能接收moveEvent)

        # === 标注拖动状态 ===
        self._drag_ann_id: str = ""       # 当前拖动的标注ID(空=未拖动)
        self._drag_start_xy: Tuple[float,float] = (0.0,0.0)  # 拖动开始时的相对坐标
        self._drag_mouse_start: QPoint = QPoint()  # 拖动开始时鼠标屏幕坐标

        # === 标注悬停状态(用于显示删除按钮) ===
        self._hover_ann_id: str = ""       # 当前鼠标悬停的标注ID(空=未悬停)
        self._delete_btn_rect: QRect = QRect()  # 删除按钮的屏幕区域(用于点击检测)
        self._pending_delete_id: str = ""   # 待删除的标注ID(延迟删除机制，双击时清空以取消)

        # === 图片缓存(避免每帧重新scale，解决播放卡顿) ===
        self._cached_scaled: List[QPixmap] = []   # 缩放后的图片缓存
        self._cache_width: int = 0                # 缓存时的画布宽度(宽度变化时失效)
        self._cache_dirty: bool = True            # 缓存是否需要重建

        # === total_h缓存(避免4处重复计算总内容高度) ===
        # total_h = sum(每张图片缩放后高度+5)，在_hit_annotation/_draw_annotations/
        #          mouseMoveEvent/mouseDoubleClickEvent中都需要使用
        self._cached_total_h: float = 0.0         # 缓存的总内容高度
        self._cached_total_h_ww: int = 0          # 缓存时的画布宽度(宽度变化时失效)
        self._total_h_dirty: bool = True           # total_h缓存是否需要重建

        # === 图片LRU缓存（性能优化P2-4: 大文件内存优化） ===
        # 当总页数超过2*_cache_page_window时启用LRU模式，
        # 仅缓存当前页±_cache_page_window范围的缩放图片，大幅减少内存占用。
        # 调整: 增大_window值可提高滚动流畅度但增加内存，减小则反之。
        self._cache_page_window: int = 15          # 每侧缓存页数（共30页活跃窗口）
        self._active_page: int = 0                 # 当前活跃页索引（用于LRU窗口计算）
        self._lru_enabled: bool = False            # LRU模式是否启用

    def set_images(self, images: List[QPixmap]) -> None:
        self.images = images; self._cache_dirty = True; self._total_h_dirty = True; self.update()
        # 检查是否启用LRU模式（总页数超过窗口大小2倍时启用）
        self._lru_enabled = len(images) > self._cache_page_window * 2

    def set_active_page(self, page: int) -> None:
        """
        设置当前活跃页索引（性能优化P2-4: LRU缓存窗口更新）
        
        由DisplayWindow在滚动时调用，通知DisplayWidget当前页面位置，
        DisplayWidget据此调整缩放缓存窗口，仅缓存活跃页附近的图片。
        
        参数:
          page: 当前正在查看的页面索引（0-based）
        """
        if self._lru_enabled and page != self._active_page:
            self._active_page = page
            self._cache_dirty = True  # 窗口移动，需要重建缓存

    def set_annotations(self, annotations: List[Annotation]) -> None:
        self.annotations = annotations; self.update()

    def _rebuild_image_cache(self) -> None:
        """
        重建缩放图片缓存
        
        原理: 将所有原始图片按当前画布宽度预缩放并存入缓存，
              paintEvent时直接使用缓存，避免每帧调用scaled()。
              这是解决播放卡顿的核心优化 — scaled()是CPU密集操作。
        
        性能优化(P2-4): 当LRU模式启用时(总页数>30)，仅缓存当前页±15页范围的
                        缩放图片。大幅减少内存占用（200页文件可节省约500MB）。
                        调整 _cache_page_window 值可平衡滚动流畅度与内存占用。
        
        触发时机:
          - set_images()后首次绘制
          - 画布宽度变化(resizeEvent)
          - 滚动到新页面区域(set_active_page)
        """
        if not self._cache_dirty and self._cache_width == self.width():
            return  # 缓存有效，无需重建
        ww = self.width()
        if ww <= 20 or not self.images:
            self._cached_scaled = []; self._cache_width = ww; self._cache_dirty = False
            return
        sw = ww - 20

        if self._lru_enabled:
            # LRU模式: 仅缓存当前活跃页附近的缩放图片
            n = len(self.images)
            start = max(0, self._active_page - self._cache_page_window)
            end = min(n, self._active_page + self._cache_page_window + 1)
            # 创建全空列表，仅填充活跃窗口内的缓存
            self._cached_scaled = [QPixmap()] * n
            for i in range(start, end):
                img = self.images[i]
                if img.isNull():
                    continue
                ratio = sw / img.width() if img.width() > 0 else 1
                sh = int(img.height() * ratio)
                self._cached_scaled[i] = img.scaled(sw, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # 常规模式: 缓存所有图片（小文件，页数少）
            self._cached_scaled = []
            for img in self.images:
                if img.isNull():
                    self._cached_scaled.append(QPixmap())
                    continue
                ratio = sw / img.width() if img.width() > 0 else 1
                sh = int(img.height() * ratio)
                self._cached_scaled.append(
                    img.scaled(sw, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        self._cache_width = ww
        self._cache_dirty = False

    def resizeEvent(self, event) -> None:
        """窗口大小变化 → 图片缓存失效(需要重新缩放) + total_h缓存失效"""
        super().resizeEvent(event)
        self._cache_dirty = True
        self._total_h_dirty = True

    def _get_total_h(self) -> float:
        """
        获取总内容高度(带缓存)

        原理: total_h = sum(每张图片缩放后高度 + 5px间距)，
              在_hit_annotation/_draw_annotations/mouseMoveEvent/mouseDoubleClickEvent
              中都需要此值。缓存避免4处重复的O(n)浮点计算。

        失效时机: set_images() / resizeEvent() 时标记dirty
        """
        if not self._total_h_dirty and self._cached_total_h_ww == self.width():
            return self._cached_total_h
        ww = self.width()
        if ww <= 20 or not self.images:
            self._cached_total_h = 0.0; self._cached_total_h_ww = ww; self._total_h_dirty = False
            return 0.0
        sw = ww - 20
        total = sum((img.height() * sw / img.width()) + 5 for img in self.images if not img.isNull())
        self._cached_total_h = total
        self._cached_total_h_ww = ww
        self._total_h_dirty = False
        return total

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        鼠标滚轮事件 - 滚动谱面位置
        原理: 滚轮每滚动一个单位(delta)，按比例调整 current_position
        方向: 向上滚=向上翻(减小position), 向下滚=向下翻(增大position)
        """
        if not self.parent_window or not self.parent_window.images:
            event.ignore(); return
        # 获取滚轮滚动量 (angleDelta().y() 正值=向上, 负值=向下)
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore(); return
        # 每次滚动移动的距离: 默认30px，可配合Ctrl加速
        step = 30
        if event.modifiers() & Qt.ControlModifier:
            step = 100  # Ctrl+滚轮快速滚动
        if event.modifiers() & Qt.ShiftModifier:
            step = 10   # Shift+滚轮精细滚动
        # 向上滚(正值)=减小position(内容上移/视口下移)
        self.parent_window.current_position -= (step if delta > 0 else -step)
        # 限制范围(与_calculate_total_distance一致，使用display_widget高度)
        max_pos = max(0, self.parent_window.total_scroll_distance)
        self.parent_window.current_position = max(0, min(self.parent_window.current_position, max_pos))
        self.parent_window.update_progress_display()
        self.parent_window._sync_play_time_from_position()  # 同步播放时间(滚轮改变位置后)
        self.update()
        event.accept()

    def _hit_annotation(self, cx: int, cy: int) -> Optional[Annotation]:
        """
        检测坐标(cx,cy)是否命中某个标注(用于拖动/编辑/悬停删除)
        
        原理: 遍历所有标注，将相对坐标映射到屏幕绝对坐标，
              使用与_draw_one_ann完全相同的bg_rect计算方式，
              检测鼠标是否落在标注的描边矩形范围内。
        
        命中区域 = _draw_one_ann中的bg_rect(含padding+圆点) + 右侧×按钮预留空间
                   (因为×按钮画在bg_rect右侧，鼠标移过去不能离开命中区域)
        
        参数:
            cx, cy: 鼠标在画布上的屏幕坐标(px)
        返回:
            命中的Annotation对象，未命中返回None
        """
        if not self.parent_window or not self.parent_window.annotations or not self.images:
            return None
        ww = self.width()
        if ww <= 20:
            return None
        total_h = self._get_total_h()
        if total_h <= 0:
            return None
        base_y = -self.parent_window.current_position

        for ann in self.parent_window.annotations:
            sx = int(10 + (ww - 20) * ann.x)
            sy = int(base_y + total_h * ann.y)
            
            # 使用与_draw_one_ann完全相同的bg_rect计算方式
            font = QFont(ann.font_family, ann.font_size)
            if ann.is_bold:
                font.setWeight(QFont.Bold)
            metrics = QFontMetrics(font)
            tw = metrics.horizontalAdvance(ann.text)
            th = metrics.height()
            pad = 5  # 与_draw_one_ann中一致
            
            # bg_rect的四个边界 (与_draw_one_ann中QRect(x-pad,y-th-pad,tw+2*pad,th+2*pad)一致)
            bg_left = sx - pad
            bg_top = sy - th - pad
            bg_right = sx + tw + pad
            bg_bottom = sy + pad + 6  # 含圆点(drawEllipse(x-3,y+2,6,6))的高度
            
            # === 关键修复: 扩展右边界以包含×删除按钮 ===
            # ×按钮位置: btn_x = x + tw + pad + 4, btn_size=18
            # 所以需要额外预留约28px(间距4 + 按钮宽18 + 余量6)
            btn_extra = 28
            bg_right_extended = bg_right + btn_extra
            
            # 检测是否在扩展后的命中区域内(标注描边范围 + 右侧×按钮区域)
            if (bg_left <= cx <= bg_right_extended) and (bg_top <= cy <= bg_bottom):
                return ann
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        鼠标按下 - 检测标注拖动 或 点击谱面跳转播放
        
        原理: 左键按下时按优先级处理:
              1. 检测是否命中标注 → 进入拖动模式
              2. 未命中标注 → 跳转到点击位置并开始播放(单击=跳转+播放)
              
        点击位置计算: 基于鼠标Y坐标在总内容高度中的相对比例，
                      映射到scroll_y(0~total_scroll_distance)
        """
        if (event.button() == Qt.LeftButton and
                self.parent_window and self.parent_window.images):
            ann = self._hit_annotation(event.x(), event.y())
            if ann:
                # 命中标注 → 进入拖动模式
                self._drag_ann_id = ann.id
                self._drag_start_xy = (ann.x, ann.y)
                self._drag_mouse_start = event.pos()
                self.setCursor(Qt.ClosedHandCursor)  # 抓手光标
                event.accept()
                return
            
            # === 未命中标注 → 点击谱面跳转到该位置并开始播放 ===
            # [v2.0.6 重构] 以"小节"为单位进行定位，与A/B循环的小节原子单位一致
            #   旧方案: 精确像素跳转 → 可能跳到小节中间位置
            #   新方案: 点击任意位置 → 自动对齐到所在小节的起始拍
            #
            # A/B循环联动:
            #   - 循环激活 + 点击小节在区间外 → 忽略跳转，维持循环播放
            #   - 循环未激活 / 点击小节在区间内 → 跳转到小节开头并播放
            ww = self.width()
            if ww > 20:
                if self.parent_window.total_scroll_distance > 0:
                    click_y = event.y()  # 点击在画布中的Y坐标

                    # === 计算点击处的绝对Y坐标(精确版) ===
                    precise_abs_y = self.parent_window.current_position
                    found_image = False
                    remaining_y = click_y
                    for cached in self._cached_scaled:
                        if cached.isNull():
                            continue
                        img_h = cached.height()
                        if remaining_y < img_h + 5:
                            precise_abs_y += remaining_y
                            found_image = True
                            break
                        remaining_y -= (img_h + 5)
                        precise_abs_y += (img_h + 5)
                    if not found_image:
                        precise_abs_y = self.parent_window.current_position + click_y

                    click_abs_y = precise_abs_y

                    # === 尝试以小节为单位定位(GTP模式) ===
                    measure_info = None
                    use_measure_jump = False
                    
                    if (self.parent_window.gtp_player and 
                        self.parent_window.gtp_player.is_audio_ready and
                        len(self.parent_window._playhead_timeline) >= 2):
                        # GTP模式: 使用小节级别定位
                        measure_info = self.parent_window.gtp_player.find_measure_at_scroll_pos(
                            click_abs_y
                        )
                        
                        if measure_info:
                            # 检查A/B循环区间约束
                            loop_active = (
                                self.parent_window.loop_config.is_enabled 
                                and self.parent_window.loop_config.loop_type == 'region'
                            )
                            
                            if loop_active:
                                loop_start_ms, loop_end_ms = (
                                    self.parent_window.gtp_player.loop_time_range
                                )
                                target_ms = measure_info['start_time_ms']
                                
                                # 判断目标小节是否在循环区间内
                                # 允许微小误差(±50ms): 避免边界值因时间精度问题被误判为"区间外"
                                if target_ms < loop_start_ms - 50 or target_ms > loop_end_ms + 50:
                                    print(f"[ClickMeasure] 小节[{measure_info['meas_idx']}] "
                                          f"(time={target_ms:.0f}ms) 在循环区间 "
                                          f"[{loop_start_ms:.0f}-{loop_end_ms:.0f}ms] 之外, 忽略跳转")
                                    event.accept()
                                    return  # 区间外: 不执行跳转,维持当前循环
                                
                                print(f"[ClickMeasure] 小节[{measure_info['meas_idx']}] "
                                      f"(time={target_ms:.0f}ms) 在循环区间内, 允许跳转")
                            
                            use_measure_jump = True
                    
                    if use_measure_jump and measure_info:
                        # === 小节单位跳转: 对齐到该小节第一个拍 ===
                        new_position = measure_info['start_scroll_y']
                        new_position = max(0, min(new_position, self.parent_window.total_scroll_distance))
                        target_ms = measure_info['start_time_ms']
                        
                        print(f"[ClickMeasure] 跳转到小节[{measure_info['meas_idx']}] "
                              f"pos={new_position:.0f}px time={target_ms:.0f}ms")
                        
                        # 步骤1: 设置视觉位置和跳转目标
                        self.parent_window.current_position = new_position
                        self.parent_window._click_jump_target = new_position
                        self.parent_window.update_progress_display()
                        self.parent_window.play_time = target_ms / 1000.0
                        
                        # 步骤2: 音频seek到小节起始位置
                        if target_ms > 0:
                            try:
                                self.parent_window.gtp_player.seek(target_ms)
                            except Exception as e:
                                print(f"[ClickMeasure] seek失败: {e}")
                    
                    else:
                        # === 降级: 非GTP模式或无时间线时使用原始像素跳转 ===
                        click_offset = 0
                        new_position = max(0, min(
                            click_abs_y - click_offset, 
                            self.parent_window.total_scroll_distance
                        ))
                        
                        self.parent_window.current_position = new_position
                        self.parent_window._click_jump_target = new_position
                        self.parent_window.update_progress_display()
                        self.parent_window._sync_play_time_from_position()

                        target_ms = 0
                        if (self.parent_window.gtp_player and
                            self.parent_window.gtp_player.is_audio_ready):
                            try:
                                target_ms = self.parent_window.gtp_player.scroll_pos_to_time(
                                    new_position,
                                    self.parent_window.total_scroll_distance,
                                    0
                                )
                                if target_ms > 0:
                                    self.parent_window.gtp_player.seek(target_ms)
                            except Exception as e:
                                print(f"[ClickPlay] seek失败: {e}")

                # === 启动/继续播放 ===
                if not self.parent_window.timer.isActive():
                    self.parent_window.toggle_playback()

                self.update()  # 立即更新显示
            
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        鼠标移动 - 拖动标注实时更新位置 + 悬停检测(显示删除按钮)
        
        原理:
          - 拖动中: 实时计算新的相对坐标(x,y)并更新标注位置
          - 非拖动: 检测是否悬停在标注上，更新悬停状态以显示/隐藏删除按钮
        """
        if (self._drag_ann_id and
                self.parent_window and self.parent_window.images):
            ww = self.width()
            if ww > 20:
                # 计算鼠标偏移量 → 映射到相对坐标变化
                dx = event.x() - self._drag_mouse_start.x()
                dy = event.y() - self._drag_mouse_start.y()
                total_h = self._get_total_h()
                if total_h > 0:
                    rel_dx = dx / (ww - 20)
                    rel_dy = dy / total_h
                    new_x = max(0.0, min(1.0, self._drag_start_xy[0] + rel_dx))
                    new_y = max(0.0, min(1.0, self._drag_start_xy[1] + rel_dy))
                    # 实时更新标注位置(仅视觉，不入栈)
                    for a in self.parent_window.annotations:
                        if a.id == self._drag_ann_id:
                            a.x = new_x; a.y = new_y; break
                    self.update()  # 重绘显示新位置
            event.accept()
            return

        # 非拖动状态: 更新光标样式 + 悬停检测(用于显示删除按钮)
        if self.parent_window and self.parent_window.images:
            ann = self._hit_annotation(event.x(), event.y())
            if ann:
                self.setCursor(Qt.OpenHandCursor)
                # 更新悬停状态(如果变化则重绘以显示删除按钮)
                if self._hover_ann_id != ann.id:
                    self._hover_ann_id = ann.id
                    self.update()  # 触发重绘显示删除按钮
            else:
                self.setCursor(Qt.ArrowCursor)
                # 清除悬停状态(隐藏删除按钮)
                if self._hover_ann_id:
                    self._hover_ann_id = ""
                    self.update()  # 触发重绘隐藏删除按钮
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        鼠标释放 - 结束拖动/点击删除按钮，保存快照+持久化
        
        原理:
          - 拖动结束: 保存位置变化到撤销栈和文件
          - 非拖动但悬停状态: 检测是否点击了删除按钮区域
        
        [v2.0.2 Bug修复] 双击标注误删问题:
          - 问题: 双击标注时，第一次mouseReleaseEvent会误判为"点击删除按钮"
                 导致标注被删除，后续mouseDoubleClickEvent无法打开编辑界面
          - 修复: 使用QTimer.singleShot延迟删除(200ms)，如果在双击间隔内收到双击事件则取消删除
        """
        from PyQt5.QtWidgets import QApplication

        if event.button() == Qt.LeftButton and self._drag_ann_id:
            self.setCursor(Qt.ArrowCursor)
            # === 区分"点击×删除按钮"和"拖动标注" ===
            # 原理: _hit_annotation() 扩展了右边界28px以包含×删除按钮，
            #       导致点×区域也会进入拖动模式。需要在release时判断：
            #       鼠标几乎没移动(是点击而非拖动) + 在×按钮精确区域内 → 走删除逻辑
            #
            # [v2.0.2修复] 只有点击×按钮的精确区域(_delete_btn_rect)才触发删除，
            #              不再使用 _hit_annotation() 作为删除判断条件(避免双击误删)
            drag_distance = (event.pos() - self._drag_mouse_start).manhattanLength()
            is_click_not_drag = (drag_distance < 5)  # 移动<5px视为点击
            is_on_x_button = self._delete_btn_rect.contains(event.pos())  # 只检测×按钮精确区域

            if is_click_not_drag and is_on_x_button and self.parent_window:
                # 点击了×删除按钮 → 延迟执行删除(200ms后)，以便区分单击和双击
                del_id = self._drag_ann_id  # _drag_ann_id就是当前标注ID
                self._pending_delete_id = del_id  # 记录待删除的标注ID

                def do_delete():
                    """延迟执行的删除操作"""
                    if hasattr(self, '_pending_delete_id') and self._pending_delete_id and self._pending_delete_id == del_id:
                        self.parent_window._anno_save_snapshot()
                        self.parent_window.annotations = [
                            a for a in self.parent_window.annotations if a.id != del_id
                        ]
                        self.parent_window._save_annotations()
                        self.set_annotations(self.parent_window.annotations)
                        self._hover_ann_id = ""
                        self._delete_btn_rect = QRect()
                        self._drag_ann_id = ""
                        self._pending_delete_id = ""

                # 延迟200ms执行删除(QApplication.doubleClickInterval()通常为400ms)
                QTimer.singleShot(200, do_delete)
                event.accept()
                return

            if self.parent_window:
                # 正常拖动结束: 检查位置是否有实际变化
                for a in self.parent_window.annotations:
                    if a.id == self._drag_ann_id:
                        if (abs(a.x - self._drag_start_xy[0]) > 0.001 or
                                abs(a.y - self._drag_start_xy[1]) > 0.001):
                            self.parent_window._anno_save_snapshot()
                            self.parent_window._save_annotations()
                        break
            self._drag_ann_id = ""
            event.accept()
            return

        # === 检测是否点击了×删除按钮(非拖动状态下) ===
        # [v2.0.2修复] 只有点击×按钮的精确区域(_delete_btn_rect)才触发删除，
        #              不再使用 _hit_annotation() 作为删除判断条件(避免双击误删)
        is_on_x_button = self._delete_btn_rect.contains(event.pos())
        if event.button() == Qt.LeftButton and self._hover_ann_id and is_on_x_button:
            if self.parent_window:
                # 点击了×按钮 → 延迟执行删除(200ms)，以便区分单击和双击
                del_id = self._hover_ann_id
                self._pending_delete_id = del_id  # 记录待删除的标注ID

                def do_delete2():
                    """延迟执行的删除操作（非拖动状态）"""
                    if hasattr(self, '_pending_delete_id') and self._pending_delete_id and self._pending_delete_id == del_id:
                        self.parent_window._anno_save_snapshot()  # 删除前保存快照(支持撤销)
                        self.parent_window.annotations = [
                            a for a in self.parent_window.annotations if a.id != del_id
                        ]
                        self.parent_window._save_annotations()
                        self.set_annotations(self.parent_window.annotations)
                        # 清除悬停状态
                        self._hover_ann_id = ""
                        self._delete_btn_rect = QRect()
                        self._pending_delete_id = ""

                # 延迟200ms执行删除
                QTimer.singleShot(200, do_delete2)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 从ThemeManager读取当前主题色
        bg_secondary = ThemeManager.get('bg_secondary', '#1E1E2E')
        text_muted = ThemeManager.get('text_muted', '#64748B')
        primary = ThemeManager.get('primary', '#3B82F6')

        painter.fillRect(self.rect(), QColor(bg_secondary))

        if not self.images:
            painter.setPen(QColor(text_muted))
            painter.setFont(QFont(get_font_family("ui"),15))
            painter.drawText(self.rect(),Qt.AlignCenter,
                I18n.t("messages.open_file_hint"))
            painter.end(); return

        ww=self.width()
        base_y=-(self.parent_window.current_position if self.parent_window else 0)

        # 使用缓存的缩放图片(避免每帧重新scaled，解决播放卡顿)
        self._rebuild_image_cache()
        sw=ww-20
        for i, cached in enumerate(self._cached_scaled):
            if cached.isNull(): continue
            sh=cached.height()
            target=QRect(10,int(base_y),sw,int(sh))
            if target.bottom()>0 and target.top()<self.height():
                painter.drawPixmap(target,cached,cached.rect())
            base_y+=sh+5

        # 绘制标注层
        self._draw_annotations(painter)
        
        # Phase 3: 绘制当前播放音符高亮(音频同步)
        self._draw_audio_highlight(painter)
        
        # Phase 3.5: 绘制播放光标(Playhead) - 移动竖条+小节高亮
        self._draw_playhead(painter)

        # 加载遮罩
        if self.parent_window and self.parent_window.is_loading:
            painter.fillRect(self.rect(),QColor(0,0,0,120))
            painter.setPen(QColor(primary))
            painter.setFont(QFont(get_font_family("ui"),18))
            painter.drawText(self.rect(),Qt.AlignCenter,I18n.t("messages.loading"))
        painter.end()

    def _draw_annotations(self,painter:QPainter)->None:
        """
        绘制所有标注 + 悬停时的删除按钮
        """
        if not self.images or not self.annotations:return
        ww=self.width()
        base_y=-(self.parent_window.current_position if self.parent_window else 0)
        total_h=self._get_total_h()
        # 重置删除按钮区域(会在_draw_one_ann中设置)
        self._delete_btn_rect = QRect()
        for ann in self.annotations:
            sx=int(10+(ww-20)*ann.x); sy=int(base_y+total_h*ann.y)
            if -60<sy<self.height()+60: 
                is_hover = (self._hover_ann_id == ann.id)
                self._draw_one_ann(painter,ann,sx,sy,is_hover)

    def _draw_one_ann(self,painter:QPainter,ann:Annotation,x:int,y:int,is_hover:bool=False)->None:
        """
        绘制单个标注(含悬停时显示的删除按钮)
        
        参数:
            painter: QPainter绘图对象
            ann: 要绘制的标注数据
            x, y: 标注的屏幕坐标(左下角基准点)
            is_hover: 是否处于鼠标悬停状态(True则绘制×删除按钮)
        """
        font=QFont(ann.font_family,ann.font_size)
        if ann.is_bold:font.setWeight(QFont.Bold)
        painter.setFont(font)
        metrics=painter.fontMetrics(); tw=metrics.horizontalAdvance(ann.text); th=metrics.height()
        pad=5; bg_rect=QRect(x-pad,y-th-pad,tw+2*pad,th+2*pad)
        painter.fillRect(bg_rect,QColor(ann.background_color))
        painter.setPen(QPen(QColor(ann.color),1));painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(bg_rect,4,4)
        painter.setPen(QColor(ann.color));painter.drawText(x,y,ann.text)
        painter.setBrush(QColor(ann.color));painter.setPen(Qt.NoPen)
        painter.drawEllipse(x-3,y+2,6,6)

        # === 悬停时绘制×删除按钮 ===
        if is_hover:
            btn_size = 18  # 删除按钮大小(px)
            btn_x = x + tw + pad + 4  # 按钮在标注文字右侧
            btn_y = y - th - pad + 2   # 与标注垂直居中对齐
            btn_rect = QRect(btn_x, btn_y, btn_size, btn_size)

            # 记录按钮区域(用于mouseReleaseEvent点击检测)
            self._delete_btn_rect = btn_rect

            # 绘制按钮背景(红色圆形)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#EF4444"))  # 红色背景
            painter.setPen(QPen(QColor("#DC2626"), 1))  # 深红边框
            painter.drawEllipse(btn_rect)

            # 绘制×符号(白色两笔交叉线)
            painter.setPen(QPen(QColor("#FFFFFF"), 2))  # 白色线条
            margin = 5  # ×符号距离边缘的间距
            # 第一条斜线(左上→右下)
            painter.drawLine(
                btn_x + margin, btn_y + margin,
                btn_x + btn_size - margin, btn_y + btn_size - margin
            )
            # 第二条斜线(右上→左下)
            painter.drawLine(
                btn_x + btn_size - margin, btn_y + margin,
                btn_x + margin, btn_y + btn_size - margin
            )

    def _draw_audio_highlight(self, painter: QPainter)->None:
        """
        Phase 3: 绘制当前播放音符的视觉高亮
        
        原理: 当音频引擎播放到某个 note_on 事件时，
              通过回调记录当前发声的 MIDI 音高，
              在谱面可视区域绘制一个半透明高亮条，
              表示当前正在播放的音符位置。
        
        视觉效果: 
          - 水平高亮条横跨整个画布宽度
          - 颜色随力度变化(弱=蓝/中=绿/强=橙)
          - 半透明(40%不透明度)避免遮挡谱面内容
        """
        if not self.parent_window:
            return
        
        highlight = self.parent_window._current_highlight
        if not highlight:
            return
        
        midi_pitch, velocity, time_ms = highlight
        
        # 根据力度选择颜色
        # 弱声(0-60)→蓝色, 中强(61-100)→绿色, 强力(101-127)→橙色
        if velocity < 60:
            color = QColor("#3B82F6")   # 蓝色
        elif velocity < 101:
            color = QColor("#22C55E")   # 绿色
        else:
            color = QColor("#F97316")   # 橙色
        
        # 绘制顶部高亮指示条
        bar_height = 3  # 高亮条高度(px)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), 100))  # 40%透明
        painter.drawRect(0, 0, self.width(), bar_height)
        
        # 绘制当前音高信息文字（右上角）
        painter.setPen(color)
        painter.setFont(QFont(get_font_family("numeric"), 9))
        pitch_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
        octave = midi_pitch // 12 - 1
        note_name = pitch_names[midi_pitch % 12]
        info_text = f"{note_name}{octave} (vel:{velocity})"
        painter.drawText(self.width() - 80, 14, info_text)

    def _draw_playhead(self, painter: QPainter)->None:
        """
        Phase 3.5: 绘制播放光标(Playhead) - 移动竖条 + 当前小节高亮
        
        原理:
          从 parent_window._playhead_info 获取当前播放位置信息，
          该信息由 _update_playhead() 每帧更新，包含:
            - 当前所在页面/系统(行)/小节/拍
            - 光标在原始渲染坐标系中的X坐标
          
          绘制时需要将原始坐标映射到显示坐标(考虑图像缩放和滚动偏移)。
        
        视觉效果:
          1. 当前播放小节的半透明背景高亮(淡蓝色)
          2. 一条从谱顶到底的红色竖线表示播放位置
          3. 竖线上方有一个小三角形指示器
          4. 仅在正在播放时显示(定时器激活状态)
        """
        if not self.parent_window:
            return
        
        # 非播放状态不绘制光标
        if not self.parent_window.timer.isActive():
            return
        
        info = self.parent_window._playhead_info
        if not info or len(info) < 6:
            return
        
        page_idx, sys_idx, meas_idx, beat_idx, x_orig, progress = info
        
        # === 计算该页面在显示区域中的位置 ===
        if page_idx >= len(self.images):
            return
        
        img = self.images[page_idx]
        if img.isNull():
            return
        
        ww = self.width()
        sw = ww - 20  # 显示宽度(去除左右边距)
        
        # 图像缩放比: 显示像素 / 原始像素
        ratio = sw / img.width() if img.width() > 0 else 1
        
        # 计算该页面在所有页面中的累积Y偏移
        page_y_offset = 0.0
        for i in range(page_idx):
            prev_img = self.images[i]
            if prev_img.isNull():
                continue
            prev_ratio = sw / prev_img.width() if prev_img.width() > 0 else 1
            page_y_offset += prev_img.height() * prev_ratio + 5
        
        # 该页面的显示区域
        page_display_top = 10 + page_y_offset - (self.parent_window.current_position or 0)
        page_h = img.height() * ratio
        
        # 如果该页面不在可视区域内 → 不绘制
        if page_display_top + page_h < 0 or page_display_top > self.height():
            return
        
        # === 将原始X坐标转换为显示X坐标 ===
        display_x = 10 + x_orig * ratio
        
        # 获取布局数据中的Y范围(用于限制竖线高度到六线谱区域)
        layouts = getattr(self.parent_window, '_page_layouts', None)
        line_top = page_display_top
        line_bottom = page_display_top + page_h
        
        if layouts and page_idx < len(layouts):
            page_layout = layouts[page_idx]
            if sys_idx < len(page_layout.systems):
                system = page_layout.systems[sys_idx]
                # 系统的Y范围(原始坐标→显示坐标)
                sys_top = page_display_top + system.y_tab_top * ratio
                sys_bottom = page_display_top + system.y_tab_bottom * ratio
                line_top = max(line_top, int(sys_top))
                line_bottom = min(line_bottom, int(sys_bottom))
        
        # === 1. 绘制当前小节背景高亮 ===
        if layouts and page_idx < len(layouts):
            page_layout = layouts[page_idx]
            if sys_idx < len(page_layout.systems):
                system = page_layout.systems[sys_idx]
                if meas_idx < len(system.measures):
                    m_layout = system.measures[meas_idx]
                    mx1 = 10 + m_layout.x_start * ratio
                    mx2 = 10 + m_layout.x_end * ratio
                    my1 = page_display_top + system.y_top * ratio
                    my2 = page_display_top + system.y_bottom * ratio
                    
                    # 半透明淡蓝背景
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(59, 130, 246, 25))  # 淡蓝 10%透明
                    painter.drawRect(int(mx1), int(my1), int(mx2 - mx1), int(my2 - my1))
                    
                    # 小节号标签
                    painter.setPen(QColor(59, 130, 246, 180))
                    painter.setFont(QFont(get_font_family("numeric"), 8))
                    painter.drawText(int(mx1) + 2, int(my1) + 10, f"{meas_idx + 1}")
        
        # === 2. 绘制竖线(Playhead Line) ===
        # 主竖线: 红色半透明, 宽2px
        pen = QPen(QColor(239, 68, 68, 200))  # 红色
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(int(display_x), max(0, int(line_top)), 
                        int(display_x), min(self.height(), int(line_bottom)))
        
        # 发光效果: 在主竖线两侧各画一条更细更透明的线
        glow_pen = QPen(QColor(239, 68, 68, 60))
        glow_pen.setWidth(4)
        painter.setPen(glow_pen)
        painter.drawLine(int(display_x), max(0, int(line_top)), 
                        int(display_x), min(self.height(), int(line_bottom)))
        
        # === 3. 绘制顶部三角形指示器 ===
        tri_size = 6
        tri_y = max(0, int(line_top)) - 2
        triangle = QPolygonF([
            QPointF(display_x, tri_y),
            QPointF(display_x - tri_size, tri_y - tri_size),
            QPointF(display_x + tri_size, tri_y - tri_size),
        ])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(239, 68, 68, 220))
        painter.drawPolygon(triangle)

    def mouseDoubleClickEvent(self,event:QMouseEvent)->None:
        """
        双击谱面 - 检测是否点击了已有标注(编辑模式)
        
        功能: 双击已有标注可打开编辑对话框进行修改或删除
        创建标注请使用: Ctrl+K快捷键 或 右键菜单"添加标注"
        
        [v2.0.2 修复] 取消延迟删除:
          - 原因: mouseReleaseEvent会延迟200ms执行删除(区分单击/双击)
          - 修复: 双击时清除_pending_delete_id，取消待执行的删除操作
        
        命中区域: 基于_draw_one_ann中的bg_rect描边矩形(含padding)
        """
        # === 取消可能存在的延迟删除操作 ===
        if hasattr(self, '_pending_delete_id'):
            self._pending_delete_id = ""  # 清除待删除ID，取消延迟删除

        if not self.parent_window or not self.parent_window.images: return
        cx,cy=event.x(),event.y()
        ww=self.width()

        # === 检测是否点击了已有标注(命中区域=bg_rect描边范围) ===
        if self.parent_window.annotations and ww>20:
            total_h=self._get_total_h()
            base_y=-self.parent_window.current_position
            target_ann_id = None
            for ann in self.parent_window.annotations:
                sx=int(10+(ww-20)*ann.x); sy=int(base_y+total_h*ann.y)
                # 使用与_draw_one_ann相同的bg_rect计算方式(基于QFontMetrics精确测量)
                font = QFont(ann.font_family, ann.font_size)
                if ann.is_bold:
                    font.setWeight(QFont.Bold)
                metrics = QFontMetrics(font)
                tw = metrics.horizontalAdvance(ann.text); th = metrics.height()
                pad = 5  # 与_draw_one_ann中一致
                bg_left = sx - pad; bg_top = sy - th - pad
                bg_right = sx + tw + pad; bg_bottom = sy + pad + 6  # 含圆点高度
                # 检测是否在bg_rect范围内(标注的完整描边区域)
                if (bg_left <= cx <= bg_right) and (bg_top <= cy <= bg_bottom):
                    target_ann_id = ann.id  # 记录目标标注ID
                    # 点击到已有标注 → 打开编辑对话框(集成全局撤销+删除)
                    self.parent_window._anno_save_snapshot()  # 修改前保存快照
                    dlg=AnnotationEditDialog(self,annotation=ann)
                    if dlg.exec_()==QDialog.Accepted:
                        if dlg.should_delete:
                            # 用户点击了删除按钮 → 根据ID移除该标注
                            self.parent_window.annotations = [
                                a for a in self.parent_window.annotations if a.id != target_ann_id
                            ]
                            self.parent_window._save_annotations()
                            self.set_annotations(self.parent_window.annotations)
                        else:
                            # 正常保存修改(使用ID定位)
                            updated=dlg.get_annotation()
                            idx=next((i for i,a in enumerate(self.parent_window.annotations) if a.id==target_ann_id),None)
                            if idx is not None:
                                self.parent_window.annotations[idx]=updated
                                self.parent_window._save_annotations()
                                self.set_annotations(self.parent_window.annotations)
                    else:
                        # 取消编辑 → 撤销刚才保存的快照
                        if self.parent_window._undo_stack:
                            self.parent_window._undo_stack.pop()
                    return  # ← 关键: 必须return

        # 双击空白处不执行任何操作(创建标注请用Ctrl+K或右键菜单)

    def _create_annotation_at(self, x: int, y: int)->None:
        """
        在指定坐标位置创建标注(由Ctrl+K快捷键或右键菜单触发)
        
        参数:
          x: DisplayWidget本地坐标X(像素)
          y: DisplayWidget本地坐标Y(像素)
        
        原理: 将像素坐标转换为相对坐标(0-1范围)，然后创建标注
              与mouseDoubleClickEvent中新建标注逻辑相同
        """
        if not self.parent_window or not self.parent_window.images:
            return
        ww = self.width()
        # 转换为相对坐标(0-1范围)
        rel_x = max(0, min(1, (x - 10) / (ww - 20))) if ww > 20 else 0
        if self.parent_window.images:
            total_h = self._get_total_h()
            base_y = -self.parent_window.current_position
            rel_y = max(0, min(1, (y - base_y) / total_h)) if total_h > 0 else 0.5
        else:
            rel_y = 0.5
        # 使用AnnotationCreateDialog创建标注
        dlg = AnnotationCreateDialog(self, x=rel_x, y=rel_y)
        if dlg.exec_() == QDialog.Accepted:
            self.parent_window.add_annotation(dlg.get_annotation())

    def contextMenuEvent(self, event: QContextMenuEvent)->None:
        """
        右键菜单 - 谱面右键菜单支持创建标注等操作
        
        功能:
          - 创建标注: 在点击位置创建新标注
          - 删除标注: 如果点击到已有标注可删除(可选)
        """
        if not self.parent_window or not self.parent_window.images:
            return
        menu = QMenu(self)
        # 添加"创建标注"选项
        create_action = menu.addAction(I18n.t("context_menu.add_annotation"))
        create_action.triggered.connect(lambda: self._create_annotation_at(event.x(), event.y()))
        # 显示菜单
        menu.exec_(event.globalPos())


# ============================================================
# 主显示窗口 - 吉他谱查看与播放
# ============================================================

class DisplayWindow(QMainWindow):
    """
    吉他谱显示与播放主窗口
    功能:
      - 显示多种格式吉他谱(PNG/JPG/WEBP/PDF/GTP)
      - 自动滚动播放 + 可拖动进度条
      - 速度控制 + 速度曲线(图片/PDF)
      - A-B区域循环播放
      - 谱面文本标注系统
      - 键盘快捷键支持
    """

    def __init__(self, file_path, file_type: str, speed: int = 500):
        super().__init__()
        self.setWindowIcon(get_app_icon())  # 设置窗口图标
        # 核心状态
        self.file_path=file_path; self.file_type=file_type
        self.base_speed:int=speed           # 基础速度(ms)
        self.current_position:float=0.0     # 当前滚动位置(px)
        # === 线性模式时间参数 ===
        # 核心公式: 总播放时长(秒) = base_speed * TIME_SCALE
        # scroll_step 和 play_time 都基于此总时长计算，保证三者严格一致:
        #   - 播放到末尾时: current_position == total_scroll_distance
        #   - 播放到末尾时: play_time == 总时长(≈现实经过时间)
        #   - 播放到末尾时: 左侧时间 ≈ 右侧总时长
        #
        # TIME_SCALE 调节整体快慢感(单位: 秒/ms):
        #   调大(如0.15)→ 同样speed下总时长更长 → 播放更慢(适合精读)
        #   调小(如0.06)→ 同样speed下总时长更短 → 播放更快(适合快速浏览)
        #
        # 示例(base_speed范围350~700):
        #   SCALE=0.15: speed=500 → 75秒 (快速浏览)
        #   SCALE=0.25: speed=500 → 125秒 (默认，自然阅读)
        #   SCALE=0.35: speed=500 → 175秒 (慢速精读)
        self.TIME_SCALE = 0.25
        self._last_tick_time:float = 0.0  # 上一帧时间戳(perf_counter)，用于精确计算帧间隔
        self.images:List[QPixmap]=[]       # 图片列表
        # 页面累积高度数组（性能优化P0-2: _sync_page_input()二分查找用）
        # 预计算每页的累积高度前缀和，将O(n)线性遍历降为O(log n)二分查找
        self._page_cumulative_heights:List[float]=[]
        self.loaded_images:List[QPixmap]=[]# 加载中图片
        self.timer:QTimer=QTimer()         # 播放定时器
        self.timer.timeout.connect(self._tick)
        self.is_loading:bool=False          # 加载状态
        self.scroll_step:float=1.0         # 每帧滚动px

        # 高级功能状态
        self.annotations:List[Annotation]=[]     # 当前音轨的标注列表(视图，实际存储在_annotations_by_track中)
        self._annotations_by_track:Dict[int,List[Annotation]]={}  # 按音轨索引分轨存储的标注字典
        # === 全局撤销/重做栈 ===
        # 原理: 命令模式 + 快照栈。每次修改annotations前保存当前状态深拷贝到undo_stack，
        #       撤销时将当前状态移入redo_stack并恢复上一个快照。
        #       所有标注操作(画布双击/管理器增删改)统一走此栈，Ctrl+Z/Y全局生效。
        self._undo_stack:List[List[Annotation]]=[]   # 撤销栈(历史状态)
        self._redo_stack:List[List[Annotation]]=[]   # 重做栈(被撤销可恢复)
        self._UNDO_MAX_DEPTH=50                      # 最大撤销深度(防止内存膨胀)
        self.speed_curve:SpeedCurveConfig=SpeedCurveConfig()  # 速度曲线
        # === 速度曲线排序缓存(避免每帧重新sorted) ===
        self._cached_sorted_curve_pts:list=None  # 缓存的已排序points列表
        self._cached_curve_pts_id:int=0          # 缓存时points的id(用于脏检测)
        self.loop_config:LoopConfig=LoopConfig()          # 循环配置
        self.total_scroll_distance:float=0.0   # 总可滚动距离
        self.play_time:float=0.0              # 已播放时间

        # GTP音轨选择状态（仅GTP文件时使用）
        self.gtp_track_combo=None             # 音轨下拉菜单控件

        # === Phase 3/4: GTP播放器（使用gtp_engine库的高级封装）===
        # GTPPlayer 整合了解析/渲染/音频/时间线的完整功能
        # 原来分散在主程序中的 _synth_engine/_midi_converter/_gtp_song/
        # _audio_events/_playhead_timeline 等全部由 GTPPlayer 统一管理
        from ApolloTab import GTPPlayer
        self.gtp_player: Optional[GTPPlayer] = None  # 延迟初始化（加载GTP文件时创建）
        
        self._current_highlight:tuple=None    # 当前高亮音符(midi_pitch, time_ms)

        # === Phase 3.5: 播放光标(Playhead) ===
        # 布局数据: 由TabRenderer.render()生成, 包含每页/行/小节/拍的精确坐标
        # 类型: List[PageLayout]
        self._page_layouts:list=[]
        # 当前播放光标位置信息 (由音频回调或_tick更新)
        # 格式: (page_idx, system_idx, measure_idx, beat_idx, x_in_page)
        #       x_in_page = 光标在页面内的X坐标(原始渲染分辨率)
        self._playhead_info:tuple=None

        # === 播放光标时间线(必须在此初始化，否则图片/PDF模式会报AttributeError) ===
        # 由 GTPPlayer.build_timeline() 构建(GTP文件)，或保持空列表(非GTP文件降级为线性滚动)
        # 数据结构: List[dict]，每个元素包含 time_ms/scroll_y/page_idx/sys_idx/meas_idx/beat_idx/x_center
        self._playhead_timeline:list=[]  # 修复: 初始化空列表，防止_update_playhead()访问时报错

        # === 点击跳转播放目标(防止_tick()音频时间覆盖点击位置) ===
        # 当用户点击谱面跳转播放时设置，_tick()在音频时间未追上之前使用此值
        self._click_jump_target:float = -1.0  # -1表示无待处理跳转
        
        # === 总音频时长(ms)(用于进度条百分比计算) ===
        self._total_audio_duration_ms:float=0.0
        
        # === 暂停时保存的播放时间(用于恢复播放) ===
        # 当用户暂停播放时，保存当前音频时间，恢复播放时从此位置继续
        self._paused_time_ms:float=0.0

        # === 全屏模式状态(v2.1.0新增) ===
        # is_fullscreen: 当前是否处于全屏模式
        # _saved_geometry: 进入全屏前保存的窗口几何信息(位置+大小)，用于退出时精确恢复
        self.is_fullscreen:bool=False
        self._saved_geometry=None  # 类型: Optional[QByteArray]

        self.init_ui()
        self._load_annotations()               # 加载已有标注
        self.load_content_async()              # 异步加载内容

    def init_ui(self)->None:
        """初始化用户界面"""
        self.setWindowTitle(I18n.t("app.title"))
        self.setGeometry(150,80,1100,850)
        self._apply_theme()

        central=QWidget();self.setCentralWidget(central)
        main_layout=QVBoxLayout(central)
        main_layout.setContentsMargins(10,10,10,10);main_layout.setSpacing(8)

        # ===== 顶部工具栏 =====
        toolbar=self._create_toolbar()
        main_layout.addLayout(toolbar)

        # ===== 主内容区 =====
        splitter=QSplitter(Qt.Horizontal)

        # 谱面画布
        self.display_widget=DisplayWidget(self)
        splitter.addWidget(self.display_widget)

        # 连接主题变更信号: 当ThemeManager切换主题时自动刷新本窗口(含GTP谱重渲染)
        try:
            ThemeManager.theme_changed.connect(self._refresh_theme)
        except Exception:
            pass  # 连接失败时静默忽略(正常，信号可能在某些边界情况下不可用)

        # 右侧控制面板
        right_panel=self._create_control_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([820,260])
        main_layout.addWidget(splitter,1)

        # ===== 底部进度条 =====
        bottom=self._create_bottom_bar()
        main_layout.addLayout(bottom)

    def _apply_theme(self)->None:
        """
        应用当前主题样式到DisplayWindow
        从ThemeManager读取当前主题配色，支持深色/浅色动态切换
        
        性能优化(P0-1): 使用 _get_cached_qss() 缓存QSS字符串，
                        避免每次调用重新生成和Qt重新解析样式表。
        """
        theme_name = ThemeManager.current_name()
        t = ThemeManager.current()
        # 缓存key: (窗口类名, 主题名)，同一主题下QSS字符串只生成一次
        qss = _get_cached_qss('DisplayWindow', theme_name, lambda: f"""
            QMainWindow,QWidget{{background-color:{t['bg_primary']};color:{t['text_primary']};
                font-family:{get_font_family_css('ui')};}}
            QLabel{{color:{t['text_primary']};font-size:13px;}}
            QSlider::groove:horizontal{{border:none;height:4px;background:{t['bg_surface']};border-radius:2px;}}
            QSlider::handle:horizontal{{background:{t['primary']};border:2px solid{t['bg_primary']};
                width:16px;margin:-7px 0;border-radius:8px;}}
            QSpinBox{{background-color:{t['bg_surface']};color:{t['text_primary']};
                border:1px solid{t['border']};border-radius:4px;padding:4px;}}
            QComboBox{{background-color:{t['bg_surface']};color:{t['text_primary']};
                border:1px solid{t['border']};border-radius:4px;padding:4px 8px;}}
            QComboBox::drop-down{{border:none;width:20px;}}
            QComboBox QAbstractItemView{{background-color:{t['bg_surface']};color:{t['text_primary']};
                selection-background-color:{t['primary']};}}
            QGroupBox{{color:{t['text_primary']};border:1px solid{t['border']};
                border-radius:8px;margin-top:12px;padding-top:8px;font-weight:bold;}}
            QGroupBox::title{{subcontrol-origin;margin;left:12px;padding:0 6px;}}
        """)
        self.setStyleSheet(qss)

    def _refresh_theme(self) -> None:
        """
        主题切换时刷新DisplayWindow所有UI组件样式
        
        调用时机:
          - SettingsDialog 中切换主题时调用
          - 也可连接到 ThemeManager.theme_changed 信号
        
        刷新内容:
          1. 重新应用窗口级样式表(_apply_theme)
          2. 刷新工具栏文件名标签颜色
          3. 刷新控制面板各标签/状态文字颜色
          4. 刷新进度条组件(触发重绘)
          5. 刷新ModernButton/ModernSlider等自定义组件
          6. 如果是GTP文件，同步切换渲染主题
        """
        # 1. 重新应用窗口样式
        self._apply_theme()

        # 2. 刷新工具栏文字颜色
        if hasattr(self, 'file_label'):
            self.file_label.setStyleSheet(
                f"font-size:14px;font-weight:bold;color:{ThemeManager.get('primary_light', '#60A5FA')};")

        # 3. 刷新控制面板标签颜色
        if hasattr(self, 'curve_status_label'):
            self.curve_status_label.setStyleSheet(
                f"color:{ThemeManager.get('text_muted', '#64748B')};font-size:11px;")
        if hasattr(self, 'ab_info_label'):
            self.ab_info_label.setStyleSheet(
                f"color:{ThemeManager.get('accent', '#F97316')};font-size:11px;")
        if hasattr(self, 'help_txt'):  # 快捷键帮助(在_create_control_panel中创建的局部变量无法访问，跳过)
            pass

        # 4. 刷新页码控件
        if hasattr(self, 'page_input'):
            self.page_input.setStyleSheet(
                f"background-color:{ThemeManager.get('bg_surface', '#252536')};"
                f"color:{ThemeManager.get('text_primary', '#E2E8F0')};"
                f"border:1px solid{ThemeManager.get('border', '#3A3A4A')};border-radius:4px;padding:2px;")
        if hasattr(self, 'page_total_label'):
            self.page_total_label.setStyleSheet(
                f"color:{ThemeManager.get('text_muted', '#64748B')};font-size:12px;")

        # 5. 刷新播放/停止按钮颜色
        if hasattr(self, 'play_btn'):
            is_playing = self.timer.isActive()
            btn_color = ThemeManager.get('warning', '#F59E0B') if is_playing else ThemeManager.get('success', '#10B981')
            self.play_btn.setStyleSheet(f"background-color:{btn_color};")

        # 7. 刷新进度条(触发重绘)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.update()

        # 8. 刷新显示画布
        if hasattr(self, 'display_widget'):
            self.display_widget.update()

        # 9. 同步GTP渲染主题到UI主题（如果当前打开的是GTP文件）
        #    重要: 必须重新渲染全部页面，避免出现"第1页浅色+第2页深色"不一致问题
        #
        #    性能优化(P1-3): 将GTP重渲染移至后台线程(ThemeRefreshWorker)，
        #                    避免主线程卡顿。完成后通过信号回调更新UI。
        if self.gtp_player and hasattr(self.gtp_player, 'set_theme') and self.gtp_player.is_loaded:
            try:
                render_theme = ThemeManager.get_gtp_render_theme()
                
                # 创建异步工作线程
                worker = ThemeRefreshWorker(self.gtp_player, render_theme)
                
                def _on_gtp_theme_refreshed(all_pixmaps):
                    """GTP主题刷新完成回调(在主线程中执行)"""
                    if all_pixmaps:
                        self.display_widget.set_images(all_pixmaps)
                        print(f"[DisplayWindow] GTP渲染全部{len(all_pixmaps)}页已同步为: {render_theme}")
                
                def _on_gtp_theme_error(err_msg):
                    print(f"[DisplayWindow] GTP渲染主题同步失败: {err_msg}")
                
                worker.signals.finished.connect(_on_gtp_theme_refreshed)
                worker.signals.error.connect(_on_gtp_theme_error)
                QThreadPool.globalInstance().start(worker)
            except Exception as e:
                print(f"[DisplayWindow] GTP渲染主题同步启动失败: {e}")

    def _create_toolbar(self)->QHBoxLayout:
        """创建顶部工具栏"""
        tb=QHBoxLayout();tb.setSpacing(10)

        # 文件名
        fname=os.path.basename(self.file_path) if isinstance(self.file_path,str) else I18n.t("app.multi_images")
        self.file_label=QLabel(I18n.t("toolbar.file_label", name=fname))
        self.file_label.setStyleSheet(f"font-size:14px;font-weight:bold;color:{ThemeManager.get('primary_light', '#60A5FA')};")
        tb.addWidget(self.file_label)

        # GTP音轨选择下拉菜单（仅GTP文件显示，默认隐藏）
        self.gtp_track_combo=QComboBox()
        self.gtp_track_combo.setMinimumWidth(160)
        self.gtp_track_combo.setVisible(False)  # 非GTP文件时隐藏
        self.gtp_track_combo.currentIndexChanged.connect(self._on_gtp_track_changed)
        tb.addWidget(self.gtp_track_combo)

        # 音频播放模式按钮（仅GTP文件显示，默认隐藏）(SVG图标: 扬声器)
        # 3种模式: 全轨并轨(默认) / 仅当前轨 / 关闭音频
        self.audio_btn = QToolButton()
        self.audio_btn.setText(I18n.t("toolbar.audio_all"))
        self.audio_btn.setToolTip(I18n.t("toolbar.audio_tooltip"))
        self.audio_btn.setPopupMode(QToolButton.InstantPopup)  # 点击即弹出菜单
        self.audio_btn.setVisible(False)  # 非GTP文件时隐藏
        self.audio_btn.setMinimumSize(QSize(80, 36))  # 最小尺寸确保可见性
        self.audio_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # 图标在文字左侧
        # 设置音频按钮图标(增大尺寸提升可见度) / Set audio button icon (larger size for visibility)
        vol_icon = load_icon('volume')
        if not vol_icon.isNull():
            self.audio_btn.setIcon(vol_icon)
            self.audio_btn.setIconSize(QSize(24, 24))  # 从18增大到24，更醒目
        
        # 创建下拉菜单
        audio_menu = QMenu(self)
        self._audio_action_all = QAction(I18n.t("toolbar.audio_all_menu"), self, checkable=True, checked=True)
        self._audio_action_current = QAction(I18n.t("toolbar.audio_current_menu"), self, checkable=True)
        self._audio_action_off = QAction(I18n.t("toolbar.audio_off_menu"), self, checkable=True)
        
        self._audio_action_all.triggered.connect(lambda: self._set_audio_mode("all"))
        self._audio_action_current.triggered.connect(lambda: self._set_audio_mode("current"))
        self._audio_action_off.triggered.connect(lambda: self._set_audio_mode("off"))
        
        audio_menu.addAction(self._audio_action_all)
        audio_menu.addAction(self._audio_action_current)
        audio_menu.addAction(self._audio_action_off)
        self.audio_btn.setMenu(audio_menu)
        tb.addWidget(self.audio_btn)

        tb.addStretch()

        # 标注按钮 (SVG图标: 铅笔)
        self.annotation_btn=ModernButton(I18n.t("toolbar.annotation_btn"),'accent','annotate')
        self.annotation_btn.clicked.connect(self._open_annotation_manager)
        tb.addWidget(self.annotation_btn)

        # 导出按钮(A4 PNG/PDF，含标注) (SVG图标: 下载箭头)
        self.export_btn=ModernButton(I18n.t("toolbar.export_btn"),'primary','export')
        self.export_btn.setToolTip(I18n.t("toolbar.export_tooltip"))
        self.export_btn.clicked.connect(self._export_to_a4)
        tb.addWidget(self.export_btn)

        # 打印按钮(下拉菜单: 直接打印 / 打印预览) (SVG图标: 打印机)
        self.print_btn = QToolButton()
        self.print_btn.setText(I18n.t("toolbar.print_btn"))
        self.print_btn.setIcon(load_icon('printer'))
        self.print_btn.setPopupMode(QToolButton.MenuButtonPopup)  # 下拉菜单模式
        self.print_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.print_btn.setToolTip(I18n.t("toolbar.print_tooltip"))

        # 创建下拉菜单
        print_menu = QMenu(self)

        # 菜单项1: 直接打印
        action_print_direct = QAction(I18n.t("toolbar.print_direct"), self)
        action_print_direct.setIcon(load_icon('printer'))
        action_print_direct.triggered.connect(lambda: self._print_score(use_preview=False))
        print_menu.addAction(action_print_direct)

        # 菜单项2: 打印预览
        action_print_preview = QAction(I18n.t("toolbar.print_preview"), self)
        action_print_preview.setIcon(load_icon('printer'))  # 复用打印机图标
        action_print_preview.triggered.connect(lambda: self._print_score(use_preview=True))
        print_menu.addAction(action_print_preview)

        self.print_btn.setMenu(print_menu)
        # 默认点击行为: 直接打印（与下拉菜单第一项一致）
        self.print_btn.clicked.connect(lambda: self._print_score(use_preview=False))

        tb.addWidget(self.print_btn)

        # 全屏模式按钮 (v2.1.0新增) (SVG图标: 展开四角箭头)
        # 位置: 打印按钮之后，速度曲线按钮之前
        # 功能: 切换全屏/窗口模式(F11快捷键)，最大化谱面显示区域
        self.fullscreen_btn=ModernButton(I18n.t("toolbar.fullscreen_btn"),'accent','fullscreen')
        self.fullscreen_btn.setToolTip(I18n.t("toolbar.fullscreen_tooltip"))
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        tb.addWidget(self.fullscreen_btn)

        # 速度曲线按钮 (SVG图标: 趋势线图表)
        self.curve_btn=ModernButton(I18n.t("toolbar.curve_btn"),'primary','chart')
        self.curve_btn.clicked.connect(self._open_speed_curve_editor)
        tb.addWidget(self.curve_btn)

        return tb

    def _create_control_panel(self)->QWidget:
        """创建右侧控制面板"""
        panel=QWidget();panel.setMaximumWidth(280);panel.setMinimumWidth(240)
        layout=QVBoxLayout(panel);layout.setSpacing(10)

        # === 播放控制 ===
        pg=QGroupBox(I18n.t("control_panel.playback_control"));pl=QVBoxLayout(pg)
        btn_row=QHBoxLayout()
        self.play_btn=ModernButton(I18n.t("control_panel.play_btn"),'success','play');self.play_btn.clicked.connect(self.toggle_playback)
        self.stop_btn=ModernButton(I18n.t("control_panel.stop_btn"),'danger','stop');self.stop_btn.clicked.connect(lambda: self.stop_playback(reset_position=True));self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.play_btn);btn_row.addWidget(self.stop_btn);pl.addLayout(btn_row)

        # 循环模式
        loop_row=QHBoxLayout();loop_row.addWidget(QLabel(I18n.t("control_panel.loop_label")))
        self.loop_combo=QComboBox()
        self.loop_combo.addItems([I18n.t("control_panel.loop_no_loop"),I18n.t("control_panel.loop_global"),I18n.t("control_panel.loop_ab")])
        self.loop_combo.currentIndexChanged.connect(self._on_loop_mode_changed)
        loop_row.addWidget(self.loop_combo);pl.addLayout(loop_row)

        # A-B点按钮 (SVG图标: 旗标/删除)
        ab_row=QHBoxLayout()
        self.set_a_btn=ModernButton(I18n.t("control_panel.set_a_btn"),'warning','flag-a');self.set_a_btn.clicked.connect(lambda:self._set_ab_point('a'))
        self.set_b_btn=ModernButton(I18n.t("control_panel.set_b_btn"),'warning','flag-b');self.set_b_btn.clicked.connect(lambda:self._set_ab_point('b'))
        self.clear_ab_btn=ModernButton(I18n.t("control_panel.clear_ab_btn"),'text_muted','trash');self.clear_ab_btn.clicked.connect(self._clear_ab_points)
        ab_row.addWidget(self.set_a_btn);ab_row.addWidget(self.set_b_btn);ab_row.addWidget(self.clear_ab_btn)
        pl.addLayout(ab_row)
        layout.addWidget(pg)

        # === 速度控制(非GTP文件显示，GTP文件由BPM驱动自动隐藏) ===
        self.speed_group_box=QGroupBox(I18n.t("control_panel.speed_group"));sl=QVBoxLayout(self.speed_group_box)
        sr=QHBoxLayout();sr.addWidget(QLabel(I18n.t("control_panel.speed_label")))
        self.speed_spin=QSpinBox();self.speed_spin.setRange(350,700)
        self.speed_spin.setValue(self.base_speed);self.speed_spin.setSuffix(I18n.t("control_panel.speed_suffix"))
        self.speed_spin.valueChanged.connect(self._on_speed_changed)
        sr.addWidget(self.speed_spin);sl.addLayout(sr)

        self.curve_status_label=QLabel(I18n.t("control_panel.curve_status_disabled"))
        self.curve_status_label.setStyleSheet(f"color:{ThemeManager.get('text_muted', '#64748B')};font-size:11px;")
        sl.addWidget(self.curve_status_label)
        layout.addWidget(self.speed_group_box)  # 使用实例变量以便动态控制可见性

        # 状态信息栏已移除(简化界面，位置/时间信息可在进度条提示中查看)

        # 快捷键帮助
        hg=QGroupBox(I18n.t("control_panel.shortcut_group"));hl=QVBoxLayout(hg)
        help_txt=QLabel(I18n.t("control_panel.shortcut_help"))
        help_txt.setStyleSheet(f"color:{ThemeManager.get('text_muted', '#64748B')};font-size:11px;")
        hl.addWidget(help_txt);layout.addWidget(hg)

        # === GTP音轨音量控制(仅GTP文件显示，默认隐藏) ===
        self.volume_group_box = QGroupBox(I18n.t("control_panel.volume_group"))
        volume_layout = QHBoxLayout(self.volume_group_box)
        volume_layout.setSpacing(4)
        volume_layout.setContentsMargins(4, 10, 4, 4)

        # 使用QScrollArea包裹，防止音轨过多时撑开面板
        self.volume_scroll = QScrollArea()
        self.volume_scroll.setWidgetResizable(True)
        self.volume_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 改为需要时显示
        self.volume_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.volume_scroll.setMinimumHeight(190)  # 设置最小高度确保可见
        self.volume_scroll.setVisible(False)  # 默认隐藏

        # 音轨滑块容器(水平排列所有滑块)
        self.volume_container = QWidget()
        self.volume_slider_layout = QHBoxLayout(self.volume_container)
        self.volume_slider_layout.setSpacing(1)  # 超紧凑间距
        self.volume_slider_layout.setContentsMargins(1, 0, 1, 0)
        self.volume_scroll.setWidget(self.volume_container)

        volume_layout.addWidget(self.volume_scroll)
        layout.addWidget(self.volume_group_box)

        # 存储音量滑块引用 {track_index: TrackVolumeSlider}
        self._track_volume_sliders: Dict[int, TrackVolumeSlider] = {}
        self._master_volume_slider: Optional[TrackVolumeSlider] = None

        # 默认隐藏整个音量控制组
        self.volume_group_box.setVisible(False)

        layout.addStretch()
        return panel

    def _create_bottom_bar(self)->QHBoxLayout:
        """创建底部进度条栏 - 含页码输入(多图/PDF时显示)"""
        bar=QHBoxLayout();bar.setSpacing(10)

        # ===== 页码导航区 (多图/PDF模式) =====
        self.page_widget=QWidget()
        self.page_widget.setVisible(False)  # 默认隐藏，加载内容后根据图片数量决定
        pg_layout=QHBoxLayout(self.page_widget)
        pg_layout.setContentsMargins(0,0,0,0);pg_layout.setSpacing(4)

        self.page_input=QSpinBox()
        self.page_input.setRange(1,9999)
        self.page_input.setMinimumWidth(50)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setStyleSheet(f"background-color:{ThemeManager.get('bg_surface', '#252536')};color:{ThemeManager.get('text_primary', '#E2E8F0')};border:1px solid{ThemeManager.get('border', '#3A3A4A')};border-radius:4px;padding:2px;")
        self.page_input.valueChanged.connect(self._on_page_jump)
        pg_layout.addWidget(self.page_input)

        self.page_total_label=QLabel("/ 1")
        self.page_total_label.setStyleSheet(f"color:{ThemeManager.get('text_muted', '#64748B')};font-size:12px;")
        pg_layout.addWidget(self.page_total_label)

        pg_layout.addStretch()

        bar.addWidget(self.page_widget)

        # ===== 时间/进度条 =====
        self.time_start_label=QLabel("00:00")
        bar.addWidget(self.time_start_label)

        self.progress_bar=ProgressBarSlider()
        self.progress_bar.positionChanged.connect(self._on_progress_changed)
        self.progress_bar.regionSelected.connect(self._on_region_selected)
        bar.addWidget(self.progress_bar,1)

        self.time_end_label=QLabel("--:--")
        bar.addWidget(self.time_end_label)
        return bar

    def _update_page_display(self)->None:
        """更新页码显示 - 多图或PDF时显示页码控件"""
        if not self.images or len(self.images)<=1:
            self.page_widget.setVisible(False); return
        total=len(self.images)
        self.page_input.setRange(1,total)
        self.page_total_label.setText(f"/ {total}")
        self.page_widget.setVisible(True)

    def _on_page_jump(self,page:int)->None:
        """
        跳转到指定页
        原理: 根据页码索引计算该页顶部在总滚动距离中的位置，设置current_position
        """
        if not self.images or len(self.images)<=1:return
        ww=self.display_widget.width()-20
        # 计算目标页之前所有页面的累计高度
        target_idx=max(0,min(page-1,len(self.images)-1))
        offset=0.0
        for i in range(target_idx):
            img=self.images[i]
            if img.isNull(): continue
            ratio=img.width()>0 and ww/img.width() or 1
            offset+=img.height()*ratio+5
        self.current_position=offset
        self.update_progress_display()
        self.display_widget.update()

    # ========== 内容加载 ==========

    def load_content_async(self)->None:
        """异步加载谱面内容"""
        self.is_loading=True;self.images=[];self.current_position=0
        self.display_widget.update()
        pool=QThreadPool.globalInstance()
        worker=LoadContentWorker(self,self.file_path,self.file_type)
        worker.signals.finished.connect(self._on_content_loaded)
        worker.signals.error.connect(self._on_content_load_error)
        worker.signals.progress.connect(lambda p: None)
        pool.start(worker)

    def _on_content_loaded(self, images=None)->None:
        """加载完成回调 - images为加载的图片列表(信号携带)"""
        self.is_loading=False
        if images is not None:
            self.loaded_images = images
        self.images=self.loaded_images
        self.display_widget.set_images(self.images)
        self.display_widget.set_annotations(self.annotations)
        self._calculate_total_distance()
        self.update_progress_display()
        self._update_page_display()  # 更新页码显示

        # GTP文件：填充音轨选择下拉菜单 + 初始化音频引擎 + 构建播放光标时间线 + 隐藏手动速度控制
        if self.file_type == 'gtp':
            self._populate_gtp_track_combo()
            self._setup_volume_controls()  # 初始化音轨音量控制滑块(新增)
            self._init_audio_engine()  # Phase 3: 初始化音频播放引擎
            self._build_playhead_timeline()  # Phase 3.5: 构建播放光标时间线(必须在init_audio之后)
            self.audio_btn.setVisible(True)  # 显示音频按钮
            # GTP模式: 隐藏手动速度控制(由BPM驱动，不需要ms/曲线控制)
            if hasattr(self, 'speed_spin'):
                self.speed_spin.setVisible(False)
            if hasattr(self, 'curve_btn'):
                self.curve_btn.setVisible(False)
            if hasattr(self, 'speed_group_box'):
                self.speed_group_box.setVisible(False)
            if hasattr(self, 'curve_status_label'):
                self.curve_status_label.setVisible(False)
        else:
            if self.gtp_track_combo:
                self.gtp_track_combo.setVisible(False)
            if self.audio_btn:
                self.audio_btn.setVisible(False)  # 非GTP文件隐藏音频按钮
            # 非GTP模式: 显示手动速度控制(图片/PDF需要)
            if hasattr(self, 'speed_spin'):
                self.speed_spin.setVisible(True)
            if hasattr(self, 'curve_btn'):
                self.curve_btn.setVisible(True)
            if hasattr(self, 'speed_group_box'):
                self.speed_group_box.setVisible(True)
            if hasattr(self, 'curve_status_label'):
                self.curve_status_label.setVisible(True)
            
            # 非GTP文件: 隐藏音量控制面板
            if hasattr(self, 'volume_group_box'):
                self.volume_group_box.setVisible(False)

        # 延迟重算: 确保窗口布局完成后再精确计算一次总滚动距离
        QTimer.singleShot(200,self._calculate_total_distance)

    def _populate_gtp_track_combo(self)->None:
        """
        填充GTP音轨下拉菜单
        
        原理: 使用 GTPPlayer.get_all_tracks_info() 获取所有音轨信息，
              然后填充到QComboBox中供用户选择。
              用户切换选项后触发重新渲染对应音轨的六线谱。
        
        注意: 此方法在主线程中调用（_on_content_loaded回调），解析操作很快（<50ms）
        """
        try:
            # 检查GTP播放器是否可用
            if not self.gtp_player or not self.gtp_player.song:
                if self.gtp_track_combo:
                    self.gtp_track_combo.setVisible(False)
                return
            
            song = self.gtp_player.song

            # 阻断信号避免触发不必要的重新渲染
            self.gtp_track_combo.blockSignals(True)
            self.gtp_track_combo.clear()

            for i, track in enumerate(song.tracks):
                # 显示格式: "序号. 音轨名 (调弦)"
                tuning_name = track.get_tuning_name()
                display_name = f"{i+1}. {track.name} ({tuning_name})"
                self.gtp_track_combo.addItem(display_name, userData=i)

            # 恢复之前的选择或默认第0个
            current_idx = self.gtp_player.current_track
            if current_idx < self.gtp_track_combo.count():
                self.gtp_track_combo.setCurrentIndex(current_idx)
            else:
                self.gtp_player.current_track = 0

            self.gtp_track_combo.blockSignals(False)
            self.gtp_track_combo.setVisible(True)

        except Exception as e:
            # 解析失败时隐藏下拉菜单，不影响正常显示
            if self.gtp_track_combo:
                self.gtp_track_combo.setVisible(False)

    def _setup_volume_controls(self) -> None:
        """
        初始化GTP音轨音量控制滑块
        
        原理: 根据GTP文件中的音轨数量，动态创建垂直音量滑块组件。
              每个音轨一个独立滑块 + 一个Master总音量滑块。
              滑块排列在水平滚动区域内(类似专业DAW混音器界面)。
        
        调用时机:
          - GTP文件加载完成后(_on_content_loaded中调用)
          - 音轨切换时不需要重建(仅首次加载时创建)
        
        UI布局:
          [Master] [音轨1] [音轨2] [音轨3] ...
          每个滑块: 48px宽 × 140px高，简洁风格(无左侧刻度)
        
        音量范围: -60.0dB(静音) ~ +12.0dB(最大增益)
        默认值: 0.0dB (单位增益)
        """
        print(f"[VolumeControl] 开始初始化音量控制... gtp_player={self.gtp_player is not None}")
        try:
            # 清除旧的滑块
            for slider in self._track_volume_sliders.values():
                slider.deleteLater()
            self._track_volume_sliders.clear()
            
            if self._master_volume_slider:
                self._master_volume_slider.deleteLater()
                self._master_volume_slider = None
            
            # 检查GTP播放器是否可用
            if not self.gtp_player or not self.gtp_player.song:
                self.volume_group_box.setVisible(False)
                return
            
            song = self.gtp_player.song
            num_tracks = len(song.tracks)
            
            if num_tracks == 0:
                self.volume_group_box.setVisible(False)
                return
            
            # 1. 创建Master总音量滑块(放在最左边，使用特殊样式)
            master_slider = TrackVolumeSlider(track_name="Master", is_master=True)
            master_slider.valueChanged.connect(self._on_master_volume_changed)
            
            self.volume_slider_layout.addWidget(master_slider)
            self._master_volume_slider = master_slider
            
            # 添加分隔线(QFrame作为视觉分隔)
            separator = QFrame()
            separator.setFrameShape(QFrame.VLine)
            separator.setStyleSheet(f"color: {ThemeManager.get('border', '#3A3A4A')};")
            separator.setFixedHeight(120)  # 固定高度(匹配滑块)
            self.volume_slider_layout.addWidget(separator)
            
            # 2. 为每个音轨创建音量滑块(跟在Master后面)
            for i, track in enumerate(song.tracks):
                track_name = track.name if track.name else f"Track {i+1}"
                
                # 创建音轨音量滑块
                slider = TrackVolumeSlider(track_name=track_name, is_master=False)
                slider.valueChanged.connect(lambda db, idx=i: self._on_track_volume_changed(idx, db))
                
                # 添加到布局和字典
                self.volume_slider_layout.addWidget(slider)
                self._track_volume_sliders[i] = slider
            
            # 显示整个音量控制组
            self.volume_group_box.setVisible(True)
            self.volume_scroll.setVisible(True)
            
            # 根据音轨数量调整滚动区域宽度(使用新的WIDGET_WIDTH=48)
            total_width = (num_tracks + 1) * (48 + 2) + 16  # 滑块宽 + 间距 + 分隔线
            self.volume_container.setMinimumWidth(min(total_width, 480))  # 最大480px
            
            print(f"[VolumeControl] 已初始化 {num_tracks} 个音轨音量滑块 + Master总音量")
            
        except Exception as e:
            print(f"[VolumeControl] 初始化音量控制失败: {e}")
            self.volume_group_box.setVisible(False)

    def _on_track_volume_changed(self, track_index: int, db_value: float) -> None:
        """
        单个音轨音量变化回调
        
        参数:
            track_index: 音轨索引(0-based)
            db_value:    新的dB值
        
        功能:
          1. 存储该音轨的音量设置(用于后续播放时应用)
          2. 如果正在播放且音频引擎支持实时调整，立即应用
          3. 打印调试信息(开发阶段)
        """
        # 存储到字典(即使音频引擎不支持也能保存设置)
        if not hasattr(self, '_track_volumes'):
            self._track_volumes: Dict[int, float] = {}
        self._track_volumes[track_index] = db_value
        
        # 尝试实时应用到音频引擎
        try:
            if self.gtp_player and hasattr(self.gtp_player, 'set_track_volume'):
                # 如果GTPPlayer支持per-track音量控制
                self.gtp_player.set_track_volume(track_index, db_value)
        except Exception as e:
            pass  # 静默失败(底层可能不支持)
        
        # 调试输出
        track_name = f"Track {track_index+1}"
        if self.gtp_player and self.gtp_player.song and track_index < len(self.gtp_player.song.tracks):
            track_name = self.gtp_player.song.tracks[track_index].name
        print(f"[VolumeControl] {track_name}: {db_value:+.1f} dB")

    def _on_master_volume_changed(self, db_value: float) -> None:
        """
        Master总音量变化回调
        
        参数:
            db_value: 新的dB值(-60.0 ~ +12.0)
        
        功能:
          1. 存储Master音量设置
          2. 尝试应用到音频引擎的总音量控制
          3. 影响所有音轨的最终输出音量
        """
        # 存储
        if not hasattr(self, '_master_volume'):
            self._master_volume: float = 0.0
        self._master_volume = db_value
        
        # 尝试应用到音频引擎
        try:
            if self.gtp_player and hasattr(self.gtp_player, 'set_master_volume'):
                self.gtp_player.set_master_volume(db_value)
        except Exception as e:
            pass  # 静默失败
        
        print(f"[VolumeControl] Master: {db_value:+.1f} dB")

    def _on_gtp_track_changed(self, index:int)->None:
        """
        音轨切换回调 - 重新渲染指定音轨的六线谱
        
        参数:
            index: 下拉菜单选中项索引(0-based)，对应音轨序号
        
        并轨模式特殊处理:
          当音频模式为"全轨并轨"(all)时，切换音轨仅改变视觉显示，
          不停止音频播放、不重置滚动位置、不重建MIDI事件。
          因为并轨模式下所有音轨的音频同时在播放。
        """
        from ApolloTab import GTPPlayer  # 延迟导入(仅GTP文件需要)
        if index < 0 or not self.gtp_player or not self.gtp_player.file_path:
            return

        # === 切换分轨标注(在更新current_track之前调用) ===
        old_track = self.gtp_player.current_track
        if old_track != index:
            self._switch_track_annotations(old_track, index)
            # _switch_track_annotations 内部已更新 gtp_player.current_track = index
        else:
            self.gtp_player.current_track = index

        # === 判断是否需要停止播放 ===
        # 仅在非并轨模式时停止（因为单轨模式音频与视觉绑定）
        need_stop = (self.gtp_player.audio_mode != GTPPlayer.MODE_ALL)
        
        was_playing = self.timer.isActive()
        if need_stop and was_playing:
            self.stop_playback(reset_position=True)  # 切换音轨，重置位置

        try:
            # 使用 GTPPlayer 重新渲染新音轨
            pixmaps = self.gtp_player.render_track(index)
            
            self.images = pixmaps
            self.loaded_images = pixmaps
            # 捕获布局数据(播放光标功能依赖此数据)
            self._page_layouts = self.gtp_player.last_layouts
            self.display_widget.set_images(pixmaps)
            
            # 并轨模式: 保持当前播放位置不变（仅切换视觉）
            # 单轨模式: 重置到开头
            if not need_stop:
                self._calculate_total_distance()  # 重新计算总距离(新图像尺寸可能不同)
                # 重建播放光标时间线(基于新轨道的布局数据)
                # 修复: 并轨模式切轨时必须重建时间线，否则scroll_y映射仍基于旧轨道导致速度不同步
                self._build_playhead_timeline()
                self._update_page_display()
                self.update_progress_display()
                self.display_widget.update()
                # 不重置 current_position / play_time，继续从当前位置滚动
            else:
                self.current_position = 0.0
                self.play_time = 0.0
                self._calculate_total_distance()
                self._update_page_display()
                self.update_progress_display()
                self.display_widget.update()

            # Phase 3/4: 仅单轨模式才需要重建音频事件（由GTPPlayer管理）
            if need_stop and self.gtp_player.is_audio_ready:
                self.gtp_player.rebuild_audio_events()

        except Exception as e:
            QMessageBox.warning(self, I18n.t("messages.track_switch_fail"), I18n.t("messages.track_switch_fail_msg", index=index+1, error=str(e)))

    def _on_content_load_error(self,msg:str)->None:
        """加载失败回调"""
        self.is_loading=False
        QMessageBox.critical(self,I18n.t("messages.load_error"),I18n.t("messages.load_error_msg", msg=msg))

    def update_content(self,file_path,file_type:str,speed:int)->None:
        """更新显示内容"""
        self.file_path=file_path;self.file_type=file_type;self.base_speed=speed
        self._calculate_scroll_step(speed);self.annotations.clear()
        # 重置GTP播放器状态（切换文件时清空）
        if self.gtp_player:
            self.gtp_player.shutdown()
            self.gtp_player = None
        if self.gtp_track_combo:
            self.gtp_track_combo.setVisible(False)
        self._load_annotations();self.load_content_async()

    # ========== 播放控制 ==========

    def toggle_playback(self)->None:
        """切换播放/暂停"""
        if self.timer.isActive(): self.stop_playback()
        else: self.start_playback()

    def start_playback(self)->None:
        """
        开始播放
        使用固定30fps定时器确保播放条和滚动平滑连贯
        原理: 固定帧率(33ms) + 每帧滚动像素量随速度变化，避免低帧率导致的卡顿感
        """
        # 使用固定30fps定时器(33ms)，不再用base_speed作为间隔
        self.timer.start(33)
        self._last_tick_time = time.perf_counter()  # 重置时间戳，从当前时刻开始计时
        # Phase 3: 同时启动音频引擎
        if self.gtp_player and self.gtp_player.is_audio_ready:
            # 恢复播放: 如果有暂停时保存的时间，从该位置继续
            if self._paused_time_ms > 0:
                self.gtp_player.seek(self._paused_time_ms)
            self.gtp_player.play()
        self.play_btn.setText(I18n.t("control_panel.pause_btn"))
        self.play_btn.set_color('warning')  # 暂停状态: 橙色警告色
        self.stop_btn.setEnabled(True)

    def closeEvent(self, event):
        """
        窗口关闭事件: 确保音频引擎完全停止释放资源
        
        原理: PyQt5 窗口关闭时默认只隐藏窗口，后台线程可能继续运行。
              此方法在窗口销毁前强制停止 GTPPlayer 播放线程和音频输出，
              防止"关窗后声音仍在播放"的问题。
        """
        # 停止定时器和播放
        self.timer.stop()
        
        # 强制停止GTP播放器（释放所有发声音符 + 结束播放线程）
        if self.gtp_player:
            try:
                self.gtp_player.stop()
                self.gtp_player.shutdown()
            except Exception:
                pass
        
        # 调用父类关闭
        super().closeEvent(event)

    def stop_playback(self, reset_position: bool = False)->None:
        """
        停止播放
        
        参数:
            reset_position: 是否重置播放位置到开始
                - True: 停止模式(点击停止按钮)，重置到开始
                - False: 暂停模式(点击播放按钮)，保存当前位置以便恢复
        """
        self.timer.stop()
        self._click_jump_target = -1.0  # 清除点击跳转目标
        # Phase 3: 同时停止GTP播放器
        if self.gtp_player and self.gtp_player.is_audio_ready:
            if reset_position:
                # 停止模式: 重置到开始位置
                self._paused_time_ms = 0.0
                self.gtp_player.stop()
            else:
                # 暂停模式: 保存当前位置以便恢复
                self._paused_time_ms = self.gtp_player.current_time_ms
                self.gtp_player.stop()
        self.play_btn.setText(I18n.t("control_panel.play_btn"))
        self.play_btn.set_color('success')  # 播放状态: 绿色成功色
        self.stop_btn.setEnabled(False)

    def _init_audio_engine(self)->None:
        """
        Phase 3/4: 初始化音频播放引擎(GTP文件加载后调用)
        
        原理: 使用 GTPPlayer.init_audio() 统一初始化所有音频相关功能，
              包括解析GTP文件、创建MIDI转换器、初始化FluidSynth合成器、
              加载SoundFont音色、转换MIDI事件等。
              
        注意: 此方法在 _on_content_loaded 中调用，仅对 GTP 文件生效。
              默认模式为"全轨并轨"，用户可通过按钮菜单切换。
              如果 fluidsynth 未安装会优雅降级（音频按钮显示为禁用状态）。
        """
        if not self.gtp_player:
            print("[Audio] 错误: GTP播放器未初始化")
            self.audio_btn.setEnabled(False)
            return
        
        # === 确保SoundFont音色库可被找到(开发模式+打包模式兼容) ===
        # 原理: ApolloTab的SynthEngine使用相对路径搜索sf2文件,
        #       PyInstaller不同打包模式数据文件位置不同:
        #         onedir (直接运行):     exe同目录/_internal/soundfont/
        #         .app bundle (双击):    .app/Contents/Resources/soundfont/
        #         onedir (直接运行exe):  exe同目录/soundfont/ (Windows spec用'.')
        #       开发模式: 脚本目录下直接访问
        try:
            from ApolloTab.audio.synth_engine import SynthEngine
            import sys
            added = []
            if getattr(sys, 'frozen', False):
                # ---- 添加多个可能的打包后路径 ----
                exe_dir = os.path.dirname(sys.executable)
                # (1) onedir 模式: exe同目录/_internal/soundfont/
                sf_dir_internal = os.path.join(exe_dir, '_internal', 'soundfont')
                if sf_dir_internal not in SynthEngine.SOUNDFONT_SEARCH_PATHS and os.path.isdir(sf_dir_internal):
                    SynthEngine.SOUNDFONT_SEARCH_PATHS.insert(0, sf_dir_internal)
                    added.append(sf_dir_internal)
                # (2) onedir 模式: exe同目录/soundfont/ (Windows spec用 '.')
                sf_dir_exe = os.path.join(exe_dir, 'soundfont')
                if sf_dir_exe not in SynthEngine.SOUNDFONT_SEARCH_PATHS and os.path.isdir(sf_dir_exe):
                    SynthEngine.SOUNDFONT_SEARCH_PATHS.insert(0, sf_dir_exe)
                    added.append(sf_dir_exe)
                # (3) .app bundle 模式: .app/Contents/Resources/soundfont/
                if '.app/Contents/MacOS' in exe_dir:
                    resources_dir = os.path.join(os.path.dirname(exe_dir), 'Resources')
                    sf_dir_bundle = os.path.join(resources_dir, 'soundfont')
                    if sf_dir_bundle not in SynthEngine.SOUNDFONT_SEARCH_PATHS and os.path.isdir(sf_dir_bundle):
                        SynthEngine.SOUNDFONT_SEARCH_PATHS.insert(0, sf_dir_bundle)
                        added.append(sf_dir_bundle)
            else:
                # 开发模式: 脚本所在目录
                sf_dir = os.path.join(_APP_BASE_DIR, 'soundfont')
                if sf_dir not in SynthEngine.SOUNDFONT_SEARCH_PATHS and os.path.isdir(sf_dir):
                    SynthEngine.SOUNDFONT_SEARCH_PATHS.insert(0, sf_dir)
                    added.append(sf_dir)
            if added:
                print(f"[Audio] SoundFont搜索路径已添加({len(added)}个): {added}")
        except Exception as e:
            print(f"[Audio] 警告: 无法设置SoundFont搜索路径: {e}")
        
        # 设置音符回调(视觉高亮同步)
        success = self.gtp_player.init_audio(note_callback=self._on_audio_note_played)
        
        if not success:
            self.audio_btn.setEnabled(False)
            self.audio_btn.setToolTip(I18n.t("toolbar.audio_error_tooltip"))
            return
        
        # 更新时间线数据
        self._playhead_timeline = self.gtp_player.playhead_timeline
        self._total_audio_duration_ms = self.gtp_player.total_duration_ms
    
    def _set_audio_mode(self, mode: str)->None:
        """
        Phase 3/4: 切换音频播放模式(3种模式)
        
        参数:
            mode: 目标模式
              - "all":     全轨并轨 - 所有音轨同时播放(默认, 乐队合奏效果)
              - "current": 仅当前轨 - 只播放当前选中音轨的音频
              - "off":     关闭音频 - 仅滚动播放，不输出声音
        
        原理: 用户通过音频按钮下拉菜单选择模式，委托给 GTPPlayer 处理。
              切换时如果正在播放会自动重建事件序列并继续播放。
        """
        from ApolloTab import GTPPlayer  # 延迟导入(仅GTP文件需要)
        # 检查GTP播放器是否可用
        if self.gtp_player:
            old_mode = self.gtp_player.audio_mode
            
            # 委托给GTPPlayer处理模式切换
            self.gtp_player.set_audio_mode(mode)
            
            # 更新UI状态
            self._update_audio_button_ui(mode)

            # === 速度控件显隐切换 ===
            # 原理: GTP文件在 all/current 模式下由BPM时间驱动滚动(不需要手动速度控制)，
            #       但 off 模式下降级为线性恒速滚动(需要 base_speed + 曲线控制)
            is_off = (mode == "off")
            if hasattr(self, 'speed_group_box'):
                self.speed_group_box.setVisible(is_off)
            if hasattr(self, 'speed_spin'):
                self.speed_spin.setVisible(is_off)
            if hasattr(self, 'curve_btn'):
                self.curve_btn.setVisible(is_off)
            if hasattr(self, 'curve_status_label'):
                self.curve_status_label.setVisible(is_off)

            # 重建播放光标时间线（如果布局数据可用）
            if (self.images and self._page_layouts and
                mode != GTPPlayer.MODE_OFF):
                # 使用统一的_build_playhead_timeline()方法(内部会记录宽度用于resizeEvent检测)
                self._build_playhead_timeline()
        else:
            # 无GTP播放器时只更新UI
            self._update_audio_button_ui(mode)
    
    def _update_audio_button_ui(self, mode: str) -> None:
        """更新音频按钮的UI显示"""
        # 更新菜单项勾选状态
        if hasattr(self, '_audio_action_all'):
            self._audio_action_all.setChecked(mode == "all")
            self._audio_action_current.setChecked(mode == "current")
            self._audio_action_off.setChecked(mode == "off")
        
        # 更新按钮文字和样式
        if mode == "all":
            self.audio_btn.setText(I18n.t("toolbar.audio_all"))
            self.audio_btn.setStyleSheet(
                f"QToolButton{{background-color:{ThemeManager.get('accent', '#F97316')};"
                f"border-radius:4px;padding:4px 10px;}}"
            )
        elif mode == "current":
            self.audio_btn.setText(I18n.t("toolbar.audio_current"))
            self.audio_btn.setStyleSheet(
                f"QToolButton{{background-color:{ThemeManager.get('primary', '#3B82F6')};"
                f"border-radius:4px;padding:4px 10px;}}"
            )
        else:  # "off"
            self.audio_btn.setText(I18n.t("toolbar.audio_off"))
            self.audio_btn.setStyleSheet("")
    
    def _toggle_audio(self, checked: bool)->None:
        """保留兼容接口（已由 _set_audio_mode 替代）"""
        self._set_audio_mode("all" if checked else "off")
    
    def _on_audio_note_played(self, midi_pitch: int, velocity: int, time_ms: float)->None:
        """
        Phase 3: 音频音符触发回调(由SynthEngine在note_on时调用)
        
        功能: 记录当前正在发声的音符信息，
              用于 DisplayWidget.paintEvent 绘制高亮框。
        
        参数:
            midi_pitch: MIDI音高值
            velocity:   力度
            time_ms:    事件时间位置(毫秒)
        """
        self._current_highlight = (midi_pitch, velocity, time_ms)
        # 触发重绘以更新高亮
        if hasattr(self, 'display_widget'):
            self.display_widget.update()
    
    def _build_playhead_timeline(self)->None:
        """
        构建播放光标时间线 - 委托给 GTPPlayer 处理
        
        原理: 调用 GTPPlayer.build_timeline() 生成时间线索引，
              将每个拍(Beat)映射到其音频时间、屏幕X坐标和滚动Y位置。
              
        注意: 此方法已迁移到 gtp_engine/player.py 中的 GTPPlayer 类，
              主程序仅作为薄封装层调用。
        """
        if not self.gtp_player or not self.images or not self._page_layouts:
            return
        
        # 使用 display_widget 宽度作为显示区域宽度（scroll_area 可能尚未初始化）
        display_w = max(self.display_widget.width() - 20, 100)  # 减去左右边距，最小100px
        
        # 委托给GTPPlayer构建时间线
        timeline = self.gtp_player.build_timeline(
            self._page_layouts, 
            self.images, 
            display_w
        )
        
        # 更新主程序的时间线数据
        self._playhead_timeline = timeline
        self._total_audio_duration_ms = self.gtp_player.total_duration_ms

        # [v2.1.0] 记录构建timeline时的display_widget宽度
        # 用于resizeEvent中检测宽度变化以决定是否需要重建timeline(修复全屏滚动偏移)
        self._last_timeline_build_width = self.display_widget.width()
    
    def _update_playhead(self, time_ms: float = None)->None:
        """
        根据当前播放时间更新光标位置 - 委托给 GTPPlayer 处理
        
        参数:
            time_ms: 当前音频时间(毫秒)。None则从GTPPlayer获取。
        
        更新 self._playhead_info 为:
            (page_idx, sys_idx, meas_idx, beat_idx, x_in_page, progress_in_beat)
        其中 progress_in_beat ∈ [0,1) 表示当前拍内的进度。
        
        注意: 此方法已迁移到 gtp_engine/player.py 中的 GTPPlayer 类，
              主程序仅作为薄封装层调用。
        """
        if self.gtp_player:
            # 委托给GTPPlayer处理
            info = self.gtp_player.update_playhead(time_ms)
            self._playhead_info = info
        else:
            self._playhead_info = None
    
    def _time_to_scroll_pos(self, time_ms: float)->float:
        """
        根据音频时间计算对应的滚动Y位置 - 委托给 GTPPlayer 处理
        
        参数:
            time_ms: 当前音频时间(毫秒)
            
        返回:
            对应的滚动Y位置(像素)
        """
        if self.gtp_player:
            return self.gtp_player.time_to_scroll_pos(
                time_ms, 
                self.total_scroll_distance, 
                self.display_widget.height()
            )
        return 0.0
    
    def _scroll_pos_to_time(self, scroll_pos: float) -> float:
        """
        根据滚动Y位置反推对应的音频时间 - 委托给 GTPPlayer 处理
        
        参数:
            scroll_pos: 滚动位置(像素)
            
        返回:
            对应的音频时间(毫秒)
        """
        if self.gtp_player:
            return self.gtp_player.scroll_pos_to_time(
                scroll_pos, 
                self.total_scroll_distance, 
                self.display_widget.height()
            )
        return 0.0
    
    # ========== 标注功能 ==========
    
    def _switch_track_annotations(self, old_track: int, new_track: int) -> None:
        """切换音轨时保存/加载对应音轨的标注数据"""
        # 保存旧音轨的标注
        if old_track >= 0:
            self._save_track_annotations(old_track)
        
        # 更新当前音轨索引
        self.gtp_player.current_track = new_track
        
        # 加载新音轨的标注
        self._load_track_annotations(new_track)
    
    def _save_track_annotations(self, track_index: int) -> None:
        """保存指定音轨的标注数据到文件"""
        if not self.annotations:
            return
        
        # 构建文件路径
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        ann_file = os.path.join("annotations", f"{base_name}_track{track_index}.json")
        
        # 保存到文件
        try:
            os.makedirs("annotations", exist_ok=True)
            with open(ann_file, 'w', encoding='utf-8') as f:
                json.dump(self.annotations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[标注] 保存失败: {e}")
    
    def _load_track_annotations(self, track_index: int) -> None:
        """加载指定音轨的标注数据"""
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        ann_file = os.path.join("annotations", f"{base_name}_track{track_index}.json")
        
        if os.path.exists(ann_file):
            try:
                with open(ann_file, 'r', encoding='utf-8') as f:
                    self.annotations = json.load(f)
            except Exception as e:
                print(f"[标注] 加载失败: {e}")
                self.annotations = []
        else:
            self.annotations = []
    
    def _tick(self)->None:
        """
        播放定时器回调 - 每帧执行(已优化: 时间驱动滚动+图片缓存+节流UI)
        
        核心改进: 当音频引擎可用且有播放时间线时，使用音乐时间驱动滚动位置，
        而非线性恒速滚动。这样播放条速度会随音符时值自动变化：
        - 音符密集区(16/32分音符) → 同时间内scroll_y变化大 → 滚动加快
        - 音符稀疏区(全/二分音符) → 同时间内scroll_y变化小 → 滚动减慢
        
        性能优化点:
          1. 图片缩放缓存: paintEvent使用预缓存的scaled图片，避免每帧重新scale(CPU密集)
          2. UI节流: 进度条位置每帧更新(轻量)，页码同步/标签每3帧更新一次
        """
        # === 判断是否使用时间驱动滚动(有GTP播放器 + 有时间线 + 音频未关闭) ===
        # 注意: 当音频模式为"off"时，虽然is_audio_ready可能为True(引擎已初始化)，
        #       但current_time_ms不会递增(音频未实际播放)，必须降级为线性滚动
        use_time_scroll = (
            self.gtp_player is not None
            and self.gtp_player.is_audio_ready
            and len(self._playhead_timeline) >= 2
            and self.gtp_player.audio_mode != 'off'  # off模式下禁用时间驱动滚动
        )

        if use_time_scroll:
            # --- 时间驱动模式: 滚动位置由音乐时间决定 ---
            # [v2.0.4] 循环逻辑已下沉到库层(SynthEngine内置A/B循环)
            # UI层只需正常读取audio_time_ms并计算position即可
            # 库层在音频线程内部处理循环重启，无竞态、无需冷却、无需模拟时钟
            audio_time_ms = self.gtp_player.current_time_ms
            # 用速度曲线调整时间流逝速度(曲线加速=时间变快)
            if self.speed_curve.is_enabled and len(self.speed_curve.points) >= 2:
                curve_speed = self._get_curve_speed()
                time_scale = self.base_speed / max(curve_speed, 1)
                effective_time = audio_time_ms * time_scale
            else:
                effective_time = audio_time_ms

            # === 时间驱动位置计算（干净版：无冷却、无模拟时钟） ===
            time_based_pos = self._time_to_scroll_pos(effective_time)

            if self._click_jump_target >= 0:
                if time_based_pos < self._click_jump_target:
                    self.current_position = self._click_jump_target
                else:
                    self.current_position = time_based_pos
                    self._click_jump_target = -1.0
            else:
                self.current_position = time_based_pos

            self.play_time = effective_time / 1000.0

            total_dur = getattr(self, '_total_audio_duration_ms', 0) or 1
            pct = min((effective_time / total_dur) * 100, 100)

            # === 全曲循环(all模式): UI层仍需处理(库层只支持region循环) ===
            if self.loop_config.is_enabled and self.loop_config.loop_type == 'all':
                if effective_time >= total_dur:
                    self.current_position = 0
                    self.play_time = 0
                    if self.gtp_player:
                        self.gtp_player.seek(0)
            # === 播放结束判断 ===
            # [v2.0.6 修复] region循环模式下，播放结束由库层(SynthEngine)内部管理
            # UI层不应因 effective_time >= total_dur 而提前调用 stop_playback()
            # 原因: _loop_end_ms(B点)通常 < _total_audio_duration_ms(总时长)
            #       当 effective_time 达到总时长时，库层可能正在执行循环重启
            #       此时UI层stop会导致循环失效("到达B点后不seek回A点")
            elif effective_time >= total_dur:
                # region循环模式: 交给库层管理生命周期，UI层不干预
                if self.loop_config.is_enabled and self.loop_config.loop_type == 'region':
                    pass  # 库层会自动循环回A点，UI层继续读取current_time_ms即可
                else:
                    # 非循环或all循环模式: 正常停止播放
                    self.current_position = self.total_scroll_distance
                    self.stop_playback(reset_position=True)

        else:
            # --- 线性恒速模式(无音频时降级使用) ---
            if self.speed_curve.is_enabled and len(self.speed_curve.points)>=2:
                # 获取曲线速度值(范围约25~120)，作为倍率作用于base_speed
                # 映射公式: 实际速度 = base_speed * (curve_speed / CURVE_BASE)
                #   curve_speed=50 → 1.0倍(与base_speed相同，基准速度)
                #   curve_speed=100→ 2.0倍(更慢，总时长翻倍)
                #   curve_speed=25 → 0.5倍(更快，总时长减半)
                CURVE_BASE = 50.0  # 基准值: 曲线speed=50时等于base_speed
                curve_val=self._get_curve_speed()
                current_speed=self.base_speed * (curve_val / CURVE_BASE)
            else:
                current_speed=self.base_speed

            self._calculate_scroll_step(current_speed)
            self.current_position+=self.scroll_step
            # 线性模式: 使用perf_counter计算实际帧间隔，保证play_time与现实时间严格同步
            # 之前用硬编码33.0/1000.0假设每帧精确33ms，但渲染开销导致实际帧间隔>33ms，
            # 导致play_time累加比真实时间慢(显示的时间比实际经过的少)
            now = time.perf_counter()
            if self._last_tick_time > 0:
                self.play_time += (now - self._last_tick_time)
            self._last_tick_time = now

            # 循环检查
            should_loop=self._check_loop_condition()
            if should_loop:
                if self.loop_config.loop_type=='all':
                    self.current_position=0;self.play_time=0
                elif self.loop_config.loop_type=='region':
                    self.current_position=self.total_scroll_distance*self.loop_config.start_position/100
            elif self.current_position>=self.total_scroll_distance:
                self.current_position=self.total_scroll_distance
                self.stop_playback(reset_position=True)  # 播放结束，重置位置

            if self.total_scroll_distance > 0:
                pct = (self.current_position / self.total_scroll_distance) * 100
            else:
                pct = 0

        # 更新播放光标位置(每帧同步)
        self._update_playhead()

        # === 重绘画布(使用缓存图片，已优化) ===
        self.display_widget.update()

        # === 更新进度显示(节流: 页码同步每3帧执行一次) ===
        if not hasattr(self, '_tick_counter'):
            self._tick_counter = 0
        self._tick_counter += 1

        # 状态信息栏已移除，跳过位置标签更新(简化界面)
        self.progress_bar.blockSignals(True)
        self.progress_bar.position = pct
        self.progress_bar.blockSignals(False)

        secs = int(self.play_time)
        self.time_start_label.setText(f"{secs // 60:02d}:{secs % 60:02d}")
        
        # 页码同步: 每3帧执行一次(避免每帧遍历所有图片计算高度)
        if self._tick_counter % 3 == 1:
            self._sync_page_input()

    def _get_curve_speed(self)->float:
        """
        根据速度曲线获取当前时刻的速度值(带排序缓存优化)
        
        性能优化: 之前每帧(30fps)都执行sorted()排序O(k log k)，
                  现在通过id()检测points列表是否变化，仅在变化时重新排序。
        """
        if not self.speed_curve.points or self.total_scroll_distance<=0:
            return self.base_speed
        # 脏检测: points列表引用未变时复用缓存
        current_id = id(self.speed_curve.points)
        if current_id != self._cached_curve_pts_id:
            self._cached_sorted_curve_pts = sorted(self.speed_curve.points, key=lambda p:p.position)
            self._cached_curve_pts_id = current_id
        pts = self._cached_sorted_curve_pts
        progress_pct=(self.current_position/self.total_scroll_distance)*100
        progress_pct=max(0,min(100,progress_pts:=progress_pct))
        for i in range(len(pts)-1):
            p1,p2=pts[i],pts[i+1]
            if p1.position<=progress_pts<=p2.position:
                t=(progress_pts-p1.position)/(p2.position-p1.position) if p2.position!=p1.position else 0
                return p1.speed+t*(p2.speed-p1.speed)
        return self.base_speed

    def _get_curve_average_speed(self)->float:
        """
        计算速度曲线的加权平均速度(用于估算总播放时长)

        原理: 曲线将播放进度分为多段，每段有自己的speed值。
              总时长 ≈ Σ(每段长度比例 × 该段有效速度) × TIME_SCALE
              加权平均速度 = Σ(每段长度比例 × 该段有效速度)

        返回值: 转换后的实际ms值(= base_speed * avg_curve_speed / 50)
        """
        if not self.speed_curve.points or len(self.speed_curve.points) < 2:
            return self.base_speed

        pts = sorted(self.speed_curve.points, key=lambda p: p.position)
        CURVE_BASE = 50.0  # 与 _tick 中的倍率基准一致

        total_weighted_speed = 0.0
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            segment_len = p2.position - p1.position  # 该段的进度百分比长度
            avg_segment_speed = (p1.speed + p2.speed) / 2.0  # 该段平均曲线speed
            # 转换为实际有效速度并按段长加权
            total_weighted_speed += segment_len * (avg_segment_speed / CURVE_BASE)

        # 加权平均后乘以base_speed得到实际有效ms值
        return self.base_speed * (total_weighted_speed / 100.0)  # 总进度100%

    def _calculate_scroll_step(self,speed_ms:float)->None:
        """
        根据速度(ms)计算每帧滚动像素数 - 使用固定30fps定时器确保平滑

        核心设计: 总时长(秒) = speed_ms * TIME_SCALE，scroll_step 反推保证正好播完。

          scroll_step = total_distance / (总时长 * 30帧/秒)
                     = total_distance / ((speed_ms * TIME_SCALE) * 30)

        验证:
          30fps下，总帧数 = 总时长 * 30
          每帧滚动 = total_distance / 总帧数
          总帧数 * 每帧滚动 = total_distance ✓ (正好播完)
          play_time 每帧 +0.033s → 总时长后 play_time ≈ 现实时间 ✓

        参数:
            speed_ms: 当前有效速度(毫秒)。值越大→播放越慢(总时长更长)

        调整效果(TIME_SCALE=0.25, 谱面10000px):
            speed_ms=350 → 87.5秒总时长, ~3.8px/帧
            speed_ms=500 → 125秒总时长, ~2.67px/帧 (默认)
            speed_ms=700 → 175秒总时长, ~1.9px/帧
        """
        if speed_ms<=0:
            speed_ms=1

        if self.total_scroll_distance > 0:
            # 总时长(秒) = speed_ms * TIME_SCALE
            total_duration_s = speed_ms * self.TIME_SCALE
            # 每帧像素 = 总距离 / (总时长秒数 * 30fps)
            self.scroll_step = self.total_scroll_distance / (total_duration_s * 30.0)
        else:
            self.scroll_step = 1.0

    def _calculate_total_distance(self)->None:
        """计算总可滚动距离
        原理: 总内容高度 - 显示区域高度 = 最大可滚动距离
        播放结束条件: current_position >= total_scroll_distance 时，末页底部刚好到达显示区底部
        
        性能优化(P0-2): 同时计算页面累积高度前缀和数组(_page_cumulative_heights)，
                        供 _sync_page_input() 使用二分查找替代O(n)线性遍历。
        """
        if not self.images:return
        # 必须使用 display_widget 的宽度(与 paintEvent 绘制时一致)，而非 DisplayWindow 的宽度
        ww=self.display_widget.width()
        total=0
        # 页面累积高度前缀和（性能优化P0-2: 二分查找定位当前页）
        cumulative = [0.0]  # 第0页开始位置为0
        for img in self.images:
            if not img.isNull():
                sw=ww-20;ratio=img.width()>0 and sw/img.width() or 1
                h=img.height()*ratio+5
                total+=h
                cumulative.append(total)
            else:
                cumulative.append(cumulative[-1])
        self._page_cumulative_heights = cumulative
        # 使用display_widget的实际高度(不含工具栏/控制面板)
        # 安全检查: 如果display_widget尚未完成布局(height过小)，使用窗口高度估算
        display_h=self.display_widget.height()
        if display_h<100:  # 布局未完成时的兜底值
            display_h=self.height()*2//3  # 估算显示区约占窗口高度的2/3
        self.total_scroll_distance=max(0,total-display_h)
        # 更新总时长显示(右侧时间标签)
        # 线性模式: 总时长 = 有效速度 * TIME_SCALE
        #   无曲线时: 有效速度 = base_speed
        #   有曲线时: 有效速度 = 曲线各段速度的加权平均(积分近似)
        effective_speed = self._get_curve_average_speed() if (
            self.speed_curve.is_enabled and len(self.speed_curve.points) >= 2
        ) else self.base_speed
        secs = int(effective_speed * self.TIME_SCALE)
        self.time_end_label.setText(f"{secs//60:02d}:{secs%60:02d}")

    def _check_loop_condition(self)->bool:
        """检查是否需要循环"""
        if not self.loop_config.is_enabled or self.loop_config.loop_type=='none':
            return False
        if self.loop_config.loop_type=='all':
            return self.current_position>=self.total_scroll_distance
        elif self.loop_config.loop_type=='region':
            pos_pct=(self.current_position/self.total_scroll_distance)*100 if self.total_scroll_distance>0 else 0
            return pos_pct>=self.loop_config.end_position
        return False

    def _sync_play_time_from_position(self)->None:
        """
        根据当前滚动位置同步播放时间(线性模式/外部位置变更时调用)

        原理: 当用户通过滚轮、进度条拖动、点击谱面等方式改变位置时，
              play_time 需要与 current_position 保持比例一致，否则时间显示会错乱。

        线性模式: 总时长 = base_speed * DURATION_SCALE (秒)
                 play_time = (position / total_distance) * 总时长
        时间驱动模式(GTP音频): 总时长 = _total_audio_duration_ms / 1000
                             play_time 由音频引擎驱动，此处不覆盖
        """
        if self.total_scroll_distance <= 0:
            return
        ratio = self.current_position / self.total_scroll_distance
        ratio = max(0.0, min(ratio, 1.0))  # 限制在[0,1]

        # 判断当前使用哪种模式的总时长
        if (self.gtp_player and self.gtp_player.is_audio_ready
                and self.gtp_player.audio_mode != 'off'):
            # 时间驱动模式: 使用音频总时长
            total_dur_s = getattr(self, '_total_audio_duration_ms', 0) / 1000.0 or 1.0
        else:
            # 线性模式: 根据速度公式反推总时长
            # 有曲线时使用加权平均有效速度，无曲线时用base_speed
            total_dur_s = self._get_curve_average_speed() * self.TIME_SCALE

        self.play_time = ratio * total_dur_s

    def update_progress_display(self)->None:
        """更新进度显示(非播放时调用，如拖动进度条/滚轮滚动)"""
        if self.total_scroll_distance>0:
            pct=(self.current_position/self.total_scroll_distance)*100
        else:
            pct=0
        # 状态信息栏已移除，跳过位置标签更新(简化界面)
        self.progress_bar.blockSignals(True)
        self.progress_bar.position=pct
        self.progress_bar.blockSignals(False)
        secs=int(self.play_time)
        self.time_start_label.setText(f"{secs//60:02d}:{secs%60:02d}")
        # 同步页码(非播放时每次都同步)
        self._sync_page_input()

    def _sync_page_input(self)->None:
        """
        同步页码输入框(从update_progress_display中提取的节流方法)
        
        性能优化(P0-2): 使用预计算的 _page_cumulative_heights 前缀和数组 +
                      bisect.bisect_left 二分查找，将O(n)线性遍历降为O(log n)。
                      _page_cumulative_heights 在 _calculate_total_distance() 中计算。
        """
        if not (hasattr(self,'page_input') and self.images and len(self.images)>1):
            return
        # 使用累积高度前缀和 + 二分查找定位当前页
        if self._page_cumulative_heights and len(self._page_cumulative_heights) > 1:
            # bisect_left: 找到第一个 > current_position 的页面索引
            # cumulative_heights[i] 是第i页的起始位置，cumulative_heights[i+1] 是结束位置
            current_page = bisect.bisect_right(self._page_cumulative_heights, self.current_position)
            current_page = max(1, min(current_page, len(self.images)))
        else:
            # 降级方案: 累积高度数组未计算时用线性遍历
            ww=self.display_widget.width()-20
            offset=0.0;current_page=1
            for i,img in enumerate(self.images):
                if img.isNull(): continue
                ratio=img.width()>0 and ww/img.width() or 1
                h=img.height()*ratio+5
                if offset+h>self.current_position:
                    current_page=i+1; break
                offset+=h
            else:
                current_page=len(self.images)
        self.page_input.blockSignals(True)
        self.page_input.setValue(current_page)
        self.page_input.blockSignals(False)
        # 性能优化(P2-4): 通知DisplayWidget当前页面位置，触发LRU缓存窗口更新
        self.display_widget.set_active_page(current_page - 1)  # 转为0-based索引

    # ========== 事件处理 ==========

    def _on_speed_changed(self,val:int)->None:
        """
        速度改变回调 - 更新base_speed参数 + 重算滚动步长 + 更新总时长显示
        
        原理(v1.6.0+): 定时器已改为固定33ms(30fps)，速度通过以下方式生效:
          - 时间驱动模式(有音频): _tick()中 time_scale = base_speed / curve_speed
          - 线性模式(无音频): _calculate_scroll_step()使用base_speed计算scroll_step
          
        注意: 不再调用timer.start(val)，因为那会把33ms定时器重置为350-700ms，
              导致帧率从30fps骤降到1-3fps，播放条严重卡顿。
        """
        self.base_speed=val
        # 重新计算每帧滚动步长(线性模式立即生效)
        self._calculate_scroll_step(val)
        # 重新计算并更新总时长显示(右侧时间标签)
        if self.total_scroll_distance > 0:
            effective_speed = self._get_curve_average_speed() if (
                self.speed_curve.is_enabled and len(self.speed_curve.points) >= 2
            ) else self.base_speed
            secs = int(effective_speed * self.TIME_SCALE)
            self.time_end_label.setText(f"{secs//60:02d}:{secs%60:02d}")
        # 按当前进度比例重新同步play_time(总时长变了，当前时间也要按比例调整)
        self._sync_play_time_from_position()
        # base_speed变化会在下一次_tick()自动生效(已通过scroll_step生效)

    def _on_progress_changed(self,pos:float)->None:
        """
        进度条拖动回调: 同步更新滚动位置 + 音频跳转
        
        原理: 用户拖动进度条时，除了更新视觉滚动位置外，
              还需要让音频引擎跳转到对应时间位置(如果音频正在播放)。
        """
        if self.total_scroll_distance>0:
            self.current_position=pos/100*self.total_scroll_distance
            self.display_widget.update()
            
            # === 音频同步跳转 ===
            # 仅在GTP播放器已初始化且启用时执行seek
            if self.gtp_player and self.gtp_player.is_audio_ready:
                try:
                    total_ms = self.gtp_player.total_duration_ms
                    
                    if total_ms > 0:
                        target_ms = (pos / 100.0) * total_ms
                        self.gtp_player.seek(target_ms)
                except Exception as e:
                    print(f"[Audio] seek失败: {e}")

            # 同步播放时间(线性模式/拖动进度条后时间需与位置一致)
            self._sync_play_time_from_position()

    def _on_region_selected(self,start:float,end:float)->None:
        """A-B区域选择(进度条Ctrl+Click=设A, Shift+Click=设B)"""
        self.loop_config.start_position=start
        self.loop_config.end_position=end
        self.progress_bar.set_region(start,end)
        if hasattr(self, 'ab_info_label'):
            self.ab_info_label.setText(f"A-B: {start:.1f}% - {end:.1f}%")
        
        # [v2.0.4] 如果已在region模式，立即同步到库层
        if (self.loop_config.is_enabled 
            and self.loop_config.loop_type == 'region'
            and self.gtp_player 
            and self.gtp_player.is_audio_ready):
            self.gtp_player.set_loop_region_by_position(
                start_pct=self.loop_config.start_position,
                end_pct=self.loop_config.end_position
            )

    def _on_loop_mode_changed(self,idx:int)->None:
        """
        循环模式改变
        
        [v2.0.4] A/B循环逻辑已下沉到库层(SynthEngine内置):
          - 切换到region模式时，调用 gtp_player.set_loop_region_by_position() 
            将百分比转换为小节索引，再基于小节边界设置循环
          - 切换到none模式时，调用 gtp_player.clear_loop_region() 取消循环
          - UI层不再需要任何冷却/帧计数器/模拟时钟机制
        """
        modes=['none','all','region']
        self.loop_config.loop_type=modes[idx]
        self.loop_config.is_enabled=(idx>0)

        if idx==2:  # A-B区域循环模式
            # 步骤1: 如果A>B(用户先设B点后设A点)，交换使start<end
            needs_swap=self.loop_config.end_position<self.loop_config.start_position
            if needs_swap:
                self.loop_config.start_position,self.loop_config.end_position = \
                    self.loop_config.end_position,self.loop_config.start_position
                self.progress_bar.set_region(self.loop_config.start_position,self.loop_config.end_position)

            # 步骤2: 防御性检查 — 如果A/B仍为默认值(0/100)，说明用户还没手动设置过
            # 此时使用合理的默认值: A=开头(0%), B=结尾(100%)，即全谱循环
            # 用户后续通过Ctrl/Shift点击进度条或点击A/B按钮可重新设定
            if (self.loop_config.start_position == 0.0 
                and self.loop_config.end_position == 100.0):
                print("[DisplayWindow] A/B循环: 使用默认值(0%-100%), 用户尚未手动设置A/B点")
            
            # 步骤3: 通过库层API设置基于小节的循环(核心改动!)
            # 将UI层的百分比位置→转换为小节索引→对齐到小节边界→设置循环
            if self.gtp_player and self.gtp_player.is_audio_ready:
                result = self.gtp_player.set_loop_region_by_position(
                    start_pct=self.loop_config.start_position,
                    end_pct=self.loop_config.end_position
                )
                if not result:
                    print(f"[DisplayWindow] 警告: 库层循环设置失败 "
                          f"(start={self.loop_config.start_position:.1f}%, "
                          f"end={self.loop_config.end_position:.1f}%)")
                
                # [v2.0.4 修复] 设置循环后立即seek到A点(如果正在播放)
                # set_loop_region()只设置循环参数，不会主动跳转
                # 用户期望切换到region模式后从A点开始循环播放
                if self.timer.isActive() and result:
                    start_pct = self.loop_config.start_position
                    total_dur = getattr(self, '_total_audio_duration_ms', 0) or 60000
                    target_ms = total_dur * start_pct / 100
                    print(f"[DisplayWindow] 循环已启用, 立即seek到A点: {target_ms:.0f}ms")
                    try:
                        self.gtp_player.seek(target_ms)
                        # 同步UI position到A点
                        if self.total_scroll_distance > 0:
                            self.current_position = self.total_scroll_distance * start_pct / 100
                        self.play_time = target_ms / 1000.0
                    except Exception as e:
                        print(f"[DisplayWindow] seek到A点失败: {e}")

            # 步骤4: 显示A>B警告
            if needs_swap and hasattr(self,'ab_info_label'):
                self.ab_info_label.setText(I18n.t("ab_info.ab_set_both"))

        elif idx==0:
            # 清除循环设置
            if self.gtp_player and self.gtp_player.is_audio_ready:
                self.gtp_player.clear_loop_region()
            self.progress_bar.clear_region()
            if hasattr(self, 'ab_info_label'):
                self.ab_info_label.setText("")

    def _set_ab_point(self,point:str)->None:
        """
        设置A/B点
        
        [v2.0.4 修复] 优先使用GTP播放时间计算百分比(而非UI层滚动位置)
        原因: current_position在未播放/未滚动时为0，导致pct=0→小节索引=0
        新方案: 
          - GTP模式: 用 audio_time_ms / total_duration_ms → 准确反映当前播放到哪个小节
          - 非GTP/off模式: 回退到 current_position / total_scroll_distance
        """
        # 优先用GTP音频时间(更准确: 直接对应小节位置)
        if (self.gtp_player and self.gtp_player.is_audio_ready 
            and self.gtp_player.total_duration_ms > 0):
            pct = (self.gtp_player.current_time_ms / self.gtp_player.total_duration_ms) * 100
            source = f"audio_time={self.gtp_player.current_time_ms:.0f}ms"
        elif self.total_scroll_distance > 0:
            pct = (self.current_position / self.total_scroll_distance) * 100
            source = f"scroll_pos={self.current_position:.0f}"
        else:
            pct = 0
            source = "default=0"
        
        if point=='a':
            self.loop_config.start_position = pct
            print(f"[DisplayWindow] 设A点: {source}, pct={pct:.1f}%")
        else:
            self.loop_config.end_position = pct
            print(f"[DisplayWindow] 设B点: {source}, pct={pct:.1f}%")
        self.progress_bar.set_region(self.loop_config.start_position,self.loop_config.end_position)
        if hasattr(self, 'ab_info_label'):
            self.ab_info_label.setText(f"A-B: {self.loop_config.start_position:.1f}% - {self.loop_config.end_position:.1f}%")
        
        # [v2.0.4] A/B两点都设置好后，立即同步到库层(基于小节的循环)
        if (self.loop_config.is_enabled 
            and self.loop_config.loop_type == 'region'
            and self.gtp_player 
            and self.gtp_player.is_audio_ready):
            self.gtp_player.set_loop_region_by_position(
                start_pct=self.loop_config.start_position,
                end_pct=self.loop_config.end_position
            )

    def _clear_ab_points(self)->None:
        """清除AB点"""
        self.loop_config.start_position=0
        self.loop_config.end_position=100
        self.progress_bar.clear_region()
        # [v2.0.4] 同步清除库层循环设置
        if self.gtp_player and self.gtp_player.is_audio_ready:
            self.gtp_player.clear_loop_region()
        if hasattr(self, 'ab_info_label'):
            self.ab_info_label.setText("")

    # ========== 标注管理 ==========

    def add_annotation(self,ann:Annotation)->None:
        """添加标注(集成全局撤销)"""
        self._anno_save_snapshot()  # 修改前保存快照
        self.annotations.append(ann)
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()

    def _open_annotation_manager(self)->None:
        """打开标注管理器(保存引用供撤销/重做同步)"""
        dlg=AnnotationManagerDialog(self,self.annotations)
        self._ann_manager = dlg  # 保存引用，用于撤销/重做时同步列表
        dlg.annotationsChanged.connect(self._on_annotations_changed)
        dlg.exec_()
        self._ann_manager = None  # 关闭后清除引用

    def _on_annotations_changed(self,new_anns:List[Annotation])->None:
        """标注列表变更回调"""
        self.annotations=new_anns
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()

    def _get_annotation_file_path(self)->str:
        """
        获取当前音轨的标注存储路径(同名.anno.json策略 + 分轨)
        
        原理: 标注文件与源文件放在同一目录:
          - 非GTP/单轨: {源文件名}.anno.json (例: 晚安北京.png.anno.json)
          - GTP多轨:   {源文件名}.t{轨道号}.anno.json (例: song.gp4.t0.anno.json, song.gp4.t1.anno.json)
              每个音轨独立一个标注文件，切换音轨时自动加载对应轨道的标注。
        
        兼容性: 如果源文件路径无效(如多图模式)，回退到旧的 data/annotations/ 路径
        
        返回:
            标注文件的绝对路径字符串
        """
        if isinstance(self.file_path, str) and self.file_path:
            # GTP多轨文件: 文件名后追加 .t{track_idx}
            if self.gtp_player and self.gtp_player.is_loaded:
                return f"{self.file_path}.t{self.gtp_player.current_track}{ANNOTATION_EXT}"
            # 非GTP/单轨文件: 直接追加 .anno.json
            return self.file_path + ANNOTATION_EXT
        # 回退: 多图模式等无法确定源文件时，用旧路径
        base = "multi_image"
        os.makedirs(ANNOTATION_DIR, exist_ok=True)
        return os.path.join(ANNOTATION_DIR, f"{base}.json")

    def _get_annotation_file_path_legacy(self)->str:
        """
        获取旧版标注存储路径(data/annotations/{base}.json)
        用于向后兼容: 加载时同时检查新旧两个位置
        """
        if isinstance(self.file_path, str):
            base = os.path.splitext(os.path.basename(self.file_path))[0]
        else:
            base = "multi_image"
        os.makedirs(ANNOTATION_DIR, exist_ok=True)
        return os.path.join(ANNOTATION_DIR, f"{base}.json")

    def _load_annotations(self)->None:
        """
        从JSON加载标注 - 支持新旧两种路径(优先新路径)
        
        加载顺序:
          1. 新路径: {源文件}.anno.json (同目录)
          2. 旧路径: data/annotations/{base}.json (兼容旧版)
        """
        # 尝试新路径(同目录 .anno.json)
        new_path = self._get_annotation_file_path()
        old_path = self._get_annotation_file_path_legacy()
        
        load_from = None
        if os.path.exists(new_path):
            load_from = new_path
        elif os.path.exists(old_path):
            load_from = old_path  # 向后兼容: 旧位置有数据则加载
        
        if load_from:
            try:
                with open(load_from, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.annotations = [Annotation(**d) for d in data]
                return
            except Exception:
                pass
        self.annotations = []

    def _save_annotations(self)->None:
        """保存标注到JSON - 写入到源文件同目录的 .anno.json 文件"""
        try:
            fpath = self._get_annotation_file_path()
            dname = os.path.dirname(fpath)
            if dname:
                os.makedirs(dname, exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump([asdict(a) for a in self.annotations], f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存标注失败: {e}")

    def _switch_track_annotations(self, old_track:int, new_track:int)->None:
        """
        切换音轨时的标注切换(保存当前轨 → 加载目标轨)
        
        原理: GTP多轨文件每个音轨有独立的标注文件(.t0.anno.json, .t1.anno.json, ...)。
              切换音轨时:
                1. 将当前annotations存入分轨字典 _annotations_by_track[old_track]
                2. 从字典或文件中加载 new_track 的 annotations
                3. 更新画布显示 + 清空撤销/重做栈(跨轨撤销无意义)
        
        参数:
            old_track: 切换前的音轨索引
            new_track: 切换后的音轨索引
        """
        if old_track == new_track:
            return

        # 1. 保存当前轨标注到内存字典
        self._annotations_by_track[old_track] = self.annotations.copy()

        # 2. 持久化当前轨标注到文件(确保不丢失)
        try:
            fpath = self._get_annotation_file_path()  # 注意: 此时gtp_current_track还是old_track!
            dname = os.path.dirname(fpath)
            if dname:
                os.makedirs(dname, exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump([asdict(a) for a in self.annotations], f,
                          ensure_ascii=False, indent=2)
        except Exception:
            pass

        # 3. 加载目标轨标注(优先内存 > 文件 > 空列表)
        # 先更新GTP播放器的当前音轨索引
        if self.gtp_player:
            self.gtp_player.current_track = new_track

        if new_track in self._annotations_by_track and self._annotations_by_track[new_track]:
            # 内存中有缓存
            self.annotations = [Annotation(**asdict(a)) for a in self._annotations_by_track[new_track]]
        else:
            # 从文件加载或空列表
            self._load_annotations()
            self._annotations_by_track[new_track] = self.annotations.copy()

        # 4. 更新画布显示
        self.display_widget.set_annotations(self.annotations)

        # 5. 清空撤销/重做栈(跨轨操作不应共享撤销历史)
        self._undo_stack.clear()
        self._redo_stack.clear()

    # ========== 全局撤销/重做 ==========

    def _anno_save_snapshot(self)->None:
        """
        保存当前标注状态快照到撤销栈(修改前必须调用)
        
        性能优化(P0-3): 存储 dict 列表而非 Annotation 对象列表，
                        避免每次快照创建N个Annotation对象。
                        仅在撤销/重做时按需重建Annotation对象。
        
        使用场景: 所有修改annotations的操作前调用此方法:
                  - 双击画布添加/编辑标注
                  - 管理器中新增/编辑/删除/清空标注
        """
        snapshot = [asdict(a) for a in self.annotations]
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()  # 新操作清空重做栈
        # 限制深度防止内存膨胀
        if len(self._undo_stack) > self._UNDO_MAX_DEPTH:
            self._undo_stack.pop(0)

    def _anno_undo(self)->None:
        """
        Ctrl+Z 全局撤销 - 回退到上一个标注状态
        
        性能优化(P0-3): 栈中存储dict列表，撤销时按需重建Annotation对象。
        """
        if not self._undo_stack:
            return
        # 当前状态存入重做栈(存储dict，延迟重建)
        redo_snap = [asdict(a) for a in self.annotations]
        self._redo_stack.append(redo_snap)
        # 恢复上一个状态(从dict重建Annotation)
        prev = self._undo_stack.pop()
        self.annotations = [Annotation(**d) for d in prev]
        # 刷新UI
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()
        # 同步管理器(如果打开着)
        if hasattr(self, '_ann_manager') and self._ann_manager:
            self._ann_manager.annotations = self.annotations
            self._ann_manager._populate_list()

    def _anno_redo(self)->None:
        """
        Ctrl+Y 全局重做 - 恢复被撤销的状态
        
        性能优化(P0-3): 栈中存储dict列表，重做时按需重建Annotation对象。
        """
        if not self._redo_stack:
            return
        # 当前状态存入撤销栈(存储dict)
        undo_snap = [asdict(a) for a in self.annotations]
        self._undo_stack.append(undo_snap)
        # 恢复重做状态(从dict重建Annotation)
        nxt = self._redo_stack.pop()
        self.annotations = [Annotation(**d) for d in nxt]
        # 刷新UI
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()
        # 同步管理器(如果打开着)
        if hasattr(self, '_ann_manager') and self._ann_manager:
            self._ann_manager.annotations = self.annotations
            self._ann_manager._populate_list()

    def _create_annotation_at_cursor(self)->None:
        """
        在鼠标光标位置创建标注(Ctrl+K快捷键或右键菜单触发)
        
        原理: 获取鼠标全局坐标，转换为DisplayWidget相对坐标，
              然后调用标注创建逻辑(与双击空白处相同)
        """
        if not self.display_widget or not self.images:
            return
        # 获取鼠标在屏幕上的位置
        cursor_pos = QCursor.pos()
        # 转换为DisplayWidget的本地坐标
        local_pos = self.display_widget.mapFromGlobal(cursor_pos)
        # 确保坐标在控件范围内
        x = max(0, min(local_pos.x(), self.display_widget.width()))
        y = max(0, min(local_pos.y(), self.display_widget.height()))
        # 调用DisplayWidget的创建标注方法
        self.display_widget._create_annotation_at(x, y)

    # ========== 打印曲谱(含标注，支持分轨/分页/预览) ==========

    def _print_score(self, use_preview:bool=False)->None:
        """
        打印谱面(含标注)到打印机或打印预览

        功能:
          - 使用系统打印对话框选择打印机 / 或显示打印预览窗口
          - 分轨: GTP文件可选指定轨道打印，或"全部轨道"按顺序拼接
          - 分页: 可选单页、页码范围、全部页面
          - 标注: 完整渲染所有标注(颜色/字体/大小)
          - 自动分页: 内容超过一页时自动分多页打印
          - **GTP文件强制浅色主题**: 与导出一致，确保打印输出清晰可读

        原理:
          1. 弹出自定义打印设置对话框(PrintDialog)让用户选择轨道/页码范围
          2. 收集需要打印的图片列表(GTP多轨时按需重新渲染各轨，强制浅色主题)
          3. 根据模式:
             - 直接打印: 弹出QPrintDialog选择打印机 → _render_to_printer()
             - 打印预览: 弹出QPrintPreviewDialog → 用户确认后执行打印
          4. 排序规则与导出功能完全一致(复用_collect_export_data)

        参数:
            use_preview: 是否使用打印预览模式(True=预览, False=直接打印)

        调用方式: 工具栏"打印"下拉菜单触发
        """
        if not self.images or all(img.isNull() for img in self.images):
            QMessageBox.warning(self, I18n.t("messages.print_no_content"), I18n.t("messages.print_no_content_msg"))
            return

        # 弹出打印设置对话框(选择轨道和页码)
        dlg = PrintDialog(
            parent=self,
            src_name=os.path.basename(self.file_path) if isinstance(self.file_path, str) else I18n.t("app.score_name"),
            is_gtp=bool(self.gtp_player and self.gtp_player.is_loaded),
            gtp_track_count=self.gtp_track_combo.count() if self.gtp_track_combo else 0,
            current_track=self.gtp_player.current_track if self.gtp_player else 0,
            total_pages=len([i for i in self.images if not i.isNull()])
        )
        if dlg.exec_() != QDialog.Accepted:
            return

        # 获取用户选择
        track_mode = dlg.track_mode  # "current" | "all" | list[int]
        page_mode = dlg.page_mode    # "all" | ("range", start, end)

        try:
            # === Step 1: 收集要打印的数据(复用导出逻辑，GTP强制浅色主题) ===
            print_items = self._collect_export_data(track_mode, page_mode)
            # print_items: List[(images_list, annotations_list, track_label), ...]

            if not print_items or not any(item[0] for item in print_items):
                QMessageBox.warning(self, I18n.t("messages.print_no_content"), I18n.t("messages.print_no_data"))
                return

            # === Step 2: 根据模式执行打印或预览 ===
            if use_preview:
                self._show_print_preview(print_items)
            else:
                self._execute_print(print_items)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, I18n.t("messages.print_fail"), I18n.t("messages.print_fail_msg", error=str(e)))

    def _execute_print(self, print_items:list)->None:
        """
        执行直接打印流程(弹出系统打印对话框 → 打印)

        参数:
            print_items: List[(images, annotations, label)] 已收集的打印数据
        """
        # 创建打印机配置
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        printer.setFullPage(True)

        # 弹出系统打印对话框
        print_dlg = QPrintDialog(printer, self)
        print_dlg.setWindowTitle(I18n.t("print_dialog.window_title"))
        if print_dlg.exec_() != QDialog.Accepted:
            return

        # 执行打印
        total_pages = 0
        for imgs, anns, label in print_items:
            if not imgs:
                continue
            n = self._render_to_printer(printer, imgs, anns)
            total_pages += n

        QMessageBox.information(
            self, I18n.t("messages.print_success"),
            I18n.t("messages.print_success_msg", count=total_pages)
        )

    def _show_print_preview(self, print_items:list)->None:
        """
        显示打印预览窗口

        功能:
          - 使用QPrintPreviewDialog显示谱面在纸上的实际效果
          - 用户可在预览窗口中缩放、翻页、调整打印参数
          - 点击预览窗口中的"打印"按钮直接发送到打印机

        原理:
          1. 创建QPrintPreviewDialog并连接paintRequested信号
          2. 信号触发时调用_render_to_printer()渲染当前页到预览画布
          3. 预览窗口内置缩放/翻页/打印功能，无需额外实现

        参数:
            print_items: List[(images, annotations, label)] 已收集的打印数据
        """
        # 创建打印机配置(用于预览和后续打印)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        printer.setFullPage(True)

        # 创建打印预览对话框
        preview_dlg = QPrintPreviewDialog(printer, self)
        preview_dlg.setWindowTitle(I18n.t("print_dialog.preview_title"))
        preview_dlg.setMinimumSize(820, 600)  # 最小尺寸确保预览效果良好(宽度+50px以完整显示打印图标)

        # 连接渲染信号: 当预览需要绘制页面时触发
        def on_paint_requested(printer_for_preview:QPrinter)->None:
            """打印预览回调: 将内容渲染到预览打印机"""
            for imgs, anns, label in print_items:
                if not imgs:
                    continue
                self._render_to_printer(printer_for_preview, imgs, anns)

        preview_dlg.paintRequested.connect(on_paint_requested)
        preview_dlg.exec_()

    def _render_to_printer(self, printer:QPrinter, images:list, annotations:list)->int:
        """
        渲染谱面到打印机(v1: 复用A4导出的缩放+预渲染逻辑)

        原理:
          1. 按A4宽度等比缩放所有图片(与PNG/PDF导出一致)
          2. 计算总高度和分页数
          3. 逐页使用预渲染方案绘制到printer(100%杜绝溢出)
          4. 在每页上绘制该页范围内的标注

        参数:
            printer:    QPrinter实例(已配置好纸张大小和边距)
            images:     要打印的QPixmap列表
            annotations: 标注列表(Annotation对象)

        返回: 打印的页数
        """
        # 获取打印机实际可打印区域
        printer_rect = printer.pageRect(QPrinter.DevicePixel)
        draw_w = int(printer_rect.width())  # 必须转int: QPixmap.scaled()不接受float参数
        draw_area_h = int(printer_rect.height()) - 35  # 预留35px给页码

        # 按A4宽度等比缩放所有图片(与导出一致)
        scaled_info = []; total_h = 0
        for img in images:
            if img.isNull(): continue
            ratio = draw_w / img.width() if img.width() > 0 else 1
            sh = int(img.height() * ratio)
            scaled_info.append((img.scaled(draw_w, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation), sh))
            total_h += sh
        if not scaled_info:
            raise ValueError("没有可打印的内容")

        # 计算分页数
        n_pages = max(1, (total_h + draw_area_h - 1) // draw_area_h)

        # 检测并跳过末尾空白/近空白页(与导出一致)
        if n_pages > 1:
            last_page_start = (n_pages - 1) * draw_area_h
            last_page_content = total_h - last_page_start
            if last_page_content < draw_area_h * 0.05:
                n_pages -= 1

        # 开始打印(每页一个newPage调用)
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        printed = 0
        for page_idx in range(n_pages):
            if page_idx > 0:
                printer.newPage()  # 分页(第1页不需要)

            ps = page_idx * draw_area_h; pe = ps + draw_area_h

            # === 预渲染到独立画布(与导出一致: 100%杜绝溢出) ===
            page_buffer = QImage(draw_w, draw_area_h, QImage.Format_ARGB32_Premultiplied)
            page_buffer.fill(QColor(255,255,255,255).rgba())  # 白色背景

            pb = QPainter(page_buffer)
            pb.setRenderHint(QPainter.Antialiasing); pb.setRenderHint(QPainter.SmoothPixmapTransform)

            ry = 0
            for scaled_img, sh in scaled_info:
                if ry + sh > ps and ry < pe:
                    src_top = max(0, ps - ry)
                    src_bottom = min(sh, pe - ry)
                    src_h = max(0, src_bottom - src_top)
                    if src_h > 0:
                        dst_y = (ry - ps) + src_top
                        pb.drawPixmap(
                            QRect(0, dst_y, draw_w, src_h),
                            scaled_img,
                            QRect(0, src_top, draw_w, src_h)
                        )
                ry += sh

            # 绘制标注(在page_buffer内，复用导出的标注绘制逻辑)
            orig_anns = self.annotations
            self.annotations = annotations
            self._draw_annotations_on_canvas(pb, 0, 0, draw_w, float(total_h), float(ps), float(pe),
                                               scale_ratio=draw_w / max(self.display_widget.width()-20, 1))
            self.annotations = orig_anns
            pb.end()

            # 将预渲染内容绘制到打印机
            painter.drawImage(0, 0, page_buffer)

            # 页码(底部居中)
            painter.setPen(QColor("#999999"))
            painter.setFont(QFont(get_font_family("numeric"), 9))
            painter.drawText(QRect(0, int(printer_rect.height()) - 35, draw_w, 35),
                           Qt.AlignCenter, f"- {page_idx+1}/{n_pages} -")
            printed += 1

        painter.end()
        return printed

    # ========== A4导出(PNG/PDF，含标注，支持分轨/分页) ==========

    def _export_to_a4(self)->None:
        """
        导出谱面(含标注)为A4尺寸的PNG/JPG或PDF (v3: 异步导出+进度条)
        
        功能:
          - 格式: PNG(无损图片) / JPG(有损压缩,适合分享) / PDF(矢量文档)
          - 分轨: GTP文件可选指定轨道导出，或"全部轨道"按顺序拼接
          - 分页: 可选单页、页数范围、全部页面
          - 标注: 完整渲染所有标注(颜色/字体/大小)
          - 异步: 后台线程渲染，UI不冻结，显示进度条，支持取消

        原理 (v3异步架构):
          1. 弹出ExportDialog让用户选择格式(JPG含质量滑块)/轨道/页码范围
          2. 创建ExportWorker(QRunnable) + ExportProgressDialog
          3. 将Worker提交到QThreadPool全局线程池后台运行
          4. Worker通过信号报告进度→ProgressDialog更新进度条
          5. 用户可随时点击取消按钮中断导出
          6. 完成/出错/取消后自动关闭进度对话框并提示结果

        对比旧版(v2同步):
          - 旧版: UI主线程直接调用渲染方法 → 大文件时界面冻结5-10秒
          - 新版: 后台线程渲染 → UI保持响应，实时显示进度
        """
        if not self.images or all(img.isNull() for img in self.images):
            QMessageBox.warning(self, I18n.t("messages.export_no_content"), I18n.t("messages.export_no_content_msg"))
            return

        # 弹出导出对话框(含JPG质量选项)
        dlg = ExportDialog(
            parent=self,
            src_name=os.path.basename(self.file_path) if isinstance(self.file_path, str) else I18n.t("app.score_name"),
            is_gtp=bool(self.gtp_player and self.gtp_player.is_loaded),
            gtp_track_count=self.gtp_track_combo.count() if self.gtp_track_combo else 0,
            current_track=self.gtp_player.current_track if self.gtp_player else 0,
            total_pages=len([i for i in self.images if not i.isNull()])
        )
        if dlg.exec_() != QDialog.Accepted:
            return

        # 获取用户选择
        fmt = dlg.format_choice           # "png" | "jpg" | "pdf"
        track_mode = dlg.track_mode       # "current" | "all" | list[int]
        page_mode = dlg.page_mode         # "all" | ("range", start, end)
        save_path = dlg.save_path
        jpg_quality = dlg.jpg_quality     # JPG质量(1-100)

        # === 计算总轨道数(用于进度条) ===
        total_tracks = 1
        if track_mode == "all" and self.gtp_track_combo:
            total_tracks = self.gtp_track_combo.count()
        elif isinstance(track_mode, list):
            total_tracks = len(track_mode)

        # === 创建异步工作线程和进度对话框 ===
        worker = ExportWorker(self, fmt, track_mode, page_mode, save_path, jpg_quality)
        progress_dlg = ExportProgressDialog(parent=self, total_tracks=total_tracks)
        progress_dlg.set_worker(worker)

        # 提交到全局线程池后台执行
        QThreadPool.globalInstance().start(worker)

        # 显示进度对话框(模态，但不阻塞后台线程)
        progress_dlg.exec_()

    def _collect_export_data(self, track_mode, page_mode)->list:
        """
        收集导出数据: 根据用户选择的轨道模式和页码模式，收集图片列表和标注
        
        参数:
            track_mode: "current"(当前轨) | "all"(全部轨) | [int,...](指定轨道索引列表)
            page_mode: "all"(全部页) | ("range", start, end)(页码范围,1-based)
        
        返回:
            List[(images:List[QPixmap], annotations:List[Annotation], label:str), ...]
        """
        items = []

        if track_mode == "current":
            # v2.0修复: GTP文件导出当前轨时，必须强制用浅色主题重新渲染
            # 原因: self.images 可能是深色主题的缓存图像，直接导出会导致深色谱面
            if self.gtp_player and self.gtp_player.is_loaded:
                from ApolloTab.renderer import TabRenderer
                renderer = TabRenderer()
                try:
                    renderer.set_theme('light')  # 强制浅色主题
                except Exception:
                    pass
                try:
                    pixmaps = renderer.render_from_file(
                        self.gtp_player.file_path,
                        track_index=self.gtp_player.current_track
                    )
                    imgs = [p for p in pixmaps if not p.isNull()]
                    if page_mode[0] == "range":
                        imgs = imgs[page_mode[1]-1:page_mode[2]]
                except Exception as e:
                    print(f"警告: 导出当前轨重渲染失败({e})，回退到缓存图像")
                    imgs, anns, label = self._get_page_range_images(page_mode)
                    items.append((imgs, anns, ""))
                    return items  # 回退后直接返回，不再执行下方代码
                anns = self._load_track_annotations(self.gtp_player.current_track)
                items.append((imgs, anns, ""))
            else:
                # 非GTP文件(图片/PDF): 直接使用缓存图像(无主题问题)
                imgs, anns, label = self._get_page_range_images(page_mode)
                items.append((imgs, anns, ""))

        elif track_mode == "all" and self.gtp_player and self.gtp_player.is_loaded:
            from ApolloTab.renderer import TabRenderer
            renderer = TabRenderer()
            # v2.0新增: 导出时强制使用浅色主题(无论当前UI主题是什么)
            try:
                renderer.set_theme('light')
            except Exception:
                pass
            for t_idx in range(self.gtp_track_combo.count()):
                try:
                    pixmaps = renderer.render_from_file(self.gtp_player.file_path, track_index=t_idx)
                    valid_pixmaps = [p for p in pixmaps if not p.isNull()]
                    if page_mode[0] == "range":
                        valid_pixmaps = valid_pixmaps[page_mode[1]-1:page_mode[2]]
                    track_anns = self._load_track_annotations(t_idx)
                    tname = self.gtp_track_combo.itemText(t_idx).replace(' ', '_')[:20]
                    items.append((valid_pixmaps, track_anns, f"t{t_idx+1}_{tname}"))
                except Exception as e:
                    print(f"警告: 渲染轨道{t_idx}失败: {e}")

        elif isinstance(track_mode, list):
            from ApolloTab.renderer import TabRenderer
            renderer = TabRenderer()
            # v2.0新增: 导出时强制使用浅色主题(无论当前UI主题是什么)
            try:
                renderer.set_theme('light')
            except Exception:
                pass
            for t_idx in track_mode:
                try:
                    pixmaps = renderer.render_from_file(self.gtp_player.file_path, track_index=t_idx)
                    valid_pixmaps = [p for p in pixmaps if not p.isNull()]
                    if page_mode[0] == "range":
                        valid_pixmaps = valid_pixmaps[page_mode[1]-1:page_mode[2]]
                    track_anns = self._load_track_annotations(t_idx)
                    items.append((valid_pixmaps, track_anns, f"t{t_idx+1}"))
                except Exception as e:
                    print(f"警告: 渲染轨道{t_idx}失败: {e}")
        else:
            imgs, anns, label = self._get_page_range_images(page_mode)
            items.append((imgs, anns, ""))
        return items

    def _get_page_range_images(self, page_mode)->tuple:
        """根据页码模式获取当前显示的图片子集"""
        valid_imgs = [img for img in self.images if not img.isNull()]
        if page_mode[0] == "range":
            valid_imgs = valid_imgs[page_mode[1]-1:page_mode[2]]
        return (valid_imgs, self.annotations.copy(), "")

    def _load_track_annotations(self, track_idx:int)->list:
        """加载指定轨道的标注(从文件或内存缓存)"""
        if track_idx in self._annotations_by_track and self._annotations_by_track[track_idx]:
            return [Annotation(**asdict(a)) for a in self._annotations_by_track[track_idx]]
        if self.gtp_player:
            old_track = self.gtp_player.current_track
            self.gtp_player.current_track = track_idx
            fpath = self._get_annotation_file_path()
            self.gtp_player.current_track = old_track
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Annotation(**d) for d in data]
            except Exception:
                pass
        return []

    def _get_a4_size_px(self, dpi:int=300)->tuple:
        """
        获取A4纸的像素尺寸
        参数: dpi(默认300印刷级，调大更清晰文件更大)
        返回: (宽度px, 高度px)
        """
        mm_to_inch = 25.4
        w_px = int(210 / mm_to_inch * dpi)
        h_px = int(297 / mm_to_inch * dpi)
        return w_px, h_px

    def _render_to_a4_png_v2(self, file_path:str, images:list, annotations:list, dpi:int=300)->int:
        """
        渲染为PNG(v6: 按A4宽度等比缩放 + 预渲染防溢出)

        设计说明:
          - 将渲染器输出的图片按A4宽度等比缩放，谱面占满整个A4宽度
          - 使用"预渲染+合成"方案: page_buffer(固定高度) → A4画布，物理隔离杜绝溢出
          - 无边距、无间距
        返回: 生成的文件数
        """
        a4_w, a4_h = self._get_a4_size_px(dpi)
        draw_w = a4_w  # 谱面占满A4宽度

        # 按A4宽度等比缩放所有图片(最大化利用空间)
        scaled_info = []; total_h = 0
        for img in images:
            if img.isNull(): continue
            ratio = draw_w / img.width() if img.width() > 0 else 1
            sh = int(img.height() * ratio)
            scaled_info.append((img.scaled(draw_w, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation), sh))
            total_h += sh
        if not scaled_info:
            raise ValueError("没有可渲染的内容")

        draw_area_h = a4_h - 25  # 每页可用高度(仅预留25px给页码)
        n_pages = max(1, (total_h + draw_area_h - 1) // draw_area_h)

        # === 检测并跳过末尾空白/近空白页 ===
        # 原理: 内容刚好跨页边界时(如total_h=3483 > draw_area_h=3482)，
        #       尾页只有几像素内容，视觉上等同空白页，应跳过。
        #       阈值5%: 尾页内容不足页面高度的5%时视为空白(约174px@300dpi)
        if n_pages > 1:
            last_page_start = (n_pages - 1) * draw_area_h
            last_page_content = total_h - last_page_start
            if last_page_content < draw_area_h * 0.05:
                n_pages -= 1  # 跳过近空白尾页(少量溢出被page_buffer裁剪吸收)

        saved = 0

        for page_idx in range(n_pages):
            ps = page_idx * draw_area_h; pe = ps + draw_area_h

            # === 方案: 预渲染到独立画布再合成到A4(100%杜绝溢出) ===
            # 原理: ClipRect方式在某些Qt版本/渲染路径下不可靠(已验证多次失败)。
            #       改用"预渲染+合成"方案:
            #       1. 创建一个固定高度=draw_area_h的独立画布(page_buffer)
            #       2. 将本页所有内容绘制到page_buffer(物理上不可能超出draw_area_h)
            #       3. 将page_buffer一次性blit到A4画布上
            #       → 即使page_buffer有溢出，也只影响page_buffer本身，不会污染A4画布
            page_buffer = QImage(draw_w, draw_area_h, QImage.Format_ARGB32_Premultiplied)
            page_buffer.fill(QColor(255,255,255,255).rgba())  # 白色背景

            pb = QPainter(page_buffer)
            pb.setRenderHint(QPainter.Antialiasing); pb.setRenderHint(QPainter.SmoothPixmapTransform)

            ry = 0
            for scaled_img, sh in scaled_info:
                if ry + sh > ps and ry < pe:
                    src_top = max(0, ps - ry)
                    src_bottom = min(sh, pe - ry)
                    src_h = max(0, src_bottom - src_top)
                    if src_h > 0:
                        dst_y = (ry - ps) + src_top
                        pb.drawPixmap(
                            QRect(0, dst_y, draw_w, src_h),
                            scaled_img,
                            QRect(0, src_top, draw_w, src_h)
                        )
                ry += sh

            # === 绘制标注(在page_buffer内) ===
            orig_anns = self.annotations
            self.annotations = annotations
            self._draw_annotations_on_canvas(pb, 0, 0, draw_w, float(total_h), float(ps), float(pe),
                                               scale_ratio=draw_w / max(self.display_widget.width()-20, 1))
            self.annotations = orig_anns
            pb.end()  # 关闭page_buffer的painter

            # === 合成: A4画布 ← page_buffer(预渲染内容) + 页码 ===
            canvas = QImage(a4_w, a4_h, QImage.Format_ARGB32_Premultiplied)
            canvas.fill(QColor(255,255,255,255).rgba())  # 白色A4背景

            p = QPainter(canvas)
            p.drawPixmap(0, 0, QPixmap.fromImage(page_buffer))  # 预渲染内容(QImage→QPixmap转换)

            # 页码(A4底部固定位置)
            p.setPen(QColor("#999999")); p.setFont(QFont(get_font_family("numeric"),9))
            p.drawText(QRect(0, a4_h - 25, draw_w, 25), Qt.AlignCenter, f"- {page_idx+1}/{n_pages} -")
            p.end()

            path = file_path if n_pages == 1 else f"{os.path.splitext(file_path)[0]}_p{page_idx+1}{os.path.splitext(file_path)[1]}"
            if not canvas.save(path, "PNG"):
                raise IOError(f"PNG保存失败: {path}")
            saved += 1
        return saved

    def _render_to_a4_jpg(self, file_path:str, images:list, annotations:list,
                          quality:int=90, dpi:int=300)->int:
        """
        渲染为JPG格式(v1: 基于PNG渲染逻辑，增加质量参数)

        功能:
          - 与PNG导出完全一致的渲染流程(缩放/分页/标注/页码)
          - 输出格式为JPG(有损压缩)，文件体积远小于PNG
          - 可调压缩质量(1-100)，平衡画质与文件大小

        参数:
            file_path:   保存路径(如 "output.jpg")
            images:      QPixmap图片列表(每页一张)
            annotations: 标注列表(Annotation对象)
            quality:     JPG压缩质量(1-100), 默认90(高质量)
                        调整效果: 越大文件越大但画质越好
                        推荐: 90=高质量接近无损 / 80=网络分享 / 60=极致压缩
            dpi:        分辨率(默认300印刷级)

        返回:
            生成的文件数(int)

        原理:
          1. 复用_render_to_a4_png_v2的完整渲染逻辑(QImage画布+预渲染防溢出)
          2. 最后保存时改用QImage.save(path, "JPEG", quality=quality)输出JPG
          3. Qt的JPG质量范围是0-99(-1表示默认)，内部自动映射用户输入1-100→0-99

        适用场景:
          - 网络分享(微信/QQ/论坛): 质量80，文件小加载快
          - 电子文档存档: 质量90，接近无损但比PNG小3-5倍
          - 极限压缩(邮件附件): 质量60，可接受画质损失换最小体积
        """
        a4_w, a4_h = self._get_a4_size_px(dpi)
        draw_w = a4_w  # 谱面占满A4宽度(与PNG一致)

        # 按A4宽度等比缩放所有图片(与PNG导出一致)
        scaled_info = []; total_h = 0
        for img in images:
            if img.isNull(): continue
            ratio = draw_w / img.width() if img.width() > 0 else 1
            sh = int(img.height() * ratio)
            scaled_info.append((img.scaled(draw_w, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation), sh))
            total_h += sh
        if not scaled_info:
            raise ValueError("没有可渲染的内容")

        draw_area_h = a4_h - 25  # 每页可用高度(仅预留25px给页码)
        n_pages = max(1, (total_h + draw_area_h - 1) // draw_area_h)

        # === 检测并跳过末尾空白/近空白页(与PNG导出一致) ===
        if n_pages > 1:
            last_page_start = (n_pages - 1) * draw_area_h
            last_page_content = total_h - last_page_start
            if last_page_content < draw_area_h * 0.05:
                n_pages -= 1

        # Qt JPG质量映射: 用户输入1-100 → Qt的0-99 (-1=默认)
        qt_quality = max(0, min(99, quality - 1))  # 映射到Qt范围

        saved = 0
        for page_idx in range(n_pages):
            ps = page_idx * draw_area_h; pe = ps + draw_area_h

            # === 预渲染到独立画布(与PNG导出一致: 100%杜绝溢出) ===
            page_buffer = QImage(draw_w, draw_area_h, QImage.Format_ARGB32_Premultiplied)
            page_buffer.fill(QColor(255,255,255,255).rgba())  # 白色背景(JPG不支持透明)

            pb = QPainter(page_buffer)
            pb.setRenderHint(QPainter.Antialiasing); pb.setRenderHint(QPainter.SmoothPixmapTransform)

            ry = 0
            for scaled_img, sh in scaled_info:
                if ry + sh > ps and ry < pe:
                    src_top = max(0, ps - ry)
                    src_bottom = min(sh, pe - ry)
                    src_h = max(0, src_bottom - src_top)
                    if src_h > 0:
                        dst_y = (ry - ps) + src_top
                        pb.drawPixmap(
                            QRect(0, dst_y, draw_w, src_h),
                            scaled_img,
                            QRect(0, src_top, draw_w, src_h)
                        )
                ry += sh

            # 绘制标注(在page_buffer内)
            orig_anns = self.annotations
            self.annotations = annotations
            self._draw_annotations_on_canvas(pb, 0, 0, draw_w, float(total_h), float(ps), float(pe),
                                               scale_ratio=draw_w / max(self.display_widget.width()-20, 1))
            self.annotations = orig_anns
            pb.end()

            # === 合成到A4画布 ===
            canvas = QImage(a4_w, a4_h, QImage.Format_RGB32)  # JPG用RGB32(无alpha通道，更小)
            canvas.fill(QColor(255,255,255).rgb())           # 纯白背景

            p = QPainter(canvas)
            p.drawPixmap(0, 0, QPixmap.fromImage(page_buffer))

            # 页码(A4底部固定位置)
            p.setPen(QColor("#666666")); p.setFont(QFont(get_font_family("numeric"),9))
            p.drawText(QRect(0, a4_h - 25, draw_w, 25), Qt.AlignCenter, f"- {page_idx+1}/{n_pages} -")
            p.end()

            # === 保存为JPG格式(带质量参数) ===
            path = file_path if n_pages == 1 else f"{os.path.splitext(file_path)[0]}_p{page_idx+1}{os.path.splitext(file_path)[1]}"
            if not canvas.save(path, "JPEG", qt_quality):
                raise IOError(f"JPG保存失败: {path}")
            saved += 1
        return saved

    def _render_to_a4_pdf_v2(self, file_path:str, images:list, annotations:list, dpi:int=300)->None:
        """
        渲染为PDF(v6: 按A4宽度等比缩放 + 预渲染防溢出)

        设计说明: 与PNG导出一致，按A4宽度等比缩放 + 预渲染防溢出
        """
        import io
        a4_w, a4_h = self._get_a4_size_px(dpi)
        draw_w = a4_w  # 谱面占满A4宽度(与PNG一致)

        # 按A4宽度等比缩放所有图片(与PNG导出一致)
        scaled_info = []; total_h = 0
        for img in images:
            if img.isNull(): continue
            ratio = draw_w / img.width() if img.width() > 0 else 1
            sh = int(img.height() * ratio)
            scaled_info.append((img.scaled(draw_w, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation), sh))
            total_h += sh
        if not scaled_info:
            raise ValueError("没有可渲染的内容")

        draw_area_h = a4_h - 25
        n_pages = max(1, (total_h + draw_area_h - 1) // draw_area_h)

        # === 检测并跳过末尾空白/近空白页(与PNG导出一致) ===
        if n_pages > 1:
            last_page_start = (n_pages - 1) * draw_area_h
            last_page_content = total_h - last_page_start
            if last_page_content < draw_area_h * 0.05:
                n_pages -= 1

        # 用PyMuPDF创建PDF
        pdf_doc = fitz.open()
        a4_pt_w, a4_pt_h = 595.28, 841.89
        px_to_pt = a4_pt_w / a4_w  # 像素→点数转换比

        for page_idx in range(n_pages):
            ps = page_idx * draw_area_h; pe = ps + draw_area_h

            # === 预渲染到独立画布(与PNG导出一致: 100%杜绝溢出) ===
            page_buffer = QImage(draw_w, draw_area_h, QImage.Format_ARGB32_Premultiplied)
            page_buffer.fill(QColor(255,255,255,255).rgba())

            pb = QPainter(page_buffer)
            pb.setRenderHint(QPainter.Antialiasing); pb.setRenderHint(QPainter.SmoothPixmapTransform)

            ry = 0
            for scaled_img, sh in scaled_info:
                if ry + sh > ps and ry < pe:
                    src_top = max(0, ps - ry)
                    src_bottom = min(sh, pe - ry)
                    src_h = max(0, src_bottom - src_top)
                    if src_h > 0:
                        dst_y = (ry - ps) + src_top
                        pb.drawPixmap(
                            QRect(0, dst_y, draw_w, src_h),
                            scaled_img,
                            QRect(0, src_top, draw_w, src_h)
                        )
                ry += sh

            # 绘制标注
            orig_anns = self.annotations
            self.annotations = annotations
            self._draw_annotations_on_canvas(pb, 0, 0, draw_w, float(total_h), float(ps), float(pe),
                                               scale_ratio=draw_w / max(self.display_widget.width()-20, 1))
            self.annotations = orig_anns
            pb.end()

            # === 合成到A4画布 ===
            canvas = QImage(a4_w, a4_h, QImage.Format_ARGB32_Premultiplied)
            canvas.fill(QColor(255,255,255,255).rgba())
            p = QPainter(canvas)
            p.drawPixmap(0, 0, QPixmap.fromImage(page_buffer))  # 预渲染内容(QImage→QPixmap转换)

            # 页码
            p.setPen(QColor("#999999")); p.setFont(QFont(get_font_family("numeric"),9))
            p.drawText(QRect(0, a4_h - 25, draw_w, 25), Qt.AlignCenter, f"- {page_idx+1}/{n_pages} -")
            p.end()

            # === 将QImage转为PDF页面(固定A4尺寸) ===
            buf = QBuffer()
            buf.open(QBuffer.WriteOnly)
            canvas.save(buf, "PNG")
            png_bytes = bytes(buf.data())  # QByteArray → Python bytes(PyMuPDF需要)
            buf.close()

            page_pt_w = a4_pt_w
            page_pt_h = a4_pt_h  # 固定A4尺寸(与画布一致)
            page = pdf_doc.new_page(width=page_pt_w, height=page_pt_h)
            rect = fitz.Rect(0, 0, page_pt_w, page_pt_h)
            page.insert_image(rect, stream=png_bytes)

        pdf_doc.save(file_path)
        pdf_doc.close()

    def _draw_annotations_on_canvas(self, painter:QPainter,
                                     offset_x:int, offset_y:int,
                                     draw_w:int, total_h:float,
                                     page_start:float, page_end:float,
                                     scale_ratio:float=1.0)->None:
        """
        在导出画布上绘制标注层(供PNG/PDF导出使用)
        
        原理: 将标注从相对坐标(0-1)映射到绝对像素坐标，
              只绘制落在当前页范围内的标注。
        
        参数:
            painter:      QPainter实例(已在目标画布上初始化)
            offset_x:     画布左边距(px)
            offset_y:     画布上边距(px)
            draw_w:       画布绘图区域宽度(px)
            total_h:      总内容高度(px，用于计算相对坐标对应的绝对位置)
            page_start:   当前页在总内容中的起始Y位置
            page_end:     当前页在总内容中的结束Y位置
            scale_ratio:  坐标缩放比(显示宽度/导出宽度)
        """
        if not self.annotations:
            return
        
        for ann in self.annotations:
            # 相对坐标 → 总内容中的绝对位置
            abs_x = offset_x + draw_w * ann.x
            abs_y = offset_y + total_h * ann.y
            
            # 只绘制在当前页范围内的标注
            ann_top = abs_y - ann.font_size
            ann_bottom = abs_y + 8
            if ann_bottom < page_start or ann_top > page_end:
                continue  # 不在当前页，跳过
            
            # 设置字体
            font = QFont(ann.font_family, int(ann.font_size * scale_ratio))
            font.setBold(ann.is_bold)
            painter.setFont(font)
            
            # 绘制背景(如果有且带透明度)
            if ann.background_color and ann.background_color != "#00000000":
                bg_color = QColor(ann.background_color)
                text_bbox = painter.fontMetrics().boundingRect(
                    QRect(int(abs_x), int(abs_y), 1000, 100),
                    Qt.AlignLeft | Qt.TextSingleLine, ann.text
                )
                painter.setPen(Qt.NoPen)
                painter.setBrush(bg_color)
                painter.drawRect(
                    int(abs_x - 2), int(abs_y - text_bbox.height()),
                    text_bbox.width() + 4, text_bbox.height() + 4
                )
            
            # 绘制文字
            painter.setPen(QColor(ann.color))
            painter.drawText(int(abs_x), int(abs_y), ann.text)


    # ========== 速度曲线 ==========

    def _open_speed_curve_editor(self)->None:
        """打开速度曲线编辑器"""
        dlg=SpeedCurveEditor(parent=self,current_curve=self.speed_curve)
        dlg.curveUpdated.connect(self._on_curve_updated)
        dlg.exec_()

    def _on_curve_updated(self,config:SpeedCurveConfig)->None:
        """速度曲线更新回调 - 刷新曲线配置+状态标签+总时长显示"""
        self.speed_curve=config
        status=f"已启用({len(config.points)}个控制点)" if config.is_enabled else "未启用"
        self.curve_status_label.setText(f"速度曲线: {status}")
        # 曲线变化后重新计算并更新总时长(右侧时间标签)
        if self.total_scroll_distance > 0:
            effective_speed = self._get_curve_average_speed() if (
                config.is_enabled and len(config.points) >= 2
            ) else self.base_speed
            secs = int(effective_speed * self.TIME_SCALE)
            self.time_end_label.setText(f"{secs//60:02d}:{secs%60:02d}")

    # ========== 全屏模式(v2.1.0新增) ==========

    def toggle_fullscreen(self)->None:
        """
        切换全屏/窗口模式

        原理: 检查当前is_fullscreen状态，调用对应的进入/退出方法
        调用方式: 工具栏按钮点击 / F11快捷键
        """
        if self.is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self)->None:
        """
        进入全屏模式

        执行步骤:
          1. 保存当前窗口几何信息(位置+大小)到_saved_geometry
          2. 设置is_fullscreen标志为True
          3. 调用Qt的showFullScreen()API使窗口填满屏幕
          4. 更新工具栏按钮图标和提示文字

        技术说明:
          - saveGeometry()返回QByteArray，包含窗口位置、大小、状态
          - showFullScreen()自动隐藏窗口标题栏和边框
          - 全屏后谱面画布自动扩展填充整个屏幕空间
        """
        self._saved_geometry=self.saveGeometry()
        print(f"[Fullscreen] 已保存窗口几何信息，准备进入全屏模式")
        self.is_fullscreen=True
        self.showFullScreen()
        self._update_fullscreen_button()
        print(f"[Fullscreen] ✓ 已进入全屏模式")

    def exit_fullscreen(self)->None:
        """
        退出全屏模式，恢复之前的窗口状态

        执行步骤:
          1. 设置is_fullscreen标志为False
          2. 调用showNormal()恢复正常窗口显示
          3. 如有保存的几何信息则恢复窗口位置和大小
          4. 更新工具栏按钮图标和提示文字

        边界情况处理:
          - _saved_geometry为None时使用默认大小1100x850
        """
        self.is_fullscreen=False
        self.showNormal()
        if self._saved_geometry is not None:
            self.restoreGeometry(self._saved_geometry)
            print(f"[Fullscreen] 已恢复窗口几何信息")
        else:
            self.setGeometry(150,80,1100,850)
            print(f"[Fullscreen] ⚠ 无保存的几何信息，使用默认大小")
        self._update_fullscreen_button()
        print(f"[Fullscreen] ✓ 已退出全屏模式")

    def _update_fullscreen_button(self)->None:
        """
        更新全屏按钮的图标和提示文字

        原理: 根据is_fullscreen状态切换按钮视觉反馈
          - 非全屏: 显示"展开"图标 + "进入全屏"提示
          - 全屏模式: 显示"收缩"图标 + "退出全屏"提示
        """
        if not hasattr(self,'fullscreen_btn'):
            return  # 按钮尚未创建时跳过
        if self.is_fullscreen:
            self.fullscreen_btn.setIcon(QIcon('icons/exit-fullscreen.svg'))
            self.fullscreen_btn.setToolTip(I18n.t("toolbar.exit_fullscreen_tooltip"))
        else:
            self.fullscreen_btn.setIcon(QIcon('icons/fullscreen.svg'))
            self.fullscreen_btn.setToolTip(I18n.t("toolbar.fullscreen_tooltip"))

    # ========== 键盘事件 ==========

    def keyPressEvent(self,event:QKeyEvent)->None:
        """键盘快捷键 - 含全局标注撤销/重做(Ctrl+Z / Ctrl+Y) + Ctrl+K创建标注"""
        try:
            # === 标注撤销/重做(优先于其他快捷键) ===
            if event.modifiers() & Qt.ControlModifier:
                if event.key() == Qt.Key_Z:       # Ctrl+Z: 撤销标注
                    self._anno_undo(); return
                elif event.key() == Qt.Key_Y:      # Ctrl+Y: 重做标注
                    self._anno_redo(); return
                elif event.key() == Qt.Key_K:      # Ctrl+K: 在鼠标位置创建标注
                    self._create_annotation_at_cursor()
                    return

            if event.key()==Qt.Key_Space:          # 空格: 播放/暂停
                self.toggle_playback()
            elif event.key()==Qt.Key_Up:           # 上箭头: 向上滚动
                self.current_position=max(0,self.current_position-30)
                self.display_widget.update();self.update_progress_display()
            elif event.key()==Qt.Key_Down:         # 下箭头: 向下滚动
                self.current_position=min(self.total_scroll_distance,self.current_position+30)
                self.display_widget.update();self.update_progress_display()
            elif event.key()==Qt.Key_Left:          # 左箭头: 减速
                self.speed_spin.setValue(max(350,self.speed_spin.value()-25))
            elif event.key()==Qt.Key_Right:         # 右箭头: 加速
                self.speed_spin.setValue(min(700,self.speed_spin.value()-25))
            elif event.key()==Qt.Key_F11:           # F11: 切换全屏模式(v2.1.0新增)
                self.toggle_fullscreen()
            elif event.key()==Qt.Key_Escape:        # ESC: 全屏时退出全屏，否则关闭窗口
                if self.is_fullscreen:
                    self.exit_fullscreen()  # v2.1.0修改: 全屏模式下ESC退出全屏而非关闭
                else:
                    self.close()             # 窗口模式保持原有行为: 关闭窗口
            super().keyPressEvent(event)
        except Exception:
            pass

    def showEvent(self,event:QShowEvent)->None:
        """窗口显示事件"""
        super().showEvent(event)
        self._calculate_total_distance()

    def resizeEvent(self,event:QResizeEvent)->None:
        """
        窗口大小改变事件

        功能:
          1. 重新计算总滚动距离(_calculate_total_distance)
          2. [v2.1.0修复] GTP模式: 宽度变化>50px时重建播放时间线
             (修复全屏滚动偏移bug: 全屏时显示宽度变化→缩放比例改变→
              timeline的scroll_y与实际渲染内容不匹配)

        阈值说明: 50px约等于拖动窗口边缘的常规变化量，
                  全屏切换通常变化几百px(如1080→1920)，远超此阈值
        """
        super().resizeEvent(event)
        self._calculate_total_distance()

        # [v2.1.0] GTP模式: 宽度变化时重建播放时间线
        if self.gtp_player and self.gtp_player.is_loaded and self.images and self._page_layouts:
            new_width = self.display_widget.width()
            old_width = getattr(self, '_last_timeline_build_width', 0)
            if old_width > 0 and abs(new_width - old_width) > 50:
                print(f"[ResizeEvent] 宽度变化 {old_width}→{new_width} (Δ={new_width-old_width}px)，重建GTP播放时间线")
                self._build_playhead_timeline()
            self._last_timeline_build_width = new_width


# ========== 导出设置对话框 ==========

class ExportDialog(QDialog):
    """
    导出设置对话框 - 选择格式/轨道/页码范围

    功能:
      - 格式: PNG(无损图片) / JPG(有损压缩,适合网络分享) / PDF(矢量文档)
      - JPG质量: 可调压缩质量(1-100), 默认90
      - 分轨: GTP文件可选指定轨道导出，或"全部轨道"按顺序拼接
      - 分页: 可选单页、页数范围、全部页面

    调整参数:
      - jpg_quality默认值: 90 (高质量), 改小可减小文件大小但降低画质
      - jpg_quality范围: 1-100, 对应Qt的0-99质量映射(内部自动-1)
    """

    def __init__(self, parent, src_name:str, is_gtp:bool,
                 gtp_track_count:int, current_track:int, total_pages:int):
        super().__init__(parent)
        self.src_name = src_name; self.is_gtp = is_gtp
        self.gtp_track_count = gtp_track_count; self.current_track = current_track
        self.total_pages = total_pages
        self.format_choice = "png"; self.track_mode = "current"
        self.page_mode = "all"; self.save_path = ""
        self.jpg_quality = 90  # JPG压缩质量(1-100), 默认90(高质量)
        self.setWindowTitle(I18n.t("export_dialog.window_title")); self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self)->None:
        lo = QVBoxLayout(self); lo.setSpacing(12)
        # === 格式选择 (PNG / JPG / PDF) ===
        fg = QGroupBox(I18n.t("export_dialog.format_group")); fl = QHBoxLayout(fg)
        self.fmt_png = QRadioButton(I18n.t("export_dialog.fmt_png"))
        self.fmt_jpg = QRadioButton(I18n.t("export_dialog.fmt_jpg"))
        self.fmt_pdf = QRadioButton(I18n.t("export_dialog.fmt_pdf"))
        self.fmt_png.setChecked(True)
        fl.addWidget(self.fmt_png); fl.addWidget(self.fmt_jpg); fl.addWidget(self.fmt_pdf)
        lo.addWidget(fg)

        # === JPG质量滑块 (仅JPG格式时显示) ===
        qg = QGroupBox(I18n.t("export_dialog.jpg_quality_label")); ql = QHBoxLayout(qg)
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)  # 质量1-100
        self.quality_slider.setValue(90)       # 默认90(高质量)
        self.quality_slider.setMinimumWidth(200)
        self.quality_label = QLabel("90")      # 显示当前质量值
        self.quality_label.setMinimumWidth(30)
        self.quality_slider.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        self.quality_slider.setToolTip(I18n.t("export_dialog.jpg_quality_tooltip"))
        ql.addWidget(self.quality_slider); ql.addWidget(self.quality_label)
        qg.setVisible(False)  # 默认隐藏，选JPG时显示
        self._quality_group = qg  # 保存引用以便切换显示
        lo.addWidget(qg)

        # 格式切换时联动显示/隐藏质量滑块
        self.fmt_jpg.toggled.connect(qg.setVisible)

        # 轨道(GTP多轨时显示)
        if self.is_gtp and self.gtp_track_count > 1:
            tg = QGroupBox(I18n.t("export_dialog.track_group", count=self.gtp_track_count)); tl = QVBoxLayout(tg)
            self.tk_cur = QRadioButton(I18n.t("export_dialog.track_current")); self.tk_all = QRadioButton(I18n.t("export_dialog.track_all"))
            self.tk_sel = QRadioButton(I18n.t("export_dialog.track_select"))
            self.tk_cur.setChecked(True); self.tk_sel.toggled.connect(lambda c: self._ck.setVisible(c))
            tl.addWidget(self.tk_cur); tl.addWidget(self.tk_all)
            sr = QHBoxLayout(); sr.addWidget(self.tk_sel)
            self._ck = QWidget(); cl = QHBoxLayout(self._ck); cl.setContentsMargins(0,0,0,0)
            self.tks = []
            for i in range(self.gtp_track_count):
                cb = QCheckBox(str(i+1)); cb.setChecked(i == self.current_track); self.tks.append(cb); cl.addWidget(cb)
            self._ck.setVisible(False); sr.addWidget(self._ck); sr.addStretch(); tl.addLayout(sr); lo.addWidget(tg)
        else:
            self.tk_all = None; self.tk_sel = None; self.tks = []; self.tk_cur = None
        # 页码
        pg = QGroupBox(I18n.t("export_dialog.page_group", total=self.total_pages)); pl = QVBoxLayout(pg)
        self.pg_all = QRadioButton(I18n.t("export_dialog.page_all")); self.pg_rng = QRadioButton(I18n.t("export_dialog.page_range"))
        self.pg_all.setChecked(True); self.pg_rng.toggled.connect(lambda c: self._pw.setVisible(c))
        pl.addWidget(self.pg_all)
        rl = QHBoxLayout(); rl.addWidget(self.pg_rng)
        self._ps = QSpinBox(); self._ps.setRange(1,max(1,self.total_pages)); self._ps.setValue(1)
        self._pe = QSpinBox(); self._pe.setRange(1,max(1,self.total_pages)); self._pe.setValue(self.total_pages)
        rl.addWidget(QLabel(I18n.t("export_dialog.page_from"))); rl.addWidget(self._ps); rl.addWidget(QLabel(I18n.t("export_dialog.page_to")))
        rl.addWidget(self._pe); rl.addWidget(QLabel(I18n.t("export_dialog.page_unit"))); rl.addStretch()
        self._pw = QWidget(); rw = QHBoxLayout(self._pw); rw.setContentsMargins(0,0,0,0); rw.addLayout(rl)
        self._pw.setVisible(False); pl.addWidget(self._pw); lo.addWidget(pg)
        # 按钮
        bb = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lo.addWidget(bb)

    def accept(self)->None:
        """确认时收集用户选择的格式/轨道模式/页码模式/JPG质量"""
        # 收集格式选择 (PNG / JPG / PDF)
        if self.fmt_pdf.isChecked():
            self.format_choice = "pdf"
        elif self.fmt_jpg.isChecked():
            self.format_choice = "jpg"
        else:
            self.format_choice = "png"

        # 收集JPG质量(仅JPG格式有效)
        self.jpg_quality = self.quality_slider.value()

        # 收集轨道选择
        if self.is_gtp and self.gtp_track_count > 1:
            if self.tk_all and self.tk_all.isChecked(): self.track_mode = "all"
            elif self.tk_sel and self.tk_sel.isChecked():
                self.track_mode = [i for i,c in enumerate(self.tks) if c.isChecked()]
                if not self.track_mode: QMessageBox.warning(self,"提示",I18n.t("messages.select_track_hint")); return
            else: self.track_mode = "current"
        else: self.track_mode = "current"

        # 收集页码范围
        if hasattr(self,'pg_rng') and self.pg_rng.isChecked():
            s,e = self._ps.value(), self._pe.value()
            if s > e: s,e = e,s
            self.page_mode = ("range", s, e)
        else: self.page_mode = "all"

        # 根据格式确定文件扩展名和过滤器
        ext_map = {"pdf": ".pdf", "png": ".png", "jpg": ".jpg"}
        filter_map = {
            "pdf": I18n.t('export_dialog.file_filter_pdf'),
            "png": I18n.t('export_dialog.file_filter_png'),
            "jpg": I18n.t('export_dialog.file_filter_jpg')
        }
        ext = ext_map[self.format_choice]
        fp,_ = QFileDialog.getSaveFileName(self,I18n.t("export_dialog.save_title"),f"{os.path.splitext(self.src_name)[0]}_annotated{ext}",
                                           f"{filter_map[self.format_choice]} (*{ext})")
        if not fp: return
        self.save_path = fp; super().accept()


# ========== 打印设置对话框 ==========

class PrintDialog(QDialog):
    """
    打印设置对话框 - 选择轨道/页码范围
    功能: GTP可选轨道; 可选页码范围; 确认后弹出系统打印对话框

    设计说明: 复用ExportDialog的UI布局和逻辑，仅移除格式选择部分
    """

    def __init__(self, parent, src_name:str, is_gtp:bool,
                 gtp_track_count:int, current_track:int, total_pages:int):
        super().__init__(parent)
        self.src_name = src_name; self.is_gtp = is_gtp
        self.gtp_track_count = gtp_track_count; self.current_track = current_track
        self.total_pages = total_pages
        self.track_mode = "current"
        self.page_mode = "all"
        self.setWindowTitle(I18n.t("print_dialog.window_title")); self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self)->None:
        lo = QVBoxLayout(self); lo.setSpacing(12)

        # 轨道(GTP多轨时显示) - 与导出对话框一致
        if self.is_gtp and self.gtp_track_count > 1:
            tg = QGroupBox(I18n.t("print_dialog.track_group", count=self.gtp_track_count)); tl = QVBoxLayout(tg)
            self.tk_cur = QRadioButton(I18n.t("print_dialog.track_current")); self.tk_all = QRadioButton(I18n.t("print_dialog.track_all"))
            self.tk_sel = QRadioButton(I18n.t("print_dialog.track_select"))
            self.tk_cur.setChecked(True); self.tk_sel.toggled.connect(lambda c: self._ck.setVisible(c))
            tl.addWidget(self.tk_cur); tl.addWidget(self.tk_all)
            sr = QHBoxLayout(); sr.addWidget(self.tk_sel)
            self._ck = QWidget(); cl = QHBoxLayout(self._ck); cl.setContentsMargins(0,0,0,0)
            self.tks = []
            for i in range(self.gtp_track_count):
                cb = QCheckBox(str(i+1)); cb.setChecked(i == self.current_track); self.tks.append(cb); cl.addWidget(cb)
            self._ck.setVisible(False); sr.addWidget(self._ck); sr.addStretch(); tl.addLayout(sr); lo.addWidget(tg)
        else:
            self.tk_all = None; self.tk_sel = None; self.tks = []; self.tk_cur = None

        # 页码范围 - 与导出对话框一致
        pg = QGroupBox(I18n.t("print_dialog.page_group", total=self.total_pages)); pl = QVBoxLayout(pg)
        self.pg_all = QRadioButton(I18n.t("print_dialog.page_all")); self.pg_rng = QRadioButton(I18n.t("print_dialog.page_range"))
        self.pg_all.setChecked(True); self.pg_rng.toggled.connect(lambda c: self._pw.setVisible(c))
        pl.addWidget(self.pg_all)
        rl = QHBoxLayout(); rl.addWidget(self.pg_rng)
        self._ps = QSpinBox(); self._ps.setRange(1,max(1,self.total_pages)); self._ps.setValue(1)
        self._pe = QSpinBox(); self._pe.setRange(1,max(1,self.total_pages)); self._pe.setValue(self.total_pages)
        rl.addWidget(QLabel(I18n.t("print_dialog.page_from")))
        rl.addWidget(self._ps)
        rl.addWidget(QLabel(I18n.t("print_dialog.page_to")))
        rl.addWidget(self._pe)
        rl.addWidget(QLabel(I18n.t("print_dialog.page_unit")))
        rl.addStretch()
        self._pw = QWidget(); rw = QHBoxLayout(self._pw); rw.setContentsMargins(0,0,0,0); rw.addLayout(rl)
        self._pw.setVisible(False); pl.addWidget(self._pw); lo.addWidget(pg)

        # 按钮
        bb = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lo.addWidget(bb)

    def accept(self)->None:
        """确认时收集用户选择的轨道模式和页码模式"""
        # 收集轨道选择
        if self.is_gtp and self.gtp_track_count > 1:
            if self.tk_all and self.tk_all.isChecked():
                self.track_mode = "all"
            elif self.tk_sel and self.tk_sel.isChecked():
                self.track_mode = [i for i,c in enumerate(self.tks) if c.isChecked()]
                if not self.track_mode:
                    QMessageBox.warning(self, "提示", I18n.t("messages.select_track_hint"))
                    return
            else:
                self.track_mode = "current"
        else:
            self.track_mode = "current"

        # 收集页码范围
        if hasattr(self,'pg_rng') and self.pg_rng.isChecked():
            s,e = self._ps.value(), self._pe.value()
            if s > e: s,e = e,s
            self.page_mode = ("range", s, e)
        else:
            self.page_mode = "all"

        super().accept()


# ============================================================
# 异步导出系统 - 后台线程 + 进度对话框
# ============================================================

# ============================================================
# 主题刷新工作线程（性能优化：P1-3）
# ============================================================
# 原理: GTP主题切换时需要重新渲染所有页面，此为CPU密集操作。
#       将渲染移至后台线程，完成后通过信号通知UI更新，避免主题切换时UI卡顿。

class ThemeRefreshSignals(QObject):
    """主题刷新线程信号"""
    finished = pyqtSignal(list)  # 携带渲染结果 (all_pixmaps)
    error = pyqtSignal(str)      # 错误信息


class ThemeRefreshWorker(QRunnable):
    """
    异步GTP主题刷新工作线程
    
    原理: 在后台线程中调用 GTPPlayer 重新渲染所有页面，
          完成后通过信号将结果通知主线程更新UI。
          
    使用方式:
      worker = ThemeRefreshWorker(gtp_player, theme_name)
      worker.signals.finished.connect(update_callback)
      QThreadPool.globalInstance().start(worker)
    """
    def __init__(self, gtp_player, theme_name: str):
        super().__init__()
        self.gtp_player = gtp_player
        self.theme_name = theme_name
        self.signals = ThemeRefreshSignals()
    
    def run(self) -> None:
        try:
            self.gtp_player.set_theme(self.theme_name)
            all_pixmaps = self.gtp_player.render_track(self.gtp_player.current_track)
            self.signals.finished.emit(all_pixmaps)
        except Exception as e:
            self.signals.error.emit(str(e))


class ExportWorkerSignals(QObject):
    """
    导出工作线程信号类

    信号说明:
      - progress: (current_track, total_tracks, current_page, total_pages) 渲染进度
      - finished: (total_files, save_path, fmt_name, mode_desc) 导出完成
      - error: (str,) 导出出错
      - cancelled: () 用户取消导出
    """
    progress = pyqtSignal(int, int, int, int)   # (当前轨道, 总轨道, 当前页, 总页)
    finished = pyqtSignal(int, str, str, str)   # (文件数, 路径, 格式名, 模式描述)
    error = pyqtSignal(str)                     # 错误信息
    cancelled = pyqtSignal()                    # 取消信号


class ExportWorker(QRunnable):
    """
    异步导出工作线程 - 在后台执行PNG/JPG/PDF渲染，避免UI冻结

    原理:
      1. 继承QRunnable，提交到QThreadPool全局线程池后台运行
      2. 通过ExportWorkerSignals信号向UI线程报告进度/结果/错误
      3. 支持用户通过cancelled标志随时取消导出(每页渲染前检查)
      4. 内部持有DisplayWindow引用，调用其渲染方法完成实际工作

    使用方式:
      worker = ExportWorker(window, fmt, track_mode, page_mode, save_path, jpg_quality)
      worker.signals.progress.connect(progress_callback)
      worker.signals.finished.connect(done_callback)
      QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, window: 'DisplayWindow', fmt: str, track_mode, page_mode,
                 save_path: str, jpg_quality: int = 90):
        super().__init__()
        self.window = window          # DisplayWindow实例(持有渲染方法)
        self.fmt = fmt                # "png" | "jpg" | "pdf"
        self.track_mode = track_mode  # "current" | "all" | list[int]
        self.page_mode = page_mode    # "all" | ("range", start, end)
        self.save_path = save_path    # 保存路径
        self.jpg_quality = jpg_quality # JPG质量(1-100)
        self.signals = ExportWorkerSignals()
        self._is_cancelled = False    # 取消标志(原子检查)

    def cancel(self)->None:
        """请求取消导出(由UI线程调用，下个渲染循环生效)"""
        self._is_cancelled = True

    def run(self)->None:
        """
        异步执行导出流程(在后台线程中运行)

        执行步骤:
          1. 发出"正在收集数据"的初始进度
          2. 调用window._collect_export_data()收集图片和标注
          3. 遍历每个轨道项:
             a. 检查是否已取消 → 是则发出cancelled信号并返回
             b. 根据格式调用对应渲染方法(_render_to_a4_png_v2 / _render_to_a4_jpg / _render_to_a4_pdf_v2)
             c. 每完成一页发出progress信号更新UI
          4. 全部完成后发出finished信号
          5. 任何异常发出error信号
        """
        try:
            # === Step 1: 收集导出数据 ===
            self.signals.progress.emit(0, 1, 0, 1)  # 初始状态: "正在收集数据..."

            export_items = self.window._collect_export_data(self.track_mode, self.page_mode)
            # export_items: List[(images_list, annotations_list, track_label), ...]

            if not export_items or not any(item[0] for item in export_items):
                self.signals.error.emit(I18n.t("messages.export_no_data"))
                return

            # === Step 2: 计算总工作量(用于进度显示) ===
            total_items = len(export_items)

            # === Step 3: 逐轨逐页渲染 ===
            total_files = 0
            for item_idx, (imgs, anns, label) in enumerate(export_items):
                # 检查取消
                if self._is_cancelled:
                    self.signals.cancelled.emit()
                    return

                if not imgs:
                    continue

                # 构建此轨/部分的保存路径
                if len(export_items) > 1 or label:
                    base, ext = os.path.splitext(self.save_path)
                    part_path = f"{base}_{label}{ext}"
                else:
                    part_path = self.save_path

                # 根据格式选择渲染方法
                if self.fmt == "pdf":
                    n = self.window._render_to_a4_pdf_v2(part_path, imgs, anns)
                    total_files += 1
                elif self.fmt == "jpg":
                    n = self.window._render_to_a4_jpg(part_path, imgs, anns, self.jpg_quality)
                    total_files += n
                else:  # png
                    n = self.window._render_to_a4_png_v2(part_path, imgs, anns)
                    total_files += n

                # 报告轨道级进度
                self.signals.progress.emit(item_idx + 1, total_items, 0, 0)

            # === Step 4: 完成 ===
            fmt_name = {"png": "PNG", "jpg": "JPG", "pdf": "PDF"}.get(self.fmt, "PNG")
            mode_desc = ""
            if self.track_mode == "all":
                mode_desc = I18n.t("messages.export_mode_all",
                    count=self.window.gtp_track_combo.count() if self.window.gtp_track_combo else 0)
            elif isinstance(self.track_mode, list):
                mode_desc = I18n.t("messages.export_mode_tracks",
                    tracks=', '.join(str(t+1) for t in self.track_mode))

            self.signals.finished.emit(total_files, self.save_path, fmt_name, mode_desc)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.signals.error.emit(str(e))


class ExportProgressDialog(QDialog):
    """
    导出进度对话框 - 显示异步导出的实时进度

    功能:
      - 显示当前渲染状态(收集数据 / 渲染轨道X/Y / 保存文件 / 完成)
      - 进度条可视化展示整体进度
      - 取消按钮可中断导出操作
      - 自动关闭: 完成或出错后1.5秒自动关闭(或用户手动关闭)

    UI布局:
      ┌─────────────────────────────────┐
      │  正在导出 - TAB Score Viewer     │
      ├─────────────────────────────────┤
      │  状态: 正在渲染: 轨道 2/4       │
      │         第 7/25 页              │
      │  ████████████░░░░░░  52%       │
      │           [取消]               │
      └─────────────────────────────────┘
    """

    def __init__(self, parent, total_tracks:int=1):
        super().__init__(parent)
        self.total_tracks = total_tracks
        self.setWindowTitle(I18n.t("export_progress.window_title"))
        self.setMinimumWidth(400)
        self.setFixedSize(420, 160)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self._worker = None          # ExportWorker引用(用于取消)
        self._setup_ui()

    def _setup_ui(self)->None:
        lo = QVBoxLayout(self); lo.setSpacing(10)

        # 状态标签
        self.status_label = QLabel(I18n.t("export_progress.status_collecting"))
        self.status_label.setStyleSheet("font-size:13px; color:#666;")
        lo.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total_tracks * 100)  # 轨道数*100作为最大值
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        lo.addWidget(self.progress_bar)

        # 取消按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton(I18n.t("export_progress.btn_cancel"))
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        lo.addLayout(btn_layout)

    def set_worker(self, worker: ExportWorker)->None:
        """绑定ExportWorker实例(用于取消操作)"""
        self._worker = worker
        # 连接信号
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.cancelled.connect(self._on_cancelled)

    def _on_progress(self, current_track:int, total_tracks:int,
                     current_page:int, total_pages:int)->None:
        """进度更新回调"""
        # 更新状态文字
        if current_track == 0:
            status = I18n.t("export_progress.status_collecting")
        elif total_pages > 0:
            status = I18n.t("export_progress.status_rendering", current=current_track,
                           total=total_tracks) + \
                    I18n.t("export_progress.status_page", page=current_page, pages=total_pages)
        else:
            status = I18n.t("export_progress.status_rendering", current=current_track,
                           total=total_tracks)
        self.status_label.setText(status)

        # 更新进度条 (轨道级粗粒度 + 页码细粒度)
        if total_tracks > 0 and total_pages > 0:
            # 每个轨道占 (100/total_tracks) 分，当前轨道内按页码细分
            per_track = 100 // max(total_tracks, 1)
            track_done = (current_track - 1) * per_track
            page_in_track = (per_track * current_page // max(total_pages, 1)) if current_page > 0 else 0
            self.progress_bar.setValue(track_done + page_in_track)
        elif total_tracks > 0:
            self.progress_bar.setValue(current_track * 100 // total_tracks)

    def _on_finished(self, total_files:int, save_path:str, fmt_name:str, mode_desc:str)->None:
        """导出完成回调"""
        self.status_label.setText(I18n.t("export_progress.status_done"))
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText(I18n.t("control_panel.ok_btn") if hasattr(I18n.t('control_panel'), 'ok_btn') else "确定")

        # 显示成功提示
        QMessageBox.information(
            self, I18n.t("messages.export_success"),
            I18n.t("messages.export_success_msg",
                  fmt=fmt_name, path=save_path, count=total_files, mode=mode_desc)
        )
        # 延迟自动关闭
        QTimer.singleShot(500, self.close)

    def _on_error(self, error_msg:str)->None:
        """导出出错回调"""
        self.status_label.setText(f"Error: {error_msg}")
        self.cancel_btn.setEnabled(False)
        QMessageBox.critical(self, I18n.t("messages.export_fail"),
                             I18n.t("messages.export_fail_msg", error=error_msg))
        QTimer.singleShot(500, self.close)

    def _on_cancelled(self)->None:
        """导出被用户取消"""
        self.status_label.setText(I18n.t("export_progress.status_cancelled"))
        self.cancel_btn.setEnabled(False)
        QTimer.singleShot(800, self.close)

    def _on_cancel(self)->None:
        """取消按钮点击处理"""
        if self._worker:
            self._worker.cancel()  # 请求取消
        self.status_label.setText(I18n.t("export_progress.status_cancelled"))
        self.cancel_btn.setEnabled(False)


# ============================================================
# 设置面板 (SettingsDialog) - v2.0.9 新增
# ============================================================

# GTP 渲染参数定义 (对应 ApolloTab.utils.constants.RenderConfig 第 359-390 行)
# 每个元组: (类属性名, 中文标签, 类型, 最小值, 最大值, 步长)
# 说明: 修改这些参数后需要重新打开 GTP 文件才能看到效果
_RENDER_PARAMS = [
    ("TAB_LINE_SPACING", "弦线间距 (px)", int, 1, 100, 1),
    ("TAB_LINE_WIDTH_PER_STRING", "每弦水平宽度 (px)", int, 5, 200, 1),
    ("TAB_LINE_THICKNESS", "弦线粗细 (px)", int, 1, 20, 1),
    ("NOTE_FONT_SIZE", "品格数字字号 (px)", int, 4, 64, 1),
    ("NOTE_MIN_SPACING", "相邻拍最小间距 (px)", int, 10, 300, 1),
    ("NOTE_EXTRA_WIDTH_PER_CHAR", "多位数字额外宽度 (px/字符)", int, 0, 50, 1),
    ("STEM_HEIGHT", "符干高度 (px)", int, 5, 120, 1),
    ("STEM_THICKNESS", "符干粗细 (px)", int, 1, 20, 1),
    ("BEAM_HEIGHT", "符尾横杠高度 (px)", int, 1, 60, 1),
    ("BEAM_SLOPE_MAX", "符尾最大斜率", float, 0.0, 2.0, 0.05),
    ("BARLINE_THICKNESS", "小节线粗细 (px)", float, 0.1, 10.0, 0.1),
    ("BARLINE_HEIGHT_EXTEND", "小节线延伸量 (px)", int, 0, 80, 1),
    ("MEASURE_PADDING_LEFT", "小节左侧内边距 (px)", int, 0, 100, 1),
    ("MEASURE_PADDING_RIGHT", "小节右侧内边距 (px)", int, 0, 100, 1),
    ("INFO_SECTION_HEIGHT", "顶部信息区高度 (px)", int, 10, 200, 1),
    ("INFO_FONT_SIZE", "信息文字大小 (px)", int, 4, 64, 1),
    ("TRACK_NAME_FONT_SIZE", "音轨名称字号 (px)", int, 4, 80, 1),
    ("LINE_SPACING", "行间距 (px)", int, 5, 300, 1),
    ("SYSTEM_SPACING", "系统间距 (px)", int, 0, 300, 1),
]

# 渲染参数默认值快照（用于"恢复默认"功能）
# 在模块加载时捕获 RenderConfig 类属性的初始值, 避免被运行时修改影响
_DEFAULT_RENDER_VALUES: Dict[str, Any] = {
    attr: getattr(RenderConfig, attr)
    for attr, _, _, _, _, _ in _RENDER_PARAMS
}
_DEFAULT_GTP_FONT: str = RenderConfig.NOTE_FONT_FAMILY  # "Arial"
_DEFAULT_LANGUAGE: str = "zh_CN"
_DEFAULT_THEME: str = "dark"


def apply_config_settings(cfg: dict) -> None:
    """
    从配置字典应用语言、主题、字体和 GTP 渲染参数

    参数:
        cfg: 从 config/settings.json 读取到的字典

    说明:
        兼容旧配置: 缺少新字段时使用 RenderConfig 默认值, 不报错
    """
    global _UI_FONT_FAMILY

    # 语言
    lang = cfg.get("language", "zh_CN")
    if lang != I18n.current_language():
        I18n.set_language(lang)

    # 主题
    theme = cfg.get("theme", "dark")
    if theme != ThemeManager.current_name():
        ThemeManager.set_theme(theme)

    # UI 字体
    ui_font = cfg.get("ui_font")
    _UI_FONT_FAMILY = ui_font if ui_font else None

    # GTP 渲染字体
    gtp_font = cfg.get("gtp_font")
    if gtp_font:
        RenderConfig.NOTE_FONT_FAMILY = gtp_font

    # GTP 渲染数值参数
    render_cfg = cfg.get("render_config", {})
    for attr, _, typ, *_ in _RENDER_PARAMS:
        if attr not in render_cfg:
            continue
        try:
            val = render_cfg[attr]
            if typ is int:
                val = int(val)
            elif typ is float:
                val = float(val)
            setattr(RenderConfig, attr, val)
        except Exception:
            pass


class SettingsDialog(QDialog):
    """
    设置对话框

    功能:
      - 集中管理应用常规设置(语言/主题/UI字体)
      - 集中管理 GTP 六线谱渲染参数(字体/线宽/间距等)
      - 支持实时预览主题与 UI 字体, 取消时恢复
      - 支持一键恢复所有设置为出厂默认值
      - 所有设置保存到 config/settings.json
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._parent_window = parent
        self.setWindowTitle(I18n.t("settings_dialog.window_title"))
        self.setWindowIcon(get_app_icon())
        self.resize(560, 520)

        # 记录原始值, 用于取消时恢复主题和 UI 字体预览
        self._original_theme = ThemeManager.current_name()
        self._original_ui_font = _UI_FONT_FAMILY

        # 渲染参数控件映射 {属性名: QSpinBox/QDoubleSpinBox}
        self._render_spinboxes: Dict[str, QSpinBox] = {}

        self._setup_ui()
        self._apply_theme()
        self._load_current_values()

    def _setup_ui(self) -> None:
        """初始化设置对话框 UI"""
        main_layout = QVBoxLayout(self)

        # 标签页容器
        self.tabs = QTabWidget()

        # 常规设置页
        self.general_tab = QWidget()
        general_layout = QFormLayout(self.general_tab)
        general_layout.setLabelAlignment(Qt.AlignRight)

        # 语言选择
        self.lang_combo = QComboBox()
        for code, name in I18n.available_languages():
            self.lang_combo.addItem(name, code)
        general_layout.addRow(I18n.t("settings_dialog.language_label"), self.lang_combo)

        # 主题选择
        self.theme_combo = QComboBox()
        for name, display_name in ThemeManager.available_themes():
            self.theme_combo.addItem(display_name, name)
        general_layout.addRow(I18n.t("settings_dialog.theme_label"), self.theme_combo)

        # UI 字体选择
        self.ui_font_combo = QFontComboBox()
        # 仅显示可缩放字体, 保证跨平台一致性
        self.ui_font_combo.setFontFilters(QFontComboBox.ScalableFonts)
        general_layout.addRow(I18n.t("settings_dialog.ui_font_label"), self.ui_font_combo)

        self.tabs.addTab(self.general_tab, I18n.t("settings_dialog.tab_general"))

        # GTP 渲染设置页
        self.gtp_tab = QWidget()
        gtp_layout = QFormLayout(self.gtp_tab)
        gtp_layout.setLabelAlignment(Qt.AlignRight)

        # GTP 渲染字体
        self.gtp_font_combo = QFontComboBox()
        self.gtp_font_combo.setFontFilters(QFontComboBox.ScalableFonts)
        gtp_layout.addRow(I18n.t("settings_dialog.gtp_font_label"), self.gtp_font_combo)

        # 渲染参数分组标签
        render_group = QLabel(I18n.t("settings_dialog.render_params_group"))
        render_group.setStyleSheet("font-weight:bold;margin-top:8px;")
        gtp_layout.addRow(render_group)

        # 渲染参数输入控件
        for attr, label, typ, min_val, max_val, step in _RENDER_PARAMS:
            if typ is int:
                spin = QSpinBox()
                spin.setRange(min_val, max_val)
                spin.setSingleStep(step)
            else:
                spin = QDoubleSpinBox()
                spin.setRange(min_val, max_val)
                spin.setSingleStep(step)
                spin.setDecimals(1 if step >= 0.1 else 2)
            spin.setMinimumWidth(90)
            # 中文 tooltip: 说明参数作用与调整效果
            spin.setToolTip(f"RenderConfig.{attr}: 当前参数控制 {label}。数值越大通常间距/字号越大, 越小越紧凑。")
            gtp_layout.addRow(label, spin)
            self._render_spinboxes[attr] = spin

        self.tabs.addTab(self.gtp_tab, I18n.t("settings_dialog.tab_gtp"))
        main_layout.addWidget(self.tabs)

        # 按钮: 确定 / 取消 / 恢复默认
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.reset_btn = self.button_box.addButton(
            I18n.t("settings_dialog.reset_btn"), QDialogButtonBox.ResetRole
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self._on_reject)
        self.button_box.clicked.connect(self._on_button_clicked)
        main_layout.addWidget(self.button_box)

        # 实时预览连接 (主题和 UI 字体)
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)
        self.ui_font_combo.currentFontChanged.connect(self._preview_ui_font)

    def _apply_theme(self) -> None:
        """
        应用当前主题样式到设置对话框
        
        性能优化(P0-1): 使用 _get_cached_qss() 缓存QSS字符串。
        """
        theme_name = ThemeManager.current_name()
        t = ThemeManager.current()
        qss = _get_cached_qss('SettingsDialog', theme_name, lambda: f"""
            QDialog{{background-color:{t['bg_primary']};color:{t['text_primary']};
                font-family:{get_font_family_css('ui')};}}
            QLabel{{color:{t['text_primary']};font-size:13px;}}
            QPushButton{{background-color:{t['primary']};color:white;border:none;
                border-radius:6px;padding:6px 14px;font-family:{get_font_family_css('ui')};}}
            QPushButton:hover{{background-color:{t['primary_hover']};}}
            QLineEdit,QComboBox,QFontComboBox,QSpinBox,QDoubleSpinBox{{
                background-color:{t['bg_surface']};color:{t['text_primary']};
                border:1px solid {t['border']};border-radius:4px;padding:4px 8px;}}
            QTabWidget::pane{{border:1px solid {t['border']};background-color:{t['bg_surface']};}}
            QTabBar::tab{{background-color:{t['bg_secondary']};color:{t['text_primary']};
                padding:6px 14px;margin:2px;border-radius:4px;}}
            QTabBar::tab:selected{{background-color:{t['primary']};color:white;}}
            QGroupBox{{color:{t['text_primary']};border:1px solid {t['border']};margin-top:8px;}}
        """)
        self.setStyleSheet(qss)

    def _load_current_values(self) -> None:
        """从当前配置和 RenderConfig 加载默认值到控件"""
        # 语言
        idx = self.lang_combo.findData(I18n.current_language())
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        # 主题
        idx = self.theme_combo.findData(ThemeManager.current_name())
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        # UI 字体
        ui_font = _UI_FONT_FAMILY or get_font_family('ui')
        idx = self.ui_font_combo.findText(ui_font)
        if idx >= 0:
            self.ui_font_combo.setCurrentIndex(idx)
        else:
            self.ui_font_combo.setCurrentText(ui_font)

        # GTP 渲染字体
        gtp_font = getattr(RenderConfig, "NOTE_FONT_FAMILY", "Arial")
        idx = self.gtp_font_combo.findText(gtp_font)
        if idx >= 0:
            self.gtp_font_combo.setCurrentIndex(idx)
        else:
            self.gtp_font_combo.setCurrentText(gtp_font)

        # 渲染参数
        for attr, spin in self._render_spinboxes.items():
            spin.setValue(getattr(RenderConfig, attr))

    def _preview_theme(self) -> None:
        """主题下拉框变化时实时预览"""
        theme_name = self.theme_combo.currentData()
        if not theme_name or theme_name == ThemeManager.current_name():
            return
        ThemeManager.set_theme(theme_name)
        self._apply_theme()
        if isinstance(self._parent_window, SelectionWindow):
            self._parent_window._apply_theme()
            if self._parent_window.display_window and hasattr(self._parent_window.display_window, '_refresh_theme'):
                self._parent_window.display_window._refresh_theme()

    def _preview_ui_font(self) -> None:
        """UI 字体下拉框变化时实时预览"""
        family = self.ui_font_combo.currentFont().family()
        set_ui_font(family)
        self._apply_theme()
        if isinstance(self._parent_window, SelectionWindow):
            self._parent_window._apply_theme()
            if self._parent_window.display_window and hasattr(self._parent_window.display_window, '_refresh_theme'):
                self._parent_window.display_window._refresh_theme()

    def _on_accept(self) -> None:
        """点击确定: 应用语言、保存所有配置并关闭"""
        # 语言切换
        new_lang = self.lang_combo.currentData()
        if new_lang and new_lang != I18n.current_language():
            I18n.set_language(new_lang)
            QMessageBox.information(
                self,
                I18n.t("settings_window.language_switch_title"),
                I18n.t("settings_window.language_switch_msg")
            )

        # 主题和 UI 字体已在预览时应用, 这里只需要保存
        set_ui_font(self.ui_font_combo.currentFont().family())
        if self.theme_combo.currentData() != ThemeManager.current_name():
            ThemeManager.set_theme(self.theme_combo.currentData())

        # GTP 渲染字体
        RenderConfig.NOTE_FONT_FAMILY = self.gtp_font_combo.currentFont().family()

        # GTP 渲染参数
        for attr, spin in self._render_spinboxes.items():
            setattr(RenderConfig, attr, spin.value())

        # 保存到 settings.json
        if isinstance(self._parent_window, SelectionWindow):
            self._parent_window.save_config()

        self.accept()

    def _on_reject(self) -> None:
        """点击取消: 恢复主题和 UI 字体预览, 放弃其他修改"""
        # 恢复主题
        if ThemeManager.current_name() != self._original_theme:
            ThemeManager.set_theme(self._original_theme)
            if isinstance(self._parent_window, SelectionWindow):
                self._parent_window._apply_theme()
                if self._parent_window.display_window and hasattr(self._parent_window.display_window, '_refresh_theme'):
                    self._parent_window.display_window._refresh_theme()

        # 恢复 UI 字体
        set_ui_font(self._original_ui_font)
        if isinstance(self._parent_window, SelectionWindow):
            self._parent_window._apply_theme()
            if self._parent_window.display_window and hasattr(self._parent_window.display_window, '_refresh_theme'):
                self._parent_window.display_window._refresh_theme()

        self.reject()

    def _on_button_clicked(self, button: QAbstractButton) -> None:
        """
        按钮点击统一处理（除确定/取消外的其他按钮）

        参数:
            button: 被点击的按钮对象
        """
        role = self.button_box.buttonRole(button)
        if role == QDialogButtonBox.ResetRole:
            self._reset_defaults()

    def _reset_defaults(self) -> None:
        """恢复所有设置为模块加载时捕获的默认值"""
        reply = QMessageBox.question(
            self,
            I18n.t("settings_dialog.reset_confirm_title"),
            I18n.t("settings_dialog.reset_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 语言
        idx = self.lang_combo.findData(_DEFAULT_LANGUAGE)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        # 主题
        idx = self.theme_combo.findData(_DEFAULT_THEME)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        # UI 字体 → 平台默认
        default_ui_font = get_font_family('ui')
        idx = self.ui_font_combo.findText(default_ui_font)
        if idx >= 0:
            self.ui_font_combo.setCurrentIndex(idx)
        else:
            self.ui_font_combo.setCurrentText(default_ui_font)

        # GTP 渲染字体
        idx = self.gtp_font_combo.findText(_DEFAULT_GTP_FONT)
        if idx >= 0:
            self.gtp_font_combo.setCurrentIndex(idx)
        else:
            self.gtp_font_combo.setCurrentText(_DEFAULT_GTP_FONT)

        # 渲染数值参数
        for attr, spin in self._render_spinboxes.items():
            spin.setValue(_DEFAULT_RENDER_VALUES.get(attr, 0))


# ============================================================
# 设置窗口 - 文件浏览与配置
# ============================================================

class SelectionWindow(QMainWindow):
    """
    选择主窗口(原 SettingsWindow)
    功能: 文件夹浏览、文件列表、搜索、最近文件(可折叠/展开)、打开设置面板、启动谱面显示窗口

    最近文件功能:
      - 独立控件(与文件夹文件列表分离)，支持折叠/展开按钮
      - 折叠状态只显示最新1个文件，展开显示全部(最多4个)
      - 数据持久化到 config/settings.json 的 recent_files 字段
      - 每次通过 show_display() 打开文件时自动更新(去重+截断)
    """

    def __init__(self):
        super().__init__()
        self.setWindowIcon(get_app_icon())  # 设置窗口图标
        self.display_window:Optional[DisplayWindow]=None
        self.current_directory:str=""
        self.is_loading:bool=False
        self._loaded_files:List[Tuple]=[]
        self._recent_files:List[str]=[]   # 最近打开的文件路径列表(最多4条)
        self.MAX_RECENT_FILES:int=4       # 最大记录数 (可调范围: 1-10)
        self._recent_expanded:bool=False  # 最近文件列表折叠状态 (默认折叠)

        self.init_ui()
        self._apply_theme()  # 应用深色主题

        loading_item=QListWidgetItem(I18n.t("settings_window.loading_init"))
        loading_item.setFlags(loading_item.flags() & ~Qt.ItemIsEnabled)
        self.file_list.addItem(loading_item)

        self.show()
        QTimer.singleShot(100,self._load_config_and_restore)

    def init_ui(self)->None:
        """初始化UI"""
        self.setWindowTitle(I18n.t("app.settings_title"))
        self.setGeometry(100,100,800,600)

        central=QWidget();self.setCentralWidget(central)
        main_layout=QVBoxLayout(central)

        # 文件夹选择 + 设置按钮
        folder_layout=QHBoxLayout()
        self.folder_label=QLabel(I18n.t("settings_window.folder_not_selected"))
        self.folder_button=QPushButton(I18n.t("settings_window.folder_btn"))
        self.folder_button.clicked.connect(self.select_folder)
        # 设置按钮: 点击打开设置对话框, 集中管理语言/主题/字体/GTP渲染参数
        self.settings_btn=QPushButton("⚙ " + I18n.t("settings_dialog.window_title"))
        self.settings_btn.setToolTip(I18n.t("settings_dialog.window_title"))
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_button)
        folder_layout.addStretch()
        folder_layout.addWidget(self.settings_btn)
        main_layout.addLayout(folder_layout)

        # === 最近打开文件列表 (独立控件，支持折叠/展开) ===
        # Recent files list (separate widget, collapsible)

        # 标题行: 标签 + 展开/折叠按钮 (水平布局) / Title row: label + toggle button
        recent_header_layout=QHBoxLayout()
        recent_header_layout.setContentsMargins(0,0,0,4)  # 减少底部间距
        self.recent_label=QLabel(I18n.t("settings_window.recent_list_label"))
        self.recent_toggle_btn=QPushButton(I18n.t("settings_window.recent_expand"))
        self.recent_toggle_btn.setFixedHeight(24)  # 紧凑按钮高度
        self.recent_toggle_btn.clicked.connect(self._toggle_recent_list)
        recent_header_layout.addWidget(self.recent_label)
        recent_header_layout.addStretch()
        recent_header_layout.addWidget(self.recent_toggle_btn)

        self.recent_list=QListWidget()
        self.recent_list.setObjectName("recent_list_widget")  # CSS选择器ID
        self.recent_list.itemClicked.connect(self._on_recent_file_clicked)  # 单击打开最近文件
        self.recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self._show_recent_context_menu)

        # 文件列表
        file_list_label=QLabel(I18n.t("settings_window.file_list_label"))
        search_layout=QHBoxLayout()
        search_layout.addWidget(QLabel(I18n.t("settings_window.search_label")))
        self.search_edit=QLineEdit()
        self.search_edit.setPlaceholderText(I18n.t("settings_window.search_placeholder"))
        self.search_edit.returnPressed.connect(self.filter_file_list)
        self.clear_search_btn=QPushButton(I18n.t("settings_window.search_clear"))
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.clear_search_btn)

        self.file_list=QListWidget()
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)

        self.original_items:List[Tuple]=[]
        self.is_searching:bool=False

        main_layout.addLayout(recent_header_layout)       # 标题行(标签+展开/折叠按钮)
        main_layout.addWidget(self.recent_list)            # 最近文件列表(独立控件)
        main_layout.addSpacing(8)                         # 两列表之间间距: 8px (可调范围5-10px)
        main_layout.addWidget(file_list_label)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.file_list)

    def _apply_theme(self)->None:
        """
        应用当前主题样式到SelectionWindow - 从ThemeManager读取当前主题配色
        
        性能优化(P0-1): 使用 _get_cached_qss() 缓存QSS字符串。
        """
        theme_name = ThemeManager.current_name()
        t = ThemeManager.current()
        qss = _get_cached_qss('SelectionWindow', theme_name, lambda: f"""
            QMainWindow,QWidget{{background-color:{t['bg_primary']};color:{t['text_primary']};
                font-family:{get_font_family_css('ui')};}}
            QLabel{{color:{t['text_primary']};font-size:13px;}}
            QPushButton{{background-color:{t['primary']};color:white;border:none;
                border-radius:6px;padding:7px 16px;font-weight:500;}}
            QPushButton:hover{{background-color:{t['primary_hover']};}}
            QPushButton:pressed{{background-color:{t['primary']};}}
            QLineEdit{{background-color:{t['bg_surface']};color:{t['text_primary']};
                border:1px solid{t['border']};border-radius:5px;padding:5px 8px;}}
            QSlider::groove:horizontal{{border:none;height:6px;background:{t['bg_surface']};border-radius:3px;}}
            QSlider::handle:horizontal{{background:{t['primary']};width:16px;margin:-6px 0;border-radius:8px;
                border:2px solid{t['bg_primary']};}}
            /* 最近文件列表样式 (独立控件，带强调色) / Recent list with accent color */
            QListWidget#recent_list_widget{{background-color:{t['bg_surface']};color:{t['accent']};
                border:1px solid{t['accent']};border-radius:6px;outline:none;}}
            QListWidget#recent_list_widget::item{{padding:6px;border-bottom:1px solid{t['border']};color:{t['accent']};}}
            QListWidget#recent_list_widget::item:selected{{background-color:{t['accent']};color:{t['bg_primary']};font-weight:bold;}}
            QListWidget#recent_list_widget::item:hover{{background-color:{t['accent']};opacity:0.15;border-radius:4px;}}
            QListWidget{{background-color:{t['bg_surface']};color:{t['text_primary']};
                border:1px solid{t['border']};border-radius:6px;outline:none;}}
            QListWidget::item{{padding:6px;border-bottom:1px solid{t['border']};}}
            QListWidget::item:selected{{background-color:{t['primary']};color:white;}}
            QListWidget::item:hover{{background-color:{t['primary']};opacity:0.15;border-radius:4px;}}
            QScrollBar:vertical{{background:{t['bg_secondary']};width:10px;border-radius:5px;}}
            QScrollBar::handle:vertical{{background:{t['border']};border-radius:5px;min-height:30px;}}
            QScrollBar::handle:vertical:hover{{background:{t['text_muted']};}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
        """)
        self.setStyleSheet(qss)

    def _load_config_and_restore(self)->None:
        """加载配置并恢复状态 - 包含目录有效性检查"""
        try:
            self.load_config()
            # 刷新最近文件列表 / Refresh recent files list
            self._refresh_recent_list()
            # 恢复上次打开的文件夹(带完整性检查)
            if hasattr(self,'last_folder') and self.last_folder:
                if os.path.isdir(self.last_folder) and os.access(self.last_folder, os.R_OK):
                    self.current_directory=self.last_folder
                    self.folder_label.setText(self.last_folder)
                    self.load_file_list_async(self.last_folder)
                else:
                    # 目录不存在或不可访问 - 清除无效记录并提示用户
                    print(f"提示: 上次目录不可用({self.last_folder})，请重新选择")
                    self.last_folder=''
                    self.save_config()  # 清除无效路径
        except Exception as e:
            print(f"恢复配置出错: {e}")

    def load_config(self)->None:
        """加载配置文件 - 恢复目录、语言、主题、字体、GTP渲染参数和最近文件"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE,'r',encoding='utf-8') as f:
                    cfg=json.load(f)
                    self.last_folder=cfg.get('last_folder','')
                    # 加载最近文件列表(过滤不存在的文件) / Load recent files (filter missing)
                    raw_recent=cfg.get('recent_files', [])
                    self._recent_files=[p for p in raw_recent if os.path.isfile(p)]
                    # 应用语言/主题/UI字体/GTP渲染参数
                    apply_config_settings(cfg)
            else:
                self.last_folder=''
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.last_folder=''

    def save_config(self)->None:
        """保存配置文件 - 包含目录、语言、主题、字体、GTP渲染参数和最近文件"""
        try:
            cfg={
                'last_folder': self.current_directory,
                'language': I18n.current_language(),
                'theme': ThemeManager.current_name(),
                'ui_font': _UI_FONT_FAMILY,
                'gtp_font': getattr(RenderConfig, 'NOTE_FONT_FAMILY', 'Arial'),
                'recent_files': self._recent_files,  # 保存最近文件列表
                'render_config': {
                    attr: getattr(RenderConfig, attr)
                    for attr, _, _, _, _, _ in _RENDER_PARAMS
                },
            }
            os.makedirs(os.path.dirname(CONFIG_FILE),exist_ok=True)
            with open(CONFIG_FILE,'w',encoding='utf-8') as f:
                json.dump(cfg,f,ensure_ascii=False,indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def _open_settings_dialog(self)->None:
        """打开设置对话框, 集中配置语言/主题/字体/GTP渲染参数"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def select_folder(self)->None:
        """选择文件夹"""
        folder=QFileDialog.getExistingDirectory(self,I18n.t("settings_window.folder_dialog_title"),"",QFileDialog.ShowDirsOnly)
        if folder:
            self.current_directory=folder
            self.folder_label.setText(folder)
            self.load_file_list_async(folder)
            self.save_config()

    def load_file_list_async(self,folder:str)->None:
        """异步加载文件列表"""
        self.is_loading=True;self.file_list.clear()
        item=QListWidgetItem(I18n.t("settings_window.loading_files"));item.setFlags(item.flags()&~Qt.ItemIsEnabled)
        self.file_list.addItem(item)
        pool=QThreadPool.globalInstance()
        worker=LoadFileListWorker(folder)
        worker.signals.finished.connect(self._on_files_loaded)
        worker.signals.error.connect(self._on_files_error)
        pool.start(worker)

    def _on_files_loaded(self, result: List[Tuple])->None:
        """文件列表加载完成 - result为文件列表[(name,path,is_dir),...]"""
        self.is_loading=False;self.file_list.clear()
        self.original_items=[];self.is_searching=False;self.search_edit.clear()
        self._loaded_files=result  # 接收并存储加载结果

        if self.current_directory and self.current_directory!=os.path.dirname(self.current_directory):
            up=QListWidgetItem(I18n.t("settings_window.parent_dir"))
            up.setData(Qt.UserRole,os.path.dirname(self.current_directory));up.setData(Qt.UserRole+1,True)
            self.file_list.addItem(up);self.original_items.append((I18n.t("settings_window.parent_dir"),os.path.dirname(self.current_directory),True))

        # 性能优化(P2-3): 批量插入文件列表项，避免逐个addItem触发N次repaint
        # setUpdatesEnabled(False) 禁用界面更新，批量完成后统一刷新
        self.file_list.setUpdatesEnabled(False)
        for name,fpath,is_dir in self._loaded_files:
            item=QListWidgetItem(name)
            item.setData(Qt.UserRole,fpath);item.setData(Qt.UserRole+1,is_dir)
            if is_dir:item.setToolTip(f"进入: {name}")
            else:item.setToolTip(fpath)
            self.file_list.addItem(item);self.original_items.append((name,fpath,is_dir))
        self.file_list.setUpdatesEnabled(True)

    def _on_files_error(self,msg:str)->None:
        """加载错误处理 - 区分目录错误与一般错误"""
        self.is_loading=False;self.file_list.clear()
        # 添加空状态提示
        empty_item=QListWidgetItem(I18n.t("settings_window.empty_folder"));empty_item.setFlags(empty_item.flags()&~Qt.ItemIsEnabled)
        self.file_list.addItem(empty_item)
        # 根据错误类型给出不同提示
        if "目录不存在" in msg or "路径不是文件夹" in msg:
            QMessageBox.warning(self,I18n.t("settings_window.dir_unavailable_title"),I18n.t("settings_window.dir_unavailable_msg", msg=msg))
        elif "无权限" in msg:
            QMessageBox.warning(self,I18n.t("settings_window.permission_denied_title"),I18n.t("settings_window.permission_denied_msg", msg=msg))
        else:
            QMessageBox.critical(self,I18n.t("messages.load_error"),I18n.t("messages.load_error_msg", msg=msg))

    def on_file_double_clicked(self,item:QListWidgetItem)->None:
        """双击文件项 - 图片格式自动加载同目录所有图片(按序拼接)"""
        fpath=item.data(Qt.UserRole);is_dir=item.data(Qt.UserRole+1)
        if is_dir:
            self.is_loading=True;self.file_list.clear()
            li=QListWidgetItem(I18n.t("settings_window.loading_entering"));li.setFlags(li.flags()&~Qt.ItemIsEnabled)
            self.file_list.addItem(li)
            self.current_directory=fpath;self.folder_label.setText(fpath)
            self.load_file_list_async(fpath);self.save_config()
        else:
            ext=os.path.splitext(fpath)[1].lower()
            if ext in SUPPORTED_PDF_EXTENSIONS:
                self.show_display(fpath,'pdf')
            elif ext in SUPPORTED_IMAGE_EXTENSIONS:
                # 收集同目录下所有支持的图片文件，按名称排序后拼接
                directory=os.path.dirname(fpath)
                all_images=sorted(
                    [os.path.join(directory,f) for f in os.listdir(directory)
                     if os.path.isfile(os.path.join(directory,f))
                     and os.path.splitext(f)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS]
                )
                self.show_display(all_images,'images')
            elif ext in SUPPORTED_GTP_EXTENSIONS:
                self.show_display(fpath,'gtp')

    def show_context_menu(self,pos:QPoint)->None:
        """右键菜单 - 支持查看/播放/打开文件位置等操作"""
        item=self.file_list.itemAt(pos)
        if not item:return
        fpath=item.data(Qt.UserRole);is_dir=item.data(Qt.UserRole+1) or False
        menu=QMenu(self)
        if is_dir:
            menu.addAction(I18n.t("settings_window.context_play_all"),lambda:self.play_all_images(fpath))
            menu.addAction(I18n.t("settings_window.context_enter_folder"),lambda:self.on_file_double_clicked(item))
            menu.addSeparator()
            menu.addAction(I18n.t("settings_window.context_open_location"),lambda:self.open_file_location(fpath))
        else:
            menu.addAction(I18n.t("settings_window.context_view_file"),lambda:self.on_file_double_clicked(item))
            ext=os.path.splitext(fpath)[1].lower()
            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                menu.addAction(I18n.t("settings_window.context_play_image"),lambda:self.show_display([fpath],'images'))
                src=self.original_items if not self.is_searching else []
                menu.addAction(I18n.t("settings_window.context_play_all_images"),lambda:self.play_all_images(os.path.dirname(fpath)))
            menu.addSeparator()
            # 通用：任何文件都可在资源管理器中定位
            menu.addAction(I18n.t("settings_window.context_open_location"),lambda:self.open_file_location(fpath))
        menu.exec_(self.file_list.mapToGlobal(pos))

    def open_file_location(self,fpath:str)->None:
        """
        在系统文件资源管理器中打开并选中指定文件/文件夹
        
        原理: 调用系统命令定位到文件
          Windows: explorer /select,"路径" (需确保路径为绝对路径)
          macOS:   open -R "路径"
          Linux:   xdg-open 目录 或 nautilus --select "路径"
        
        修复: 
          - 确保传入绝对路径(相对路径会导致explorer打开默认文档文件夹)
          - 使用shell=True避免PowerShell参数解析问题
          - 路径不存在时给出明确提示
          - 添加macOS支持 (open -R)
        
        参数:
            fpath: 要定位的文件或文件夹的路径(绝对或相对)
        """
        import subprocess, platform
        try:
            # 统一转为绝对路径(关键修复: 相对路径会导致explorer打开"文档"文件夹)
            abs_path = os.path.abspath(fpath) if fpath else ""
            
            if not os.path.exists(abs_path):
                QMessageBox.warning(self,I18n.t("settings_window.locate_fail_title"),I18n.t("settings_window.locate_fail_msg", path=abs_path))
                return
            
            sys_name = platform.system()
            if sys_name == 'Windows':
                # Windows: 使用shell=True确保explorer正确解析/select参数
                # 注意: /select和路径之间不能有空格，否则explorer会忽略select参数
                subprocess.run(f'explorer /select,"{abs_path}"', shell=True, check=False)
            elif sys_name == 'Darwin':
                # macOS: 使用 open -R 在 Finder 中定位并选中文件
                # open -R 是 macOS 原生命令，会在 Finder 中高亮选中文件
                subprocess.run(['open', '-R', abs_path], check=False, timeout=10)
            elif sys_name == 'Linux':
                # Linux: 尝试多种文件管理器
                for cmd in [
                    ['xdg-open', os.path.dirname(abs_path)],
                    ['nautilus', '--select', abs_path],
                    ['dolphin', '--select', abs_path],
                    ['thunar', abs_path],
                ]:
                    try:
                        subprocess.run(cmd, check=False, timeout=3)
                        break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
        except Exception as e:
            QMessageBox.warning(self,I18n.t("settings_window.open_fail_title"),I18n.t("settings_window.open_fail_msg", error=str(e)))

    def play_all_images(self,directory:str)->None:
        """播放文件夹内所有图片"""
        images=[]
        for f in sorted(os.listdir(directory)):
            fp=os.path.join(directory,f)
            if os.path.isfile(fp) and os.path.splitext(fp)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS:
                images.append(fp)
        if images:
            self.show_display(images,'images')

    def show_display(self,fpath,ftype:str)->None:
        """显示谱面窗口"""
        # 默认播放速度 500ms（中等速度）
        speed=500

        if not self.display_window or not self.display_window.isVisible():
            self.display_window=DisplayWindow(fpath,ftype,speed)
        else:
            self.display_window.update_content(fpath,ftype,speed)
        self.display_window.show()

        # 记录到最近文件(仅单个文件)/Record to recent files (single file only)
        if isinstance(fpath, str):
            self._add_recent_file(fpath)

    def filter_file_list(self)->None:
        """搜索过滤"""
        text=self.search_edit.text().strip()
        if not text:self.clear_search();return
        self.is_searching=True;self.file_list.clear()
        results=[]
        for name,fpath,is_dir in self.original_items:
            if name=="[返回上一级]":continue
            if text.lower() in name.lower():
                results.append((name,fpath,is_dir))
        up=QListWidgetItem("[返回上一级]")
        up.setData(Qt.UserRole,os.path.dirname(self.current_directory));up.setData(Qt.UserRole+1,True)
        self.file_list.addItem(up)
        for name,fpath,is_dir in results:
            item=QListWidgetItem(name)
            item.setData(Qt.UserRole,fpath);item.setData(Qt.UserRole+1,is_dir)
            self.file_list.addItem(item)

    def clear_search(self)->None:
        """清除搜索"""
        self.search_edit.clear();self.is_searching=False;self.file_list.clear()
        for name,fpath,is_dir in self.original_items:
            item=QListWidgetItem(name)
            item.setData(Qt.UserRole,fpath);item.setData(Qt.UserRole+1,is_dir)
            self.file_list.addItem(item)

    # ============================================================
    # 最近文件功能 / Recent Files
    # ============================================================

    def _add_recent_file(self, file_path: str) -> None:
        """
        将文件添加到最近打开列表

        原理:
          1. 将新文件插入到列表头部(最新的在最前面)
          2. 去重: 如果文件已在列表中，先移除旧位置再插入头部
          3. 截断: 只保留最近的 MAX_RECENT_FILES(4) 条记录
          4. 持久化: 立即保存到 config/settings.json

        参数:
            file_path: 文件的绝对路径
        """
        if not file_path or not isinstance(file_path, str):
            return

        # 统一转为绝对路径 / Convert to absolute path
        abs_path = os.path.abspath(file_path)

        # 检查是否为支持的文件格式 / Check if supported format
        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in SUPPORTED_ALL_EXTENSIONS:
            return

        # 去重: 先移除已存在的相同路径 / Deduplicate: remove existing
        if abs_path in self._recent_files:
            self._recent_files.remove(abs_path)

        # 插入到列表头部 / Insert at head (most recent first)
        self._recent_files.insert(0, abs_path)

        # 截断到最大数量 / Truncate to max count
        self._recent_files = self._recent_files[:self.MAX_RECENT_FILES]

        # 持久化保存 + 刷新UI / Persist and refresh UI
        self.save_config()
        self._refresh_recent_list()

    def _on_recent_file_clicked(self, item: QListWidgetItem) -> None:
        """
        最近文件列表项单击处理 - 单击即可打开文件

        参数:
            item: 被单击的最近文件 QListWidgetItem 对象
        """
        if not item or self.is_loading:
            return

        fpath = item.data(Qt.UserRole)
        if fpath and os.path.isfile(fpath):
            ext = os.path.splitext(fpath)[1].lower()
            if ext in SUPPORTED_PDF_EXTENSIONS:
                self.show_display(fpath, 'pdf')
            elif ext in SUPPORTED_IMAGE_EXTENSIONS:
                self.show_display([fpath], 'images')
            elif ext in SUPPORTED_GTP_EXTENSIONS:
                self.show_display(fpath, 'gtp')

    def _show_recent_context_menu(self, pos: QPoint) -> None:
        """
        最近文件列表的右键菜单

        功能: 提供打开文件、在资源管理器中定位、从列表移除
        """
        item=self.recent_list.itemAt(pos)
        if not item:return
        fpath=item.data(Qt.UserRole)
        if not fpath or not os.path.isfile(fpath):return

        menu=QMenu(self)
        menu.addAction(I18n.t("settings_window.context_view_file"),
                      lambda:self._open_recent_file_by_path(fpath))
        menu.addSeparator()
        menu.addAction(I18n.t("settings_window.context_open_location"),
                      lambda:self.open_file_location(fpath))
        menu.addAction(I18n.t("settings_window.recent_remove"),
                      lambda:self._remove_recent_file(fpath))
        menu.exec_(self.recent_list.mapToGlobal(pos))

    def _open_recent_file_by_path(self, fpath: str) -> None:
        """根据路径打开最近文件(供右键菜单调用)"""
        if not fpath or not os.path.isfile(fpath):
            return
        ext = os.path.splitext(fpath)[1].lower()
        if ext in SUPPORTED_PDF_EXTENSIONS:
            self.show_display(fpath, 'pdf')
        elif ext in SUPPORTED_IMAGE_EXTENSIONS:
            self.show_display([fpath], 'images')
        elif ext in SUPPORTED_GTP_EXTENSIONS:
            self.show_display(fpath, 'gtp')

    def _remove_recent_file(self, fpath: str) -> None:
        """
        从最近文件列表中移除指定文件

        参数:
            fpath: 要移除的文件绝对路径
        """
        if fpath in self._recent_files:
            self._recent_files.remove(fpath)
            self.save_config()  # 持久化
            self._refresh_recent_list()  # 刷新UI

    def _refresh_recent_list(self) -> None:
        """
        刷新最近文件列表控件 (独立recent_list)

        原理:
          1. 清空 recent_list 控件
          2. 折叠时只显示最新1项，展开时显示全部
          3. 跳过不存在的文件
        """
        self.recent_list.clear()

        if not self._recent_files:
            # 无最近文件时显示提示 / Show hint when empty
            empty_item=QListWidgetItem(I18n.t("settings_window.recent_empty"))
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEnabled)
            empty_item.setForeground(QColor(ThemeManager.get('text_muted')))
            self.recent_list.addItem(empty_item)
            row_h=self.recent_list.sizeHintForRow(0) if self.recent_list.count()>0 else 28
            self.recent_list.setFixedHeight(row_h + 12)
            return

        # 折叠只显示最新1项，展开显示全部 / Collapsed=1 latest, expanded=all
        files_to_show = self._recent_files if self._recent_expanded else self._recent_files[:1]

        for recent_path in files_to_show:
            if not os.path.isfile(recent_path):
                continue

            filename=os.path.basename(recent_path)
            item=QListWidgetItem(f"📄 {filename}")
            item.setData(Qt.UserRole, recent_path)
            item.setToolTip(I18n.t("settings_window.recent_file_tooltip") + f"\n{recent_path}")
            self.recent_list.addItem(item)

        # 根据展开/折叠状态设置高度 / Set height based on expand/collapse state
        self._apply_recent_list_height()

    def _apply_recent_list_height(self) -> None:
        """
        根据展开/折叠状态设置最近列表高度

        原理: 高度 = sizeHintForRow(0) × 实际项数 + 12px边距
        """
        if self.recent_list.count() <= 0:
            self.recent_list.setFixedHeight(32)
            return

        row_h = self.recent_list.sizeHintForRow(0)
        self.recent_list.setFixedHeight(row_h * self.recent_list.count() + 12)

    def _toggle_recent_list(self) -> None:
        """
        切换最近文件列表的展开/折叠状态

        原理:
          1. 翻转 _recent_expanded 布尔值
          2. 更新按钮文字(展开↔折叠)
          3. 重新构建列表内容(折叠只显示1项，展开显示全部)
        """
        self._recent_expanded = not self._recent_expanded

        if self._recent_expanded:
            self.recent_toggle_btn.setText(I18n.t("settings_window.recent_collapse"))
        else:
            self.recent_toggle_btn.setText(I18n.t("settings_window.recent_expand"))

        self._refresh_recent_list()


# ============================================================
# 程序入口
# ============================================================

if __name__ == '__main__':
    # 确保配置和标注目录存在
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    os.makedirs(ANNOTATION_DIR, exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式作为基础，配合自定义深色/浅色主题
    app.setWindowIcon(get_app_icon())  # 设置全局应用图标(任务栏图标/窗口默认图标)

    # v2.0.9 修改: 统一从配置文件加载语言/主题/UI字体/GTP渲染参数
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE,'r',encoding='utf-8') as f:
                cfg=json.load(f)
            apply_config_settings(cfg)
        else:
            I18n.set_language('zh_CN')
            ThemeManager.set_theme('dark')
    except Exception:
        I18n.set_language('zh_CN')
        ThemeManager.set_theme('dark')

    settings = SelectionWindow()
    sys.exit(app.exec_())
