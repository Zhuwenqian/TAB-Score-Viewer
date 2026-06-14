# -*- coding: utf-8 -*-
"""
============================================================
文件名: TAB Score Viewer.py
功能描述: 万能吉他谱查看器(TAB Score Viewer) - 支持多格式查看、播放、标注、导出
         支持格式: PNG, JPG, JPEG, WEBP(图片), PDF(文档), GP3/GP4/GP5/GPX(GTP吉他谱)

         核心功能:
           1. 多格式吉他谱查看与自动滚动播放(速度范围350-700ms)
           2. 可拖动进度条 + 循环播放(不循环/全局循环/区域A-B循环)
           3. 速度曲线编辑器 - 贝塞尔曲线可视化编辑，含预设模板(图片/PDF格式)
           4. 谱面文本标注系统 - 双击添加/拖动移动/样式自定义
           5. 标注导入导出 - 自动加载同名.anno.json标注文件，A4尺寸PNG/PDF导出
           6. 全局撤销重做 - Ctrl+Z/Y统一撤销所有标注操作(画布+管理器共享栈)
           7. 页码导航 - PDF/多图模式底部页码输入框直接跳转
           8. 鼠标滚轮滚动 - 支持Ctrl加速/Shift精细控制
           9. 深色/浅色主题UI + 自定义组件(按钮/滑块/进度条) + 实时主题切换
          10. 键盘快捷键 - 空格播放暂停/方向键调速/Ctrl+Z撤销/Ctrl+Y重做/ESC关闭
          11. GTP文件完整渲染 - 基于ApolloTab库解析并渲染为六线谱图像
          12. 右键打开文件位置 - 文件列表右键菜单支持在资源管理器中定位文件
          13. GTP音轨切换 - 下拉菜单选择不同音轨查看(含调弦信息显示)
          14. 播放光标 - 竖线跟随播放进度移动，当前小节高亮显示
          15. 播放性能优化 - 图片缩放缓存+UI节流更新，解决播放卡顿
          16. 国际化支持(i18n) - 中文/英文双语切换，JSON翻译文件

创建日期: 2026-06-06
最后修改: 2026-06-13 (v2.0.1 - UI优化: 移除缩放/移除Emoji/SoundFont打包支持 + Bug修复)

依赖库:
  - PyQt5 >= 5.15     # GUI框架(窗口/控件/信号槽/绘图/PDF导出)
  - PyMuPDF >= 1.23   # PDF解析与页面渲染为图片 (开源项目: Artifex Software)
  - Pillow >= 10.0    # 图片处理(PNG/JPG/WEBP解码) (开源项目: Python Imaging Library)
  - guitarpro >= 0.11 # Guitar Pro文件解析 (开源项目: pyguitarpro) - GTP渲染功能依赖

技术栈: Python 3.8+ / PyQt5 / PyMuPDF / Pillow / guitarpro(gtp_engine)
兼容性: Windows / Linux / Docker (所有路径使用相对路径)

项目结构:
  TAB Score Viewer.py     - 主程序(本文件，含I18n国际化类)
  TAB Score Viewer.spec   - PyInstaller打包配置
  locales/                - 翻译文件目录(zh_CN.json/en_US.json)
  soundfont/              - SoundFont音色库目录(GTP音频播放必需,需下载FluidR3_GM.sf2)
  config/settings.json    - 用户配置(含语言/主题设置,运行时自动生成)
  data/annotations/       - 标注数据存储(JSON格式)
  readme/                 - 项目文档目录
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
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# Qt GUI组件
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QListWidget,
    QListWidgetItem, QMenu, QAction, QMessageBox, QLineEdit,
    QDialog, QTextEdit, QDialogButtonBox, QGroupBox, QCheckBox,
    QSpinBox, QColorDialog, QFontDialog, QSplitter, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QSizePolicy, QToolTip,
    QProgressBar, QComboBox, QTabWidget, QToolButton, QRadioButton
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QPen, QColor, QFont, QFontMetrics, QIcon,
    QImage, QCursor, QPainterPath, QLinearGradient, QRadialGradient,
    QMouseEvent, QKeyEvent, QWheelEvent, QResizeEvent, QShowEvent,
    QKeySequence, QPalette, QBrush, QTransform, QPolygonF
)
from PyQt5.QtCore import (
    Qt, QTimer, QRect, QSize, QPoint, QRunnable, QThreadPool,
    pyqtSignal, QObject, QEasingCurve, QPropertyAnimation,
    QRectF, QPointF, pyqtProperty, QBuffer
)

# 第三方库
import fitz  # PyMuPDF - PDF解析 (开源库)
from PIL import Image as PILImage  # Pillow - 图片处理(含WEBP) (开源库)


# ============================================================
# 配置常量
# ============================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "settings.json")
ANNOTATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "annotations")
# 应用图标路径(开发模式: 脚本目录; 打包模式: exe所在目录)
_APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(_APP_BASE_DIR, "icon.ico")


def get_app_icon() -> QIcon:
    """
    获取应用图标(QIcon对象)
    原理: 兼容开发和PyInstaller打包两种运行模式
      - 开发模式: 从脚本同目录读取icon.ico
      - 打包模式(sys.frozen): 从exe所在目录读取icon.ico(非单文件模式数据在exe旁)
    返回: QIcon对象，文件不存在时返回空 QIcon
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller打包模式: exe所在目录
        base = os.path.dirname(sys.executable)
    else:
        # 开发模式: 脚本所在目录
        base = _APP_BASE_DIR
    ico_path = os.path.join(base, "icon.ico")
    if os.path.exists(ico_path):
        return QIcon(ico_path)
    return QIcon()  # 文件不存在时返回空图标
# 标注文件扩展名: 与源文件同目录，命名为 {源文件名}.anno.json
# 例如: 晚安北京.gp4 → 晚安北京.gp4.anno.json
ANNOTATION_EXT = ".anno.json"

