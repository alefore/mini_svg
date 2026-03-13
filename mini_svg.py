from abc import ABC, abstractmethod
import pathlib
import re
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from typing import Any, Callable, Iterable
import re
import matplotlib.pyplot as plt
from dataclasses import dataclass
import statistics


class PointTransformer(ABC):

  @abstractmethod
  def transform(self, x: float, y: float) -> tuple[float, float]:
    pass


class NoopTransformer(PointTransformer):

  def transform(self, x, y):
    return x, y


class PointTranslate(PointTransformer):

  def __init__(self, dx: float, dy: float):
    self.dx, self.dy = dx, dy

  def transform(self, x, y):
    return x + self.dx, y + self.dy


class PointScale(PointTransformer):

  def __init__(self, sx: float, sy: float):
    self.sx, self.sy = sx, sy

  def transform(self, x, y):
    return x * self.sx, y * self.sy


class ComposeTransformers(PointTransformer):

  def __init__(self, transformers: list[PointTransformer]):
    self._transformers = transformers

  def transform(self, x, y):
    for t in self._transformers:
      x, y = t.transform(x, y)
    return x, y


class ShapeDrawer(ABC):

  @abstractmethod
  def add_line(self, x1, y1, x2, y2, params: dict[str, str] | None) -> None:
    pass

  def add_horizontal_line(self, x1, x2, y, params=None) -> None:
    self.add_line(x1, y, x2, y, params)

  def add_vertical_line(self, x, y1, y2, params=None) -> None:
    self.add_line(x, y1, x, y2, params)

  @abstractmethod
  def width(self) -> float:
    pass

  @abstractmethod
  def height(self) -> float:
    pass

  def transformer(self) -> PointTransformer:
    return NoopTransformer()

  @abstractmethod
  def add_rect(self, x, y, w, h, params: dict[str, str] | None = None) -> None:
    pass

  @abstractmethod
  def add_circle(self, cx, cy, r, params: dict[str, str] | None = None) -> None:
    pass


class TransformedShapeDrawer(ShapeDrawer):

  def __init__(self, transformer: PointTransformer,
               delegate: ShapeDrawer) -> None:
    self._transformer = transformer
    self.delegate = delegate

  def add_line(self, x1, y1, x2, y2, params) -> None:
    tx1, ty1 = self._transformer.transform(x1, y1)
    tx2, ty2 = self._transformer.transform(x2, y2)
    self.delegate.add_line(tx1, ty1, tx2, ty2, params)

  def width(self):
    p1 = self._transformer(0, 0)[0]
    p2 = self._transformer(self.delegate.width, self.delegate.height)[0]
    return p2 - p1

  def height(self):
    p1 = self._transformer(0, 0)[1]
    p2 = self._transformer(self.delegate.width, self.delegate.height)[1]
    return p2 - p1

  def transformer(self) -> PointTransformer:
    return self._transformer

  def add_rect(self, x, y, w, h, params=None) -> None:
    # Map two points to find the new bounding box
    tx1, ty1 = self._transformer.transform(x, y)
    tx2, ty2 = self._transformer.transform(x + w, y + h)

    # Calculate new top-left and dimensions
    nx, ny = min(tx1, tx2), min(ty1, ty2)
    nw, nh = abs(tx1 - tx2), abs(ty1 - ty2)
    self.delegate.add_rect(nx, ny, nw, nh, params)

  def add_circle(self, cx, cy, r, params: dict[str, str] | None = None) -> None:
    tx, ty = self._transformer.transform(cx, cy)
    self.delegate.add_circle(
        tx, ty, abs(self._transformer.transform(cx + r, cy)[0] - tx), params)


@dataclass
class Box:
  x1: float
  y1: float
  x2: float
  y2: float

  def width(self) -> float:
    return abs(self.x2 - self.x1)

  def height(self) -> float:
    return abs(self.y2 - self.y1)


def MapToBox(input_box: Box, output_box: Box,
             delegate: ShapeDrawer) -> ShapeDrawer:
  """Returns a new delegate where drawing is constrained to the box given."""

  to_origin = PointTranslate(-input_box.x1, -input_box.y1)

  sx = (output_box.x2 - output_box.x1) / (input_box.x2 - input_box.x1)
  sy = (output_box.y2 - output_box.y1) / (input_box.y2 - input_box.y1)
  scale = PointScale(sx, sy)

  to_output = PointTranslate(output_box.x1, output_box.y1)

  transformer = ComposeTransformers([to_origin, scale, to_output])
  return TransformedShapeDrawer(transformer, delegate)


class SvgChart(ShapeDrawer):

  def __init__(self, width, height, styles: list[pathlib.Path]):
    self._width = width
    self._height = height
    self._lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"',
        '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
        f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" version="1.1">',
    ]

    if styles:
      self.add_literal("<style>")
      for path in styles:
        self.add_literal(path.read_text())
      self.add_literal('</style>')

  def width(self):
    return self._width

  def height(self):
    return self._height

  def _get_extra(self, params):
    extra_params = ""
    style = params and params.get('style')
    if style:
      extra_params = f" style='{style}'"
    return extra_params

  def add_line(self, x1, y1, x2, y2, params) -> None:
    extra_params = self._get_extra(params)
    self.add_literal(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"{extra_params}/>'
    )

  def add_literal(self, text: str) -> None:
    self._lines.append(text)

  def add_rect(self, x, y, w, h, params: dict[str, str] | None = None) -> None:
    extra_params = self._get_extra(params)
    self.add_literal(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{extra_params}/>'
    )

  def add_circle(self, cx, cy, r, params: dict[str, str] | None = None) -> None:
    extra_params = self._get_extra(params)
    self.add_literal(f"<circle cx='{cx}' cy='{cy}' r='{r}'{extra_params}/>")

  def write(self, path) -> None:
    with open(path, 'w') as f:
      f.write("\n".join(self._lines))
      f.write("</svg>")
