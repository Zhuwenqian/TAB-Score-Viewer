# alphaTab 推弦 MIDI 合成原理分析

## 1. 概述

本文档分析 `alphaTab-develop` 仓库（基于 coderline/alphatab 的 TypeScript 源码）中**推弦（Bend）**、**摇把（Whammy）**、**滑弦（Slide）**与**揉弦（Vibrato）**的 MIDI 合成实现原理，并给出可移植到 ApolloTab（Python）的要点。

核心源码位置：

- [alphaTab-develop/packages/alphatab/src/midi/MidiFileGenerator.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/midi/MidiFileGenerator.ts)
- [alphaTab-develop/packages/alphatab/src/model/BendPoint.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/model/BendPoint.ts)
- [alphaTab-develop/packages/alphatab/src/model/BendType.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/model/BendType.ts)
- [alphaTab-develop/packages/alphatab/src/model/WhammyType.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/model/WhammyType.ts)
- [alphaTab-develop/packages/alphatab/src/midi/AlphaSynthMidiFileHandler.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/midi/AlphaSynthMidiFileHandler.ts)
- [alphaTab-develop/packages/alphatab/src/synth/SynthConstants.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/synth/SynthConstants.ts)

---

## 2. 数据模型

### 2.1 BendPoint

推弦曲线由若干离散点 `BendPoint` 组成。

```ts
export class BendPoint {
    public static readonly MaxPosition: number = 60;  // 时间相对位置最大值
    public static readonly MaxValue: number = 12;     // 音高偏移最大值
    public offset: number;  // 0~60，表示在音符时值内的相对位置
    public value: number;   // 0~12，单位为 1/4 半音（即 1 个 value = 0.5 半音）
}
```

> 关键约定：**`value` 的单位是 1/4 半音**。例如 `value = 2` 表示升高 1 个半音；`value = 4` 表示升高 2 个半音（Full bend 在标准调弦下）。

### 2.2 BendType（音符级推弦）

- `None`：无推弦
- `Custom`：自定义曲线（GP3-5 常用）
- `Bend`：从原位推到更高音
- `Release`：释放前音的推弦
- `BendRelease`：先推后放
- `Hold`：保持已推状态
- `Prebend`：音符开始前已推弦
- `PrebendBend`：先预推再推
- `PrebendRelease`：先预推再释放

### 2.3 WhammyType（拍级摇把）

- `None` / `Custom` / `Dive` / `Dip` / `Hold` / `Predive` / `PrediveDive`

摇把效果作用于整个拍（Beat），通过拍子的 `whammyBarPoints` 描述。

### 2.4 与 ApolloTab 现有模型的对应

ApolloTab 当前已有 `BendData`（见 `ApolloTab/models/note.py`），其字段：

- `bend_type`
- `value`
- `max_value`
- `points: List[(position, value)]`
- `has_release`

这与 alphaTab 的 `BendPoint` 概念同源，但数据单位不同：

| 项目 | alphaTab | ApolloTab 当前 |
|------|----------|----------------|
| 时间位置 | `offset` ∈ [0, 60] | `position` ∈ [0, 1] |
| 音高偏移 | `value` ∈ [0, 12]，1/4 半音 | `value` 为 25/50/100 等 "cents" |

移植时需要进行单位换算。

---

## 3. 弯音范围初始化

alphaTab 在生成每个音轨的开头，通过 **RPN（Registered Parameter Number）** 把 MIDI Pitch Bend Range 设为 **±12 半音**：

```ts
// 选择 RPN 0: Pitch Bend Range
this._handler.addControlChange(..., ControllerType.RegisteredParameterFine, 0);
this._handler.addControlChange(..., ControllerType.RegisteredParameterCourse, 0);

// Data Entry 设置弯音范围为 12 半音
this._handler.addControlChange(..., ControllerType.DataEntryFine, 0);
this._handler.addControlChange(..., ControllerType.DataEntryCoarse, 12);
```

> 为什么设 12 半音？GP 文件中的摇把最大可达 8 个全音（16 半音），alphaTab 源码注释写 "GP has 8 full tones on whammys"，但实际常量取 `8 * 2 = 16` 后又被写死为 `12`。此处按源码实际执行值 **12 半音** 记录。

ApolloTab 当前 `midi_converter.py` 尚未设置弯音范围，默认依赖 FluidSynth / 合成器的 ±2 半音。要正确播放 Full bend 或摇把，必须先发送上述 RPN 序列。

---

## 4. Pitch Wheel 值计算

### 4.1 常量

```ts
private static readonly _pitchBendRangeInSemitones = 8 * 2;  // 源码实际=16, 但DataEntry发12
private static readonly _pitchValuePerSemitone: number =
    SynthConstants.DefaultPitchWheel / MidiFileGenerator._pitchBendRangeInSemitones;
```

