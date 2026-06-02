"""xdg-desktop-portal 截图接口"""
import os
import tempfile
from urllib.parse import unquote

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gio, GLib


class ScreenshotPortal:
    """通过 xdg-desktop-portal 调用 GNOME 原生截图"""

    def __init__(self):
        self.conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self._cb = None
        self._tid = None
        self._sid = None

    def capture(self, cb):
        """截屏，结果通过 cb(path, error) 回调"""
        self._cb = cb
        self.conn.call(
            'org.freedesktop.portal.Desktop',
            '/org/freedesktop/portal/desktop',
            'org.freedesktop.portal.Screenshot',
            'Screenshot',
            GLib.Variant('(sa{sv})', ('', {'interactive': GLib.Variant('b', True)})),
            GLib.VariantType('(o)'),
            Gio.DBusCallFlags.NONE, -1, None, self._on_ret, None
        )

    def _on_ret(self, conn, result, _):
        try:
            r = conn.call_finish(result)
            p = r.get_child_value(0).get_string()
            self._sid = conn.signal_subscribe(
                'org.freedesktop.portal.Desktop',
                'org.freedesktop.portal.Request',
                'Response', p, None, 0, self._on_resp, None
            )
            self._tid = GLib.timeout_add_seconds(60, self._timeout)
        except Exception as e:
            self._finish(None, str(e))

    def _on_resp(self, conn, _, _1, _2, _3, params, _4):
        code = params.get_child_value(0).get_uint32()
        if code == 0:
            try:
                v = params.get_child_value(1).lookup_value('uri', GLib.VariantType('s'))
                self._finish(unquote(v.get_string()[7:]), None)
            except Exception:
                self._finish(None, "no uri")
        elif code == 1:
            self._finish(None, None)
        else:
            self._finish(None, f"code={code}")

    def _timeout(self):
        self._finish(None, "timeout")
        return False

    def _finish(self, path, error):
        if self._tid:
            GLib.source_remove(self._tid)
            self._tid = None
        if self._sid:
            self.conn.signal_unsubscribe(self._sid)
            self._sid = None
        cb = self._cb
        self._cb = None
        if cb:
            cb(path, error)


def check_portal():
    """检查 portal 是否可用"""
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call_sync(
            'org.freedesktop.portal.Desktop',
            '/org/freedesktop/portal/desktop',
            'org.freedesktop.DBus.Properties',
            'Get',
            GLib.Variant('(ss)', ('org.freedesktop.portal.Screenshot', 'version')),
            GLib.VariantType('(v)'),
            Gio.DBusCallFlags.NONE, -1, None
        )
        return True
    except Exception:
        return False
