# -*- coding: utf-8 -*-
"""
============================================================
文件名: layout_engine.py
功能描述: 六线谱布局引擎 - 计算所有小节/拍/音符的屏幕坐标
         负责自动换行、分页、宽度分配等核心布局算法

核心算法:
  1. 小节宽度 = 拍数 × 固定间距 + 左右边距（音符越多越宽，有最短长度）
  2. 每两个拍(Beat)之间使用固定水平间距(NOTE_MIN_SPACING)，不按时值比例缩放
  3. 自动换行：当一行放不下更多小节时换到下一行（贪心策略）

依赖库:
  - 内部依赖: gtp_engine.models.*, gtp_engine.utils.constants

创建日期: 2026-06-06
============================================================
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from ..models.track import GTPTrack
from ..models.measure import GTPMeasure
from ..models.beat import GTPBeat
from ..utils.constants import RenderConfig


# ============================================================
# 布局数据结构
# ============================================================

@dataclass
class BeatLayout:
    """
    单个拍(Beat)的布局位置
    
    属性:
      beat:        原始拍数据
      x_center:    该拍的中心X坐标（音符绘制基准点）
      x_start:     该拍的起始X坐标
      x_end:       该拍的结束X坐标
    """
    beat: GTPBeat
    x_center: int = 0
    x_start: int = 0
    x_end: int = 0


@dataclass
class MeasureLayout:
    """
    单个小节的布局位置
    
    属性:
      measure:     原始小芽数据
      x_start:     小节左边界X坐标
      x_end:       小节右边界X坐标
      beats:       该小节内各拍的布局列表
    """
    measure: GTPMeasure
    x_start: int = 0
    x_end: int = 0
    beats: List[BeatLayout] = field(default_factory=list)


@dataclass
class SystemLayout:
    """
    一行六线谱(系统)的布局 - 可包含多个连续小节
    
    属性:
      y_top:          该行顶部Y坐标（信息区下方）
      y_bottom:       该行底部Y坐标（含符干符尾空间）
      y_tab_top:      六线谱区域顶部Y（第1弦线位置）
      y_tab_bottom:   六线谱区域底部Y（第6弦线位置）
      measures:       该行包含的小节布局列表
    """
    y_top: int = 0
    y_bottom: int = 0
    y_tab_top: int = 0
    y_tab_bottom: int = 0
    measures: List[MeasureLayout] = field(default_factory=list)


@dataclass
class PageLayout:
    """
    一页乐谱的布局 - 包含多行系统
    
    属性:
      page_number:    页码
      systems:        该页包含的系统(行)列表
      height:         该页总高度(px)
    """
    page_number: int = 0
    systems: List[SystemLayout] = field(default_factory=list)
    height: int = 0


# ============================================================
# 布局引擎主类
# ============================================================

class TabLayoutEngine:
    """
    六线谱布局引擎
    
    功能:
      1. 计算每个小节在每行中的水平位置
      2. 自动换行：当一行放不下更多小节时换到下一行
      3. 分页：当一页放不下更多行时分到下一页
      4. 为每个拍计算精确的X坐标
    
    用法:
        engine = TabLayoutEngine()
        pages = engine.layout(track, page_width=900, page_height=1200)
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        """
        初始化布局引擎
        
        参数:
            config: 渲染配置，None时使用默认配置
        """
        self.cfg = config or RenderConfig()

    def layout(self, track: GTPTrack, 
               page_width: int = None, 
               page_height: int = None) -> List[PageLayout]:
        """
        对整条轨道进行完整布局计算
        
        参数:
            track:        要布局的音轨数据
            page_width:   每页宽度(px)，None则使用配置默认值
            page_height:  每页高度(px)，None则使用配置默认值
            
        返回:
            页面布局列表，每页包含多个系统(行)
        """
        pw = page_width or self.cfg.PAGE_WIDTH_PX
        ph = page_height or self.cfg.PAGE_HEIGHT_PX
        
        # 可用绘图区域（去除左右边距）
        usable_width = pw - self.cfg.PAGE_MARGIN_LEFT - self.cfg.PAGE_MARGIN_RIGHT
        
        # 第一步：将所有小节按行分组（自动换行）
        systems_raw = self._group_measures_into_systems(track.measures, usable_width)
        
        # 第二步：为每个系统分配精确坐标
        systems = self._assign_system_coordinates(
            systems_raw, 
            self.cfg.PAGE_MARGIN_LEFT,
            self.cfg.PAGE_MARGIN_TOP,
            usable_width
        )
        
        # 第三步：按页面高度分页
        pages = self._split_into_pages(systems, ph)
        
        return pages

    def _group_measures_into_systems(self, measures: List[GTPMeasure], 
                                      usable_width: int) -> List[List[GTPMeasure]]:
        """
        将小节分组到各行中（自动换行算法）
        
        算法: 贪心策略 - 尝试将每个小节放入当前行，
              如果当前行的剩余空间不够放下该小节的最小宽度，则换行。
        
        参数:
            measures:     所有小节列表
            usable_width: 可用绘图宽度
            
        返回:
            二维列表，每个内层列表代表一行的所有小节
        """
        if not measures:
            return [[]]
        
        rows: List[List[GTPMeasure]] = []
        current_row: List[GTPMeasure] = []
        current_width = 0
        
        # 每个小节的最小宽度 = 左右内边距 + 至少一个音符的空间
        min_measure_width = (
            self.cfg.MEASURE_PADDING_LEFT + 
            self.cfg.MEASURE_PADDING_RIGHT + 
            self.cfg.NOTE_MIN_SPACING
        )
        
        for measure in measures:
            # 估算该小节需要的宽度（基于拍的数量和平均间距）
            measure_width = self._estimate_measure_width(measure)
            
            # 检查是否需要换行
            if current_row and current_width + measure_width > usable_width:
                # 当前行已满，开始新行
                rows.append(current_row)
                current_row = [measure]
                current_width = measure_width
            else:
                # 放入当前行
                current_row.append(measure)
                current_width += measure_width
        
        # 处理最后一行
        if current_row:
            rows.append(current_row)
        
        return rows if rows else [[]]

    def _estimate_measure_width(self, measure: GTPMeasure) -> int:
        """
        估算一个小节的像素宽度
        
        新算法: 基于拍(音符组)数量 × 固定间距 + 左右边距
                音符越多小节越长，音符越少小节越短（但有最短长度保证可读性）
                每两个相邻拍之间使用固定间距(NOTE_MIN_SPACING)，不按时值比例缩放
        
        参数:
            measure: 要估算的小节数据
            
        返回:
            该小节需要的像素宽度
        """
        base_width = self.cfg.MEASURE_PADDING_LEFT + self.cfg.MEASURE_PADDING_RIGHT
        
        if not measure.beats:
            # 空小节：给4个拍位的最短空间
            return base_width + self.cfg.NOTE_MIN_SPACING * 3
        
        # 核心公式: 拍数 × 固定间距
        # N个拍之间有 (N-1) 个间隔，最后一个拍也需要一个单位宽度
        total_beats = len(measure.beats)
        
        # 固定间距部分：(N-1) 个间隔 × 每个间隔固定宽度
        beat_spacing_width = max(total_beats - 1, 0) * self.cfg.NOTE_MIN_SPACING
        
        # 多位数品格数字额外占位
        extra_chars = 0
        for beat in measure.beats:
            for note in beat.notes:
                if note.fret >= 10:
                    extra_chars += 1
                if note.fret >= 100:
                    extra_chars += 1
        extra_width = extra_chars * self.cfg.NOTE_EXTRA_WIDTH_PER_CHAR
        
        width = base_width + beat_spacing_width + self.cfg.NOTE_MIN_SPACING + extra_width
        
        # 最短长度保证：即使只有1-2个拍也不会太窄
        min_width = base_width + self.cfg.NOTE_MIN_SPACING * 3
        return max(width, min_width)

    def _assign_system_coordinates(self, rows: List[List[GTPMeasure]],
                                    start_x: int, start_y: int,
                                    usable_width: int) -> List[SystemLayout]:
        """
        为每个系统和其中的小节/拍分配精确坐标
        
        参数:
            rows:          按行分组的小节二维列表
            start_x:       起始X坐标
            start_y:       起始Y坐标（第一行顶部）
            usable_width:  可用宽度
            
        返回:
            SystemLayout 列表，每个元素包含完整的坐标信息
        """
        systems: List[SystemLayout] = []
        current_y = start_y
        
        # 六线谱高度 = (弦数-1) × 弦间距
        tab_height = (6 - 1) * self.cfg.TAB_LINE_SPACING
        # 一行总高度 = 六线谱高度 + 符干空间 + 行间距
        row_total_height = tab_height + self.cfg.STEM_HEIGHT + self.cfg.LINE_SPACING
        
        for row_idx, row_measures in enumerate(rows):
            # 创建系统布局
            system = SystemLayout()
            system.y_top = current_y
            system.y_tab_top = current_y + self.cfg.INFO_SECTION_HEIGHT
            system.y_tab_bottom = system.y_tab_top + tab_height
            system.y_bottom = system.y_tab_bottom + self.cfg.STEM_HEIGHT + 8
            
            current_x = start_x
            
            for measure in row_measures:
                # 创建小节布局
                m_layout = MeasureLayout(measure=measure)
                m_layout.x_start = current_x
                
                # 在小节内分配各拍的X坐标
                current_x = self._distribute_beats_in_measure(
                    measure, m_layout, 
                    current_x + self.cfg.MEASURE_PADDING_LEFT,
                    usable_width
                )
                
                m_layout.x_end = current_x + self.cfg.MEASURE_PADDING_RIGHT
                system.measures.append(m_layout)
                
                current_x = m_layout.x_end
            
            systems.append(system)
            current_y = system.y_bottom + self.cfg.SYSTEM_SPACING
        
        return systems

    def _distribute_beats_in_measure(self, measure: GTPMeasure,
                                      m_layout: MeasureLayout,
                                      start_x: int,
                                      usable_width: int) -> int:
        """
        在一个小节内按固定间距分布各拍的X坐标
        
        新算法: 每两个相邻拍之间使用固定间距(NOTE_MIN_SPACING)，
                不再按时值比例分配空间。
                这样音符密集的小节自然更长，稀疏的小节更短（但有最短长度）。
        
        参数:
            measure:     小节数据
            m_layout:    小节布局对象（结果写入此处）
            start_x:     小节内第一个拍的起始X
            usable_width: 总可用宽度（用于参考）
            
        返回:
            最后一个拍的结束X坐标
        """
        if not measure.beats:
            return start_x + self.cfg.NOTE_MIN_SPACING
        
        # 固定间距：每个拍占用相同水平宽度
        beat_spacing = self.cfg.NOTE_MIN_SPACING
        
        current_x = start_x
        for i, beat in enumerate(measure.beats):
            bl = BeatLayout(beat=beat)
            
            if i < len(measure.beats) - 1:
                # 非最后一个拍：固定间距
                bl.x_center = current_x + beat_spacing // 2
                bl.x_start = current_x
                bl.x_end = current_x + beat_spacing
                current_x += beat_spacing
            else:
                # 最后一个拍：占满剩余空间（避免末端空白过多）
                measure_inner_width = self._estimate_measure_width(measure)
                measure_inner_width -= (
                    self.cfg.MEASURE_PADDING_LEFT + self.cfg.MEASURE_PADDING_RIGHT
                )
                last_beat_width = max(
                    measure_inner_width - (len(measure.beats) - 1) * beat_spacing,
                    beat_spacing  # 保证至少一个间距的宽度
                )
                bl.x_center = current_x + last_beat_width // 2
                bl.x_start = current_x
                bl.x_end = current_x + last_beat_width
                current_x += last_beat_width
            
            m_layout.beats.append(bl)
        
        return current_x

    def _split_into_pages(self, systems: List[SystemLayout],
                           page_height: int) -> List[PageLayout]:
        """
        将系统列表按页面高度分页
        
        参数:
            systems:     所有系统的布局列表
            page_height: 每页可用高度
            
        返回:
            PageLayout 列表
        """
        if not systems:
            return []
        
        pages: List[PageLayout] = []
        current_page = PageLayout(page_number=len(pages) + 1)
        
        # 第一页顶部留出边距
        used_height = self.cfg.PAGE_MARGIN_TOP
        
        for system in systems:
            system_height = system.y_bottom - system.y_top + self.cfg.LINE_SPACING
            
            # 检查是否需要分页
            if used_height + system_height > page_height - self.cfg.PAGE_MARGIN_BOTTOM:
                # 当前页已满，保存并创建新页
                current_page.height = used_height
                pages.append(current_page)
                current_page = PageLayout(page_number=len(pages) + 1)
                used_height = self.cfg.PAGE_MARGIN_TOP
            
            current_page.systems.append(system)
            used_height += system_height
        
        # 处理最后一页
        if current_page.systems:
            current_page.height = used_height + self.cfg.PAGE_MARGIN_BOTTOM
            pages.append(current_page)
        
        return pages