其中：

```ts
SynthConstants.MaxPitchWheel = 0x4000 = 16384
SynthConstants.DefaultPitchWheel = MaxPitchWheel / 2 = 8192
```

### 4.2 换算公式

```ts
public static getPitchWheel(bendValue: number) {
    // bendValue 单位为 1/4 半音，所以实际半音数要除以 2
    return SynthConstants.DefaultPitchWheel + (bendValue / 2) * MidiFileGenerator._pitchValuePerSemitone;
}
```

代入数值：

```
Pitch Wheel = 8192 + (bendValue / 2) * (8192 / 16)
            = 8192 + bendValue * 256
```

| bendValue | 半音偏移 | Pitch Wheel |
|-----------|----------|-------------|
| 0 | 0 | 8192 |
| 2 | +1 | 8704 |
| 4 | +2 (Full) | 9216 |
| 8 | +4 | 10240 |
| 12 | +6 | 11264 |

ApolloTab 当前 `_cents_to_midi()` 按 100 cents = 8192 计算，与 alphaTab 不完全一致。移植时建议统一为 alphaTab 公式，并配套发送 RPN=12。

---

## 5. 推弦事件生成流程

### 5.1 触发位置

在 `_generateNote()` 末尾，根据效果分支：

```ts
if (note.hasBend) {
    this._generateBend(...);
} else if (note.beat.hasWhammyBar && note.index === 0) {
    this._generateWhammy(...);
} else if (slide) {
    this._generateSlide(...);
} else if (vibrato) {
    this._generateVibrato(...);
}
```

### 5.2 初始弯音

在 `note_on` 之前，先发送初始 Pitch Bend：

```ts
let initialBend = 0;
if (note.hasBend) {
    initialBend = getPitchWheel(note.bendPoints[0].value);
} else if (note.beat.hasWhammyBar) {
    initialBend = getPitchWheel(note.beat.whammyBarPoints[0].value);
} else if (note.isTieDestination || legatoSlide) {
    initialBend = -1;  // 不发送，继承前音状态
} else {
    initialBend = getPitchWheel(0);
}

if (initialBend >= 0) {
    this._handler.addNoteBend(track, noteStart, channel, noteKey, initialBend);
}
```

> alphaTab 区分 `addNoteBend`（MIDI 2.0 单音弯音，SMF1 回退为通道弯音）与 `addBend`（通道弯音）。ApolloTab 当前 FluidSynth 只支持 MIDI 1.0 通道弯音，因此可直接用通道级 `pitch_bend`。

### 5.3 `_generateBend()` 处理逻辑

`_generateBend()` 根据 `BendType` 与 `BendStyle`（Default / Gradual / Fast）构造实际要播放的 `playedBendPoints`，最终调用 `_generateWhammyOrBend()` 插值。

主要行为：

| BendType | Default | Gradual | Fast |
|----------|---------|---------|------|
| `Custom` | 使用原始 `bendPoints` | - | - |
| `Bend` / `Release` | 使用原始点 | 重建为 0→Max 的两点 | 走 SongBook 快速路径 |
| `BendRelease` | 使用原始点 | 重建为 0→Max→0 三点 | 走 SongBook 快速路径 |
| `Hold` | 使用原始点 | - | - |
| `Prebend` | 使用原始点 | - | - |
| `PrebendBend` | 使用原始点 | 0→Max 两点 | 先发送预推值，再走 SongBook |
| `PrebendRelease` | 使用原始点 | 0→0 两点 | 先发送预推值，再走 SongBook |

**Tie（延音线）处理**：若当前音符是 `TieOrigin` 且设置 `extendBendArrowsOnTiedNotes`，alphaTab 会把弯音时长扩展到后续所有 tied 音符的总时长，直到遇到下一个有推弦或揉弦的音符。

**Prebend 提前触发**：若第一个点 `value > 0` 且不是 continued bend，alphaTab 会把 `noteStart` 提前 1 tick，避免音符开头出现"咔嗒"音高跳变。

### 5.4 `_generateWhammy()` 摇把逻辑

与 `_generateBend()` 几乎一致，区别：

- 数据源为 `beat.whammyBarPoints`
- 只触发一次（`note.index === 0`）
- 通过 `addBend()` 发送**通道级** Pitch Bend，影响该拍所有音符

### 5.5 `_generateSlide()` 滑弦逻辑

滑弦也被建模为 `BendPoint` 序列：

- `IntoFromAbove`：`(0, +offset) → (short, 0)`
- `IntoFromBelow`：`(0, -offset) → (short, 0)`
- `Shift` / `Legato`：`(0, 0) → (MaxPosition, dy)`，其中 `dy = (targetPitch - currentPitch) * 2`（单位为 1/4 半音）
- `OutDown` / `OutUp`：在末尾快速滑出

