from abc import ABC, abstractmethod
import pathlib
import re
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from typing import Any, Callable, Iterable, NewType
import re
import matplotlib.pyplot as plt
from dataclasses import dataclass
import statistics


class PointTransformer(ABC):

  @abstractmethod
  def transform(self, x: float, y: float) -> tuple[float, float]:
    pass


class NoopTransformer(PointTransformer):

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x, y


class PointTranslate(PointTransformer):

  def __init__(self, dx: float, dy: float):
    self.dx, self.dy = dx, dy

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x + self.dx, y + self.dy


class PointScale(PointTransformer):

  def __init__(self, sx: float, sy: float):
    self.sx, self.sy = sx, sy

  def transform(self, x: float, y: float) -> tuple[float, float]:
    return x * self.sx, y * self.sy


class ComposeTransformers(PointTransformer):

  def __init__(self, transformers: list[PointTransformer]):
    self._transformers = transformers

  def transform(self, x: float, y: float) -> tuple[float, float]:
    for t in self._transformers:
      x, y = t.transform(x, y)
    return x, y


@dataclass
class Rect:
  x: float
  y: float
  w: float
  h: float
  params: dict[str, str] = {}


class ShapeDrawer(ABC):

  @abstractmethod
  def add_line(self, x1: float, y1: float, x2: float, y2: float,
               params: dict[str, str] | None) -> None:
    pass

  def add_horizontal_line(self,
                          x1: float,
                          x2: float,
                          y: float,
                          params: dict[str, str] | None = None) -> None:
    self.add_line(x1, y, x2, y, params)

  def add_vertical_line(self,
                        x: float,
                        y1: float,
                        y2: float,
                        params: dict[str, str] | None = None) -> None:
    self.add_line(x, y1, x, y2, params)

  @abstractmethod
  def add_literal(self, content: str) -> None:
    pass

  @abstractmethod
  def width(self) -> float:
    pass

  @abstractmethod
  def height(self) -> float:
    pass

  def transformer(self) -> PointTransformer:
    return NoopTransformer()

  @abstractmethod
  def add_rect(self,
               x: float,
               y: float,
               w: float,
               h: float,
               params: dict[str, str] | None = None) -> None:
    pass

  @abstractmethod
  def add_circle(self,
                 cx: float,
                 cy: float,
                 r: float,
                 params: dict[str, str] | None = None) -> None:
    pass


class TransformedShapeDrawer(ShapeDrawer):

  def __init__(self, transformer: PointTransformer,
               delegate: ShapeDrawer) -> None:
    self._transformer = transformer
    self.delegate = delegate

  def add_line(self, x1: float, y1: float, x2: float, y2: float,
               params: dict[str, str] | None) -> None:
    tx1, ty1 = self._transformer.transform(x1, y1)
    tx2, ty2 = self._transformer.transform(x2, y2)
    self.delegate.add_line(tx1, ty1, tx2, ty2, params)

  def width(self) -> float:
    p1_x, _ = self._transformer.transform(0.0, 0.0)
    p2_x, _ = self._transformer.transform(self.delegate.width(),
                                          self.delegate.height())
    return p2_x - p1_x

  def height(self) -> float:
    _, p1_y = self._transformer.transform(0.0, 0.0)
    _, p2_y = self._transformer.transform(self.delegate.width(),
                                          self.delegate.height())
    return p2_y - p1_y

  def transformer(self) -> PointTransformer:
    return self._transformer

  def add_rect(self,
               x: float,
               y: float,
               w: float,
               h: float,
               params: dict[str, str] | None = None) -> None:
    # Map two points to find the new bounding box
    tx1, ty1 = self._transformer.transform(x, y)
    tx2, ty2 = self._transformer.transform(x + w, y + h)

    # Calculate new top-left and dimensions
    nx, ny = min(tx1, tx2), min(ty1, ty2)
    nw, nh = abs(tx1 - tx2), abs(ty1 - ty2)
    self.delegate.add_rect(nx, ny, nw, nh, params)

  def add_circle(self,
                 cx: float,
                 cy: float,
                 r: float,
                 params: dict[str, str] | None = None) -> None:
    tx, ty = self._transformer.transform(cx, cy)
    self.delegate.add_circle(
        tx, ty, abs(self._transformer.transform(cx + r, cy)[0] - tx), params)

  def add_literal(self, content: str) -> None:
    self.delegate.add_literal(content)


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
  "Returns a new delegate where drawing is constrained to the box given."

  to_origin = PointTranslate(-input_box.x1, -input_box.y1)

  sx = (output_box.x2 - output_box.x1) / (input_box.x2 - input_box.x1)
  sy = (output_box.y2 - output_box.y1) / (input_box.y2 - input_box.y1)
  scale = PointScale(sx, sy)

  to_output = PointTranslate(output_box.x1, output_box.y1)

  transformer = ComposeTransformers([to_origin, scale, to_output])
  return TransformedShapeDrawer(transformer, delegate)


