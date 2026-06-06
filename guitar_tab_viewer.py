# -*- coding: utf-8 -*-
"""
============================================================
文件名: guitar_tab_viewer.py
功能描述: 万能吉他谱查看器(TAB Score Viewer) - 支持多格式查看、播放、标注
         支持格式: PNG, JPG, JPEG, WEBP(图片), PDF(文档), GP3/GP4/GP5/GPX(GTP吉他谱)

         核心功能:
           1. 多格式吉他谱查看与自动滚动播放
           2. 可拖动进度条 + 循环播放(不循环/全局循环/区域A-B循环)
           3. 速度曲线编辑器 - 贝塞尔曲线可视化编辑，含预设模板(图片/PDF格式)
           4. 谱面文本标注系统 - 双击任意位置添加演奏技巧说明，支持样式自定义
           5. 标注管理器 - 批量管理，Ctrl+Z撤销/Ctrl+Y重做(最多50步)
           6. 页码导航 - PDF/多图模式底部页码输入框直接跳转
           7. 鼠标滚轮滚动 - 支持Ctrl加速/Shift精细控制
           8. 深色主题UI + 自定义组件(按钮/滑块/进度条)
           9. 键盘快捷键 - 空格播放暂停/方向键调速/ESC关闭
          10. GTP文件完整渲染 - 基于gtp_engine库解析并渲染为六线谱图像
          11. 右键打开文件位置 - 文件列表右键菜单支持在资源管理器中定位文件

创建日期: 2026-06-06
最后修改: 2026-06-06

依赖库:
  - PyQt5 >= 5.15     # GUI框架(窗口/控件/信号槽/绘图)
  - PyMuPDF >= 1.23   # PDF解析与页面渲染为图片 (开源项目: Artifex Software)
  - Pillow >= 10.0    # 图片处理(PNG/JPG/WEBP解码) (开源项目: Python Imaging Library)
  - guitarpro >= 0.11 # Guitar Pro文件解析 (开源项目: pyguitarpro) - GTP渲染功能依赖

技术栈: Python 3.8+ / PyQt5 / PyMuPDF / Pillow / guitarpro(gtp_engine)
兼容性: Windows / Linux / Docker (所有路径使用相对路径)

项目结构:
  guitar_tab_viewer.py   - 主程序(本文件)
  gtp_engine/            - GTP渲染引擎库(解析+渲染六线谱)
  config/settings.json   - 用户配置(运行时自动生成)
  data/annotations/      - 标注数据存储(JSON格式)
  readme/                - 项目文档目录
============================================================
"""

import sys
import os
import json
import math
import copy
import uuid
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# Qt GUI组件
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QListWidget,
    QListWidgetItem, QMenu, QAction, QMessageBox, QLineEdit,
    QDialog, QTextEdit, QDialogButtonBox, QGroupBox, QCheckBox,
    QSpinBox, QColorDialog, QFontDialog, QSplitter, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QSizePolicy, QToolTip,
    QProgressBar, QComboBox, QTabWidget
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QPen, QColor, QFont, QIcon,
    QImage, QCursor, QPainterPath, QLinearGradient, QRadialGradient,
    QMouseEvent, QKeyEvent, QWheelEvent, QResizeEvent, QShowEvent,
    QKeySequence, QPalette, QBrush, QTransform
)
from PyQt5.QtCore import (
    Qt, QTimer, QRect, QSize, QPoint, QRunnable, QThreadPool,
    pyqtSignal, QObject, QEasingCurve, QPropertyAnimation,
    QRectF, QPointF, pyqtProperty
)

# 第三方库
import fitz  # PyMuPDF - PDF解析 (开源库)
from PIL import Image as PILImage  # Pillow - 图片处理(含WEBP) (开源库)


# ============================================================
# 配置常量
# ============================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "settings.json")
ANNOTATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "annotations")

# 支持的文件扩展名
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
SUPPORTED_PDF_EXTENSIONS = ('.pdf',)
SUPPORTED_GTP_EXTENSIONS = ('.gp3', '.gp4', '.gp5', '.gpx', '.gtp')
SUPPORTED_ALL_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_PDF_EXTENSIONS + SUPPORTED_GTP_EXTENSIONS

# UI颜色主题 - 深色音乐风格
THEME_COLORS = {
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
    """速度曲线控制点"""
    position: float = 0.0   # 位置百分比 (0-100)
    speed: float = 50.0     # 速度值


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
        
        原理: 使用 gtp_engine 库（基于 PyGuitarPro）完整解析 GTP 文件，
              并通过 QPainter 渲染为六线谱图像。
              解析流程: .gp文件 → PyGuitarPro → GTPSong中介模型 → TabRenderer → QPixmap列表
        
        依赖库:
          - guitarpro >= 0.11   # Guitar Pro 文件解析（开源项目: pyguitarpro）
          - gtp_engine           # 本项目内置的渲染引擎库
        """
        images = []
        try:
            # 使用 gtp_engine 进行完整解析和渲染
            from gtp_engine.renderer import TabRenderer
            
            renderer = TabRenderer()
            
            # 进度报告：开始加载
            self.signals.progress.emit(10)
            
            # 解析并渲染（内部调用 parse_gtp + render）
            pixmaps = renderer.render_from_file(self.file_path)
            
            # 进度报告：完成
            self.signals.progress.emit(100)
            
            images = pixmaps
            
        except ImportError as e:
            # gtp_engine 或 guitarpro 未安装时，回退到信息展示图
            info_pixmap = self._create_gtp_info_image(
                f"GTP引擎依赖缺失:\n{str(e)}\n\n请安装: pip install PyGuitarPro"
            )
            images.append(info_pixmap)
        except Exception as e:
            # 其他错误时，显示错误信息和回退预览
            error_pixmap = self._create_error_image(f"GTP加载失败:\n{str(e)}")
            images.append(error_pixmap)
        
        return images

    def _create_gtp_info_image(self, message: str) -> QPixmap:
        """创建GTP信息/错误展示图（当gtp_engine不可用时回退显示）"""
        width, height = 800, 500
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(THEME_COLORS['bg_surface']))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 标题
        painter.setPen(QColor(THEME_COLORS['primary']))
        title_font = QFont("Microsoft YaHei", 26, QFont.Bold)
        painter.setFont(title_font)
        filename = os.path.basename(self.file_path)
        painter.drawText(QRect(50, 40, 700, 60), Qt.AlignCenter, f"Guitar Pro 文件: {filename}")

        # 信息文本
        painter.setPen(QColor(THEME_COLORS['text_primary']))
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
        painter.setPen(QPen(QColor(THEME_COLORS['primary']), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(30, 30, width - 60, height - 60, 15, 15)
        painter.end()
        return pixmap


# ============================================================
# 自定义UI组件
# ============================================================

class ModernButton(QPushButton):
    """
    现代化按钮组件
    功能: 带悬停效果、阴影、圆角的按钮基类
    """

    def __init__(self, text: str, color_key: str = 'primary', parent=None):
        super().__init__(text, parent)
        self.color_key = color_key
        self._setup_style()

    def _setup_style(self) -> None:
        """初始化按钮样式 - 深色主题配色"""
        color = THEME_COLORS.get(self.color_key, THEME_COLORS['primary'])
        hover_color = THEME_COLORS.get(f'{self.color_key}_hover', color)

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
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


class ModernSlider(QSlider):
    """
    现代化滑块组件
    功能: 继承QSlider，应用深色主题样式
    参数:
      orientation: 滑块方向(水平/垂直)
      color_key:   主题色键名(对应THEME_COLORS)
    """

    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal,
                 color_key: str = 'primary', parent=None):
        super().__init__(orientation, parent)
        self.color_key = color_key
        self._setup_style()

    def _setup_style(self) -> None:
        """初始化滑块样式 - 深色主题配色"""
        color = THEME_COLORS.get(self.color_key, THEME_COLORS['primary'])
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {THEME_COLORS['bg_surface']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                border: 2px solid {THEME_COLORS['bg_primary']};
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
                background: {THEME_COLORS['bg_surface']};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {color};
                border: 2px solid {THEME_COLORS['bg_primary']};
                height: 18px;
                margin: 0 -7px;
                border-radius: 9px;
            }}
            QSlider::add-page:vertical {{
                background: {color};
                border-radius: 3px;
            }}
        """)


