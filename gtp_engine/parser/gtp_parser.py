# -*- coding: utf-8 -*-
"""
============================================================
文件名: gtp_parser.py
功能描述: GTP文件解析器 - 将 PyGuitarPro 解析的原始数据转换为
         gtp_engine 的中介数据模型 (GTPSong → GTPTrack → GTPMeasure → GTPBeat → GTPNote)

原理:
  PyGuitarPro 库读取 .gp3/.gp4/.gp5/.gpx 文件后返回原始的 Song 对象，
  本模块将其转换为更易用的 GTP* 中介模型，便于渲染引擎消费。

依赖库:
  - guitarpro >= 0.11   # Guitar Pro 文件解析（开源项目: pyguitarpro）
  - 内部依赖: gtp_engine.models.*

创建日期: 2026-06-06
============================================================
"""

import guitarpro
from typing import List, Optional

from ..models.song import GTPSong
from ..models.track import GTPTrack
from ..models.measure import GTPMeasure
from ..models.beat import GTPBeat
from ..models.note import GTPNote, BendData
from ..utils.constants import (
    NoteDuration, TechniqueType, DURATION_RATIO,
)


class GTPParser:
    """
    GTP文件解析器
    
    功能: 将 PyGuitarPro 的原始数据结构转换为 gtp_engine 中介数据模型
    用法:
        parser = GTPParser()
        song = parser.parse("path/to/song.gp5")
    """

    def parse(self, file_path: str) -> GTPSong:
        """
        解析Guitar Pro文件
        
        参数:
            file_path: .gp3/.gp4/.gp5/.gpx 文件路径
            
        返回:
            GTPSong 中介数据模型，包含完整的乐谱信息
            
        异常:
            GPException: 文件格式错误或无法解析时抛出
        """
        # 使用 PyGuitarPro 库解析原始文件
        raw_song = guitarpro.parse(file_path)
        
        # 转换为中介模型
        return self._convert_song(raw_song)

    def _convert_song(self, raw_song: guitarpro.models.Song) -> GTPSong:
        """转换顶层 Song 对象"""
        song = GTPSong(
            title=raw_song.title or "",
            artist=raw_song.artist or "",
            album=raw_song.album or "",
            tempo=raw_song.tempo,
            tempo_name=raw_song.tempoName or "",
            key=self._convert_key(raw_song.key),
            subtitle=raw_song.subtitle or "",
            copyright=raw_song.copyright or "",
            instructions=raw_song.instructions or "",
        )
        
        # 转换所有音轨
        for raw_track in raw_song.tracks:
            track = self._convert_track(raw_track, raw_song)
            song.tracks.append(track)
        
        return song

    def _convert_key(self, key_sig) -> int:
        """
        转换调号枚举为整数值
        返回: 0=C大调/a小调, 正值=升号数, 负值=降号数
        """
        try:
            # guitarpro.KeySignature 是枚举，尝试获取数值
            if hasattr(key_sig, 'value'):
                return key_sig.value
            elif hasattr(key_sig, 'name'):
                # 从名称推断: CMajor=0, GMajor=1(1升), etc.
                name_map = {
                    'CMajor': 0, 'AMinor': 0,
                    'GMajor': 1, 'EMinor': 1,
                    'DMajor': 2, 'BMinor': 2,
                    'AMajor': 3, 'FSharpMinor': 3,
                    'EMajor': 4, 'CSharpMinor': 4,
                    'BMajor': 5, 'GSharpMinor': 5,
                    'FSharpMajor': 6, 'DSharpMinor': 6,
                    'CSharpMajor': 7, 'ASharpMinor': 7,
                    'FMajor': -1, 'DMinor': -1,
                    'BFlatMajor': -2, 'GMinor': -2,
                    'EFlatMajor': -3, 'CMinor': -3,
                    'AFlatMajor': -4, 'FMinor': -4,
                    'DFlatMajor': -5, 'BFlatMinor': -5,
                    'GFlatMajor': -6, 'EFlatMinor': -6,
                    'CFlatMajor': -7, 'AFlatMinor': -7,
                }
                return name_map.get(key_sig.name, 0)
            return 0
        except Exception:
            return 0

    def _convert_track(self, raw_track: guitarpro.models.Track, 
                       raw_song: guitarpro.models.Song) -> GTPTrack:
        """转换音轨对象"""
        # 提取调弦信息 (MIDI音高值列表)
        tuning = tuple(s.value for s in raw_track.strings)
        
        # 获取MIDI乐器编号
        instrument = 0
        if hasattr(raw_track.channel, 'instrument'):
            instrument = raw_track.channel.instrument
        elif raw_track.channel:
            instrument = getattr(raw_track.channel, 'instrument', 30)
        
        track = GTPTrack(
            name=raw_track.name or "",
            number=raw_track.number,
            strings=tuning,
            fret_count=raw_track.fretCount,
            instrument=instrument,
            is_visible=raw_track.isVisible,
            is_solo=raw_track.isSolo,
            is_mute=raw_track.isMute,
        )
        
        # 转换该轨道的所有小节
        for mi, raw_measure in enumerate(raw_track.measures):
            measure = self._convert_measure(raw_measure, mi + 1)
            track.measures.append(measure)
        
        return track

    def _convert_measure(self, raw_measure: guitarpro.models.Measure, 
                         number: int) -> GTPMeasure:
        """转换小节对象"""
        hdr = raw_measure.header
        ts = hdr.timeSignature
        
        # 拍号提取
        numerator = ts.numerator if ts.numerator else 4
        denominator = ts.denominator.value if ts.denominator else 4
        
        # 段落标记
        marker = None
        if hdr.marker and hdr.marker.title:
            marker = hdr.marker.title
        
        measure = GTPMeasure(
            number=number,
            time_signature=(numerator, denominator),
            is_repeat_open=hdr.isRepeatOpen,
            repeat_close=hdr.repeatClose if hdr.repeatClose > 0 else -1,
            marker=marker,
            key_signature=self._convert_key(hdr.keySignature),
        )
        
        # 转换该小节的所有声部(Voice)和拍(Beat)
        for voice in raw_measure.voices:
            for raw_beat in voice.beats:
                beat = self._convert_beat(raw_beat)
                measure.beats.append(beat)
        
        return measure

    def _convert_beat(self, raw_beat: guitarpro.models.Beat) -> GTPBeat:
        """转换拍对象"""
        # 时值转换: guitarpro.Duration.value → NoteDuration 枚举
        dur_value = raw_beat.duration.value
        duration = self._duration_from_value(dur_value)
        
        beat = GTPBeat(
            duration=duration,
            is_dotted=raw_beat.duration.isDotted,
            text=raw_beat.text,
        )
        
        # 转换该拍的所有音符
        for raw_note in raw_beat.notes:
            note = self._convert_note(raw_note, duration, raw_beat.duration.isDotted)
            beat.notes.append(note)
        
        # 如果没有音符且没有文本标注，视为休止符
        if not beat.notes and not beat.text:
            beat.is_rest = True
        
        return beat

    def _convert_note(self, raw_note: guitarpro.models.Note,
                      duration: NoteDuration, is_dotted: bool) -> GTPNote:
        """
        转换单个音符对象
        这是技巧信息提取的核心方法
        """
        effect = raw_note.effect
        
        note = GTPNote(
            midi_pitch=raw_note.realValue,     # 实际MIDI音高
            string=raw_note.string - 1,         # 弦号(PyGuitarPro是1-based, 转为0-based: 0=1弦顶线, 5=6弦底线)
            fret=raw_note.value,                 # 品格数
            velocity=raw_note.velocity,          # 力度
            duration=duration,
            is_dotted=is_dotted,
            is_ghost=effect.ghostNote,           # 幽灵音标记
        )
        
        # ===== 技巧信息提取 =====
        # 击弦 Hammer-on
        if effect.hammer:
            note.add_technique(TechniqueType.HAMMER_ON)
        
        # 颤音 Vibrato
        if effect.vibrato:
            note.add_technique(TechniqueType.VIBRATO)
        
        # 闷音 Palm Mute
        if effect.palmMute:
            note.add_technique(TechniqueType.PALM_MUTE)
        
        # 断奏 Staccato
        if effect.staccato:
            note.add_technique(TechniqueType.STACCATO)
        
        # 延音 Let Ring
        if effect.letRing:
            note.add_technique(TechniqueType.LET_RING)
        
        # 重音 Accentuated
        if effect.accentuatedNote:
            note.add_technique(TechniqueType.ACCENTUATED)
        
        # 强重音 Heavy Accentuated
        if effect.heavyAccentuatedNote:
            note.add_technique(TechniqueType.ACCENTUATED)
        
        # 推弦 Bend - 提取完整推弦数据(类型/度数/曲线点)
        if effect.bend:
            note.add_technique(TechniqueType.BEND)
            b = effect.bend
            # 提取推弦曲线点
            points = []
            max_val = 0
            for bp in b.points:
                # BendPoint: position(时间), value(音高偏移), vibrato(是否颤音)
                p_val = bp.value if hasattr(bp, 'value') else 0
                p_pos = bp.position if hasattr(bp, 'position') else 0
                p_vib = bp.vibrato if hasattr(bp, 'vibrato') else False
                points.append((p_pos, p_val, p_vib))
                if p_val > max_val:
                    max_val = p_val
            
            # 获取推弦类型名称
            btype_name = str(b.type) if hasattr(b.type, 'name') else str(getattr(b, 'type', 'bend'))
            
            note.bend = BendData(
                bend_type=btype_name,
                value=getattr(b, 'value', 0),
                max_value=max_val or getattr(b, 'maxValue', 0),
                points=points
            )
        
        # 滑音 Slides (支持多个滑音方向)
        for slide in effect.slides:
            slide_name = slide.name if hasattr(slide, 'name') else str(slide)
            if 'intoFromAbove' in slide_name or 'outUpwards' in slide_name:
                note.add_technique(TechniqueType.SLIDE_UP)
            elif 'intoFromBelow' in slide_name or 'outDownwards' in slide_name:
                note.add_technique(TechniqueType.SLIDE_DOWN)
            elif 'legato' in slide_name.lower():
                # legato滑音通常伴随hammer/pull-off
                pass
            elif 'shift' in slide_name.lower():
                note.add_technique(TechniqueType.SLIDE_UP)
        
        # 泛音 Harmonic
        if effect.harmonic and effect.harmonic.type:
            harm_type = effect.harmonic.type
            harm_name = harm_type.name if hasattr(harm_type, 'name') else str(harm_type)
            if 'Natural' in harm_name:
                note.add_technique(TechniqueType.NATURAL_HARMONIC)
            elif 'Artificial' in harm_name:
                note.add_technique(TechniqueType.ARTIFICIAL_HARMONIC)
            elif 'Tapped' in harm_name:
                note.add_technique(TechniqueType.TAPPED_HARMONIC)
            elif 'Pinch' in harm_name:
                note.add_technique(TechniqueType.PINCH_HARMONIC)
            elif 'Semi' in harm_name:
                note.add_technique(TechniqueType.NATURAL_HARMONIC)
            else:
                note.add_technique(TechniqueType.NATURAL_HARMONIC)
        
        # 震音拨弦 Tremolo Picking
        if effect.tremoloPicking:
            note.add_technique(TechniqueType.TREMOLO_PICKING)
        
        # 颤音 Trill
        if effect.trill:
            note.add_technique(TechniqueType.TRILL)
        
        # 装饰音 Grace Note
        if effect.grace:
            note.add_technique(TechniqueType.GRACE_NOTE)
        
        return note

    @staticmethod
    def _duration_from_value(value: int) -> NoteDuration:
        """
        将 guitarpro Duration 的整数值转换为 NoteDuration 枚举
        映射关系: 1=全音符, 2=二分, 4=四分, 8=八分, 16=十六分, 32=三十二分
        """
        mapping = {
            1: NoteDuration.WHOLE,
            2: NoteDuration.HALF,
            4: NoteDuration.QUARTER,
            8: NoteDuration.EIGHTH,
            16: NoteDuration.SIXTEENTH,
            32: NoteDuration.THIRTY_SECOND,
        }
        return mapping.get(value, NoteDuration.QUARTER)


# ============================================================
# 便捷函数
# ============================================================

def parse_gtp(file_path: str) -> GTPSong:
    """
    便捷函数：解析Guitar Pro文件并返回中介数据模型
    
    参数:
        file_path: .gp3/.gp4/.gp5/.gpx 文件路径
        
    返回:
        GTPSong 对象
        
    示例:
        >>> from gtp_engine.parser import parse_gtp
        >>> song = parse_gtp("my_song.gp5")
        >>> print(f"标题: {song.title}, 音轨数: {song.track_count}")
    """
    parser = GTPParser()
    return parser.parse(file_path)