class SvgChart(ShapeDrawer):

  def __init__(self, width: float, height: float,
               styles: list[pathlib.Path]) -> None:
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

  def width(self) -> float:
    return self._width

  def height(self) -> float:
    return self._height

  def _get_extra(self, params: dict[str, str] | None) -> str:
    extra_params = ""
    style = params and params.get('style')
    if style:
      extra_params += f" style='{style}'"
    class_value = params and params.get('class')
    if class_value:
      extra_params += f" class='{class_value}'"
    return extra_params

  def add_line(self, x1: float, y1: float, x2: float, y2: float,
               params: dict[str, str] | None) -> None:
    extra_params = self._get_extra(params)
    self.add_literal(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"{extra_params}/>'
    )

  def add_literal(self, text: str) -> None:
    self._lines.append(text)

  def add_rect(self,
               x: float,
               y: float,
               w: float,
               h: float,
               params: dict[str, str] | None = None) -> None:
    extra_params = self._get_extra(params)
    self.add_literal(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{extra_params}/>'
    )

  def add_circle(self,
                 cx: float,
                 cy: float,
                 r: float,
                 params: dict[str, str] | None = None) -> None:
    extra_params = self._get_extra(params)
    contents = f"circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}'{extra_params}"
    title = (params or {}).get("title")
    if title:
      self.add_literal(f"<{contents}><title>{title}</title></circle>")
    else:
      self.add_literal(f"<{contents}/>")

  def write(self, path: pathlib.Path) -> None:
    with open(path, 'w') as f:
      f.write("\n".join(self._lines))
      f.write("</svg>")


@dataclass
class PlotXY:

  delegate: ShapeDrawer
  input_box: Box
  output_box: Box
  x_label: str | None = None
  y_label: str | None = None

  # Draw up to this number of tics on the axes.
  x_tics_count: int = 10
  y_tics_count: int = 10

  labels: frozenset[str] = frozenset()

  def __init__(self, delegate: ShapeDrawer, input_box: Box) -> None:
    self.delegate = delegate
    self.input_box = input_box
    self.output_box = Box(0, 0, self.delegate.width(), self.delegate.height())

  def _find_tic_interval(self, low: float, high: float, max_len: int) -> float:
    """Returns the ideal distance between tics."""
    assert low < high
    assert max_len > 0
    power_of_10 = 10**math.floor(math.log10((high - low) / max_len))
    for factor in [1, 2, 5, 10]:
      candidate = power_of_10 * factor
      count = (high - max(low, 0)) // candidate  # Positive tics.
      if low <= 0:
        count += 1  # For zero.
        if low < 0:
          count += abs(low) // candidate  # Negative tics.
      if count <= max_len:
        return candidate
    assert False

  def _get_tics(self, low: float, high: float, max_len: int) -> list[float]:
    """Returns a list with the values where tics should be drawn.

    Uses `_find_tic_interval` to find the multiplers and returns at most
    `max_len` values (between `low` and `high`, inclusive).
    """
    assert low < high
    if max_len <= 0:
      return []
    interval: float = self._find_tic_interval(low, high, max_len)
    assert interval != 0
    first_tic: float = math.ceil(low / interval) * interval
    if first_tic > high:
      return []
    return [
        first_tic + k * interval
        for k in range(min(max_len,
                           int((high - first_tic) / interval) + 1))
    ]

  def build(self) -> ShapeDrawer:
    box = MapToBox(self.input_box, self.output_box, self.delegate)
    for x in self._get_tics(self.input_box.x1, self.input_box.x2,
                            self.x_tics_count):
      box.add_vertical_line(x, self.input_box.y1, self.input_box.y2,
                            {"class": "tic"})
      span = (self.input_box.height() / 50) * (
          self.output_box.width() / self.output_box.height())
      box.add_vertical_line(x, -span, 0)
      dx, dy = box.transformer().transform(x, 2 * -span)
      box.add_literal(f"<text x='{dx}' y='{dy}' class='tic-value-x'>{x}</text>")

    for y in self._get_tics(self.input_box.y1, self.input_box.y2,
                            self.y_tics_count):
      box.add_horizontal_line(self.input_box.x1, self.input_box.x2, y,
                              {"class": "tic"})
      span = self.input_box.width() / 50
      box.add_horizontal_line(-span, 0, y)
      dx, dy = box.transformer().transform(2 * -span, y)
      box.add_literal(f"<text x='{dx}' y='{dy}' class='tic-value-y'>{y}</text>")

    for i, key in enumerate(sorted(self.labels)):
      lx = self.delegate.width() - 60
      ly = 20 + (i * 20)
      self.delegate.add_rect(lx, ly, 10, 10, {"class": key})
      self.delegate.add_literal(
          f'<text x="{lx + 15}" y="{ly + 9}">{key}</text>')

    box.add_vertical_line(self.input_box.x1, self.input_box.y1,
                          self.input_box.y2)
    box.add_horizontal_line(self.input_box.x1, self.input_box.x2,
                            self.input_box.y1)

    self.delegate.add_literal(
        f'<text x="{self.delegate.width()/2}" y="{self.delegate.height()-10}" text-anchor="middle" font-size="12">{self.x_label}</text>'
    )
    self.delegate.add_literal(
        f'<text transform="rotate(-90 15,{self.delegate.height()/2})" x="15" y="{self.delegate.height()/2}" text-anchor="middle" font-size="12">{self.y_label}</text>'
    )

    return box


DataDict = NewType("DataDict", dict[str, list[tuple[float, float]]])


def _box_for_points(data_dict: DataDict) -> Box:
  all_points = [pt for pts in data_dict.values() for pt in pts]
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  return Box(min(0, min(all_x)), min(0, min(all_y)), max(all_x), max(all_y))


def simple_plot(delegate: ShapeDrawer, points: DataDict) -> PlotXY:
  return PlotXY(delegate, _box_for_points(points))


def scatterplot(drawer: ShapeDrawer, data_dict: DataDict) -> None:
  box = _box_for_points(data_dict)
  radius = min(box.width(), box.height()) / 30
  for key, points in data_dict.items():
    for x, y in points:
      drawer.add_circle(x, y, radius, {
          "class": key,
          "title": f"{key}: ({x}, {y})"
      })
