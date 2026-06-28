# alphaTab GTP 播放逻辑分析报告

## 1. 概述

alphaTab 是一个跨平台的乐谱解析与渲染引擎，支持 Guitar Pro (GTP) 多种格式。其播放系统采用"解析 → 模型化 → MIDI生成 → 合成播放"的四层架构。

**核心播放流程**:

```
GTP文件 → ScoreImporter → Score(数据模型)
                                ↓
                    MidiFileGenerator(生成MIDI事件)
                                ↓
                        MidiFile(SMF格式)
                                ↓
                AlphaSynth(合成器控制器)
                    ├─ MidiFileSequencer(事件调度器)
                    └─ TinySoundFont(SoundFont合成器)
                                ↓
                    ISynthOutput(音频输出)
```

---

## 2. 模块结构与核心类

### 2.1 文件导入层 (`src/importer/`)

| 类 | 文件 | 职责 |
|----|------|------|
| `ScoreLoader` | `ScoreLoader.ts` | 统一入口，自动检测文件格式并派发到合适的导入器 |
| `Gp3To5Importer` | `Gp3To5Importer.ts` | 解析 GP3/GP4/GP5 二进制格式 |
| `Gp7To8Importer` | `Gp7To8Importer.ts` | 解析 GP7/GP8 格式 |
| `GpxImporter` | `GpxImporter.ts` | 解析 GPX 格式 |
| `GpifParser` | `GpifParser.ts` | 解析 GPIF XML 内容 |
| `ScoreImporter` | `ScoreImporter.ts` | 抽象基类，所有导入器继承 |

**策略**: ScoreLoader 使用"尝试-失败-下一个"策略依次尝试各导入器，直到成功解析。

### 2.2 数据模型层 (`src/model/`)

核心模型类（各级容器）：

```
Score(乐谱)
  └─ MasterBar[](主小节)       — 小节级信息（拍号、调号、速度、重复记号）
  └─ Track[](音轨)
       └─ Staff[](谱表)
            └─ Bar[](小节)
                 └─ Voice[](声部)
                      └─ Beat[](拍)       — 时值、技法、自动化参数
                           └─ Note[](音符) — 弦号、品格、MIDI音高、技巧
```

关键属性：
- `Beat.playbackStart` / `Beat.playbackDuration` — 拍在节内的MIDI偏移和时长
- `MasterBar.tempoAutomations` — 小节内速度变化列表
- `MasterBar.calculateDuration()` — 计算小节总MIDI嘀嗒数
- `Note.calculateRealValue()` — 计算音符实际MIDI音高（含调弦、移调）

### 2.3 MIDI 生成层 (`src/midi/`)

| 类 | 文件 | 职责 |
|----|------|------|
| `MidiFileGenerator` | `MidiFileGenerator.ts` | 核心生成器，遍历乐谱模型生成MIDI事件 |
| `MidiFile` | `MidiFile.ts` | 内存中的MIDI文件表示(SMF格式)，含事件列表 |
| `MidiTrack` | `MidiFile.ts` | MIDI音轨，事件有序列表 |
| `AlphaSynthMidiFileHandler` | `AlphaSynthMidiFileHandler.ts` | IMidiFileHandler实现，将事件写入MidiFile |
| `MidiEvent` (及其子类) | `MidiEvent.ts` | MIDI事件基类及具体类型（NoteOn, NoteOff, PitchBend等） |
| `MidiUtils` | `MidiUtils.ts` | MIDI工具函数（嘀嗒↔毫秒转换、连音、附点计算） |
| `MidiPlaybackController` | `MidiPlaybackController.ts` | 播放控制器，处理重复、跳跃(D.C./D.S./Coda) |

### 2.4 时间线查找层 (`src/midi/`)

| 类 | 文件 | 职责 |
|----|------|------|
| `MidiTickLookup` | `MidiTickLookup.ts` | 全局Tick查找表，主小节→拍 二级索引 |
| `MasterBarTickLookup` | `MasterBarTickLookup.ts` | 主小节时间范围，内含链表式BeatTickLookup |
| `BeatTickLookup` | `BeatTickLookup.ts` | 拍的时间切片，标记多个声部的拍重叠 |
| `MidiTickLookupFindBeatResult` | `MidiTickLookup.ts` | 查找到的当前拍结果（含下一拍指针和时长） |

