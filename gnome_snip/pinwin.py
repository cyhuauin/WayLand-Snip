"""贴图窗口"""
import math
import cairo

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

from .icons import load_icon_as_image

COLORS = [
    (1, 0, 0), (0, .8, 0), (0, .4, 1), (1, .6, 0),
    (1, 1, 0), (1, 0, 1), (0, 0, 0), (1, 1, 1),
]


class PinWin(Gtk.Window):
    """浮动贴图窗口：底部工具栏 + 标注 + 拖拽 + 缩放"""

    def __init__(self, path, settings, on_close=None):
        super().__init__()
        self.on_close = on_close
        self.settings = settings
        self.orig = GdkPixbuf.Pixbuf.new_from_file(path)
        self.scale = 1.0
        self.tool = settings.get("default_tool", "move")
        self.color = tuple(settings.get("default_color", [1, 0, 0]))
        self.lw = settings.get("default_line_width", 3)
        self.anns = []
        self._drawing = False
        self._start = (0, 0)
        self._pen_pts = []

        iw, ih = self.orig.get_width(), self.orig.get_height()
        self._ann_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, iw, ih)
        self._temp_surface = None  # 临时预览 surface

        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)

        # 初始缩放
        mon = (self.get_display().get_primary_monitor()
               or self.get_display().get_monitor_at_point(0, 0))
        g = mon.get_geometry()
        if hasattr(g, 'width'):
            gw, gh = g.width, g.height
        else:
            gw, gh = 1920, 1080
        init_sc = settings.get("initial_scale", 0.6)
        self.scale = min(gw * init_sc / iw, gh * init_sc / ih, 1.0)
        self._disp_w = max(1, int(iw * self.scale))
        self._disp_h = max(1, int(ih * self.scale))

        # 底部工具栏
        bar = self._build_toolbar()

        # 主布局
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # ── DrawingArea：直接渲染图片+标注 ──
        self.darea = Gtk.DrawingArea()
        self.darea.set_size_request(self._disp_w, self._disp_h)
        self.darea.connect("draw", self._on_draw)
        self.darea.connect("button-press-event", self._on_press)
        self.darea.connect("button-release-event", self._on_release)
        self.darea.connect("motion-notify-event", self._on_motion)
        self.darea.connect("scroll-event", self._on_scroll)
        self.darea.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
        )
        vbox.pack_start(self.darea, True, True, 0)

        self.connect("destroy", lambda _: on_close(self) if on_close else None)
        vbox.pack_end(bar, False, False, 0)

        # 居中
        gx = getattr(g, 'x', 0)
        x = gx + (gw - self._disp_w) // 2
        y = (gh - self._disp_h - 40) // 2
        self.move(max(0, x), max(0, y))
        self.show_all()

    def _build_toolbar(self):
        bar = Gtk.Box(spacing=3)
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        bar.set_margin_top(4)
        bar.set_margin_bottom(4)

        # ── 现代化 CSS ──
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .snip-bar {
                background: rgba(250, 250, 250, 0.95);
                border-top: 1px solid rgba(0,0,0,0.1);
                padding: 4px 6px;
            }
            .snip-bar button {
                color: #333;
                font-size: 13px;
                min-width: 26px;
                min-height: 26px;
                padding: 3px 6px;
                border-radius: 6px;
                border: 1px solid transparent;
                background: transparent;
            }
            .snip-bar button:hover {
                background: rgba(0,0,0,0.06);
                border-color: rgba(0,0,0,0.08);
            }
            .snip-bar button:active {
                background: rgba(0,0,0,0.1);
            }
            .tool-active {
                background: rgba(74, 144, 226, 0.15);
                border-color: rgba(74, 144, 226, 0.4);
                color: #4a90e2;
            }
            .color-dot {
                min-width: 16px;
                min-height: 16px;
                padding: 0;
                border-radius: 50%;
                border: 2px solid rgba(255,255,255,0.15);
            }
            .color-dot:hover {
                border-color: rgba(255,255,255,0.4);
            }
            .lw-btn {
                min-width: 24px;
                min-height: 24px;
                font-size: 11px;
                opacity: 0.7;
            }
            .lw-btn:hover {
                opacity: 1;
            }
            .snip-zoom {
                color: #666;
                font-size: 12px;
                min-width: 40px;
            }
            .snip-action {
                color: #2e7d32;
            }
            .snip-close {
                color: #c62828;
            }
            .snip-sep {
                background: rgba(0,0,0,0.1);
                min-width: 1px;
                margin: 4px 3px;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
        )
        bar.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
        )
        bar.get_style_context().add_class("snip-bar")

        def mkbtn(icon_name, tip, cb, css_class=None):
            b = Gtk.Button()
            b.set_tooltip_text(tip)
            b.set_relief(Gtk.ReliefStyle.NONE)
            img = load_icon_as_image(icon_name, 16)
            if img:
                b.set_image(img)
            else:
                # 回退到文字
                b.set_label(icon_name)
            b.connect("clicked", cb)
            if css_class:
                b.get_style_context().add_class(css_class)
            return b

        def sep():
            s = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            s.get_style_context().add_class("snip-sep")
            return s

        # ── 工具按钮 ──
        self._tool_btns = {}
        self._tool_providers = {}
        for icon, tid, tip in [("move", "move", "移动"), ("pen", "pen", "画笔"),
                                 ("rect", "rect", "矩形"), ("arrow", "arrow", "箭头"),
                                 ("line", "line", "直线"), ("text", "text", "文字")]:
            b = mkbtn(icon, tip, lambda _, t=tid: self._settool(t))
            self._tool_btns[tid] = b
            bar.pack_start(b, False, False, 0)
        self._tool_btns[self.tool].get_style_context().add_class("tool-active")
        # 初始高亮
        init_prov = Gtk.CssProvider()
        init_prov.load_from_data(b"button { background: rgba(74,144,226,0.15); border-color: rgba(74,144,226,0.4); color: #4a90e2; }")
        self._tool_btns[self.tool].get_style_context().add_provider(init_prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
        self._tool_providers[self.tool] = init_prov
        bar.pack_start(sep(), False, False, 0)

        # ── 颜色选择（当前颜色按钮 + 点击弹出调色板）──
        self._color_btn = Gtk.Button()
        self._color_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._color_btn.set_tooltip_text("选择颜色")
        self._color_btn.connect("clicked", self._show_color_picker)
        # 去掉所有 padding/border
        btn_css = Gtk.CssProvider()
        btn_css.load_from_data(b".color-btn { padding: 0; border: 0; margin: 0; background: transparent; }")
        self._color_btn.get_style_context().add_provider(btn_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
        self._color_btn.get_style_context().add_class("color-btn")
        self._update_color_btn()
        bar.pack_start(self._color_btn, False, False, 0)

        bar.pack_start(sep(), False, False, 0)

        # ── 线粗 ──
        self._lw_btns = {}
        self._lw_providers = {}
        for lw_val, lw_label in [(1, "·"), (2, "─"), (3, "━"), (5, "▬"), (8, "■")]:
            b = mkbtn(lw_label, f"线宽 {lw_val}", lambda _, v=lw_val: self._setlw(v), "lw-btn")
            self._lw_btns[lw_val] = b
            bar.pack_start(b, False, False, 0)
        # 初始高亮
        self._highlight_lw(self.lw)

        bar.pack_start(sep(), False, False, 0)

        # ── 操作按钮 ──
        bar.pack_start(mkbtn("undo", "撤销", lambda _: self._undo()), False, False, 0)
        bar.pack_start(mkbtn("clear", "清除", lambda _: self._clear_anns()), False, False, 0)
        bar.pack_start(mkbtn("zoom-out", "缩小", lambda _: self._zoom(-1)), False, False, 0)
        self.zlbl = Gtk.Label(label="100%")
        self.zlbl.get_style_context().add_class("snip-zoom")
        bar.pack_start(self.zlbl, False, False, 0)
        bar.pack_start(mkbtn("zoom-in", "放大", lambda _: self._zoom(1)), False, False, 0)

        bar.pack_start(sep(), False, False, 0)
        bar.pack_start(mkbtn("copy", "复制到剪贴板", self._copy, "snip-action"), False, False, 0)
        bar.pack_end(mkbtn("close", "关闭", lambda _: self.close(), "snip-close"), False, False, 0)

        return bar

    # ── 工具/颜色 ──
    def _settool(self, t):
        # 移除旧高亮
        if self.tool in self._tool_btns:
            btn = self._tool_btns[self.tool]
            if self.tool in self._tool_providers:
                btn.get_style_context().remove_provider(self._tool_providers[self.tool])
        self.tool = t
        # 添加新高亮
        if t in self._tool_btns:
            btn = self._tool_btns[t]
            prov = Gtk.CssProvider()
            prov.load_from_data(b"button { background: rgba(74,144,226,0.15); border-color: rgba(74,144,226,0.4); color: #4a90e2; }")
            btn.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
            self._tool_providers[t] = prov
    def _setcolor(self, c):
        self.color = c
        self._update_color_btn()

    def _update_color_btn(self):
        """更新颜色按钮外观"""
        r, g, b = self.color
        # 用纯色 Image 作为按钮内容，确保正方形
        pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 16, 16)
        pb.fill(int(r * 255) << 24 | int(g * 255) << 16 | int(b * 255) << 8 | 255)
        img = Gtk.Image.new_from_pixbuf(pb)
        old_img = self._color_btn.get_image()
        if old_img:
            self._color_btn.remove(old_img)
        self._color_btn.set_image(img)
        self._color_btn.set_image_position(Gtk.PositionType.LEFT)

    def _show_color_picker(self, _btn):
        """弹出颜色选择：预设 + 自定义"""
        dlg = Gtk.Dialog(title="选择颜色", parent=self, flags=Gtk.DialogFlags.MODAL)
        dlg.add_buttons("确定", Gtk.ResponseType.OK, "取消", Gtk.ResponseType.CANCEL)
        dlg.set_default_size(280, -1)

        box = dlg.get_content_area()
        box.set_spacing(8)
        box.set_border_width(10)

        # 标题
        lbl = Gtk.Label(label="预设颜色")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_opacity(0.7)
        box.pack_start(lbl, False, False, 0)

        # 预设颜色网格
        grid = Gtk.Grid()
        grid.set_column_spacing(4)
        grid.set_row_spacing(4)
        selected = [list(self.color)]

        for i, (r, g, b) in enumerate(COLORS):
            btn = Gtk.Button()
            btn.set_size_request(32, 32)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            prov = Gtk.CssProvider()
            prov.load_from_data(
                f"button {{ background: rgb({int(r*255)},{int(g*255)},{int(b*255)}); "
                f"border-radius: 6px; padding: 0; }}".encode()
            )
            btn.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
            # 选中高亮
            if (r, g, b) == tuple(self.color):
                btn.get_style_context().add_class("tool-active")
            btn.connect("clicked", lambda _, cc=(r, g, b), b_ref=btn: (
                selected.__setitem__(0, list(cc)),
                self._highlight_preset(grid, cc)
            ))
            grid.attach(btn, i % 4, i // 4, 1, 1)
        box.pack_start(grid, False, False, 0)

        # 自定义颜色
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 0)

        custom_box = Gtk.Box(spacing=8)
        custom_lbl = Gtk.Label(label="自定义：")
        custom_box.pack_start(custom_lbl, False, False, 0)

        color_btn = Gtk.ColorButton()
        color_btn.set_rgba(Gdk.RGBA(red=self.color[0], green=self.color[1], blue=self.color[2], alpha=1))
        color_btn.connect("color-set", lambda cb: selected.__setitem__(0, [
            cb.get_rgba().red, cb.get_rgba().green, cb.get_rgba().blue
        ]))
        custom_box.pack_start(color_btn, False, False, 0)
        box.pack_start(custom_box, False, False, 0)

        dlg.show_all()
        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            self._setcolor(tuple(selected[0]))
        dlg.destroy()

    def _highlight_preset(self, grid, color):
        """高亮选中的预设颜色"""
        # 清除所有高亮
        for child in grid.get_children():
            child.get_style_context().remove_class("tool-active")
        # 找到对应按钮并高亮
        for i, (r, g, b) in enumerate(COLORS):
            if (r, g, b) == color:
                child = grid.get_child_at(i % 4, i // 4)
                if child:
                    prov = Gtk.CssProvider()
                    prov.load_from_data(
                        f"button {{ background: rgb({int(r*255)},{int(g*255)},{int(b*255)}); "
                        f"border-radius: 6px; padding: 0; border: 2px solid #4a90e2; }}".encode()
                    )
                    child.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
                break
    def _setlw(self, w):
        self.lw = w
        self._highlight_lw(w)

    def _highlight_lw(self, lw):
        """高亮当前线粗按钮"""
        # 移除旧高亮
        if hasattr(self, '_lw_active') and self._lw_active in self._lw_providers:
            btn = self._lw_btns.get(self._lw_active)
            if btn:
                try:
                    btn.get_style_context().remove_provider(self._lw_providers[self._lw_active])
                except Exception:
                    pass
        # 添加新高亮
        if lw in self._lw_btns:
            btn = self._lw_btns[lw]
            prov = Gtk.CssProvider()
            prov.load_from_data(b"button { background: rgba(74,144,226,0.15); border-color: rgba(74,144,226,0.4); color: #4a90e2; }")
            btn.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
            self._lw_providers[lw] = prov
        self._lw_active = lw

    # ── 缩放 ──
    def _zoom(self, d):
        self.scale = max(0.1, min(5.0, self.scale + 0.1 * d))
        self._disp_w = max(1, int(self.orig.get_width() * self.scale))
        self._disp_h = max(1, int(self.orig.get_height() * self.scale))
        self._refresh_img()

    def _refresh_img(self):
        """刷新显示"""
        self.darea.queue_draw()
        self.zlbl.set_label(f"{int(self.scale * 100)}%")
        self.resize(self._disp_w, self._disp_h + 36)

    def _on_scroll(self, w, e):
        if e.direction == Gdk.ScrollDirection.UP:
            d = 1
        elif e.direction == Gdk.ScrollDirection.DOWN:
            d = -1
        elif e.direction == Gdk.ScrollDirection.SMOOTH:
            # 触控板/部分鼠标：用 delta_y 判断方向
            _, dx, dy = e.get_scroll_deltas()
            d = 1 if dy < 0 else -1
        else:
            return False
        self._zoom(d)
        return True

    def _w2i(self, wx, wy):
        """控件坐标 → 原图坐标"""
        alloc = self.darea.get_allocation()
        aw, ah = alloc.width, alloc.height
        if aw <= 0 or ah <= 0:
            aw, ah = self._disp_w, self._disp_h
        return (
            wx * self.orig.get_width() / max(1, aw),
            wy * self.orig.get_height() / max(1, ah),
        )

    def _on_press(self, w, e):
        if e.button != 1:
            return False
        if self.tool == "move":
            self.get_window().begin_move_drag(
                int(e.button), int(e.x_root), int(e.y_root), e.time
            )
            return True
        if self.tool == "text":
            self._add_text(self._w2i(e.x, e.y))
            return True
        self._drawing = True
        self._start = self._w2i(e.x, e.y)
        if self.tool == "pen":
            self._pen_pts = [self._start]
        return True

    def _on_release(self, w, e):
        if not self._drawing:
            return False
        end = self._w2i(e.x, e.y)
        ctx = cairo.Context(self._ann_surface)
        if self.tool in ("rect", "arrow", "line"):
            self._draw_shape(ctx, self.tool, self._start, end)
            self.anns.append((self.tool, self._start, end, self.color, self.lw))
        elif self.tool == "pen":
            self._draw_pen(ctx, self._pen_pts)
            self.anns.append(("pen", list(self._pen_pts), self.color, self.lw))
        self._drawing = False
        self._temp_surface = None  # 清空临时预览
        self._refresh_img()
        return True

    def _on_motion(self, w, e):
        if not self._drawing:
            return False
        p = self._w2i(e.x, e.y)
        # 创建临时预览 surface（基于已有标注）
        w_orig, h_orig = self.orig.get_width(), self.orig.get_height()
        self._temp_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w_orig, h_orig)
        ctx = cairo.Context(self._temp_surface)
        # 先画已有标注
        for a in self.anns:
            if a[0] == "pen":
                self._draw_pen(ctx, a[1], color=a[2], lw=a[3])
            elif a[0] == "text":
                _, text, pos, color, fsize = a
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(fsize)
                ctx.set_source_rgba(*color, 0.95)
                ctx.move_to(pos[0], pos[1] + fsize)
                ctx.show_text(text)
            else:
                self._draw_shape(ctx, a[0], a[1], a[2], color=a[3], lw=a[4])
        # 再画当前拖拽的形状
        if self.tool == "pen":
            self._pen_pts.append(p)
            self._draw_pen(ctx, self._pen_pts)
        elif self.tool in ("rect", "arrow", "line"):
            self._draw_shape(ctx, self.tool, self._start, p)
        self.darea.queue_draw()
        return True

    def _on_draw(self, w, cr):
        """DrawingArea 绘制：原图 + 标注"""
        # 绘制原图
        pb = self.orig.scale_simple(self._disp_w, self._disp_h,
                                    GdkPixbuf.InterpType.BILINEAR)
        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        cr.paint()
        # 绘制标注 surface（已有标注 + 当前绘制）
        if self._temp_surface:
            # 有临时预览（正在绘制中）
            cr.save()
            cr.scale(self.scale, self.scale)
            cr.set_source_surface(self._temp_surface, 0, 0)
            cr.paint()
            cr.restore()
        elif self.anns:
            # 有已完成的标注
            cr.save()
            cr.scale(self.scale, self.scale)
            cr.set_source_surface(self._ann_surface, 0, 0)
            cr.paint()
            cr.restore()
        return True

    # ── 标注绘制 ──
    def _draw_pen(self, ctx, pts, color=None, lw=None):
        if len(pts) < 2:
            return
        ctx.set_source_rgba(*(color or self.color), 0.9)
        ctx.set_line_width(lw or self.lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.stroke()

    def _draw_shape(self, ctx, tool, start, end, color=None, lw=None):
        ctx.set_source_rgba(*(color or self.color), 0.9)
        ctx.set_line_width(lw or self.lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        x0, y0 = start
        x1, y1 = end
        if tool == "rect":
            ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
            ctx.stroke()
        elif tool == "line":
            ctx.move_to(x0, y0)
            ctx.line_to(x1, y1)
            ctx.stroke()
        elif tool == "arrow":
            ctx.move_to(x0, y0)
            ctx.line_to(x1, y1)
            ctx.stroke()
            a = math.atan2(y1 - y0, x1 - x0)
            L = 15 + (lw or self.lw) * 2
            for da in [math.pi * 0.8, -math.pi * 0.8]:
                ctx.move_to(x1, y1)
                ctx.line_to(x1 + L * math.cos(a + da), y1 + L * math.sin(a + da))
                ctx.stroke()

    def _redraw_anns(self):
        w, h = self.orig.get_width(), self.orig.get_height()
        self._ann_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        ctx = cairo.Context(self._ann_surface)
        for a in self.anns:
            if a[0] == "pen":
                # ("pen", points, color, lw)
                self._draw_pen(ctx, a[1], color=a[2], lw=a[3])
            elif a[0] == "text":
                # ("text", text, pos, color, fsize)
                _, text, pos, color, fsize = a
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(fsize)
                ctx.set_source_rgba(*color, 0.95)
                ctx.move_to(pos[0], pos[1] + fsize)
                ctx.show_text(text)
            else:
                # (tool, start, end, color, lw)
                self._draw_shape(ctx, a[0], a[1], a[2], color=a[3], lw=a[4])

    def _add_text(self, pos):
        d = Gtk.Dialog(title="文字", parent=self, flags=0)
        d.add_buttons("确定", Gtk.ResponseType.OK, "取消", Gtk.ResponseType.CANCEL)
        e = Gtk.Entry()
        e.set_size_request(200, -1)
        d.get_content_area().pack_start(e, True, True, 10)
        d.show_all()
        r = d.run()
        t = e.get_text()
        d.destroy()
        if r == Gtk.ResponseType.OK and t:
            ctx = cairo.Context(self._ann_surface)
            fsize = max(14, self.lw * 5)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(fsize)
            ctx.set_source_rgba(*self.color, 0.95)
            ctx.move_to(pos[0], pos[1] + fsize)
            ctx.show_text(t)
            self.anns.append(("text", t, pos, self.color, fsize))
            self._refresh_img()

    def _undo(self):
        if self.anns:
            self.anns.pop()
            self._redraw_anns()
            self._refresh_img()

    def _clear_anns(self):
        if self.anns:
            self.anns.clear()
            self._redraw_anns()
            self._refresh_img()

    def _copy(self, _):
        try:
            w, h = self.orig.get_width(), self.orig.get_height()
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            ctx = cairo.Context(s)
            Gdk.cairo_set_source_pixbuf(ctx, self.orig, 0, 0)
            ctx.paint()
            ctx.set_source_surface(self._ann_surface, 0, 0)
            ctx.paint()
            pb = Gdk.pixbuf_get_from_surface(s, 0, 0, w, h)
            cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            cb.set_image(pb)
            cb.store()
        except Exception as e:
            print(f"复制失败: {e}")
