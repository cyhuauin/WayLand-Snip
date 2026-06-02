"""主应用"""
import os
import sys
import shutil
import signal

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

from .portal import ScreenshotPortal, check_portal
from .pinwin import PinWin
from .settings import Settings, CONFIG_DIR
from .prefs import PrefsDialog
from .single import SingleInstance


class App:
    def __init__(self):
        self.settings = Settings()
        self.portal = ScreenshotPortal()
        self.pins = []
        self._main_win = None
        self._tray = None
        self._single = SingleInstance()

    def run(self):
        """启动应用"""
        # 单实例检查：如果已有实例运行，通知它截图并退出
        if not self._single.try_start(self.take_screenshot):
            sys.exit(0)

        # 检查 portal
        if not check_portal():
            print("portal 不可用，请安装: sudo apt install xdg-desktop-portal-gnome",
                  file=sys.stderr)
            sys.exit(1)

        # 创建主窗口（隐藏，仅用于快捷键）
        self._main_win = Gtk.Window(title="gnome-snip")
        self._main_win.set_default_size(300, 100)
        self._main_win.set_border_width(15)
        self._main_win.connect("destroy", self._on_main_destroy)
        self._main_win.connect("key-press-event", self._on_key)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_valign(Gtk.Align.CENTER)
        lbl = Gtk.Label()
        lbl.set_markup(
            '<b>gnome-snip</b>\n\n'
            '<b>F1</b> 截图+贴屏\n'
            '<b>Esc</b> 关闭所有贴图\n\n'
            '底部工具栏: 画笔/矩形/箭头/文字\n'
            '滚轮缩放 · 拖拽移动\n\n'
            '右键托盘图标可访问设置'
        )
        lbl.set_justify(Gtk.Justification.CENTER)
        box.add(lbl)
        self._main_win.add(box)

        # 设置托盘
        try:
            from .tray import TrayIcon
            self._tray = TrayIcon(self)
        except Exception as e:
            print(f"托盘初始化失败: {e}")

        # 注册全局快捷键
        self._register_hotkey()

        self._main_win.show_all()
        self._main_win.hide()  # 隐藏主窗口，只留托盘

        Gtk.main()

    def _register_hotkey(self):
        """通过 GNOME 自定义快捷键注册 F1"""
        pass  # 由 install.sh 设置

    def take_screenshot(self):
        """截屏"""
        save_dir = self.settings.get("save_dir", "/tmp/gnome-snip")
        os.makedirs(save_dir, exist_ok=True)
        self.portal.capture(self._on_screenshot_done)

    def _on_screenshot_done(self, path, err):
        if err:
            print(f"截图错误: {err}", file=sys.stderr)
            return
        if not path:
            return

        save_dir = self.settings.get("save_dir", "/tmp/gnome-snip")
        os.makedirs(save_dir, exist_ok=True)
        d = os.path.join(save_dir, f"snip_{os.getpid()}_{GLib.get_monotonic_time()}.png")
        shutil.copy2(path, d)

        # 清理超出数量的旧截图
        self._cleanup_old_files(save_dir)

        # 自动复制到剪贴板
        if self.settings.get("auto_copy", True):
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file(d)
                cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                cb.set_image(pb)
                cb.store()
            except Exception:
                pass

        # 自动贴屏
        if self.settings.get("auto_pin", True):
            self._pin(d)

        print(f"✓ {d}")

    def _pin(self, image_path):
        """创建贴图窗口"""
        try:
            max_pins = self.settings.get("max_pins", 20)
            while len(self.pins) >= max_pins:
                old = self.pins.pop(0)
                old.close()
            w = PinWin(image_path, self.settings,
                       on_close=lambda w: self.pins.remove(w) if w in self.pins else None)
            self.pins.append(w)
        except Exception as e:
            print(f"贴图创建失败: {e}", file=sys.stderr)

    def show_prefs(self):
        """显示设置对话框"""
        dlg = PrefsDialog(self.settings, self._main_win)
        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            dlg.get_settings()
        dlg.destroy()

    def close_all_pins(self):
        """关闭所有贴图"""
        for w in list(self.pins):
            w.close()
        self.pins.clear()

    def _cleanup_old_files(self, save_dir):
        """清理超出数量的旧截图"""
        try:
            max_files = self.settings.get("max_saved_files", 20)
            files = sorted(
                [os.path.join(save_dir, f) for f in os.listdir(save_dir)
                 if f.endswith(".png")],
                key=os.path.getmtime, reverse=True
            )
            for f in files[max_files:]:
                try:
                    os.remove(f)
                except OSError:
                    pass
        except Exception:
            pass

    def quit(self):
        """退出应用"""
        self.close_all_pins()
        self._single.cleanup()
        Gtk.main_quit()

    def restart(self):
        """重新启动"""
        self.close_all_pins()
        self._single.cleanup()
        Gtk.main_quit()
        # 重新启动
        import subprocess
        subprocess.Popen([sys.executable, sys.argv[0]])

    def show_help(self):
        """显示帮助"""
        dlg = Gtk.MessageDialog(
            parent=self._main_win,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="gnome-snip 使用帮助"
        )
        dlg.format_secondary_text(
            "快捷键：\n"
            "  F1 — 截图并贴屏\n"
            "  Esc — 关闭所有贴图\n\n"
            "贴图操作：\n"
            "  滚轮 — 缩放\n"
            "  拖拽 — 移动（↔模式或直接拖图片）\n\n"
            "底部工具栏：\n"
            "  ↔ 移动  ✏ 画笔  □ 矩形\n"
            "  → 箭头  ╱ 直线  T 文字\n"
            "  ↩ 撤销  ⌫ 清除  复制  ❌ 关闭\n\n"
            "右键托盘图标可访问设置和退出。\n"
            "配置文件：~/.config/gnome-snip/settings.json"
        )
        dlg.run()
        dlg.destroy()

    def show_about(self):
        """显示关于"""
        dlg = Gtk.AboutDialog()
        dlg.set_transient_for(self._main_win)
        dlg.set_program_name("wayland-snip")
        dlg.set_version("1.0.0")
        dlg.set_comments("GNOME Wayland 原生截图 + 贴图 + 标注工具")
        dlg.set_copyright("© 2026")
        dlg.set_license_type(Gtk.License.MIT_X11)
        dlg.set_website("https://github.com/cyhuauin/WayLand-Snip")
        dlg.set_website_label("GitHub 仓库")
        dlg.set_authors(["Peek"])
        icon_path = "/usr/local/bin/gnome-snip-icon.png"
        if os.path.exists(icon_path):
            dlg.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, 64, 64, True))
        dlg.run()
        dlg.destroy()

    def _on_main_destroy(self, w):
        self.quit()

    def _on_key(self, w, e):
        k = Gdk.keyval_name(e.keyval)
        if k == 'F1':
            self.take_screenshot()
            return True
        if k == 'Escape':
            self.close_all_pins()
            return True
        return False
