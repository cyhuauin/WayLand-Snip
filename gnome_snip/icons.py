"""图标加载工具"""
import os
import cairo
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Rsvg', '2.0')
from gi.repository import Gtk, GdkPixbuf

ICON_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "icons"),
    os.path.join(os.path.dirname(__file__), "..", "..", "gnome_snip_icons"),
    "/usr/local/lib/python3.13/dist-packages/gnome_snip_icons",
]


def _find_icon(name):
    for base in ICON_PATHS:
        path = os.path.join(base, f"{name}.svg")
        if os.path.exists(path):
            return path
    return None


def load_icon(name, size=16):
    """加载 SVG 图标（2x 超采样渲染）"""
    path = _find_icon(name)
    if not path:
        return None
    try:
        import rsvg
        handle = rsvg.Handle(file=path)
        w, h = handle.get_dimension_data()[:2]
        # 2x 超采样
        render_size = size * 2
        scale = render_size / max(w, h)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, render_size, render_size)
        ctx = cairo.Context(surface)
        ctx.scale(scale, scale)
        handle.render_cairo(ctx)
        surface.flush()
        # 缩小到目标尺寸（高质量）
        pb_full = Gdk.pixbuf_get_from_surface(surface, 0, 0, render_size, render_size)
        if pb_full:
            return pb_full.scale_simple(size, size, GdkPixbuf.InterpType.HYPER)
    except Exception:
        pass

    # 回退
    try:
        img = Gtk.Image.new_from_file(path)
        pb = img.get_pixbuf()
        if pb:
            return pb.scale_simple(size, size, GdkPixbuf.InterpType.HYPER)
    except Exception:
        pass
    return None


def load_icon_as_image(name, size=16):
    pb = load_icon(name, size)
    if pb:
        return Gtk.Image.new_from_pixbuf(pb)
    return None