### 2.5 合成播放层 (`src/synth/`)

| 类 | 文件 | 职责 |
|----|------|------|
| `AlphaSynth` | `AlphaSynth.ts` | 合成器主控制器，管理播放状态、同步点、事件回调 |
| `MidiFileSequencer` | `MidiFileSequencer.ts` | MIDI事件序列器，将时间轴上的事件分发到合成器 |
| `TinySoundFont` | `synthesis/TinySoundFont.ts` | SoundFont合成引擎（C# TinySoundFont的TypeScript移植） |
| `IAudioSampleSynthesizer` | `IAudioSampleSynthesizer.ts` | 合成器接口 |
| `ISynthOutput` | `ISynthOutput.ts` | 音频输出接口（WebAudio、NAudio等实现） |
| `PlayerState` | `PlayerState.ts` | 播放状态枚举 (Paused/Playing) |
| `BackingTrackSyncPoint` | `IAlphaSynth.ts` | 同步点，用于MIDI时间轴与伴奏音频的同步 |

---

## 3. 核心数据流详解

### 3.1 从文件加载到 Score 模型

```
ScoreLoader.loadScoreFromBytes(bytes)
  → 遍历所有 ScoreImporter（Gp3To5Importer, Gp7To8Importer, GpxImporter）
  → importer.init(readable, settings)
  → importer.readScore()
  → 返回 Score 对象
```

**关键实现**: 导入器解析二进制/XML格式，构建完整的 `Score` 对象树。每种格式有各自的解析器。

### 3.2 从 Score 到 MIDI 文件

这是播放逻辑中最复杂的一环，由 `MidiFileGenerator` 完成。

#### 3.2.1 主流程 (`generate()`)

```
MidiFileGenerator.generate()
  1. 初始化每个Track的MIDI通道（Program Change, Volume, Pan, PitchBendRange）
  2. 调用 _playThroughSong() 遍历所有小节（处理重复和跳跃）
     → 每个MasterBar: _generateMasterBar() — 节拍号/速度变化
     → 每个Bar: _generateBar() — 遍历声部
       → 每个Voice: _generateVoice() — 遍历拍
         → 每个Beat: _generateBeat() — 遍历音符 + 技法效果
           → 每个Note: _generateNote() — 生成NoteOn/Off, Bend, Slide等
  3. 所有事件通过 AlphaSynthMidiFileHandler 写入 MidiFile
```

#### 3.2.2 重复与跳跃处理

`MidiPlaybackController` 负责：

- **重复**: 使用 `RepeatGroup` 和迭代计数器栈，处理 repeat start/end 和 alternate endings
- **方向标记**: 支持 D.C. (Da Capo)、D.S. (Dal Segno)、Coda、Fine 等
- **状态机**: PlayingNormally → DirectionJumped / DirectionJumpedAlCoda / DirectionJumpedAlFine

#### 3.2.3 音符MIDI生成

`_generateNote()` 是核心函数，处理：

1. **音高计算**: `Note.calculateRealValue()` + 打击乐映射 `PercussionMapper`
2. **力度计算**: `_getNoteVelocity()` — 基础力度来自 DynamicValue，结合 accent/hammer/ghost 调整
3. **持续时间计算**: `_getNoteDuration()` — 三层时长:
   - `noteOnly`: 实际发声长度（受 dead/palm-mute/staccato 影响）
   - `untilTieOrSlideEnd`: 连音/滑音延长后的总时长
   - `letRingEnd`: Let Ring 效果延长的结束时间
4. **技法处理**（优先级顺序）:
   - **Rasgueado**: 弗拉门戈轮扫，生成多个短音符
   - **Ornament**: 装饰音（上波音、下波音、回音等）
   - **Trill**: 颤音，在相邻品上快速交替
   - **Tremolo Picking**: 轮拨，快速重复弹奏
   - **Bend/Whammy**: 推弦/摇把，生成连续的 PitchBend 事件
   - **Slide**: 滑音，生成音高过渡 Bend 事件
   - **Vibrato**: 揉弦，正弦波调制音高

