#!/bin/bash
# -*- coding: utf-8 -*-
"""
============================================================
文件名: build_deb.sh
功能描述: 将 PyInstaller 打包结果打包为 .deb 安装包
         包含启动脚本、桌面快捷方式、PATH 环境变量配置

使用方法:
  1. 先执行 PyInstaller 打包: pyinstaller "TAB Score Viewer_linux.spec"
  2. 执行本脚本: chmod +x build_deb.sh && ./build_deb.sh
  3. 输出: tab-score-viewer_<version>_<arch>.deb

安装后使用:
  - 命令行: tabsv (全局可用)
  - 桌面: 应用菜单中搜索 "TAB Score Viewer"
  - 直接运行: /opt/tab-score-viewer/tabsv

依赖:
  - dpkg-deb (系统自带)
  - 可选: fakeroot (避免需要 root 权限)

创建日期: 2026-06-19
最后修改: 2026-06-19
============================================================
"""

set -e  # 遇到错误立即退出

# ===== 配置参数 =====
APP_NAME="tab-score-viewer"                    # 包名(小写+连字符)
APP_VERSION="2.0.7"                             # 版本号
APP_DISPLAY_NAME="TAB Score Viewer"             # 显示名称
APP_EXECUTABLE="TAB Score Viewer"               # PyInstaller 生成的可执行文件名
LAUNCHER_COMMAND="tabsv"                        # 启动命令(安装后可直接输入)
PYINSTALLER_DIST="dist/${APP_DISPLAY_NAME}"     # PyInstaller 输出目录

# ===== 自动检测架构 =====
ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")

# ===== 工作目录 =====
BUILD_DIR="build_deb_temp"
PACKAGE_DIR="${BUILD_DIR}/${APP_NAME}"

echo "============================================"
echo "  TAB Score Viewer - DEB 打包工具"
echo "============================================"
echo "版本: ${APP_VERSION}"
echo "架构: ${ARCH}"
echo ""

# ===== 清理旧构建 =====
if [ -d "${BUILD_DIR}" ]; then
    echo "[*] 清理旧的构建目录..."
    rm -rf "${BUILD_DIR}"
fi

# ===== 检查 PyInstaller 输出 =====
if [ ! -d "${PYINSTALLER_DIST}" ]; then
    echo "[错误] 未找到 PyInstaller 打包输出: ${PYINSTALLER_DIST}"
    echo "请先执行: pyinstaller \"TAB Score Viewer_linux.spec\""
    exit 1
fi

echo "[*] 使用 PyInstaller 输出: ${PYINSTALLER_DIST}"

# ===== 创建 DEB 目录结构 =====
# Debian 标准目录布局:
#   /opt/<app_name>       - 应用程序主目录
#   /usr/bin/             - 启动脚本链接(PATH)
#   /usr/share/applications/ - 桌面快捷方式(.desktop)
#   /usr/share/icons/     - 应用图标
#   /usr/share/doc/<pkg>/ - 文档(版权等)
mkdir -p "${PACKAGE_DIR}/DEBIAN"
mkdir -p "${PACKAGE_DIR}/opt/${APP_NAME}"
mkdir -p "${PACKAGE_DIR}/usr/bin"
mkdir -p "${PACKAGE_DIR}/usr/share/applications"
mkdir -p "${PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PACKAGE_DIR}/usr/share/doc/${APP_NAME}"

