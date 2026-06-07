# -*- coding: utf-8 -*-
"""
============================================================
文件名: tab_renderer.py
功能描述: 六线谱渲染引擎 - 使用 QPainter 将 GTP 数据模型绘制为
         可视化的吉他六线谱图像（QPixmap），支持多页输出

原理:
  1. 接收 GTPTrack 数据和布局计算结果
  2. 使用 QPainter 在 QPixmap 上绑制:
     - 六线谱线(6条横线，代表6根弦)
     - 品格数字(在对应弦线的正确位置显示品格数)
     - 小节线(分隔各小节)
     - 符干/符尾(表示音符时值，含附点标记和优化休止符符号)
     - 技巧标记(图形化+文字混合渲染):
       * 泛音菱形、滑音连线、推弦弧线箭头、颤音波浪线
       * P.M./Let Ring虚线延长线
       * 击弦/勾弦/滑音等缩写文字标签
     - 调号/拍号标记(每行系统开头显示非标准拍号和升降号)
  3. 输出多页 QPixmap 列表，供 DisplayWidget 直接使用

核心方法:
  - render_from_file(): 从GTP文件路径直接渲染（便捷入口）
  - render(): 主渲染入口，返回多页QPixmap列表
  - _draw_system(): 绘制一行系统(弦线 + 调拍号 + 所有小节)
  - _draw_measure(): 绘制单个小节(小节线 + 段落标记 + 所有拍 + P.M.虚线)
  - _draw_beat(): 绘制单个拍(品格数字 + 技巧标记 + 符干符尾)
  - _draw_technique_marks(): 技巧标记分发器，按类型调用对应绘制方法

依赖库:
  - PyQt5 (QPainter, QPixmap, QFont, QPen, QColor, QPainterPath等)
  - 内部依赖: gtp_engine.models.*, layout_engine.*, utils.constants

创建日期: 2026-06-06
最后更新: 2026-06-07 (v1.2.0: Phase 2增强渲染 - 技巧符号图形化/时值显示/调拍号)
============================================================
"""

from typing import List, Optional

from PyQt5.QtGui import (
    QPainter, QPixmap, QFont, QPen, QColor,
    QImage, QLinearGradient, QFontMetrics
)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize

from ..models.track import GTPTrack
from ..models.song import GTPSong
from .layout_engine import (
    TabLayoutEngine, PageLayout, SystemLayout, 
    MeasureLayout, BeatLayout
)
from ..utils.constants import (
    RenderConfig, TechniqueType, TECHNIQUE_ABBREVIATION,
    NoteDuration, DURATION_RATIO, get_string_name
)