最终同样调用 `_generateWhammyOrBend()`。

---

## 6. 曲线插值：`_generateWhammyOrBend()` 与 `_generateBendValues()`

这是把离散 `BendPoint` 转换成密集 MIDI Pitch Bend 事件的核心。

```ts
private _generateWhammyOrBend(
    noteStart: number,
    duration: number,
    playedBendPoints: BendPoint[],
    tempoOnBeatStart: number,
    addBend: (tick: number, value: number) => void
): void {
    const ticksPerPosition: number = duration / BendPoint.MaxPosition;
    for (let i = 0; i < playedBendPoints.length - 1; i++) {
        const currentPoint = playedBendPoints[i];
        const nextPoint = playedBendPoints[i + 1];
        const currentBendValue = getPitchWheel(currentPoint.value);
        const nextBendValue = getPitchWheel(nextPoint.value);
        const ticksBetweenPoints = ticksPerPosition * (nextPoint.offset - currentPoint.offset);
        const tick = noteStart + ticksPerPosition * currentPoint.offset;
        this._generateBendValues(tick, ticksBetweenPoints, currentBendValue, nextBendValue, tempoOnBeatStart, addBend);
    }
}
```

`_generateBendValues()` 插值策略：

```ts
const millisBetweenPoints = MidiUtils.ticksToMillis(ticksBetweenPoints, tempoOnBeatStart);
const numberOfSemitones = Math.abs(nextBendValue - currentBendValue) / _pitchValuePerSemitone;
const numberOfSteps = Math.max(
    _minBreakpointsPerSemitone * numberOfSemitones,   // 每半音至少 6 个断点
    millisBetweenPoints / _millisecondsPerBreakpoint  // 每 150ms 至少 1 个断点
);
const ticksPerBreakpoint = ticksBetweenPoints / numberOfSteps;
const pitchPerBreakpoint = (nextBendValue - currentBendValue) / numberOfSteps;

for (let i = 0; i < numberOfSteps; i++) {
    addBend(tick | 0, Math.round(currentBendValue));
    currentBendValue += pitchPerBreakpoint;
    currentTick += ticksPerBreakpoint;
}
addBend(endTick | 0, nextBendValue);
```

> 注意：alphaTab 的插值**不保证固定时间间隔**，而是优先保证"每半音足够平滑"与"每 150ms 至少一个断点"的平衡。时长很短、音高变化又很小时，事件会稀疏；音高跨度大时，事件会变密。

---

## 7. SongBook 快速弯音路径

`BendStyle.Fast`（常见于乐谱/SongBook 显示模式）不走逐点插值，而是把所有目标值压缩到一个较短固定时长内：

```ts
private _generateSongBookWhammyOrBend(
    noteStart, duration, bendAtBeginning, bendValues, bendDuration, tempo, addBend
): void {
    const startTick = bendAtBeginning ? noteStart : noteStart + duration - bendDuration;
    const ticksBetweenPoints = bendDuration / (bendValues.length - 1);
    for (let i = 0; i < bendValues.length - 1; i++) {
        const current = getPitchWheel(bendValues[i]);
        const next = getPitchWheel(bendValues[i + 1]);
        const tick = startTick + ticksBetweenPoints * i;
        this._generateBendValues(tick, ticksBetweenPoints, current, next, tempo, addBend);
    }
}
```

- `bendDuration` 默认由 `settings.player.songBookBendDuration` 控制（毫秒）
- `bendAtBeginning=true` 表示从音符开头开始弯音（如 Dip）
- `bendAtBeginning=false` 表示在音符结束前才开始弯音（如普通 Bend / Dive）

---

## 8. 揉弦（Vibrato）

alphaTab 不用 LFO 控制器，而是用正弦波生成大量 Pitch Bend 事件：

```ts
private _generateVibratorWithParams(
    noteStart, noteDuration, phaseLength, bendBase, bendAmplitude, addBend
): void {
    const resolution = this.vibratoResolution;  // 默认 16 ticks
    const phaseHalf = phaseLength / 2;
    const noteEnd = noteStart + noteDuration;
    while (noteStart < noteEnd) {
        let phase = 0;
        const phaseDuration = noteStart + phaseLength < noteEnd ? phaseLength : noteEnd - noteStart;
        while (phase < phaseDuration) {
            const bend = bendBase + bendAmplitude * Math.sin((phase * Math.PI) / phaseHalf);
            addBend((noteStart + phase) | 0, getPitchWheel(bend));
            phase += resolution;
        }
        noteStart += phaseLength;
    }
    addBend(noteEnd | 0, getPitchWheel(bendBase));  // 结尾复位
}
```