#### 3.2.4 速度变化处理

每个 MasterBar 可包含多个 `TempoAutomation`（相对位置 + BPM值）。生成流程：

```
_generateMasterBar()
  → 遍历 bar.tempoAutomations
  → 对每个 automation: handler.addTempo(tick, automation.value)
  → 同时构建 MasterBarTickLookup.tempoChanges[] 用于查找
```

`_processBarTime()` 在遍历过程中同步维护 `PlayThroughContext.synthTime`（毫秒时间轴），精确计算每个速度段的耗时。

#### 3.2.5 三连音感处理

`TripletFeel` 影响第1拍和第2拍的时长比例，支持：
- Triplet8th / Triplet16th: 三连音感
- Dotted8th / Dotted16th: 附点音感
- Scottish8th / Scottish16th: 苏格兰切分音感

#### 3.2.6 扫弦(Brush)处理

`_fillBrushInfo()` 为扫弦方向计算各弦的偏移时间：
- 从低音到高音或反之
- 总时长 = `beat.brushDuration`
- 增量 = 总时长 / (弦数 - 1)

### 3.3 从 MIDI 文件到音频输出

#### 3.3.1 MIDI文件加载

```
AlphaSynth.loadMidiFile(midiFile)
  → sequencer.loadMidi(midi) // MidiFileSequencer
    → createStateFromFile(midiFile)
      → 遍历 midiFile.events 构建 SynthEvent[]
      → 计算每个事件的绝对时间（毫秒）
      → 构建 tempoChanges[] 数组
      → 插入节拍器事件
      → 按时间排序所有事件
```

#### 3.3.2 实时合成循环

```
AlphaSynth.onSampleRequest() // 被ISynthOutput回调
  循环 SynthConstants.MicroBufferCount(32) 次:
    1. sequencer.fillMidiEventQueue() — 将到期的MIDI事件入队
    2. synthesizer.synthesize(samples, bufferPos, bufferSize) — 合成音频样本
    3. 收集已处理的事件用于回调
  4. output.addSamples(samples) — 将合成样本送入输出缓冲
```

#### 3.3.3 MidiFileSequencer 内部机制

顺序器维护一个 `MidiSequencerState`，包含：
- `synthData: SynthEvent[]` — 所有MIDI事件（按时间排序）
- `eventIndex` — 当前已处理到的事件下标
- `currentTime` — 当前合成时间位置（毫秒）
- `tempoChanges[]` — 速度变化时间线
- `tempoChangeIndex` — 当前速度段下标

每次调用 `fillMidiEventQueue()`：
1. 前进 `currentTime` 一个微缓冲时长
2. 将时间 <= currentTime 的事件派发到合成器
3. 合成器处理 NoteOn/NoteOff/Bend/ControlChange 等

#### 3.3.4 SoundFont 合成（TinySoundFont）

TinySoundFont 是基于 SoundFont2 规范的软件合成器：
- 加载 `.sf3`/`.sf2` 文件中的音频样本
- 为每个活跃音符分配 Voice（合成通道）
- 支持：音高调制（PitchWheel/NoteBend）、音量调制（Volume Envelope）、低通滤波器、LFO
- 使用 SoundFont 的 preset/region 映射 MIDI program 到样本

#### 3.3.5 节拍器

在 `createStateFromFile()` 中，根据拍号信息自动插入节拍器嘀嗒事件：
- 在每拍的开始位置生成 NoteOn/NoteOff
- 第1拍使用较高的音高(MetronomeKey=33)
- 其余拍使用较低音高
- 通过 `metronomeChannel`（最后一个通道）独立控制音量

### 3.4 播放控制

| 操作 | 方法 | 行为 |
|------|------|------|
| 播放 | `play()` | 设置状态为 Playing，激活输出，可选预备拍 |
| 暂停 | `pause()` | 暂停输出，关闭所有音符释放声音 |
| 停止 | `stop()` | 暂停 + 重置位置到起点，关闭所有音符 |
| 跳转 | `timePosition = value` | 静默合成跳转(含速度变化重置)，重置输出缓冲 |
| 循环 | `isLooping = true` | 到达末尾自动跳回起点 |
| 播放范围 | `playbackRange = PlaybackRange` | 限制播放范围（用于AB循环） |