class TabRenderer:
    """
    六线谱渲染引擎
    
    功能: 将解析后的GTP乐谱数据渲染为可视化的六线谱图像
    
    用法:
        renderer = TabRenderer()
        pixmaps = renderer.render(song, track_index=0)
        # pixmaps: List[QPixmap] - 每页一张图片
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        self.cfg = config or RenderConfig()
        self._layout_engine = TabLayoutEngine(self.cfg)

    def render(self, song: GTPSong, track_index: int = 0,
               page_width: int = None, page_height: int = None) -> List[QPixmap]:
        """
        渲染指定音轨的完整六线谱
        
        参数:
            song:          完整歌曲数据
            track_index:   要渲染的音轨索引（默认第1条）
            page_width:    每页宽度(px)，None则用配置默认值
            page_height:   每页高度(px)，None则用配置默认值
            
        返回:
            QPixmap列表，每元素对应一页乐谱图像
        """
        # 获取目标音轨
        if track_index >= len(song.tracks):
            track_index = 0
        track = song.tracks[track_index]
        
        pw = page_width or self.cfg.PAGE_WIDTH_PX
        ph = page_height or self.cfg.PAGE_HEIGHT_PX
        
        # 执行布局计算
        pages_layout = self._layout_engine.layout(track, pw, ph)
        
        # 为每页生成图像
        pixmaps: List[QPixmap] = []
        for page_layout in pages_layout:
            pixmap = self._render_page(song, track, page_layout, pw, ph)
            pixmaps.append(pixmap)
        
        return pixmaps

    def render_from_file(self, file_path: str, track_index: int = 0,
                         page_width: int = None, page_height: int = None) -> List[QPixmap]:
        """
        便捷方法：从文件路径直接渲染（解析+渲染一步完成）
        
        参数:
            file_path:    .gp3/.gp4/.gp5/.gpx 文件路径
            track_index:  要渲染的音轨索引（默认0=第一条）
            page_width:   每页宽度(px)，None则用配置默认值
            page_height:  每页高度(px)，None则用配置默认值
            
        返回:
            QPixmap列表，每元素对应一页乐谱图像
        """
        from ..parser.gtp_parser import parse_gtp
        song = parse_gtp(file_path)
        return self.render(song, track_index=track_index,
                          page_width=page_width, page_height=page_height)

    def _render_page(self, song: GTPSong, track: GTPTrack,
                     page: PageLayout, width: int, height: int) -> QPixmap:
        """渲染单页乐谱图像"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(self.cfg.COLOR_BG))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        
        try:
            # 1. 绘制页面头部信息区（仅第1页显示标题/调弦/BPM，后续页省略以节省空间）
            if page.page_number == 1:
                self._draw_header(painter, song, track, width)
            
            # 2. 绘制每行系统(六线谱行)
            for system in page.systems:
                self._draw_system(painter, track, system)
            
            # 3. 绘制页码
            self._draw_page_number(painter, f"第 {page.page_number} 页", width, height)
            
        finally:
            painter.end()
        
        return pixmap

    # ============================================================
    # 头部信息区绘制
    # ============================================================

    def _draw_header(self, painter: QPainter, song: GTPSong,
                     track: GTPTrack, page_width: int) -> None:
        """绘制页面顶部信息区（标题、轨道名、调弦、BPM）"""
        y = 15
        
        # 歌曲标题
        painter.setPen(QColor(self.cfg.COLOR_TEXT))
        title_font = QFont(self.cfg.NOTE_FONT_FAMILY, self.cfg.TRACK_NAME_FONT_SIZE, QFont.Bold)
        painter.setFont(title_font)
        title_text = song.title or "Untitled"
        if len(title_text) > 50:
            title_text = title_text[:47] + "..."
        painter.drawText(QRect(10, y, page_width - 20, 25), Qt.AlignLeft, title_text)
        y += 26
        
        # 第二行：轨道名 | 调弦 | BPM
        info_font = QFont(self.cfg.NOTE_FONT_FAMILY, self.cfg.INFO_FONT_SIZE)
        painter.setFont(info_font)
        painter.setPen(QColor(self.cfg.COLOR_TRACK_NAME))
        
        tuning_str = ','.join(
            self._midi_to_note_name(p) for p in track.strings
        )
        info_line = f"{track.name}  |  调弦: {tuning_str}  |  {song.tempo} BPM"
        painter.drawText(QRect(10, y, page_width - 20, 20), Qt.AlignLeft, info_line)

    @staticmethod
    def _midi_to_note_name(midi: int) -> str:
        """将MIDI音高值转换为音符名称"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi // 12) - 1
        note = note_names[midi % 12]
        return f"{note}{octave}"

    # ============================================================
    # 系统(行)绘制
    # ============================================================

    def _draw_system(self, painter: QPainter, track: GTPTrack,
                     system: SystemLayout) -> None:
        """
        绘制一行完整的六线谱系统（含所有小节）
        
        绘制顺序:
          1. 六条弦线
          2. 调号/拍号信息（仅在该系统第一个小节有变化时显示）
          3. 每个小节的内容（小节线 + 音符 + 技巧标记）
        """
        
        # 1. 绘制六条弦线
        self._draw_tab_lines(painter, system)
        
        # 2. 在该系统第一个小节前绘制调号/拍号（如果需要）
        if system.measures:
            first_measure = system.measures[0].measure
            self._draw_time_signature(painter, first_measure, system)
            self._draw_key_signature(painter, first_measure, system)
        
        # 3. 绘制每个小节的内容
        for m_layout in system.measures:
            self._draw_measure(painter, track, system, m_layout)

    def _draw_time_signature(self, painter: QPainter,
                              measure, system: SystemLayout) -> None:
        """
        绘制拍号记号（如 "4/4"、"3/4"、"6/8" 等）
        
        原理: 拍号表示每小节的拍数和每拍的时值单位。
              标准记谱法中拍号显示在谱号和调号之后、乐曲开头。
              六线谱中在每行系统开头或拍号变化处显示。
              格式：上下堆叠的两个数字，分子在上（拍数），分母在下（时值单位）。
        
        显示规则:
          - 仅当拍号不是默认的 4/4 时才显示（节省空间）
          - 拍号变化时（与前一小节不同）也显示
        
        参数:
            painter: QPainter绑制对象
            measure: 小节数据（含 time_signature 属性）
            system:  系统布局（含Y坐标信息）
        """
        numerator, denominator = measure.time_signature
        
        # 仅非标准拍号(非4/4)时显示，避免视觉冗余
        # 如需始终显示，可去掉此判断
        if numerator == 4 and denominator == 4:
            return
        
        # 拍号位置：六线谱左侧，在小节线右边一点
        x = self.cfg.PAGE_MARGIN_LEFT - 2
        y_top = system.y_tab_top + 2   # 分子Y（上数字）
        y_bottom = system.y_tab_top + self.cfg.TAB_LINE_SPACING * 3 + 6  # 分母Y（下数字）
        
        painter.setPen(QColor(self.cfg.COLOR_TEXT))
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 11, QFont.Bold)
        painter.setFont(font)
        
        # 上方：分子（拍数）
        fm = QFontMetrics(font)
        num_text = str(numerator)
        num_w = fm.horizontalAdvance(num_text)
        painter.drawText(QPoint(x - num_w // 2, y_top + 10), num_text)
        
        # 下方：分母（时值单位）
        den_text = str(denominator)
        den_w = fm.horizontalAdvance(den_text)
        painter.drawText(QPoint(x - den_w // 2, y_bottom), den_text)

    def _draw_key_signature(self, painter: QPainter,
                             measure, system: SystemLayout) -> None:
        """
        绘制调号记号（升号# 或降号b 的数量）
        
        原理: 调号表示乐曲的调性（如C大调=0升降号, G大调=1升号）。
              标准记谱法中调号紧跟在谱号之后。六线谱简化为：
              在拍号左侧显示升降号数量文字标注。
        
        显示规则:
          - 仅当调号非C大调/a小调(0)时显示
          - 正数表示升号数(Sharps)，负数表示降号数(Flats)
        
        参数:
            painter: QPainter绑制对象
            measure: 小节数据（含 key_signature 属性）
            system:  系统布局
        """
        key_sig = measure.key_signature
        
        # 兼容处理：key_signature 可能是int或tuple格式
        if isinstance(key_sig, (list, tuple)):
            # 如果是元组，取第一个元素作为升降号数
            key_val = key_sig[0] if len(key_sig) > 0 else 0
        else:
            key_val = key_sig
        
        # C大调/a小调不显示调号（无升降号）
        if not key_val or key_val == 0:
            return
        
        # 调号位置：在拍号左边
        x = self.cfg.PAGE_MARGIN_LEFT - 20
        y_center = system.y_tab_top + self.cfg.TAB_LINE_SPACING * 2.5
        
        painter.setPen(QColor(self.cfg.COLOR_TEXT))
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 9)
        painter.setFont(font)
        
        if key_val > 0:
            # 升号调：显示 "#N" (N=升号数量)
            text = f"#{key_val}"
        else:
            # 降号调：显示 "bN" (N=降号数量的绝对值)
            text = f"b{abs(key_val)}"
        
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        painter.drawText(QPoint(x - tw // 2, int(y_center + 3)), text)

    def _draw_tab_lines(self, painter: QPainter, system: SystemLayout) -> None:
        """绘制六条水平的弦线（六线谱的基础线）"""
        pen = QPen(QColor(self.cfg.COLOR_TAB_LINE), self.cfg.TAB_LINE_THICKNESS)
        painter.setPen(pen)
        
        x_start = self.cfg.PAGE_MARGIN_LEFT - 5
        x_end = self.cfg.PAGE_MARGIN_LEFT + 800  # 行宽度估算
        
        # 找到该行最右边的小节结束位置
        if system.measures:
            x_end = system.measures[-1].x_end + 10
        
        for i in range(6):
            y = system.y_tab_top + i * self.cfg.TAB_LINE_SPACING
            painter.drawLine(x_start, y, x_end, y)

    # ============================================================
    # 小节绘制
    # ============================================================

    def _draw_measure(self, painter: QPainter, track: GTPTrack,
                      system: SystemLayout, m_layout: MeasureLayout) -> None:
        """绘制单个小节（包含小节线和所有拍）"""
        measure = m_layout.measure
        
        # 1. 绘制小节线（左侧）
        self._draw_barline(
            painter, 
            m_layout.x_start - 2, 
            system.y_tab_top - self.cfg.BARLINE_HEIGHT_EXTEND,
            system.y_tab_bottom + self.cfg.BARLINE_HEIGHT_EXTEND,
            is_open=measure.is_repeat_open
        )
        
        # 2. 绘制重复记号
        if measure.is_repeat_open:
            self._draw_repeat_dots(painter, m_layout.x_start - 2, 
                                   system.y_tab_top, system.y_tab_bottom, side='left')
        if measure.repeat_close > 0:
            # 右侧重复线 + 点
            self._draw_barline(
                painter,
                m_layout.x_end + 2,
                system.y_tab_top - self.cfg.BARLINE_HEIGHT_EXTEND,
                system.y_tab_bottom + self.cfg.BARLINE_HEIGHT_EXTEND,
                is_double=True
            )
            self._draw_repeat_dots(painter, m_layout.x_end + 2,
                                   system.y_tab_top, system.y_tab_bottom, side='right')
            # 重复次数标记
            painter.setPen(QColor(self.cfg.COLOR_REPEAT))
            painter.setFont(QFont(self.cfg.NOTE_FONT_FAMILY, 8))
            painter.drawText(int(m_layout.x_end + 8), int(system.y_tab_bottom + 14),
                           str(measure.repeat_close))
        
        # 3. 绘制段落标记
        if measure.marker:
            painter.setPen(QColor(self.cfg.COLOR_TECHNIQUE))
            painter.setFont(QFont(self.cfg.NOTE_FONT_FAMILY, 9, QFont.Bold))
            painter.drawText(int(m_layout.x_start), int(system.y_tab_top - 8),
                           measure.marker)
        
        # 4. 绘制每个拍（音符）
        for b_layout in m_layout.beats:
            self._draw_beat(painter, system, b_layout, m_layout)
        
        # 5. 绘制P.M./Let Ring延长虚线（需要在所有拍绘制完成后才能确定范围）
        self._draw_pm_letring_extensions(painter, system, m_layout)

    def _draw_barline(self, painter: QPainter, x: int, y_top: int, 
                      y_bottom: int, is_open: bool = False, 
                      is_double: bool = False) -> None:
        """绘制小节线"""
        pen = QPen(QColor(self.cfg.COLOR_BARLINE), self.cfg.BARLINE_THICKNESS)
        painter.setPen(pen)
        painter.drawLine(x, y_top, x, y_bottom)
        
        if is_double:
            painter.drawLine(x + 4, y_top, x + 4, y_bottom)
        
        if is_open:
            # 反复起始加粗线
            thick_pen = QPen(QColor(self.cfg.COLOR_BARLINE), 3)
            painter.setPen(thick_pen)
            painter.drawLine(x + 4, y_top, x + 4, y_bottom)

    def _draw_repeat_dots(self, painter: QPainter, x: int,
                          y_top: int, y_bottom: int, 
                          side: str = 'left') -> None:
        """绘制反复记号的两个点"""
        painter.setPen(QPen(QColor(self.cfg.COLOR_BARLINE), 3))
        dot_y1 = y_top + (y_bottom - y_top) // 3
        dot_y2 = y_bottom - (y_bottom - y_top) // 3
        offset = 6 if side == 'right' else -8
        painter.drawEllipse(x + offset, dot_y1 - 2, 4, 4)
        painter.drawEllipse(x + offset, dot_y2 - 2, 4, 4)

    # ============================================================
    # 拍(Beat)绘制 - 核心渲染逻辑
    # ============================================================

    def _draw_beat(self, painter: QPainter, system: SystemLayout,
                   b_layout: BeatLayout, m_layout: MeasureLayout = None) -> None:
        """
        绘制单个拍的所有内容：
          1. 品格数字（在对应弦线上）
          2. 符干（根据音符位置决定上下方向）
          3. 符尾（连接同组短时值音符）
          4. 技巧标记缩写
        
        参数:
            m_layout: 可选，传入时支持滑音连线查找下一个音符
        """
        beat = b_layout.beat
        cx = b_layout.x_center  # 该拍的中心X坐标
        
        # --- 休止符处理 ---
        if beat.is_rest and not beat.notes:
            self._draw_rest_symbol(painter, beat, cx, system)
            return
        
        # --- 按弦分组绘制品格数字 ---
        # 同一拍内不同弦上的音符垂直排列
        for note in beat.notes:
            self._draw_note_fret(painter, note, cx, system)
        
        # --- 绘制技巧标记（传入m_layout以支持滑音连线查找下一个音符）---
        for note in beat.notes:
            # 记录父拍引用，供滑音查找用
            note._parent_beat = beat
            self._draw_technique_marks(painter, note, cx, system, m_layout)
        
        # --- 绘制符干 ---
        self._draw_stem(painter, beat, b_layout, system)

    def _draw_note_fret(self, painter: QPainter, note, 
                        cx: int, system: SystemLayout) -> None:
        """
        在对应弦线上绘制品格数字
        
        坐标计算:
          Y坐标 = y_tab_top + string_index × TAB_LINE_SPACING
                 （string_index: 0=1弦顶线, 5=6弦底线）
          X坐标 = cx（拍的中心位置）
        
        文字居中策略: 让文字的视觉中心对齐到弦线位置，
                     避免品格数字超出六线谱区域（尤其是底部弦）。
                     公式: baseline = line_y - height/2 + ascent
        """
        # 计算Y坐标：弦索引越大越靠下（1弦在最上面）
        y = system.y_tab_top + note.string * self.cfg.TAB_LINE_SPACING
        
        # 字体设置
        font = QFont(self.cfg.NOTE_FONT_FAMILY, self.cfg.NOTE_FONT_SIZE)
        painter.setFont(font)
        
        # 颜色：幽灵音用灰色，正常音符用主文字色
        if note.is_ghost:
            painter.setPen(QColor("#666666"))
        else:
            painter.setPen(QColor(self.cfg.COLOR_TEXT))
        
        # 获取显示文本
        display_text = note.get_display_fret()
        
        # 居中绘制：文字中心对齐到弦线Y位置
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(display_text)
        text_x = cx - text_width // 2
        # 垂直居中：文字视觉中心对齐弦线，避免底部弦文字溢出
        text_y = y - fm.height() // 2 + fm.ascent()
        
        painter.drawText(QPoint(text_x, text_y), display_text)

    def _draw_technique_marks(self, painter: QPainter, note,
                               cx: int, system: SystemLayout,
                               m_layout: MeasureLayout = None) -> None:
        """
        绘制技巧标记（增强版：根据技巧类型选择不同的可视化方式）
        
        渲染策略（按优先级）:
          1. 泛音 → 菱形包围品格数字 + 缩写文字
          2. 滑音 → 斜线连接到下一个同弦音符 + 缩写文字
          3. 推弦 → 弧线箭头 + 文字
          4. 颤音 → 波浪线(~~~)在音符上方
          5. P.M. / Let Ring → 文字标记（虚线延长在小节级绘制）
          6. 其他 → 缩写文字显示在品格数字右侧
        
        参数:
            painter:   QPainter绑制对象
            note:      音符数据(含techniques列表)
            cx:        该拍的中心X坐标
            system:    系统布局(含Y坐标信息)
            m_layout:  小节布局(可选，用于滑音查找下一个音符位置)
        """
        if not note.techniques:
            return
        
        y_base = system.y_tab_top + note.string * self.cfg.TAB_LINE_SPACING
        
        # 按类型分别处理每种技巧的图形化渲染
        for tech in note.techniques:
            
            # --- 泛音：菱形包围品格数字 ---
            if tech in (TechniqueType.NATURAL_HARMONIC,
                        TechniqueType.ARTIFICIAL_HARMONIC,
                        TechniqueType.TAPPED_HARMONIC,
                        TechniqueType.PINCH_HARMONIC):
                self._draw_harmonic_diamond(painter, cx, y_base)
            
            # --- 滑音：斜线连接到下一个同弦音符 ---
            elif tech in (TechniqueType.SLIDE_UP, TechniqueType.SLIDE_DOWN):
                self._draw_slide_line(painter, note, cx, y_base, 
                                       system, m_layout, tech)
            
            # --- 推弦：弧线箭头 ---
            elif tech == TechniqueType.BEND:
                self._draw_bend_indicator(painter, cx, y_base, system)
            
            # --- 颤音：波浪线 ---
            elif tech == TechniqueType.VIBRATO:
                self._draw_vibrato_wave(painter, cx, y_base, system)
        
        # --- 绘制文字缩写标签（所有非图形化的技巧）---
        self._draw_technique_text_labels(painter, note, cx, system)

    def _draw_harmonic_diamond(self, painter: QPainter, 
                                cx: int, y_base: int) -> None:
        """
        绘制泛音菱形标记：在品格数字位置画一个菱形框
        
        原理: 泛音在标准记谱中用菱形音符头表示，
              六线谱中用菱形包围品格数字来模拟此效果。
              
        参数:
            cx:      品格数字中心X坐标
            y_base:  弦线Y坐标
        """
        painter.setPen(QPen(QColor(self.cfg.COLOR_TECHNIQUE), 1))
        # 菱形大小：约等于品格数字的大小
        size = 8  # 菱形半宽(px)，调整效果: 越大菱形越明显
        # 画菱形: 上→右→下→左→上
        diamond = [
            QPoint(cx, y_base - size),       # 顶点
            QPoint(cx + size, y_base),        # 右点
            QPoint(cx, y_base + size),        # 底点
            QPoint(cx - size, y_base),        # 左点
        ]
        painter.drawPolygon(diamond)

    def _draw_slide_line(self, painter: QPainter, note,
                         cx: int, y_base: int, system: SystemLayout,
                         m_layout: MeasureLayout, 
                         slide_type: TechniqueType) -> None:
        """
        绘制滑音连线：从当前音符画斜线到下一个同弦的音符
        
        原理: 滑音(slide)表示手指从当前品滑到目标品而不离弦。
              用斜线连接两个音符位置直观表达滑音方向：
              - 上滑(Slide Up): 线向右上方倾斜（品位升高）
              - 下滑(Slide Down): 线向右下方倾斜（品位降低）
        
        参数:
            note:       当前音符
            cx:         当前拍中心X
            y_base:     当前弦线Y
            system:     系统布局
            m_layout:   小节布局（用于查找下一个同弦音符的位置）
            slide_type: SLIDE_UP 或 SLIDE_DOWN
        """
        if not m_layout:
            return
        
        # 在同一小节的后续拍中查找下一个同弦音符
        target_cx = None
        target_fret = None
        found_current = False
        
        for b in m_layout.beats:
            if b.beat is note._parent_beat:
                found_current = True
                continue
            if not found_current:
                continue
            # 找到了后续拍，检查是否有同弦音符
            for n in b.beat.notes:
                if n.string == note.string:
                    target_cx = b.x_center
                    target_fret = n.fret
                    break
            if target_cx is not None:
                break
        
        if target_cx is None:
            return  # 没找到目标音符，不画连线
        
        # 设置滑线样式
        pen = QPen(QColor(self.cfg.COLOR_TECHNIQUE), 1)
        painter.setPen(pen)
        
        # 计算终点Y坐标（目标音符所在弦线）
        target_y = system.y_tab_top + note.string * self.cfg.TAB_LINE_SPACING
        
        # 根据滑音方向决定倾斜方向
        if slide_type == TechniqueType.SLIDE_UP:
            # 上滑：向右上方倾斜（即使实际目标品格更低也向上倾斜表示"滑向更高把位"）
            end_y = y_base - 6
        else:
            # 下滑：向右下方倾斜
            end_y = y_base + 6
        
        # 从品格数字右侧开始画线
        start_x = cx + 6
        painter.drawLine(start_x, y_base, target_cx - 4, end_y)

    def _draw_bend_indicator(self, painter: QPainter,
                              cx: int, y_base: int, 
                              system: SystemLayout) -> None:
        """
        绘制推弦指示器：在音符上方画一个向上的弧线箭头
        
        原理: 推弦(bend)通过将弦推向/拉向来升高音高。
              标准记谱法中用向上弯曲的箭头+度数标注(如"Full"、"1/2")。
              六线谱简化为：弧线箭头 + "B"文字。
        
        参数:
            cx:      拍中心X坐标
            y_base:  弦线Y坐标
            system:  系统布局
        """
        pen = QPen(QColor(self.cfg.COLOR_TECHNIQUE), 1.5)
        painter.setPen(pen)
        
        # 弧线起点：品格数字上方
        arc_start_x = cx - 4
        arc_start_y = y_base - 10
        # 弧线终点（向上弯曲后回落）
        arc_end_x = cx + 8
        arc_end_y = y_base - 4
        
        # 画弧线（用二次贝塞尔曲线模拟）
        # 控制点在弧线上方，形成向上凸起的形状
        ctrl_x = cx + 2
        ctrl_y = y_base - 18  # 弧线高度，调整效果: 越高推弦感越强
        
        # QPainterPath 画贝塞尔曲线
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(arc_start_x, arc_start_y)
        path.quadTo(ctrl_x, ctrl_y, arc_end_x, arc_end_y)
        painter.drawPath(path)
        
        # 画箭头尖端
        arrow_size = 3
        painter.drawLine(arc_end_x, arc_end_y, 
                        arc_end_x - arrow_size, arc_end_y + arrow_size)
        painter.drawLine(arc_end_x, arc_end_y,
                        arc_end_x - arrow_size, arc_end_y - arrow_size)

    def _draw_vibrato_wave(self, painter: QPainter,
                           cx: int, y_base: int,
                           system: SystemLayout) -> None:
        """
        绘制颤音波浪线：在音符上方画 "~~~" 形状的波浪线
        
        原理: 颤音(vibrato)通过快速小幅摇动按弦手指产生音高波动。
              记谱法中使用波浪线(~)表示。六线谱中画在品格数字正上方。
        
        参数:
            cx:      拍中心X坐标
            y_base:  弦线Y坐标
            system:  系统布局
        """
        pen = QPen(QColor(self.cfg.COLOR_TECHNIQUE), 1)
        painter.setPen(pen)
        
        # 波浪线参数
        wave_y = y_base - 14  # 波浪线基线Y（品格数字上方）
        wave_width = 5        # 每个波的宽度(px)
        wave_height = 2       # 波浪振幅(px)
        wave_count = 3        # 波的数量（~~~ = 3个波）
        
        start_x = cx - (wave_width * wave_count) // 2
        
        # 用小线段拼接出波浪效果
        points = []
        for i in range(wave_count * 2 + 1):
            px = start_x + i * (wave_width // 2)
            if i % 2 == 0:
                py = wave_y
            else:
                py = wave_y + wave_height
            points.append(QPoint(px, py))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

    def _draw_technique_text_labels(self, painter: QPainter, note,
                                     cx: int, system: SystemLayout) -> None:
        """
        绘制技巧文字标签（用于不需要图形化或已有图形化但还需补充文字的技巧）
        
        显示规则:
          - 单字符标记(H/P/s/B/>/.等): 显示在品格数字右侧
          - 多字符标记(P.M./Let Ring/N.H.等): 显示在六线谱下方区域
          - 已有图形化的技巧(泛音/滑音/推弦/颤音): 也同时显示简短文字辅助说明
        
        参数:
            painter: QPainter绑制对象
            note:    音符数据
            cx:      拍中心X坐标
            system:  系统布局
        """
        if not note.techniques:
            return
        
        painter.setPen(QColor(self.cfg.COLOR_TECHNIQUE))
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 8)
        painter.setFont(font)
        
        # 收集需要显示文字的技巧（排除纯图形化不需要额外文字的）
        text_techs = []
        for tech in note.techniques:
            abbr = TECHNIQUE_ABBREVIATION.get(tech, tech.value)
            text_techs.append(abbr)
        
        if not text_techs:
            return
        
        tech_text = ''.join(text_techs)
        y_base = system.y_tab_top + note.string * self.cfg.TAB_LINE_SPACING
        
        # 长标记放在六线谱下方（P.M., Let Ring 等），避免遮挡品格数字
        if len(tech_text) > 3:
            tech_y = system.y_tab_bottom + 4
        else:
            # 短标记放在品格数字右下方
            tech_y = y_base + 12
        
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(tech_text)
        text_x = cx + (self.cfg.NOTE_FONT_SIZE // 2) + 2
        
        painter.drawText(QPoint(text_x, tech_y), tech_text)

    def _draw_pm_letring_extensions(self, painter: QPainter,
                                     system: SystemLayout,
                                     m_layout: MeasureLayout) -> None:
        """
        绘制P.M.(闷音)和Let Ring(延音)的延长虚线
        
        原理: 当连续多个音符都有P.M.或Let Ring技巧时，
              在这些音符下方画一条水平虚线表示该技巧持续有效，
              避免每个音符都重复标注"P.M."文字造成视觉混乱。
        
        参数:
            painter:  QPainter绑制对象
            system:  系统布局
            m_layout: 小节布局（包含该小节所有拍的列表）
        """
        # 收集所有有P.M.或Let Ring的音符及其X坐标
        pm_notes = []   # (x_center, string, tech_type) 列表
        lr_notes = []
        
        for b_layout in m_layout.beats:
            for note in b_layout.beat.notes:
                if note.has_technique(TechniqueType.PALM_MUTE):
                    pm_notes.append((b_layout.x_center, note.string))
                if note.has_technique(TechniqueType.LET_RING):
                    lr_notes.append((b_layout.x_center, note.string))
        
        # 为P.M.画虚线（在同一弦上连续的P.M.音符之间画线）
        self._draw_dashed_extension_line(
            painter, pm_notes, system, "P.M.", QColor(self.cfg.COLOR_TECHNIQUE)
        )
        
        # 为Let Ring画虚线
        self._draw_dashed_extension_line(
            painter, lr_notes, system, "Let Ring", QColor("#60A5FA")
        )

    def _draw_dashed_extension_line(self, painter: QPainter,
                                     notes_info: list, system: SystemLayout,
                                     label: str, color: QColor) -> None:
        """
        绘制通用虚线延长线（P.M. / Let Ring 共用方法）
        
        参数:
            notes_info: [(x_center, string), ...] 音符位置列表
            system:     系统布局
            label:      线段起始处的文字标签("P.M." 或 "Let Ring")
            color:      线条颜色
        """
        if len(notes_info) < 2:
            return  # 只有1个音符无需画延长线
        
        # 按X坐标排序
        notes_info.sort(key=lambda x: x[0])
        
        # 取第一个和最后一个音符的位置作为线的起止点
        first_x, first_str = notes_info[0]
        last_x, last_str = notes_info[-1]
        
        # Y坐标：六线谱底部下方
        line_y = system.y_tab_bottom + 8
        
        # 画虚线
        pen = QPen(color, 1, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(first_x + 8, line_y, last_x - 4, line_y)
        
        # 在起始位置画标签文字
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 7)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(QPoint(first_x - 2, line_y + 3), label)

    def _draw_stem(self, painter: QPainter, beat, 
                   b_layout: BeatLayout, system: SystemLayout) -> None:
        """
        绘制符干
        
        规则:
          - 全音符/二分音符：无符干（仅空心的全音符头在五线谱中适用，六线谱中省略）
          - 四分音符及更短：有符干
          - 符干方向：音符在第3弦及以上 → 向上；第4弦及以下 → 向下
          - 八分音符及更短：需要画符尾(beams)
        """
        if not beat.notes:
            return
        
        dur_val = beat.duration.value
        
        # 全音符和二分音符不画符干（六线谱简化处理）
        if dur_val <= NoteDuration.HALF.value:
            return
        
        # 确定符干方向和基准点
        highest_string = beat.get_highest_string()
        lowest_string = beat.get_lowest_string()
        
        # 符干方向统一向下：所有符干从第6弦线下方延伸，符尾在下方
        # 这样视觉上更整洁，符尾不会与上方内容重叠
        stem_up = False
        
        if stem_up:
            # 符干向上：从第1弦线上方延伸
            stem_base_y = system.y_tab_top - 2
            stem_tip_y = stem_base_y - self.cfg.STEM_HEIGHT
        else:
            # 符干向下：从第6弦线下方延伸
            stem_base_y = system.y_tab_bottom + 2
            stem_tip_y = stem_base_y + self.cfg.STEM_HEIGHT
        
        # 绘制符干线
        pen = QPen(QColor(self.cfg.COLOR_STEM), self.cfg.STEM_THICKNESS)
        painter.setPen(pen)
        painter.drawLine(b_layout.x_center, stem_base_y,
                        b_layout.x_center, stem_tip_y)
        
        # 绘制符尾（八分音符及更短）
        if dur_val >= NoteDuration.EIGHTH.value:
            self._draw_beam_flags(painter, beat, b_layout, 
                                  system, stem_up, stem_tip_y)

    def _draw_beam_flags(self, painter: QPainter, beat,
                         b_layout: BeatLayout, system: SystemLayout,
                         stem_up: bool, stem_tip_y: int) -> None:
        """
        绘制符尾旗（单个拍独立时的斜杠标记）
        
        符尾规则:
          - 八分音符: 1条符尾旗
          - 十六分音符: 2条符尾旗（平行）
          - 三十二分音符: 3条符尾旗（平行）
          - 符尾方向与符干相反：向下符干 → 符尾向右上倾斜
        
        注意: MVP阶段暂不实现跨拍的连梁(beaming)，
              仅在每个拍上绘制独立的符尾旗。
        """
        dur_val = beat.duration.value
        cx = b_layout.x_center
        
        # 符尾数量：八分=1, 十六分=2, 三十二分=3
        flag_count = 0
        if dur_val >= NoteDuration.EIGHTH.value:
            flag_count += 1
        if dur_val >= NoteDuration.SIXTEENTH.value:
            flag_count += 1
        if dur_val >= NoteDuration.THIRTY_SECOND.value:
            flag_count += 1
        
        pen = QPen(QColor(self.cfg.COLOR_BEAM), 1.5)  # 加粗使符尾更清晰
        painter.setPen(pen)
        
        beam_h = self.cfg.BEAM_HEIGHT
        flag_len = 7  # 符尾旗长度(px)，调整效果: 越长越明显
        
        for i in range(flag_count):
            offset = i * 4  # 多个符尾之间的垂直间距(px)
            if stem_up:
                # 向上的符尾旗：向右下方倾斜
                painter.drawLine(cx, stem_tip_y + offset,
                               cx + flag_len, stem_tip_y + offset + beam_h)
            else:
                # 向下的符尾旗：向右上方倾斜
                painter.drawLine(cx, stem_tip_y - offset,
                               cx + flag_len, stem_tip_y - offset - beam_h)
        
        # --- 附点标记：在符尾旁边画一个小圆点 ---
        if beat.is_dotted:
            dot_cx = cx + flag_len + 4  # 附点在符尾右侧
            dot_cy = stem_tip_y  # 与符干末端对齐
            painter.setPen(QPen(QColor(self.cfg.COLOR_BEAM), 1.5))
            painter.setBrush(QColor(self.cfg.COLOR_BEAM))
            painter.drawEllipse(dot_cx, dot_cy - 2, 4, 4)

    def _draw_rest_symbol(self, painter: QPainter, beat,
                          cx: int, system: SystemLayout) -> None:
        """
        绘制休止符符号（根据时值绘制不同的休止符形状）
        
        休止符规则:
          - 全休止符: 悬挂在小节线上方的一条短粗线（类似"⊥"倒置）
          - 二分休止符: 坐落在小节线上的短粗线（类似"⊥"）
          - 四分休止符: 锯齿形/闪电形符号
          - 八分休止符: 类似数字"7"的圆形符号
          - 更短时值: 在四分休止符基础上加符尾
        
        参数:
            painter: QPainter绑制对象
            beat:    休止符拍的时值信息
            cx:      X坐标（拍中心）
            system:  系统布局（含Y坐标）
        """
        dur_val = beat.duration.value
        y_center = system.y_tab_top + 2.5 * self.cfg.TAB_LINE_SPACING  # 六线谱中心Y
        y_top = system.y_tab_top
        y_bottom = system.y_tab_bottom
        
        painter.setPen(QPen(QColor(self.cfg.COLOR_TEXT), 1.5))
        
        if dur_val == NoteDuration.WHOLE.value:
            # === 全休止符：悬挂式矩形块 ===
            # 标准记谱法中全休止符悬挂在第四线下方，六线谱简化为悬挂在最上方
            rh = 6   # 矩形高度(px)
            rw = 8   # 矩形宽度(px)
            rx = cx - rw // 2
            ry = y_top - rh - 2  # 悬挂在六线谱上方
            painter.setBrush(QColor(self.cfg.COLOR_TEXT))
            painter.drawRect(rx, ry, rw, rh)
            
        elif dur_val == NoteDuration.HALF.value:
            # === 二分休止符：坐落式矩形块 ===
            rh = 6
            rw = 8
            rx = cx - rw // 2
            ry = y_top + 2  # 坐落在六线谱顶部区域
            painter.setBrush(QColor(self.cfg.COLOR_TEXT))
            painter.drawRect(rx, ry, rw, rh)
            
        elif dur_val == NoteDuration.QUARTER.value:
            # === 四分休止符：锯齿形/闪电形 ===
            # 用折线模拟标准四分休止符的锯齿形状
            points = [
                QPoint(cx + 3, int(y_top + 4)),      # 右上起点
                QPoint(cx - 3, int(y_center)),         # 左下拐角
                QPoint(cx + 4, int(y_bottom - 6)),     # 右上拐角
                QPoint(cx - 2, int(y_bottom - 2)),     # 终点
            ]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
                
        else:
            # === 八分及更短休止符：类似"7"的圆弧 + 符尾 ===
            # 画一个左开口的圆弧（类似"7"的上半部分）
            arc_r = 5  # 圆弧半径
            painter.drawArc(cx - arc_r, y_center - arc_r - 4,
                           arc_r * 2, arc_r * 2,
                           180 * 16, 160 * 16)  # 从左边开始画约160度的弧
            
            # 画竖线向下（"7"的下半部分）
            painter.drawLine(cx + arc_r - 2, y_center - 2, 
                            cx + arc_r - 2, y_center + 10)
            
            # 附点标记
            if beat.is_dotted:
                dot_x = cx + arc_r + 3
                dot_y = y_center + 2
                painter.setBrush(QColor(self.cfg.COLOR_TEXT))
                painter.drawEllipse(dot_x, dot_y, 3, 3)
        
        # 附点（全音符和二分音符也支持附点）
        if beat.is_dotted and dur_val <= NoteDuration.HALF.value:
            dot_x = cx + 6
            dot_y = (y_top + y_bottom) // 2
            painter.setBrush(QColor(self.cfg.COLOR_TEXT))
            painter.drawEllipse(dot_x, dot_y, 3, 3)

    # ============================================================
    # 页码绘制
    # ============================================================

    @staticmethod
    def _draw_page_number(painter: QPainter, text: str, 
                          width: int, height: int) -> None:
        """绘制页码"""
        painter.setPen(QColor("#666666"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(QRect(0, height - 25, width, 20),
                        Qt.AlignCenter, text)


# ============================================================
# 便捷函数
# ============================================================

def render_gtp(file_path: str, track_index: int = 0) -> List[QPixmap]:
    """
    便捷函数：解析并渲染Guitar Pro文件
    
    参数:
        file_path:    .gp3/.gp4/.gp5/.gpx 文件路径
        track_index:  要渲染的音轨索引（默认0=第一条）
        
    返回:
        QPixmap列表，每页一张图片
        
    示例:
        >>> from gtp_engine.renderer import render_gtp
        >>> pages = render_gtp("song.gp5", track_index=2)
        >>> print(f"共 {len(pages)} 页")
    """
    from ..parser.gtp_parser import parse_gtp
    song = parse_gtp(file_path)
    renderer = TabRenderer()
    return renderer.render(song, track_index=track_index)
