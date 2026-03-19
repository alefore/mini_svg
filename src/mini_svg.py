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
from plot_ticks import PlotTicks, PlotTicksConfig
from box import Margins, Box, simple_box
from shape import Circle, Line, Rect, Path, PathPoint, Shape, ShapeParams, ShapeStream, Text, shape_generator
from xyplot import XYPlot, with_plot_config


class ShapeProducer(ABC):

  @abstractmethod
  def produce(self, plot: XYPlot) -> ShapeStream:
    pass


def get_domain(points_it: Iterable[tuple[float, float]]) -> Box:
  all_points = list(points_it)
  all_x = [pt[0] for pt in all_points]
  all_y = [pt[1] for pt in all_points]
  return Box(x1=min(all_x), y1=min(all_y), x2=max(all_x), y2=max(all_y))


@dataclass(frozen=True)
class SvgWriter:

  output_path: pathlib.Path
  width: float
  height: float
  css: tuple[pathlib.Path, ...] = ()

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

  @_write_shape.register
  def _(self, path: Path) -> str:
    return f"<path d='{' '.join(str(p) for p in path.points)}' {path.params.as_text()}/>"


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

  def produce(self, plot: XYPlot) -> ShapeStream:
    plot = plot.with_defaults(
        XYPlot(domain=self.domain, labels=frozenset(self.data)))
    return plot.produce() + plot.transformer(self._draw())


@with_svg_writer
@with_plot_config
def scatterplot(writer: SvgWriter, plot: XYPlot,
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
                  plot.with_defaults(XYPlot(output_range=writer.get_box()))))


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

  def produce(self, plot: XYPlot) -> ShapeStream:
    bin_count = max(len(bins) for bins in self.binned_data.values())
    plot = plot.with_defaults(
        XYPlot(
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
def histogram(writer: SvgWriter, plot: XYPlot, bins: int,
              data: dict[str, list[float]]) -> None:
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
      _Histogram(binned_data, bin_size, min_value, max_value,
                 max_count).produce(
                     plot.with_defaults(XYPlot(output_range=writer.get_box()))))


@dataclass(frozen=True)
class _BoxPlotOne:
  label: str
  y_min: float
  y_max: float
  quantiles: tuple[float, float, float]
  min_whisker: float
  max_whisker: float

  @classmethod
  def create(cls, label: str, data: list[float]) -> "_BoxPlotOne":
    data = sorted(data)
    q1, median, q3 = statistics.quantiles(data, n=4, method='inclusive')
    iqr = q3 - q1
    fences = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
    min_whisker = min(x for x in data if x >= fences[0])
    max_whisker = max(x for x in data if x <= fences[1])

    return cls(label, min(data), max(data), (q1, median, q3), min_whisker,
               max_whisker)

  def draw(self, index: int, plot: XYPlot) -> Iterable[Shape]:
    x = plot.transformer.transformer.transform(index, 0)[0]
    assert plot.output_range
    margins_bottom: float = 0
    if plot.margins:
      margins_bottom = plot.margins.bottom
    return plot.transformer(self._shapes(index)) + [
        Text(self.label, x,
             plot.output_range.height() - margins_bottom - 20,
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
  def _draw(self, plot: XYPlot) -> Iterable[Shape]:
    return itertools.chain.from_iterable(
        self.data[key].draw(index, plot)
        for index, key in enumerate(sorted(self.data)))

  def produce(self, plot: XYPlot) -> ShapeStream:
    plot = plot.with_defaults(
        XYPlot(
            domain=Box(-1, math.floor(self.y_min), len(self.data),
                       math.ceil(self.y_max)),
            x_axis_values=PlotTicksConfig(max_count=0)))
    assert plot.domain.x1 == -1
    assert plot.domain.x2 == len(self.data)
    return plot.produce() + self._draw(plot)


@with_svg_writer
@with_plot_config
def boxplot(writer: SvgWriter, plot: XYPlot, data: dict[str,
                                                        list[float]]) -> None:
  box_data = {k: _BoxPlotOne.create(k, v) for k, v in data.items()}
  writer.consume(
      _BoxPlot(box_data, min(d.y_min for d in box_data.values()),
               max(d.y_max for d in box_data.values())).produce(
                   plot.with_defaults(XYPlot(output_range=writer.get_box()))))


@dataclass(frozen=True)
class _LinePlotOne:
  label: str
  data: tuple[tuple[float, float], ...]

  def draw(self, plot: XYPlot) -> Iterable[Shape]:
    points: list[PathPoint] = []
    points.append(PathPoint("M", self.data[0][0], self.data[0][1]))
    for point in self.data[1:]:
      points.append(PathPoint("L", point[0], point[1]))
    yield Path(tuple(points), ShapeParams(css_class="lineplot-line"))


@with_svg_writer
@with_plot_config
def lineplot(writer: SvgWriter, plot: XYPlot,
             data: dict[str, list[tuple[float, float]]]) -> None:
  line_data = {k: _LinePlotOne(k, tuple(v)) for k, v in data.items()}
  plot = plot.with_defaults(
      XYPlot(
          output_range=writer.get_box(),
          domain=get_domain(itertools.chain.from_iterable(data.values()))))
  writer.consume(plot.produce() + itertools.chain.from_iterable(
      plot.transformer(line_data[key].draw(plot)) for key in sorted(line_data)))