**播放完成检查** (`checkForFinish()`)：
1. 当前 tick >= endTick
2. 待播放样本数量 <= 0
3. 根据循环模式：触发finished事件 → 停止 或 跳回起点

### 3.5 速度/播放速度

- **原始速度**: 来自乐谱的 `MasterBar.tempoAutomations`
- **播放速度**: `playbackSpeed` (0.125 ~ 8倍速)
- **实际时间**: `currentTime = state.currentTime / playbackSpeed`

核心公式：
```
毫秒 = ticks × (60000 / (BPM × division))
```

其中 `MidiUtils.QuarterTime = 960`（每四分音符的嘀嗒数），division = 960。

---

## 4. 时间线构建与查找

### 4.1 构建过程

在 `MidiFileGenerator.generate()` 过程中，同时构建 `MidiTickLookup`：

```
_generateMasterBar()
  → 创建 MasterBarTickLookup(masterBar, startTick, endTick)
  → 存入 tempoChanges[]
  → tickLookup.addMasterBar(lookup)

_generateBeat()
  → tickLookup.addBeat(beat, beatStart, audioDuration)
  → MasterBarTickLookup.addBeat(beat, start, end) 
    → 执行复杂的分片算法处理多声部重叠
```

**分片算法** (`MasterBarTickLookup.addBeat()`):
当多个声部的拍在时间轴上重叠时，需要将时间轴切分为不重叠的时间片，每个片包含所有重叠的拍。算法涵盖 14 种情况（A~N），如：
- 新拍完全在现有片之后 → 追加新片
- 新拍与现有片部分重叠 → 分割现有片，插入新片
- 新拍与现有片完全重叠 → 合并标记

### 4.2 查找过程

```
MidiTickLookup.findBeat(trackLookup, tick)
  → 尝试快速路径: 通过当前拍提示的 nextBeat 链式查找
  → 失败则慢速路径: 二分查找 MasterBar，再线性查找拍
```

- **快速路径**: 利用 `currentBeatHint` 的 `nextBeat` 指针，O(1) 定位下一拍
- **慢速路径**: `_findMasterBar(tick)` 使用二分查找，在 MasterBarTickLookup[] 数组中定位所在小节

### 4.3 多小节休止处理

对于多小节休止，`MidiTickLookup.multiBarRestInfo` 存储了休止小节的范围映射。查找时通过 `_fillNextBeatMultiBarRest()` 跳过多个小节。

---

## 5. 同步点系统 (Backing Track Sync)

同步点用于将 MIDI 合成时间轴与外部伴奏音频对齐：

```
BackingTrackSyncPoint:
  - masterBarIndex / masterBarOccurence  — 对应的小节和出现次数
  - synthTick / synthBpm / synthTime     — MIDI时间轴
  - syncTime / syncBpm                    — 外部音频时间轴
```

`MidiFileGenerator._processBarTimeWithSyncPoints()` 处理已有同步点的小节，`_processBarTimeWithNewSyncPoints()` 在处理速度变化时生成新的同步点。

`MidiFileSequencer.mainUpdateSyncPoints()` 在加载时处理同步点插值：当 MIDI 时间轴上的速度变化点与同步点不一致时，计算插值同步点确保线性映射。

`ExternalMediaPlayer` 和 `BackingTrackPlayer` 分别处理外部媒体和内置伴奏轨的同步播放。

---

## 6. 播放光标（播放条）与元素高亮系统

### 6.1 概述

alphaTab 的播放光标系统在 `AlphaTabApiBase` 中集成，由光标处理器(`CursorHandler`)、滚动处理器(`ScrollHandlers`)、时间线查找表(`MidiTickLookup`)和UI外观层(`IUiFacade`)四个模块协作实现。

**核心流程**:

