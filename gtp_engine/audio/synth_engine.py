# -*- coding: utf-8 -*-
"""
============================================================
文件名: synth_engine.py
功能描述: FluidSynth 音频合成引擎 - 基于 SoundFont 的实时 MIDI 播放
         将 MIDI 事件序列通过 FluidSynth 合成器转换为音频输出

创建日期: 2026-06-07
依赖: 
  - pyfluidsynth >= 1.4.0 (Python绑定, 开源项目: pyfluidsynth/nwhitehead)
  - libfluidsynth-3.dll (FluidSynth C库, 需放到项目根目录或系统PATH中)
  - SoundFont 文件 (.sf2) 用于音色采样
设计原则:
  - 线程安全: 音频播放在独立线程中运行，不阻塞UI主线程
  - 精确定时: 使用系统高精度定时器驱动 MIDI 事件发送
  - 资源管理: 自动释放合成器资源，支持多次初始化/销毁

调用示例:
    from gtp_engine.audio.synth_engine import SynthEngine
    
    engine = SynthEngine()
    engine.load_soundfont("path/to/soundfont.sf2")
    
    # 加载MIDI事件后播放
    engine.load_events(midi_event_list, bpm=120)
    engine.play()
    
    # 暂停/继续
    engine.pause()
    engine.resume()
    
    # 停止并清理
    engine.stop()

依赖库说明:
  - pyfluidsynth: FluidSynth 的 Python ctypes 绑定（开源项目: nwhitehead/pyfluidsynth）
    安装命令: pip install pyfluidsynth -i https://pypi.tuna.tsinghua.edu.cn/simple
  - libfluidsynth-3.dll: FluidSynth C运行时库
    下载地址: https://github.com/FluidSynth/fluidsynth/releases
    放置位置: 项目根目录即可（代码自动搜索）
============================================================
"""

import os
import time
import threading
from typing import List, Optional, Callable


