from abc import ABC, abstractmethod
import pathlib
import re
from functools import singledispatchmethod
import itertools
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter
from typing import Any, Callable, Iterable, Iterator, NamedTuple, NewType
import re
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
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


ParamsDict = NewType("ParamsDict", dict[str, str])


@dataclass(frozen=True)
class Margins:
  top: float = 0
  right: float = 0
  bottom: float = 0
  left: float = 0


@dataclass(frozen=True)
class Box:
  x1: float
  y1: float
  x2: float
  y2: float

  def width(self) -> float:
    return abs(self.x2 - self.x1)

  def height(self) -> float:
    return abs(self.y2 - self.y1)

  def with_margins(self, margins: Margins) -> "Box":
    if self.y1 < self.y2:
      return Box(self.x1 + margins.left, self.y1 + margins.bottom,
                 self.x2 - margins.right, self.y2 - margins.top)
    return Box(self.x1 + margins.left, self.y1 - margins.bottom,
               self.x2 - margins.right, self.y2 + margins.top)

  def with_y_reversed(self) -> "Box":
    return Box(self.x1, self.y2, self.x2, self.y1)


def simple_box(width: float, height: float) -> Box:
  return Box(0, 0, width, height)


DEFAULT_BOX = simple_box(1.0, 1.0)


@dataclass(frozen=True)
class Rect:
  x: float
  y: float
  w: float
  h: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


@dataclass(frozen=True)
class Line:
  x1: float
  y1: float
  x2: float
  y2: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


def vertical_line(x, y1, y2, params: ParamsDict | None = None) -> Line:
  return Line(x, y1, x, y2, params or ParamsDict({}))


def horizontal_line(x1, x2, y, params: ParamsDict | None = None) -> Line:
  return Line(x1, y, x2, y, params or ParamsDict({}))


@dataclass(frozen=True)
class Circle:
  cx: float
  cy: float
  r: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


@dataclass(frozen=True)
class Text:
  text: str
  x: float
  y: float
  params: ParamsDict = field(default_factory=lambda: ParamsDict({}))


Shape = Rect | Line | Circle | Text


class ShapeTransformer:

  def __init__(self, transformer: PointTransformer) -> None:
    self.transformer = transformer

  def transform(self, shapes: Iterable[Shape]) -> Iterable[Shape]:
    return map(self._handle, shapes)

  @singledispatchmethod
  def _handle(self, arg: Any) -> Shape:
    raise TypeError(f"Cannot handle type {type(arg)}")

  @_handle.register
  def _(self, line: Line) -> Line:
    tx1, ty1 = self.transformer.transform(line.x1, line.y1)
    tx2, ty2 = self.transformer.transform(line.x2, line.y2)
    return Line(tx1, ty1, tx2, ty2, line.params)

  @_handle.register
  def _(self, rect: Rect) -> Rect:
    # Map two points to find the new bounding box
    tx1, ty1 = self.transformer.transform(rect.x, rect.y)
    tx2, ty2 = self.transformer.transform(rect.x + rect.w, rect.y + rect.h)

    # Calculate new top-left and dimensions
    nx, ny = min(tx1, tx2), min(ty1, ty2)
    nw, nh = abs(tx1 - tx2), abs(ty1 - ty2)
    return Rect(nx, ny, nw, nh, rect.params)

  @_handle.register
  def _(self, circle: Circle) -> Circle:
    tx, ty = self.transformer.transform(circle.cx, circle.cy)
    return Circle(
        tx, ty,
        abs(
            self.transformer.transform(circle.cx + circle.r, circle.cy)[0] -
            tx), circle.params)

  @_handle.register
  def _(self, text: Text) -> Text:
    tx, ty = self.transformer.transform(text.x, text.y)
    return Text(text.text, tx, ty, text.params)


def MoveAndScale(input_box: Box, output_box: Box) -> ShapeTransformer:
  "Returns a new delegate where drawing is constrained to the box given."

  to_origin = PointTranslate(-input_box.x1, -input_box.y1)

  sx = (output_box.x2 - output_box.x1) / (input_box.x2 - input_box.x1)
  sy = (output_box.y2 - output_box.y1) / (input_box.y2 - input_box.y1)
  scale = PointScale(sx, sy)

  to_output = PointTranslate(output_box.x1, output_box.y1)

  return ShapeTransformer(ComposeTransformers([to_origin, scale, to_output]))


