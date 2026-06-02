"""设置管理"""
import os
import json

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "gnome-snip")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
AUTOSTART_DIR = os.path.join(os.path.expanduser("~"), ".config", "autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "gnome-snip.desktop")

DEFAULTS = {
    "auto_copy": True,
    "auto_pin": True,
    "save_dir": "/tmp/gnome-snip",
    "max_pins": 20,
    "max_saved_files": 20,       # 最大保存截图数
    "initial_scale": 0.6,
    "default_tool": "move",
    "default_color": [1, 0, 0],
    "default_line_width": 3,
    "hotkey": "F1",
    "autostart": False,
}


class Settings:
    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    saved = json.load(f)
                self._data.update(saved)
        except Exception:
            pass

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        val = self._data.get(key)
        return val if val is not None else default

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value


# ─── 开机启动管理 ───

def set_autostart(enabled):
    """设置开机启动"""
    if enabled:
        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        desktop = f"""[Desktop Entry]
Type=Application
Name=gnome-snip
Comment=GNOME Wayland 截图工具
Exec=/usr/local/bin/gnome-snip
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
"""
        with open(AUTOSTART_FILE, "w") as f:
            f.write(desktop)
    else:
        try:
            os.remove(AUTOSTART_FILE)
        except FileNotFoundError:
            pass


def is_autostart_enabled():
    """检查开机启动是否启用"""
    return os.path.exists(AUTOSTART_FILE)


# ─── 快捷键管理（通过 GNOME 自定义快捷键）──

BINDING_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/gnome-snip/"
BINDINGS_LIST = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"


def set_hotkey(hotkey_str):
    """设置截图快捷键（GNOME 级别）"""
    import subprocess

    # 转换快捷键格式: "F1" -> "'F1'", "Ctrl+Shift+A" -> "'<Primary><Shift>a'"
    gnome_key = _to_gnome_hotkey(hotkey_str)

    # 写入快捷键配置
    subprocess.run(["dconf", "write", f"{BINDING_PATH}name", "'GNOME Snip'"],
                   capture_output=True)
    subprocess.run(["dconf", "write", f"{BINDING_PATH}command",
                    "'/usr/local/bin/gnome-snip'"],
                   capture_output=True)
    subprocess.run(["dconf", "write", f"{BINDING_PATH}binding", f"'{gnome_key}'"],
                   capture_output=True)

    # 确保在列表中
    result = subprocess.run(["dconf", "read", BINDINGS_LIST],
                           capture_output=True, text=True)
    current = result.stdout.strip()
    if "gnome-snip" not in current:
        if not current or current == "[]":
            new = f"['{BINDING_PATH}']"
        else:
            new = current.rstrip("]") + f", '{BINDING_PATH}']"
        subprocess.run(["dconf", "write", BINDINGS_LIST, new],
                       capture_output=True)


def remove_hotkey():
    """移除截图快捷键"""
    import subprocess
    subprocess.run(["dconf", "reset", "-f", BINDING_PATH], capture_output=True)
    # 从列表中移除
    result = subprocess.run(["dconf", "read", BINDINGS_LIST],
                           capture_output=True, text=True)
    current = result.stdout.strip()
    if "gnome-snip" in current:
        # 移除 gnome-snip 条目
        parts = [p.strip().strip("'") for p in current.strip("[]").split(",")]
        parts = [p for p in parts if "gnome-snip" not in p]
        if parts:
            new = "['" + "', '".join(parts) + "']"
        else:
            new = "[]"
        subprocess.run(["dconf", "write", BINDINGS_LIST, new],
                       capture_output=True)


def get_current_hotkey():
    """获取当前快捷键（显示用）"""
    import subprocess
    result = subprocess.run(
        ["dconf", "read", f"{BINDING_PATH}binding"],
        capture_output=True, text=True
    )
    raw = result.stdout.strip().strip("'")
    if not raw:
        return "F1"
    return _from_gnome_hotkey(raw)


def _to_gnome_hotkey(key_str):
    """'Ctrl+Shift+A' -> '<Primary><Shift>a'"""
    key = key_str
    key = key.replace("Ctrl+", "<Primary>")
    key = key.replace("Alt+", "<Alt>")
    key = key.replace("Shift+", "<Shift>")
    key = key.replace("Super+", "<Super>")
    return key


def _from_gnome_hotkey(gnome_key):
    """'<Primary><Shift>a' -> 'Ctrl+Shift+A'"""
    key = gnome_key
    key = key.replace("<Primary>", "Ctrl+")
    key = key.replace("<Alt>", "Alt+")
    key = key.replace("<Shift>", "Shift+")
    key = key.replace("<Super>", "Super+")
    return key
