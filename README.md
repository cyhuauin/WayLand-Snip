# wayland-snip

GNOME Wayland 原生截图 + 贴图 + 标注工具。

基于 xdg-desktop-portal 调用 GNOME 原生截图 API，高分屏无偏移，支持多屏。

## ✨ 功能

- 📸 **截图** — 调用 GNOME 原生截图 UI（xdg-desktop-portal），支持区域/窗口/全屏
- 📌 **贴图** — 截图自动贴在屏幕上，可拖拽移动、滚轮缩放
- ✏️ **标注** — 画笔、矩形、箭头、直线、文字
- 🎨 **颜色** — 8 种预设颜色 + 自定义调色盘
- 📏 **线粗** — 5 档线宽可选
- 📋 **剪贴板** — 截图自动复制到剪贴板，含标注复制
- 🖥️ **系统托盘** — 最小化到托盘，右键菜单操作
- ⚙️ **设置** — 可配置快捷键、截图行为、标注默认值、开机启动
- 🔄 **多次截图** — 一个实例内可多次截图，不会重复启动
- 🚀 **单实例** — 自动检测已有实例，避免重复运行

## 📦 依赖

- Python 3.8+
- GTK 3 + PyCairo
- xdg-desktop-portal + xdg-desktop-portal-gnome
- AppIndicator3（托盘支持，可选）

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-cairo gir1.2-gtk-3.0 \
    xdg-desktop-portal-gnome gir1.2-appindicator3-0.1
```

## 🚀 安装

### 从源码安装

```bash
git clone https://github.com/yourname/wayland-snip.git
cd wayland-snip
sudo ./install.sh
```

### 手动安装

```bash
# 复制程序
sudo cp gnome-snip /usr/local/bin/gnome-snip
sudo cp -r gnome_snip /usr/local/lib/python3.13/dist-packages/gnome_snip
sudo chmod +x /usr/local/bin/gnome-snip

# 复制图标
sudo cp icon.png /usr/local/bin/gnome-snip-icon.png

# 注册应用（出现在 Ubuntu 应用列表中）
sudo cp gnome-snip.desktop /usr/share/applications/
```

## 📖 使用

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| F1 | 截图并贴屏（可在设置中自定义） |
| Esc | 关闭所有贴图 |

### 底部工具栏

| 按钮 | 功能 |
|------|------|
| ↔ | 移动模式（拖拽移动窗口） |
| ✏ | 画笔（自由绘制） |
| □ | 矩形标注 |
| → | 箭头标注 |
| ╱ | 直线标注 |
| T | 文字标注 |
| 🎨 | 颜色选择（预设 + 自定义） |
| · ─ ━ ▬ ■ | 线粗选择 |
| ↩ | 撤销上一步 |
| ⌫ | 清除所有标注 |
| −/+ | 缩放 |
| 📋 | 复制到剪贴板（含标注） |
| ✕ | 关闭贴图 |

### 贴图操作

- **滚轮** — 缩放贴图
- **拖拽** — 移动贴图（↔ 模式下直接拖拽图片区域）
- **单击 ✕** — 关闭贴图

### 托盘菜单

- 📸 截图 — 触发截图
- ⚙ 设置 — 打开设置界面
- ❓ 帮助 — 使用说明
- 🔄 重新启动 — 重启程序
- 🚪 退出 — 关闭程序

## ⚙️ 设置

右键托盘图标 → 设置，可配置：

### 快捷键
- 自定义截图快捷键（GNOME 级别全局快捷键）

### 截图行为
- 截图后自动复制到剪贴板
- 截图后自动贴屏
- 保存目录
- 最大贴图数

### 标注默认值
- 初始缩放比例
- 默认线宽
- 默认工具

### 系统
- 开机自动启动

配置文件：`~/.config/gnome-snip/settings.json`

## 🏗️ 项目结构

```
wayland-snip/
├── gnome-snip              # 入口脚本
├── install.sh              # 安装脚本
├── gnome-snip.desktop      # 桌面文件（Ubuntu 应用列表）
├── icon.png                # 托盘图标
├── README.md               # 说明文档
├── LICENSE                 # 开源协议
└── gnome_snip/
    ├── __init__.py         # 版本信息
    ├── app.py              # 主应用（托盘、快捷键、截图调度）
    ├── portal.py           # xdg-desktop-portal 截图接口
    ├── pinwin.py           # 贴图窗口（标注、缩放、拖拽）
    ├── settings.py         # 设置管理 + 快捷键/开机启动
    ├── prefs.py            # 设置界面
    ├── tray.py             # 系统托盘图标
    └── single.py           # 单实例管理（Unix Socket）
```


## 🐛 限制

- Wayland 下窗口置顶取决于合成器（GNOME Mutter 支持）
- 不支持撤销单步标注（只能逐步撤销或全部清除）
- 文字标注弹出对话框，可能影响流畅度
- 部分 Wayland 合成器可能不支持 always-on-top

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request