```
AlphaSynth.positionChanged事件
  → _onPlayerPositionChanged()
    → _cursorUpdateTick(tick, cursorSpeed)
      → MidiTickLookup.findBeatWithChecker(tick)
        → 快速路径: _findBeatFast() 通过nextBeat链式O(1)查找
        → 慢速路径: _findBeatSlow() 二分查找MasterBar + 线性查找拍
      → _cursorUpdateBeat(lookupResult)
        → _internalCursorUpdateBeat()
          → cursorHandler.placeBarCursor()  — 放置小节光标
          → cursorHandler.placementBeatCursor() / transitionBeatCursor() — 放置/动画拍光标
          → uiFacade.highlightElements()    — 高亮音符元素
          → scrollHandler.onBeatCursorUpdating() — 自动滚动
          → _onPlayedBeatChanged() / _onActiveBeatsChanged() — 触发事件
```

### 6.2 光标系统架构

#### 6.2.1 光标容器 (`Cursors`)

```typescript
class Cursors {
    cursorWrapper: IContainer;   // 整个乐谱的包装容器
    barCursor: IContainer;       // 小节光标 — 覆盖整小节矩形区域
    beatCursor: IContainer;      // 拍光标 — 竖线，在拍之间动画过渡
    selectionWrapper: IContainer; // 选择区域包装容器
}
```

三个层叠的 DOM 元素，通过 CSS 样式（背景色、透明度、位置）控制视觉效果。

#### 6.2.2 光标处理器 (`CursorHandler.ts`)

`ICursorHandler` 接口定义：

| 方法 | 参数 | 职责 |
|------|------|------|
| `onAttach(cursors)` | Cursors | 处理器激活时初始化 |
| `onDetach(cursors)` | Cursors | 处理器停用时清理 |
| `placeBarCursor(barCursor, beatBounds)` | IContainer, BeatBounds | 放置小节光标（覆盖整小节区域） |
| `placeBeatCursor(beatCursor, beatBounds, startBeatX)` | IContainer, BeatBounds, number | 放置拍光标（竖线） |
| `transitionBeatCursor(beatCursor, beatBounds, startBeatX, nextBeatX, duration, cursorMode)` | 同上 + 下一拍X + 时长 + 模式 | 过渡动画拍光标 |

**两种内置实现**：

1. **`NonAnimatingCursorHandler`** — 无动画，跳转到当前拍
   - `placeBeatCursor()`: 直接设置到 `beatBounds.onNotesX`
   - `placeBarCursor()`: 覆盖整小节 `visualBounds`
   - `transitionBeatCursor()`: 直接调用 `placeBeatCursor()` 无过渡

2. **`ToNextBeatAnimatingCursorHandler`** — 平滑动画过渡
   - `placeBeatCursor()`: 初始放置到 `onNotesX`
   - `transitionBeatCursor()`: CSS transition 从当前X动画到下一拍X
   - 动画时长乘以 **2倍因子** (cursorMode=ToNextBeat时) 防止光标提前停止
   - 通过 `cursor.transitionToX(duration, nextBeatX)` 驱动

**选择逻辑** (`_updateCursorHandler()`):
- `settings.player.enableAnimatedBeatCursor === true` → `ToNextBeatAnimatingCursorHandler`
- `settings.player.enableAnimatedBeatCursor === false` → `NonAnimatingCursorHandler`
- 用户可设置 `customCursorHandler` 完全自定义

#### 6.2.3 光标更新时机

`_onPlayerPositionChanged()` 是核心入口：

```typescript
private _onPlayerPositionChanged(e: PositionChangedEventArgs): void {
    this.uiFacade.beginInvoke(() => {
        const cursorSpeed = e.modifiedTempo / e.originalTempo;
        this._cursorUpdateTick(e.currentTick, false, cursorSpeed, false, e.isSeek);
    });
}
```

在以下时机也会触发光标更新：
- **状态变化** (`_onPlayerStateChanged`): 暂停时对齐光标到拍的起始位置
- **播放完成** (`_onPlayerFinished`): 停止光标
- **手动跳转** (`seek`/`tickPosition`): 带 `isSeek=true` 参数强制刷新
- **选中播放范围** (`playbackRange`): 跳转到起点后更新光标

