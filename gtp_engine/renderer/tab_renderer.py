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
     - 符干/符尾(表示音符时值)
     - 技巧标记(击弦/滑音/推弦等缩写)
  3. 输出多页 QPixmap 列表，供 DisplayWidget 直接使用

依赖库:
  - PyQt5 (QPainter, QPixmap, QFont, QPen, QColor等)
  - 内部依赖: gtp_engine.models.*, layout_engine.*, utils.constants

创建日期: 2026-06-06
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
            # 1. 绘制页面头部信息区
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
        """绘制一行完整的六线谱系统（含所有小节）"""
        
        # 1. 绘制六条弦线
        self._draw_tab_lines(painter, system)
        
        # 2. 绘制每个小节的内容
        for m_layout in system.measures:
            self._draw_measure(painter, track, system, m_layout)

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
            self._draw_beat(painter, system, b_layout)

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
                   b_layout: BeatLayout) -> None:
        """
        绘制单个拍的所有内容：
          1. 品格数字（在对应弦线上）
          2. 符干（根据音符位置决定上下方向）
          3. 符尾（连接同组短时值音符）
          4. 技巧标记缩写
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
        
        # --- 绘制技巧标记 ---
        for note in beat.notes:
            self._draw_technique_marks(painter, note, cx, system)
        
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
                               cx: int, system: SystemLayout) -> None:
        """
        绘制技巧标记（在品格数字旁边或上方显示缩写）
        
        标记规则:
          - H/P/s 等单字符标记显示在品格数字右侧
          - P.M., Let Ring 等长标记显示在下方或上方
        """
        if not note.techniques:
            return
        
        painter.setPen(QColor(self.cfg.COLOR_TECHNIQUE))
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 8)
        painter.setFont(font)
        
        # 收集该音符所有技巧的缩写文本
        abbreviations = []
        for tech in note.techniques:
            abbr = TECHNIQUE_ABBREVIATION.get(tech, tech.value)
            abbreviations.append(abbr)
        
        if not abbreviations:
            return
        
        # 合并技巧文本
        tech_text = ''.join(abbreviations)
        
        # 计算Y位置：品格数字下方
        y_base = system.y_tab_top + note.string * self.cfg.TAB_LINE_SPACING
        tech_y = y_base + 12  # 显示在品格数字右下方
        
        # 对于较长的标记（如P.M., Let Ring），放在更下方避免重叠
        if len(tech_text) > 3:
            tech_y = system.y_tab_bottom + 4
        
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(tech_text)
        text_x = cx + (self.cfg.NOTE_FONT_SIZE // 2) + 2  # 品格数字右侧
        
        painter.drawText(QPoint(text_x, tech_y), tech_text)

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
        
        # 多数情况：以最高音为准决定方向
        stem_up = highest_string <= 2  # 第1-3弦 → 符干向上
        
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
        
        pen = QPen(QColor(self.cfg.COLOR_BEAM), self.cfg.STEM_THICKNESS)
        painter.setPen(pen)
        
        beam_h = self.cfg.BEAM_HEIGHT
        
        for i in range(flag_count):
            offset = i * 4  # 多个符尾之间的间距
            if stem_up:
                # 向上的符尾旗：向右下方倾斜
                painter.drawLine(cx, stem_tip_y + offset,
                               cx + 6, stem_tip_y + offset + beam_h)
            else:
                # 向下的符尾旗：向右上方倾斜
                painter.drawLine(cx, stem_tip_y - offset,
                               cx + 6, stem_tip_y - offset - beam_h)

    def _draw_rest_symbol(self, painter: QPainter, beat,
                          cx: int, system: SystemLayout) -> None:
        """绘制休止符符号（简化为小圆点表示）"""
        # 休止符位置：在六线谱中间区域
        y = system.y_tab_top + 2 * self.cfg.TAB_LINE_SPACING
        
        painter.setPen(QPen(QColor(self.cfg.COLOR_TEXT), 1))
        # 用小"×"或"."表示休止
        font = QFont(self.cfg.NOTE_FONT_FAMILY, 14)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text = "."
        tw = fm.horizontalAdvance(text)
        painter.drawText(QPoint(cx - tw // 2, y + 5), text)

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
