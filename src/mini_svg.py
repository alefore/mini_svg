from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from functools import singledispatchmethod
import itertools
import math
import pathlib
import re
import statistics
from typing import Any, Callable, Iterable, Iterator, NamedTuple, NewType, Protocol, TypeVar, cast

from meta import value_with_default, with_config
from point_transformer import PointTransformer, MoveAndScale
from plot_ticks import PlotTicks, PlotTicksConfig
from box import Margins, Box, simple_box
from shape import Circle, Line, Rect, Shape, ShapeParams, ShapeStream, Text, shape_generator


class ShapeTransformer:

  def __init__(self, transformer: PointTransformer) -> None:
    self.transformer = transformer

  def __call__(self, shapes: Iterable[Shape]) -> ShapeStream:
    return ShapeStream(map(self._handle, shapes))

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


@dataclass(frozen=True, kw_only=True)
class _XYPlot:
  domain: Box | None = None
  output_range: Box | None = None
  margins: Margins | None = None

  x_axis_values: PlotTicksConfig = PlotTicksConfig()
  y_axis_values: PlotTicksConfig = PlotTicksConfig()

  x_label: str | None = None
  y_label: str | None = None

  labels: frozenset[str] = frozenset()

  identity_line: bool | None = None

  @property
  def transformer(self) -> ShapeTransformer:
    assert self.domain
    assert self.output_range
    assert self.margins
    return ShapeTransformer(
        MoveAndScale(
            self.domain,
            self.output_range.with_y_reversed().with_margins(self.margins)))

  def with_defaults(self, defaults: "_XYPlot") -> "_XYPlot":
    return _XYPlot(
        domain=self.domain or defaults.domain,
        output_range=self.output_range or defaults.output_range,
        margins=self.margins or defaults.margins,
        x_axis_values=self.x_axis_values.with_defaults(defaults.x_axis_values),
        y_axis_values=self.y_axis_values.with_defaults(defaults.y_axis_values),
        x_label=self.x_label or defaults.x_label,
        y_label=self.y_label or defaults.y_label,
        labels=self.labels or defaults.labels,
        identity_line=value_with_default(self.identity_line,
                                         defaults.identity_line))

  def produce(self) -> ShapeStream:
    return self.transformer(self._draw()) + self._legend()

  def _legend(self) -> Iterator[Shape]:
    assert self.output_range
    for i, key in enumerate(sorted(self.labels)):
      lx = self.output_range.width() - 60
      ly = 20 + (i * 20)
      yield Rect(lx, ly, 10, 10, ShapeParams(css_class=key))
      yield Text(key, lx + 15, ly + 9)

    if self.x_label:
      yield Text(self.x_label,
                 self.output_range.width() / 2, self.output_range.height(),
                 ShapeParams(css_class="label-x"))
    if self.y_label:
      yield Text(
          self.y_label, 15,
          self.output_range.height() / 2,
          ShapeParams(
              css_class="label-y",
              transform=f"rotate(-90 15,{self.output_range.height()/2})"))

  @shape_generator
  def _draw(self) -> Iterator[Shape]:
    assert self.domain
    assert self.output_range
    x_values = self.x_axis_values.build(self.domain.x1, self.domain.x2)
    for x in x_values.values:
      yield Line.vertical(x, self.domain.y1, self.domain.y2,
                          ShapeParams(css_class="tic"))
      span = (self.domain.height() / 50) * (
          self.output_range.width() / self.output_range.height())
      yield Line.vertical(x, -span, 0)
      yield Text(f"{x:{x_values.value_format}}", x, 2 * -span,
                 ShapeParams(css_class="tic-value-x"))

    y_values = self.y_axis_values.build(self.domain.y1, self.domain.y2)
    for y in y_values.values:
      yield Line.horizontal(self.domain.x1, self.domain.x2, y,
                            ShapeParams(css_class="tic"))
      span = self.domain.width() / 50
      yield Line.horizontal(self.domain.x1 - span, self.domain.x1, y)
      yield Text(f"{y:{y_values.value_format}}", self.domain.x1 - 2 * span, y,
                 ShapeParams(css_class="tic-value-y"))

    yield Line.vertical(self.domain.x1, self.domain.y1, self.domain.y2)
    yield Line.horizontal(self.domain.x1, self.domain.x2, self.domain.y1)

    if self.identity_line:
      clip = min(self.domain.x2, self.domain.y2)
      yield Line(0, 0, clip, clip, ShapeParams(css_class="identity-line"))


