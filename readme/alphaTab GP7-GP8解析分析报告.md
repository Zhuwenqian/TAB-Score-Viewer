# alphaTab GP7/GP8 解析分析报告

## 一、文件容器结构

GP7/GP8 文件（`.gp`）本质是一个 **ZIP 压缩包**，内部包含以下文件：

| 文件名 | 类型 | 说明 |
|--------|------|------|
| `VERSION` | 文本 | 版本号，如 `"7.0"` |
| `Content/score.gpif` | XML | **核心**，乐谱全部数据 |
| `Content/BinaryStylesheet` | 二进制 | 显示样式键值对 |
| `Content/PartConfiguration` | 二进制 | 音轨视图配置（显示哪些谱表） |
| `Content/LayoutConfiguration` | 二进制 | 布局配置 |
| `Content/Assets/*` | 二进制 | 嵌入的音频文件（Backing Track） |

参考文件：`Gp7To8Importer.ts` 和 `Gp7Exporter.ts`

---

## 二、解析流程（两阶段）

### 阶段 1：ZIP 解包（`Gp7To8Importer.ts`）

```
Gp7To8Importer.readScore()
  ├── ZipReader 解压 ZIP
  ├── 遍历 entries，按文件名分类：
  │     ├── "score.gpif"          → XML 字符串
  │     ├── "BinaryStylesheet"     → 二进制数据
  │     ├── "PartConfiguration"    → 二进制数据
  │     └── "LayoutConfiguration"  → 二进制数据
  ├── GpifParser.parseXml(xml)     → 解析 XML 构建 Score
  ├── BinaryStylesheet.apply(score) → 应用样式
  ├── PartConfiguration.apply(score) → 应用音轨视图
  └── LayoutConfiguration.apply(score) → 应用布局
```

### 阶段 2：XML 解析（`GpifParser.ts`）

`GpifParser` 是核心，约 2900 行。采用 **两遍解析** 策略：

#### 第一遍：按 ID 解析所有元素（`_parseDom`）

```
GPIF 根节点
  ├── <Score>          → 标题、艺术家、版权、系统布局等元数据
  ├── <BackingTrack>   → 伴奏音轨（启用/源/资源ID）
  ├── <MasterTrack>    → 自动化和音轨顺序映射
  ├── <Tracks>         → 各音轨属性（乐器、调弦、MIDI、歌词等）
  ├── <MasterBars>     → 小节结构（拍号、调号、反复、段落标记等）
  ├── <Bars>           → 每轨每小节的谱号、八度位移等
  ├── <Voices>         → 声部→拍子映射
  ├── <Beats>          → 拍子属性（时值、技巧、动态、推弦等）
  ├── <Notes>          → 音符属性（品位、弦、滑音、颤音、装饰音等）
  ├── <Rhythms>        → 节奏定义（时值、附点、连音）
  └── <Assets>         → 嵌入资源（音频文件）
```

#### 第二遍：按映射关系组装模型（`_buildModel`）

```
_buildModel()
  ├── 遍历 _masterBars → 添加到 score
  ├── 遍历 _tracksMapping → 按顺序添加 Track
  ├── 遍历 _barsOfMasterBar → 纵向组装：
  │     ├── 每个 MasterBar 对应多个 Bar（每个 Track 一个）
  │     ├── 每个 Bar 有多个 Voice
  │     ├── 每个 Voice 有多个 Beat（**克隆！** GP6 复用 Beat 实例）
  │     ├── 每个 Beat 附加 Rhythm 信息（duration/dots/tuplet）
  │     └── 每个 Beat 有多个 Note（**克隆！**）
  ├── 应用 Track 自动化（Automations）
  ├── 应用 Sustain Pedal 标记
  └── 应用 MasterBar 自动化（Tempo/SyncPoint）
```

---

## 三、关键设计决策

### 1. ID 引用系统
GPIF XML 使用 **ID 引用** 而非嵌套结构。所有元素通过 `ref` 属性关联：
- `<Beats>` 通过 `ref` 引用 `<Rhythms>` 中的节奏定义
- `<Voices>` 通过空格分隔的 ID 列表引用 `<Beats>`
- `<Bars>` 通过空格分隔的 ID 列表引用 `<Voices>`

这导致需要两遍解析：先存入 Map，再按 ID 组装。

### 2. Beat/Note 克隆
```typescript
// important! we clone the beat because beats get reused
// in gp6, our model needs to have unique beats.
const beat: Beat = BeatCloner.clone(this._beatById.get(beatId)!);
```
GP 格式中 Beat 和 Note 实例可能被多个位置引用，alphaTab 的模型要求唯一实例，因此必须克隆。这在 `GpifParser.ts` 的 `_buildModel` 方法中有明确注释。

### 3. 无效 ID 哨兵值
`GpifParser._invalidId = '-1'` 表示该位置没有元素，解析时创建空的 Voice/Beat 占位。

### 4. 数值转换因子
- **推弦位置**：GPIF 范围 0-100 → 内部 0-60，因子 `_bendPointPositionFactor = 60/100`
- **推弦幅度**：GPIF 25/四分音符 → 内部 1/四分音符，因子 `_bendPointValueFactor = 1/25`
- **采样率**：固定 44100Hz 用于计算音频同步点偏移

### 5. 打击乐处理
- 通过 `InstrumentSet/Type` 为 `"drumKit"` 识别
- 打击乐轨道：`note.fret = -1, note.string = -1`，使用 `percussionArticulation`
- 非打击乐轨道：`note.percussionArticulation = -1`
- 非打击乐轨道清除 `percussionArticulations` 数组

