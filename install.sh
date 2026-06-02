#!/bin/bash
# gnome-snip 安装脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/local/bin"
PKG_DIR="/usr/local/lib/python3.13/dist-packages/gnome_snip"

echo "=== gnome-snip 安装 ==="

# 检查依赖
echo "检查依赖..."
command -v python3 >/dev/null 2>&1 || { echo "缺少 python3"; exit 1; }

python3 -c "import gi; gi.require_version('Gtk','3.0')" 2>/dev/null || {
    echo "安装 GTK3..."
    sudo apt install -y python3-gi gir1.2-gtk-3.0
}

python3 -c "import cairo" 2>/dev/null || {
    echo "安装 PyCairo..."
    sudo apt install -y python3-cairo
}

dpkg -l 2>/dev/null | grep -q xdg-desktop-portal-gnome || {
    echo "安装 xdg-desktop-portal-gnome..."
    sudo apt install -y xdg-desktop-portal-gnome
}

python3 -c "import gi; gi.require_version('AppIndicator3','0.1')" 2>/dev/null || {
    echo "安装 AppIndicator3..."
    sudo apt install -y gir1.2-appindicator3-0.1 2>/dev/null || true
}

# 安装程序
echo "安装 gnome-snip..."
sudo mkdir -p "$PKG_DIR"
sudo cp "$SCRIPT_DIR/gnome_snip/"*.py "$PKG_DIR/"
sudo cp -r "$SCRIPT_DIR/icons" "$PKG_DIR/../gnome_snip_icons" 2>/dev/null || true
sudo mkdir -p /usr/local/lib/python3.13/dist-packages/gnome_snip_icons
sudo cp "$SCRIPT_DIR/icons/"*.svg /usr/local/lib/python3.13/dist-packages/gnome_snip_icons/
sudo cp "$SCRIPT_DIR/gnome-snip" "$INSTALL_DIR/gnome-snip"
sudo cp "$SCRIPT_DIR/icon.png" "$INSTALL_DIR/gnome-snip-icon.png" 2>/dev/null || true
sudo chmod +x "$INSTALL_DIR/gnome-snip"
echo "✓ 已安装到 $INSTALL_DIR/gnome-snip"

# 安装 .desktop 文件（出现在 Ubuntu 应用列表中）
echo "注册应用..."
sudo cp "$SCRIPT_DIR/gnome-snip.desktop" /usr/share/applications/gnome-snip.desktop
sudo chmod +x /usr/share/applications/gnome-snip.desktop
echo "✓ 已添加到应用列表"

echo ""
echo "安装完成！"
echo "  应用列表: 在 Ubuntu 中搜索 gnome-snip"
echo "  命令行: gnome-snip"
echo "  托盘: 右键托盘图标访问设置和截图"
