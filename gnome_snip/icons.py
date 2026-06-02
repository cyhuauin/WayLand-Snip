"""图标加载工具"""
import os
import cairo
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Rsvg', '2.0')
from gi.repository import Gtk, GdkPixbuf

# 多个图标路径
ICON_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "icons"),
    os.path.join(os.path.dirname(__file__), "..", "..", "gnome_snip_icons"),
    "/usr/local/lib/python3.13/dist-packages/gnome_snip_icons",
]


def _find_icon(name):
    """查找图标文件"""
    for base in ICON_PATHS:
        path = os.path.join(base, f"{name}.svg")
        if os.path.exists(path):
            return path
    return None


def load_icon(name, size=16):
    """加载 SVG 图标为 GdkPixbuf"""
    path = _find_icon(name)
    if not path:
        return None
    try:
        # 尝试用 rsvg 加载 SVG
        import rsvg
        handle = rsvg.Handle(file=path)
        w, h = handle.get_dimension_data()[:2]
        scale = size / max(w, h)
        pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)
        pb.fill(0x00000000)
        # 用 cairo 渲染
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        ctx = cairo.Context(surface)
        ctx.scale(scale, scale)
        handle.render_cairo(ctx)
        surface.flush()
        # 转为 pixbuf
        result = Gdk.pixbuf_get_from_surface(surface, 0, 0, size, size)
        return result
    except Exception:
        pass

    # 回退：用 Gtk.Image 从文件加载
    try:
        img = Gtk.Image.new_from_file(path)
        pb = img.get_pixbuf()
        if pb:
            return pb.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
    except Exception:
        pass

    return None


def load_icon_as_image(name, size=16):
    """加载 SVG 图标为 Gtk.Image"""
    pb = load_icon(name, size)
    if pb:
        return Gtk.Image.new_from_pixbuf(pb)
    return None
