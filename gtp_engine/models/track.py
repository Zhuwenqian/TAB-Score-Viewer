# -*- coding: utf-8 -*-
"""
============================================================
文件名: track.py
功能描述: 音轨(Track)数据模型 - 存储一条吉他/贝斯轨道的完整信息
         包含调弦、乐器设置、所有小节等内容

创建日期: 2026-06-06
依赖: Python 3.8+ dataclasses
============================================================
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from .measure import GTPMeasure


@dataclass
class GTPTrack:
    """
    一条音轨(Track)的数据模型 - 对应 Guitar Pro 中的一条吉他/贝斯轨道
    
    属性说明:
      name:          轨道名称 (如 "Lead Guitar", "Bass")
      number:        轨道编号 (从1开始)
      strings:       调弦信息 (MIDI音高元组, 从1弦到6弦)
                    例: (64,59,55,50,45,40) = 标准调弦 EADGBE
      fret_count:    品格数量 (通常21-24)
      instrument:    MIDI乐器编号 (24=尼龙弦吉他, 25=钢弦吉他,
                    26=爵士吉他, 27=清洁吉他, 28=失真吉他,
                    29=过载吉他, 30=电吉他)
      measures:      该轨道的所有小节列表
      is_visible:    是否在乐谱中可见
      is_solo:       是否独奏
      is_mute:       是否静音
      capo:          变调夹位置 (0=无变调夹)
    """

    name: str = ""                                      # 轨道名称
    number: int = 1                                     # 轨道编号
    strings: Tuple[int, ...] = (64, 59, 55, 50, 45, 40) # 调弦(MIDI音高)
    fret_count: int = 24                                # 品格数
    instrument: int = 30                                # MIDI乐器编号
    measures: List[GTPMeasure] = field(default_factory=list)  # 小节列表
    is_visible: bool = True                             # 可见性
    is_solo: bool = False                               # 独奏
    is_mute: bool = False                               # 静音
    capo: int = 0                                       # 变调夹位置

    @property
    def string_count(self) -> int:
        """弦的数量"""
        return len(self.strings)

    @property
    def total_measures(self) -> int:
        """总小节数"""
        return len(self.measures)

    def get_tuning_name(self) -> str:
        """
        获取调弦方案的名称
        返回: 已知调弦返回名称，否则返回自定义描述
        
        匹配方式: 遍历所有预设调弦方案，逐一比较元组值。
                 比字典键方式更健壮，可处理元组子类/类型差异等边界情况。
        """
        from ..utils.constants import StandardTunings
        tuning_tuple = self.strings
        for name, stuning in [
            ("标准调弦(EADGBE)", StandardTunings.STANDARD),
            ("Drop D", StandardTunings.DROP_D),
            ("Open G", StandardTunings.OPEN_G),
            ("Open D", StandardTunings.OPEN_D),
            ("DADGAD", StandardTunings.DADGAD),
            ("降半音", StandardTunings.HALF_STEP_DOWN),
        ]:
            if tuning_tuple == stuning:
                return name
        return f"自定义调弦({len(self.strings)}弦)"

    def get_total_beats(self) -> int:
        """获取该轨道所有小节的总拍数"""
        return sum(len(m.beats) for m in self.measures)
