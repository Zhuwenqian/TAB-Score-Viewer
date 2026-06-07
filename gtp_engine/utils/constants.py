# -*- coding: utf-8 -*-
"""
============================================================
文件名: constants.py
功能描述: GTP引擎全局常量定义 - 包含调弦、时值映射、渲染参数等
         所有可调整的渲染参数都在此集中管理，修改后全局生效

创建日期: 2026-06-06
最后更新: 2026-06-06 (v1.1.2: NOTE_MIN_SPACING 14→22)
依赖库: 无（纯常量定义模块）
============================================================
"""

from enum import Enum, IntEnum
from typing import Tuple, List


# ============================================================
# 标准调弦定义（MIDI音高值）
# ============================================================

class StandardTunings:
    """
    常用吉他调弦方案（MIDI音高值）
    弦序：索引0 = 1弦(最细/高音E)，索引5 = 6弦(最粗/低音E)
    """
    STANDARD = (64, 59, 55, 50, 45, 40)       # 标准调弦 EADGBE
    DROP_D = (64, 59, 55, 50, 45, 38)           # Drop D
    OPEN_G = (62, 59, 55, 50, 43, 38)           # Open G (DGDGBD)
    OPEN_D = (62, 57, 50, 50, 45, 38)            # Open D (DADF#AD)
    DADGAD = (62, 57, 50, 45, 38, 45)            # DADGAD
    HALF_STEP_DOWN = (63, 58, 54, 49, 44, 39)    # 降半音调弦


# ============================================================
# 时值枚举（与 guitarpro.Duration.value 对应）
# ============================================================

class NoteDuration(IntEnum):
    """音符时值枚举 - 数值为 guitarpro Duration 的 value 字段"""
    WHOLE = 1              # 全音符
    HALF = 2               # 二分音符
    QUARTER = 4            # 四分音符
    EIGHTH = 8             # 八分音符
    SIXTEENTH = 16         # 十六分音符
    THIRTY_SECOND = 32     # 三十二分音符


# 时值 → 以四分音符为基准的时长比值
DURATION_RATIO = {
    1: 4.0,      # 全音符 = 4个四分音符
    2: 2.0,      # 二分音符 = 2个四分音符
    4: 1.0,      # 四分音符 = 1
    8: 0.5,      # 八分音符 = 0.5
    16: 0.25,    # 十六分音符 = 0.25
    32: 0.125,   # 三十二分音符 = 0.125
}

# 附点时值乘数（附点增加原时值的50%）
DOTTED_MULTIPLIER = 1.5


# ============================================================
# 技巧类型枚举（可扩展）
# ============================================================

class TechniqueType(Enum):
    """演奏技巧类型枚举 - 用于标注和渲染"""
    HAMMER_ON = "Hammer On"           # 击弦 (hammer)
    PULL_OFF = "Pull Off"             # 勾弦 (pull-off，通过slide反向推断)
    SLIDE_UP = "Slide Up"             # 上滑音 (slide into/from above)
    SLIDE_DOWN = "Slide Down"         # 下滑音 (slide into/from below)
    BEND = "Bend"                     # 推弦 (bend)
    VIBRATO = "Vibrato"               # 颤音 (vibrato)
    PALM_MUTE = "P.M."                # 闷音 (palm mute)
    STACCATO = "Staccato"             # 断奏 (staccato)
    GHOST_NOTE = "Ghost"              # 幽灵音 (ghost note)
    LET_RING = "Let Ring"             # 延音 (let ring)
    NATURAL_HARMONIC = "N.H."         # 自然泛音
    ARTIFICIAL_HARMONIC = "A.H."      # 人工泛音
    TAPPED_HARMONIC = "T.H."          # 点弦泛音
    PINCH_HARMONIC = "P.H."           # 拨弦泛音
    TREMOLO_PICKING = "Trem.Pick."    # 震音拨弦
    TRILL = "Trill"                   # 颤音(trill)
    GRACE_NOTE = "Grace"              # 装饰音(grace note)
    ACCENTUATED = ">"                 # 重音
    SLAP = "Slap"                     # 拍弦
    POP = "Pop"                       # 勾弦(贝斯)


# 技巧 → 渲染时的缩写文本映射
TECHNIQUE_ABBREVIATION = {
    TechniqueType.HAMMER_ON: "H",
    TechniqueType.PULL_OFF: "P",
    TechniqueType.SLIDE_UP: "s",
    TechniqueType.SLIDE_DOWN: "S",
    TechniqueType.BEND: "B",
    TechniqueType.VIBRATO: "~",
    TechniqueType.PALM_MUTE: "P.M.",
    TechniqueType.STACCATO: ".",
    TechniqueType.GHOST_NOTE: "(",
    TechniqueType.LET_RING: "Let Ring",
    TechniqueType.NATURAL_HARMONIC: "N.H.",
    TechniqueType.ARTIFICIAL_HARMONIC: "A.H.",
    TechniqueType.TAPPED_HARMONIC: "T.H.",
    TechniqueType.PINCH_HARMONIC: "P.H.",
    TechniqueType.TREMOLO_PICKING: "Trem.P.",
    TechniqueType.TRILL: "tr",
    TechniqueType.ACCENTUATED: ">",
}


