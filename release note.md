# TAB Score Viewer v2.0.1 Release Note

**Version**: v2.0.1
**Release Date**: 2026-06-13
**Author**: Zhu Wenqian

---

## Overview

TAB Score Viewer v2.0.1 is a **major version iteration following v1.0.0**, with **9 intermediate versions** of continuous development. Building upon all core features from v1.0.0, this release adds **complete GTP guitar tablature rendering engine, audio playback, dark/light theme system, internationalization support, application icon & EXE packaging**, and fixes **30+ bugs**.

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
| **v2.0.1** | **2026-06-13** | **Bug fix: GTP mode click-to-seek precise positioning** |

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

---

## Bug Fixes (v2.0.1 Focus + Historical Accumulation)

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

| File | Action | Description |
|------|--------|-------------|
| `TAB Score Viewer.py` | Refactored | Theme manager + I18n + performance optimization + all new features integrated |
| `ApolloTab/player.py` | Added/Modified | is_loaded property + set_theme() proxy method |
| `ApolloTab/` | New Directory | GTP standalone rendering engine library (parser/renderer/layout engine/data model) |
| `locales/zh_CN.json` | New | Chinese translation file |
| `locales/en_US.json` | New | English translation file |
| `icon.ico` | New | Multi-size application icon |
| `guitar_tab_viewer.spec` | New | PyInstaller packaging config |
| `config/settings.json` | Modified | Added theme/language fields |
| `readme/功能更新.md` | Updated | Full version update log |
| `readme/开发文档.md` | Updated | Architecture/module/class docs synced |
| `readme/实施文档.md` | Updated | Deployment docs synced |

---

## Technical Architecture Overview

```
+--------------------------------------------------+
|               SettingsWindow (Main Window)         |
|  +----------+ +------------+ +------------------+  |
|  | File List| | Toolbar    | | Bottom Progress   |  |
|  +----------+ +------------+ | Bar w/ Page Input |  |
|                             +------------------+  |
|  +-----------------------------------------------+ |
|  |           DisplayWindow (Tab Window)            | |
|  |  +--------------+  +------------------------+  | |
|  |  | DisplayWidget|  | Control Panel            |  | |
|  |  | (Canvas Render)| | Play/Speed/Loop/Track   |  | |
|  |  +--------------+  +------------------------+  | |
|  +-----------------------------------------------+ |
+--------------------------------------------------+
+--------------------------------------------------+
|  ThemeManager (Singleton) <--> I18n (Singleton)   |
|  |-> theme_changed signal     |-> language_changed |
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

---

## Roadmap (Future Versions)

- [ ] Annotation import/export feature enhancement
- [ ] Recently opened files list
- [ ] Fullscreen mode
- [ ] More playing technique symbol extensions
- [ ] Plugin system
- [ ] Cross-platform compatibility