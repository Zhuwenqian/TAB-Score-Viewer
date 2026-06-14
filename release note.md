# TAB Score Viewer v2.0.4 Release Note

**Version**: v2.0.4
**Release Date**: 2026-06-14
**Author**: Zhu Wenqian

---

## Overview

TAB Score Viewer v2.0.4 is a **major version iteration following v1.0.0**, with **9 intermediate versions** of continuous development. Building upon all core features from v1.0.0, this release adds **complete GTP guitar tablature rendering engine, audio playback, dark/light theme system, internationalization support, application icon & EXE packaging**, and fixes **30+ bugs**.

This update (**2026-06-14**) focuses on **UI professionalization and code quality improvement**:
- **SVG Icon System**: Replace emoji icons with Lucide-style SVG icons for professional UI standards
- **Translation Completeness Fix**: Resolve 30 missing translation keys causing Terminal warnings
- **Bilingual Comments**: Convert all code comments to English-Chinese bilingual format for international collaboration
- **Documentation Optimization**: Reorganize README.md with English version first (international best practice)
- **SoundFont Path Correction**: Adjust packaged executable path to `_internal/soundfont/` for PyInstaller onedir mode
- **Play Button Style Fix**: Resolve button style mutation issue when clicking play/pause

---

## Version Evolution

| Version | Date | Milestone |
|---------|------|-----------|
| v1.0.0 | 2026-06-06 | Initial official release (Image/PDF viewer + auto-scroll + annotation system) |
| v1.1.0 | — | GTP file complete parsing & rendering engine |
| v1.1.1 | — | Multi-track switching support |
| v1.2.x | — | Advanced technique symbol rendering (slide/bend curves, etc.) |
| v1.3.0 | — | GTP audio playback (MIDI -> FluidSynth) |
| v1.8.1 | 2026-06-12 | GTP code library extraction (ApolloTab standalone library) |
| v1.8.2 | 2026-06-12 | Library rename: gtp_engine -> ApolloTab + License MIT -> MPL-2.0 |
| v1.9.0 | 2026-06-12 | Internationalization (i18n) - Chinese/English bilingual support |
| v1.9.1 | 2026-06-12 | Application icon + PyInstaller EXE packaging config |
| **v2.0.0** | **2026-06-13** | **Dark/Light theme system + UI beautification** |
| **v2.0.1** | **2026-06-14** | **SVG icons + Translation fix + Bilingual comments + Documentation optimization + Bug fixes** |

---

## New Features (since v1.0.0)

### 1. GTP Guitar Tab Complete Rendering Engine (v1.1.0)

Based on the standalone library **ApolloTab** (formerly `gtp_engine`) for complete Guitar Pro file parsing and rendering:

| Capability | Description |
|------------|-------------|
| Supported Formats | GP3, GP4, GP5, GPX |
| Parsing Engine | PyGuitarPro (pyguitarpro >= 0.11) |
| Rendering Output | Tablature images (QPainter drawing) |
| Data Model | GTPSong -> GTrack -> GMeasure -> GBeat -> GNote (18 playing techniques) |

**Architecture Design**:
```
.gp file -> PyGuitarPro -> raw Song object -> GTPParser conversion
    -> GTPSong(intermediate model) -> TabRenderer.render() -> TabLayoutEngine.layout()
    -> QPainter drawing -> QPixmap[] (multi-page images)
```

### 2. Multi-Track Switching (v1.1.1)

- Dropdown menu to select and view different guitar tracks
- Display tuning information per track
- Per-track independent annotation storage (`filename.t{track_num}.anno.json`)
- Auto-load corresponding track annotations on switch (memory cache `_annotations_by_track`)

### 3. Advanced Technique Symbol Rendering (v1.2.x)

Visual rendering support for **18 playing technique symbols**:
- Slide, Bend, Hammer-On/Pull-Off
- Harmonic, Vibrato, Palm Mute
- Tapping, Dead Note, etc.

### 4. GTP Audio Playback (v1.3.0)

- MIDI -> FluidSynth real-time audio synthesis playback
- Playback cursor: vertical line follows playback progress with current measure highlight
- Resume playback from paused position (not restart from beginning)

### 5. ApolloTab Standalone Code Library (v1.8.1)

- Full decoupling: all GTP code migrated to `ApolloTab/` standalone directory
- Unified API: `GTPPlayer` provides `load/play/stop/seek/timeline/audio`
- Code cleanup: ~200 lines of redundant inline code removed from main program

### 6. Internationalization Support i18n (v1.9.0)