class SvgWriter:

  def __init__(self, filename: pathlib.Path, width: float, height: float,
               styles: list[pathlib.Path]) -> None:
    self._filename = filename
    self._box = Box(0, 0, width, height)
    self._lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"',
        '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
        f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" version="1.1">',
    ]

    if styles:
      self._add_literal("<style>")
      for path in styles:
        self._add_literal(path.read_text())
      self._add_literal('</style>')

  def get_box(self) -> Box:
    return self._box

  def _get_extra(self, params: ParamsDict) -> str:
    extra_params = ""
    for keyword in ['style', 'class', 'transform']:
      value = params.get(keyword)
      if value:
        extra_params += f" {keyword}='{value}'"
    return extra_params

  def receive(self, shapes: Iterable[Shape]) -> None:
    for shape in shapes:
      match shape:
        case Rect():
          self._add_rect(shape)
        case Line():
          self._add_line(shape)
        case Circle():
          self._add_circle(shape)
        case Text():
          self._add_text(shape)
    with open(self._filename, 'w') as f:
      f.write("\n".join(self._lines))
      f.write("</svg>")

  def _add_line(self, line: Line) -> None:
    extra_params = self._get_extra(line.params)
    self._add_literal(
        f'<line x1="{line.x1:.1f}" y1="{line.y1:.1f}" x2="{line.x2:.1f}" y2="{line.y2:.1f}"{extra_params}/>'
    )

  def _add_literal(self, text: str) -> None:
    self._lines.append(text)

  def _add_rect(self, rect: Rect) -> None:
    extra_params = self._get_extra(rect.params)
    self._add_literal(
        f'<rect x="{rect.x:.1f}" y="{rect.y:.1f}" width="{rect.w:.1f}" height="{rect.h:.1f}"{extra_params}/>'
    )

  def _add_circle(self, circle: Circle) -> None:
    extra_params = self._get_extra(circle.params)
    contents = f"circle cx='{circle.cx:.1f}' cy='{circle.cy:.1f}' r='{circle.r:.1f}'{extra_params}"
    title = circle.params.get("title")
    if title:
      self._add_literal(f"<{contents}><title>{title}</title></circle>")
    else:
      self._add_literal(f"<{contents}/>")

  def _add_text(self, text: Text) -> None:
    extra_params = self._get_extra(text.params)
    self._add_literal(
        f"<text x='{text.x}' y='{text.y}'{extra_params}>{text.text}</text>")


@dataclass(frozen=True)
class PlotTics:
  values: frozenset[float]
  value_format: str


@dataclass(frozen=True)
class PlotTicsConfig:
  # List of values where tics should be drawn. If given, all other fields are
  # ignored.
  values: frozenset[float] | None = None

  # Do not draw more than this number of tics.
  max_count: int = 10

  # Minimum distance between tics.
  min_distance: float | None = None

  value_format: str | None = None

  def _find_base(self, low: float, high: float) -> float:
    """Returns the ideal distance between tics."""
    assert low < high
    assert self.max_count > 0
    assert not self.values
    rough_distance = (high - low) / self.max_count
    if self.min_distance:
      rough_distance = max(rough_distance, self.min_distance)
    power_of_10 = 10**math.floor(math.log10(rough_distance))
    for factor in [1, 2, 5, 10]:
      candidate: float = power_of_10 * factor
      count = (high - max(low, 0)) // candidate  # Positive tics.
      if low <= 0:
        count += 1  # For zero.
        if low < 0:
          count += abs(low) // candidate  # Negative tics.
      if count <= self.max_count and (not self.min_distance or
                                      candidate >= self.min_distance):
        return candidate
    assert False

  def _get_values(self, low: float, high: float,
                  base: float) -> frozenset[float]:
    """Returns a list with the values where tics should be drawn."""
    assert low < high
    if self.values is not None:
      return self.values
    if self.max_count <= 0:
      return frozenset()
    assert base != 0
    first_tic: float = math.ceil(low / base) * base
    if first_tic > high:
      return frozenset()
    return frozenset(
        first_tic + k * base
        for k in range(min(self.max_count,
                           int((high - first_tic) / base) + 1)))

  def _get_fmt(self, low: float, high: float, base: float) -> str:
    if self.value_format:
      return self.value_format
    return "d" if base > 1 else f".{abs(math.floor(math.log10(base)))}f"

  def build(self, low: float, high: float) -> PlotTics:
    if self.max_count <= 0:
      return PlotTics(values=frozenset(), value_format="ignored")
    if self.values:
      sorted_values = sorted(self.values)
      base = sorted_values[1] - sorted_values[0]
      return PlotTics(
          values=self.values, value_format=self._get_fmt(low, high, base))
    base = self._find_base(low, high)
    return PlotTics(
        values=self._get_values(low, high, base),
        value_format=self._get_fmt(low, high, base))