### 6.3 拍查找算法

在 `MidiTickLookup.findBeatWithChecker()` 中实现：

#### 快速路径 (`_findBeatFast`) — O(1)

```
当前拍提示(currentBeatHint)仍然有效:
  tick 在 [currentBeatHint.start, currentBeatHint.end) 内 → 直接返回

下一拍链式查找:
  tick 在 [currentBeatHint.nextBeat.start, currentBeatHint.nextBeat.end) 内
  且可见性检查通过
  → 填充 nextBeat 的后续链 (_fillNextBeat)
  → 返回 nextBeat
```

**`_fillNextBeat()`**：预填充 MidiTickLookupFindBeatResult 的 nextBeat 链，支持：
- 多小节休止 (`_fillNextBeatMultiBarRest`) — 跳过多个小节
- 默认模式 (`_fillNextBeatDefault`) — 在当前 MasterBar 内查找下一个可见拍

#### 慢速路径 (`_findBeatSlow`) — O(log n + m)

```
1. _findMasterBar(tick): 二分查找 MasterBarTickLookup[]
   → 找到 tick 所在的主小节
2. _findBeatInMasterBar(masterBar, firstBeat, tick, checker):
   → 在 MasterBar 的 BeatTickLookup 链表中线性遍历
   → 每个 BeatTickLookup 是已分片的不重叠时间区间
   → 返回 tick 所属的 BeatTickLookup
3. 填充 nextBeat 链
```

### 6.4 光标动画计算

在 `_internalCursorUpdateBeat()` 中，光标的 X 位置计算：

```typescript
// 动画宽度 = 下一拍X - 当前拍onNotesX
const animationWidth = nextBeatX - beatBoundings.onNotesX;

// 相对位置 = (当前Tick - 拍起始Tick) / 拍时长Tick
const ratioPosition = (previousTick - lookupResult.start) / lookupResult.tickDuration;

// 起始X = onNotesX + 动画宽度 × 已完成比例
startBeatX = beatBoundings.onNotesX + animationWidth * ratioPosition;

// 剩余时长 = 总时长 - 已消耗时长
duration = duration - duration * ratioPosition;

// 考虑播放速度修正
duration = duration / cursorSpeed;
```

**跳转判定** — 是否重新放置（重置）光标：
- `forceUpdate === true`（强制更新）
- `_isInitialBeatCursorUpdate === true`（首次更新）
- 小节Y坐标变化（换行/跨页）
- `startBeatX < previousBeatBounds.onNotesX`（向后跳转）
- 小节索引跳跃 > 1（跳过多个小节）

**下一拍X计算**：
- `cursorMode === ToNextBeat`: 使用下一拍的 `onNotesX`，若在同一谱表系统内
- `cursorMode === ToEndOfBeat`: 使用当前拍的 `realBounds.x + realBounds.w`（拍末尾）

### 6.5 元素高亮系统

当 `settings.player.enableElementHighlighting` 启用时：

```typescript
if (this.settings.player.enableElementHighlighting) {
    for (const highlight of beatsToHighlight) {
        const className = BeatContainerGlyph.getGroupId(highlight.beat);
        this.uiFacade.highlightElements(className, beat.voice.bar.index);
    }
}
```

#### 高亮数据来源 (`BeatTickLookup.highlightedBeams`)

在 MIDI 文件生成阶段，`MasterBarTickLookup.addBeat()` 处理多声部拍重叠时，将重叠在同一时间片上的所有拍记录到 `highlightedBeats[]` 数组中：

```typescript
class BeatTickLookup {
    private _highlightedBeats: Map<number, boolean> = new Map();
    highlightedBeats: BeatTickLookupItem[] = [];

    highlightBeat(beat: Beat, playbackStart: number): void {
        if (!this._highlightedBeats.has(beat.id)) {
            this._highlightedBeats.set(beat.id, true);
            this.highlightedBeats.push(new BeatTickLookupItem(beat, playbackStart));
        }
    }
}
```

#### UI 层实现 (`IUiFacade`)