# ============================================================
# 渲染参数常量（可调整）
# ============================================================

class RenderConfig:
    """
    六线谱渲染配置参数
    所有数值单位为像素(px)，可根据显示效果调整
    """

    # --- 画布尺寸 ---
    PAGE_WIDTH_PX = 900              # 每页渲染宽度(px) - 调整效果: 越宽每行容纳越多音符
    PAGE_HEIGHT_PX = 1200            # 每页渲染高度(px) - 调整效果: 越高每页容纳更多行
    PAGE_MARGIN_TOP = 60             # 页面上边距(px) - 用于标题和调号信息区
    PAGE_MARGIN_LEFT = 40            # 页面左边距(px)
    PAGE_MARGIN_RIGHT = 40           # 页面右边距(px)
    PAGE_MARGIN_BOTTOM = 40          # 页面下边距(px)

    # --- 六线谱线 ---
    TAB_LINE_SPACING = 14            # 弦线间距(px) - 调整效果: 越大六线谱越高，品格数字越清晰
    TAB_LINE_WIDTH_PER_STRING = 22   # 每根弦线分配的水平宽度(px) - 用于品格数字绘制区域
    TAB_LINE_THICKNESS = 1           # 弦线粗细(px)

    # --- 音符/品格数字 ---
    NOTE_FONT_SIZE = 10              # 品格数字字体大小(px) - 调整效果: 越大数字越清晰但占用空间多
    NOTE_FONT_FAMILY = "Arial"       # 品格数字字体族 - 推荐使用等宽字体保证对齐
    NOTE_MIN_SPACING = 26            # 相邻拍之间的最小水平间距(px) - 调整效果: 越小越紧凑，越大越宽松(推荐18-26)
    NOTE_EXTRA_WIDTH_PER_CHAR = 7    # 多位数品格数字的额外宽度(px/字符) - 如品10比品0多占10px

    # --- 符干与符尾 ---
    STEM_HEIGHT = 18                 # 符干高度(px) - 从六线谱向上/下延伸
    STEM_THICKNESS = 1               # 符干粗细(px)
    BEAM_HEIGHT = 6                  # 符尾横杠高度(px)
    BEAM_SLOPE_MAX = 0.3             # 笔尾最大倾斜斜率

    # --- 小节线 ---
    BARLINE_THICKNESS = 1.5          # 小节线粗细(px)
    BARLINE_HEIGHT_EXTEND = 6        # 小节线超出六线谱上下延伸量(px)
    MEASURE_PADDING_LEFT = 10        # 小节左侧内边距(px)
    MEASURE_PADDING_RIGHT = 12       # 小节右侧内边距(px)

    # --- 调号/拍号/BPM 信息区 ---
    INFO_SECTION_HEIGHT = 50         # 顶部信息区高度(px)
    INFO_FONT_SIZE = 13              # 信息文字大小(px)
    TRACK_NAME_FONT_SIZE = 16        # 音轨名称字体大小(px)

    # --- 行间距 ---
    LINE_SPACING = 30                # 两行六线谱之间的垂直间距(px) - 含符干符尾空间
    SYSTEM_SPACING = 20              # 不同系统(组)之间的额外间距(px)

    # --- 颜色主题（深色模式）---
    COLOR_BG = "#1E1E2E"             # 背景色
    COLOR_TAB_LINE = "#888888"       # 六线谱线颜色
    COLOR_TEXT = "#E2E8F0"           # 文字颜色（品格数字/标题等）
    COLOR_BARLINE = "#AAAAAA"        # 小节线颜色
    COLOR_STEM = "#CCCCCC"           # 符干颜色
    COLOR_BEAM = "#CCCCCC"           # 符尾颜色
    COLOR_TECHNIQUE = "#F97316"      # 技巧标记颜色（橙色高亮）
    COLOR_TRACK_NAME = "#60A5FA"     # 音轨名称颜色（蓝色）
    COLOR_REPEAT = "#10B981"         # 重复记号颜色（绿色）


# ============================================================
# 弦序辅助函数
# ============================================================

def get_string_name(string_index: int) -> str:
    """
    根据弦索引获取弦名称
    参数: string_index - 弦索引(0-5, 0=1弦高音E)
    返回: 弦名称字符串，如 '1弦(E)', '6弦(E)'
    """
    string_names = ["1弦(E)", "2弦(B)", "3弦(G)", "4弦(D)", "5弦(A)", "6弦(E)"]
    if 0 <= string_index < len(string_names):
        return string_names[string_index]
    return f"{string_index + 1}弦"
