# -*- mode: python ; coding: utf-8 -*-
"""
============================================================
文件名: guitar_tab_viewer.spec
功能描述: PyInstaller 非单文件打包配置(TAB Score Viewer)
         打包模式: onedir(目录模式，非单文件exe)
         图标: 根目录下的 icon.ico

         原理: 使用PyInstaller将Python应用打包为Windows可执行程序
           - onedir模式: 生成一个文件夹，内含exe和所有依赖(推荐，启动快)
           - 数据文件(locales/翻译、DLL音频库)会被自动复制到输出目录
           - icon.ico同时作为exe文件图标和运行时窗口/任务栏图标

使用方法:
  1. 安装pyinstaller: pip install pyinstaller
  2. 执行打包:   pyinstaller "TAB Score Viewer.spec"
  3. 输出目录: dist/TAB Score Viewer//
  4. 运行程序: dist/TAB Score Viewer/TAB Score Viewer.exe

创建日期: 2026-06-12
最后修改: 2026-06-12 (v1.9.1)
============================================================
"""

import os
import sys

# 项目根目录(本spec文件所在目录)
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))

block_cipher = None

# ===== 数据文件配置 =====
# 原理: PyInstaller会将这些文件/目录复制到打包输出目录中
# 运行时通过 sys.executable 所在目录定位(见 get_app_icon() 函数)
datas = [
    # 翻译文件目录 -> 打包后保留在 locales/
    (os.path.join(SPEC_DIR, 'locales'), 'locales'),
    # FluidSynth 音频合成DLL库(音频播放功能依赖)
    (os.path.join(SPEC_DIR, 'libfluidsynth-3.dll'), '.'),
    (os.path.join(SPEC_DIR, 'SDL3.dll'), '.'),
    (os.path.join(SPEC_DIR, 'sndfile.dll'), '.'),
    # SoundFont 音色库文件(GTP音频播放依赖，约140MB)
    (os.path.join(SPEC_DIR, 'soundfont'), 'soundfont'),
    # 应用图标
    (os.path.join(SPEC_DIR, 'icon.ico'), '.'),
]

# ===== 隐藏导入配置 =====
# 原理: PyInstaller静态分析可能遗漏的动态导入模块，手动声明确保打包完整
hiddenimports = [
    # ApolloTab GTP引擎库(动态导入)
    'ApolloTab',
    'ApolloTab.parser',
    'ApolloTab.renderer',
    'ApolloTab.audio',
    'ApolloTab.models',
    'ApolloTab.utils',
    # 第三方依赖
    'guitarpro',
    'pyfluidsynth',
]

a = Analysis(
    [os.path.join(SPEC_DIR, 'TAB Score Viewer.py')],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型模块以减小包体积
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'tkinter', 'IPython', 'jupyter',
        'pytest', 'black', 'isort', 'mypy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TAB Score Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # 启用UPX压缩(减小体积，需安装UPX)
    console=False,     # 不显示控制台窗口(GUI应用)
    icon=os.path.join(SPEC_DIR, 'icon.ico'),  # exe文件图标
    version=None,      # 可选: 添加版本信息文件(version resource)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TAB Score Viewer',  # 输出目录名: dist/TAB Score Viewer/
)