### 6. 移调处理
- 支持 `Transpose`（Chromatic + Octave）和 `PartSounding/NominalKey`
- 调号通过 `ModelUtils.transposeKey()` 进行移调
- 每轨单独存储移调映射 `_transposeKeySignaturePerTrack`

---

## 四、辅助文件格式

### 1. BinaryStylesheet（`BinaryStylesheet.ts`）

```
文件结构：
  int32 (大端)  | 键值对数量
  KeyValuePair[] | 每条记录：1字节key长度 + UTF8 key + 1字节类型 + 值
```

支持 7 种数据类型：
| 类型码 | 类型 | 存储方式 |
|--------|------|----------|
| 0 | Boolean | 1 字节（0=false） |
| 1 | Integer | 4 字节大端 int32 |
| 2 | Float | 4 字节大端 IEEE float32 |
| 3 | String | int16 长度 + UTF8 内容 |
| 4 | Point | int32 x + int32 y |
| 5 | Size | int32 width + int32 height |
| 6 | Rectangle | int32 x/y/width/height |
| 7 | Color | 4 字节 RGBA |

用于存储显示样式：隐藏力度、括号扩展模式、音轨名显示策略、页眉/页脚格式等。

### 2. PartConfiguration（`PartConfiguration.ts`）

```
文件结构：
  int32 (大端) | ScoreView 数量
  ScoreView[]  | 每个包含：MultiRest(bool) + TrackViewGroup[]
  int32        | 当前活跃视图索引
```

TrackViewGroup 位标志：
| 位 | 含义 |
|----|------|
| bit0 | showStandardNotation（五线谱） |
| bit1 | showTablature（TAB谱） |
| bit2 | showSlash（斜线谱） |
| bit3 | showNumbered（简谱，GP8功能） |
| 全0 | 默认启用五线谱 |

---

## 五、与 GP6/GPX 的区别

GP6 使用 `.gpx` 格式，文件结构完全不同：

- GPX 使用 **BCFS/BCFZ 压缩文件系统**（`GpxFileSystem.ts`）
- BCFS = 未压缩，BCFZ = 使用 LZ-like 算法压缩
- 文件系统按 0x1000 字节（4KB）扇区组织
- `GpxImporter` 使用 `GpxFileSystem` 解包后，也是调用 `GpifParser` 解析 `score.gpif`
- **GP7/GP8 改用 ZIP 容器**，简化了文件系统层，但核心 `score.gpif` XML 格式与 GPX 保持一致

---

## 六、整体架构图

```
┌─────────────────────────────────────────────────┐
│                  ScoreLoader                      │
│  (遍历所有 Importer 尝试解析)                       │
└────────────────────┬────────────────────────────┘
                     │
    ┌────────────────┼────────────────────┐
    │                │                    │
    ▼                ▼                    ▼
Gp3To5Importer  Gp7To8Importer     GpxImporter
                (ZIP 容器)          (BCFS/BCFZ)
                     │                    │
                     ▼                    ▼
               ┌─────────────┐    ┌──────────────┐
               │ GpifParser  │◄───│ GpxFileSystem│
               │ (XML→Model) │    └──────────────┘
               └──────┬──────┘
                      │
    ┌─────────────────┼──────────────────┐
    │                 │                  │
    ▼                 ▼                  ▼
BinaryStylesheet  PartConfiguration  LayoutConfiguration
(显示样式)         (谱表视图)          (布局)
```

---

## 七、解析中的重要节拍/音符属性映射

### Beat 属性映射（`_parseBeat`）

| GPIF XML 元素 | 映射到 Beat 属性 | 说明 |
|--------------|-----------------|------|
| `Fadding` | `.fade` | 淡入/FadeOut/VolumeSwell |
| `Tremolo` | `.tremoloPicking` | 1/2=1线, 1/4=2线, 1/8=3线 |
| `Hairpin` | `.crescendo` | Crescendo/Decrescendo |
| `Arpeggio` | `.brushType` | ArpeggioUp/ArpeggioDown |
| `Dynamic` | `.dynamics` | PPP~FFF 全部力度 |
| `Whammy` | `.addWhammyBarPoint()` | 原点+中两点+终点 |
| `Timer` | `.showTimer/.timer` | 显示计时器值 |
| `Lyrics` | `.lyrics` | 逐拍歌词（会禁用全局歌词应用） |

### Note 属性映射（`_parseNote`）

| GPIF XML 元素 | 映射到 Note 属性 | 说明 |
|--------------|-----------------|------|
| `Accent` | `.isStaccato/.accentuated` | 位标志：1=Staccato, 4=Heavy, 8=Normal, 16=Tenuto |
| `Tie` | `.isTieDestination` | 连音目标 |
| `Vibrato` | `.vibrato` | Slight/Wide |
| `Trill` | `.trillValue/.trillSpeed` | 颤音音程+速度（固定Sixteenth） |
| `LeftFingering` / `RightFingering` | `.leftHandFinger/.rightHandFinger` | P/I/M/A/C 对应各手指 |
| `LetRing` | `.isLetRing` | 延音标记 |
| `Slide` | `.slideInType/.slideOutType` | 位标志映射 7 种滑音类型 |
| `HarmonicType` | `.harmonicType/.harmonicValue` | 6 种泛音类型+泛音品位 |
| `Bend` | `.addBendPoint()` | 原点+中两点+终点（与 Whammy 结构相同） |