@dataclass(frozen=True)
class Plot2D:

  input_box: Box
  output_box: Box
  margins: Margins

  x_axis_values: PlotTicsConfig = PlotTicsConfig()
  y_axis_values: PlotTicsConfig = PlotTicsConfig()

  x_label: str | None = None
  y_label: str | None = None

  labels: frozenset[str] = frozenset()

  def transformer(self) -> ShapeTransformer:
    return MoveAndScale(
        self.input_box,
        self.output_box.with_y_reversed().with_margins(self.margins))

  def produce(self) -> Iterator[Shape]:
    return itertools.chain(self.transformer().transform(self._draw()),
                           self._legend())

  def _legend(self) -> Iterator[Shape]:
    for i, key in enumerate(sorted(self.labels)):
      lx = self.output_box.width() - 60
      ly = 20 + (i * 20)
      yield Rect(lx, ly, 10, 10, ParamsDict({"class": key}))
      yield Text(key, lx + 15, ly + 9)

    if self.x_label:
      yield Text(self.x_label,
                 self.output_box.width() / 2, self.output_box.height(),
                 ParamsDict({"class": "label-x"}))
    if self.y_label:
      yield Text(
          self.y_label, 15,
          self.output_box.height() / 2,
          ParamsDict({
              "class": "label-y",
              "transform": f"rotate(-90 15,{self.output_box.height()/2})"
          }))

  def _draw(self) -> Iterator[Shape]:
    x_values = self.x_axis_values.build(self.input_box.x1, self.input_box.x2)
    for x in x_values.values:
      yield vertical_line(x, self.input_box.y1, self.input_box.y2,
                          ParamsDict({"class": "tic"}))
      span = (self.input_box.height() / 50) * (
          self.output_box.width() / self.output_box.height())
      yield vertical_line(x, -span, 0)
      yield Text(f"{x:{x_values.value_format}}", x, 2 * -span,
                 ParamsDict({"class": "tic-value-x"}))

    y_values = self.y_axis_values.build(self.input_box.y1, self.input_box.y2)
    for y in y_values.values:
      yield horizontal_line(self.input_box.x1, self.input_box.x2, y,
                            ParamsDict({"class": "tic"}))
      span = self.input_box.width() / 50
      yield horizontal_line(self.input_box.x1 - span, self.input_box.x1, y)
      yield Text(f"{y:{y_values.value_format}}", self.input_box.x1 - 2 * span,
                 y, ParamsDict({"class": "tic-value-y"}))

    yield vertical_line(self.input_box.x1, self.input_box.y1, self.input_box.y2)
    yield horizontal_line(self.input_box.x1, self.input_box.x2,
                          self.input_box.y1)


DataDict = NewType("DataDict", dict[str, list[tuple[float, float]]])


def box_for_points(data_dict: DataDict) -> Box:
  all_points = [pt for pts in data_dict.values() for pt in pts]
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  return Box(min(0, min(all_x)), min(0, min(all_y)), max(all_x), max(all_y))


def scatterplot(data_dict: DataDict) -> Iterable[Shape]:
  box = box_for_points(data_dict)
  radius = min(box.width(), box.height()) / 30
  for key, points in data_dict.items():
    for x, y in points:
      yield Circle(x, y, radius,
                   ParamsDict({
                       "class": key,
                       "title": f"{key}: ({x}, {y})"
                   }))


BinElements = NewType("BinElements", int)