with_plot_config = with_config(_XYPlot)


class ShapeProducer(ABC):

  @abstractmethod
  def produce(self, plot: _XYPlot) -> ShapeStream:
    pass


@dataclass(frozen=True)
class SvgWriter:

  output_path: pathlib.Path
  width: float
  height: float
  css: list[pathlib.Path]

  def get_box(self) -> Box:
    return simple_box(self.width, self.height)

  def consume(self, shapes: Iterable[Shape]) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"',
        '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
        f'<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" version="1.1">',
    ]

    if self.css:
      lines += ["<style>"]
      for path in self.css:
        lines += [path.read_text()]
      lines += ['</style>']

    lines += map(self._write_shape, shapes)
    lines += ["</svg>"]
    with open(self.output_path, 'w') as f:
      f.write("\n".join(lines))

  @singledispatchmethod
  def _write_shape(self, arg: Any) -> str:
    raise TypeError(f"Cannot handle type {type(arg)}")

  @_write_shape.register
  def _(self, line: Line) -> str:
    return f'<line x1="{line.x1:.1f}" y1="{line.y1:.1f}" x2="{line.x2:.1f}" y2="{line.y2:.1f}"{line.params.as_text()}/>'

  @_write_shape.register
  def _(self, rect: Rect) -> str:
    return f'<rect x="{rect.x:.1f}" y="{rect.y:.1f}" width="{rect.w:.1f}" height="{rect.h:.1f}"{rect.params.as_text()}/>'

  @_write_shape.register
  def _(self, circle: Circle) -> str:
    contents = f"circle cx='{circle.cx:.1f}' cy='{circle.cy:.1f}' r='{circle.r:.1f}'{circle.params.as_text()}"
    title = circle.params.title
    if title is not None:
      return f"<{contents}><title>{title}</title></circle>"
    else:
      return f"<{contents}/>"

  @_write_shape.register
  def _(self, text: Text) -> str:
    return f"<text x='{text.x}' y='{text.y}'{text.params.as_text()}>{text.text}</text>"


with_svg_writer = with_config(SvgWriter)

DataDict = NewType("DataDict", dict[str, list[tuple[float, float]]])


@dataclass(frozen=True)
class _Scatterplot(ShapeProducer):
  data: DataDict
  domain: Box

  @shape_generator
  def _draw(self) -> Iterable[Shape]:
    radius = min(self.domain.width(), self.domain.height()) / 30
    for key, points in self.data.items():
      for x, y in points:
        yield Circle(x, y, radius,
                     ShapeParams(css_class=key, title=f"{key}: ({x}, {y})"))

  def produce(self, plot: _XYPlot) -> ShapeStream:
    plot = plot.with_defaults(
        _XYPlot(domain=self.domain, labels=frozenset(self.data)))
    print(plot)
    return plot.produce() + plot.transformer(self._draw())


@with_svg_writer
@with_plot_config
def scatterplot(writer: SvgWriter, plot: _XYPlot,
                data: dict[str, list[tuple[float, float]]]) -> None:
  all_points = [pt for pts in data.values() for pt in pts]
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  writer.consume(
      _Scatterplot(
          DataDict(data),
          domain=Box(
              min(0, min(all_x)), min(0, min(all_y)), max(all_x),
              max(all_y))).produce(
                  plot.with_defaults(_XYPlot(output_range=writer.get_box()))))


BinElements = NewType("BinElements", int)