# ===== 1. 复制应用程序文件 =====
echo "[*] 复制应用程序文件..."
cp -r "${PYINSTALLER_DIST}"/* "${PACKAGE_DIR}/opt/${APP_NAME}/"

# 设置可执行权限
chmod +x "${PACKAGE_DIR}/opt/${APP_NAME}/${APP_EXECUTABLE}"

# ===== 2. 创建启动脚本 =====
# 原理: 创建一个简单的 shell 脚本作为入口点，
#       放在 /usr/bin/ 下自动加入 PATH，用户可直接输入 tabsv 运行
echo "[*] 创建启动脚本: ${LAUNCHER_COMMAND}..."
cat > "${PACKAGE_DIR}/usr/bin/${LAUNCHER_COMMAND}" << LAUNCHER_EOF
#!/bin/bash
# ============================================================
# TAB Score Viewer 启动脚本
# 功能: 定位并启动 TAB Score Viewer 应用程序
# 安装路径: /usr/bin/tabsv (已在 PATH 中)
# ============================================================

# 应用程序安装目录
APP_DIR="/opt/${APP_NAME}"
EXECUTABLE="${APP_DIR}/${APP_EXECUTABLE}"

# 检查可执行文件是否存在
if [ ! -f "\${EXECUTABLE}" ]; then
    echo "错误: 找不到应用程序 \${EXECUTABLE}"
    echo "请重新安装: sudo apt-get install --reinstall ${APP_NAME}"
    exit 1
fi

# 设置库路径(确保能找到 libfluidsynth 等 .so 文件)
export LD_LIBRARY_PATH="\${APP_DIR}:\${APP_DIR}/_internal:\${LD_LIBRARY_PATH}"

# 启动应用程序(传递所有参数)
exec "\${EXECUTABLE}" "\$@"
LAUNCHER_EOF

chmod 755 "${PACKAGE_DIR}/usr/bin/${LAUNCHER_COMMAND}"

# ===== 3. 创建桌面快捷方式 (.desktop) =====
# 原理: FreeDesktop 标准，让应用出现在系统应用菜单中
echo "[*] 创建桌面快捷方式..."
cat > "${PACKAGE_DIR}/usr/share/applications/${APP_NAME}.desktop" << DESKTOP_EOF
[Desktop Entry]
Name=${APP_DISPLAY_NAME}
Comment=Guitar Pro file viewer and player
Exec=${LAUNCHER_COMMAND}
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Player;Music;
StartupWMClass=TABScoreViewer
Keywords=guitar;tab;music;score;gtp;gp;
DESKTOP_EOF

chmod 644 "${PACKAGE_DIR}/usr/share/applications/${APP_NAME}.desktop"

# ===== 4. 复制图标 =====
# 支持 PNG 格式(Linux 桌面标准)
ICON_SRC=""
for icon_path in "icon.png" "icons/icon.png"; do
    if [ -f "\${icon_path}" ]; then
        ICON_SRC="\${icon_path}"
        break
    fi
done

if [ -n "\${ICON_SRC}" ]; then
    echo "[*] 复制应用图标..."
    cp "\${ICON_SRC}" "${PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    chmod 644 "${PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
else
    echo "[警告] 未找到 icon.png，跳过图标复制"
fi

# ===== 5. 创建版权文件 =====
echo "[*] 创建版权信息..."
cat > "${PACKAGE_DIR}/usr/share/doc/${APP_NAME}/copyright" << COPYRIGHT_EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ${APP_DISPLAY_NAME}
Upstream-Contact: Your Name <your@email.com>
Source: https://github.com/your-repo/tab-score-viewer

License: MIT (or your license)

Files: *
License: MIT
 Copyright (c) 2026 Your Name
 .
 This is free software; see the source for copying conditions.
COPYRIGHT_EOF

chmod 644 "${PACKAGE_DIR}/usr/share/doc/${APP_NAME}/copyright"

# ===== 6. 创建 DEBIAN/control 控制文件 =====
# 原理: deb 包的元数据描述，包含依赖关系、版本等信息
echo "[*] 创建控制文件..."
cat > "${PACKAGE_DIR}/DEBIAN/control" << CONTROL_EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libfluidsynth3, libsndfile1, libpulse0, libqt5widgets5, libqt5gui5, libqt5core5a, libc6 (>= 2.14)
Recommends: fluid-soundfont-gm | timgm6mb-fluid-soundfont
Maintainer: Your Name <your@email.com>
Description: Guitar Pro file viewer and player with audio playback
 TAB Score Viewer is a cross-platform application for viewing,
 playing, and exporting Guitar Pro (.gp3/.gp4/.gp5/.gpx) files.
 .
 Features:
  - View multi-track guitar tablature with syntax highlighting
  - Play audio using FluidSynth synthesizer
  - Export to PDF, PNG, JPG formats
  - A/B loop practice mode
  - Multi-language support (Chinese/English)
# 控制文件末尾必须有空行(Debian规范要求)
CONTROL_EOF

chmod 644 "${PACKAGE_DIR}/DEBIAN/control"

# ===== 7. 创建安装后/卸载脚本 =====
# postinst: 安装后执行 - 更新桌面数据库、图标缓存
echo "[*] 创建 postinst 脚本..."
cat > "${PACKAGE_DIR}/DEBIAN/postinst" << POSTINST_EOF
#!/bin/bash
set -e

# 更新桌面数据库(让新安装的应用立即显示在菜单中)
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi

# 更新图标缓存
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi

echo ""
echo "============================================"
echo "  ${APP_DISPLAY_NAME} 安装完成!"
echo "============================================"
echo "  启动命令: ${LAUNCHER_COMMAND}"
echo "  或在应用菜单中搜索 '${APP_DISPLAY_NAME}'"
echo ""
echo "  如需音频播放功能，请确保已安装 SoundFont:"
echo "    sudo apt-get install fluid-soundfont-gm"
echo "============================================"
POSTINST_EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/postinst"

# prerm: 卸载前执行 - 清理缓存
cat > "${PACKAGE_DIR}/DEBIAN/prerm" << PRERM_EOF
#!/bin/bash
set -e

# 清理图标缓存
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi
PRERM_EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/prerm"

# ===== 8. 构建 .deb 包 =====
DEB_FILE="${APP_NAME}_${APP_VERSION}_${ARCH}.deb"
echo ""
echo "[*] 正在构建 ${DEB_FILE}..."

# 使用 fakeroot 如果可用(避免需要 root)
if command -v fakeroot &> /dev/null; then
    fakeroot dpkg-deb --build --root-owner-group "${PACKAGE_DIR}" "${DEB_FILE}"
else
    # 需要 root 权限来设置正确的文件所有权
    sudo chown -R root:root "${PACKAGE_DIR}"
    dpkg-deb --build --root-owner-group "${PACKAGE_DIR}" "${DEB_FILE}"
fi

# ===== 9. 清理临时文件 =====
echo "[*] 清理临时文件..."
rm -rf "${BUILD_DIR}"

# ===== 完成 =====
DEB_SIZE=$(du -h "${DEB_FILE}" | cut -f1)
echo ""
echo "============================================"
echo "  打包完成!"
echo "============================================"
echo "  文件: ${DEB_FILE}"
echo "  大小: ${DEB_SIZE}"
echo ""
echo "  安装命令:"
echo "    sudo dpkg -i ${DEB_FILE}"
echo "    sudo apt-get install -f  (如有依赖问题)"
echo ""
echo "  运行命令:"
echo "    ${LAUNCHER_COMMAND}"
echo "============================================"
