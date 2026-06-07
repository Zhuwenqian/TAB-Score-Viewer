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
  - _draw_beat(): 绘制单个拍(品格数字 + 技巧标记 + 符干符尾, 含休止符过滤)
  - _draw_technique_marks(): 技巧标记分发器，按类型调用对应绘制方法
  - _draw_dashed_extension_line(): P.M./Let Ring GP5格式虚线(strict参数控制断开策略)

依赖库:
  - PyQt5 (QPainter, QPixmap, QFont, QPen, QColor, QPainterPath等)
  - 内部依赖: gtp_engine.models.*, layout_engine.*, utils.constants

创建日期: 2026-06-06
最后更新: 2026-06-07 (v1.2.2: GP5格式推弦渲染+休止符规则优化+空小节过滤)
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
          2. 信息栏（TAB标识 + 谱号 + 拍号 + 调号）— 仅每行第一系统绘制
          3. 每个小节的内容（小节线 + 音符 + 技巧标记）
        
        信息栏设计（参照 Guitar Pro 标准布局）:
          - 最左侧: "T A B" 竖排文字（标识这是六线谱）
          - 中部: 拍号(如4/4上下堆叠) + 调号升降号数
          - 上方: 调性名称(如C5, G3等)
          - 用竖线与后续小节内容分隔
        """
        
        # 1. 绘制六条弦线
        self._draw_tab_lines(painter, system)
        
        # 2. 在该系统第一个小节前绘制独立信息栏
        if system.measures:
            first_measure = system.measures[0].measure
            self._draw_info_bar(painter, first_measure, system)
        
        # 3. 绘制每个小节的内容
        for m_layout in system.measures:
            self._draw_measure(painter, track, system, m_layout)

    def _draw_info_bar(self, painter: QPainter,
                       measure, system: SystemLayout) -> None:
        """
        绘制独立信息栏（每行系统开头，类似 Guitar Pro 的谱号区域）
        
        布局结构（从左到右）:
          ┌────┬─────┬──────┬────┐
          │    │调性 │      │    │
          │ T │拍号 │      │ 小│
          │ A │4/4 │ 竖线 │ 节 │
          │ B │     │      │ 内│
          │    │     │      │ 容│
          └────┴─────┴──────┴────┘
        
        参数:
            painter: QPainter绑制对象
            measure: 该行第一个小节（含拍号/调号信息）
            system:  系统布局（含Y坐标）
        """
        # --- 布局参数（信息栏总宽度约55px）---
        tab_x = self.cfg.PAGE_MARGIN_LEFT - 38   # TAB文字X坐标
        clef_x = self.cfg.PAGE_MARGIN_LEFT - 24  # 谱号线X坐标
        ts_x = self.cfg.PAGE_MARGIN_LEFT - 6     # 拍号X坐标  
        divider_x = self.cfg.PAGE_MARGIN_LEFT + 18  # 分隔线X坐标
        
        y_top = system.y_tab_top
        y_bot = system.y_tab_bottom
        y_mid = (y_top + y_bot) // 2
        
        # ===== 1. "T A B" 竖排文字（最左侧）=====
        painter.setPen(QColor(self.cfg.COLOR_TEXT))
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 8, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        # 竖向排列 T / A / B，均匀分布在六线谱高度范围内
        tab_letters = ['T', 'A', 'B']
        tab_spacing = (y_bot - y_top) // (len(tab_letters) + 1)
        for i, letter in enumerate(tab_letters):
            ly = y_top + tab_spacing * (i + 1) + 3  # +3使视觉居中
            tw = fm.horizontalAdvance(letter)
            painter.drawText(QPoint(tab_x - tw // 2, int(ly)), letter)
        
        # ===== 2. 谱号竖线（类似高音谱号的简化表示）=====
        pen = QPen(QColor(self.cfg.COLOR_TEXT), 1.5)
        painter.setPen(pen)
        # 画一条从第2弦到第5弦的竖线（模拟谱号主体）
        line_y1 = y_top + int(self.cfg.TAB_LINE_SPACING * 1)  # 第2弦位置
        line_y2 = y_top + int(self.cfg.TAB_LINE_SPACING * 4.5)  # 接近第5弦底部
        painter.drawLine(clef_x, line_y1, clef_x, line_y2)
        # 底部小弯钩（模拟谱号尾部曲线）
        from PyQt5.QtGui import QPainterPath
        hook_path = QPainterPath()
        hook_path.moveTo(clef_x, line_y2)
        hook_path.cubicTo(clef_x + 5, line_y2 - 3, 
                         clef_x + 6, line_y2 + 2, 
                         clef_x + 2, line_y2 + 6)
        painter.drawPath(hook_path)
        
        # ===== 3. 拍号（分子在上，分母在下）=====
        numerator, denominator = measure.time_signature
        
        # 始终显示拍号（Guitar Pro 风格：每行开头都显示）
        font_ts = QFont(self.cfg.NOTE_FONT_FAMILY, 11, QFont.Bold)
        painter.setFont(font_ts)
        fm_ts = QFontMetrics(font_ts)
        
        # 分子（上数字）：位于六线谱上半部分
        num_text = str(numerator)
        num_w = fm_ts.horizontalAdvance(num_text)
        painter.drawText(QPoint(ts_x - num_w // 2, int(y_top + self.cfg.TAB_LINE_SPACING * 1.5 + 9)), 
                        num_text)
        
        # 分母（下数字）：位于六线谱下半部分
        den_text = str(denominator)
        den_w = fm_ts.horizontalAdvance(den_text)
        painter.drawText(QPoint(ts_x - den_w // 2, int(y_top + self.cfg.TAB_LINE_SPACING * 4 + 4)), 
                        den_text)
        
        # ===== 4. 调号（在拍号上方显示调性名称或升降号数）=====
        key_sig = measure.key_signature
        if isinstance(key_sig, (list, tuple)):
            key_val = key_sig[0] if len(key_sig) > 0 else 0
        else:
            key_val = key_sig if key_sig else 0
        
        font_key = QFont(self.cfg.NOTE_FONT_FAMILY, 7)
        painter.setFont(font_key)
        painter.setPen(QColor("#888888"))  # 灰色次要信息
        
        if key_val > 0:
            key_text = f"#{key_val}"
        elif key_val < 0:
            key_text = f"b{abs(key_val)}"
        else:
            key_text = ""  # C大调不显示或显示"C"
        
        if key_text:
            fm_key = QFontMetrics(font_key)
            kw = fm_key.horizontalAdvance(key_text)
            painter.drawText(QPoint(ts_x - kw // 2, int(y_top) - 4), key_text)
        
        # ===== 5. 右侧分隔线（双细线，类似GP的小节线风格）=====
        pen_div = QPen(QColor(self.cfg.COLOR_BARLINE), 1)
        painter.setPen(pen_div)
        painter.drawLine(divider_x, y_top - 2, divider_x, y_bot + 2)
        painter.drawLine(divider_x + 3, y_top - 2, divider_x + 3, y_bot + 2)

    def _draw_time_signature(self, painter: QPainter,
                              measure, system: SystemLayout) -> None:
        """
        [已废弃] 拍号绘制已合并到 _draw_info_bar() 中统一处理。
        此方法保留仅作向后兼容。
        """

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
        # 休止符渲染规则（严格参照 Guitar Pro 5 的六线谱行为）:
        #   规则1: 完全空的小节（所有拍都是休止符，无任何音符）→ 不画任何休止符
        #          GP5中空小节完全空白，只有小节线
        #   规则2: 有音符的小节中的休止拍 → 仅绘制有意义的休止符
        #          （排除末尾填充空拍：最后1个拍且时值≥四分音符）
        #   规则3: 全休止符/二分休止符 → 改用细线框样式（避免填充矩形看起来像□）
        if beat.is_rest and not beat.notes:
            # === 规则1: 检查整个小节是否完全为空（无任何音符）===
            is_empty_measure = True
            if m_layout and m_layout.beats:
                for other_bl in m_layout.beats:
                    if other_bl.beat.notes:  # 只要有一个拍包含音符
                        is_empty_measure = False
                        break
            
            # 空小节完全不画休止符
            if is_empty_measure:
                return
            
            # === 规则2: 检查是否为末尾填充空拍 ===
            is_meaningful_rest = True
            if m_layout and m_layout.beats:
                try:
                    beat_idx = m_layout.beats.index(b_layout)
                    # 如果是小节最后一个拍，且时值为四分或更长 → 可能是填充
                    if beat_idx == len(m_layout.beats) - 1:
                        if beat.duration.value <= NoteDuration.QUARTER.value:
                            is_meaningful_rest = False
                except ValueError:
                    pass
            
            if is_meaningful_rest:
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
                self._draw_bend_indicator(painter, note, cx, y_base, system)
            
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
                              note, cx: int, y_base: int,
                              system: SystemLayout) -> None:
        """
        绘制推弦指示器 - 严格参照 Guitar Pro 5 的推弦记谱格式
        
        GP5 推弦格式（3种类型）:
          类型1(完整推+释放):  "1/4"文字 + 上弧线↑ + 下弧线↓ 回到原位
          类型2(仅推弦):      "1/4"文字 + 上弧线↑ (不回)
          类型3(推+保持+释放): "1/2"文字 + 上弧线↑ + 虚线横线 + ↓
        
        视觉特征:
          - 度数文字("1/4"/"1/2"/"Full")在弧线上方居中显示
          - 弧线从品格数字下方开始，向上弯曲
          - 峰值处有向上箭头(▲)
          - 有释放时末端有向下箭头(▼)或虚线段
        
        参数:
            note:    音符对象(含bend属性:BendData)
            cx:      拍中心X坐标
            y_base:  弦线Y坐标
            system:  系统布局
        
        数据来源: note.bend (BendData对象, 从GTP文件解析的BendEffect)
        """
        # 获取推弦数据
        bend = getattr(note, 'bend', None)
        if not bend or not bend.points:
            # 无详细数据时用简单渲染(向后兼容)
            self._draw_bend_simple(painter, cx, y_base, system)
            return
        
        pen = QPen(QColor(self.cfg.COLOR_TECHNIQUE), 1.5)
        painter.setPen(pen)
        
        # === 布局参数 ===
        text = bend.get_display_text()  # "1/4", "1/2", "Full"
        
        # 弧线起点：品格数字下方偏左
        start_x = cx - 6
        start_y = y_base + 6
        
        # 弧线高度（根据推弦量动态调整）
        arc_height_map = {25: 14, 50: 18, 75: 22, 100: 26}  # px高度
        arc_h = arc_height_map.get(bend.max_value, 20)
        
        # 弧线总宽度
        total_w = 16  # 基础宽度(px)，调整效果: 增大则弧线更宽更平缓
        
        # 峰值点坐标
        peak_x = start_x + total_w * 0.45
        peak_y = start_y - arc_h
        
        # 终点坐标
        end_x = start_x + total_w
        end_y = start_y if bend.has_release else peak_y  # 有释放则回到起点Y
        
        # === 1. 绘制度数文字（在弧线上方）===
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 7)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        text_x = peak_x - tw // 2
        text_y = peak_y - 8  # 文字在峰值上方
        painter.drawText(QPoint(int(text_x), int(text_y)), text)
        
        # === 2. 绘制上弯弧线（从起点到峰值）===
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(start_x, start_y)
        # 二次贝塞尔曲线：控制点在起止点连线的上方中点
        ctrl_x = (start_x + peak_x) / 2
        ctrl_y = min(start_y, peak_y) - arc_h * 0.3  # 控制点略高于峰值
        path.quadTo(ctrl_x, ctrl_y, peak_x, peak_y)
        painter.drawPath(path)
        
        # === 3. 在峰值处画向上箭头 ▲ ===
        arr_size = 4  # 箭头大小(px)
        painter.drawLine(int(peak_x), int(peak_y),
                        int(peak_x - arr_size), int(peak_y + arr_size * 0.8))
        painter.drawLine(int(peak_x), int(peak_y),
                        int(peak_x + arr_size), int(peak_y + arr_size * 0.8))
        
        # === 4. 如果有释放段，绘制下弯弧线或虚线+下箭头 ===
        if bend.has_release:
            # 判断释放方式：如果终点接近起点Y值 → 用平滑回曲线(Image1风格)
            # 否则用虚线横线+下箭头(Image3风格)
            release_path = QPainterPath()
            release_path.moveTo(peak_x, peak_y)
            
            # 用二次贝塞尔曲线绘制释放段（从峰值回落到终点）
            r_ctrl_x = (peak_x + end_x) / 2
            r_ctrl_y = min(peak_y, end_y) - arc_h * 0.15  # 释放段控制点较平
            release_path.quadTo(r_ctrl_x, r_ctrl_y, end_x, end_y)
            painter.drawPath(release_path)
            
            # 在终点处画向下箭头 ▼
            painter.drawLine(int(end_x), int(end_y),
                           int(end_x - arr_size), int(end_y - arr_size * 0.8))
            painter.drawLine(int(end_x), int(end_y),
                           int(end_x + arr_size), int(end_y - arr_size * 0.8))

    def _draw_bend_simple(self, painter: QPainter,
                          cx: int, y_base: int,
                          system: SystemLayout) -> None:
        """
        简单推弦渲染（无详细数据时的后备方案）
        仅画一个基础弧线箭头，不显示度数文字
        """
        pen = QPen(QColor(self.cfg.COLOR_TECHNIQUE), 1.5)
        painter.setPen(pen)
        
        arc_start_x = cx - 4
        arc_start_y = y_base - 10
        arc_end_x = cx + 8
        arc_end_y = y_base - 4
        
        ctrl_x = cx + 2
        ctrl_y = y_base - 18
        
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(arc_start_x, arc_start_y)
        path.quadTo(ctrl_x, ctrl_y, arc_end_x, arc_end_y)
        painter.drawPath(path)
        
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
          - P.M. 和 Let Ring 不在此处绘制（由 _draw_pm_letring_extensions 统一画虚线+标签）
        
        参数:
            painter: QPainter绑制对象
            note:    音符数据
            cx:      拍中心X坐标
            system:  系统布局
        """
        if not note.techniques:
            return
        
        # P.M.和Let Ring由虚线延长方法统一处理，此处跳过避免重复标注
        SKIP_TECHS = {TechniqueType.PALM_MUTE, TechniqueType.LET_RING}
        
        painter.setPen(QColor(self.cfg.COLOR_TECHNIQUE))
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 8)
        painter.setFont(font)
        
        # 收集需要显示文字的技巧（排除纯图形化和P.M./Let Ring）
        text_techs = []
        for tech in note.techniques:
            if tech in SKIP_TECHS:
                continue  # 跳过P.M.和Let Ring，由虚线方法处理
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
        # 收集所有有P.M.或Let Ring的**拍**及其完整位置信息
        # 使用 BeatLayout 的 x_start/x_end/x_center 确保虚线长度跟随时值
        pm_beats = []   # (x_start, x_end, x_center) 列表 — 每个有P.M.的拍
        lr_beats = []
        
        for b_layout in m_layout.beats:
            has_pm = any(note.has_technique(TechniqueType.PALM_MUTE)
                         for note in b_layout.beat.notes)
            has_lr = any(note.has_technique(TechniqueType.LET_RING)
                         for note in b_layout.beat.notes)
            if has_pm:
                pm_beats.append((b_layout.x_start, b_layout.x_end,
                                 b_layout.x_center))
            if has_lr:
                lr_beats.append((b_layout.x_start, b_layout.x_end,
                                 b_layout.x_center))
        
        # 为P.M.画虚线（基于拍的时值宽度）
        self._draw_dashed_extension_line(
            painter, pm_beats, system, "P.M.", QColor(self.cfg.COLOR_TECHNIQUE)
        )
        
        # 为Let Ring画虚线（GP5格式：小写 + 跨拍连线，更严格断开）
        self._draw_dashed_extension_line(
            painter, lr_beats, system, "let ring", QColor("#60A5FA"),
            strict=True
        )

    def _draw_dashed_extension_line(self, painter: QPainter,
                                     beats_info: list, system: SystemLayout,
                                     label: str, color: QColor,
                                     strict: bool = False) -> None:
        """
        绘制通用虚线延长线（P.M. / Let Ring 共用方法）
        
        严格参照 Guitar Pro 5 的渲染格式:
          - P.M.: "P.M.----|" (大写 + 虚线跨拍连接 + 停止竖线)
          - Let Ring: "let ring ----|" (小写 + 虚线跨拍连接 + 停止竖线)
          - 每个**有技巧的拍**独立绘制: 标签文字 + 虚线
          - 虚线长度 = 该拍的 x_start → x_end（严格跟随时值）
          - **连续技巧拍**之间用虚线贯通连接（不重复画标签）
          - 每段连续技巧**末尾画竖线 |** 表示技巧停止
        
        参数:
            beats_info: [(x_start, x_end, x_center), ...] 有技巧的拍的位置列表
            system:     系统布局
            label:      文字标签("P.M." 或 "let ring")
            color:      线条颜色
            strict:     是否使用严格断开模式(Let Ring=True, P.M.=False)
                        True: 间距 > 1.3倍标准拍间距就断开（中间隔1个非技巧拍即分段）
                        False: 用相对阈值(1.3倍平均间距)，适合密集的P.M.
        """
        if len(beats_info) < 1:
            return
        
        # 按X坐标排序
        beats_info.sort(key=lambda b: b[0])
        
        line_y = int(system.y_tab_bottom + 8)
        
        # 设置虚线样式
        pen = QPen(color, 1, Qt.DashLine)
        
        # 字体设置
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 7)
        painter.setFont(font)
        
        # 计算连续判断阈值
        if strict:
            # 严格模式(Let Ring): 基于标准拍间距的绝对阈值
            # 间距 > 1.3倍NOTE_MIN_SPACING 就认为中间隔了非技巧拍，需要断开
            beat_spacing = self.cfg.NOTE_MIN_SPACING
            continuous_threshold = beat_spacing * 1.3  # 约34px
        else:
            # 宽松模式(P.M.): 基于实际数据相对阈值
            gaps = [beats_info[i+1][0] - beats_info[i][2]
                    for i in range(len(beats_info) - 1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else beat_spacing
            continuous_threshold = avg_gap * 1.3
        
        i = 0
        while i < len(beats_info):
            seg_start = i
            
            # 找到当前连续段的结束位置
            seg_end = i
            while seg_end < len(beats_info) - 1:
                next_gap = beats_info[seg_end + 1][0] - beats_info[seg_end][2]
                if next_gap > continuous_threshold:
                    break
                seg_end += 1
            
            # === 绘制这一段连续的技巧拍 ===
            
            # 第一拍起始位置画标签文字
            sx = int(beats_info[seg_start][0])
            
            painter.setPen(color)
            painter.drawText(QPoint(sx + 2, line_y + 3), label)
            
            # 从标签后面画虚线到整段最后拍的结束位置
            # 根据标签文字长度计算虚线起点
            label_width = len(label) * 7 + 4  # 根据文字长度估算宽度(px)
            dash_start = sx + label_width
            total_end_x = int(beats_info[seg_end][1]) - 2
            
            if dash_start < total_end_x:
                painter.setPen(pen)
                painter.drawLine(dash_start, line_y, total_end_x, line_y)
            
            # 在整段末尾画竖线 | 表示停止
            painter.setPen(color)
            stop_x = int(beats_info[seg_end][1])
            painter.drawLine(stop_x, line_y - 4, stop_x, line_y + 5)
            
            i = seg_end + 1

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
        y_center = int(system.y_tab_top + 2.5 * self.cfg.TAB_LINE_SPACING)  # 六线谱中心Y(转int)
        y_top = system.y_tab_top
        y_bottom = system.y_tab_bottom
        
        painter.setPen(QPen(QColor(self.cfg.COLOR_TEXT), 1.5))
        
        if dur_val == NoteDuration.WHOLE.value:
            # === 全休止符：悬挂式细线框 ===
            # 标准记谱法中全休止符悬挂在第四线下方
            # 六线谱简化为悬挂在最上方，用细线矩形而非填充块(避免看起来像□)
            rh = 6   # 矩形高度(px)，调整效果: 增大则符号更高
            rw = 8   # 矩形宽度(px)，调整效果: 增宽则符号更胖
            rx = cx - rw // 2
            ry = int(y_top) - rh - 2  # 悬挂在六线谱上方
            painter.setBrush(Qt.NoBrush)  # 不填充，只用细线边框
            painter.drawRect(rx, int(ry), rw, rh)
            
        elif dur_val == NoteDuration.HALF.value:
            # === 二分休止符：坐落式细线框 ===
            rh = 6   # 矩形高度(px)
            rw = 8   # 矩形宽度(px)
            rx = cx - rw // 2
            ry = int(y_top) + 2  # 坐落在六线谱顶部区域
            painter.setBrush(Qt.NoBrush)  # 不填充，只用细线边框
            painter.drawRect(rx, int(ry), rw, rh)
            
        elif dur_val == NoteDuration.QUARTER.value:
            # === 四分休止符：紧凑锯齿形 ===
            # 用折线模拟标准四分休止符，限制在六线谱中间区域（约20px高）
            r_top = y_center - 10    # 锯齿顶部Y
            r_bot = y_center + 10    # 锯齿底部Y
            points = [
                QPoint(cx + 3, r_top),         # 右上起点
                QPoint(cx - 3, r_top + 7),      # 左拐角
                QPoint(cx + 4, r_bot - 3),      # 右拐角
                QPoint(cx - 2, r_bot),          # 终点
            ]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
                
        else:
            # === 八分及更短休止符：类似"7"的圆弧 + 符尾 ===
            # 画一个左开口的圆弧（类似"7"的上半部分）
            arc_r = 5  # 圆弧半径(px)
            arc_x = int(cx - arc_r)
            arc_y = int(y_center) - arc_r - 4  # 确保所有参数为int，避免PyQt5类型错误
            painter.drawArc(arc_x, arc_y,
                           arc_r * 2, arc_r * 2,
                           180 * 16, 160 * 16)  # 从左边开始画约160度的弧
            
            # 画竖线向下（"7"的下半部分）
            painter.drawLine(cx + arc_r - 2, int(y_center) - 2, 
                            cx + arc_r - 2, int(y_center) + 10)
            
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