| 方法 | 职责 |
|------|------|
| `highlightElements(groupId, masterBarIndex)` | 通过 CSS class 高亮音符元素 |
| `removeHighlights()` | 每次光标准备更新前，清除所有高亮 |

在 Web 平台 `BrowserUiFacade` 中：
- `highlightElements()`: 查找拥有指定 CSS class 的 DOM 元素，添加高亮样式
- `removeHighlights()`: 移除所有高亮相关 CSS class

### 6.6 自动滚动系统 (`ScrollHandlers.ts`)

`IScrollHandler` 接口定义：

| 方法 | 职责 |
|------|------|
| `forceScrollTo(currentBeatBounds)` | 强制滚动到当前拍的谱表位置 |
| `onBeatCursorUpdating(startBeat, endBeat, cursorMode, startX, endX, duration)` | 拍光标更新时同步滚动 |

**三种内置滚动模式** (`ScrollMode`)：

| 模式 | 行为 | 实现类 |
|------|------|--------|
| `Off` | 不滚动 | 无 |
| `Continuous` | 连续平滑跟随光标 | `VerticalContinuousScrollHandler` / `HorizontalContinuousScrollHandler` |
| `OffScreen` | 仅当光标超出可视区时才滚动 | `VerticalOffScreenScrollHandler` / `HorizontalOffScreenScrollHandler` |
| `Smooth` | 平滑滚动，保持光标居中 | `VerticalSmoothScrollHandler` / `HorizontalSmoothScrollHandler` |

每种模式根据 `LayoutMode` 是垂直还是水平，分别有垂直/水平两种实现。

### 6.7 用户交互

当 `settings.player.enableUserInteraction` 启用时，用户可以通过点击乐谱进行 seek 操作：

- **点击定位**: 点击谱面触发 `_onContainerPointerUp()` → `_tryHandleMouseClicks()`
  - 通过 `MidiTickLookup.findBeat()` 找到点击位置对应的拍
  - 通过 `MidiTickLookup.getBeatStart()` 获取拍的精确 tick 位置
  - 调用 `player.tickPosition = tick` 执行跳转
  - 同时更新光标：`_cursorUpdateTick(tick, false, 1, true)`

- **选中播放范围**: 鼠标拖拽选择起止范围，通过 `playbackRange` 限制播放区间
  - `_selectionStart` / `_selectionEnd` 记录起止拍
  - 播放时自动使用选中的范围

### 6.8 完整事件链

```
AlphaSynth(Worker线程)
  ├─ positionChanged 事件 (currentTick, isSeek)
  ↓
AlphaTabApiBase._onPlayerPositionChanged()
  ├─ uiFacade.beginInvoke()          → 主线程异步调度
  │  └─ _cursorUpdateTick(tick)     
  │     ├─ MidiTickLookup.findBeatWithChecker() → 查找当前拍
  │     └─ _cursorUpdateBeat(result)
  │        ├─ cursorHandler.placeBarCursor()    → 更新小节覆层
  │        ├─ cursorHandler.placeBeatCursor()   → 更新拍竖线
  │        │  └─ transitionBeatCursor()         → CSS动画过渡
  │        ├─ uiFacade.removeHighlights()       → 清除旧高亮
  │        ├─ uiFacade.highlightElements()      → 高亮当前拍元素
  │        ├─ scrollHandler.onBeatCursorUpdating() → 自动滚动
  │        ├─ _onPlayedBeatChanged(beat)        → 触发事件
  │        └─ _onActiveBeatsChanged()           → 触发事件
  └─ uiFacade.triggerEvent(playerPositionChanged) → 外部事件
```

---

## 7. 关键算法

### 7.1 弯音(Pitch Wheel)计算

```
PitchBendRange = 8 × 2 = 16 semitones（上下各8个全音）
PitchValuePerSemitone = DefaultPitchWheel(8192) / 16 = 512

getPitchWheel(bendValue): 
  // bendValue 是 1/4 音单位, 每 bendValue = 1/2 semitone
  return DefaultPitchWheel + (bendValue / 2) × PitchValuePerSemitone
```