@dataclass(frozen=True)
class _Histogram(ShapeProducer):
  binned_data: dict[str, list[BinElements]]

  bin_size: float
  min_value: float
  max_value: float
  max_count: BinElements

  def _draw(self) -> Iterable[Shape]:
    individual_bin_width = self.bin_size * 0.8 / len(self.binned_data)
    for group_index, (label, counts) in enumerate(self.binned_data.items()):
      for bin_index, count in enumerate(counts):
        if count > 0:
          start_range = self.bin_size * bin_index
          yield Rect(
              self.min_value + self.bin_size *
              (bin_index + 0.1 + 0.8 * group_index / len(self.binned_data)), 0,
              individual_bin_width, count, ShapeParams(css_class=label.lower()))

  def produce(self, plot: _XYPlot) -> ShapeStream:
    bin_count = max(len(bins) for bins in self.binned_data.values())
    plot = plot.with_defaults(
        _XYPlot(
            domain=Box(self.min_value, 0, self.max_value, self.max_count),
            y_label="Histogram",
            x_axis_values=PlotTicksConfig(
                values=frozenset(self.min_value + i * self.bin_size
                                 for i in range(0, bin_count, 2))),
            y_axis_values=PlotTicksConfig(min_distance=1),
            labels=frozenset(self.binned_data)))
    return plot.produce() + plot.transformer(self._draw())


@with_svg_writer
@with_plot_config
def histogram(writer: SvgWriter, plot: _XYPlot, bins: int,
              data: dict[str, list[float]]) -> None:
  print(writer)
  print(plot)
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
  writer.consume(
      _Histogram(
          binned_data, bin_size, min_value, max_value, max_count).produce(
              plot.with_defaults(_XYPlot(output_range=writer.get_box()))))


@dataclass(frozen=True)
class _BoxPlotOne:
  label: str
  y_min: float
  y_max: float
  quantiles: tuple[float, float, float]
  min_whisker: float
  max_whisker: float

  @classmethod
  def create(cls, label: str, data: list[float]) -> _BoxPlotOne:
    data = sorted(data)
    q1, median, q3 = statistics.quantiles(data, n=4, method='inclusive')
    iqr = q3 - q1
    fences = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
    min_whisker = min(x for x in data if x >= fences[0])
    max_whisker = max(x for x in data if x <= fences[1])

    return cls(label, min(data), max(data), (q1, median, q3), min_whisker,
               max_whisker)

  def draw(self, index: int, plot: _XYPlot) -> Iterable[Shape]:
    x = plot.transformer.transformer.transform(index, 0)[0]
    assert plot.output_range
    assert plot.margins
    return plot.transformer(self._shapes(index)) + [
        Text(self.label, x,
             plot.output_range.height() - plot.margins.bottom - 20,
             ShapeParams(css_class="boxplot-label"))
    ]

  @shape_generator
  def _shapes(self, index: int) -> Iterable[Shape]:
    q1, median, q3 = self.quantiles
    box_w = 0.7
    yield Line.vertical(index, self.min_whisker, self.max_whisker)
    for y in [self.min_whisker, self.max_whisker]:
      yield Line.horizontal(index - box_w / 2, index + box_w / 2, y)
    yield Rect(index - box_w / 2, q1, box_w, q3 - q1,
               ShapeParams(css_class="boxplot"))
    yield Line.horizontal(index - box_w / 2, index + box_w / 2, median,
                          ShapeParams(css_class="boxplot-median"))


@dataclass(frozen=True)
class _BoxPlot(ShapeProducer):

  data: dict[str, _BoxPlotOne]
  y_min: float
  y_max: float

  @shape_generator
  def _draw(self, plot: _XYPlot) -> Iterable[Shape]:
    return itertools.chain.from_iterable(
        self.data[key].draw(index, plot)
        for index, key in enumerate(sorted(self.data)))

  def produce(self, plot: _XYPlot) -> ShapeStream:
    plot = plot.with_defaults(
        _XYPlot(
            domain=Box(-1, math.floor(self.y_min), len(self.data),
                       math.ceil(self.y_max)),
            x_axis_values=PlotTicksConfig(max_count=0)))
    return plot.produce() + self._draw(plot)


@with_svg_writer
@with_plot_config
def boxplot(writer: SvgWriter, plot: _XYPlot, data: dict[str,
                                                         list[float]]) -> None:
  box_data = {k: _BoxPlotOne.create(k, v) for k, v in data.items()}
  writer.consume(
      _BoxPlot(box_data, min(d.y_min for d in box_data.values()),
               max(d.y_max for d in box_data.values())).produce(
                   plot.with_defaults(_XYPlot(output_range=writer.get_box()))))
