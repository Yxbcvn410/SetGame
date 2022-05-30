from enum import Enum
from math import pi

import cairo

CARD_ASPECT_RATIO = 1.35


class CardColor(Enum):
    GREEN = 0
    RED = 1
    PURPLE = 2


def rgb(c: CardColor):
    if c == CardColor.GREEN:
        return 0, 0.4, 0
    elif c == CardColor.RED:
        return 0.8, 0, 0
    else:
        return 0.5, 0, 0.5


class CardFill(Enum):
    SOLID = 0
    STRIPES = 1
    NONE = 2


class CardShape(Enum):
    RHOMBUS = 0
    OVAL = 1
    SNAKE = 2


def draw_shape_outline(ctx: cairo.Context, shape: CardShape):
    if shape == CardShape.RHOMBUS:
        ctx.move_to(0, 50)
        ctx.line_to(50, 0)
        ctx.line_to(100, 50)
        ctx.line_to(50, 100)
        ctx.line_to(0, 50)
    elif shape == CardShape.OVAL:
        ctx.arc(50, 50, 50, 0, 2 * pi)
    elif shape == CardShape.SNAKE:
        x0, y0 = (80, 8)
        x1, y1 = (95, 90)
        ctx.move_to(x0, y0)
        for _ in range(2):
            ctx.curve_to(x0 + 40, y0 + 20, x1 - 80, y1 - 20, x1, y1)
            ctx.curve_to(x1 + 20, y1 + 5, 100 - x0 + 30, 100 - y0 + 15, 100 - x0, 100 - y0)
            ctx.rotate(pi)
            ctx.translate(-100, -100)


def get_striped_surface(color: CardColor):
    s = cairo.ImageSurface(cairo.Format.RGB24, 100, 100)
    ctx = cairo.Context(s)
    ctx.rectangle(0, 0, 100, 100)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()
    for i in range(0, 100, 5):
        ctx.move_to(0, i)
        ctx.line_to(100, i)
    ctx.set_source_rgb(*rgb(color))
    ctx.set_line_width(2)
    ctx.stroke()
    return s


class Card:
    Shape: CardShape
    Fill: CardFill
    Color: CardColor
    Count: int

    def __init__(self, shape, fill, color, count):
        assert 1 <= count <= 3
        self.Shape = shape
        self.Fill = fill
        self.Color = color
        self.Count = count

    def draw(self, ctx: cairo.Context, lw=2, rotate=False):
        if rotate:
            ctx.rotate(-pi / 2)
            ctx.translate(-330, 0)
        ctx.translate(105 / 2 * (3 - self.Count) + 10, 10)
        for _ in range(self.Count):
            ctx.new_sub_path()
            draw_shape_outline(ctx, self.Shape)
            if self.Fill == CardFill.STRIPES:
                ctx.set_source_surface(get_striped_surface(self.Color))
                ctx.fill_preserve()
            ctx.set_source_rgb(*rgb(self.Color))
            if self.Fill == CardFill.SOLID:
                ctx.fill()
            else:
                ctx.set_line_width(lw)
                ctx.stroke()
            ctx.translate(105, 0)
        ctx.translate(-105 / 2 * (3 - self.Count) - 10 - 105 * self.Count, -10)
        if rotate:
            ctx.translate(330, 0)
            ctx.rotate(pi / 2)