class ProgressBarSlider(QWidget):
    """
    自定义进度条滑块组件
    功能: 显示播放进度(0-100%)，支持拖动跳转，支持A-B区域标记
    操作: 左键拖动=跳转, Ctrl+点击=A点, Shift+点击=B点
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

        rect = self.rect()
        bar_height = 6
        bar_y = (rect.height() - bar_height) // 2
        bar_rect = QRect(8, bar_y, rect.width() - 16, bar_height)

        # 背景轨道
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(THEME_COLORS['bg_surface']))
        painter.drawRoundedRect(bar_rect, 3, 3)

        # A-B循环区域高亮
        if self._region_start >= 0 and self._region_end > self._region_start:
            rx = bar_rect.x() + int(bar_rect.width() * self._region_start / 100)
            rw = int(bar_rect.width() * (self._region_end - self._region_start) / 100)
            painter.setBrush(QColor(THEME_COLORS['accent'] + "50"))
            painter.drawRoundedRect(rx, bar_y, max(rw, 1), bar_height, 3, 3)

        # 已播放进度
        pw = int(bar_rect.width() * self._position / 100)
        if pw > 0:
            gradient = QLinearGradient(bar_rect.left(), 0, bar_rect.left() + pw, 0)
            gradient.setColorAt(0, QColor(THEME_COLORS['primary']))
            gradient.setColorAt(1, QColor(THEME_COLORS['primary_light']))
            painter.setBrush(gradient)
            painter.drawRoundedRect(bar_rect.x(), bar_y, pw, bar_height, 3, 3)

        # 滑块手柄
        hx = bar_rect.x() + int(bar_rect.width() * self._position / 100)
        hy = rect.height() // 2
        painter.setPen(QPen(QColor('#ffffff'), 2))
        painter.setBrush(QColor(THEME_COLORS['primary']))
        painter.drawEllipse(QPoint(hx, hy), 9, 9)

        # 位置文字
        painter.setPen(QColor(THEME_COLORS['text_muted']))
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
        self.setWindowTitle("速度曲线编辑器")
        self.setMinimumSize(680, 480)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {THEME_COLORS['bg_primary']}; }}
            QLabel {{ color: {THEME_COLORS['text_primary']}; font-family: 'Microsoft YaHei'; }}
            QGroupBox {{ color: {THEME_COLORS['text_primary']}; border: 1px solid {THEME_COLORS['border']};
                         border-radius: 8px; margin-top: 10px; padding-top: 10px; font-weight: bold; }}
            QCheckBox {{ color: {THEME_COLORS['text_primary']}; }}
            QPushButton {{ background-color: {THEME_COLORS['primary']}; color: white; border: none;
                          border-radius: 6px; padding: 6px 14px; font-family: 'Microsoft YaHei'; }}
            QPushButton:hover {{ background-color: {THEME_COLORS['primary_hover']}; }}
        """)

        layout = QVBoxLayout(self)

        # 启用开关
        top_row = QHBoxLayout()
        self.enable_check = QCheckBox("启用速度曲线模式")
        self.enable_check.setChecked(self.curve_config.is_enabled)
        self.enable_check.stateChanged.connect(self._on_enable_changed)
        top_row.addWidget(self.enable_check)
        top_row.addStretch()
        layout.addLayout(top_row)

        # 曲线画布
        canvas_group = QGroupBox("速度曲线 (点击添加控制点，拖动调整，右键删除)")
        canvas_layout = QVBoxLayout(canvas_group)
        self.canvas_widget = _SpeedCurveCanvas(self, self.curve_config)
        self.canvas_widget.setMinimumHeight(280)
        self.canvas_widget.curveChanged.connect(self._on_curve_changed)
        canvas_layout.addWidget(self.canvas_widget)
        layout.addWidget(canvas_group)

        # 预设按钮
        btn_group = QGroupBox("预设曲线")
        btn_layout = QHBoxLayout(btn_group)
        for name, fn in [("线性", self._preset_linear), ("渐入", self._preset_ease_in),
                         ("渐出", self._preset_ease_out), ("渐入渐出", self._preset_ease_in_out)]:
            btn = QPushButton(name)
            btn.clicked.connect(fn)
            btn.setMaximumWidth(75)
            btn_layout.addWidget(btn)
        clear_btn = QPushButton("清除全部")
        clear_btn.setStyleSheet(f"background-color: {THEME_COLORS['danger']};")
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)
        layout.addWidget(btn_group)

        # 说明
        hint = QLabel(
            "提示: X轴=播放进度(%) | Y轴=速度值(ms)\n"
            "Y值越小=播放越快。适合制作渐入/渐出等变速效果用于练习。"
        )
        hint.setStyleSheet(f"color: {THEME_COLORS['text_muted']}; font-size: 11px;")
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
    """速度曲线绘图画布内部组件"""

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

        rect = self.rect()
        pad = 40
        draw_rect = QRect(pad, pad, rect.width() - 2*pad, rect.height() - 2*pad)
        painter.fillRect(rect, QColor(THEME_COLORS['bg_surface']))

        # 网格
        painter.setPen(QPen(QColor(THEME_COLORS['border']), 1, Qt.DotLine))
        for pct in [25, 50, 75]:
            x = draw_rect.x() + int(draw_rect.width()*pct/100)
            painter.drawLine(x, draw_rect.top(), x, draw_rect.bottom())
        for spd in [30, 80, 130]:
            y = draw_rect.bottom() - int(draw_rect.height()*spd/160)
            painter.drawLine(draw_rect.left(), y, draw_rect.right(), y)

        # 坐标标签
        painter.setPen(QColor(THEME_COLORS['text_muted']))
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
            painter.fillPath(path, QColor(THEME_COLORS["primary"]+"35"))

            pen = QPen(QColor(THEME_COLORS['primary']), 2)
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
            painter.setPen(QPen(QColor(THEME_COLORS['accent']) if is_sel else QColor(THEME_COLORS['primary']), 2))
            painter.setBrush(QColor(THEME_COLORS['accent_light']) if is_sel else QColor(THEME_COLORS['primary']))
            painter.drawEllipse(QPoint(px, py), 8 if is_sel else 6, 8 if is_sel else 6)

        painter.setPen(QPen(QColor(THEME_COLORS['border']), 1))
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


