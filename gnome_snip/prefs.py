"""设置界面"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .settings import (
    set_autostart, is_autostart_enabled,
    set_hotkey, remove_hotkey, get_current_hotkey
)


class PrefsDialog(Gtk.Dialog):
    """偏好设置对话框"""

    def __init__(self, settings, parent=None):
        super().__init__(
            title="gnome-snip 设置",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self.settings = settings
        self.add_buttons("保存", Gtk.ResponseType.OK, "取消", Gtk.ResponseType.CANCEL)
        self.set_default_size(420, 450)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)

        # ── 快捷键 ──
        frame0 = Gtk.Frame(label="快捷键")
        grid0 = Gtk.Grid()
        grid0.set_column_spacing(10)
        grid0.set_row_spacing(8)
        grid0.set_border_width(8)

        lbl = Gtk.Label(label="截图快捷键：")
        lbl.set_halign(Gtk.Align.START)
        grid0.attach(lbl, 0, 0, 1, 1)

        self.hotkey_entry = Gtk.Entry()
        self.hotkey_entry.set_text(get_current_hotkey())
        self.hotkey_entry.set_tooltip_text("例如: F1, Ctrl+Shift+A, Alt+Q")
        self.hotkey_entry.set_hexpand(True)
        grid0.attach(self.hotkey_entry, 1, 0, 1, 1)

        lbl_note = Gtk.Label(label="(GNOME 级别全局快捷键)")
        lbl_note.set_opacity(0.5)
        lbl_note.set_halign(Gtk.Align.START)
        grid0.attach(lbl_note, 1, 1, 1, 1)

        frame0.add(grid0)
        box.pack_start(frame0, False, False, 0)

        # ── 截图行为 ──
        frame1 = Gtk.Frame(label="截图行为")
        grid1 = Gtk.Grid()
        grid1.set_column_spacing(10)
        grid1.set_row_spacing(8)
        grid1.set_border_width(8)

        self.auto_copy = Gtk.CheckButton(label="截图后自动复制到剪贴板")
        self.auto_copy.set_active(settings.get("auto_copy", True))
        grid1.attach(self.auto_copy, 0, 0, 2, 1)

        self.auto_pin = Gtk.CheckButton(label="截图后自动贴屏")
        self.auto_pin.set_active(settings.get("auto_pin", True))
        grid1.attach(self.auto_pin, 0, 1, 2, 1)

        lbl2 = Gtk.Label(label="保存目录：")
        lbl2.set_halign(Gtk.Align.START)
        grid1.attach(lbl2, 0, 2, 1, 1)
        self.save_dir = Gtk.Entry()
        self.save_dir.set_text(settings.get("save_dir", "/tmp/gnome-snip"))
        self.save_dir.set_hexpand(True)
        grid1.attach(self.save_dir, 1, 2, 1, 1)

        lbl3 = Gtk.Label(label="最大贴图数：")
        lbl3.set_halign(Gtk.Align.START)
        grid1.attach(lbl3, 0, 3, 1, 1)
        self.max_pins = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.max_pins.set_value(settings.get("max_pins", 20))
        grid1.attach(self.max_pins, 1, 3, 1, 1)

        lbl4 = Gtk.Label(label="最大保存截图数：")
        lbl4.set_halign(Gtk.Align.START)
        grid1.attach(lbl4, 0, 4, 1, 1)
        self.max_saved = Gtk.SpinButton.new_with_range(5, 500, 5)
        self.max_saved.set_value(settings.get("max_saved_files", 20))
        grid1.attach(self.max_saved, 1, 4, 1, 1)
        lbl4_note = Gtk.Label(label="(超过自动覆盖最早的)")
        lbl4_note.set_opacity(0.5)
        lbl4_note.set_halign(Gtk.Align.START)
        grid1.attach(lbl4_note, 1, 5, 1, 1)

        frame1.add(grid1)
        box.pack_start(frame1, False, False, 0)

        # ── 标注默认值 ──
        frame2 = Gtk.Frame(label="标注默认值")
        grid2 = Gtk.Grid()
        grid2.set_column_spacing(10)
        grid2.set_row_spacing(8)
        grid2.set_border_width(8)

        lbl4 = Gtk.Label(label="初始缩放：")
        lbl4.set_halign(Gtk.Align.START)
        grid2.attach(lbl4, 0, 0, 1, 1)
        self.init_scale = Gtk.SpinButton.new_with_range(0.2, 1.0, 0.05)
        self.init_scale.set_value(settings.get("initial_scale", 0.6))
        self.init_scale.set_digits(2)
        grid2.attach(self.init_scale, 1, 0, 1, 1)

        lbl5 = Gtk.Label(label="默认线宽：")
        lbl5.set_halign(Gtk.Align.START)
        grid2.attach(lbl5, 0, 1, 1, 1)
        self.line_width = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.line_width.set_value(settings.get("default_line_width", 3))
        grid2.attach(self.line_width, 1, 1, 1, 1)

        lbl6 = Gtk.Label(label="默认工具：")
        lbl6.set_halign(Gtk.Align.START)
        grid2.attach(lbl6, 0, 2, 1, 1)
        tools = ["move", "pen", "rect", "arrow", "line", "text"]
        self.default_tool = Gtk.ComboBoxText()
        for t in tools:
            self.default_tool.append_text(t)
        self.default_tool.set_active_id(settings.get("default_tool", "move"))
        grid2.attach(self.default_tool, 1, 2, 1, 1)

        frame2.add(grid2)
        box.pack_start(frame2, False, False, 0)

        # ── 系统 ──
        frame3 = Gtk.Frame(label="系统")
        grid3 = Gtk.Grid()
        grid3.set_column_spacing(10)
        grid3.set_row_spacing(8)
        grid3.set_border_width(8)

        self.autostart = Gtk.CheckButton(label="开机自动启动")
        self.autostart.set_active(is_autostart_enabled())
        grid3.attach(self.autostart, 0, 0, 2, 1)

        frame3.add(grid3)
        box.pack_start(frame3, False, False, 0)

        self.show_all()

    def get_settings(self):
        """返回更新后的设置"""
        self.settings.set("auto_copy", self.auto_copy.get_active())
        self.settings.set("auto_pin", self.auto_pin.get_active())
        self.settings.set("save_dir", self.save_dir.get_text())
        self.settings.set("max_pins", int(self.max_pins.get_value()))
        self.settings.set("max_saved_files", int(self.max_saved.get_value()))
        self.settings.set("initial_scale", self.init_scale.get_value())
        self.settings.set("default_line_width", int(self.line_width.get_value()))
        self.settings.set("default_tool", self.default_tool.get_active_id())

        # 快捷键
        hotkey = self.hotkey_entry.get_text().strip()
        if hotkey:
            self.settings.set("hotkey", hotkey)
            set_hotkey(hotkey)

        # 开机启动
        autostart = self.autostart.get_active()
        self.settings.set("autostart", autostart)
        set_autostart(autostart)

        return self.settings