- **I18n singleton translation manager**: JSON translation files + signal notification
- Supported languages: Simplified Chinese (`zh_CN`) / English (`en_US`)
- Language selector dropdown in Settings window
- Full coverage: main window / settings window / dialogs / progress bar / all UI text
- Translation file path: `locales/{lang_code}.json`

### 7. Application Icon & EXE Packaging (v1.9.1)

- **Application icon**: `icon.ico` multi-size icon (window icon + taskbar icon unified)
- **PyInstaller packaging**: `guitar_tab_viewer.spec` onedir mode packaging config
- Auto-adapt development mode / packaged mode (via `sys.frozen` detection)

### 8. Dark/Light Theme System (v2.0.0) ⭐ Major Update

- **ThemeManager**: Singleton pattern + QObject + pyqtSignal observer notification
- **Runtime real-time switching**: No app restart required, global UI instant refresh
- **Two carefully crafted color schemes**:
  - `THEME_DARK`: Dark theme (default, inherited from v1.0.0)
  - `THEME_LIGHT`: Brand new light theme color palette
- **GTP rendering sync**: UI theme auto-syncs to ApolloTab rendering theme
  - Light UI -> GTP uses light rendering theme
  - Dark UI -> GTP uses dark rendering theme
  - Export GTP tabs -> force light theme (print-friendly)
- **Custom component full adaptation**: ModernButton / ModernSlider / ProgressBarSlider all dynamically fetch colors from ThemeManager
- **Theme persistence**: `settings.json` `theme` field, auto-restore last selection on startup

**Technical Notes**:
> - pyqtSignal must be defined as a **class attribute** within a **QObject subclass** (PyQt5 compliance)
> - Design patterns: Singleton + Observer (pyqtSignal)

### 9. Right-Click Open File Location

- File list right-click context menu supports "Reveal in File Explorer"

### 10. A4 Size Export Optimization (v2.0.0)

- PNG/PDF export uses `QPainter.setClipRect()` **absolute clipping**, completely eliminating cross-page overflow
- Margin optimization: reduced from 2% to 0.5%, image spacing from 5px to 3px
- Reserved 30px page number area, no content overlap

### 11. SVG Icon System (v2.0.1) ⭐ UI Professionalization

**Design Principle**: Following ui-ux-pro-max professional UI standards, replace emoji characters with vector SVG icons for better accessibility, scalability, and theme compatibility.

**Implementation Details**:

| Component | Description |
|-----------|-------------|
| `load_icon()` function | Load SVG icons from `icons/` directory as QIcon objects |
| Path adaptation | Compatible with development mode and PyInstaller onedir mode (`_internal/` subdirectory) |
| ModernButton enhancement | Support optional `icon_name` parameter, auto-load and display icon (16x16px, left of text) |
| Icon library | 13 Lucide-style SVG icons created |

**Icon Library** (13 icons):

| Icon File | Usage | Visual Description |
|-----------|-------|-------------------|
| `annotate.svg` | Annotation button | Pencil/edit icon |
| `export.svg` | Export button | Download arrow icon |
| `play.svg` | Play button | Play triangle icon |
| `stop.svg` | Stop button | Stop square icon |
| `volume.svg` | Audio on | Speaker icon |
| `volume-off.svg` | Audio off | Muted speaker icon |
| `chart.svg` | Speed curve | Trending line icon |
| `folder.svg` | Folder select | Folder icon |
| `search.svg` | Search box | Magnifying glass icon |
| `flag-a.svg` | Loop point A | Flag marker A |
| `flag-b.svg` | Loop point B | Flag marker B |
| `trash.svg` | Clear/delete | Trash bin icon |
| `x-close.svg` | Close/clear | X mark icon |

**Technical Flow**:
```
User clicks button → ModernButton.__init__(icon_name='play')
    ↓
load_icon('play') called
    ↓
Detect runtime mode:
  ├─ Dev mode → _APP_BASE_DIR/icons/play.svg
  └─ Packaged mode → exe_dir/_internal/icons/play.svg
    ↓
QIcon(svg_path) loads SVG file
    ↓
Qt rendering engine converts SVG to pixel icon (16x16)
    ↓
setIcon() displays on button
```

### 12. Bilingual Code Comments (v2.0.1)

**Purpose**: Improve code readability for international developers and team collaboration.

**Format Standard**:
```python
"""
English description / 中文描述
Principle: Technical explanation / 原理: 技术说明
"""
```

**Coverage**: File header docstring, function documentation, class definitions, key logic comments

### 13. Documentation Internationalization (v2.0.1)

