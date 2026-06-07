# -*- coding: utf-8 -*-
"""
============================================================
文件名: midi_converter.py
功能描述: GTP歌曲数据 → MIDI事件序列转换器
         将 GTPSong 数据模型转换为带时间戳的 MIDI 事件列表，
         用于驱动 FluidSynth 合成器进行音频播放

创建日期: 2026-06-07
依赖: Python 3.8+ dataclasses, gtp_engine.models
设计原则: 
  - 时间精度: 使用 tick(脉冲)作为最小时间单位，避免浮点累积误差
  - 标准MIDI格式: 兼容标准 MIDI 事件(note_on/note_off/tempo)
  - 可扩展: 支持未来添加控制变化/弯音轮等事件

调用示例:
    from gtp_engine.audio.midi_converter import MidiConverter
    converter = MidiConverter()
    events = converter.convert(song, track_index=0)
    for evt in events:
        print(f"tick={evt.time}: {evt.type} ch={evt.channel} pitch={evt.pitch} vel={evt.velocity}")
============================================================
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

# 导入技巧枚举（用于力度计算和断奏判断）
from ..utils.constants import TechniqueType


@dataclass
class MidiEvent:
    """
    单个 MIDI 事件的数据模型
    
    属性说明:
      time:     绝对时间位置(tick单位, 从歌曲开头开始累加)
      type:     事件类型 ('note_on' | 'note_off' | 'tempo')
      channel:  MIDI通道 (0-15), 吉他通常用通道0-3
      pitch:    音高/MIDI音高值 (0-127)
      velocity: 力度/击弦强度 (0-127), note_off时为0
      value:    附加值(tempo事件用, BPM值)
    
    调用来源: MidiConverter.convert() 生成的所有MIDI事件
    """
    time: int = 0                    # 绝对时间位置(tick)
    type: str = "note_on"            # 事件类型
    channel: int = 0                 # MIDI通道
    pitch: int = 0                   # MIDI音高
    velocity: int = 0                # 力度
    value: int = 0                   # 附加值(BPM等)


class MidiConverter:
    """
    GTP歌曲 → MIDI事件序列转换器
    
    功能:
      将 GTPSong 数据模型转换为按时间排序的 MIDI 事件列表。
      每个音符生成一对 note_on + note_off 事件，
      并在开头插入 tempo 事件设置播放速度。
    
    时间计算原理:
      - 使用 tick 作为内部时间单位（类似 MIDI 文件的 ticks-per-beat）
      - ticks_per_beat 默认为 480（MIDI 标准分辨率）
      - 每个 Beat 的时长 = (ticks_per_beat) × (四分音符基准 / 时值比例)
      - 附点音符时长 × 1.5
    
    力度处理:
      - 正常音符: 使用 note.velocity (默认95=mf中强)
      - 幽灵音(Ghost Note): 力度降低到 60 (pp-弱)
      - 断奏(Staccato): 时值缩短50%，力度不变
    
    参数说明:
      ticks_per_beat: 每个四分音符的tick数，调整效果:
                       越大则时间精度越高(推荐480/960)，越小计算越快
    """
    
    # MIDI 标准分辨率：每四分音符的 tick 数
    TICKS_PER_BEAT = 480  # 调整效果: 标准 MIDI 分辨率，足够精确
    
    # 吉他音色 MIDI 通道映射
    GUITAR_CHANNEL = 0    # 主吉他轨道使用通道0
    
    # 多轨并轨时每轨分配的起始通道号（最多支持16个音轨，通道0-15）
    MULTI_TRACK_START_CHANNEL = 0
    
    # MIDI标准中通道9(第10通道)是打击乐/鼓组保留通道，不能用于旋律乐器
    # 多轨并轨时自动跳过此通道（非鼓轨）
    PERCUSSION_CHANNEL = 9
    
    # GM标准鼓音映射范围: MIDI note 35-81 对应不同鼓/镲音色
    # 常用值: 36=底鼓, 38/40=军鼓, 42=闭镲, 44=开镲, 49=碎镲, 51=吊镲
    DRUM_NOTE_RANGE = (35, 82)
    
    # 鼓轨识别关键词(轨道名称匹配)
    DRUM_KEYWORDS = ('drum', 'percussion', 'drums', 'perc', '鼓')
    
    def __init__(self, ticks_per_beat: int = None):
        """
        初始化转换器
        
        参数:
            ticks_per_beat: 自定义每拍tick数(None=使用默认480)
        """
        self.ticks_per_beat = ticks_per_beat or self.TICKS_PER_BEAT
    
    def convert(self, song, track_index: int = 0) -> List[MidiEvent]:
        """
        将 GTPSong 的指定音轨转换为 MIDI 事件序列
        
        参数:
            song:         GTPSong 歌曲数据对象
            track_index:  要转换的音轨索引(0-based)
        
        返回:
            List[MidiEvent]: 按时间排序的 MIDI 事件列表
        
        执行步骤:
          1. 验证输入参数有效性
          2. 在 tick=0 处插入 tempo 事件(BPM)
          3. 遍历每个小节→每个拍→每个音符，计算绝对 tick 位置
          4. 为每个非休止符音符生成 note_on + note_off 事件对
          5. 按时间排序返回完整事件列表
        """
        events: List[MidiEvent] = []
        
        # === 参数验证 ===
        if not song or not song.tracks:
            return events
        if track_index < 0 or track_index >= len(song.tracks):
            return events
        
        track = song.tracks[track_index]
        
        # === Step 1: 插入 tempo 事件(歌曲开头的速度标记) ===
        events.append(MidiEvent(
            time=0,
            type="tempo",
            channel=self.GUITAR_CHANNEL,
            pitch=0,
            velocity=song.tempo,
            value=song.tempo
        ))
        
        # === Step 2: 遍历所有小节和拍，生成音符事件 ===
        current_tick = 0  # 当前绝对 tick 位置（从歌曲开头开始累加）
        
        for measure in track.measures:
            measure_events = self._convert_measure(
                measure, current_tick, self.GUITAR_CHANNEL
            )
            events.extend(measure_events)
            
            # 当前小节结束，累加小节总时长到 current_tick
            measure_ticks = self._measure_to_ticks(measure)
            current_tick += measure_ticks
        
        # === Step 3: 按 time 排序确保时序正确 ===
        events.sort(key=lambda e: (e.time, 0 if e.type == "note_on" else 1))
        
        return events
    
    @staticmethod
    def is_drum_track(track) -> bool:
        """
        检测一个音轨是否为鼓轨(打击乐轨道)
        
        检测策略(按优先级):
          1. 名称匹配: 轨道名称包含 drum/percussion/鼓 等关键词
          2. 音符特征: 鼓轨的音符特征是 fret == midi_pitch
             （因为鼓轨不使用弦/品格系统，直接存储MIDI鼓音编号）
             且所有音符的pitch都在GM鼓音范围(35-81)内
        
        参数:
            track: GTPTrack 音轨对象
        
        返回:
            True=是鼓轨, False=普通旋律轨
        """
        # === 策略1: 名称匹配 ===
        name_lower = track.name.lower()
        if any(kw in name_lower for kw in MidiConverter.DRUM_KEYWORDS):
            return True
        
        # === 策略2: 音符特征检测 ===
        # 鼓轨关键特征: fret == midi_pitch (鼓音直接存为MIDI编号，非品格计算值)
        #              且 pitch 在 GM 鼓音范围(35-81)
        sample_notes = []
        for m in track.measures[:8]:  # 取前8小节样本
            for b in m.beats:
                for n in b.notes:
                    sample_notes.append((n.midi_pitch, getattr(n, 'fret', None)))
                    if len(sample_notes) >= 20:
                        break
                if len(sample_notes) >= 20:
                    break
            if len(sample_notes) >= 20:
                break
        
        if len(sample_notes) >= 5:  # 至少5个音符才做特征判断
            lo, hi = MidiConverter.DRUM_NOTE_RANGE
            # 检查是否所有样本都满足: (1)在鼓音范围 (2)fret==pitch
            all_drum_like = all(
                lo <= p <= hi and f == p
                for p, f in sample_notes
            )
            if all_drum_like:
                return True
        
        return False
    
    def convert_all_tracks(self, song) -> Tuple[List[MidiEvent], List[int]]:
        """
        转换歌曲所有音轨为合并的 MIDI 事件序列（并轨模式）
        
        原理:
          遍历 GTPSong 中所有音轨，每个音轨分配独立的 MIDI 通道，
          将所有音轨的音符事件合并到一个列表中按时间排序。
          这样播放时所有音轨同时发声，实现"乐队合奏"效果。
        
        通道分配规则:
          - 音轨0 → MIDI通道0
          - 音轨1 → MIDI通道1
          - ...以此类推，最多支持16个音轨(通道0-15)
          - 超过16个音轨时循环使用通道(取模)
        
        参数:
            song: GTPSong 歌曲数据对象
        
        返回:
            Tuple[events, track_channels]:
              - events: 合并后的全部MIDI事件列表(已排序)
              - track_channels: 每个音轨对应的MIDI通道号列表
        
        使用场景:
          全轨并轨播放模式 - 用户想听到完整乐队效果而非单轨独奏
        """
        all_events: List[MidiEvent] = []
        track_channels: List[int] = []
        
        if not song or not song.tracks:
            return all_events, track_channels
        
        # 只在开头插入一次 tempo 事件（避免重复）
        all_events.append(MidiEvent(
            time=0,
            type="tempo",
            channel=0,
            pitch=0,
            velocity=0,
            value=song.tempo
        ))
        
        # 遍历每个音轨，各自转换后合并
        # 通道分配规则:
        #   - 鼓轨(检测到) → 固定分配通道9(MIDI打击乐保留通道)
        #   - 旋律轨 → 从可用通道中循环分配(0-8, 10-15，跳过通道9)
        _melody_channels = [c for c in range(16) if c != self.PERCUSSION_CHANNEL]
        _melody_idx = 0  # 旋律轨通道计数器
        
        for track_idx, track in enumerate(song.tracks):
            # === 鼓轨检测与通道分配 ===
            if self.is_drum_track(track):
                ch = self.PERCUSSION_CHANNEL  # 鼓轨固定使用通道9
            else:
                ch = _melody_channels[_melody_idx % len(_melody_channels)]
                _melody_idx += 1
            
            track_channels.append(ch)
            
            # 复用 convert 的逻辑但指定该轨道的通道
            current_tick = 0
            for measure in track.measures:
                measure_events = self._convert_measure(
                    measure, current_tick, ch
                )
                all_events.extend(measure_events)
                measure_ticks = self._measure_to_ticks(measure)
                current_tick += measure_ticks
        
        # 全局排序：所有轨道的事件按时间统一排序
        all_events.sort(key=lambda e: (e.time, 0 if e.type == "note_on" else 1))
        
        return all_events, track_channels
    
    def get_all_tracks_duration_ms(self, song) -> float:
        """
        获取所有音轨中最长的总时长(毫秒)
        
        用于全轨并轨模式下的进度条计算，
        取最长轨道的时长作为总时长。
        
        参数:
            song: GTPSong 对象
        
        返回:
            最长音轨的时长(毫秒)
        """
        if not song or not song.tracks:
            return 0.0
        
        max_duration = 0.0
        for idx in range(len(song.tracks)):
            duration = self.get_total_duration_ms(song, idx)
            max_duration = max(max_duration, duration)
        
        return max_duration
    
    def _convert_measure(self, measure, start_tick: int, 
                          channel: int) -> List[MidiEvent]:
        """
        转换单个小节的所有音符为 MIDI 事件
        
        参数:
            measure:    GTPMeasure 小节数据
            start_tick: 该小节开始的绝对 tick 位置
            channel:    MIDI 通道
        
        返回:
            该小节内所有音符的 note_on/note_off 事件列表
        """
        events: List[MidiEvent] = []
        beat_tick = start_tick  # 当前拍的起始 tick（在小节内相对+绝对）
        
        for beat in measure.beats:
            # 计算当前拍的 tick 时长
            beat_ticks = self._beat_duration_to_ticks(beat)
            
            # 跳过空拍和纯休止符拍
            if beat.is_empty or (beat.is_rest and not beat.notes):
                beat_tick += beat_ticks
                continue
            
            # 为该拍中的每个音符生成 MIDI 事件
            for note in beat.notes:
                if note.is_rest:
                    continue
                
                # === 计算力度(velocity) ===
                velocity = self._calculate_velocity(note)
                
                # === 计算实际时长(考虑断奏等技巧) ===
                actual_duration = beat_ticks
                if TechniqueType.STACCATO in note.techniques:
                    actual_duration = int(beat_ticks * 0.5)  # 断奏缩短一半
                
                # === 生成 note_on 事件 ===
                events.append(MidiEvent(
                    time=beat_tick,
                    type="note_on",
                    channel=channel,
                    pitch=note.midi_pitch,
                    velocity=velocity
                ))
                
                # === 生成 note_off 事件(在音符结束时触发) ===
                events.append(MidiEvent(
                    time=beat_tick + actual_duration,
                    type="note_off",
                    channel=channel,
                    pitch=note.midi_pitch,
                    velocity=0  # note_off 的 velocity 固定为0
                ))
            
            # 移动到下一拍
            beat_tick += beat_ticks
        
        return events
    
    def _beat_duration_to_ticks(self, beat) -> int:
        """
        将拍的时值转换为 tick 数
        
        参数:
            beat: GTPBeat 对象
        
        返回:
            该拍的时长(以 tick 为单位)
        
        计算公式:
          ticks = TICKS_PER_BEAT × DURATION_RATIO[duration.value]
                 × (1.5 if is_dotted else 1.0)
        
        示例:
          四分音符 → 480 ticks
          八分音符 → 240 ticks
          附点四分 → 720 ticks
        """
        from ..utils.constants import DURATION_RATIO, DOTTED_MULTIPLIER
        
        base_ratio = DURATION_RATIO.get(beat.duration.value, 1.0)
        ticks = int(self.ticks_per_beat * base_ratio)
        if beat.is_dotted:
            ticks = int(ticks * DOTTED_MULTIPLIER)
        return max(ticks, 1)  # 最少1 tick，防止除零
    
    def _measure_to_ticks(self, measure) -> int:
        """
        计算一个小节的总 tick 时长
        
        基于拍号计算: 总时长 = 分子 × (TICKS_PER_BEAT × 4 / 分母)
        例如 4/4拍 = 4 × 480 = 1920 ticks
        """
        numerator, denominator = measure.time_signature
        return int(numerator * self.ticks_per_beat * 4.0 / denominator)
    
    def _calculate_velocity(self, note) -> int:
        """
        根据音符属性计算实际演奏力度
        
        规则:
          - 幽灵音(Ghost Note): 降低力度到 60 (弱声)
          - 正常音符: 使用原始 velocity (默认95)
          - 重音(Accentuated): 提升力度到 120 (接近最强127)
        
        参数:
            note: GTPNote 音符对象
        
        返回:
            实际力度值 (0-127)
        """
        base_vel = note.velocity
        
        # 幽灵音降低力度
        if note.is_ghost or TechniqueType.GHOST_NOTE in note.techniques:
            base_vel = min(base_vel, 60)
        
        # 重音提升力度
        if TechniqueType.ACCENTUATED in note.techniques:
            base_vel = min(base_vel + 25, 127)
        
        # 确保在合法范围内
        return max(0, min(127, base_vel))
    
    def tick_to_ms(self, tick: int, bpm: int) -> float:
        """
        将 tick 数转换为毫秒时间
        
        公式: ms = tick × (60000 / (bpm × ticks_per_beat))
        
        参数:
            tick: tick 数值
            bpm:  每分钟拍数
        
        返回:
            对应的毫秒数
        """
        if bpm <= 0:
            bpm = 120
        return tick * 60000.0 / (bpm * self.ticks_per_beat)
    
    def get_total_duration_ms(self, song, track_index: int = 0) -> float:
        """
        获取指定音轨的总播放时长(毫秒)
        
        用于进度条显示和同步计算
        
        参数:
            song:         GTPSong 对象
            track_index:  音轨索引
        
        返回:
            总时长(毫秒)
        """
        if not song or not song.tracks:
            return 0.0
        if track_index >= len(song.tracks):
            return 0.0
        
        total_ticks = 0
        track = song.tracks[track_index]
        for measure in track.measures:
            total_ticks += self._measure_to_ticks(measure)
        
        return self.tick_to_ms(total_ticks, song.tempo)
