"""系统托盘 — 双方案：AppIndicator3 优先，StatusIcon 兜底"""
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

HAS_APPINDICATOR = False
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    HAS_APPINDICATOR = True
except Exception:
    pass


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self._indicator = None
        self._status_icon = None

        # ── 菜单 ──
        menu = Gtk.Menu()
        menu.set_reserve_toggle_size(False)

        # 截图
        item_snip = Gtk.MenuItem(label="    📸  截图")
        item_snip.connect("activate", lambda _: app.take_screenshot())
        menu.append(item_snip)

        menu.append(Gtk.SeparatorMenuItem())

        # 设置
        item_prefs = Gtk.MenuItem(label="    ⚙  设置")
        item_prefs.connect("activate", lambda _: app.show_prefs())
        menu.append(item_prefs)

        # 帮助
        item_help = Gtk.MenuItem(label="    ❓  帮助")
        item_help.connect("activate", lambda _: app.show_help())
        menu.append(item_help)

        menu.append(Gtk.SeparatorMenuItem())

        # 重新启动
        item_restart = Gtk.MenuItem(label="    🔄  重新启动")
        item_restart.connect("activate", lambda _: app.restart())
        menu.append(item_restart)

        menu.append(Gtk.SeparatorMenuItem())

        # 退出
        item_quit = Gtk.MenuItem(label="    🚪  退出")
        item_quit.connect("activate", lambda _: app.quit())
        menu.append(item_quit)

        menu.show_all()
        self._menu = menu

        # 图标
        self._icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "icon.png"
        )
        if not os.path.exists(self._icon_path):
            self._icon_path = None

        # 方案 1: AppIndicator3
        if HAS_APPINDICATOR:
            try:
                if self._icon_path:
                    self._indicator = AppIndicator3.Indicator.new(
                        "gnome-snip", self._icon_path,
                        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                    )
                else:
                    self._indicator = AppIndicator3.Indicator.new(
                        "gnome-snip", "applets-screenshooter",
                        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                    )
                self._indicator.set_menu(self._menu)
                try:
                    self._indicator.set_tooltip_text("gnome-snip — 截图工具")
                except AttributeError:
                    try:
                        self._indicator.set_tooltip("gnome-snip — 截图工具")
                    except AttributeError:
                        pass
                self._indicator.set_label("Snip", "Snip")
                GLib.idle_add(lambda: (
                    self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE),
                    False
                )[-1])
                return
            except Exception as e:
                print(f"AppIndicator3 失败: {e}")

        # 方案 2: Gtk.StatusIcon
        self._status_icon = Gtk.StatusIcon()
        if self._icon_path:
            self._status_icon.set_from_file(self._icon_path)
        else:
            self._status_icon.set_from_icon_name("applets-screenshooter")
        self._status_icon.set_tooltip_text("gnome-snip — 截图工具")
        self._status_icon.set_title("gnome-snip")
        self._status_icon.connect("popup-menu", self._on_popup)
        self._status_icon.connect("activate", lambda _: app.take_screenshot())
        self._status_icon.set_visible(True)

    def _on_popup(self, icon, button, activate_time):
        self._menu.popup_at_pointer(None)

    def set_tooltip(self, text):
        if self._indicator:
            try:
                self._indicator.set_tooltip_text(text)
            except AttributeError:
                pass
        elif self._status_icon:
            self._status_icon.set_tooltip_text(text)