# 支持的文件扩展名
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
SUPPORTED_PDF_EXTENSIONS = ('.pdf',)
SUPPORTED_GTP_EXTENSIONS = ('.gp3', '.gp4', '.gp5', '.gpx', '.gtp')
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
               font-family: 'Microsoft YaHei','Segoe UI',sans-serif; }}
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
    font_family: str = "Microsoft YaHei"
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
      1. 从 locales/ 目录加载JSON翻译文件(如 zh_CN.json, en_US.json)
      2. 提供 t(key, **kwargs) 方法获取翻译文本，支持 {} 占位符格式化
      3. 支持运行时语言切换，切换后通过 language_changed 信号通知UI刷新
      4. 缺失翻译自动回退到中文(zh_CN)，确保UI不会出现空白字符串
    
    使用方式:
      # 获取翻译文本
      text = I18n.t("app.title")                    # 无占位符
      text = I18n.t("messages.export_success_msg",  # 带占位符
                   fmt="PDF", path="/tmp/a.pdf", count=3)
      
      # 切换语言
      I18n.set_language("en_US")
    
    翻译文件格式 (locales/xx_XX.json):
      {
        "_meta": {"language": "zh_CN", "name": "简体中文"},
        "app": {"title": "..."},
        "toolbar": {"zoom": "缩放:", ...},
        ...
      }
    
    调整说明:
      - 新增语言: 在 locales/ 下新建 xx_XX.json 文件即可
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
        # 使用相对路径，兼容 Windows/Linux/Docker
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
            lang_code: 目标语言代码，如 "zh_CN", "en_US"
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
            [(code, name), ...] 如 [("zh_CN", "简体中文"), ("en_US", "English")]
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
        """加载PDF文件 - 使用PyMuPDF渲染每页为高DPI图片"""
        images = []
        pdf_document = fitz.open(self.file_path)
        total_pages = len(pdf_document)
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            pix = page.get_pixmap(dpi=200)  # 高DPI渲染保证清晰度
            qt_image = QPixmap()
            qt_image.loadFromData(pix.tobytes("png"))
            images.append(qt_image)
            self.signals.progress.emit(int((page_num + 1) / total_pages * 100))
        pdf_document.close()
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
        加载Guitar Pro文件(.gp3/.gp4/.gp5/.gpx/.gtp)
        
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
        title_font = QFont("Microsoft YaHei", 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path)
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"加载失败: {filename}")

        # 错误文本
        painter.setPen(QColor(ThemeManager.get('text_primary', '#E2E8F0')))
        info_font = QFont("Microsoft YaHei", 13)
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
        title_font = QFont("Microsoft YaHei", 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path)
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"Guitar Pro 文件: {filename}")

        # 信息文本
        painter.setPen(QColor(ThemeManager.get('text_primary', '#E2E8F0')))
        info_font = QFont("Microsoft YaHei", 13)
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
    现代化按钮组件 - 支持动态主题切换
    功能: 带悬停效果、阴影、圆角的按钮基类
    主题: 通过 ThemeManager.get() 读取当前主题色，支持运行时切换
    """

    def __init__(self, text: str, color_key: str = 'primary', parent=None):
        super().__init__(text, parent)
        self.color_key = color_key
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
                font-family: 'Microsoft YaHei';
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

    def refresh_theme(self) -> None:
        """主题切换时调用 - 重新应用样式"""
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
        painter.setFont(QFont("Microsoft YaHei", 9))
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
            QLabel {{ color: {t['text_primary']}; font-family: 'Microsoft YaHei'; }}
            QGroupBox {{ color: {t['text_primary']}; border: 1px solid {t['border']};
                         border-radius: 8px; margin-top: 10px; padding-top: 10px; font-weight: bold; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                          border-radius: 6px; padding: 6px 14px; font-family: 'Microsoft YaHei'; }}
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
        painter.setFont(QFont("Microsoft YaHei", 9))
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
            QLabel {{ color: {t['text_primary']}; font-family: 'Microsoft YaHei'; }}
            QTextEdit {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: 'Microsoft YaHei'; }}
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
            QLabel {{ color: {t['text_primary']}; font-family: 'Microsoft YaHei'; }}
            QTextEdit {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {t['bg_surface']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {t['text_primary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: 'Microsoft YaHei'; }}
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
            QLabel{{color:{t['text_primary']};font-family:'Microsoft YaHei';}}
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

    def set_images(self, images: List[QPixmap]) -> None:
        self.images = images; self._cache_dirty = True; self._total_h_dirty = True; self.update()

    def set_annotations(self, annotations: List[Annotation]) -> None:
        self.annotations = annotations; self.update()

    def _rebuild_image_cache(self) -> None:
        """
        重建缩放图片缓存
        
        原理: 将所有原始图片按当前画布宽度预缩放并存入缓存，
              paintEvent时直接使用缓存，避免每帧调用scaled()。
              这是解决播放卡顿的核心优化 — scaled()是CPU密集操作。
        
        触发时机:
          - set_images()后首次绘制
          - 画布宽度变化(resizeEvent)
        """
        if not self._cache_dirty and self._cache_width == self.width():
            return  # 缓存有效，无需重建
        ww = self.width()
        if ww <= 20 or not self.images:
            self._cached_scaled = []; self._cache_width = ww; self._cache_dirty = False
            return
        sw = ww - 20
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
            # 坐标系统说明:
            #   current_position: 滚动偏移量(像素)，paintEvent中 base_y = -current_position
            #   total_scroll_distance: 最大可滚动距离(像素) = 总内容高度 - 显示区域高度
            #   两者都是像素单位，不需要比例转换！
            #
            # 点击位置计算:
            #   event.y() = 鼠标在画布中的Y坐标(像素)
            #   click_abs_y = 当前滚动偏移 + 鼠标Y = 点击处在总内容中的绝对Y坐标(像素)
            #   new_position = click_abs_y - 偏移量 = 使点击处显示在目标位置
            #
            # [v2.0.1 Bug修复] 点击跳转位置不准确的迭代修复:
            #   v2.0.1a问题: height/2居中偏移 → 点击前几行截断为0(无法跳转)
            #   v2.0.1b问题: height*0.25偏移 → position大时点上部仍会后移("跳到很后面")
            #   根因: click_abs_y = position + y, 当position很大时结果必然很大,
            #         与窗口高度成比例的偏移无法有效抵消
            #   最终修复: 改为固定小偏移(80px),点击处直接出现在视口顶部附近,
            #            行为直觉——点顶部=向前翻,点底部=向后翻,幅度正比于点击位置
            ww = self.width()
            if ww > 20:
                if self.parent_window.total_scroll_distance > 0:
                    # === 精确点击定位: 基于缓存图片实际高度计算位置 ===
                    # [v2.0.1核心修复] 原方案用 current_position + event.y() 计算绝对Y,
                    #   但这假设像素坐标与图片布局完全线性对应。实际上:
                    #   1. _rebuild_image_cache用int()截断缩放高度(如802.4→802)
                    #   2. _calculate_total_distance用float计算(保留802.4)
                    #   3. 两者随图片数量增多会产生累积误差→点击偏移
                    #
                    # 新方案: 遍历_cached_scaled的**实际像素高度**,精确找到点击位置落在哪张图片内,
                    #         用累积的真实像素值作为click_abs_y,消除截断误差

                    click_y = event.y()  # 点击在画布中的Y坐标

                    # 方法A: 快速估算(原方案,用于对比)
                    rough_abs_y = self.parent_window.current_position + click_y

                    # 方法B: 精确计算(遍历缓存图片的实际渲染高度)
                    # 原理: 从current_position开始,逐张累加缓存图片真实高度(+5px间距),
                    #       找到click_y落入哪张图片的范围,得到精确的内容绝对Y坐标
                    precise_abs_y = self.parent_window.current_position
                    found_image = False
                    remaining_y = click_y
                    for cached in self._cached_scaled:
                        if cached.isNull():
                            continue
                        img_h = cached.height()  # 缓存图片的实际渲染像素高度(已含int截断)
                        if remaining_y < img_h + 5:  # 在这张图片或间距内
                            precise_abs_y += remaining_y
                            found_image = True
                            break
                        remaining_y -= (img_h + 5)  # 跳过这张图片+间距
                        precise_abs_y += (img_h + 5)
                    if not found_image:
                        # 点击超出所有图片范围(不太可能,但防兜底)
                        precise_abs_y = rough_abs_y

                    # 使用精确计算的绝对Y坐标
                    click_abs_y = precise_abs_y

                    # [调试] 输出粗略值和精确值的差异(确认是否为int截断导致)
                    # 如果差异>5px说明截断误差是主因, 正式版可删除此print
                    diff = abs(rough_abs_y - precise_abs_y)
                    if diff > 2:
                        print(f"[ClickDebug] y={click_y} pos={self.parent_window.current_position:.0f} rough={rough_abs_y:.0f} precise={precise_abs_y:.0f} diff={diff:.0f}px")

                    # 无偏移: 点击处直接对齐到屏幕顶部(y=0)
                    click_offset = 0

                    # 视觉位置: clamp到有效范围(防止滚动越界)
                    new_position = click_abs_y - click_offset
                    new_position = max(0, min(new_position, self.parent_window.total_scroll_distance))

                    # Seek位置: 与视觉位置一致(都是基于点击的真实位置)
                    seek_position = new_position

                    # === 步骤1: 设置视觉位置和跳转目标(防止_tick覆盖) ===
                    self.parent_window.current_position = new_position
                    self.parent_window._click_jump_target = new_position
                    self.parent_window.update_progress_display()
                    self.parent_window._sync_play_time_from_position()  # 同步播放时间(点击跳转后)

                    # === 步骤2: 音频seek(跳转到对应时间点) ===
                    # [v2.0.1修复] height参数必须传0!
                    #
                    # 库函数内部实现(scroll_pos_to_time):
                    #   raw_scroll_y = scroll_pos + display_height / 2   ← 自动+h/2!
                    #
                    # 而我们的seek_position已经是"居中坐标"(与_tick的time_based_pos同坐标系),
                    # 即相当于 time_to_scroll_pos 返回值 = scroll_y - h/2。
                    # 如果再传self.height(),库内部会+h/2→多加~375px→经非线性映射放大→超前一页!
                    #
                    # 正确做法: 传0,让库内部只加0,保持对称性。
                    # 残留微小误差(如果有)用常量微调即可。
                    target_ms = 0
                    if (self.parent_window.gtp_player and
                        self.parent_window.gtp_player.is_audio_ready):
                        try:
                            target_ms = self.parent_window.gtp_player.scroll_pos_to_time(
                                seek_position,
                                self.parent_window.total_scroll_distance,
                                0  # 居中坐标不再需要h/2转换(内部会+0=无偏移)
                            )
                            print(f"[ClickDebug] pos={new_position:.0f} → ms={target_ms:.0f}")
                            if target_ms > 0:
                                self.parent_window.gtp_player.seek(target_ms)
                        except Exception as e:
                            print(f"[ClickPlay] seek失败: {e}")

                # === 步骤3: 启动播放(无论是否可滚动都执行!) ===
                # [v2.0.1修复] 热跳转方案: 不stop/restart,直接seek+继续播放
                # 原因: stop()会重置音频引擎内部状态→play()从0开始,覆盖seek结果!
                # 方案: 未播放则启动;播放中则热seek,_click_jump_target保护视觉位置
                if not self.parent_window.timer.isActive():
                    self.parent_window.toggle_playback()
                # 播放中: 步骤2的seek(target_ms)已生效,音频引擎从新位置继续
                #         _click_jump_target在步骤1已设置,_tick保护视觉直到追上

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
        """
        if event.button() == Qt.LeftButton and self._drag_ann_id:
            self.setCursor(Qt.ArrowCursor)
            # === 关键修复: 区分"点击X删除"和"拖动标注" ===
            # 原因: _hit_annotation() 扩展了右边界28px以包含X删除按钮，
            #       导致点X区域也会进入拖动模式。需要在release时判断：
            #       鼠标几乎没移动(是点击而非拖动) + 在X按钮区域内 → 走删除逻辑
            drag_distance = (event.pos() - self._drag_mouse_start).manhattanLength()
            is_click_not_drag = (drag_distance < 5)  # 移动<5px视为点击
            is_on_delete_btn = (self._delete_btn_rect.contains(event.pos()) or
                                (self._hover_ann_id and self._hit_annotation(event.x(), event.y()) is not None))

            if is_click_not_drag and is_on_delete_btn and self.parent_window:
                # 点击了X删除按钮 → 执行删除（不保存位置变化）
                del_id = self._drag_ann_id  # _drag_ann_id就是当前标注ID
                self.parent_window._anno_save_snapshot()
                self.parent_window.annotations = [
                    a for a in self.parent_window.annotations if a.id != del_id
                ]
                self.parent_window._save_annotations()
                self.set_annotations(self.parent_window.annotations)
                self._hover_ann_id = ""
                self._delete_btn_rect = QRect()
                self._drag_ann_id = ""
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

        # === 检测是否点击了删除按钮(非拖动状态下) ===
        # 修复: 播放时内容会滚动，paintEvent中缓存的_delete_btn_rect可能已过时。
        #       因此同时用 _hit_annotation 实时验证鼠标当前位置是否仍在标注区域内，
        #       任一条件满足即触发删除，确保播放中也能正常点击X按钮。
        is_on_stale_rect = self._delete_btn_rect.contains(event.pos())
        is_currently_hovered = (self._hover_ann_id and self._hit_annotation(event.x(), event.y()) is not None)
        if event.button() == Qt.LeftButton and self._hover_ann_id and (is_on_stale_rect or is_currently_hovered):
            if self.parent_window:
                # 找到要删除的标注并执行删除
                del_id = self._hover_ann_id
                self.parent_window._anno_save_snapshot()  # 删除前保存快照(支持撤销)
                self.parent_window.annotations = [
                    a for a in self.parent_window.annotations if a.id != del_id
                ]
                self.parent_window._save_annotations()
                self.set_annotations(self.parent_window.annotations)
                # 清除悬停状态
                self._hover_ann_id = ""
                self._delete_btn_rect = QRect()
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
            painter.setFont(QFont("Microsoft YaHei",15))
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
            painter.setFont(QFont("Microsoft YaHei",18))
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
        painter.setFont(QFont("Arial", 9))
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
                    painter.setFont(QFont("Arial", 8))
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
        双击谱面 - 优先检测是否点击了已有标注(编辑)，否则新建
        
        使用两种不同对话框:
          - 点击已有标注 → AnnotationEditDialog(带删除按钮)
          - 点击空白处 → AnnotationCreateDialog(无删除，只有确定/取消)
        
        命中区域: 基于_draw_one_ann中的bg_rect描边矩形(含padding)
        """
        if not self.parent_window or not self.parent_window.images: return
        cx,cy=event.x(),event.y()
        ww=self.width()

        # === 先检测是否点击了已有标注(命中区域=bg_rect描边范围) ===
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
                    return  # ← 关键: 必须return，防止继续执行新建标注

        # === 未点击到任何标注 → 新建标注(使用专用创建对话框) ===
        rel_x=max(0,min(1,(cx-10)/(ww-20))) if ww>20 else 0
        if self.parent_window.images:
            total_h=self._get_total_h()
            base_y=-self.parent_window.current_position
            rel_y=max(0,min(1,(cy-base_y)/total_h)) if total_h>0 else 0.5
        else:
            rel_y=0.5

        # 使用AnnotationCreateDialog(专用新建对话框，无删除功能)
        dlg=AnnotationCreateDialog(self, x=rel_x, y=rel_y)
        if dlg.exec_()==QDialog.Accepted:
            self.parent_window.add_annotation(dlg.get_annotation())  # 内部已调用 _anno_save_snapshot


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
        """
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{background-color:{t['bg_primary']};color:{t['text_primary']};
                font-family:'Microsoft YaHei','Segoe UI',sans-serif;}}
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

    def _refresh_theme(self) -> None:
        """
        主题切换时刷新DisplayWindow所有UI组件样式
        
        调用时机:
          - SettingsWindow._on_theme_changed() 切换主题时调用
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
        #    使用 display_widget.set_images() 而非直接赋值 self.images，
        #    因为 set_images() 会将 _cache_dirty 置为 True，确保缩放缓存被重建
        if self.gtp_player and hasattr(self.gtp_player, 'set_theme') and self.gtp_player.is_loaded:
            try:
                render_theme = ThemeManager.get_gtp_render_theme()
                self.gtp_player.set_theme(render_theme)
                # 重新渲染全部页面（替换整个images列表，确保所有页主题一致）
                all_pixmaps = self.gtp_player.render_track(self.gtp_player.current_track)
                if all_pixmaps:
                    self.display_widget.set_images(all_pixmaps)  # 触发缓存失效+重绘
                    print(f"[DisplayWindow] GTP渲染全部{len(all_pixmaps)}页已同步为: {render_theme}")
            except Exception as e:
                print(f"[DisplayWindow] GTP渲染主题同步失败: {e}")

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

        # 音频播放模式按钮（仅GTP文件显示，默认隐藏）
        # 3种模式: 全轨并轨(默认) / 仅当前轨 / 关闭音频
        self.audio_btn = QToolButton()
        self.audio_btn.setText(I18n.t("toolbar.audio_all"))
        self.audio_btn.setToolTip(I18n.t("toolbar.audio_tooltip"))
        self.audio_btn.setPopupMode(QToolButton.InstantPopup)  # 点击即弹出菜单
        self.audio_btn.setVisible(False)  # 非GTP文件时隐藏
        
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

        # 标注按钮
        self.annotation_btn=ModernButton(I18n.t("toolbar.annotation_btn"),'accent')
        self.annotation_btn.clicked.connect(self._open_annotation_manager)
        tb.addWidget(self.annotation_btn)

        # 导出按钮(A4 PNG/PDF，含标注)
        self.export_btn=ModernButton(I18n.t("toolbar.export_btn"),'primary')
        self.export_btn.setToolTip(I18n.t("toolbar.export_tooltip"))
        self.export_btn.clicked.connect(self._export_to_a4)
        tb.addWidget(self.export_btn)

        # 速度曲线按钮
        self.curve_btn=ModernButton(I18n.t("toolbar.curve_btn"),'primary')
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
        self.play_btn=ModernButton(I18n.t("control_panel.play_btn"),'success');self.play_btn.clicked.connect(self.toggle_playback)
        self.stop_btn=ModernButton(I18n.t("control_panel.stop_btn"),'danger');self.stop_btn.clicked.connect(lambda: self.stop_playback(reset_position=True));self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.play_btn);btn_row.addWidget(self.stop_btn);pl.addLayout(btn_row)

        # 循环模式
        loop_row=QHBoxLayout();loop_row.addWidget(QLabel(I18n.t("control_panel.loop_label")))
        self.loop_combo=QComboBox()
        self.loop_combo.addItems([I18n.t("control_panel.loop_no_loop"),I18n.t("control_panel.loop_global"),I18n.t("control_panel.loop_ab")])
        self.loop_combo.currentIndexChanged.connect(self._on_loop_mode_changed)
        loop_row.addWidget(self.loop_combo);pl.addLayout(loop_row)

        # A-B点按钮
        ab_row=QHBoxLayout()
        self.set_a_btn=ModernButton(I18n.t("control_panel.set_a_btn"),'warning');self.set_a_btn.clicked.connect(lambda:self._set_ab_point('a'))
        self.set_b_btn=ModernButton(I18n.t("control_panel.set_b_btn"),'warning');self.set_b_btn.clicked.connect(lambda:self._set_ab_point('b'))
        self.clear_ab_btn=ModernButton(I18n.t("control_panel.clear_ab_btn"),'text_muted');self.clear_ab_btn.clicked.connect(self._clear_ab_points)
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

        # === 状态信息 ===
        ig=QGroupBox(I18n.t("control_panel.status_info"));il=QVBoxLayout(ig)
        self.position_label=QLabel(I18n.t("control_panel.position_label", pct="0.0"));self.time_label=QLabel(I18n.t("control_panel.time_label", time="00:00"))
        il.addWidget(self.position_label);il.addWidget(self.time_label)
        self.ab_info_label=QLabel("")
        self.ab_info_label.setStyleSheet(f"color:{ThemeManager.get('accent', '#F97316')};font-size:11px;")
        il.addWidget(self.ab_info_label)
        layout.addWidget(ig)

        # 快捷键帮助
        hg=QGroupBox(I18n.t("control_panel.shortcut_group"));hl=QVBoxLayout(hg)
        help_txt=QLabel(I18n.t("control_panel.shortcut_help"))
        help_txt.setStyleSheet(f"color:{ThemeManager.get('text_muted', '#64748B')};font-size:11px;")
        hl.addWidget(help_txt);layout.addWidget(hg)
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
        self.play_btn.setStyleSheet(f"background-color:{ThemeManager.get('warning', '#F59E0B')};")
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
        self.play_btn.setStyleSheet(f"background-color:{ThemeManager.get('success', '#10B981')};")
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
        #       打包后exe所在目录与CWD可能不同, 需要显式添加搜索路径
        try:
            from ApolloTab.audio.synth_engine import SynthEngine
            # 获取应用根目录(开发模式: 脚本目录 / 打包模式: exe所在目录)
            import sys
            app_base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else _APP_BASE_DIR
            sf_dir = os.path.join(app_base, 'soundfont')
            # 将应用根目录下的soundfont目录插入搜索列表最前面(最高优先级)
            if sf_dir not in SynthEngine.SOUNDFONT_SEARCH_PATHS:
                SynthEngine.SOUNDFONT_SEARCH_PATHS.insert(0, sf_dir)
                print(f"[Audio] SoundFont搜索路径已添加: {sf_dir}")
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
                display_w = max(self.display_widget.width() - 20, 100)
                self.gtp_player.build_timeline(
                    self._page_layouts, self.images, display_w
                )
                self._playhead_timeline = self.gtp_player.playhead_timeline
                self._total_audio_duration_ms = self.gtp_player.total_duration_ms
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
            audio_time_ms = self.gtp_player.current_time_ms
            # 用速度曲线调整时间流逝速度(曲线加速=时间变快)
            if self.speed_curve.is_enabled and len(self.speed_curve.points) >= 2:
                curve_speed = self._get_curve_speed()
                time_scale = self.base_speed / max(curve_speed, 1)
                effective_time = audio_time_ms * time_scale
            else:
                effective_time = audio_time_ms

            # === 点击跳转保护: 如果有待处理的点击跳转目标，优先使用它 ===
            # 原因: 点击谱面后音频引擎刚开始播放，audio_time_ms接近0，
            #       _time_to_scroll_pos(接近0)会返回接近0的位置，覆盖掉用户点击的位置
            # 策略: 当音频时间推导出的位置 < 跳转目标时，保持使用跳转目标
            #       当音频时间追上或超过目标后，恢复正常的时间驱动模式
            if self._click_jump_target >= 0:
                time_based_pos = self._time_to_scroll_pos(effective_time)
                if time_based_pos < self._click_jump_target:
                    # 音频还没追上 → 保持点击位置
                    self.current_position = self._click_jump_target
                    self.play_time = effective_time / 1000.0
                else:
                    # 音频已追上 → 清除标记，恢复正常模式
                    self.current_position = time_based_pos
                    self.play_time = effective_time / 1000.0
                    self._click_jump_target = -1.0  # 清除跳转目标
            else:
                self.current_position = self._time_to_scroll_pos(effective_time)
                self.play_time = effective_time / 1000.0

            # 进度百分比基于音频时间
            total_dur = getattr(self, '_total_audio_duration_ms', 0) or 1
            pct = min((effective_time / total_dur) * 100, 100)

            # 循环检查(时间模式)
            should_loop = self._check_loop_condition()
            if should_loop:
                if self.loop_config.loop_type == 'all':
                    self.current_position = 0; self.play_time = 0
                    if self.gtp_player:
                        self.gtp_player.seek(0)
                elif self.loop_config.loop_type == 'region':
                    start_pct = self.loop_config.start_position
                    target_time = total_dur * start_pct / 100
                    self.current_position = self.total_scroll_distance * start_pct / 100
                    if self.gtp_player:
                        self.gtp_player.seek(target_time)
            elif effective_time >= total_dur:
                self.current_position = self.total_scroll_distance
                self.stop_playback(reset_position=True)  # 播放结束，重置位置

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
        
        self.position_label.setText(I18n.t("control_panel.position_label", pct=f"{pct:.1f}"))
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
        """
        if not self.images:return
        # 必须使用 display_widget 的宽度(与 paintEvent 绘制时一致)，而非 DisplayWindow 的宽度
        ww=self.display_widget.width()
        total=0
        for img in self.images:
            if not img.isNull():
                sw=ww-20;ratio=img.width()>0 and sw/img.width() or 1
                total+=img.height()*ratio+5
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
        self.position_label.setText(I18n.t("control_panel.position_label", pct=f"{pct:.1f}"))
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
        
        原理: 遍历所有图片计算累积高度，确定当前滚动位置落在哪一页。
              此操作O(n)且涉及浮点乘法，在_tick中每3帧调用一次以减少CPU开销。
        """
        if not (hasattr(self,'page_input') and self.images and len(self.images)>1):
            return
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
        """A-B区域选择"""
        self.loop_config.start_position=start
        self.loop_config.end_position=end
        self.progress_bar.set_region(start,end)
        self.ab_info_label.setText(f"A-B: {start:.1f}% - {end:.1f}%")

    def _on_loop_mode_changed(self,idx:int)->None:
        """循环模式改变"""
        modes=['none','all','region']
        self.loop_config.loop_type=modes[idx]
        self.loop_config.is_enabled=(idx>0)
        if idx==2 and self.loop_config.end_position<self.loop_config.start_position:
            self.ab_info_label.setText(I18n.t("ab_info.ab_set_both"))
        elif idx==0:
            self.progress_bar.clear_region()
            self.ab_info_label.setText("")

    def _set_ab_point(self,point:str)->None:
        """设置A/B点"""
        if self.total_scroll_distance>0:
            pct=(self.current_position/self.total_scroll_distance)*100
        else:
            pct=0
        if point=='a':
            self.loop_config.start_position=pct
        else:
            self.loop_config.end_position=pct
        self.progress_bar.set_region(self.loop_config.start_position,self.loop_config.end_position)
        self.ab_info_label.setText(f"A-B: {self.loop_config.start_position:.1f}% - {self.loop_config.end_position:.1f}%")

    def _clear_ab_points(self)->None:
        """清除AB点"""
        self.loop_config.start_position=0
        self.loop_config.end_position=100
        self.progress_bar.clear_region()
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
        
        原理: 深拷贝当前annotations列表存入undo_stack，
              同时清空redo_stack(新操作使重做历史失效)。
        
        使用场景: 所有修改annotations的操作前调用此方法:
                  - 双击画布添加/编辑标注
                  - 管理器中新增/编辑/删除/清空标注
        """
        snapshot = [Annotation(**asdict(a)) for a in self.annotations]
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()  # 新操作清空重做栈
        # 限制深度防止内存膨胀
        if len(self._undo_stack) > self._UNDO_MAX_DEPTH:
            self._undo_stack.pop(0)

    def _anno_undo(self)->None:
        """
        Ctrl+Z 全局撤销 - 回退到上一个标注状态
        
        操作流程:
          1. 当前状态 → 移入 redo_stack(可被Ctrl+Y恢复)
          2. undo_stack 弹出上一个状态 → 设为当前 annotations
          3. 刷新显示 + 自动保存
        """
        if not self._undo_stack:
            return
        # 当前状态存入重做栈
        redo_snap = [Annotation(**asdict(a)) for a in self.annotations]
        self._redo_stack.append(redo_snap)
        # 恢复上一个状态
        prev = self._undo_stack.pop()
        self.annotations = [Annotation(**asdict(a)) for a in prev]
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
        
        操作流程:
          1. 当前状态 → 存入 undo_stack
          2. redo_stack 弹出状态 → 设为当前 annotations
          3. 刷新显示 + 自动保存
        """
        if not self._redo_stack:
            return
        # 当前状态存入撤销栈
        undo_snap = [Annotation(**asdict(a)) for a in self.annotations]
        self._undo_stack.append(undo_snap)
        # 恢复重做状态
        nxt = self._redo_stack.pop()
        self.annotations = [Annotation(**asdict(a)) for a in nxt]
        # 刷新UI
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()
        # 同步管理器(如果打开着)
        if hasattr(self, '_ann_manager') and self._ann_manager:
            self._ann_manager.annotations = self.annotations
            self._ann_manager._populate_list()

    # ========== A4导出(PNG/PDF，含标注，支持分轨/分页) ==========

    def _export_to_a4(self)->None:
        """
        导出谱面(含标注)为A4尺寸的PNG或PDF
        
        功能:
          - 格式: PNG(每页一图) / PDF(单文件多页)
          - 分轨: GTP文件可选指定轨道导出，或"全部轨道"按顺序拼接
          - 分页: 可选单页、页数范围、全部页面
          - 标注: 完整渲染所有标注(颜色/字体/大小)
        
        原理:
          1. 弹出自定义导出对话框(ExportDialog)让用户选择格式/轨道/页码范围
          2. 收集需要导出的图片列表(GTP多轨时按需重新渲染各轨)
          3. 按A4尺寸(2480×3508px @300dpi)逐页/逐轨绘制到画布
          4. PNG: 每页保存独立文件; PDF: 单文件多页
        """
        if not self.images or all(img.isNull() for img in self.images):
            QMessageBox.warning(self, I18n.t("messages.export_no_content"), I18n.t("messages.export_no_content_msg"))
            return

        # 弹出导出对话框
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
        fmt = dlg.format_choice  # "png" 或 "pdf"
        track_mode = dlg.track_mode  # "current" | "all" | list[int]
        page_mode = dlg.page_mode    # "all" | ("range", start, end)
        save_path = dlg.save_path

        try:
            # === Step 1: 收集要导出的图片和标注 ===
            export_items = self._collect_export_data(track_mode, page_mode)
            # export_items: List[ExportItem] = [(images_list, annotations_list, track_label), ...]

            if not export_items or not any(item[0] for item in export_items):
                QMessageBox.warning(self, I18n.t("messages.export_no_content"), I18n.t("messages.export_no_data"))
                return

            # === Step 2: 执行导出 ===
            total_files = 0
            for item_idx, (imgs, anns, label) in enumerate(export_items):
                if not imgs:
                    continue

                # 构建此轨/部分的保存路径
                if len(export_items) > 1 or label:
                    base, ext = os.path.splitext(save_path)
                    part_path = f"{base}_{label}{ext}"
                else:
                    part_path = save_path

                if fmt == "pdf":
                    self._render_to_a4_pdf_v2(part_path, imgs, anns)
                    total_files += 1
                else:
                    n = self._render_to_a4_png_v2(part_path, imgs, anns)
                    total_files += n

            fmt_name = "PDF" if fmt == "pdf" else "PNG"
            mode_desc = ""
            if track_mode == "all":
                mode_desc = I18n.t("messages.export_mode_all", count=self.gtp_track_combo.count())
            elif isinstance(track_mode, list):
                mode_desc = I18n.t("messages.export_mode_tracks", tracks=', '.join(str(t+1) for t in track_mode))

            QMessageBox.information(
                self, I18n.t("messages.export_success"),
                I18n.t("messages.export_success_msg", fmt=fmt_name, path=save_path, count=total_files, mode=mode_desc)
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, I18n.t("messages.export_fail"), I18n.t("messages.export_fail_msg", error=str(e)))

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
            p.setPen(QColor("#999999")); p.setFont(QFont("Arial",9))
            p.drawText(QRect(0, a4_h - 25, draw_w, 25), Qt.AlignCenter, f"- {page_idx+1}/{n_pages} -")
            p.end()

            path = file_path if n_pages == 1 else f"{os.path.splitext(file_path)[0]}_p{page_idx+1}{os.path.splitext(file_path)[1]}"
            if not canvas.save(path, "PNG"):
                raise IOError(f"PNG保存失败: {path}")
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
            p.setPen(QColor("#999999")); p.setFont(QFont("Arial",9))
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

    # ========== 键盘事件 ==========

    def keyPressEvent(self,event:QKeyEvent)->None:
        """键盘快捷键 - 含全局标注撤销/重做(Ctrl+Z / Ctrl+Y)"""
        try:
            # === 标注撤销/重做(优先于其他快捷键) ===
            if event.modifiers() & Qt.ControlModifier:
                if event.key() == Qt.Key_Z:       # Ctrl+Z: 撤销标注
                    self._anno_undo(); return
                elif event.key() == Qt.Key_Y:      # Ctrl+Y: 重做标注
                    self._anno_redo(); return
        
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
                self.speed_spin.setValue(min(700,self.speed_spin.value()+25))
            elif event.key()==Qt.Key_Escape:        # ESC: 关闭
                self.close()
            super().keyPressEvent(event)
        except Exception:
            pass

    def showEvent(self,event:QShowEvent)->None:
        """窗口显示事件"""
        super().showEvent(event)
        self._calculate_total_distance()

    def resizeEvent(self,event:QResizeEvent)->None:
        """窗口大小改变"""
        super().resizeEvent(event)
        self._calculate_total_distance()


# ========== 导出设置对话框 ==========

class ExportDialog(QDialog):
    """
    导出设置对话框 - 选择格式/轨道/页码范围
    功能: PNG(每页一图)或PDF(单文件多页); GTP可选轨道; 可选页码范围
    """

    def __init__(self, parent, src_name:str, is_gtp:bool,
                 gtp_track_count:int, current_track:int, total_pages:int):
        super().__init__(parent)
        self.src_name = src_name; self.is_gtp = is_gtp
        self.gtp_track_count = gtp_track_count; self.current_track = current_track
        self.total_pages = total_pages
        self.format_choice = "png"; self.track_mode = "current"
        self.page_mode = "all"; self.save_path = ""
        self.setWindowTitle(I18n.t("export_dialog.window_title")); self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self)->None:
        lo = QVBoxLayout(self); lo.setSpacing(12)
        # 格式
        fg = QGroupBox(I18n.t("export_dialog.format_group")); fl = QHBoxLayout(fg)
        self.fmt_png = QRadioButton(I18n.t("export_dialog.fmt_png")); self.fmt_pdf = QRadioButton(I18n.t("export_dialog.fmt_pdf"))
        self.fmt_png.setChecked(True); fl.addWidget(self.fmt_png); fl.addWidget(self.fmt_pdf); lo.addWidget(fg)
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
        self.format_choice = "pdf" if self.fmt_pdf.isChecked() else "png"
        if self.is_gtp and self.gtp_track_count > 1:
            if self.tk_all and self.tk_all.isChecked(): self.track_mode = "all"
            elif self.tk_sel and self.tk_sel.isChecked():
                self.track_mode = [i for i,c in enumerate(self.tks) if c.isChecked()]
                if not self.track_mode: QMessageBox.warning(self,"提示",I18n.t("messages.select_track_hint")); return
            else: self.track_mode = "current"
        else: self.track_mode = "current"
        if hasattr(self,'pg_rng') and self.pg_rng.isChecked():
            s,e = self._ps.value(), self._pe.value()
            if s > e: s,e = e,s
            self.page_mode = ("range", s, e)
        else: self.page_mode = "all"
        ext = ".pdf" if self.format_choice=="pdf" else ".png"
        fp,_ = QFileDialog.getSaveFileName(self,I18n.t("export_dialog.save_title"),f"{os.path.splitext(self.src_name)[0]}_annotated{ext}",
                                           f"{I18n.t('export_dialog.file_filter_pdf') if self.format_choice=='pdf' else I18n.t('export_dialog.file_filter_png')} (*{ext})")
        if not fp: return
        self.save_path = fp; super().accept()


# ============================================================
# 设置窗口 - 文件浏览与配置
# ============================================================

class SettingsWindow(QMainWindow):
    """
    设置主窗口
    功能: 文件夹浏览、文件列表、速度配置、启动显示窗口
    """

    def __init__(self):
        super().__init__()
        self.setWindowIcon(get_app_icon())  # 设置窗口图标
        self.display_window:Optional[DisplayWindow]=None
        self.current_directory:str=""
        self.is_loading:bool=False
        self._loaded_files:List[Tuple]=[]

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

        # 文件夹选择
        folder_layout=QHBoxLayout()
        self.folder_label=QLabel(I18n.t("settings_window.folder_not_selected"))
        self.folder_button=QPushButton(I18n.t("settings_window.folder_btn"))
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_button)
        main_layout.addLayout(folder_layout)

        # 语言选择
        lang_layout=QHBoxLayout()
        lang_layout.addWidget(QLabel(I18n.t("settings_window.language_label")))
        self.lang_combo=QComboBox()
        for code,name in I18n.available_languages():
            self.lang_combo.addItem(name, code)
        # 从配置恢复语言选择
        saved_lang=self._load_saved_language()
        idx=self.lang_combo.findData(saved_lang)
        if idx>=0: self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        main_layout.addLayout(lang_layout)

        # 主题选择 (v2.0新增)
        theme_layout=QHBoxLayout()
        theme_layout.addWidget(QLabel(I18n.t("settings_window.theme_label")))
        self.theme_combo=QComboBox()
        for name, display_name in ThemeManager.available_themes():
            self.theme_combo.addItem(display_name, name)
        # 从配置恢复主题选择
        saved_theme=self._load_saved_theme()
        idx=self.theme_combo.findData(saved_theme)
        if idx>=0: self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        main_layout.addLayout(theme_layout)

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

        main_layout.addWidget(file_list_label)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.file_list)

    def _apply_theme(self)->None:
        """应用当前主题样式到SettingsWindow - 从ThemeManager读取当前主题配色"""
        t = ThemeManager.current()
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{background-color:{t['bg_primary']};color:{t['text_primary']};
                font-family:'Microsoft YaHei','Segoe UI',sans-serif;}}
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

    def _load_config_and_restore(self)->None:
        """加载配置并恢复状态 - 包含目录有效性检查"""
        try:
            self.load_config()
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
        """加载配置文件"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE,'r',encoding='utf-8') as f:
                    cfg=json.load(f)
                    self.last_folder=cfg.get('last_folder','')
            else:
                self.last_folder=''
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.last_folder=''

    def save_config(self)->None:
        """保存配置文件（包含主题设置）"""
        try:
            cfg={'last_folder':self.current_directory,
                 'language':I18n.current_language(),
                 'theme':ThemeManager.current_name()}  # v2.0新增: 保存主题
            os.makedirs(os.path.dirname(CONFIG_FILE),exist_ok=True)
            with open(CONFIG_FILE,'w',encoding='utf-8') as f:
                json.dump(cfg,f,ensure_ascii=False,indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def _load_saved_language(self)->str:
        """从配置文件加载已保存的语言设置"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE,'r',encoding='utf-8') as f:
                    cfg=json.load(f)
                    return cfg.get('language','zh_CN')
        except Exception:
            pass
        return 'zh_CN'

    def _on_language_changed(self,index:int)->None:
        """语言切换处理 - 切换语言并刷新UI"""
        lang_code=self.lang_combo.itemData(index)
        if not lang_code or lang_code==I18n.current_language():
            return
        # 执行语言切换
        I18n.set_language(lang_code)
        # 保存语言设置
        self.save_config()
        # 提示用户重启应用以完全生效(部分静态文本需重建窗口才能更新)
        QMessageBox.information(self,I18n.t("settings_window.language_switch_title"),
                                I18n.t("settings_window.language_switch_msg"))

    def _load_saved_theme(self)->str:
        """从配置文件加载已保存的主题设置"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE,'r',encoding='utf-8') as f:
                    cfg=json.load(f)
                    return cfg.get('theme','dark')
        except Exception:
            pass
        return 'dark'

    def _on_theme_changed(self, index: int)->None:
        """
        主题切换处理 - 切换深色/浅色主题并实时刷新所有窗口
        
        原理:
          1. 从下拉框获取目标主题名(dark/light)
          2. 调用 ThemeManager.set_theme() 切换全局配色
          3. 发射 theme_changed 信号通知所有窗口刷新样式
          4. 保存主题设置到配置文件(持久化)
          5. 如果有打开的DisplayWindow，同步刷新其GTP渲染主题
        """
        theme_name = self.theme_combo.itemData(index)
        if not theme_name or theme_name == ThemeManager.current_name():
            return

        # 切换全局主题
        if not ThemeManager.set_theme(theme_name):
            return

        # 刷新设置窗口自身样式
        self._apply_theme()

        # 刷新已打开的DisplayWindow（如果存在）
        if self.display_window and hasattr(self.display_window, '_refresh_theme'):
            self.display_window._refresh_theme()

        # 保存设置
        self.save_config()

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

        for name,fpath,is_dir in self._loaded_files:
            item=QListWidgetItem(name)
            item.setData(Qt.UserRole,fpath);item.setData(Qt.UserRole+1,is_dir)
            if is_dir:item.setToolTip(f"进入: {name}")
            else:item.setToolTip(fpath)
            self.file_list.addItem(item);self.original_items.append((name,fpath,is_dir))

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
          Linux:   xdg-open 或 nautilus --select "路径"
        
        修复: 
          - 确保传入绝对路径(相对路径会导致explorer打开默认文档文件夹)
          - 使用shell=True避免PowerShell参数解析问题
          - 路径不存在时给出明确提示
        
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
            
            if platform.system() == 'Windows':
                # Windows: 使用shell=True确保explorer正确解析/select参数
                # 注意: /select和路径之间不能有空格，否则explorer会忽略select参数
                subprocess.run(f'explorer /select,"{abs_path}"', shell=True, check=False)
            elif platform.system() == 'Linux':
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
# 程序入口
# ============================================================

if __name__ == '__main__':
    # 确保配置和标注目录存在
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    os.makedirs(ANNOTATION_DIR, exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式作为基础，配合自定义深色/浅色主题
    app.setWindowIcon(get_app_icon())  # 设置全局应用图标(任务栏图标/窗口默认图标)

    # 初始化国际化系统 - 从配置文件加载已保存的语言设置
    saved_lang='zh_CN'
    saved_theme='dark'  # v2.0新增: 默认深色主题
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE,'r',encoding='utf-8') as f:
                cfg=json.load(f)
                saved_lang=cfg.get('language','zh_CN')
                saved_theme=cfg.get('theme','dark')  # v2.0新增: 加载保存的主题
    except Exception:
        pass
    I18n.set_language(saved_lang)
    
    # v2.0新增: 应用保存的主题（在创建窗口之前）
    ThemeManager.set_theme(saved_theme)

    settings = SettingsWindow()
    sys.exit(app.exec_())