参数来源（`PlayerSettings`）：

- `noteSlightLength` / `noteSlightAmplitude`
- `noteWideLength` / `noteWideAmplitude`
- `beatSlightLength` / `beatSlightAmplitude`
- `beatWideLength` / `beatWideAmplitude`

若揉弦出现在推弦末尾（tie destination 且 origin 有推弦），`bendBase` 取推弦终点值，避免音高跳回本位。

---

## 9. 通道隔离策略

alphaTab 用**主/副两个通道**（primaryChannel / secondaryChannel）播放同一轨道：

```ts
private _needsSecondaryChannel(note: Note): boolean {
    return note.hasBend || note.beat.hasWhammyBar || note.beat.vibrato !== VibratoType.None;
}
```

- 普通音符：使用 `primaryChannel`
- 有推弦/摇把/揉弦的音符：使用 `secondaryChannel`

> 这是为了防止弯音状态泄漏到同通道其他音符。ApolloTab 当前只用一个通道，若加入推弦必须考虑：要么为每个"带效果音符"动态分配独立通道，要么在 note_on 前/ note_off 后严格复位 pitch_bend。

---

## 10. 移植到 ApolloTab 的建议

### 10.1 最小改动路径

1. **扩展 `BendData`**：新增 `bend_type` / `bend_style` / `points` 标准化为 alphaTab 单位（offset 0~60，value 1/4 半音）。
2. **在 `midi_converter.py` 音轨初始化时发送 RPN**：把 Pitch Bend Range 设为 12 半音。
3. **统一 `_cents_to_midi()` 为 `get_pitch_wheel()`**：
   ```python
   DEFAULT_PITCH_WHEEL = 8192
   PITCH_BEND_RANGE_SEMITONES = 12
   PITCH_VALUE_PER_SEMITONE = DEFAULT_PITCH_WHEEL / PITCH_BEND_RANGE_SEMITONES

   def get_pitch_wheel(bend_value: float) -> int:
       # bend_value: 1/4 半音单位
       return int(DEFAULT_PITCH_WHEEL + (bend_value / 2) * PITCH_VALUE_PER_SEMITONE)
   ```
4. **替换现有 `_generate_bend_events()`**：采用 alphaTab 的 `_generateBendValues()` 插值逻辑，保证平滑度。
5. **处理 Whammy / Slide / Vibrato**：按第 5~8 节补充对应生成函数。
6. **严格复位 pitch_bend**：每个带弯音的音符结束后必须发送 `pitch_bend=8192`；或在 note_on 前对"干净"音符复位。

### 10.2 需要新增的数据结构

```python
from dataclasses import dataclass
from enum import Enum

class BendType(Enum):
    NONE = 0; CUSTOM = 1; BEND = 2; RELEASE = 3
    BEND_RELEASE = 4; HOLD = 5; PREBEND = 6
    PREBEND_BEND = 7; PREBEND_RELEASE = 8

class BendStyle(Enum):
    DEFAULT = 0; GRADUAL = 1; FAST = 2

class WhammyType(Enum):
    NONE = 0; CUSTOM = 1; DIVE = 2; DIP = 3
    HOLD = 4; PREDIVE = 5; PREDIVE_DIVE = 6

@dataclass
class BendPoint:
    offset: int = 0   # 0~60
    value: int = 0    # 1/4 半音
```

### 10.3 与现有 ApolloTab 代码的差异点

| 方面 | alphaTab | ApolloTab 当前 |
|------|----------|----------------|
| 弯音范围 | 通过 RPN 显式设为 12 半音 | 未设置，依赖默认 ±2 半音 |
| 推弦单位 | `value` = 1/4 半音 | `value` = 100 cents/四分之一音 |
| 插值策略 | 按半音数 + 时长双重保证断点 | 按固定最小间隔采样 |
| 通道使用 | 主/副通道隔离 | 单通道 |
| 摇把/滑弦/揉弦 | 全部用 Pitch Bend 模拟 | 仅简单推弦有初步实现 |

---

## 11. 参考资料

- alphaTab 源码: [alphaTab-develop/packages/alphatab/src/midi/MidiFileGenerator.ts](file:///e:/Projects/TAB%20Score%20Viewer/alphaTab-develop/packages/alphatab/src/midi/MidiFileGenerator.ts)
- ApolloTab 当前 MIDI 转换器: [ApolloTab/audio/midi_converter.py](file:///e:/Projects/TAB%20Score%20Viewer/venv/Lib/site-packages/ApolloTab/audio/midi_converter.py)
- ApolloTab 音符模型: [ApolloTab/models/note.py](file:///e:/Projects/TAB%20Score%20Viewer/venv/Lib/site-packages/ApolloTab/models/note.py)
