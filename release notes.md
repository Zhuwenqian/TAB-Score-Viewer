# TAB Score Viewer Release Notes

**Current Version**: v2.0.7
**Release Date**: 2026-06-15
**Author**: Zhu Wenqian

---

## Table of Contents

- [Version Evolution](#version-evolution)
- [v2.0.7 - Async Export & JPG Format Support](#207---async-export--jpg-format-support)
- [v2.0.6 - Measure-Based Click Navigation & Loop Integration](#v206---measure-based-click-navigation--loop-integration)
- [v2.0.5 - Print & Print Preview Feature](#v205---print--print-preview-feature)
- [v2.0.4 - GTP A/B Loop Architecture Refactoring](#v204---gtp-ab-loop-architecture-refactoring)
- [v2.0.1 - UI Professionalization & Code Quality](#v201---ui-professionalization--code-quality)
- [v2.0.0 - Dark/Light Theme System](#v200---darklight-theme-system)
- [Historical Versions (v1.0.0 - v1.9.1)](#historical-versions-v100--v191)

---

## Version Evolution

| Version | Date | Milestone |
|---------|------|-----------|
| v1.0.0 | 2026-06-06 | Initial release (Image/PDF viewer + auto-scroll + annotation) |
| v1.1.0 | — | GTP file parsing & rendering engine |
| v1.1.1 | — | Multi-track switching support |
| v1.2.x | — | Advanced technique symbol rendering |
| v1.3.0 | — | GTP audio playback (MIDI -> FluidSynth) |
| v1.8.1 | 2026-06-12 | ApolloTab standalone library extraction |
| v1.8.2 | 2026-06-12 | Library rename: gtp_engine -> ApolloTab |
| v1.9.0 | 2026-06-12 | Internationalization (i18n) |
| v1.9.1 | 2026-06-12 | Application icon + PyInstaller packaging |
| **v2.0.0** | **2026-06-13** | **Dark/Light theme system** |
| **v2.0.1** | **2026-06-14** | **SVG icons + Translation fix + Bilingual comments** |
| **v2.0.4** | **2026-06-14** | **GTP A/B loop architecture refactoring** |
| **v2.0.5** | **2026-06-14** | **Print & print preview feature** |
| **v2.0.6** | **2026-06-14** | **Measure-based click navigation & loop integration** |
| **v2.0.7** | **2026-06-15** | **Async export with progress bar + JPG format support** |

---

## v2.0.7 (2026-06-15) - Async Export & JPG Format Support

### Problem Description

Two critical pain points in the export system:

| # | Symptom | Root Cause |
|---|---------|------------|
| 1 | **UI freezes during large file export** | `_export_to_a4()` runs rendering on UI main thread, blocking event loop for 5-10 seconds on 50+ page files |
| 2 | **No JPG format support** | Only PNG and PDF available; users need smaller files for web sharing (WeChat/QQ/forums) |

### Solution: Async Export Architecture + JPG Rendering

#### 1. Async Export System (QRunnable + QThreadPool)

```
Old Flow (v2 synchronous):
  _export_to_a4() → [UI Thread] → render PNG/PDF → UI FREEZES 5-10s

New Flow (v3 async):
  _export_to_a4() → create ExportWorker(QRunnable)
                  → QThreadPool.globalInstance().start(worker)
                  → ExportProgressDialog shows progress
                  → Worker runs in background thread
                  → Signals: progress → finished/error/cancelled → UI updates safely
```

**Key Components:**

| Class | Role |
|-------|------|
| `ExportWorkerSignals(QObject)` | Custom signals: `progress`, `finished`, `error`, `cancelled` |
| `ExportWorker(QRunnable)` | Background thread: collect data → render per-track → emit progress |
| `ExportProgressDialog(QDialog)` | Progress bar + status label + cancel button, auto-close on done/error/cancel |

**Thread Safety**: All cross-thread communication uses Qt's signal-slot mechanism (automatically queued connection across threads).

#### 2. JPG Format Support

| Feature | Detail |
|---------|--------|
| **Format option** | New "JPG Image (Lossy, for sharing)" radio button in ExportDialog |
| **Quality slider** | Range 1-100, default 90 (high quality); only visible when JPG selected |
| **Rendering method** | `_render_to_a4_jpg()` — reuses PNG pipeline with JPEG output |
| **Quality mapping** | User input 1-100 → Qt internal 0-99 (`quality - 1`) |
| **Image format** | Uses `QImage.Format_RGB32` (no alpha channel = smaller file size) |
| **File size** | ~3-5x smaller than PNG at quality 90; suitable for web sharing |

**Recommended Quality Settings:**

| Use Case | Quality | Effect |
|----------|---------|--------|
| High-quality archive | 90 | Near-lossless, slightly smaller than PNG |
| Web sharing (WeChat/QQ/forums) | 80 | Good quality, significantly smaller file |
| Extreme compression (email attachment) | 60 | Acceptable artifacts for minimum size |

### Key Changes

#### New Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `ExportWorkerSignals` | ~15 | Signal container (QObject subclass for pyqtSignal support) |
| `ExportWorker` | ~120 | QRunnable implementation with cancel support |
| `ExportProgressDialog` | ~120 | Modal dialog with progress bar and cancel button |

#### Modified Methods

| Method | Before | After |
|--------|--------|-------|
| `_export_to_a4()` | Synchronous: direct render call → QMessageBox result | Async: create worker → thread pool start → show progress dialog |
| `ExportDialog._setup_ui()` | PNG/PDF format options only | Added JPG option + quality slider (conditional visibility) |
| *New* `_render_to_a4_jpg()` | N/A | Full A4 rendering pipeline with JPEG compression quality parameter |

#### Translation Keys Added (28 new keys)

| Section | Count | Description |
|---------|-------|-------------|
| `export_dialog` | 20 | Format names, track selection, page range, file filters, JPG quality labels/tooltips |
| `export_progress` | 8 | Window title, status messages (collecting/rendering/saving/done/cancelled), button text |

### Test Cases (10 Scenarios)

| Case | Scenario | Expected Result |
|------|----------|-----------------|
| 1 | Single image score + PNG format | Progress dialog appears → completes quickly → success message → PNG file generated |
| 2 | GTP multi-track (4 tracks) + all tracks + PDF | Progress shows "Rendering: track 1/4" ... "4/4" → complete → 1 PDF file |
| 3 | Large file (50 pages GTP) + JPG quality 80 | Real-time progress updates → completes in ~3-5s → JPG file (~1/4 of PNG size) |
| 4 | Click Cancel during export | Status changes to "Export cancelled" → auto-close after 800ms → no/partial output files |
| 5 | JPG quality slider visibility | Hidden when PNG/PDF selected; immediately visible when switching to JPG |
| 6 | JPG quality=60 extreme compression | Very small file but slight text edge aliasing (acceptable) |
| 7 | JPG quality=100 max quality | Slightly smaller than PNG but nearly lossless |
| 8 | Non-GTP file (image/PDF) + JPG export | Normal JPG export, same behavior as PNG except format |
| 9 | Operate UI during export | UI remains responsive (scroll/zoom/play), not blocked |
| 10 | No content + click export button | Direct "cannot export" warning (no progress dialog shown) |

### Modified Files

| File | Action | Description |
|------|--------|-------------|
| `TAB Score Viewer.py` | **Modified** | Added `ExportWorkerSignals`, `ExportWorker`, `ExportProgressDialog`; refactored `_export_to_a4()` to v3 async; added `_render_to_a4_jpg()`; updated `ExportDialog` with JPG option + quality slider |
| `locales/zh_CN.json` | **Modified** | +28 new translation keys (export_dialog + export_progress) |
| `locales/en_US.json` | **Modified** | +28 corresponding English translation keys |
| `readme/功能更新.md` | **Updated** | Complete v2.0.7 changelog |

---

## v2.0.6 (2026-06-14) - Measure-Based Click Navigation & Loop Integration ⭐ Major Enhancement

### Problem Description

Three interconnected issues in the click-to-seek and A/B loop system:

| # | Symptom | Root Cause |
|---|---------|------------|
| 1 | **Click jumps to middle of measure** | Old code used exact pixel positioning, landing anywhere within the clicked measure |
| 2 | **A/B loop breaks when clicking outside loop region** | No boundary check — any click position could jump out of the [A,B] range |
| 3 | **Cross-line measure index collision** | `meas_idx` reset to 0 per System (line), causing different lines' measure-0 to collide |

### Solution: Global Unique Measure ID + Boundary-Aware Navigation

**Core Principle**: Every measure gets a globally unique `global_meas_idx`, and all internal matching uses this ID instead of the local `meas_idx`.

### Key Changes

#### 1. Library: `player.py` — Global Measure Index System

| Component | Before | After |
|-----------|--------|-------|
| `build_timeline()` | `meas_idx = enumerate(system.measures)` (resets per line) | Adds `global_meas_idx` counter (increments across all systems/pages) |
| Timeline entry | `{ 'meas_idx': 0 }` (non-unique) | `{ 'meas_idx': 0, 'global_meas_idx': 5 }` (unique) |
| Empty measures | `continue` (no timeline entry) | Generates placeholder entry (`beat_idx=-1`) |
| Sentinel point | Inherits local meas_idx | Also inherits global_meas_idx |

#### 2. Library: `player.py` — New APIs

| Method/Property | Purpose |
|-----------------|---------|
| `find_measure_at_scroll_pos(scroll_y)` | Binary search scroll_y → returns measure info (global_meas_idx, start_time_ms, start_scroll_y) |
| `loop_time_range` property | Returns `(loop_start_ms, loop_end_ms)` tuple for UI boundary checking |
| `_find_measure_at_time(time_ms)` | Now returns `global_meas_idx` instead of local `meas_idx` |
| `set_loop_region_by_measure()` | Uses `global_meas_idx` as dict key (no more collisions) |

#### 3. Main Program: `TAB Score Viewer.py` — Measure-Based Click Handler

**Old flow**:
```
click → pixel position → seek(exact pixel) → play from arbitrary position
```

**New flow**:
```
click → absolute Y coordinate
  → find_measure_at_scroll_pos() → get target measure's start position
  → Check A/B loop boundary (if active):
      ├─ Outside [loop_start, loop_end] → IGNORE (maintain loop playback)
      └─ Inside range or no loop → seek(measure_start_ms) + play
```

**Boundary tolerance**: ±50ms (prevents edge cases from being misjudged as "outside")

#### 4. Main Program: `TAB Score Viewer.py` — Region Loop Lifecycle Fix

**Problem**: In region loop mode, UI layer `_tick()` called `stop_playback()` when `effective_time >= total_dur`, before library had chance to trigger loop restart.

**Fix**: Skip stop_playback in region mode — let library manage loop lifecycle internally.

### Bug Fixes (5 issues)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `TAB Score Viewer.py` | Region loop stops at song end instead of looping back | Skip `stop_playback()` when `loop_type == 'region'` and `effective_time >= total_dur` |
| 2 | `TAB Score Viewer.py` | Click-to-seek lands at arbitrary pixel position | Refactored to measure-unit alignment via `find_measure_at_scroll_pos()` |
| 3 | `TAB Score Viewer.py` | Click outside A/B region breaks loop | Added boundary check using `loop_time_range`; ignore clicks outside [start, end] |
| 4 | `player.py` | `meas_idx` resets per System → cross-line collisions | Introduced `global_meas_idx` (monotonic counter across all systems/pages) |
| 5 | `player.py` | Empty measures have no timeline entry → large click error | Generate placeholder entries for empty measures (`beat_idx=-1`) |

### Test Cases (10 Scenarios)

| Case | Scenario | Expected Result |
|------|----------|-----------------|
| 1 | GTP mode, no loop: click measure 5 | Jumps to start of measure 5, begins playback |
| 2 | GTP mode, A/B loop [2-8]: click measure 3 (inside) | Jumps to measure 3 start, continues A/B loop |
| 3 | GTP mode, A/B loop [2-8]: click measure 1 (outside) | **Ignored**, console logs "outside loop range", maintains current loop |
| 4 | GTP mode, A/B loop [2-8]: click measure 10 (outside) | Same as Case 3 — ignored |
| 5 | GTP mode, A/B loop active: click boundary measure (±50ms) | Allowed (tolerance prevents false negative) |
| 6 | Image/PDF file: click anywhere | Falls back to original pixel-level jump (no timeline data) |
| 7 | Not playing: click measure | Jumps to target measure AND auto-starts playback |
| 8 | Already playing: click measure | Hot-seek to target measure without interrupting stream |
| 9 | A/B loop not set (region mode but no points) | Normal jump to clicked measure (no constraint) |
| 10 | All-loop mode (full song): click any measure | Unrestricted jump (all-mode has no range constraint) |

### Data Structure Changes

```python
# Timeline entry (v2.0.6):
entry = {
    'time_ms': 1234.5,
    'scroll_y': 5678.9,
    'page_idx': 0,
    'sys_idx': 0,
    'meas_idx': 2,              # Local index (for UI display)
    'global_meas_idx': 7,       # [NEW] Globally unique (for internal matching)
    'beat_idx': 0,
    ...
}

# Empty measure placeholder:
placeholder = {
    ...
    'beat_idx': -1,             # Marker: empty measure (no beats/notes)
    ...
}
```

### Modified Files

| File | Action | Description |
|------|--------|-------------|
| `ApolloTab/player.py` | **Modified** | Added `global_meas_idx` to `build_timeline()`; new methods: `find_measure_at_scroll_pos()`, `loop_time_range`; empty measure placeholder generation; updated `_find_measure_at_time()` and `set_loop_region_by_measure()` to use global IDs |
| `TAB Score Viewer.py` | **Modified** | Refactored `mousePressEvent()` for measure-based navigation; added A/B loop boundary check; fixed region loop lifecycle in `_tick()` |
| `readme/功能更新.md` | **Updated** | Complete v2.0.6 changelog with all bug fixes and features |

---

## v2.0.5 (2026-06-14) - Print & Print Preview Feature

### New Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Direct Print** | Send score directly to printer with A4 paper size |
| 2 | **Print Preview** | Preview window with zoom (50%~400%), page flipping, thumbnails |
| 3 | **Track Selection** (GTP) | Choose specific tracks for printing |
| 4 | **Page Range** | Select page range to print (e.g., "1-3" or "all") |
| 5 | **Forced Light Theme** | GTP tabs always use light theme for print readability |

### Architecture

```
Toolbar Print Button (QToolButton dropdown)
├── Direct Print...     → _print_score() → _render_to_printer() → QPrinter
└── Print Preview...    → _show_print_preview() → PreviewWindow(QDialog)
                         ├── Zoom control (50%-400%)
                         ├── Page navigation (prev/next/input)
                         ├── Thumbnail sidebar
                         └── One-click print button
```

### Modified Files

| File | Change |
|------|--------|
| `TAB Score Viewer.py` | Added `_print_score()`, `_render_to_printer()`, `PrintDialog`, `_show_print_preview()` |
| `icons/printer.svg` | New Lucide-style printer icon |
| `locales/*.json` | 12 new translation keys each |

---

## v2.0.4 (2026-06-14) - GTP A/B Loop Architecture Refactoring ⭐ Major Fix

### Problem Description

GTP mode A/B region loop had **3 critical issues**:

| # | Symptom | Root Cause |
|---|---------|------------|
| 1 | Short loops (<5% of song) stuck/frozen at start position | UI-layer cooldown mechanism caused race condition with audio thread |
| 2 | Loop jumps past B point instead of looping back to A | `current_position=0` → percentage always 0% → measure index always [0-0] |
| 3 | Setting A/B points in non-region mode then switching yields [0-0] | A/B buttons used scroll position instead of audio time |

### Solution: Library-Layer Measure-Based Loop

**Architecture Change**: Moved all loop logic from UI layer down to audio engine library layer.

```
Old Architecture (v2.0.3):                          New Architecture (v2.0.4):
                                           
UI _tick():                                         UI _tick():
  Read audio_time_ms                                  Read audio_time_ms
  ↓                                                  ↓
  Check if in cooldown? ─Yes→ Simulated clock        Calculate position (clean!)
  ↓ No                                              ↓
  Check if past B? ─Yes→ seek+cooldown counter       Display (Done. No loop code)
  ↓ No
  Calculate position
  
Library SynthEngine:                                Library SynthEngine:
  Only plays, no loop control                        _play_loop() for→while loop:
                                                        Iterate events → End? → Check _loop_enabled
                                                        → Yes: Mute→Reset time→Re-iterate
                                                        → All within audio thread, no race condition
```

### Key Changes

#### 1. Library: `synth_engine.py` — Built-in Event-Level Loop

| Feature | Detail |
|---------|--------|
| **Loop trigger** | When event time >= `loop_end_ms`, immediately restart (not wait for song end) |
| **Event skipping** | On restart, auto-skips events before `loop_start_ms` via time comparison |
| **Thread safety** | All operations within same audio thread (no lock contention) |
| **Seek pre-fill** | `seek()` pre-fills `_start_time` under lock to eliminate race condition on first read |

#### 2. Library: `player.py` — Measure-Based API

| Method | Purpose |
|--------|---------|
| `set_loop_region_by_position(start_pct, end_pct)` | Convert %→measure index→ms boundary→set engine loop |
| `clear_loop_region()` | Disable loop, reset engine state |
| `_find_measure_at_time(time_ms)` | Binary search timeline for measure index |
| `_get_measure_start_end(meas_idx)` | Get measure's start/end time in ms |

**Measure alignment rules**: A point → first beat of measure; B point → last beat of measure

#### 3. Main Program: `TAB Score Viewer.py` — Simplified UI (~90 lines net reduction)

| Change | Before | After |
|--------|--------|-------|
| `_tick()` GTP path | ~110 lines with cooldown/simulated clock/safety checks | ~25 lines: read time → calc position → display |
| `_set_ab_point()` | Used `current_position` (scroll pos, =0 when not scrolled) | Uses `audio_time_ms / total_duration_ms` |
| `_on_loop_mode_changed()` | Set loop config only | Sets loop + seeks to A immediately |
| `_on_region_selected()` | Updated UI only | Updates UI + syncs to library if in region mode |
| Variables removed | `_loop_seek_cooldown`, `_loop_seek_target_ms`, `_loop_seek_sim_time`, etc. | All deleted |

### Bug Fixes (6 issues)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `synth_engine.py` | Race condition: `seek()` returns but `_start_time` not yet set | Pre-fill `_start_time` under lock in `seek()` |
| 2 | `synth_engine.py` | Loop only triggered after ALL events played, not at B point | Added mid-playback check: `if target_time_ms >= loop_end_ms: restart` |
| 3 | `player.py` | Sentinel point had hardcoded `meas_idx=0` | Sentinel inherits last real entry's indices |
| 4 | `TAB Score Viewer.py` | `_set_ab_point()` used scroll position (=0) | Changed to use `audio_time_ms / total_duration_ms` |
| 5 | `TAB Score Viewer.py` | Switching to region didn't seek to A | Added immediate `seek(target_ms)` call |
| 6 | `TAB Score Viewer.py` | Progress bar A/B didn't sync to library | Added library sync in region mode |

### Test Cases (10 Scenarios)

| Case | Scenario | Expected Result |
|------|----------|-----------------|
| 1 | Normal loop (measures 10-20, >5%) | Smooth playback, seamless loop back |
| 2 | Short loop (measures 0-2, <1%) | Loops correctly without freezing |
| 3 | Ultra-short loop (single measure) | Repeats that measure, no freeze |
| 4 | Set A/B while playing, switch to region | Immediately jumps to A and loops |
| 5 | Set A/B while paused, switch to region | Seeks to A, starts from A on play |
| 6 | Ctrl/Shift click progress bar for A/B | Correct measure indices set |
| 7 | Click Set A/Set B buttons during playback | Uses audio time for accurate placement |
| 8 | Switch back to "none" mode | Loop stops, full playback resumes |
| 9 | A > B (set B before A) | Auto-swaps positions |
| 10 | Loop during linear mode (non-GTP) | Unaffected, original behavior |

---

## v2.0.1 (2026-06-14) - UI Professionalization & Code Quality

### New Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **SVG Icon System** | Replace emoji icons with Lucide-style SVG icons (13 icons) |
| 2 | **Translation Completeness** | Fixed 30 missing translation keys (zero warnings on startup) |
| 3 | **Bilingual Comments** | English-Chinese bilingual code comments |
| 4 | **Documentation Optimization** | README.md reorganized with English version first |
| 5 | **SoundFont Path Correction** | Adjusted path for PyInstaller onedir mode (`_internal/soundfont/`) |
| 6 | **Play Button Style Fix** | Resolved button style mutation issue |

### Bug Fixes (Complete Summary)

#### Critical: Play Button Style Mutation

| Aspect | Detail |
|--------|--------|
| **Issue** | Clicking play button causes style mutation: rounded shadow button becomes flat color block |
| **Root Cause** | Direct `setStyleSheet()` call replaces entire CSS → loses border-radius, font, shadow, hover effects |
| **Fix** | New method `ModernButton.set_color(color_key)` rebuilds complete CSS while preserving all properties |

#### GTP Click-to-Seek Precise Positioning (4 Iteration Fixes)

| # | Issue | Final Fix |
|---|-------|-----------|
| 1 | Entire click handler skipped when `total_scroll_distance=0` | Removed pre-condition check |
| 2 | `height/2` center offset causes truncation | Iteratively reduced offset |
| 3 | Any non-zero offset causes unexpected jumping | **Final: offset=0 (zero-offset strategy)** |

#### Historical Accumulation (v2.0.0 + v1.8.2)

| # | Issue | Fix |
|---|-------|-----|
| 1 | GTP mode pause-resume returns to beginning | Added `_paused_time_ms` var |
| 2 | LoadContentWorker method missing | Added `_create_error_image()` method |
| 3 | ThemeManager pyqtSignal spec error | Changed to QObject subclass |
| 4 | Export cross-page overflow | `setClipRect()` absolute clipping |
| 5 | GTPPlayer.is_loaded property missing | Added @property |
| 6 | Export force light theme omission | Fixed renderer creation path |
| 7 | Syntax/import/attribute errors (v1.8.2) | Full codebase correction |

### Modified Files

| File | Action | Description |
|------|--------|-------------|
| `TAB Score Viewer.py` | **Modified** | SVG loader, `ModernButton.set_color()`, bilingual comments, SoundFont path, play/pause fix |
| `icons/` | **New Directory** | 13 Lucide-style SVG icons |
| `locales/zh_CN.json` | **Modified** | +30 translation keys |
| `locales/en_US.json` | **Modified** | +30 translation keys |
| `TAB Score Viewer.spec` | **Modified** | Added icons/ and soundfont/ to datas list |
| `README.md` | **Reorganized** | English first, updated structure docs |

---

## v2.0.0 (2026-06-13) - Dark/Light Theme System ⭐ Major Update

### Features

- **ThemeManager**: Singleton pattern + QObject + pyqtSignal observer notification
- **Runtime real-time switching**: No app restart required, global UI instant refresh
- **Two color schemes**: `THEME_DARK` (default) + `THEME_LIGHT` (brand new)
- **GTP rendering sync**: UI theme auto-syncs to ApolloTab rendering theme
- **Custom component adaptation**: ModernButton / ModernSlider / ProgressBarSlider
- **Theme persistence**: `settings.json` auto-restore last selection

### Design Patterns Applied

| Pattern | Application |
|---------|-------------|
| MVC Separation | SelectionWindow(View/Control) + DisplayWidget(View) + dataclass(Model) |
| Observer Pattern | PyQt5 signals/slots / ThemeManager.theme_changed |
| Singleton Pattern | ThemeManager / I18n |
| Factory Pattern | Worker classes for async task encapsulation |
| Command Pattern | Undo/Redo snapshot stack |
| Facade Pattern | `load_icon()` unified icon loading interface |
| Strategy Pattern | `ModernButton.set_color()` dynamic color switching |

---

## Historical Versions (v1.0.0 - v1.9.1)

| Version | Date | Key Features |
|---------|------|--------------|
| v1.0.0 | 2026-06-06 | Initial release: Image/PDF viewer, auto-scroll, annotation system |
| v1.1.0 | — | GTP file parsing & rendering engine (ApolloTab) |
| v1.1.1 | — | Multi-track switching, per-track annotations |
| v1.2.x | — | 18 playing technique symbols (slide/bend/harmonic/etc.) |
| v1.3.0 | — | MIDI -> FluidSynth real-time audio synthesis |
| v1.8.1 | 2026-06-12 | ApolloTab standalone library extraction (~200 lines cleanup) |
| v1.8.2 | 2026-06-12 | Library rename gtp_engine->ApolloTab, License MIT->MPL-2.0 |
| v1.9.0 | 2026-06-12 | Internationalization (zh_CN/en_US), I18n singleton |
| v1.9.1 | 2026-06-12 | Application icon, PyInstaller EXE packaging config |

### Technical Architecture

```
+--------------------------------------------------+
|               SelectionWindow (Main Window)         |
|  +----------+ +------------+ +------------------+  |
|  | File List| | Toolbar    | | Bottom Progress   |  |
|  | (SVG Icons)│ | (SVG Icons) | | Bar w/ Page Input |  |
|  +----------+ +------------+ | Bar w/ Page Input |  |
|                             +------------------+  |
|  +-----------------------------------------------+ |
|  |           DisplayWindow (Tab Window)            |  |
|  |  +--------------+  +------------------------+  | |
|  |  | DisplayWidget|  | Control Panel            |  | |
|  |  | (Canvas Render)| | Play/Pause(set_color)   |  | |
|  |  +--------------+  +------------------------+  | |
|  +-----------------------------------------------+ |
+--------------------------------------------------+
+--------------------------------------------------+
|  ThemeManager (Singleton) <--> I18n (Singleton)   |
|  |-> theme_changed signal     |-> language_changed |
|  load_icon() -> SVG Icons (icons/ directory)       |
|  ApolloTab (GTP Engine)                              |
+--------------------------------------------------+
```

---

## Version Statistics

| Metric | Value |
|--------|-------|
| **Total Versions** | 14 (v1.0.0 → v2.0.7) |
| **Development Duration** | 10 days (2026-06-06 → 2026-06-15) |
| **Lines of Code** | ~6500+ (main program + library) |
| **Bug Fixes** | 40+ issues resolved |
| **Design Patterns Used** | 7 (MVC, Observer, Singleton, Factory, Command, Facade, Strategy) |
| **Supported Languages** | 2 (Chinese Simplified, English) |
| **SVG Icons** | 14 (Lucide-style, +printer) |
| **Translation Keys** | 170+ (complete UI coverage) |

---

## Planned for Future Versions

- [x] Recently opened files list
- [x] Fullscreen mode
- [ ] More playing technique symbol extensions
- [ ] Plugin system

---

**Document Version**: Release Notes v2.0.6
**Last Updated**: 2026-06-14
**Author**: Zhu Wenqian (14-year-old developer from China)
**AI Assistance**: GLM-5V-Turbo (code assistance, human-led architecture decisions)