class Histogram(NamedTuple):
  binned_data: dict[str, list[BinElements]]

  bin_size: float
  min_value: float
  max_value: float
  max_count: BinElements

  @classmethod
  def create(cls, bins: int, data: dict[str, list[float]]):
    all_values = [v for obs in data.values() for v in obs]
    min_value, max_value = min(all_values), max(all_values)
    bin_size = (max_value - min_value) / bins

    binned_data: dict[str, list[BinElements]] = dict()
    for label, values in data.items():
      counts: list[BinElements] = [BinElements(0)] * bins
      for v in values:
        index = int((v - min_value) / bin_size)
        if index == bins:
          index -= 1
        counts[index] = BinElements(counts[index] + 1)
      binned_data[label] = counts

    max_count = max(max(bins) for bins in binned_data.values())
    return cls(binned_data, bin_size, min_value, max_value, max_count)

  def _draw(self) -> Iterable[Shape]:
    individual_bin_width = self.bin_size * 0.8 / len(self.binned_data)
    for group_index, (label, counts) in enumerate(self.binned_data.items()):
      for bin_index, count in enumerate(counts):
        if count > 0:
          start_range = self.bin_size * bin_index
          yield Rect(
              self.min_value + self.bin_size *
              (bin_index + 0.1 + 0.8 * group_index / len(self.binned_data)), 0,
              individual_bin_width, count, ParamsDict({"class": label.lower()}))

  def produce(self, *args, **kwargs) -> Iterable[Shape]:
    bin_count = max(len(bins) for bins in self.binned_data.values())
    plot_defaults: dict[str, Any] = {
        "input_box":
            Box(self.min_value, 0, self.max_value, self.max_count),
        "y_label":
            "Histogram",
        "x_axis_values":
            PlotTicsConfig(
                values=frozenset(self.min_value + i * self.bin_size
                                 for i in range(0, bin_count, 2))),
        "y_axis_values":
            PlotTicsConfig(min_distance=1),
        "labels":
            frozenset(self.binned_data),
    }
    plot_defaults.update(kwargs)
    plot = Plot2D(**plot_defaults)
    return itertools.chain(plot.produce(),
                           plot.transformer().transform(self._draw()))


class _PlotBoxOne(NamedTuple):
  label: str
  y_min: float
  y_max: float
  quantiles: list[float]
  min_whisker: float
  max_whisker: float

  @classmethod
  def create(cls, label: str, data: list[float]):
    data = sorted(data)
    quantiles = statistics.quantiles(data, n=4, method='inclusive')
    q1, median, q3 = quantiles
    iqr = q3 - q1
    fences = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
    min_whisker = min(x for x in data if x >= fences[0])
    max_whisker = max(x for x in data if x <= fences[1])

    return cls(label, min(data), max(data), quantiles, min_whisker, max_whisker)

  def draw(self, index: int, plot: Plot2D) -> Iterable[Shape]:
    x = plot.transformer().transformer.transform(index, 0)[0]
    yield Text(self.label, x,
               plot.output_box.height() - plot.margins.bottom - 20,
               ParamsDict({"class": "boxplot-label"}))
    for shape in plot.transformer().transform(self._shapes(index)):
      yield shape

  def _shapes(self, index) -> Iterable[Shape]:
    q1, median, q3 = self.quantiles
    box_w = 0.7
    yield vertical_line(index, self.min_whisker, self.max_whisker)
    for y in [self.min_whisker, self.max_whisker]:
      yield horizontal_line(index - box_w / 2, index + box_w / 2, y)
    yield Rect(index - box_w / 2, q1, box_w, q3 - q1,
               ParamsDict({"style": "fill: var(--text)"}))
    yield horizontal_line(index - box_w / 2, index + box_w / 2, median,
                          ParamsDict({"style": "stroke: var(--bg-mild)"}))


class PlotBox(NamedTuple):

  data: dict[str, _PlotBoxOne]
  y_min: float
  y_max: float

  @classmethod
  def create(cls, raw_data: dict[str, list[float]]):
    data = {
        key: _PlotBoxOne.create(key, value) for key, value in raw_data.items()
    }
    return cls(data, min(d.y_min for d in data.values()),
               max(d.y_max for d in data.values()))

  def _draw(self, plot: Plot2D) -> Iterable[Shape]:
    return itertools.chain.from_iterable(
        value.draw(index, plot)
        for index, value in enumerate(self.data.values()))

  def produce(self, *args, **kwargs) -> Iterable[Shape]:
    plot_defaults: dict[str, Any] = {
        "input_box":
            Box(-1, math.floor(self.y_min), len(self.data),
                math.ceil(self.y_max)),
        "x_axis_values":
            PlotTicsConfig(max_count=0),
    }
    plot_defaults.update(kwargs)
    plot = Plot2D(**plot_defaults)
    return itertools.chain(plot.produce(), self._draw(plot))