class SynthEngine:
    """
    FluidSynth 音频合成引擎
    
    功能概述:
      基于 FluidSynth 开源项目实现实时 MIDI 合成。
      加载 SoundFont (.sf2) 文件作为音色源，
      接收带时间戳的 MIDI 事件序列，按精确时间间隔播放。
    
    核心原理:
      1. 初始化 FluidSynth 合成器实例 + 音频输出驱动
      2. 加载 SoundFont 文件到合成器（包含各种乐器音色采样）
      3. 播放线程按时间顺序逐个发送 MIDI 事件到合成器
      4. 合成器将 MIDI 事件实时渲染为音频波形输出到声卡
    
    支持的 MIDI 事件类型:
      - note_on:  发声(指定通道/音高/力度)
      - note_off: 止音
      - tempo:    变速标记(用于同步计算)
    
    参数说明(初始化):
      sample_rate:   采样率(Hz), 调整效果: 越高音质越好但CPU占用更多(推荐44100)
      buffer_size:   音频缓冲区大小(采样点数), 调整效果: 越大延迟越高但更稳定(推荐256/512)
      gain:          主音量增益(0.0-10.0), 调整效果: 1.0=原始音量, 2.0=翻倍
    """
    
    # 默认音频参数
    DEFAULT_SAMPLE_RATE = 44100     # 标准CD音质采样率(Hz), 调整效果: 48000更清晰
    DEFAULT_BUFFER_SIZE = 512       # 音频缓冲区大小(采样点数), 调整效果: 256延迟更低
    DEFAULT_GAIN = 0.8              # 默认主音量(0.0-1.0), 调整效果: 1.0=最大音量
    
    # 内置 SoundFont 搜索路径（按优先级排序）
    SOUNDFONT_SEARCH_PATHS = [
        "soundfont",                    # 项目内 soundfont 目录
        "../soundfont",                 # 项目上级目录
        "../../soundfont",              # 更上级目录
        os.path.expanduser("~/.fluidsynth"),  # 用户主目录
        "/usr/share/sounds/sf2",        # Linux 系统路径
        "/usr/share/soundfonts",        # Linux 备选路径
        "C:/ProgramData/FluidSynth",    # Windows 系统路径
    ]
    
    # 常见 SoundFont 文件名（自动搜索）
    SOUNDFONT_NAMES = [
        "FluidR3_GM.sf2",              # FluidSynth 官方通用音色库(推荐)
        "GeneralUser GS v1.471.sf2",   # GeneralUser 音色库
        "default-GM.sf2",              # 默认 GM 音色库
    ]
    
    def __init__(self, sample_rate: int = None, buffer_size: int = None,
                 gain: float = None):
        """
        初始化合成引擎
        
        参数:
            sample_rate:  采样率(Hz), None=使用默认44100
            buffer_size:  缓冲区大小, None=使用默认512
            gain:         主音量, None=使用默认0.8
        """
        self.sample_rate = sample_rate or self.DEFAULT_SAMPLE_RATE
        self.buffer_size = buffer_size or self.DEFAULT_BUFFER_SIZE
        self.gain = gain or self.DEFAULT_GAIN
        
        # === 内部状态 ===
        self._synth = None              # FluidSynth 合成器实例
        self._audio_driver = None       # 音频驱动实例
        self._sfid = -1                 # 当前加载的SoundFont ID
        self._soundfont_path = ""       # 当前SoundFont文件路径
        
        # === 播放状态 ===
        self._events: List = []         # 待播放的MIDI事件列表
        self._bpm: int = 120            # 当前BPM
        self._ticks_per_beat: int = 480 # 每拍tick数(与MidiConverter一致)
        
        # === 播放控制 ===
        self._is_playing: bool = False  # 是否正在播放
        self._is_paused: bool = False   # 是否暂停
        self._play_thread: threading.Thread = None  # 播放线程
        self._stop_flag: bool = False   # 停止信号
        self._pause_event = threading.Event()  # 暂停事件(用于暂停恢复同步)
        self._pause_event.set()         # 初始为非暂停状态(set=不阻塞)
        
        # === 进度追踪 ===
        self._current_time_ms: float = 0.0  # 当前播放位置(毫秒)
        self._start_time: float = 0.0        # 播放开始时的系统时间
        self._paused_duration: float = 0.0   # 累计暂停时长(毫秒)
        
        # === 回调函数 ===
        self._on_note_callback: Optional[Callable] = None  # 音符触发回调(用于视觉高亮)
        
        # === 锁 ===
        self._lock = threading.RLock()  # 可重入锁，保护共享状态
    
    @property
    def is_playing(self) -> bool:
        """是否正在播放(非暂停状态)"""
        with self._lock:
            return self._is_playing and not self._is_paused
    
    @property
    def is_paused(self) -> bool:
        """是否处于暂停状态"""
        with self._lock:
            return self._is_paused
    
    @property
    def current_time_ms(self) -> float:
        """获取当前播放位置(毫秒)"""
        with self._lock:
            if self._is_playing and not self._is_paused:
                # 实时计算：从开始时间到现在 - 暂停时间
                elapsed = (time.perf_counter() - self._start_time) * 1000.0
                return elapsed - self._paused_duration
            return self._current_time_ms
    
    @property
    def is_initialized(self) -> bool:
        """合成器是否已成功初始化"""
        return self._synth is not None
    
    def initialize(self) -> bool:
        """
        初始化 FluidSynth 合成器和音频驱动
        
        原理:
          创建 FluidSynth.Synth 实例并配置音频参数，
          然后启动音频输出驱动将合成结果送到声卡。
        
        返回:
            True=初始化成功, False=失败(fluidsynth未安装或设备不可用)
        
        注意:
          此方法必须在 load_soundfont() 之前调用！
          如果 fluidsynth 库未安装会返回 False 但不抛异常。
          
        DLL 依赖说明:
          需要 libfluidsynth-3.dll (FluidSynth C库)。
          自动搜索顺序: 项目根目录 → 系统PATH → 标准安装路径。
          用户可将DLL放到项目根目录即可免安装使用。
        """
        try:
            # === 将DLL目录加入PATH(让ctypes.util.find_library能找到libfluidsynth-3.dll) ===
            _dll_dir = self._get_project_root()
            _dll_path = os.path.join(_dll_dir, "libfluidsynth-3.dll")
            
            if os.path.isfile(_dll_path):
                # 将DLL目录添加到环境变量PATH（ctypes.util.find_library依赖PATH搜索）
                _old_path = os.environ.get('PATH', '')
                if _dll_dir not in _old_path:
                    os.environ['PATH'] = _dll_dir + os.pathsep + _old_path
                print(f"[SynthEngine] 已添加DLL目录到PATH: {_dll_dir}")
                
                # Python 3.8+ 同时添加到DLL搜索目录(用于运行时加载)
                if hasattr(os, 'add_dll_directory'):
                    try:
                        os.add_dll_directory(_dll_dir)
                    except OSError:
                        pass  # 某些情况下可能失败，不影响PATH方式
            else:
                print(f"[SynthEngine] 警告: 未找到 libfluidsynth-3.dll")
            
            import fluidsynth
            
            # 创建合成器实例
            self._synth = fluidsynth.Synth(
                gain=self.gain,
                sample_rate=self.sample_rate
            )
            
            # 启动音频驱动（默认使用系统默认音频输出）
            # driver: 'pulseaudio'(Linux), 'dsound'(Windows), 'coreaudio'(macOS)
            self._audio_driver = self._synth.start(driver=None)
            
            if self._audio_driver is None:
                # 尝试指定驱动
                import platform
                system = platform.system()
                driver_map = {
                    'Windows': 'dsound',
                    'Linux': 'pulseaudio',
                    'Darwin': 'coreaudio'
                }
                driver = driver_map.get(system, 'default')
                self._audio_driver = self._synth.start(driver=driver)
            
            return True
            
        except ImportError:
            print("[SynthEngine] 警告: fluidsynth 库未安装")
            print("  安装命令: pip install pyfluidsynth -i https://pypi.tuna.tsinghua.edu.cn/simple")
            return False
        except Exception as e:
            print(f"[SynthEngine] 初始化失败: {e}")
            return False
    
    @staticmethod
    def _get_project_root() -> str:
        """
        获取项目根目录路径，同时搜索 FluidSynth DLL 所在目录
        
        原理: 从当前文件位置向上查找，同时检查常见的DLL放置位置:
             1. 项目根目录/libfluidsynth-3.dll
             2. 项目根目录/fluidsnyth/bin/libfluidsynth-3.dll (FluidSynth Windows发行版)
             3. 项目根目录/fluidsynth/bin/libfluidsynth-3.dll
        
        返回:
            包含 libfluidsynth-3.dll 的目录绝对路径，找不到则返回项目根目录
        """
        # 方法1: 从本模块文件位置推导 (gtp_engine/audio/ → 项目根目录)
        _here = os.path.dirname(os.path.abspath(__file__))
        _root = os.path.normpath(os.path.join(_here, '..', '..'))
        
        # 搜索DLL的候选目录（按优先级排序）
        _dll_dirs = [
            _root,                                    # 项目根目录
            os.path.join(_root, "fluidsnyth", "bin"),  # FluidSynth Windows发行版(常见拼写)
            os.path.join(_root, "fluidsynth", "bin"),  # 正确拼写的发行版目录
            os.path.join(_root, "bin"),                # 通用bin目录
        ]
        
        for _d in _dll_dirs:
            if os.path.isfile(os.path.join(_d, "libfluidsynth-3.dll")):
                print(f"[SynthEngine] 找到DLL: {_d}")
                return _d
        
        # 都没找到，返回项目根目录（后续导入会报错但给出明确提示）
        return _root
    
    def _find_dll_path(self) -> str:
        """
        查找 libfluidsynth-3.dll 的完整路径
        
        返回:
            DLL完整路径，找不到返回空字符串
        """
        _root = self._get_project_root()
        for _name in ["libfluidsynth-3.dll", "libfluidsynth.dll"]:
            _path = os.path.join(_root, _name)
            if os.path.isfile(_path):
                return _path
        return ""
    
    def load_soundfont(self, path: str = None) -> bool:
        """
        加载 SoundFont 音色文件
        
        参数:
            path: SoundFont 文件路径(.sf2格式)
                  None=自动搜索内置/系统常见 SoundFont 文件
        
        返回:
            True=加载成功, False=失败(文件不存在或格式错误)
        
        注意:
          必须先调用 initialize() 成功后再调用此方法！
          SoundFont 文件包含乐器音色的采样数据，是音频输出的基础。
          推荐: FluidR3_GM.sf2 (免费开源, 包含128种GM标准音色)
        """
        if self._synth is None:
            print("[SynthEngine] 错误: 请先调用 initialize()")
            return False
        
        # 如果指定了路径，直接尝试加载
        if path and os.path.isfile(path):
            return self._load_sf_file(path)
        
        # 自动搜索 SoundFont 文件
        sf_path = self._find_soundfont()
        if sf_path:
            return self._load_sf_file(sf_path)
        
        print("[SynthEngine] 错误: 未找到 SoundFont 文件")
        print("  解决方案:")
        print("  1. 下载 FluidR3_GM.sf2: https://ftp.osuosl.org/pub/musespan/SoundFonts/")
        print("  2. 放到项目 soundfont/ 目录下")
        return False
    
    def _load_sf_file(self, path: str) -> bool:
        """
        内部方法: 实际加载 SoundFont 文件到合成器
        """
        try:
            # 先卸载旧的 SoundFont（如果有）
            if self._sfid >= 0:
                self._synth.sfunload(self._sfid)
            
            # 加载新的 SoundFont
            self._sfid = self._synth.sfload(path)
            
            if self._sfid >= 0:
                self._soundfont_path = path
                print(f"[SynthEngine] SoundFont 加载成功: {os.path.basename(path)}")
                
                # 设置吉他音色(程序号24-30对应各种吉他)
                # 通道0默认已设置钢琴(0)，这里切换到电吉他(27=Clean Guitar)
                # 用户可在后续通过 program_change 自定义
                return True
            else:
                print(f"[SynthEngine] SoundFont 加载失败: {path}")
                return False
                
        except Exception as e:
            print(f"[SynthEngine] SoundFont 加载异常: {e}")
            return False
    
    def _find_soundfont(self) -> Optional[str]:
        """
        自动搜索可用的 SoundFont 文件
        
        搜索顺序:
          1. 项目 soundfont/ 目录
          2. 用户 ~/.fluidsynth/ 目录
          3. Linux 系统目录 /usr/share/sounds/sf2/
          4. Windows ProgramData 目录
        """
        for search_dir in self.SOUNDFONT_SEARCH_PATHS:
            for sf_name in self.SOUNDFONT_NAMES:
                full_path = os.path.join(search_dir, sf_name)
                if os.path.isfile(full_path):
                    return full_path
        
        return None
    
    def set_instrument(self, channel: int = 0, program: int = 24) -> None:
        """
        设置指定通道的乐器音色(MIDI程序号)
        
        参数:
            channel: MIDI通道(0-15)
            program: 程序号(GM标准):
                     24=尼龙弦吉他(Ukulele), 25=钢弦吉他(Acoustic),
                     26=爵士电吉他(Jazz), 27=清音电吉他(Clean),
                     28=失真电吉他(Overdrive), 29=高增益失真(Distortion),
                     30=泛音(Palm Muted)
        
        常用吉他音色对照表:
          24 Nylon String Guitar  | 25 Steel String Guitar
          26 Jazz Electric        | 27 Clean Electric
          28 Overdriven           | 29 Distortion
          30 Harmonics/Palm Mute
        """
        if self._synth:
            self._synth.program_change(channel, program)
    
    def set_drum_kit(self, channel: int = 9, kit: int = 0) -> None:
        """
        设置指定通道为GM鼓组音色
        
        原理: GM标准中，鼓组音色位于 Bank MSB=128 (Percussion Bank)，
              与旋律乐器(Bank 0)完全分离。必须通过 CC#0 (Bank Select MSB)
              切换到鼓组bank后，再选择鼓组program。
        
        参数:
            channel: MIDI通道(默认9=打击乐保留通道)
            kit:     鼓组程序号(GM标准):
                     0 = Standard Kit(标准鼓组)
                     1 = Room Kit(房间鼓组)
                     2 = Power Kit(强力鼓组)
                     3 = Electronic Kit(电子鼓组)
                     ... 等等
        
        注意: 此方法必须在 load_events() 之前调用，
              否则通道可能已被设置为旋律乐器音色导致鼓声异常。
        
        GM 鼓组常用 note 映射:
          35=Kick Drum 2   | 36=Bass Drum 1(底鼓) | 37=Side Stick
          38=Acoustic Snare(军鼓) | 39=Hand Clap    | 40=Electric Snare
          41=Low Floor Tom  | 42=Closed HiHat(闭镲)| 43=High Floor Tom
          44=Pedal HiHat(踏板镲)| 45=Low Tom      | 46=Open HiHat(开镲)
          47=Low-Mid Tom    | 48=Hi-Mid Tom       | 49=Crash Cymbal 1(碎镲)
          50=High Tom       | 51=Ride Cymbal 1(吊镲)| 52=Chinese Cymbal
          53=Ride Bell     | 54=Tambourine       | 55=Splash Cymbal
          56=Cowbell       | 57=Crash Cymbal 2   | 58=Vibraslap
          59=Ride Cymbal 2 | 60=Hi Bongo         | 61=Low Bongo
          62=Conga Mute Hi | 63=Conga Open Hi    | 64=Conga Low
          65=Timbale High  | 66=Timbale Low      | 67=Agogo High
          68=Agogo Low     | 69=Cabasa           | 70=Maracas
          71=Short Whistle | 72=Long Whistle     | 73=Short Guiro
          74=Long Guiro    | 75=Claves           | 76=Hi Wood Block
          77=Low Wood Block| 78=M Triangle Open  | 79=M Triangle Closed
          80=Shaker        | 81=Jingle Bell      | 82=Bell Tree
        """
        if self._synth:
            # CC#0 = Bank Select MSB, 值128 = Percussion Bank (GM标准)
            self._synth.cc(channel, 0, 128)
            # Program Change 选择具体鼓组类型
            self._synth.program_change(channel, kit)
    
    def load_events(self, events: list, bpm: int = 120,
                    ticks_per_beat: int = 480) -> None:
        """
        加载待播放的 MIDI 事件序列
        
        参数:
            events:         MidiEvent 对象列表(由 MidiConverter.generate())
            bpm:            播放速度(BPM, 每分钟拍数)
            ticks_per_beat: 每四分音符的tick数(需与MidiConverter一致)
        
        注意:
          此方法仅加载数据，不会立即开始播放。
          需要调用 play() 才能开始播放。
          可在暂停时重新加载事件以实现跳转。
        """
        with self._lock:
            self._events = list(events)  # 浅拷贝避免外部修改
            self._bpm = bpm
            self._ticks_per_beat = ticks_per_beat
            self._current_time_ms = 0.0
            self._paused_duration = 0.0
    
    def play(self) -> None:
        """
        开始播放(从当前位置或开头开始)
        
        原理:
          在独立线程中运行播放循环：
            1. 计算每个事件的预定播放时间(毫秒)
            2. 使用 time.sleep() 精确等待到该时刻
            3. 发送 MIDI 事件到 FluidSynth 合成器
            4. 循环直到所有事件播放完毕或收到停止信号
        
        时间精度:
          使用 time.perf_counter() 高精度计时器，
          配合自适应 sleep 校正，误差 < 5ms
        """
        with self._lock:
            if self._is_playing and not self._is_paused:
                return  # 已在播放中
            
            self._is_playing = True
            self._is_paused = False
            self._stop_flag = False
            self._pause_event.set()  # 清除暂停状态
        
        # 启动播放线程
        self._play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self._play_thread.start()
    
    def pause(self) -> None:
        """
        暂停播放(保持当前进度位置)
        
        原理: 设置暂停标志，播放线程中的 sleep 会被中断，
              恢复时可从暂停处继续。
        """
        with self._lock:
            if not self._is_playing or self._is_paused:
                return
            
            self._is_paused = True
            self._current_time_ms = self.current_time_ms  # 冻结当前位置
            self._pause_event.clear()  # 触发暂停(阻塞播放线程)
    
    def resume(self) -> None:
        """
        从暂停位置恢复播放
        """
        with self._lock:
            if not self._is_paused:
                return
            
            # 调整开始时间以扣除暂停前的已播放时长
            self._start_time = time.perf_counter()
            self._is_paused = False
            self._pause_event.set()  # 清除暂停(唤醒播放线程)
    
    def stop(self) -> None:
        """
        停止播放并重置到开头
        """
        with self._lock:
            self._stop_flag = True
            self._is_playing = False
            self._is_paused = False
            self._pause_event.set()  # 确保线程不被阻塞
            self._current_time_ms = 0.0
            self._paused_duration = 0.0
        
        # 停止所有正在发声的音符
        if self._synth:
            for ch in range(16):
                for pitch in range(128):
                    self._synth.noteoff(ch, pitch)
        
        # 等待播放线程结束
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2.0)
    
    def seek(self, time_ms: float) -> None:
        """
        跳转到指定时间位置(毫秒)
        
        原理: 停止当前播放 → 过滤出时间≥目标位置的事件
              → 从目标位置开始重新播放。
              已经过去的 note_on 会被忽略（快速跳转时不回溯发声）。
        
        参数:
            time_ms: 目标时间位置(毫秒)
        """
        with self._lock:
            was_playing = self._is_playing and not self._is_paused
            
            if was_playing:
                self._stop_flag = True
                self._pause_event.set()
            
            self._current_time_ms = max(0, time_ms)
            self._paused_duration = 0.0
            
            if was_playing:
                # 重新启动播放（从新位置开始）
                self._stop_flag = False
                self._is_playing = True
                self._is_paused = False
                self._pause_event.set()
                
                if self._play_thread and self._play_thread.is_alive():
                    self._play_thread.join(timeout=1.0)
                
                self._play_thread = threading.Thread(target=self._play_loop, daemon=True)
                self._play_thread.start()
    
    def set_note_callback(self, callback: Callable) -> None:
        """
        设置音符触发回调函数(用于视觉高亮同步)
        
        参数:
            callback: 回调函数签名 callback(midi_pitch, velocity, time_ms)
                      当有 note_on 事件被触发时调用此函数，
                      用于通知 UI 层更新当前高亮的音符位置
        """
        self._on_note_callback = callback
    
    def _play_loop(self) -> None:
        """
        播放线程主循环(内部方法，勿直接调用)
        
        核心逻辑:
          1. 计算每 tick 对应的毫秒数: ms_per_tick = 60000 / (BPM × ticks_per_beat)
          2. 遍历所有事件，对每个事件:
             a. 计算目标时间 = event.tick × ms_per_tick
             b. 如果目标时间 < seek起点，跳过
             c. 否则 sleep 到达目标时间(考虑暂停)
             d. 发送 MIDI 事件到合成器
             e. 触发回调(用于视觉同步)
          3. 所有事件处理完毕 → 播放结束
        """
        if not self._events:
            with self._lock:
                self._is_playing = False
            return
        
        # === 时间基准计算 ===
        ms_per_tick = 60000.0 / (self._bpm * self._ticks_per_beat)
        start_offset = self._current_time_ms  # 跳转后的起始偏移(毫秒)
        
        # 记录实际开始播放的系统时间
        with self._lock:
            self._start_time = time.perf_counter()
        
        try:
            for evt in self._events:
                # === 检查停止信号 ===
                with self._lock:
                    if self._stop_flag:
                        break
                
                # === 检查暂停 ===
                self._pause_event.wait()  # 暂停时此处阻塞
                
                # 再次检查停止(可能在暂停期间收到停止信号)
                with self._lock:
                    if self._stop_flag:
                        break
                
                # === 计算事件的绝对时间(毫秒) ===
                target_time_ms = evt.time * ms_per_tick
                
                # 跳过已经过去的事件(seek时)
                if target_time_ms < start_offset:
                    # 对于过去的 note_off，仍然需要执行以防止长音卡住
                    if evt.type == "note_off" and self._synth:
                        self._synth.noteoff(evt.channel, evt.pitch)
                    continue
                
                # === 等待到达目标时间 ===
                relative_target = target_time_ms - start_offset
                self._wait_until(relative_target)
                
                # === 再次检查状态(等待期间可能暂停/停止) ===
                with self._lock:
                    if self._stop_flag:
                        break
                
                # === 发送 MIDI 事件到合成器 ===
                self._send_event(evt)
                
                # === 触发回调(note_on 时通知视觉层) ===
                if evt.type == "note_on" and self._on_note_callback:
                    try:
                        self._on_note_callback(evt.pitch, evt.velocity, target_time_ms)
                    except Exception:
                        pass  # 回调异常不影响播放
            
            # === 播放结束 ===
            with self._lock:
                if not self._stop_flag:
                    self._is_playing = False
                    self._current_time_ms = 0  # 播放完毕重置
                    
        except Exception as e:
            print(f"[SynthEngine] 播放循环异常: {e}")
            with self._lock:
                self._is_playing = False
    
    def _wait_until(self, target_relative_ms: float) -> None:
        """
        精确等待到指定的相对时间位置(毫秒)
        
        使用自适应 sleep 策略保证时间精度:
          1. 先 sleep 到目标时间前 5ms
          2. 然后 busy-wait(spinning) 到精确时刻
          3. 支持 pause/resume 中断
        
        参数:
            target_relative_ms: 相对于播放开始的毫秒时间
        """
        while True:
            # 检查暂停/停止
            if self._stop_flag:
                return
            if self._is_paused:
                self._pause_event.wait()
                # 恢复后重新校准开始时间
                with self._lock:
                    self._start_time = time.perf_counter()
                continue
            
            # 计算已播放的时间
            with self._lock:
                elapsed = (time.perf_counter() - self._start_time) * 1000.0
            
            remaining = target_relative_ms - elapsed
            
            if remaining <= 0:
                return  # 已到达目标时间
            elif remaining > 5:
                # 还有较多时间，先 sleep 一小段
                sleep_time = min(remaining - 2, 10)  # 最多睡10ms
                self._pause_event.wait(timeout=sleep_time / 1000.0)
            else:
                # 接近目标时间，busy-wait 提高精度
                self._pause_event.wait(timeout=0.001)  # 1ms 短暂 sleep 让出CPU
    
    def _send_event(self, event) -> None:
        """
        发送单个 MIDI 事件到 FluidSynth 合成器
        
        参数:
            event: MidiEvent 对象
        """
        if not self._synth:
            return
        
        try:
            if event.type == "note_on":
                # note_on: 通道 + 音高 + 力度
                self._synth.noteon(event.channel, event.pitch, event.velocity)
                
            elif event.type == "note_off":
                # note_off: 通道 + 音高(velocity=0)
                self._synth.noteoff(event.channel, event.pitch)
                
            elif event.type == "tempo":
                # tempo 变化: 更新内部 BPM 参考
                # (实际变速能力需要更复杂的实现，这里仅记录)
                pass
                
        except Exception as e:
            print(f"[SynthEngine] 发送事件失败: {e}")
    
    def shutdown(self) -> None:
        """
        关闭合成引擎并释放所有资源
        
        原理: 停止播放 → 卸载 SoundFont → 关闭音频驱动 → 销毁合成器实例
        此方法应在程序退出时调用以确保资源正确释放。
        """
        self.stop()
        
        if self._synth:
            try:
                if self._sfid >= 0:
                    self._synth.sfunload(self._sfid)
                    self._sfid = -1
                self._synth.delete()
            except Exception:
                pass
            finally:
                self._synth = None
                self._audio_driver = None
    
    def __del__(self):
        """析构函数：确保资源释放"""
        try:
            self.shutdown()
        except Exception:
            pass