弯音值插值算法 (`_generateBendValues()`):
```
steps = max(6 × semitones, millisecondsBetweenPoints / 150)
ticksPerStep = totalTicks / steps
pitchPerStep = (endValue - startValue) / steps
```

### 7.2 颤音(Vibrato)生成

使用正弦波调制音高：
```
for each phase:
  bend = bendBase + amplitude × sin(phase × π / phaseHalf)
```

4种颤音各可配置波长和振幅，以MIDI嘀嗒为单位。

### 7.3 力度转换

```
dynamicToVelocity(dynamicValue):
  PPP → 15, PP → 31, P → 47, MP → 63
  MF → 79,  F → 95,  FF → 111, FFF → 127
```

调整因子：
- hammer-on: -16 (velocity - 16)
- ghost note: -16
- accent: +16, heavy accent: +32

---

## 7. 文件引用汇总

所有关键文件路径（相对于 `alphaTab-develop/packages/alphatab/src/`）：

| 路径 | 说明 |
|------|------|
| `importer/ScoreLoader.ts` | 统一加载入口 |
| `importer/Gp3To5Importer.ts` | GP3/4/5导入器 |
| `importer/Gp7To8Importer.ts` | GP7/8导入器 |
| `importer/GpxImporter.ts` | GPX导入器 |
| `midi/MidiFileGenerator.ts` | MIDI事件生成器（核心） |
| `midi/AlphaSynthMidiFileHandler.ts` | MIDI事件写入器 |
| `midi/MidiFile.ts` | MIDI文件模型 |
| `midi/MidiEvent.ts` | MIDI事件类型定义 |
| `midi/MidiUtils.ts` | MIDI工具函数 |
| `midi/MidiPlaybackController.ts` | 播放控制器（重复/跳跃） |
| `midi/MidiTickLookup.ts` | 时间线查找表 |
| `midi/MasterBarTickLookup.ts` | 小节时间查找 + 分片算法 |
| `midi/BeatTickLookup.ts` | 拍时间查找切片 |
| `synth/AlphaSynth.ts` | 合成器主控制器 |
| `synth/MidiFileSequencer.ts` | MIDI事件序列器 |
| `synth/synthesis/TinySoundFont.ts` | SoundFont合成引擎 |
| `synth/synthesis/Voice.ts` | 合成音色（音符发声） |
| `synth/SynthConstants.ts` | 合成器常量 |
| `synth/PlayerSettings.ts` | 播放器设置 |
| `synth/IAlphaSynth.ts` | AlphaSynth接口 + BackingTrackSyncPoint |
| `AlphaTabApiBase.ts` | 播放光标与元素高亮主控制器 |
| `CursorHandler.ts` | 光标处理器接口与实现（动画/非动画） |
| `ScrollHandlers.ts` | 自动滚动处理器接口与实现 |
| `platform/Cursors.ts` | 光标容器（barCursor, beatCursor, selectionWrapper） |
| `platform/IUiFacade.ts` | UI外观抽象接口（highlightElements, removeHighlights等） |

---

## 8. 架构总结

alphaTab的播放系统采用"**生成式**"架构而非"**实时解析**"架构：

1. **先生成MIDI，再播放** — 先将乐谱完全转换为SMF格式的MIDI文件，然后由SoundFont合成器播放
2. **时间线预计算** — MIDI生成过程中同时构建Tick查找表，实现毫秒级的位置查找
3. **技法效果通过MIDI模拟** — 推弦、滑音、颤音等全部映射为PitchBend事件序列，轮扫/颤音拆分为多个NoteOn/Off
4. **SoundFont合成** — 使用标准SoundFont2音色库，TinySoundFont引擎实现高质量合成
5. **异步流水线** — 合成器在高优先级线程/Worker中运行，通过缓冲队列与UI线程解耦
6. **光标与高亮分离** — 播放光标（barCursor+beatCursor）通过 Container 层叠在乐谱之上，元素高亮通过 CSS class 直接修改呈现层，两者独立控制
7. **查找两级加速** — 拍查找采用「快速链式路径(nextBeat指针) + 慢速二分路径(MasterBar二分)」，兼顾实时播放的 O(1) 性能和跳转/循环场景的通用性