class AnnotationEditDialog(QDialog):
    """单个标注编辑对话框"""

    def __init__(self, parent=None, annotation: Annotation=None):
        super().__init__(parent)
        self.annotation = annotation or Annotation(
            id=f"ann_{uuid.uuid4().hex[:8]}", x=0.1, y=0.1,
            text="双击谱面可快速添加标注"
        )
        self._temp_color=self.annotation.color
        self.init_ui()

    def init_ui(self)->None:
        self.setWindowTitle("编辑标注"); self.setFixedSize(420,360)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {THEME_COLORS['bg_primary']}; }}
            QLabel {{ color: {THEME_COLORS['text_primary']}; font-family: 'Microsoft YaHei'; }}
            QTextEdit {{ background-color: {THEME_COLORS['bg_surface']}; color: {THEME_COLORS['text_primary']};
                        border: 1px solid {THEME_COLORS['border']}; border-radius: 6px; padding: 6px; }}
            QSpinBox {{ background-color: {THEME_COLORS['bg_surface']}; color: {THEME_COLORS['text_primary']};
                        border: 1px solid {THEME_COLORS['border']}; border-radius: 4px; padding: 4px; }}
            QCheckBox {{ color: {THEME_COLORS['text_primary']}; }}
            QPushButton {{ background-color: {THEME_COLORS['primary']}; color: white; border: none;
                           border-radius: 6px; padding: 8px 20px; font-family: 'Microsoft YaHei'; }}
            QPushButton:hover {{ background-color: {THEME_COLORS['primary_hover']}; }}
        """)
        layout=QVBoxLayout(self)
        pg=QGroupBox("位置坐标"); pl=QHBoxLayout(pg)
        pl.addWidget(QLabel(f"X: {self.annotation.x:.1%}  Y: {self.annotation.y:.1%}")); layout.addWidget(pg)
        tg=QGroupBox("标注内容"); tl=QVBoxLayout(tg)
        self.text_edit=QTextEdit(); self.text_edit.setPlainText(self.annotation.text)
        self.text_edit.setPlaceholderText("输入演奏技巧说明..."); tl.addWidget(self.text_edit); layout.addWidget(tg)
        fg=QGroupBox("字体"); fl=QHBoxLayout(fg)
        fl.addWidget(QLabel("大小:")); self.font_size_spin=QSpinBox()
        self.font_size_spin.setRange(8,72); self.font_size_spin.setValue(self.annotation.font_size); fl.addWidget(self.font_size_spin)
        self.bold_check=QCheckBox("加粗"); self.bold_check.setChecked(self.annotation.is_bold); fl.addWidget(self.bold_check)
        fl.addStretch(); layout.addWidget(fg)
        cg=QGroupBox("颜色"); cl=QHBoxLayout(cg)
        self.color_btn=QPushButton("选择颜色"); self.color_btn.clicked.connect(self._pick_color)
        self.color_btn.setStyleSheet(f"background-color:{self.annotation.color};color:white;")
        cl.addWidget(self.color_btn); cl.addStretch(); layout.addWidget(cg)
        bbox=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept); bbox.rejected.connect(self.reject); layout.addWidget(bbox)

    def _pick_color(self)->None:
        c=QColorDialog.getColor(QColor(self._temp_color),self,"选择标注颜色")
        if c.isValid(): self._temp_color=c.name(); self.color_btn.setStyleSheet(f"background-color:{self._temp_color};color:white;")

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
    """
    annotationsChanged=pyqtSignal(list)

    def __init__(self,parent=None,annotations:List[Annotation]=None):
        super().__init__(parent); self.annotations=annotations or []
        # 撤销/重做栈: 每次修改前保存快照
        self._undo_stack:List[List[Annotation]]=[]   # 撤销栈(可回退的状态)
        self._redo_stack:List[List[Annotation]]=[]   # 重做栈(已撤销可恢复)
        self.init_ui()

    def init_ui(self)->None:
        self.setWindowTitle("标注管理器"); self.setMinimumSize(550,400)
        self.setStyleSheet(f"""
            QDialog{{background-color:{THEME_COLORS['bg_primary']};}}
            QLabel{{color:{THEME_COLORS['text_primary']};font-family:'Microsoft YaHei';}}
            QListWidget{{background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};
                        border:1px solid{THEME_COLORS['border']};border-radius:6px;}}
            QListWidget::item:selected{{background-color:{THEME_COLORS['primary']};}}
            QListWidget::item:hover{{background-color:{THEME_COLORS['bg_card']};}}
            QPushButton{{background-color:{THEME_COLORS['primary']};color:white;border:none;border-radius:6px;padding:7px14px;}}
            QPushButton:hover{{background-color:{THEME_COLORS['primary_hover']};}}
            QPushButton#delBtn{{background-color:{THEME_COLORS['danger']};}}
            QPushButton#delBtn:hover{{background-color:#DC2626;}}
        """)
        layout=QVBoxLayout(self)
        title=QLabel(f"标注列表({len(self.annotations)}个)")
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{THEME_COLORS['primary_light']};")
        layout.addWidget(title)
        self.list_widget=QListWidget(); self._populate_list()
        self.list_widget.itemDoubleClicked.connect(self._edit_item); layout.addWidget(self.list_widget)
        bl=QHBoxLayout()
        for txt,slot,st in[("+ 新增",self._add_new,""),("编辑",lambda:self._edit_item(self.list_widget.currentItem()), ""),
                             ("删除",self._delete_item,"#delBtn"),("清空",self._clear_all,"#delBtn")]:
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

    # ========== 撤销/重做核心方法 ==========
    def _save_snapshot(self)->None:
        """修改前保存当前状态快照到撤销栈"""
        snapshot=[Annotation(**asdict(a)) for a in self.annotations]
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()  # 新操作清空重做栈
        # 限制撤销深度避免内存膨胀
        if len(self._undo_stack)>50: self._undo_stack.pop(0)

    def _undo(self)->None:
        """Ctrl+Z 撤销 - 回退到上一个状态"""
        if not self._undo_stack: return
        # 当前状态存入重做栈
        redo_snap=[Annotation(**asdict(a)) for a in self.annotations]
        self._redo_stack.append(redo_snap)
        # 恢复上一个状态
        prev=self._undo_stack.pop()
        self.annotations=[Annotation(**asdict(a)) for a in prev]
        self._populate_list();self.annotationsChanged.emit(self.annotations)

    def _redo(self)->None:
        """Ctrl+Y 重做 - 恢复被撤销的状态"""
        if not self._redo_stack: return
        # 当前状态存入撤销栈
        undo_snap=[Annotation(**asdict(a)) for a in self.annotations]
        self._undo_stack.append(undo_snap)
        # 恢复重做状态
        nxt=self._redo_stack.pop()
        self.annotations=[Annotation(**asdict(a)) for a in nxt]
        self._populate_list();self.annotationsChanged.emit(self.annotations)

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
        self._save_snapshot()  # 修改前保存快照
        dlg=AnnotationEditDialog(self)
        if dlg.exec_()==QDialog.Accepted:
            self.annotations.append(dlg.get_annotation());self._populate_list()
            self.annotationsChanged.emit(self.annotations)
        else:
            # 取消则撤销刚才保存的快照，恢复状态
            if self._undo_stack: self._undo()

    def _edit_item(self,item)->None:
        if not item:return
        aid=item.data(Qt.UserRole);ann=next((a for a in self.annotations if a.id==aid),None)
        if ann:
            self._save_snapshot()  # 修改前保存快照
            dlg=AnnotationEditDialog(self,annotation=ann)
            if dlg.exec_()==QDialog.Accepted:
                upd=dlg.get_annotation();idx=next(i for i,a in enumerate(self.annotations) if a.id==aid)
                self.annotations[idx]=upd;self._populate_list();self.annotationsChanged.emit(self.annotations)
            else:
                # 取消则撤销刚才保存的快照，恢复状态
                if self._undo_stack: self._undo()

    def _delete_item(self)->None:
        item=self.list_widget.currentItem()
        if item:
            self._save_snapshot()
            aid=item.data(Qt.UserRole)
            self.annotations=[a for a in self.annotations if a.id!=aid];self._populate_list()
            self.annotationsChanged.emit(self.annotations)

    def _clear_all(self)->None:
        if QMessageBox.question(self,"确认","清空所有标注?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self._save_snapshot()
            self.annotations.clear();self._populate_list();self.annotationsChanged.emit(self.annotations)


# ============================================================
# 谱面显示画布组件
# ============================================================

class DisplayWidget(QWidget):
    """
    谱面显示画布组件
    功能: 渲染图片/PDF页面，叠加绘制标注层，支持双击添加标注
    """

    def __init__(self, parent: 'DisplayWindow' = None):
        super().__init__(parent)
        self.parent_window = parent
        self.images: List[QPixmap] = []
        self.annotations: List[Annotation] = []
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def set_images(self, images: List[QPixmap]) -> None:
        self.images = images; self.update()

    def set_annotations(self, annotations: List[Annotation]) -> None:
        self.annotations = annotations; self.update()

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
        self.update()
        event.accept()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(THEME_COLORS['bg_secondary']))

        if not self.images:
            painter.setPen(QColor(THEME_COLORS['text_muted']))
            painter.setFont(QFont("Microsoft YaHei",15))
            painter.drawText(self.rect(),Qt.AlignCenter,
                "请打开吉他谱文件\n支持: PNG,JPG,JPEG,WEBP,PDF,GP3/GP4/GP5/GPX")
            painter.end(); return

        ww=self.width()
        base_y=-(self.parent_window.current_position if self.parent_window else 0)

        # 绘制图片序列
        for img in self.images:
            if img.isNull(): continue
            sw=ww-20; ratio=img.width()>0 and sw/img.width() or 1
            sh=img.height()*ratio
            target=QRect(10,int(base_y),sw,int(sh))
            if target.bottom()>0 and target.top()<self.height():
                scaled=img.scaled(sw,int(sh),Qt.KeepAspectRatio,Qt.SmoothTransformation)
                painter.drawPixmap(target,scaled,scaled.rect())
            base_y+=sh+5

        # 绘制标注层
        self._draw_annotations(painter)

        # 加载遮罩
        if self.parent_window and self.parent_window.is_loading:
            painter.fillRect(self.rect(),QColor(0,0,0,120))
            painter.setPen(QColor(THEME_COLORS['primary']))
            painter.setFont(QFont("Microsoft YaHei",18))
            painter.drawText(self.rect(),Qt.AlignCenter,"加载中...")
        painter.end()

    def _draw_annotations(self,painter:QPainter)->None:
        if not self.images or not self.annotations:return
        ww=self.width()
        base_y=-(self.parent_window.current_position if self.parent_window else 0)
        total_h=sum((img.height()*(ww-20)/img.width())+5 for img in self.images if not img.isNull())
        for ann in self.annotations:
            sx=int(10+(ww-20)*ann.x); sy=int(base_y+total_h*ann.y)
            if -60<sy<self.height()+60: self._draw_one_ann(painter,ann,sx,sy)

    def _draw_one_ann(self,painter:QPainter,ann:Annotation,x:int,y:int)->None:
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

    def mouseDoubleClickEvent(self,event:QMouseEvent)->None:
        """双击谱面 - 优先检测是否点击了已有标注(编辑)，否则新建"""
        if not self.parent_window or not self.parent_window.images: return
        cx,cy=event.x(),event.y()
        ww=self.width()

        # === 先检测是否点击了已有标注(点击范围: 标注文字区域+周围10px) ===
        if self.parent_window.annotations and ww>20:
            total_h=sum((img.height()*(ww-20)/img.width())+5 for img in self.parent_window.images if not img.isNull())
            base_y=-self.parent_window.current_position
            for ann in self.parent_window.annotations:
                sx=int(10+(ww-20)*ann.x); sy=int(base_y+total_h*ann.y)
                # 检测点击是否在标注区域内(基于字体大小估算范围)
                hit_w=len(ann.text)*ann.font_size//2+20; hit_h=ann.font_size+16
                if (sx-hit_w<=cx<=sx+hit_w) and (sy-hit_h<=cy<=sy+8):
                    # 点击到已有标注 → 打开编辑对话框
                    dlg=AnnotationEditDialog(self,annotation=ann)
                    if dlg.exec_()==QDialog.Accepted:
                        updated=dlg.get_annotation()
                        idx=next((i for i,a in enumerate(self.parent_window.annotations) if a.id==ann.id),None)
                        if idx is not None:
                            self.parent_window.annotations[idx]=updated
                            self.parent_window._save_annotations()
                            self.set_annotations(self.parent_window.annotations)
                    return

        # === 未点击到任何标注 → 新建标注 ===
        rel_x=max(0,min(1,(cx-10)/(ww-20))) if ww>20 else 0
        if self.parent_window.images:
            total_h=sum((img.height()*(ww-20)/img.width())+5 for img in self.parent_window.images if not img.isNull())
            base_y=-self.parent_window.current_position
            rel_y=max(0,min(1,(cy-base_y)/total_h)) if total_h>0 else 0.5
        else:
            rel_y=0.5

        new_ann=Annotation(id=f"ann_{uuid.uuid4().hex[:8]}",x=rel_x,y=rel_y,text="新标注-双击编辑")
        dlg=AnnotationEditDialog(self,annotation=new_ann)
        if dlg.exec_()==QDialog.Accepted:
            self.parent_window.add_annotation(dlg.get_annotation())


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

    def __init__(self, file_path, file_type: str, speed: int = 45):
        super().__init__()
        # 核心状态
        self.file_path=file_path; self.file_type=file_type
        self.base_speed:int=speed           # 基础速度(ms)
        self.current_position:float=0.0     # 当前滚动位置(px)
        self.images:List[QPixmap]=[]       # 图片列表
        self.loaded_images:List[QPixmap]=[]# 加载中图片
        self.timer:QTimer=QTimer()         # 播放定时器
        self.timer.timeout.connect(self._tick)
        self.is_loading:bool=False          # 加载状态
        self.scroll_step:float=1.0         # 每帧滚动px

        # 高级功能状态
        self.annotations:List[Annotation]=[]     # 标注列表
        self.speed_curve:SpeedCurveConfig=SpeedCurveConfig()  # 速度曲线
        self.loop_config:LoopConfig=LoopConfig()          # 循环配置
        self.total_scroll_distance:float=0.0   # 总可滚动距离
        self.play_time:float=0.0              # 已播放时间

        self.init_ui()
        self._load_annotations()               # 加载已有标注
        self.load_content_async()              # 异步加载内容

    def init_ui(self)->None:
        """初始化用户界面"""
        self.setWindowTitle('TAB Score Viewer - 吉他谱查看器')
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

        # 右侧控制面板
        right_panel=self._create_control_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([820,260])
        main_layout.addWidget(splitter,1)

        # ===== 底部进度条 =====
        bottom=self._create_bottom_bar()
        main_layout.addLayout(bottom)

    def _apply_theme(self)->None:
        """应用深色主题"""
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{background-color:{THEME_COLORS['bg_primary']};color:{THEME_COLORS['text_primary']};
                font-family:'Microsoft YaHei','Segoe UI',sans-serif;}}
            QLabel{{color:{THEME_COLORS['text_primary']};font-size:13px;}}
            QSlider::groove:horizontal{{border:none;height:4px;background:{THEME_COLORS['bg_surface']};border-radius:2px;}}
            QSlider::handle:horizontal{{background:{THEME_COLORS['primary']};border:2px solid{THEME_COLORS['bg_primary']};
                width:16px;margin:-7px 0;border-radius:8px;}}
            QSpinBox{{background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};
                border:1px solid{THEME_COLORS['border']};border-radius:4px;padding:4px;}}
            QComboBox{{background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};
                border:1px solid{THEME_COLORS['border']};border-radius:4px;padding:4px 8px;}}
            QComboBox::drop-down{{border:none;width:20px;}}
            QComboBox QAbstractItemView{{background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};
                selection-background-color:{THEME_COLORS['primary']};}}
            QGroupBox{{color:{THEME_COLORS['text_primary']};border:1px solid{THEME_COLORS['border']};
                border-radius:8px;margin-top:12px;padding-top:8px;font-weight:bold;}}
            QGroupBox::title{{subcontrol-origin;margin;left:12px;padding:0 6px;}}
        """)

    def _create_toolbar(self)->QHBoxLayout:
        """创建顶部工具栏"""
        tb=QHBoxLayout();tb.setSpacing(10)

        # 文件名
        fname=os.path.basename(self.file_path) if isinstance(self.file_path,str) else "多张图片"
        self.file_label=QLabel(f"📄 {fname}")
        self.file_label.setStyleSheet(f"font-size:14px;font-weight:bold;color:{THEME_COLORS['primary_light']};")
        tb.addWidget(self.file_label)
        tb.addStretch()

        # 缩放滑块
        tb.addWidget(QLabel("缩放:"))
        self.zoom_slider=ModernSlider(Qt.Horizontal,'primary')
        self.zoom_slider.setRange(50,200);self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(120)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        tb.addWidget(self.zoom_slider)

        # 标注按钮
        self.annotation_btn=ModernButton("📝 标注",'accent')
        self.annotation_btn.clicked.connect(self._open_annotation_manager)
        tb.addWidget(self.annotation_btn)

        # 速度曲线按钮
        self.curve_btn=ModernButton("📊 速度曲线",'primary')
        self.curve_btn.clicked.connect(self._open_speed_curve_editor)
        tb.addWidget(self.curve_btn)

        return tb

    def _create_control_panel(self)->QWidget:
        """创建右侧控制面板"""
        panel=QWidget();panel.setMaximumWidth(280);panel.setMinimumWidth(240)
        layout=QVBoxLayout(panel);layout.setSpacing(10)

        # === 播放控制 ===
        pg=QGroupBox("播放控制");pl=QVBoxLayout(pg)
        btn_row=QHBoxLayout()
        self.play_btn=ModernButton("▶ 播放",'success');self.play_btn.clicked.connect(self.toggle_playback)
        self.stop_btn=ModernButton("⏹ 停止",'danger');self.stop_btn.clicked.connect(self.stop_playback);self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.play_btn);btn_row.addWidget(self.stop_btn);pl.addLayout(btn_row)

        # 循环模式
        loop_row=QHBoxLayout();loop_row.addWidget(QLabel("循环:"))
        self.loop_combo=QComboBox()
        self.loop_combo.addItems(["不循环","全局循环","区域循环(A-B)"])
        self.loop_combo.currentIndexChanged.connect(self._on_loop_mode_changed)
        loop_row.addWidget(self.loop_combo);pl.addLayout(loop_row)

        # A-B点按钮
        ab_row=QHBoxLayout()
        self.set_a_btn=ModernButton("设A点",'warning');self.set_a_btn.clicked.connect(lambda:self._set_ab_point('a'))
        self.set_b_btn=ModernButton("设B点",'warning');self.set_b_btn.clicked.connect(lambda:self._set_ab_point('b'))
        self.clear_ab_btn=ModernButton("清除AB",'text_muted');self.clear_ab_btn.clicked.connect(self._clear_ab_points)
        ab_row.addWidget(self.set_a_btn);ab_row.addWidget(self.set_b_btn);ab_row.addWidget(self.clear_ab_btn)
        pl.addLayout(ab_row)
        layout.addWidget(pg)

        # === 速度控制 ===
        sg=QGroupBox("播放速度");sl=QVBoxLayout(sg)
        sr=QHBoxLayout();sr.addWidget(QLabel("速度:"))
        self.speed_spin=QSpinBox();self.speed_spin.setRange(1,500)
        self.speed_spin.setValue(self.base_speed);self.speed_spin.setSuffix(" ms")
        self.speed_spin.valueChanged.connect(self._on_speed_changed)
        sr.addWidget(self.speed_spin);sl.addLayout(sr)

        self.curve_status_label=QLabel("速度曲线: 未启用")
        self.curve_status_label.setStyleSheet(f"color:{THEME_COLORS['text_muted']};font-size:11px;")
        sl.addWidget(self.curve_status_label)
        layout.addWidget(sg)

        # === 状态信息 ===
        ig=QGroupBox("状态信息");il=QVBoxLayout(ig)
        self.position_label=QLabel("位置: 0.0%");self.time_label=QLabel("时间: 00:00")
        il.addWidget(self.position_label);il.addWidget(self.time_label)
        self.ab_info_label=QLabel("")
        self.ab_info_label.setStyleSheet(f"color:{THEME_COLORS['accent']};font-size:11px;")
        il.addWidget(self.ab_info_label)
        layout.addWidget(ig)

        # 快捷键帮助
        hg=QGroupBox("快捷键");hl=QVBoxLayout(hg)
        help_txt=QLabel(
            "空格: 播放/暂停\n↑↓: 调整位置\n←→: 微调速度\nESC: 关闭\n双击谱面: 添加标注"
        )
        help_txt.setStyleSheet(f"color:{THEME_COLORS['text_muted']};font-size:11px;")
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
        self.page_input.setStyleSheet(f"background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};border:1px solid{THEME_COLORS['border']};border-radius:4px;padding:2px;")
        self.page_input.valueChanged.connect(self._on_page_jump)
        pg_layout.addWidget(self.page_input)

        self.page_total_label=QLabel("/ 1")
        self.page_total_label.setStyleSheet(f"color:{THEME_COLORS['text_muted']};font-size:12px;")
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
        # 延迟重算: 确保窗口布局完成后再精确计算一次总滚动距离
        QTimer.singleShot(200,self._calculate_total_distance)

    def _on_content_load_error(self,msg:str)->None:
        """加载失败回调"""
        self.is_loading=False
        QMessageBox.critical(self,"加载错误",f"无法加载文件:\n{msg}")

    def update_content(self,file_path,file_type:str,speed:int)->None:
        """更新显示内容"""
        self.file_path=file_path;self.file_type=file_type;self.base_speed=speed
        self._calculate_scroll_step(speed);self.annotations.clear()
        self._load_annotations();self.load_content_async()

    # ========== 播放控制 ==========

    def toggle_playback(self)->None:
        """切换播放/暂停"""
        if self.timer.isActive(): self.stop_playback()
        else: self.start_playback()

    def start_playback(self)->None:
        """开始播放"""
        self.timer.start(max(1,int(self.base_speed)))
        self.play_btn.setText("⏸ 暂停")
        self.play_btn.setStyleSheet(f"background-color:{THEME_COLORS['warning']};")
        self.stop_btn.setEnabled(True)

    def stop_playback(self)->None:
        """停止播放"""
        self.timer.stop()
        self.play_btn.setText("▶ 播放")
        self.play_btn.setStyleSheet(f"background-color:{THEME_COLORS['success']};")
        self.stop_btn.setEnabled(False)

    def _tick(self)->None:
        """播放定时器回调 - 每帧执行"""
        # 计算当前速度(启用曲线时从曲线获取)
        if self.speed_curve.is_enabled and len(self.speed_curve.points)>=2:
            current_speed=self._get_curve_speed()
        else:
            current_speed=self.base_speed

        self._calculate_scroll_step(current_speed)
        self.current_position+=self.scroll_step
        self.play_time+=current_speed/1000.0

        # 循环检查
        should_loop=self._check_loop_condition()
        if should_loop:
            if self.loop_config.loop_type=='all':
                self.current_position=0;self.play_time=0
            elif self.loop_config.loop_type=='region':
                self.current_position=self.total_scroll_distance*self.loop_config.start_position/100
        elif self.current_position>=self.total_scroll_distance:
            self.current_position=self.total_scroll_distance
            self.stop_playback()

        self.display_widget.update()
        self.update_progress_display()

    def _get_curve_speed(self)->float:
        """根据速度曲线获取当前时刻的速度值"""
        if not self.speed_curve.points or self.total_scroll_distance<=0:
            return self.base_speed
        progress_pct=(self.current_position/self.total_scroll_distance)*100
        progress_pct=max(0,min(100,progress_pts:=progress_pct))
        pts=sorted(self.speed_curve.points,key=lambda p:p.position)
        for i in range(len(pts)-1):
            p1,p2=pts[i],pts[i+1]
            if p1.position<=progress_pts<=p2.position:
                t=(progress_pts-p1.position)/(p2.position-p1.position) if p2.position!=p1.position else 0
                return p1.speed+t*(p2.speed-p1.speed)
        return self.base_speed

    def _calculate_scroll_step(self,speed_ms:float)->None:
        """根据速度(ms)计算每帧滚动像素数 - 速度越小越快"""
        # speed_ms范围约5-150ms，映射到scroll_step 0.5-5px
        if speed_ms<=0:speed_ms=1
        # 非线性映射让速度调节更自然
        self.scroll_step=max(0.3,min(8.0,200.0/speed_ms))

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
        # 更新时间估算
        secs=int(self.total_scroll_distance/self.scroll_step/60) if self.scroll_step>0 else 0
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

    def update_progress_display(self)->None:
        """更新进度显示 - 含页码同步"""
        if self.total_scroll_distance>0:
            pct=(self.current_position/self.total_scroll_distance)*100
        else:
            pct=0
        self.position_label.setText(f"位置: {pct:.1f}%")
        self.progress_bar.blockSignals(True)
        self.progress_bar.position=pct
        self.progress_bar.blockSignals(False)
        secs=int(self.play_time)
        self.time_start_label.setText(f"{secs//60:02d}:{secs%60:02d}")

        # 同步页码输入框(避免循环触发信号)
        if hasattr(self,'page_input') and self.images and len(self.images)>1:
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

    def _on_zoom_changed(self,val:int)->None:
        """缩放改变"""
        pass  # 可扩展实现缩放功能

    def _on_speed_changed(self,val:int)->None:
        """速度改变"""
        self.base_speed=val
        if self.timer.isActive():
            self.timer.start(max(1,val))

    def _on_progress_changed(self,pos:float)->None:
        """进度条拖动"""
        if self.total_scroll_distance>0:
            self.current_position=pos/100*self.total_scroll_distance
            self.display_widget.update()

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
            self.ab_info_label.setText("请先设置A点和B点")
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
        """添加标注"""
        self.annotations.append(ann)
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()

    def _open_annotation_manager(self)->None:
        """打开标注管理器"""
        dlg=AnnotationManagerDialog(self,self.annotations)
        dlg.annotationsChanged.connect(self._on_annotations_changed)
        dlg.exec_()

    def _on_annotations_changed(self,new_anns:List[Annotation])->None:
        """标注列表变更回调"""
        self.annotations=new_anns
        self.display_widget.set_annotations(self.annotations)
        self._save_annotations()

    def _get_annotation_file_path(self)->str:
        """获取当前文件的标注存储路径"""
        if isinstance(self.file_path,str):
            base=os.path.splitext(os.path.basename(self.file_path))[0]
        else:
            base="multi_image"
        os.makedirs(ANNOTATION_DIR,exist_ok=True)
        return os.path.join(ANNOTATION_DIR,f"{base}.json")

    def _load_annotations(self)->None:
        """从JSON加载标注"""
        try:
            fpath=self._get_annotation_file_path()
            if os.path.exists(fpath):
                with open(fpath,'r',encoding='utf-8') as f:
                    data=json.load(f)
                    self.annotations=[Annotation(**d) for d in data]
        except Exception:
            self.annotations=[]

    def _save_annotations(self)->None:
        """保存标注到JSON"""
        try:
            fpath=self._get_annotation_file_path()
            os.makedirs(os.path.dirname(fpath),exist_ok=True)
            with open(fpath,'w',encoding='utf-8') as f:
                json.dump([asdict(a) for a in self.annotations],f,ensure_ascii=False,indent=2)
        except Exception as e:
            print(f"保存标注失败: {e}")

    # ========== 速度曲线 ==========

    def _open_speed_curve_editor(self)->None:
        """打开速度曲线编辑器"""
        dlg=SpeedCurveEditor(parent=self,current_curve=self.speed_curve)
        dlg.curveUpdated.connect(self._on_curve_updated)
        dlg.exec_()

    def _on_curve_updated(self,config:SpeedCurveConfig)->None:
        """速度曲线更新回调"""
        self.speed_curve=config
        status=f"已启用({len(config.points)}个控制点)" if config.is_enabled else "未启用"
        self.curve_status_label.setText(f"速度曲线: {status}")

    # ========== 键盘事件 ==========

    def keyPressEvent(self,event:QKeyEvent)->None:
        """键盘快捷键"""
        try:
            if event.key()==Qt.Key_Space:          # 空格: 播放/暂停
                self.toggle_playback()
            elif event.key()==Qt.Key_Up:           # 上箭头: 向上滚动
                self.current_position=max(0,self.current_position-30)
                self.display_widget.update();self.update_progress_display()
            elif event.key()==Qt.Key_Down:         # 下箭头: 向下滚动
                self.current_position=min(self.total_scroll_distance,self.current_position+30)
                self.display_widget.update();self.update_progress_display()
            elif event.key()==Qt.Key_Left:          # 左箭头: 减速
                self.speed_spin.setValue(max(1,self.speed_spin.value()-5))
            elif event.key()==Qt.Key_Right:         # 右箭头: 加速
                self.speed_spin.setValue(min(500,self.speed_spin.value()+5))
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
        self.display_window:Optional[DisplayWindow]=None
        self.current_directory:str=""
        self.is_loading:bool=False
        self._loaded_files:List[Tuple]=[]

        self.init_ui()
        self._apply_theme()  # 应用深色主题

        loading_item=QListWidgetItem("正在初始化...")
        loading_item.setFlags(loading_item.flags() & ~Qt.ItemIsEnabled)
        self.file_list.addItem(loading_item)

        self.show()
        QTimer.singleShot(100,self._load_config_and_restore)

    def init_ui(self)->None:
        """初始化UI"""
        self.setWindowTitle('TAB Score Viewer - 设置')
        self.setGeometry(100,100,800,600)

        central=QWidget();self.setCentralWidget(central)
        main_layout=QVBoxLayout(central)

        # 文件夹选择
        folder_layout=QHBoxLayout()
        self.folder_label=QLabel('未选择文件夹')
        self.folder_button=QPushButton('选择文件夹')
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_button)
        main_layout.addLayout(folder_layout)

        # 速度控制
        speed_layout=QHBoxLayout()
        speed_layout.addWidget(QLabel('播放速度:'))
        self.speed_slider=QSlider(Qt.Horizontal)
        self.speed_value_label=QLabel('50')
        self.speed_slider.valueChanged.connect(self._update_speed_value)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)

        speed_layout.addWidget(QLabel('最小:'))
        self.min_speed_edit=QLineEdit('50')
        self.min_speed_edit.setMaximumWidth(50)
        self.min_speed_edit.editingFinished.connect(self._update_speed_range)
        speed_layout.addWidget(self.min_speed_edit)

        speed_layout.addWidget(QLabel('最大:'))
        self.max_speed_edit=QLineEdit('200')
        self.max_speed_edit.setMaximumWidth(50)
        self.max_speed_edit.editingFinished.connect(self._update_speed_range)
        speed_layout.addWidget(self.max_speed_edit)

        main_layout.addLayout(speed_layout)

        # 文件列表
        file_list_label=QLabel('文件列表:')
        search_layout=QHBoxLayout()
        search_layout.addWidget(QLabel('搜索:'))
        self.search_edit=QLineEdit()
        self.search_edit.setPlaceholderText('输入文件名搜索...')
        self.search_edit.returnPressed.connect(self.filter_file_list)
        self.clear_search_btn=QPushButton('清除')
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
        """应用深色主题到设置窗口"""
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{background-color:{THEME_COLORS['bg_primary']};color:{THEME_COLORS['text_primary']};
                font-family:'Microsoft YaHei','Segoe UI',sans-serif;}}
            QLabel{{color:{THEME_COLORS['text_primary']};font-size:13px;}}
            QPushButton{{background-color:{THEME_COLORS['primary']};color:white;border:none;
                border-radius:6px;padding:7px 16px;font-weight:500;}}
            QPushButton:hover{{background-color:{THEME_COLORS['primary_hover']};}}
            QPushButton:pressed{{background-color:{THEME_COLORS['primary']};}}
            QLineEdit{{background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};
                border:1px solid{THEME_COLORS['border']};border-radius:5px;padding:5px 8px;}}
            QSlider::groove:horizontal{{border:none;height:6px;background:{THEME_COLORS['bg_surface']};border-radius:3px;}}
            QSlider::handle:horizontal{{background:{THEME_COLORS['primary']};width:16px;margin:-6px 0;border-radius:8px;
                border:2px solid{THEME_COLORS['bg_primary']};}}
            QListWidget{{background-color:{THEME_COLORS['bg_surface']};color:{THEME_COLORS['text_primary']};
                border:1px solid{THEME_COLORS['border']};border-radius:6px;outline:none;}}
            QListWidget::item{{padding:6px;border-bottom:1px solid{THEME_COLORS['border']};}}
            QListWidget::item:selected{{background-color:{THEME_COLORS['primary']};color:white;}}
            QListWidget::item:hover{{background-color:{THEME_COLORS['bg_card']};}}
            QScrollBar:vertical{{background:{THEME_COLORS['bg_secondary']};width:10px;border-radius:5px;}}
            QScrollBar::handle:vertical{{background:{THEME_COLORS['border']};border-radius:5px;min-height:30px;}}
            QScrollBar::handle:vertical:hover{{background:{THEME_COLORS['text_muted']};}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
        """)

    def _load_config_and_restore(self)->None:
        """加载配置并恢复状态 - 包含目录有效性检查"""
        try:
            self.load_config()
            if hasattr(self,'last_speed'):
                self.speed_slider.setValue(self.last_speed)
                self.speed_value_label.setText(str(self.last_speed))
            if hasattr(self,'min_range') and hasattr(self,'max_range'):
                self.speed_slider.setRange(self.min_range,self.max_range)
                self.min_speed_edit.setText(str(self.min_range))
                self.max_speed_edit.setText(str(self.max_range))
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
                    self.last_speed=cfg.get('last_speed',50)
                    self.min_range=cfg.get('min_range',50)
                    self.max_range=cfg.get('max_range',200)
            else:
                self.last_speed=50;self.min_range=50;self.max_range=200
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.last_speed=50;self.min_range=50;self.max_range=200

    def save_config(self)->None:
        """保存配置文件"""
        try:
            cfg={'last_folder':self.current_directory,
                 'last_speed':self.speed_slider.value(),
                 'min_range':int(self.min_speed_edit.text()),
                 'max_range':int(self.max_speed_edit.text())}
            os.makedirs(os.path.dirname(CONFIG_FILE),exist_ok=True)
            with open(CONFIG_FILE,'w',encoding='utf-8') as f:
                json.dump(cfg,f,ensure_ascii=False,indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def select_folder(self)->None:
        """选择文件夹"""
        folder=QFileDialog.getExistingDirectory(self,"选择文件夹","",QFileDialog.ShowDirsOnly)
        if folder:
            self.current_directory=folder
            self.folder_label.setText(folder)
            self.load_file_list_async(folder)
            self.save_config()

    def load_file_list_async(self,folder:str)->None:
        """异步加载文件列表"""
        self.is_loading=True;self.file_list.clear()
        item=QListWidgetItem("正在加载...");item.setFlags(item.flags()&~Qt.ItemIsEnabled)
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
            up=QListWidgetItem("[返回上一级]")
            up.setData(Qt.UserRole,os.path.dirname(self.current_directory));up.setData(Qt.UserRole+1,True)
            self.file_list.addItem(up);self.original_items.append(("[返回上一级]",os.path.dirname(self.current_directory),True))

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
        empty_item=QListWidgetItem("文件夹为空或无法访问");empty_item.setFlags(empty_item.flags()&~Qt.ItemIsEnabled)
        self.file_list.addItem(empty_item)
        # 根据错误类型给出不同提示
        if "目录不存在" in msg or "路径不是文件夹" in msg:
            QMessageBox.warning(self,"目录不可用",f"{msg}\n\n请点击「选择文件夹」重新选择。")
        elif "无权限" in msg:
            QMessageBox.warning(self,"权限不足",f"{msg}\n\n请检查文件夹权限或选择其他目录。")
        else:
            QMessageBox.critical(self,"加载错误",f"加载失败:\n{msg}")

    def _update_speed_value(self,value:int)->None:
        """速度值改变"""
        self.speed_value_label.setText(str(value));self.save_config()
        if self.display_window and self.display_window.isVisible():
            self.display_window.base_speed=value
            if self.display_window.timer.isActive():
                self.display_window.timer.start(value)

    def _update_speed_range(self)->None:
        """速度范围改变"""
        try:
            mn,mx=int(self.min_speed_edit.text()),int(self.max_speed_edit.text())
            if mn<1:mn=1;self.min_speed_edit.setText(str(mn))
            if mn>=mx:mn=mx-1;self.min_speed_edit.setText(str(mn))
            self.speed_slider.setRange(mn,mx)
            cur=self.speed_slider.value()
            if cur<mn:self.speed_slider.setValue(mn)
            elif cur>mx:self.speed_slider.setValue(mx)
            self.save_config()
        except ValueError:
            self.min_speed_edit.setText(str(getattr(self,'min_range',50)))
            self.max_speed_edit.setText(str(getattr(self,'max_range',200)))

    def on_file_double_clicked(self,item:QListWidgetItem)->None:
        """双击文件项 - 图片格式自动加载同目录所有图片(按序拼接)"""
        fpath=item.data(Qt.UserRole);is_dir=item.data(Qt.UserRole+1)
        if is_dir:
            self.is_loading=True;self.file_list.clear()
            li=QListWidgetItem("正在进入...");li.setFlags(li.flags()&~Qt.ItemIsEnabled)
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
            menu.addAction('播放此文件夹中所有图片',lambda:self.play_all_images(fpath))
            menu.addAction('进入文件夹',lambda:self.on_file_double_clicked(item))
            menu.addSeparator()
            menu.addAction('在资源管理器中打开',lambda:self.open_file_location(fpath))
        else:
            menu.addAction('查看文件',lambda:self.on_file_double_clicked(item))
            ext=os.path.splitext(fpath)[1].lower()
            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                menu.addAction('播放当前图片',lambda:self.show_display([fpath],'images'))
                src=self.original_items if not self.is_searching else []
                menu.addAction('播放全部图片',lambda:self.play_all_images(os.path.dirname(fpath)))
            menu.addSeparator()
            # 通用：任何文件都可在资源管理器中定位
            menu.addAction('在资源管理器中打开',lambda:self.open_file_location(fpath))
        menu.exec_(self.file_list.mapToGlobal(pos))

    def open_file_location(self,fpath:str)->None:
        """
        在系统文件资源管理器中打开并选中指定文件/文件夹
        
        原理: 调用系统命令定位到文件
          Windows: explorer /select,"路径"
          Linux:   xdg-open 或 nautilus --select "路径"
        
        参数:
            fpath: 要定位的文件或文件夹的绝对路径
        """
        import subprocess, platform
        try:
            if platform.system() == 'Windows':
                # Windows: explorer /select 会打开文件夹并高亮选中该文件
                subprocess.run(['explorer', '/select,', fpath], check=False)
            elif platform.system() == 'Linux':
                # Linux: 尝试多种文件管理器
                for cmd in [
                    ['xdg-open', os.path.dirname(fpath)],
                    ['nautilus', '--select', fpath],
                    ['dolphin', '--select', fpath],
                    ['thunar', fpath],
                ]:
                    try:
                        subprocess.run(cmd, check=False, timeout=3)
                        break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
        except Exception as e:
            QMessageBox.warning(self,'无法打开',f'无法打开文件位置:\n{str(e)}')

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
        slider_val=self.speed_slider.value()
        mn_range=int(self.min_speed_edit.text());mx_range=int(self.max_speed_edit.text())
        if mx_range>mn_range:
            linear_pct=(slider_val-mn_range)/(mx_range-mn_range)
            adj_pct=linear_pct**0.5
            if adj_pct>=0.8:speed=15
            elif adj_pct>=0.6:speed=25
            elif adj_pct>=0.4:speed=40
            elif adj_pct>=0.2:speed=60
            else:speed=90
        else:speed=45
        speed=int(speed)

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
    app.setStyle('Fusion')  # 使用Fusion样式作为基础，配合自定义深色主题
    settings = SettingsWindow()
    sys.exit(app.exec_())
