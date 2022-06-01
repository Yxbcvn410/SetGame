import cairo
import gi

from SetCard import CARD_ASPECT_RATIO, pi
from SetGameField import GameField

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

FRAME_DEFAULT_RGB = (0.7, 0.7, 0.7)
FRAME_SELECTED_RGB = (0, 0.7, 0)
FRAME_HINT_RGB = (0.8, 0, 0)


class GameView:
    def __init__(self, field: GameField, frame: Gtk.AspectFrame, layout, set_found_callback):
        self.field = field
        self.frame = frame
        self.layout = layout
        self.set_found_callback = set_found_callback
        self.painter = [FRAME_DEFAULT_RGB for _ in range(len(field))]
        self.selected = set()
        self.active = True
        self.make_canvases_for_cards()

    def set_active(self, active):
        self.active = active
        self.painter = [FRAME_DEFAULT_RGB for _ in range(len(self.field))]
        if not self.active:
            self.make_canvases_for_cards()

    def set_layout(self, layout):
        self.layout = layout
        self.make_canvases_for_cards()

    def make_canvases_for_cards(self):
        if self.active:
            c, r = self.field.size()
        else:
            c, r = 3, 4
        ratio = (c * CARD_ASPECT_RATIO / r) if self.layout else (r / CARD_ASPECT_RATIO / c)
        self.frame.set_property("ratio", ratio)
        gr = self.frame.get_children()[0]
        for child in gr.get_children():
            gr.remove(child)
        gr = self.frame.get_children()[0]

        for i in range(c * r):
            x = i % 3
            y = (i - x) // 3
            canvas = Gtk.DrawingArea()

            def draw_handler(i):
                def on_draw(_w, ctx: cairo.Context):
                    w = _w.get_allocated_width()
                    h = _w.get_allocated_height()
                    wd, hd = (330, 120) if self.layout else (120, 330)
                    ctx.scale(w / wd, h / hd)
                    if self.active:
                        self.field[i].draw(ctx, lw=w / 200 * 2, rotate=not self.layout)
                    ctx.scale(wd / w, hd / h)

                    m = 0.015 * w
                    ctx.rectangle(m, m, w - 2 * m, h - 2 * m)
                    if self.active:
                        ctx.set_source_rgb(*self.painter[i])
                    else:
                        ctx.set_source_rgb(*FRAME_DEFAULT_RGB)
                    ctx.set_line_width(m)
                    ctx.stroke()

                return on_draw

            canvas.connect("draw", draw_handler(i))

            def click_handler(i):
                def on_click(widget, event: Gdk.EventButton):
                    if not self.active:
                        return
                    if event.button == Gdk.BUTTON_PRIMARY and event.type == Gdk.EventType.BUTTON_PRESS:
                        if i in self.selected:
                            self.selected.remove(i)
                        else:
                            self.selected.add(i)
                        self.painter[i] = FRAME_SELECTED_RGB if i in self.selected else FRAME_DEFAULT_RGB
                        if len(self.selected) == 3 and self.field.check_set(*self.selected):
                            self.set_found_callback(*self.selected)
                            self.selected = set()
                            self.painter = [FRAME_DEFAULT_RGB for _ in range(len(self.field))]
                            self.make_canvases_for_cards()
                        widget.queue_draw()

                return on_click

            if self.active:
                canvas.connect("button-press-event", click_handler(i))
            canvas.show()
            # canvas.activate()
            canvas.set_events(canvas.get_events() | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.TOUCH_MASK)
            if self.layout:
                gr.attach(canvas, x, y, 1, 1)
            else:
                gr.attach(canvas, y, x, 1, 1)

    def redraw(self):
        for c in self.frame.get_children()[0].get_children():
            c.queue_draw()

    def hint_set(self):
        if not self.active:
            return
        for idx in self.field.find_set():
            self.painter[idx] = FRAME_HINT_RGB
            if idx in self.selected:
                self.selected.remove(idx)
        self.redraw()