**README.md Reorganization**:
- **English version moved to front** (international best practice)
- Complete English documentation added: Features / Quick Start / Shortcuts / Mouse Operations / Project Structure / Tech Stack
- Updated project structure diagram: Added `icons/` directory, SoundFont path marked as `_internal/soundfont`
- New sections: SVG icon system description, packaging configuration details
- Maintained bilingual navigation links

---

## Bug Fixes (v2.0.1 Focus + Historical Accumulation)

### v2.0.1 - Complete Bug Fix Summary (2026-06-14 Update)

#### 1. Play Button Style Mutation Issue ⭐ Critical UI Fix

| Aspect | Detail |
|--------|--------|
| **Issue** | Clicking play button causes style mutation: rounded shadow button becomes flat color block |
| **Root Cause** | `start_playback()`/`stop_playback()` directly call `setStyleSheet("background-color:#F59E0B;")` → Qt stylesheet is replaced entirely (not merged) → loses border-radius, font, shadow, hover effects, icon spacing |
| **Impact** | Button loses: 8px border-radius, Microsoft YaHei 12px font, QGraphicsDropShadowEffect, hover/pressed/disabled states, icon 16x16 with custom padding |

**Fix Solution**:

1. **New method**: `ModernButton.set_color(color_key)` ([TAB Score Viewer.py#L1045-L1054](TAB%20Score%20Viewer.py))
   ```python
   def set_color(self, color_key: str) -> None:
       """Dynamically change button theme color while preserving all UI properties"""
       self.color_key = color_key
       self.refresh_theme()  # Rebuild complete CSS (keep radius/font/shadow/icon)
   ```

2. **Replace direct style calls**:
   - ❌ Old: `self.play_btn.setStyleSheet(f"background-color:{ThemeManager.get('warning')};")`
   - ✅ New: `self.play_btn.set_color('warning')` → Orange (#F59E0B) for pause state
   - ✅ New: `self.play_btn.set_color('success')` → Green (#10B981) for play state

**Technical Principle**: Qt stylesheets use **complete replacement** not merging. Must rebuild full CSS string to preserve all properties.

**Test Cases** (7 scenarios):

| Case | Operation | Expected Result |
|------|-----------|-----------------|
| 1 | Initial state | Play button: green(success) + rounded + shadow + play icon △ |
| 2 | Click "Play" | Button turns orange(warning), **keeps round/shadow/font/icon**, text changes to "Pause" |
| 3 | Hover pause button | Background darkens (hover effect works), no style flicker |
| 4 | Click "Pause" again | Button returns green(success), text changes to "Play", style intact |
| 5 | Click "Stop" | Play button green + stop button gray(disabled) |
| 6 | Switch dark→light theme | Button auto-adapts light theme, shadow color changes |
| 7 | Rapid click play/pause | No style residue, complete refresh each toggle |

---

#### 2. Translation Key Completeness Fix (Terminal#29-45 Warnings)

| Aspect | Detail |
|--------|--------|
| **Issue** | Startup outputs 30 warnings: `"Missing translation key: settings_window.*"` |
| **Affected Files** | `locales/zh_CN.json`, `locales/en_US.json` |
| **Root Cause** | Settings window UI added new text keys but translation files not updated |

**30 Missing Keys Added**:

| Category | Keys |
|----------|------|
| **UI Text** | `loading_init`, `folder_not_selected`, `folder_btn`, `language_label`, `theme_label` |
| **File List** | `file_list_label`, `search_label`, `search_placeholder`, `search_clear` |
| **Language Switch** | `language_switch_title`, `language_switch_msg` |
| **Folder Ops** | `folder_dialog_title`, `loading_files`, `parent_dir`, `empty_folder` |
| **Error Handling** | `dir_unavailable_title/msg`, `permission_denied_title/msg` |
| **Navigation** | `loading_entering` |
| **Context Menu** | `context_play_all`, `context_enter_folder`, `context_open_location`, `context_view_file`, `context_play_image`, `context_play_all_images` |
| **Feedback** | `locate_fail_title/msg`, `open_fail_title/msg` |

**Result**: ✅ Zero warnings on startup, all UI text properly translated

---

#### 3. SoundFont Path Correction for Packaged Executable

| Aspect | Detail |
|--------|--------|
| **Issue** | SoundFont file not found in PyInstaller onedir packaged executable |
| **Correct Path** | `dist/TAB Score Viewer/_internal/soundfont/FluidR3_GM.sf2` |
| **Root Cause** | PyInstaller onedir mode places data files in `_internal/` subdirectory, not exe root |

**Fix Implementation**:

1. **Code modification** ([TAB Score Viewer.py#L3352-L3364](TAB%20Score%20Viewer.py)):
   ```python
   if getattr(sys, 'frozen', False):
       # PyInstaller onedir: data files in _internal/ subdirectory
       app_base = os.path.join(os.path.dirname(sys.executable), '_internal')
   else:
       app_base = _APP_BASE_DIR
   sf_dir = os.path.join(app_base, 'soundfont')
   ```

2. **Spec file update** (`TAB Score Viewer.spec` datas list):
   - Added: `icons/` directory → packaged to `_internal/icons/`
   - Added: `soundfont/` directory → packaged to `_internal/soundfont/`

**Compatibility**: Works regardless of CWD when launching program

---

### v2.0.1 - GTP Click-to-Seek Precise Positioning (4 Iteration Fixes)

| # | Issue | Fix |
|---|-------|-----|
| 1 | Entire click handler skipped when `total_scroll_distance=0` | Removed pre-condition check |
| 2 | `height/2` center offset -> clicking top rows truncates position to 0 | Adjusted offset strategy |
| 3 | `height*0.25` offset -> large position causes click-top to jump forward ("jumps too far") | Further reduced offset |
| 4 | Fixed 80px / dynamic max(10, y*0.14) -> still has deviation | **Final solution: completely remove offset (offset=0)** |

**Root Cause Analysis**: `click_abs_y = position + y`, any non-zero offset causes unexpected jumping

**Final Fix Solution**:
- **Zero-offset strategy**: `offset = 0`, `new_position = click_abs_y = position + event.y()`
- **Playback startup decoupling**: `toggle_playback()` moved from inner condition to outer layer, ensuring click always triggers/resumes playback
- **Behavior**: Click any row -> that row moves to screen top -> seek to corresponding time -> start playback, no extra jumping

**10 Case Validation** (pos=3000, offset=0):

| Case | Scenario | Expected Result |
|------|----------|-----------------|
| 1 | Click top y=30 | new_pos=3030 (+30px/~1 row), seek+play |
| 2 | Click upper y=100 | new_pos=3100 (+100px), seek+play |
| 3 | Click middle y=400 | new_pos=3400 (+400px), seek+play |
| 4 | Click bottom y=770 | new_pos=3770 (+770px), seek+play |
| 5 | position=0, click top | new_pos=30, seek start, start playback |
| 6 | Short tab (total_dist=0) | Skip position block, but still start playback |
| 7 | Already playing, click | Continue playback (no restart) |
| 8 | Click annotation area | Enter drag mode (unaffected) |
| 9 | Image/PDF mode | Same behavior (shared mousePressEvent) |
| 10 | Right-click | Not triggered (unaffected) |

### v2.0.0 Historical Fixes

| # | Issue | Fix |
|---|-------|-----|
| 1 | GTP mode pause-resume returns to beginning | Added `_paused_time_ms` var + `stop_playback(reset_position)` param |
| 2 | LoadContentWorker method missing | Added `_create_error_image()` method |
| 3 | GTPPlayer.set_theme compatibility | Added `hasattr()` check for legacy compatibility |
| 4 | ThemeManager pyqtSignal spec error | Changed to QObject subclass + class attribute signal definition |
| 5 | Export cross-page overflow | setClipRect() absolute clipping (v4 iteration) |
| 6 | GTPPlayer.is_loaded property missing | Added @property in ApolloTab/player.py |
| 7 | Export force light theme omission | Current track export path also creates renderer + set_theme('light') |
| 8 | Toolbar GTP theme button redundant | Removed (fully follows UI theme auto-sync) |

### v1.8.2 Historical Fixes (5 issues)

| # | Issue | Fix |
|---|-------|-----|
| 1 | Syntax error | Corrected Python syntax |
| 2 | ImportError | Fixed import paths |
| 3 | AttributeError | Completed attribute definitions |
| 4 | Progress bar not showing | Fixed progress bar rendering logic |
| 5 | Library name full replacement | `gtp_engine` -> `ApolloTab` dir/import/config/docs |

---

## Changelog

### v2.0.1 (2026-06-14) - UI Professionalization & Code Quality

| File | Action | Description |
|------|--------|-------------|
| `TAB Score Viewer.py` | **Modified** | Added `load_icon()` SVG loader, `ModernButton.set_color()`, bilingual comments, SoundFont `_internal/` path, play/pause style fix |
| `icons/` | **New Directory** | 13 Lucide-style SVG icons (annotate/export/play/stop/volume/chart/folder/search/flag-a/flag-b/trash/x-close/volume-off) |
| `locales/zh_CN.json` | **Modified** | Added 30 missing `settings_window.*` translation keys |
| `locales/en_US.json` | **Modified** | Added 30 missing `settings_window.*` translation keys (English) |
| `TAB Score Viewer.spec` | **Modified** | Added `icons/` and `soundfont/` to datas list for packaging |
| `README.md` | **Reorganized** | English version moved to front, updated project structure, added SVG icon docs |
| `readme/功能更新.md` | **Updated** | Complete v2.0.1 changelog with all bug fixes and features |

### Historical Changelog (v1.0.0 - v2.0.0)

| File | Action | Description |
|------|--------|-------------|
| `ApolloTab/player.py` | Added/Modified | is_loaded property + set_theme() proxy method |
| `ApolloTab/` | New Directory | GTP standalone rendering engine library (parser/renderer/layout engine/data model) |
| `locales/zh_CN.json` | New | Chinese translation file |
| `locales/en_US.json` | New | English translation file |
| `icon.ico` | New | Multi-size application icon |
| `guitar_tab_viewer.spec` | New | PyInstaller packaging config |
| `config/settings.json` | Modified | Added theme/language fields |
| `readme/开发文档.md` | Updated | Architecture/module/class docs synced |
| `readme/实施文档.md` | Updated | Deployment docs synced |

---

## Technical Architecture Overview

```
+--------------------------------------------------+
|               SettingsWindow (Main Window)         |
|  +----------+ +------------+ +------------------+  |
|  | File List| | Toolbar    | | Bottom Progress   |  |
|  | (SVG Icons)│ | (SVG Icons) | | Bar w/ Page Input |  |
|  +----------+ +------------+ | Bar w/ Page Input |  |
|                             +------------------+  |
|  +-----------------------------------------------+ |
|  |           DisplayWindow (Tab Window)            | |
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

**Design Patterns Applied**:

| Pattern | Application |
|---------|-------------|
| MVC Separation | SettingsWindow(View/Control) + DisplayWidget(View) + dataclass(Model) |
| Observer Pattern | PyQt5 signals/slots / ThemeManager.theme_changed / I18n language switch |
| Singleton Pattern | ThemeManager / I18n |
| Factory Pattern | Worker classes for unified async task encapsulation |
| Command Pattern | Undo/Redo snapshot stack |
| **Facade Pattern** | `load_icon()` - Unified icon loading interface (dev/packaged mode) |
| **Strategy Pattern** | `ModernButton.set_color()` - Dynamic theme color switching |

**Key Technical Components (v2.0.1 New)**:

| Component | Type | Purpose |
|-----------|------|---------|
| `load_icon()` | Function | SVG icon loader with path adaptation (dev vs `_internal/`) |
| `ModernButton.set_color()` | Method | Dynamic color switching preserving full stylesheet |
| `_build_style_with_icon()` | Method | CSS generator for icon buttons (padding/spacing adjustment) |
| Path Adapter | Logic | `sys.frozen` detection for PyInstaller onedir mode compatibility |

---

## Roadmap (Future Versions)

### Completed in v2.0.1 ✅
- [x] SVG icon system (replace emoji with professional Lucide-style icons)
- [x] Translation key completeness fix (30 missing keys resolved)
- [x] Bilingual code comments (English-Chinese format)
- [x] Documentation internationalization (README.md English first)
- [x] SoundFont path correction for PyInstaller packaging
- [x] Play button style mutation fix

### Planned for Future Versions
- [ ] Annotation import/export feature enhancement
- [ ] Recently opened files list
- [ ] Fullscreen mode
- [ ] More playing technique symbol extensions
- [ ] Plugin system
- [ ] Cross-platform compatibility enhancement

---

## Version Statistics

| Metric | Value |
|--------|-------|
| **Total Versions** | 11 (v1.0.0 → v2.0.4) |
| **Development Duration** | 8 days (2026-06-06 → 2026-06-14) |
| **Lines of Code** | ~5400+ (main program) |
| **Bug Fixes** | 35+ issues resolved |
| **Design Patterns Used** | 7 (MVC, Observer, Singleton, Factory, Command, Facade, Strategy) |
| **Supported Languages** | 2 (Chinese Simplified, English) |
| **SVG Icons** | 13 (Lucide-style) |
| **Translation Keys** | 150+ (complete UI coverage) |

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

**Document Version**: v2.0.4 Release Note
**Last Updated**: 2026-06-14
**Author**: Zhu Wenqian (14-year-old developer from China)
**AI Assistance**: GLM-5V-Turbo (code assistance, human-led architecture decisions)