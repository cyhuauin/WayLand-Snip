"""单实例管理 — 确保只有一个 gnome-snip 运行"""
import os
import sys
import signal
import socket
import json

SOCKET_PATH = "/tmp/gnome-snip.sock"


class SingleInstance:
    """通过 Unix Socket 实现单实例"""

    def __init__(self):
        self._server = None
        self._callback = None

    def try_start(self, callback):
        """
        尝试启动。如果已有实例运行，通知它截图并返回 False。
        如果没有实例，启动服务器并返回 True。
        callback: 收到通知时调用的函数
        """
        self._callback = callback

        # 尝试连接已有实例
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(SOCKET_PATH)
            # 已有实例运行，发送截图命令
            sock.sendall(b"take_screenshot")
            sock.close()
            print("已通知现有实例截图")
            return False
        except (ConnectionRefusedError, FileNotFoundError, OSError):
            pass

        # 没有实例，启动服务器
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass

        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(SOCKET_PATH)
        self._server.listen(1)
        self._server.setblocking(False)

        # 用 GLib IO 监听连接
        import gi
        gi.require_version('GLib', '2.0')
        from gi.repository import GLib

        GLib.io_add_watch(
            self._server, GLib.IO_IN, self._on_connection
        )

        return True

    def _on_connection(self, source, condition):
        try:
            conn, _ = source.accept()
            data = conn.recv(1024)
            conn.close()
            if data == b"take_screenshot" and self._callback:
                self._callback()
        except Exception:
            pass
        return True

    def cleanup(self):
        """清理锁文件"""
        try:
            if self._server:
                self._server.close()
            os.unlink(SOCKET_PATH)
        except Exception:
            pass
